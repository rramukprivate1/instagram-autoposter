import React, { useState, useEffect } from 'react'
import { fetchPosts, updatePostStatus } from '../lib/supabase'

export default function PostQueue() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadPosts()
  }, [filter])

  const loadPosts = async () => {
    setLoading(true)
    const statusFilter = filter === 'all' ? null : filter
    const { data } = await fetchPosts(statusFilter, 60)
    setPosts(data || [])
    setLoading(false)
  }

  const handleAction = async (id, status) => {
    await updatePostStatus(id, status)
    loadPosts()
  }

  const getStatusBadge = (status) => {
    switch (status) {
      case 'pending':   return <span className="badge badge-pending">Pending</span>
      case 'approved':  return <span className="badge badge-approved">Approved</span>
      case 'published': return <span className="badge badge-published">Published</span>
      case 'rejected':  return <span className="badge badge-rejected">Rejected</span>
      default:          return <span className="badge badge-inactive">{status}</span>
    }
  }

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading Queue...</p></div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Post Queue & Review</h1>
          <p>Review generated posts, manually approve/reject, or inspect published history</p>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="flex gap-2 mb-6" style={{ overflowX: 'auto', paddingBottom: 4 }}>
        {['all', 'pending', 'approved', 'published', 'rejected'].map((status) => (
          <button
            key={status}
            className={`btn ${filter === status ? 'btn-primary' : 'btn-secondary'} btn-sm`}
            onClick={() => setFilter(status)}
            style={{ textTransform: 'capitalize' }}
          >
            {status}
          </button>
        ))}
      </div>

      {posts.length === 0 ? (
        <div className="card empty-state">
          <div className="empty-icon">📭</div>
          <h3>No posts found</h3>
          <p>No posts matching filter "{filter}". Trigger a generation run from GitHub Actions to create posts.</p>
        </div>
      ) : (
        <div className="post-grid">
          {posts.map((post) => (
            <div key={post.id} className="post-card">
              {post.image_url ? (
                <img src={post.image_url} alt="Quote Card" className="post-card-image" />
              ) : (
                <div className="post-card-image flex items-center justify-center text-muted" style={{ background: '#111' }}>
                  No Image Preview
                </div>
              )}

              <div className="post-card-body">
                <p className="post-card-quote">&ldquo;{post.quote}&rdquo;</p>
                <p className="text-sm text-muted mb-3" style={{ fontSize: 12 }}>{post.caption}</p>

                <div className="post-card-meta">
                  {getStatusBadge(post.status)}
                  {post.topics && <span className="badge badge-inactive">{post.topics.emoji} {post.topics.name}</span>}
                  {post.tones && <span className="badge badge-inactive">🎭 {post.tones.name}</span>}
                </div>

                {post.status === 'pending' && (
                  <div className="post-card-actions">
                    <button className="btn btn-success btn-sm" onClick={() => handleAction(post.id, 'approved')}>
                      ✅ Approve
                    </button>
                    <button className="btn btn-danger btn-sm" onClick={() => handleAction(post.id, 'rejected')}>
                      ❌ Reject
                    </button>
                  </div>
                )}

                {post.status === 'approved' && (
                  <div className="text-sm text-accent" style={{ textAlign: 'center', fontWeight: 600 }}>
                    ⏰ Ready for next publish cycle
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
