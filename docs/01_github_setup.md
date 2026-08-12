# Step 1: GitHub Setup Guide

> **Time required:** ~10 minutes
> **Difficulty:** Beginner-friendly

## What You Need to Do

GitHub will be the home of your project code AND the engine that runs your automation 24/7 for free.

---

## 1. Create a GitHub Account (if you don't have one)

1. Go to **https://github.com**
2. Click **Sign up** in the top right corner
3. Enter your email, create a password, and choose a username
4. Verify your email address
5. Choose the **Free plan**

---

## 2. Create a New Repository

1. After logging in, click the **+** icon in the top right → **New repository**
2. Fill in the details:
   - **Repository name:** `instagram-autoposter`
   - **Description:** `AI-powered automated Instagram posting system`
   - **Visibility:** ✅ **Public** (this is important — public repos get unlimited free GitHub Actions minutes)
   - Leave other options as default
3. Click **Create repository**
4. Copy the repository URL (looks like `https://github.com/yourusername/instagram-autoposter.git`)

---

## 3. Upload Your Project Files to GitHub

Since you are a beginner, the easiest way is to use **GitHub Desktop** (a visual app, no command line needed).

### Install GitHub Desktop
1. Go to **https://desktop.github.com**
2. Download and install it
3. Sign in with your GitHub account

### Upload the project
1. Open GitHub Desktop
2. Click **File → Add Local Repository**
3. Navigate to the folder where YOU unzipped/saved this project on your own computer
   (e.g. `C:\Users\<your-username>\Documents\instagram-autoposter` on Windows, or
   `/Users/<your-username>/instagram-autoposter` on Mac — this is wherever you put it, not a path from any guide)
4. Click **Add Repository**
5. Click **Publish repository** in the top bar
6. Make sure **Keep this code private** is **unchecked** (keep it public)
7. Click **Publish Repository**

Your code is now on GitHub! 🎉

---

## 4. Add GitHub Actions Secrets

This is how you store your API keys securely so GitHub Actions can use them. You'll fill these in gradually as you go through the next guides — it's fine to come back to this step repeatedly.

1. Go to your repository on GitHub: `https://github.com/yourusername/instagram-autoposter`
2. Click **Settings** tab (top of the page)
3. In the left sidebar, click **Secrets and variables → Actions**
4. Click **New repository secret**
5. Add these secrets one by one as you collect each value from the following guides:

| Secret Name | Where to get the value |
|-------------|------------------------|
| `SUPABASE_URL` | Supabase dashboard (see Step 2 guide) |
| `SUPABASE_SERVICE_KEY` | Supabase dashboard (see Step 2 guide) |
| `SUPABASE_ANON_KEY` | Supabase dashboard (see Step 2 guide) |
| `GEMINI_API_KEY` | Google AI Studio (see Step 4 guide) |
| `GEMINI_MODEL` | Type: `gemini-3.5-flash` — see the note in Step 4 guide, this changes over time |
| `IG_ACCESS_TOKEN` | Meta Developer (see Step 3 guide) |
| `IG_ACCOUNT_ID` | Meta Developer (see Step 3 guide) |
| `RESEND_API_KEY` | Resend dashboard (see Step 5 guide) |
| `RESEND_FROM_EMAIL` | Your verified sender email (see Step 5 guide) |
| `APPROVAL_TO_EMAIL` | Your personal email address |
| `APP_BASE_URL` | Your Vercel app URL (see Step 6 guide) |

> If a menu label above doesn't match exactly what you see, GitHub occasionally
> reorganizes settings pages — look for the closest equivalent (e.g. a search
> box in Settings), it's almost always still there under a similar name.

---

## ✅ You're Done with GitHub Setup!

Next: [Supabase Setup →](02_supabase_setup.md)
