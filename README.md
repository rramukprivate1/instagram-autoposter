# 📸 Instagram Auto-Poster

A fully automated, AI-powered Instagram posting system with an Admin PWA dashboard.
Built 100% on free tiers — no credit card required.

## Features

- 🤖 **AI Content Generation** — Gemini 1.5 Flash generates original motivational quotes
- 🎨 **Image Renderer** — Python Pillow creates beautiful 1080x1080 dark-background quote cards
- 🧠 **Semantic Deduplication** — pgvector + sentence-transformers prevents duplicate content
- 📧 **Email Approvals** — Get a preview email with Approve/Reject buttons
- ⚙️ **Admin PWA** — Manage topics, tones, schedules, and post queue from your phone
- 🔄 **24/7 Automation** — GitHub Actions runs the pipeline every 2 hours, completely free
- 📲 **Official API** — Posts via the official Meta Graph API (no ban risk)

## Tech Stack

| Layer | Technology |
|-------|------------|
| Admin Panel | React + Vite + PWA (Vercel) |
| Database | Supabase (PostgreSQL + pgvector) |
| Auth | Supabase Auth |
| Storage | Supabase Storage |
| AI Engine | Google Gemini 1.5 Flash API |
| Image Renderer | Python + Pillow |
| Duplicate Check | sentence-transformers + pgvector |
| Scheduler | GitHub Actions (cron) |
| Notifications | Resend (email) |
| Publishing | Instagram Graph API |

## Getting Started

See the `docs/` folder for step-by-step setup guides:

1. [GitHub Setup](docs/01_github_setup.md)
2. [Supabase Setup](docs/02_supabase_setup.md)
3. [Meta Developer Setup](docs/03_meta_developer_setup.md)
4. [Gemini API Setup](docs/04_gemini_api_setup.md)
5. [Resend Email Setup](docs/05_resend_email_setup.md)
6. [Deployment Guide](docs/06_deployment_guide.md)

## Architecture

```
Admin PWA (React + Vite)         GitHub Actions (Cron)
  ├── Login (Supabase Auth)         ├── Generate Quote (Gemini API)
  ├── Topic Manager                 ├── Duplicate Check (pgvector)
  ├── Schedule Settings             ├── Render Image (Pillow)
  ├── Post Queue (Approve/Reject)   ├── Upload to Supabase Storage
  └── Analytics / Logs             ├── Send Approval Email (Resend)
                                   └── Publish to Instagram (Graph API)
```

## Important Notes

- **Never commit your `.env` file.** All secrets go in GitHub Actions Secrets.
- **Start with 2 posts/day** and gradually increase to avoid Instagram spam detection.
- **Keep the repo public** to use unlimited GitHub Actions minutes on the free tier.
- Instagram requires a **Business or Creator account** to use the Content Publishing API.

## Project for AI DevOps Portfolio

This project demonstrates:
- CI/CD with GitHub Actions
- AI integration (Gemini API, sentence-transformers)
- Vector databases (pgvector)
- Serverless functions (Vercel API routes)
- PWA development (React + Vite)
- Infrastructure as Code concepts
- Social media API integration (Meta Graph API)
