"""
cleanup_storage.py
Deletes images from Supabase Storage for posts that are older than 7 days
and have already been published. This keeps storage usage near zero.
"""
import logging
from datetime import datetime, timedelta, timezone
from supabase import create_client
from config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

STORAGE_BUCKET = "post-images"
CLEANUP_AFTER_DAYS = 7


def cleanup_old_images() -> None:
    """
    Deletes images from Supabase Storage for all posts that:
    - Have status = 'published'
    - Were published more than CLEANUP_AFTER_DAYS days ago
    - Still have an image_url set (not already cleaned up)
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    cutoff = (datetime.now(timezone.utc) - timedelta(days=CLEANUP_AFTER_DAYS)).isoformat()

    result = supabase.table("posts") \
        .select("id, image_url") \
        .eq("status", "published") \
        .lt("published_at", cutoff) \
        .not_.is_("image_url", "null") \
        .execute()

    posts = result.data
    if not posts:
        logger.info("No old images to clean up.")
        return

    logger.info(f"Found {len(posts)} old image(s) to delete.")

    for post in posts:
        try:
            # Extract file path from the full URL
            image_url = post["image_url"]
            file_path = image_url.split(f"/storage/v1/object/public/{STORAGE_BUCKET}/")[-1]
            supabase.storage.from_(STORAGE_BUCKET).remove([file_path])

            # Clear the image_url in DB
            supabase.table("posts").update({"image_url": None}).eq("id", post["id"]).execute()
            logger.info(f"Deleted image for post {post['id']}: {file_path}")
        except Exception as e:
            logger.error(f"Failed to delete image for post {post['id']}: {e}")


if __name__ == "__main__":
    cleanup_old_images()
