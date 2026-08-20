# Step 6: Deployment Guide

> **Time required:** ~20 minutes
> **Difficulty:** Easy (following steps)

## What We Are Deploying

1. **Admin PWA** → Vercel (free hosting, gives you a public URL)
2. **API Routes** → Also on Vercel (the approve/reject link handler)
3. **Automation Engine** → GitHub Actions (already set up, runs on schedule)

---

## 1. Deploy Admin Panel to Vercel

### Create a Vercel Account
1. Go to **https://vercel.com**
2. Click **Sign up** → **Continue with GitHub**
3. Authorize Vercel to access your GitHub

### Deploy the App
1. In Vercel dashboard, click **Add New → Project**
2. Find your `instagram-autoposter` repository and click **Import**
3. Configure the project (labels below are current as of writing — Vercel's
   import screen has been redesigned before, so look for the closest match
   if something's phrased differently):
   - **Framework Preset:** Vite
   - **Root Directory:** `admin-panel`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Add Environment Variables (click **Environment Variables** section):
   - `VITE_SUPABASE_URL` = your Supabase URL
   - `VITE_SUPABASE_ANON_KEY` = your Supabase anon key
   - `VITE_APP_BASE_URL` = leave blank for now (fill in after first deploy)
5. Click **Deploy**
6. Wait ~2 minutes for the build
7. You will get a URL like `https://instagram-autoposter-xyz.vercel.app`

### Set APP_BASE_URL
1. Copy your Vercel URL
2. Go to GitHub repo → Settings → Secrets → Add:
   - `APP_BASE_URL` = `https://instagram-autoposter-xyz.vercel.app`
3. Also update it in Vercel Environment Variables
4. Redeploy the app on Vercel (click **Redeploy** in the Vercel dashboard)

---

## 2. Double-Check the Database Is Fully Set Up

Before testing, confirm you ran **both** SQL files from the Supabase guide:
`supabase/schema.sql` AND `supabase/migrations/0002_carousel_and_scheduling.sql`.
If you only ran the first one, the Schedule Settings page will appear to save
successfully but silently do nothing, since the settings rows it's trying to
update won't exist yet.

---

## 3. Test the Automation Manually

1. Go to your GitHub repository
2. Click **Actions** tab
3. Click **Generate & Queue Post** workflow
4. Click **Run workflow** (top right)
5. Click **Run workflow** button
6. Watch the logs in real-time — each step will show as it runs
7. **Note:** as of this version, the script first checks whether the current
   time is near one of your configured Posting Times before generating
   anything — if you're testing outside those windows, it will exit early
   with "No posting window due right now." That's expected behavior, not a
   bug. To force a real test, either temporarily add a Posting Time a few
   minutes from now in the admin panel's Schedule Settings, or edit
   `posting_windows` directly in the Supabase `settings` table.
8. Once it does run, check:
   - Your email inbox (should receive the approval email!)
   - Supabase → Table Editor → `posts` table (should have a new row)

---

## 4. Approve Your First Post

1. Open the approval email you received
2. Review the quote image and caption
3. Click **✅ Approve & Schedule**
4. You should see the confirmation page
5. Go to GitHub Actions → Run the **Publish Approved Posts** workflow manually
6. Check your Instagram profile — the post should appear! 🎉

---

## 5. How the Automatic Schedule Actually Works

| Workflow | Runs | What it does |
|----------|------|---------------|
| Generate & Queue Post | Every 15 minutes | Checks your configured Posting Times; only generates a post if one is due right now |
| Publish Approved Posts | Every 30 minutes | Publishes anything you've approved (or anything auto-approved, if `auto_post` is on) |
| Cleanup | Daily | Removes old images from storage after the retention period |

Running every 15 minutes does **not** mean 96 posts a day — it means the
system checks 96 times a day whether one of *your* configured times has
arrived. Change how many times you post, and exactly when, entirely from
**Admin Panel → Schedule Settings → Posting Times** — no code or workflow
file edits needed.

---

## 6. Managing the App

- **Add a new topic:** Admin panel → Topic Manager → Add Topic
- **Change tone:** Admin panel → Tone Manager → Add/Edit Tone
- **Change posting frequency/times:** Admin panel → Schedule Settings → Posting Times
- **Adjust carousel posts:** Admin panel → Schedule Settings → Carousel / Sequence Posts
- **View post history:** Admin panel → Analytics

---

## ✅ Your Instagram Auto-Poster is Live!

### Remember:
- Start with **2 posts/day** (2 Posting Times configured) for the first 2 weeks
- Gradually increase toward 5-10 posts/day over a month, using the "Spread
  evenly" helper in Schedule Settings as a starting point each time
- Refresh your Instagram access token every **~55 days** (before the 60-day expiry)
- Monitor your Instagram account for any warnings from Meta
