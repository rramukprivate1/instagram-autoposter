"""
main.py
The main orchestrator script, called by GitHub Actions every 15 minutes.

Each run does this:
  1. Load settings from Supabase (posting_windows, timezone, etc.)
  2. Check whether NOW falls inside one of the owner's configured posting
     windows, and whether that window has already fired today - if not
     eligible, exit quietly (this is normal - most 15-min checks do nothing)
  3. Pick a topic (never the same one as the last post) and a tone
  4. Roll against carousel_probability to decide single post vs. carousel
  5. Generate text via Gemini, checked against pgvector for duplicates
  6. Render image(s) via Pillow
  7. Upload to Supabase Storage
  8. Insert the post (and slides, if a carousel) into Supabase with
     status='pending' (or 'approved' if auto_post is on)
  9. Send an approval email via Resend, unless auto_post is on

Why polling every 15 min instead of one cron entry per posting time:
the owner changes posting_windows from the admin panel, not by editing
YAML - this file is what makes that actually take effect without a
code change or a redeploy.
"""
import sys
import json
import uuid
import random
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from generate_quote import generate_quote, generate_quote_series
from duplicate_check import is_duplicate, save_embedding
from render_image import render_quote_card, render_carousel_slides
from send_email import send_approval_email

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_GENERATION_RETRIES = 3
STORAGE_BUCKET = "post-images"


# ------------------------------------------------------------------
# Settings / topic / tone loading
# ------------------------------------------------------------------

def load_active_topics(supabase) -> list:
    return supabase.table("topics").select("*").eq("is_active", True).execute().data


def load_active_tones(supabase) -> list:
    return supabase.table("tones").select("*").eq("is_active", True).execute().data


def load_settings(supabase) -> dict:
    result = supabase.table("settings").select("key, value").execute()
    return {row["key"]: row["value"] for row in result.data}


def load_most_recent_topic_id(supabase):
    result = supabase.table("posts").select("topic_id").order("created_at", desc=True).limit(1).execute()
    return result.data[0]["topic_id"] if result.data else None


def pick_topic(topics: list, recent_topic_id) -> dict:
    """Avoid repeating the same topic twice in a row when there's a choice."""
    pool = [t for t in topics if t["id"] != recent_topic_id] or topics
    return random.choice(pool)


# ------------------------------------------------------------------
# Posting-window slot matching
# ------------------------------------------------------------------

def get_current_slot(now_local: datetime, posting_windows: list, tolerance_minutes: int):
    """
    Returns the matching 'HH:MM' string from posting_windows if now_local
    is within tolerance_minutes of it, else None.
    Note: doesn't handle windows that wrap midnight (e.g. '23:55') specially -
    not needed for a same-day posting schedule, but worth knowing if you add one.
    """
    now_minutes = now_local.hour * 60 + now_local.minute
    for slot in posting_windows:
        h, m = map(int, slot.split(":"))
        if abs(now_minutes - (h * 60 + m)) <= tolerance_minutes:
            return slot
    return None


def has_slot_fired(supabase, slot_date: str, slot: str) -> bool:
    result = supabase.table("slot_runs").select("slot_time").eq("slot_date", slot_date).eq("slot_time", slot).execute()
    return len(result.data) > 0


def mark_slot_fired(supabase, slot_date: str, slot: str) -> None:
    """
    Only called AFTER a post is successfully created - so a transient
    failure (e.g. Gemini hiccup) still gets retried on the next 15-min
    check, as long as we're still inside this slot's tolerance window.
    """
    supabase.table("slot_runs").insert({"slot_date": slot_date, "slot_time": slot}).execute()


# ------------------------------------------------------------------
# Storage
# ------------------------------------------------------------------

def upload_image_to_supabase(supabase, image_path: str, storage_name: str) -> str:
    with open(image_path, "rb") as f:
        file_content = f.read()
    file_name = f"{storage_name}.jpg"
    supabase.storage.from_(STORAGE_BUCKET).upload(
        file_name, file_content,
        file_options={"content-type": "image/jpeg", "cache-control": "3600", "upsert": "false"}
    )
    return supabase.storage.from_(STORAGE_BUCKET).get_public_url(file_name)


# ------------------------------------------------------------------
# Post creation - single and carousel share everything except
# generation/rendering/upload, which is why those three steps are
# the only branch point below.
# ------------------------------------------------------------------

