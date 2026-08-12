# Step 5: Resend Email Setup

> **Time required:** ~10 minutes  
> **Difficulty:** Easy  
> **Cost:** Free tier available, no credit card required — check current limits
> at **https://resend.com/pricing**, as free-tier numbers across API providers
> shift over time. This project sends only a handful of emails a day either way.

## What is Resend?

Resend is an email delivery service. It sends you the post approval email
with the beautiful preview image and the Approve/Reject buttons.

---

## 1. Create a Resend Account

1. Go to **https://resend.com**
2. Click **Get started for free**
3. Sign up with your email or GitHub account
4. Verify your email address

---

## 2. Get Your API Key

1. In the Resend dashboard, click **API Keys** (left sidebar)
2. Click **Create API Key**
3. Name it: `instagram-autoposter`
4. Permission: **Full access**
5. Click **Add** — copy the API key immediately!

---

## 3. Set Up a Sender Domain (Two Options)

### Option A: Use Resend's free test domain (easiest, no setup needed)
You can send from `onboarding@resend.dev` for testing.
- `RESEND_FROM_EMAIL` = `onboarding@resend.dev`
- **Limitation:** Can only send to the email address you registered with on Resend.
  This is perfect for personal use where only you receive the approval emails!

### Option B: Use your own domain (if you have one)
1. In Resend dashboard, click **Domains** → **Add domain**
2. Follow the DNS setup instructions (add the provided DNS records to your domain provider)
3. Once verified, you can send from `anything@yourdomain.com`

**For beginners: Use Option A to start. It works perfectly for this project.**

---

## 4. Add to GitHub Secrets

- `RESEND_API_KEY` = your API key from Step 2
- `RESEND_FROM_EMAIL` = `onboarding@resend.dev` (Option A) or your domain email (Option B)
- `APPROVAL_TO_EMAIL` = your personal email address (where you want to receive approvals)

---

## ✅ You're Done with Resend Setup!

Next: [Deployment Guide →](06_deployment_guide.md)
