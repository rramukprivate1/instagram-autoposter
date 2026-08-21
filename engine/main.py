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
import os
import sys
import json
import uuid
import random
import logging
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from supabase import create_client
import config
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY
from generate_quote import generate_quote, generate_quote_series
from duplicate_check import is_duplicate, save_embedding
from render_image import render_quote_card, render_carousel_slides
from send_email import send_approval_email

config.require([
    "SUPABASE_URL", "SUPABASE_SERVICE_KEY", "GEMINI_API_KEY",
    "RESEND_API_KEY", "APPROVAL_TO_EMAIL", "APP_BASE_URL",
])

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

def apply_jitter(base_time: str, date_str: str, max_jitter_minutes: int) -> str:
    """
    Shifts a configured posting time by a random-looking but deterministic
    offset, unique to that day+slot combination. Same slot lands at a
    different actual minute each day (e.g. 08:00 becomes 07:44 today,
    08:19 tomorrow) without needing to persist anything - re-deriving the
    same seed on every 15-min check within the same day always gives the
    same jittered target, so it doesn't drift mid-day.
    """
    if max_jitter_minutes <= 0:
        return base_time
    rng = random.Random(f"{date_str}-{base_time}")
    offset = rng.randint(-max_jitter_minutes, max_jitter_minutes)
    h, m = map(int, base_time.split(":"))
    total = max(0, min(23 * 60 + 59, h * 60 + m + offset))
    return f"{total // 60:02d}:{total % 60:02d}"


def get_current_slots(now_local: datetime, posting_windows: list, tolerance_minutes: int, jitter_minutes: int = 0):
    """
    Returns a list of ALL 'HH:MM' base-slot strings from posting_windows
    currently within tolerance_minutes (after applying that day's jitter) -
    not just the first. At high slot density (many Posting Times close
    together, especially combined with jitter), more than one slot's
    tolerance window can be active at the same 15-min check - returning
    only the first match would silently skip the others for the whole
    day, since each is only ever compared against the current moment,
    not retried later once its own window has passed.
    Note: doesn't handle windows that wrap midnight (e.g. '23:55') specially -
    not needed for a same-day posting schedule, but worth knowing if you add one.
    """
    date_str = now_local.date().isoformat()
    now_minutes = now_local.hour * 60 + now_local.minute
    matches = []
    for base_slot in posting_windows:
        jittered = apply_jitter(base_slot, date_str, jitter_minutes)
        h, m = map(int, jittered.split(":"))
        if abs(now_minutes - (h * 60 + m)) <= tolerance_minutes:
            matches.append(base_slot)
    return matches


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

def create_single_post(supabase, topic, tone, custom_context, watermark, cta_text, auto_post, logo_url, tagline) -> str:
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
        post_id=post_id, watermark=watermark, logo_url=logo_url, tagline=tagline,
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
    auto_post, min_slides, max_slides, logo_url, tagline,
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
        post_id=post_id, watermark=watermark, logo_url=logo_url, tagline=tagline,
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
# Per-slot generation
# ------------------------------------------------------------------

