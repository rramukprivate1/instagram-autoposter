# Step 3: Meta Developer & Instagram API Setup

> **Time required:** ~30-45 minutes
> **Difficulty:** Moderate (most complex step — take it slowly, one section at a time)
> **Cost:** Free

## Overview

This is the most important step. Without this, your app cannot post to Instagram.
We will use the **official** Meta Graph API — this keeps your account safe.

**A note before you start:** Meta's developer console gets reorganized fairly
often, so a button or menu label here might be phrased slightly differently
by the time you read this. If something doesn't match exactly, look for the
closest equivalent — the overall flow (Page → App → permissions → token) has
stayed the same even when the UI around it changes.

**One important reassurance:** you'll see mentions online of Meta's "App
Review" process taking 2-4 weeks. That process is for apps that need to
publish on behalf of *other people's* Instagram accounts (think: a SaaS
scheduling tool with many customers). Since this app only ever posts to
**your own** account, you add yourself as a tester/role on your own app and
you can use the publish permissions immediately in Development Mode —
no review, no waiting. If your specific app dashboard ever shows a
permission as unavailable without review, that's the one exception to check
for, but it's not the default case for a single personal account.

---

## 1. Convert Instagram to a Professional Account

1. Open Instagram on your phone
2. Go to your Profile → Tap the ☰ menu (top right)
3. Tap **Settings and privacy**
4. Tap **Account type and tools**
5. Tap **Switch to professional account**
6. Choose **Creator** or **Business** (either works)
7. Select a category (e.g., "Motivational/Self Improvement")
8. Complete the setup

---

## 2. Create a Facebook Page

Instagram's publishing API requires a linked Facebook Page — this is a hard
requirement from Meta, not optional, regardless of which account type you chose above.

1. Go to **https://www.facebook.com/pages/create**
2. Choose **Community or public figure** (or whatever option is closest — Facebook renames these occasionally)
3. Fill in the page name (e.g., "Your Motivation Page")
4. Skip all optional setup steps
5. Your Facebook Page is created!

---

## 3. Link Instagram to Facebook Page

1. On Instagram: Profile → Settings → **Accounts Center** (Meta now centralizes
   this here — it may also be labeled "Linked accounts" depending on your app version)
2. Tap **Add accounts** and link your Facebook account/Page
3. OR go to your Facebook Page → **Settings** → **Instagram** → **Connect account**
4. Confirm the link succeeded: on the Facebook Page, Settings should now show
   your Instagram username as connected

---

## 4. Create a Meta Developer App

1. Go to **https://developers.facebook.com**
2. Log in with your Facebook account
3. Click **My Apps** (top right) → **Create App**
4. Give it a name (e.g. `InstaAutoPoster`) and your contact email
5. When asked what you're building / which use case, choose the option
   related to **Instagram** content publishing / business use — the exact
   wording varies, pick the closest match to "post content to Instagram"
6. Click through to **Create app**
7. On your app's dashboard, make sure your Facebook Page (and the Instagram
   account linked to it) is added as an asset the app can access — usually
   under **App Roles** or a "Business Assets" section prompted during setup

---

## 5. Get Permissions and a Long-Lived Access Token

This is the one step worth doing carefully, since it's easy to end up with
a token that has the wrong permissions and doesn't actually work for publishing.

1. Go to **https://developers.facebook.com/tools/explorer** (Graph API Explorer)
2. Select your app from the top-right dropdown
3. Click **Generate Access Token** and log in as yourself if prompted
4. In the permissions box, add these specific permissions (current names as of 2026 —
   if you see slightly different names, look for ones matching "content publish",
   "basic", "insights", and "comments"):
   - `instagram_business_basic`
   - `instagram_business_content_publish`
   - `instagram_business_manage_comments` (used later for reading comments into your dashboard)
   - `instagram_business_manage_insights` (used later for post analytics)
   - `pages_show_list`
   - `pages_read_engagement`
5. Click **Generate Access Token** again and approve the permissions
6. Copy the short-lived token that appears

### Exchange it for a long-lived token (lasts ~60 days instead of ~1 hour)

7. You'll need your **App ID** and **App Secret** — both are on your app's
   dashboard under **App Settings → Basic**
8. Open this URL in your browser, with your own values substituted in:
```
https://graph.facebook.com/v25.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=YOUR_SHORT_TOKEN
```
9. You'll get back a JSON response with a new `access_token` — this is your
   **long-lived token**
10. Save this as `IG_ACCESS_TOKEN` in GitHub Secrets

> **Remember:** this token expires in about 60 days. Set yourself a reminder
> to refresh it every ~55 days — a lapsed token is the single most common
> reason an automation like this quietly stops working.

---

## 6. Get Your Instagram Account ID

1. Open (with your long-lived token): `https://graph.facebook.com/v25.0/me/accounts?access_token=YOUR_TOKEN`
2. Find your Page's `id` in the response
3. Then open: `https://graph.facebook.com/v25.0/YOUR_PAGE_ID?fields=instagram_business_account&access_token=YOUR_TOKEN`
4. Copy the `id` value inside `instagram_business_account` — this is your `IG_ACCOUNT_ID`

If step 3 returns an empty result, the Page-to-Instagram link from Section 3
above didn't take — go back and reconnect them before continuing.

---

## 7. Add to GitHub Secrets

- `IG_ACCESS_TOKEN` = your long-lived token
- `IG_ACCOUNT_ID` = your Instagram Business Account ID

---

## ✅ You're Done with Meta Developer Setup!

Next: [Gemini API Setup →](04_gemini_api_setup.md)
