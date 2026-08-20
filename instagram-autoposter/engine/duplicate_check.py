"""
duplicate_check.py
Checks if a generated quote is semantically similar to recent posts
using sentence-transformers embeddings and pgvector in Supabase.
"""
import logging
import numpy as np
from sentence_transformers import SentenceTransformer
from supabase import create_client
from config import (
    SUPABASE_URL, SUPABASE_SERVICE_KEY,
    DUPLICATE_SIMILARITY_THRESHOLD, DUPLICATE_LOOKBACK_DAYS
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load model once (cached after first download)
_model = None


def get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model (first run may take ~60s)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def embed_text(text: str) -> list:
    """Embed a string into a vector."""
    model = get_model()
    return model.encode(text).tolist()


def cosine_similarity(a: list, b: list) -> float:
    """Compute cosine similarity between two vectors."""
    a, b = np.array(a), np.array(b)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def is_duplicate(quote: str) -> tuple[bool, float]:
    """
    Returns (is_duplicate: bool, highest_similarity: float).
    Queries Supabase for posts in the last DUPLICATE_LOOKBACK_DAYS days
    and checks cosine similarity of embeddings.
    """
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    embedding = embed_text(quote)

    # Use pgvector cosine distance query via RPC
    try:
        result = supabase.rpc(
            "find_similar_posts",
            {
                "query_embedding": embedding,
                "lookback_days": DUPLICATE_LOOKBACK_DAYS,
                "match_threshold": DUPLICATE_SIMILARITY_THRESHOLD,
                "match_count": 1
            }
        ).execute()

        if result.data and len(result.data) > 0:
            top_similarity = 1 - result.data[0]["distance"]  # pgvector returns distance
            logger.warning(f"Duplicate detected! Similarity: {top_similarity:.3f}")
            return True, top_similarity

        logger.info("No duplicate found. Quote is unique.")
        return False, 0.0

    except Exception as e:
        logger.error(f"Duplicate check failed (pgvector RPC error): {e}")
        # Fail open: allow post if check fails
        return False, 0.0


def save_embedding(post_id: str, quote: str) -> None:
    """Saves the embedding vector for a newly queued post."""
    supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    embedding = embed_text(quote)
    supabase.table("posts").update({"embedding": embedding}).eq("id", post_id).execute()
    logger.info(f"Saved embedding for post {post_id}")