def generate_and_queue_one(
    supabase, settings, topics, tones, topic_override, tone_override, recent_topic_id,
) -> str:
    """
    Runs one full generate -> render -> upload -> queue -> email cycle,
    for one due slot. Returns the topic_id it ended up using, so a run
    handling several due slots at once can feed that back in as the next
    iteration's "avoid this topic" hint - without it, generating 5 posts
    in one run could pick the same topic for all 5.
    """
    if topic_override:
        matched = next((t for t in topics if t["name"].lower() == topic_override.lower()), None)
        if not matched:
            logger.error(f"topic_override '{topic_override}' doesn't match any active topic name. Exiting.")
            sys.exit(1)
        topic = matched
        logger.info(f"Using topic_override: {topic['name']}")
    else:
        topic = pick_topic(topics, recent_topic_id)

    if tone_override:
        matched = next((t for t in tones if t["name"].lower() == tone_override.lower()), None)
        if not matched:
            logger.error(f"tone_override '{tone_override}' doesn't match any active tone name. Exiting.")
            sys.exit(1)
        tone = matched
        logger.info(f"Using tone_override: {tone['name']}")
    else:
        tone = random.choice(tones)

    custom_context = settings.get("custom_context", "")
    # Empty by default - showing nothing looks like a deliberate clean design
    # choice; showing a literal "@yourhandle" placeholder on a real published
    # post looks like a bug, because it is one if this isn't set.
    watermark = settings.get("ig_handle", "").strip()
    cta_text = settings.get("cta_text", "").strip()
    auto_post = settings.get("auto_post", "false").lower() == "true"
    carousel_probability = float(settings.get("carousel_probability", "0.25"))
    min_slides = int(settings.get("carousel_min_slides", "3"))
    max_slides = int(settings.get("carousel_max_slides", "6"))
    logo_url = settings.get("logo_url", "").strip()
    tagline = settings.get("watermark_tagline", "").strip()

    make_carousel = topic.get("allow_carousel", True) and random.random() < carousel_probability
    logger.info(f"Topic: {topic['name']} | Tone: {tone['name']} | Format: {'carousel' if make_carousel else 'single'}")

    if make_carousel:
        post_id, post_record = create_carousel_post(
            supabase, topic, tone, custom_context, watermark, cta_text,
            auto_post, min_slides, max_slides, logo_url, tagline,
        )
    else:
        post_id, post_record = create_single_post(
            supabase, topic, tone, custom_context, watermark, cta_text, auto_post, logo_url, tagline,
        )

    if not auto_post:
        email_data = {**post_record, "topic_name": topic["name"], "tone_name": tone["name"]}
        if send_approval_email(email_data):
            logger.info("Approval email sent successfully.")
        else:
            logger.warning("Approval email failed, but post is queued in DB - it's still visible in the admin panel.")

    logger.info(f"=== post {post_id} queued ({post_record['status']}) ===")
    return topic["id"]


# ------------------------------------------------------------------
# Entry point
# ------------------------------------------------------------------

def run() -> None:
    logger.info("=== Instagram Auto-Poster: Checking for due posting slots ===")
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    settings = load_settings(supabase)

    force_now = os.environ.get("FORCE_NOW", "").strip().lower() == "true"
    topic_override = os.environ.get("TOPIC_OVERRIDE", "").strip()
    tone_override = os.environ.get("TONE_OVERRIDE", "").strip()

    tz_name = settings.get("timezone", "Asia/Kolkata")
    try:
        posting_windows = json.loads(settings.get("posting_windows", "[]"))
    except (json.JSONDecodeError, TypeError):
        raw = settings.get('posting_windows')
        logger.error(f"posting_windows isn't valid JSON: {raw!r}. Treating as empty.")
        posting_windows = []
    tolerance = int(settings.get("slot_tolerance_minutes", "10"))
    jitter_minutes = int(settings.get("posting_time_jitter_minutes", "20"))

    now_local = datetime.now(ZoneInfo(tz_name))
    slot_date = now_local.date().isoformat()

    if force_now:
        logger.info("FORCE_NOW is set - posting immediately, ignoring configured Posting Times.")
        due_slots = [None]  # one forced post; None means "not tied to a configured slot"
    else:
        matched = get_current_slots(now_local, posting_windows, tolerance, jitter_minutes)
        due_slots = [s for s in matched if not has_slot_fired(supabase, slot_date, s)]
        if not due_slots:
            logger.info(f"No posting window due right now ({now_local.strftime('%H:%M')} {tz_name}). Exiting.")
            return
        logger.info(f"{len(due_slots)} slot(s) due this check: {due_slots}")

    topics = load_active_topics(supabase)
    tones = load_active_tones(supabase)
    if not topics:
        logger.error("No active topics found. Add topics in the admin panel.")
        sys.exit(1)
    if not tones:
        logger.error("No active tones found. Add tones in the admin panel.")
        sys.exit(1)

    recent_topic_id = load_most_recent_topic_id(supabase)

    for slot in due_slots:
        try:
            recent_topic_id = generate_and_queue_one(
                supabase, settings, topics, tones, topic_override, tone_override, recent_topic_id,
            )
        except Exception as e:
            logger.error(f"Post generation failed for slot {slot}, NOT marked as fired (will retry next check): {e}")
            continue  # one failed slot in a multi-slot run shouldn't block the rest

        # Only mark fired once a post actually exists - protects against a
        # transient failure permanently losing this slot for today. Forced
        # runs aren't tied to a configured slot, so there's nothing to mark.
        if slot:
            mark_slot_fired(supabase, slot_date, slot)

    logger.info(f"=== Generation run complete: {len(due_slots)} slot(s) processed ===")


if __name__ == "__main__":
    run()
