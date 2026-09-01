"""
publish_post.py
Publishes an approved post to Instagram via the Meta Graph API.
Uses the two-step container creation + publish flow.
"""
import time
import logging
import requests
from supabase import create_client
import config
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY, IG_ACCESS_TOKEN, IG_ACCOUNT_ID

config.require(["SUPABASE_URL", "SUPABASE_SERVICE_KEY", "IG_ACCESS_TOKEN", "IG_ACCOUNT_ID"])

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# NOTE: graph.instagram.com is Meta's newer "Instagram API with Instagram Login"
# path, documented for reading your own media without a linked Page - it is not
# consistently documented as supporting the publish endpoints below. Content
# PUBLISHING is documented against graph.facebook.com with a Business/Creator
# account linked to a Facebook Page, which is what this file actually needs.
# Meta ships a new API version roughly every quarter and supports each for
# ~2 years - check https://developers.facebook.com/docs/graph-api/changelog
# periodically and bump GRAPH_API_VERSION well before your version sunsets.
GRAPH_API_VERSION = "v25.0"
GRAPH_API_BASE = f"https://graph.facebook.com/{GRAPH_API_VERSION}"


def graph_request(method: str, url: str, **kwargs) -> dict:
    """
    Wraps a Graph API call so failures carry Meta's ACTUAL error detail
    (code, subcode, message, fbtrace_id) instead of requests' generic
    "400 Client Error: Bad Request" - that generic message says nothing
    about why Instagram rejected the request, which made real failures
    here undiagnosable from logs alone. Every Graph API call in this file
    goes through this instead of calling requests directly.
    """
    resp = requests.request(method, url, timeout=30, **kwargs)
    try:
        data = resp.json()
    except ValueError:
        resp.raise_for_status()
        raise RuntimeError(f"Graph API returned a non-JSON response: {resp.text[:300]}")

    if resp.status_code >= 400:
        err = data.get("error", {})
        raise RuntimeError(
            f"Graph API error (HTTP {resp.status_code}): "
            f"code={err.get('code')} subcode={err.get('error_subcode')} "
            f"type={err.get('type')} message={err.get('message', data)} "
            f"fbtrace_id={err.get('fbtrace_id')}"
        )
    return data


def create_media_container(image_url: str, caption: str) -> str:
    """
    Step 1: Creates a media container on Instagram.
    Returns the container ID.
    """
    url = f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    logger.info(f"Creating media container for image: {image_url[:60]}...")
    data = graph_request("POST", url, data=payload)
    container_id = data.get("id")
    if not container_id:
        raise RuntimeError(f"No container ID returned: {data}")
    logger.info(f"Container created: {container_id}")
    return container_id


def wait_for_container(container_id: str, max_retries: int = 10) -> None:
    """Polls until the media container status is FINISHED."""
    url = f"{GRAPH_API_BASE}/{container_id}"
    for attempt in range(max_retries):
        data = graph_request("GET", url, params={"fields": "status_code", "access_token": IG_ACCESS_TOKEN})
        status = data.get("status_code", "")
        logger.info(f"Container status [{attempt + 1}/{max_retries}]: {status}")
        if status == "FINISHED":
            return
        if status == "ERROR":
            raise RuntimeError("Media container processing failed with ERROR status.")
        time.sleep(5)
    raise TimeoutError(f"Container {container_id} did not finish processing in time.")


def create_carousel_item_container(image_url: str) -> str:
    """
    Creates ONE item container for a carousel slide. Same idea as
    create_media_container() but flagged is_carousel_item and with no
    caption - captions only go on the parent carousel container.
    """
    url = f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media"
    payload = {
        "image_url": image_url,
        "is_carousel_item": "true",
        "access_token": IG_ACCESS_TOKEN,
    }
    resp = graph_request("POST", url, data=payload)
    container_id = resp.get("id")
    if not container_id:
        raise RuntimeError(f"No carousel item container ID returned: {resp}")
    return container_id


