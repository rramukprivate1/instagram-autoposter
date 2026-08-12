import os
from dotenv import load_dotenv

load_dotenv()

# Supabase
SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]

# Gemini
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"]
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
# NOTE: Google retires Gemini model IDs on a ~4-6 month cycle. If generation
# starts failing with a 404, check https://ai.google.dev/gemini-api/docs/deprecations
# for the current recommended model and update GEMINI_MODEL in your .env / GitHub secret.

# Instagram / Meta Graph API
IG_ACCESS_TOKEN = os.environ["IG_ACCESS_TOKEN"]
IG_ACCOUNT_ID = os.environ["IG_ACCOUNT_ID"]

# Resend (email)
RESEND_API_KEY = os.environ["RESEND_API_KEY"]
RESEND_FROM_EMAIL = os.getenv("RESEND_FROM_EMAIL", "noreply@yourdomain.com")
APPROVAL_TO_EMAIL = os.environ["APPROVAL_TO_EMAIL"]

# App URL (for approve/reject links in email)
APP_BASE_URL = os.environ["APP_BASE_URL"]  # e.g. https://your-app.vercel.app

# Image settings
IMAGE_WIDTH = int(os.getenv("IMAGE_WIDTH", "1080"))
IMAGE_HEIGHT = int(os.getenv("IMAGE_HEIGHT", "1080"))
IMAGE_OUTPUT_DIR = os.getenv("IMAGE_OUTPUT_DIR", "/tmp/posts")

# Deduplication settings
DUPLICATE_SIMILARITY_THRESHOLD = float(os.getenv("DUPLICATE_SIMILARITY_THRESHOLD", "0.85"))
DUPLICATE_LOOKBACK_DAYS = int(os.getenv("DUPLICATE_LOOKBACK_DAYS", "30"))
