import React, { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { fetchPosts, fetchTopics, fetchTones, fetchSettings, updatePostStatus } from '../lib/supabase'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({ pending: 0, approved: 0, published: 0, topics: 0 })
  const [pendingPosts, setPendingPosts] = useState([])
  const [recentPublished, setRecentPublished] = useState([])
  const [settings, setSettings] = useState({})

  useEffect(() => {
    loadDashboardData()
  }, [])

  const loadDashboardData = async () => {
    setLoading(true)
    try {
      const [allPostsRes, topicsRes, settingsRes] = await Promise.all([
        fetchPosts(null, 100),
        fetchTopics(),
        fetchSettings()
      ])

      const posts = allPostsRes.data || []
      const topics = topicsRes.data || []

      const pending = posts.filter(p => p.status === 'pending')
      const approved = posts.filter(p => p.status === 'approved')
      const published = posts.filter(p => p.status === 'published')

      setStats({
        pending: pending.length,
        approved: approved.length,
        published: published.length,
        topics: topics.filter(t => t.is_active).length
      })

      setPendingPosts(pending.slice(0, 3))
      setRecentPublished(published.slice(0, 5))
      setSettings(settingsRes || {})
    } catch (err) {
      console.error('Error loading dashboard data:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleAction = async (id, status) => {
    await updatePostStatus(id, status)
    loadDashboardData()
  }

  if (loading) {
    return (
      <div className="loading-screen">
        <div className="loading-spinner" />
        <p>Loading Dashboard...</p>
      </div>
    )
  }

  return (
    <div>
      {/* Header */}
      <div className="page-header">
        <div>
          <h1>Dashboard Overview</h1>
          <p>Real-time automation status & queue metrics</p>
        </div>
        <Link to="/queue" className="btn btn-primary">
          📋 Review Queue ({stats.pending})
        </Link>
      </div>

      {/* Stats Grid */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Pending Approval</div>
          <div className="stat-value" style={{ color: 'var(--color-warning)' }}>{stats.pending}</div>
          <div className="stat-icon">⏳</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Approved & Ready</div>
          <div className="stat-value" style={{ color: 'var(--color-success)' }}>{stats.approved}</div>
          <div className="stat-icon">✅</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Published Posts</div>
          <div className="stat-value" style={{ color: 'var(--color-info)' }}>{stats.published}</div>
          <div className="stat-icon">🚀</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Active Topics</div>
          <div className="stat-value">{stats.topics}</div>
          <div className="stat-icon">🏷️</div>
        </div>
      </div>

      {/* System Banner */}
      <div className="card mb-8" style={{ background: 'linear-gradient(135deg, rgba(124,58,237,0.15), rgba(15,15,26,0.9))', borderColor: 'var(--color-primary)' }}>
        <div className="flex items-center justify-between flex-wrap gap-4">
          <div>
            <h3 style={{ fontSize: 16, fontWeight: 700, marginBottom: 4 }}>⚙️ Current Automation Rules</h3>
            <p className="text-sm text-muted">
              Frequency: <strong style={{ color: '#fff' }}>{settings.posts_per_day || '2'} posts/day</strong> &bull;
              Approval Mode: <strong style={{ color: '#fff' }}>{settings.auto_post === 'true' ? 'Auto-Publish' : 'Manual Email Approval'}</strong> &bull;
              Watermark: <strong style={{ color: '#fff' }}>{settings.ig_handle || '@yourhandle'}</strong>
            </p>
          </div>
          <Link to="/schedule" className="btn btn-secondary btn-sm">
            Configure Rules →
          </Link>
        </div>
      </div>

      {/* Pending Posts Requiring Action */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 style={{ fontSize: 18, fontWeight: 700 }}>⚠️ Posts Awaiting Your Approval</h2>
          {pendingPosts.length > 0 && <Link to="/queue" className="text-sm text-accent">View all ({stats.pending}) →</Link>}
        </div>

        {pendingPosts.length === 0 ? (
          <div className="card empty-state" style={{ padding: '32px' }}>
            <p>🎉 All caught up! No pending posts requiring manual review.</p>
          </div>
        ) : (
          <div className="post-grid">
            {pendingPosts.map((post) => (
              <div key={post.id} className="post-card">
                {post.image_url && <img src={post.image_url} alt="Quote Preview" className="post-card-image" />}
                <div className="post-card-body">
                  <p className="post-card-quote">&ldquo;{post.quote}&rdquo;</p>
                  <div className="post-card-meta">
                    <span className="badge badge-pending">Pending</span>
                    {post.topics && <span className="badge badge-inactive">{post.topics.emoji} {post.topics.name}</span>}
                  </div>
                  <div className="post-card-actions">
                    <button className="btn btn-success btn-sm" onClick={() => handleAction(post.id, 'approved')}>
                      ✅ Approve
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleAction(post.id, 'rejected')}>
                      ❌ Reject
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Recent Published History */}
      <div>
        <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 16 }}>📜 Recently Published</h2>
        {recentPublished.length === 0 ? (
          <div className="card empty-state" style={{ padding: '32px' }}>
            <p>No published posts yet. Run your first workflow to get started!</p>
          </div>
        ) : (
          <div className="table-wrapper">
            <table>
              <thead>
                <tr>
                  <th>Quote</th>
                  <th>Topic</th>
                  <th>Published At</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {recentPublished.map((post) => (
                  <tr key={post.id}>
                    <td>&ldquo;{post.quote}&rdquo;</td>
                    <td>{post.topics?.emoji} {post.topics?.name || 'General'}</td>
                    <td>{new Date(post.published_at || post.created_at).toLocaleString()}</td>
                    <td><span className="badge badge-published">Published</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
