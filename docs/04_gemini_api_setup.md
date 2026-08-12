# Step 4: Google Gemini API Setup

> **Time required:** ~5 minutes
> **Difficulty:** Very Easy
> **Cost:** Free tier available, no credit card required to start

## What is Gemini?

Google Gemini is the AI brain of your app — it generates the original
motivational quotes, captions, hashtags, and suggests background colors.
This project uses **`gemini-3.5-flash`** by default (set in `engine/config.py`
and your `GEMINI_MODEL` secret).

> **Why "3.5" and not an older or newer number:** Google retires and renames
> Gemini models every few months, faster than most docs (including this one)
> can track. If generation ever starts failing with a 404 "model not found"
> error, that's almost always this — check
> **https://ai.google.dev/gemini-api/docs/models** for the current
> recommended free-tier Flash model and update the `GEMINI_MODEL` secret
> (no code changes needed, it's read from that one setting).

---

## 1. Get Your API Key

1. Go to **https://aistudio.google.com**
2. Sign in with your Google account
3. Look for **Get API key** (usually top-left or in a left-side menu — this
   has moved around AI Studio's layout before)
4. Click **Create API key**
5. Choose to create it in a new project (or an existing one, doesn't matter for this)
6. Your API key will be generated — copy it immediately and save it somewhere safe

---

## 2. About Free Tier Limits

Google's free-tier request limits for Gemini have changed several times over
the past year — different models get different daily/per-minute caps, and
the numbers have moved up and down more than once. Rather than print a
specific number here that may already be wrong by the time you read this,
check the current limits directly at
**https://ai.google.dev/gemini-api/docs/rate-limits**.

What matters for you: at 2-10 posts per day, this app makes roughly one
Gemini call per post (a few more if a generated quote gets rejected as a
duplicate and retried). That's an order of magnitude below every free-tier
number Google has offered for a Flash model in the last year, even during
the more restrictive periods — so this is very unlikely to be something you
need to worry about at your posting volume.

---

## 3. Add to GitHub Secrets

- `GEMINI_API_KEY` = your API key from Step 1
- `GEMINI_MODEL` = `gemini-3.5-flash` (or whatever the current recommended
  free Flash model is, if you checked the models page above and it's changed)

---

## ✅ You're Done with Gemini Setup!

Next: [Resend Email Setup →](05_resend_email_setup.md)
