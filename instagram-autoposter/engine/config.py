import os
from dotenv import load_dotenv

load_dotenv()

# Every credential is loaded with .get() (returns None if absent) instead of
# os.environ[...] (crashes immediately). A single config.py is imported by
# every script in this project, but not every script needs every credential -
# cleanup_storage.py and publish_post.py don't touch Gemini, for example.
# Call require([...]) below with just the names a given script actually
# needs - that's what turns a missing var into a clear, specific error
# instead of either a silent None or a crash naming the wrong culprit.

# Supabase
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.environ.get("SUPABASE_SERVICE_KEY")

# Gemini
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
# NOTE: Google retires Gemini model IDs on a ~4-6 month cycle. If generation
# starts failing with a 404, check https://ai.google.dev/gemini-api/docs/deprecations
# for the current recommended model and update GEMINI_MODEL in your .env / GitHub secret.

# Instagram / Meta Graph API
IG_ACCESS_TOKEN = os.environ.get("IG_ACCESS_TOKEN")
IG_ACCOUNT_ID = os.environ.get("IG_ACCOUNT_ID")

# Resend (email)
RESEND_API_KEY = os.environ.get("RESEND_API_KEY")
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "noreply@yourdomain.com")
APPROVAL_TO_EMAIL = os.environ.get("APPROVAL_TO_EMAIL")

# App URL (for approve/reject links in email)
APP_BASE_URL = os.environ.get("APP_BASE_URL")  # e.g. https://your-app.vercel.app

# Image settings
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1080"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "1080"))
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", "/tmp/posts")

# Deduplication settings
DUPLICATE_SIMILARITY_THRESHOLD = float(os.getenv("DUPLICATE_SIMILARITY_THRESHOLD", "0.85"))
DUPLICATE_LOOKBACK_DAYS = int(os.getenv("DUPLICATE_LOOKBACK_DAYS", "30"))

_ALL_VALUES = {
    "SUPABASE_URL": SUPABASE_URL,
    "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
    "GEMINI_API_KEY": GEMINI_API_KEY,
    "IG_ACCESS_TOKEN": IG_ACCESS_TOKEN,
    "IG_ACCOUNT_ID": IG_ACCOUNT_ID,
    "RESEND_API_KEY": RESEND_API_KEY,
    "APPROVAL_TO_EMAIL": APPROVAL_TO_EMAIL,
    "APP_BASE_URL": APP_BASE_URL,
}


def require(names: list) -> None:
    """
    Call at the top of a script's entry point with just the variable names
    IT needs, e.g. require(["SUPABASE_URL", "SUPABASE_SERVICE_KEY"]).
    Raises a clear error naming exactly what's missing, instead of a
    KeyError pointing at config.py for a variable this script never uses.
    """
    missing = [name for name in names if not _ALL_VALUES.get(name)]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            f"Check this workflow's `env:` block in .github/workflows/ and your GitHub Secrets."
        )
