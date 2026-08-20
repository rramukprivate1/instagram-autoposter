/**
 * api/approve.js
 * Vercel Serverless Function
 * Handles the Approve / Reject click from the email notification.
 * 
 * URL: /api/approve?id=POST_ID&action=approve|reject&token=SECRET_TOKEN
 */

const { createClient } = require('@supabase/supabase-js');

const supabase = createClient(
  process.env.SUPABASE_URL,
  process.env.SUPABASE_SERVICE_KEY
);

module.exports = async function handler(req, res) {
  const { id, action, token } = req.query;

  // Validate parameters
  if (!id || !action || !token) {
    return res.status(400).send(renderPage('❌ Invalid Request', 'Missing required parameters.', '#dc2626'));
  }

  if (!['approve', 'reject'].includes(action)) {
    return res.status(400).send(renderPage('❌ Invalid Action', 'Action must be approve or reject.', '#dc2626'));
  }

  try {
    // Fetch the post by ID and validate the token
    const { data: post, error } = await supabase
      .from('posts')
      .select('id, status, approval_token, quote')
      .eq('id', id)
      .single();

    if (error || !post) {
      return res.status(404).send(renderPage('❌ Post Not Found', 'This post does not exist.', '#dc2626'));
    }

    // Check token matches
    if (post.approval_token !== token) {
      return res.status(403).send(renderPage('🚫 Unauthorized', 'Invalid approval token.', '#dc2626'));
    }

    // Check if already actioned
    if (post.status !== 'pending') {
      return res.status(200).send(renderPage(
        '⚠️ Already Actioned',
        `This post has already been marked as "${post.status}". No changes made.`,
        '#f59e0b'
      ));
    }

    // Update status
    const newStatus = action === 'approve' ? 'approved' : 'rejected';
    await supabase
      .from('posts')
      .update({ status: newStatus })
      .eq('id', id);

    const isApprove = action === 'approve';
    return res.status(200).send(renderPage(
      isApprove ? '✅ Post Approved!' : '❌ Post Rejected',
      isApprove
        ? 'The post has been approved and will be published in the next scheduled run.'
        : 'The post has been rejected and will not be published.',
      isApprove ? '#16a34a' : '#dc2626',
      post.quote
    ));

  } catch (err) {
    console.error('Approve handler error:', err);
    return res.status(500).send(renderPage('💥 Server Error', 'Something went wrong. Try again later.', '#dc2626'));
  }
};

/**
 * Renders a clean HTML response page.
 */
function renderPage(title, message, accentColor, quote = '') {
  return `
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${title}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body {
      background: #0d0d0d;
      color: #f0f0f0;
      font-family: 'Segoe UI', Helvetica, Arial, sans-serif;
      min-height: 100vh;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 20px;
    }
    .card {
      max-width: 480px;
      width: 100%;
      background: #111;
      border-radius: 20px;
      border-top: 4px solid ${accentColor};
      padding: 48px 40px;
      text-align: center;
      box-shadow: 0 20px 60px rgba(0,0,0,0.5);
    }
    h1 { font-size: 32px; margin-bottom: 16px; color: ${accentColor}; }
    p { font-size: 16px; color: #9ca3af; line-height: 1.6; margin-bottom: 24px; }
    .quote {
      background: #1a1a1a;
      border-left: 3px solid ${accentColor};
      padding: 16px 20px;
      border-radius: 0 10px 10px 0;
      font-style: italic;
      color: #e5e7eb;
      margin-bottom: 32px;
      font-size: 15px;
      line-height: 1.6;
    }
    a {
      display: inline-block;
      background: ${accentColor};
      color: white;
      padding: 14px 28px;
      border-radius: 10px;
      text-decoration: none;
      font-weight: 600;
      font-size: 15px;
    }
    a:hover { opacity: 0.9; }
  </style>
</head>
<body>
  <div class="card">
    <h1>${title}</h1>
    <p>${message}</p>
    ${quote ? `<div class="quote">&ldquo;${quote}&rdquo;</div>` : ''}
    <a href="/">← Back to Dashboard</a>
  </div>
</body>
</html>
`;
}