def create_single_post(supabase, topic, tone, custom_context, watermark, cta_text, auto_post) -> str:
    for attempt in range(1, MAX_GENERATION_RETRIES + 1):
        content = generate_quote(topic, tone, custom_context)
        duplicate, similarity = is_duplicate(content["quote"])
        if not duplicate:
            break
        logger.warning(f"Attempt {attempt}: duplicate (similarity={similarity:.2f}). Retrying...")
        if attempt == MAX_GENERATION_RETRIES:
            raise RuntimeError("All attempts produced duplicate content.")

    post_id = str(uuid.uuid4())
    image_path = render_quote_card(
        quote=content["quote"], caption=content["caption"],
        bg_from=content.get("bg_from", "#0d0d0d"), bg_to=content.get("bg_to", "#1a1a2e"),
        post_id=post_id, watermark=watermark,
    )
    image_url = upload_image_to_supabase(supabase, image_path, post_id)
    caption = content["caption"] + (f"\n\n{cta_text}" if cta_text else "")

    post_record = {
        "id": post_id, "quote": content["quote"], "caption": caption,
        "hashtags": content["hashtags"], "topic_id": topic["id"], "tone_id": tone["id"],
        "image_url": image_url, "post_format": "single",
        "status": "approved" if auto_post else "pending",
        "approval_token": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase.table("posts").insert(post_record).execute()
    save_embedding(post_id, content["quote"])
    logger.info(f"Single post inserted: {post_id}, status={post_record['status']}")
    return post_id, post_record


def create_carousel_post(
    supabase, topic, tone, custom_context, watermark, cta_text,
    auto_post, min_slides, max_slides,
) -> str:
    slide_count = random.randint(min_slides, max_slides)
    for attempt in range(1, MAX_GENERATION_RETRIES + 1):
        series = generate_quote_series(topic, tone, slide_count, custom_context)
        duplicate, similarity = is_duplicate(series["slides"][0])
        if not duplicate:
            break
        logger.warning(f"Attempt {attempt}: first slide duplicate (similarity={similarity:.2f}). Retrying...")
        if attempt == MAX_GENERATION_RETRIES:
            raise RuntimeError("All attempts produced duplicate content.")

    post_id = str(uuid.uuid4())
    slide_paths = render_carousel_slides(
        series["slides"], series.get("bg_from", "#0d0d0d"), series.get("bg_to", "#1a1a2e"),
        post_id=post_id, watermark=watermark,
    )
    slide_urls = [
        upload_image_to_supabase(supabase, path, f"{post_id}_slide{i + 1}")
        for i, path in enumerate(slide_paths)
    ]
    caption = series["caption"] + (f"\n\n{cta_text}" if cta_text else "")

    post_record = {
        "id": post_id, "quote": series["slides"][0], "caption": caption,
        "hashtags": series["hashtags"], "topic_id": topic["id"], "tone_id": tone["id"],
        "image_url": slide_urls[0], "post_format": "carousel",
        "status": "approved" if auto_post else "pending",
        "approval_token": str(uuid.uuid4()),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    supabase.table("posts").insert(post_record).execute()
    supabase.table("post_slides").insert([
        {"post_id": post_id, "slide_index": i, "slide_text": text, "image_url": url}
        for i, (text, url) in enumerate(zip(series["slides"], slide_urls))
    ]).execute()
    save_embedding(post_id, series["slides"][0])
    logger.info(f"Carousel post inserted: {post_id}, {len(slide_urls)} slides, status={post_record['status']}")
    return post_id, post_record


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def run() -> None:
    logger.info("=== Instagram Auto-Poster: Checking for a due posting slot ===")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    settings = load_settings(supabase)

    tz_name = settings.get("timezone", "Asia/Kolkata")
    try:
        posting_windows = json.loads(settings.get("posting_windows", "[]"))
    except (json.JSONDecodeError, TypeError):
        raw = settings.get('posting_windows')
        logger.error(f"posting_windows isn't valid JSON: {raw!r}. Treating as empty.")
        posting_windows = []
    tolerance = int(settings.get("slot_tolerance_minutes", "10"))

    now_local = datetime.now(ZoneInfo(tz_name))
    slot = get_current_slot(now_local, posting_windows, tolerance)

    if not slot:
        logger.info(f"No posting window due right now ({now_local.strftime('%H:%M')} {tz_name}). Exiting.")
        return

    slot_date = now_local.date().isoformat()
    if has_slot_fired(supabase, slot_date, slot):
        logger.info(f"Slot {slot} already posted today. Exiting.")
        return

    logger.info(f"Slot {slot} is due and hasn't fired today - generating a post.")

    topics = load_active_topics(supabase)
    tones = load_active_tones(supabase)
    if not topics:
        logger.error("No active topics found. Add topics in the admin panel.")
        sys.exit(1)
    if not tones:
        logger.error("No active tones found. Add tones in the admin panel.")
        sys.exit(1)

    recent_topic_id = load_most_recent_topic_id(supabase)
    topic = pick_topic(topics, recent_topic_id)
    tone = random.choice(tones)
    custom_context = settings.get("custom_context", "")
    watermark = settings.get("ig_handle", "@yourhandle")
    cta_text = settings.get("cta_text", "").strip()
    auto_post = settings.get("auto_post", "false").lower() == "true"
    carousel_probability = float(settings.get("carousel_probability", "0.25"))
    min_slides = int(settings.get("carousel_min_slides", "3"))
    max_slides = int(settings.get("carousel_max_slides", "6"))

    make_carousel = topic.get("allow_carousel", True) and random.random() < carousel_probability
    logger.info(f"Topic: {topic['name']} | Tone: {tone['name']} | Format: {'carousel' if make_carousel else 'single'}")

    try:
        if make_carousel:
            post_id, post_record = create_carousel_post(
                supabase, topic, tone, custom_context, watermark, cta_text,
                auto_post, min_slides, max_slides,
            )
        else:
            post_id, post_record = create_single_post(
                supabase, topic, tone, custom_context, watermark, cta_text, auto_post,
            )
    except Exception as e:
        logger.error(f"Post generation failed, slot NOT marked as fired (will retry next check): {e}")
        sys.exit(1)

    # Only mark the slot fired once a post actually exists - protects
    # against a transient failure permanently losing this slot for today.
    mark_slot_fired(supabase, slot_date, slot)

    if not auto_post:
        email_data = {**post_record, "topic_name": topic["name"], "tone_name": tone["name"]}
        if send_approval_email(email_data):
            logger.info("Approval email sent successfully.")
        else:
            logger.warning("Approval email failed, but post is queued in DB - it's still visible in the admin panel.")

    logger.info(f"=== Generation Run Complete: post {post_id} ({post_record['status']}) ===")


if __name__ == "__main__":
    run()