def create_carousel_container(item_container_ids: list, caption: str) -> str:
    """
    Creates the PARENT carousel container referencing each already-created
    item container. This is the container that actually gets published.
    """
    url = f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media"
    payload = {
        "media_type": "CAROUSEL",
        "children": ",".join(item_container_ids),
        "caption": caption,
        "access_token": IG_ACCESS_TOKEN,
    }
    logger.info(f"Creating carousel container with {len(item_container_ids)} slides...")
    data = graph_request("POST", url, data=payload)
    container_id = data.get("id")
    if not container_id:
        raise RuntimeError(f"No carousel container ID returned: {data}")
    logger.info(f"Carousel container created: {container_id}")
    return container_id


def publish_carousel(slide_image_urls: list, caption: str) -> str:
    """
    Full carousel publish flow: create + wait for each slide's item
    container, then create + wait for + publish the parent carousel
    container. Returns the published post ID.
    """
    item_ids = []
    for image_url in slide_image_urls:
        item_id = create_carousel_item_container(image_url)
        wait_for_container(item_id)
        item_ids.append(item_id)

    carousel_id = create_carousel_container(item_ids, caption)
    wait_for_container(carousel_id)
    return publish_container(carousel_id)


def publish_container(container_id: str) -> str:
    """
    Step 2: Publishes the media container to Instagram.
    Returns the published post ID.
    """
    url = f"{GRAPH_API_BASE}/{IG_ACCOUNT_ID}/media_publish"
    payload = {
        "creation_id": container_id,
        "access_token": IG_ACCESS_TOKEN,
    }
    logger.info(f"Publishing container: {container_id}")
    data = graph_request("POST", url, data=payload)
    post_id = data.get("id")
    if not post_id:
        raise RuntimeError(f"No post ID returned: {data}")
    logger.info(f"Published successfully! Instagram Post ID: {post_id}")
    return post_id


def publish_approved_posts() -> None:
    """
    Fetches the SINGLE oldest approved post and publishes it. Deliberately
    limited to one per run - if this fetched and published every approved
    post at once, approving several posts in a row would make them all go
    live within the same run, seconds apart, which looks nothing like
    natural posting behavior. One per 30-minute run cycle keeps real
    spacing between posts regardless of how many you approve at once.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    result = (
        supabase.table("posts")
        .select("*")
        .eq("status", "approved")
        .order("created_at")
        .limit(1)
        .execute()
    )
    posts = result.data

    if not posts:
        logger.info("No approved posts to publish.")
        return

    logger.info(f"Publishing the oldest approved post ({len(posts)} of possibly more waiting).")

    for post in posts:
        try:
            # Build full caption with hashtags
            hashtags = post.get("hashtags", [])
            hashtag_str = " ".join([f"#{tag}" for tag in hashtags])
            full_caption = f"{post['caption']}\n\n{hashtag_str}"

            if post.get("post_format") == "carousel":
                slides_result = supabase.table("post_slides") \
                    .select("image_url") \
                    .eq("post_id", post["id"]) \
                    .order("slide_index") \
                    .execute()
                slide_urls = [row["image_url"] for row in slides_result.data]
                if len(slide_urls) < 2:
                    raise RuntimeError(f"Carousel post {post['id']} has {len(slide_urls)} slide(s), need at least 2")
                ig_post_id = publish_carousel(slide_urls, full_caption)
            else:
                container_id = create_media_container(post["image_url"], full_caption)
                wait_for_container(container_id)
                ig_post_id = publish_container(container_id)

            # Update status in Supabase
            supabase.table("posts").update({
                "status": "published",
                "ig_post_id": ig_post_id,
                "published_at": "now()"
            }).eq("id", post["id"]).execute()

            logger.info(f"Post {post['id']} published as {ig_post_id}")
            time.sleep(2)  # Avoid hammering the API

        except Exception as e:
            error_detail = str(e)
            logger.error(f"Failed to publish post {post['id']}: {error_detail}")
            supabase.table("posts").update({
                "status": "publish_failed",
                "error_message": error_detail[:1000],
            }).eq("id", post["id"]).execute()


if __name__ == "__main__":
    publish_approved_posts()
