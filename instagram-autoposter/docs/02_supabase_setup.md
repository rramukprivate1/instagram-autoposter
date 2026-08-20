# Step 2: Supabase Setup Guide

> **Time required:** ~15 minutes  
> **Difficulty:** Beginner-friendly  
> **Cost:** Free — no credit card required

## What is Supabase?

Supabase is your free database and backend. It stores:
- Your topics, tones, and settings
- All generated posts and their status (pending/approved/published)
- Image files (for up to 1GB, which is enough for years)
- Your login credentials for the admin panel

---

## 1. Create a Supabase Account

1. Go to **https://supabase.com**
2. Click **Start your project** → **Sign up with GitHub** (easiest option since you just set up GitHub)
3. Authorize Supabase to access your GitHub account

---

## 2. Create a New Project

1. Click **New project**
2. Fill in the details:
   - **Name:** `instagram-autoposter`
   - **Database password:** Create a strong password (save this somewhere safe!)
   - **Region:** Choose whichever is physically closest to you — if you're in
     India, that's usually a South or Southeast Asia region (e.g. Mumbai or
     Singapore, whichever Supabase currently lists); closer generally means
     slightly faster dashboard/API responses, though it won't make a real
     difference at this project's scale
3. Click **Create new project**
4. Wait about 2 minutes for it to set up

---

## 3. Get Your API Keys

1. In your Supabase project, click **Settings** (gear icon, left sidebar)
2. Click **API**
3. You will see the keys you need — Supabase has renamed/reorganized this
   page before, so if the exact labels below don't match what you see, look
   for the closest equivalent:
   - **Project URL** → This is your `SUPABASE_URL`
   - **anon / public** key (sometimes labeled "publishable") → This is your `SUPABASE_ANON_KEY`
   - **service_role** key (sometimes labeled "secret", click to reveal) → This is your `SUPABASE_SERVICE_KEY`

⚠️ **IMPORTANT:** The `service_role`/secret key has full admin access. Never share it or put it in frontend code. Only use it in GitHub Secrets and your backend Python scripts.

---

## 4. Run the Database Schema

1. In your Supabase project, click **SQL Editor** (left sidebar, looks like `</>`)
2. Click **New query**
3. Open the file `supabase/schema.sql` from your project folder
4. Copy ALL the content from that file
5. Paste it into the SQL Editor
6. Click **Run** (the green play button, or press Ctrl+Enter)
7. You should see "Success. No rows returned" — that means it worked!
8. Repeat steps 2-7 for **`supabase/migrations/0002_carousel_and_scheduling.sql`**
   — this second file adds carousel posts and the admin-controlled posting
   times. It must be run after `schema.sql`, and both only need to be run once.

---

## 5. Run the Seed Data

1. In the SQL Editor, click **New query** again
2. Open the file `supabase/seed.sql` from your project folder
3. Copy ALL the content and paste it into the SQL Editor
4. Click **Run**
5. This will add the default topics, tones, and settings

---

## 6. Create the Storage Bucket

1. In your Supabase project, click **Storage** (left sidebar)
2. Click **New bucket**
3. Bucket name: `post-images`
4. ✅ Check **Public bucket** (Instagram needs a public URL to fetch the image)
5. Click **Create bucket**

---

## 7. Create Your Admin Login

The admin panel uses Supabase Auth for login.

1. Click **Authentication** (left sidebar)
2. Click **Users** → **Add user** → **Create new user**
3. Enter your email and a strong password
4. This is what you will use to log into the admin panel!

---

## 8. Add to GitHub Secrets

Go back to your GitHub repo → Settings → Secrets and add:
- `SUPABASE_URL` = Your Project URL from Step 3
- `SUPABASE_SERVICE_KEY` = Your service_role key from Step 3
- `SUPABASE_ANON_KEY` = Your anon public key from Step 3

---

## ✅ You're Done with Supabase Setup!

Next: [Meta Developer Setup →](03_meta_developer_setup.md)
