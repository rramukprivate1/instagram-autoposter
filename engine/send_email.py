"""
send_email.py
Sends a post preview email with Approve and Reject buttons
using the Resend API.
"""
import resend
import logging
from config import RESEND_API_KEY, RESEND_FROM_EMAIL, APPROVAL_TO_EMAIL, APP_BASE_URL

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

resend.api_key = RESEND_API_KEY


def build_email_html(post: dict) -> str:
    """Generates the HTML body for the approval email."""
    approve_url = f"{APP_BASE_URL}/api/approve?id={post['id']}&action=approve&token={post['approval_token']}"
    reject_url = f"{APP_BASE_URL}/api/approve?id={post['id']}&action=reject&token={post['approval_token']}"
    image_url = post.get("image_url", "")
    quote = post.get("quote", "")
    caption = post.get("caption", "")
    hashtags = " ".join([f"#{tag}" for tag in post.get("hashtags", [])])
    topic = post.get("topic_name", "Unknown")
    tone = post.get("tone_name", "Unknown")

    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>New Instagram Post Ready for Approval</title>
    </head>
    <body style="margin:0;padding:0;background:#0d0d0d;font-family:'Segoe UI',Helvetica,Arial,sans-serif;color:#f0f0f0;">
      <div style="max-width:600px;margin:0 auto;padding:40px 20px;">

        <!-- Header -->
        <div style="text-align:center;margin-bottom:32px;">
          <h1 style="font-size:28px;font-weight:700;color:#fff;margin:0;">📸 Post Ready for Review</h1>
          <p style="color:#888;margin-top:8px;font-size:14px;">Your Instagram auto-poster has generated a new post</p>
        </div>

        <!-- Image Preview -->
        {'<img src="' + image_url + '" alt="Quote Card" style="width:100%;border-radius:16px;display:block;margin-bottom:24px;">' if image_url else '<div style="background:#1a1a1a;border-radius:16px;padding:40px;text-align:center;color:#888;">Image preview not available</div>'}

        <!-- Quote -->
        <div style="background:#111;border-left:4px solid #7c3aed;padding:20px 24px;border-radius:0 12px 12px 0;margin-bottom:20px;">
          <p style="font-size:20px;font-style:italic;color:#fff;margin:0;line-height:1.5;">&ldquo;{quote}&rdquo;</p>
        </div>

        <!-- Meta Info -->
        <div style="display:flex;gap:12px;margin-bottom:20px;flex-wrap:wrap;">
          <span style="background:#1a1a2e;color:#818cf8;padding:6px 14px;border-radius:20px;font-size:13px;">📂 {topic}</span>
          <span style="background:#1a1a2e;color:#34d399;padding:6px 14px;border-radius:20px;font-size:13px;">🎭 {tone}</span>
        </div>

        <!-- Caption -->
        <div style="margin-bottom:16px;">
          <p style="font-size:12px;color:#666;margin-bottom:4px;text-transform:uppercase;letter-spacing:1px;">Caption</p>
          <p style="font-size:15px;color:#d1d5db;margin:0;">{caption}</p>
        </div>

        <!-- Hashtags -->
        <div style="margin-bottom:32px;">
          <p style="font-size:12px;color:#666;margin-bottom:4px;text-transform:uppercase;letter-spacing:1px;">Hashtags</p>
          <p style="font-size:13px;color:#7c3aed;margin:0;">{hashtags}</p>
        </div>

        <!-- Approve / Reject Buttons -->
        <div style="display:flex;gap:16px;justify-content:center;margin-bottom:40px;">
          <a href="{approve_url}" style="display:inline-block;background:#16a34a;color:#fff;padding:16px 36px;border-radius:12px;font-size:18px;font-weight:700;text-decoration:none;">✅ Approve & Schedule</a>
          <a href="{reject_url}" style="display:inline-block;background:#dc2626;color:#fff;padding:16px 36px;border-radius:12px;font-size:18px;font-weight:700;text-decoration:none;">❌ Reject</a>
        </div>

        <!-- Footer -->
        <div style="text-align:center;border-top:1px solid #222;padding-top:24px;">
          <p style="font-size:12px;color:#555;margin:0;">Instagram Auto-Poster &bull; This link is single-use and secure.</p>
        </div>
      </div>
    </body>
    </html>
    """


def send_approval_email(post: dict) -> bool:
    """
    Sends the approval email for a given post dict.
    Returns True on success, False on failure.
    """
    try:
        html = build_email_html(post)
        result = resend.Emails.send({
            "from": RESEND_FROM_EMAIL,
            "to": APPROVAL_TO_EMAIL,
            "subject": f"📸 New Post Ready: {post.get('quote', '')[:40]}...",
            "html": html
        })
        logger.info(f"Approval email sent. ID: {result.get('id', 'unknown')}")
        return True
    except Exception as e:
        logger.error(f"Failed to send approval email: {e}")
        return False
