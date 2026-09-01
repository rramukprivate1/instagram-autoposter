import React, { useState, useEffect, useCallback } from 'react'
import { fetchPosts, updatePostStatus, fetchPostSlides, deleteSlide } from '../lib/supabase'

export default function PostQueue() {
  const [posts, setPosts] = useState([])
  const [filter, setFilter] = useState('all')
  const [loading, setLoading] = useState(true)
  const [slidesByPost, setSlidesByPost] = useState({})   // { [postId]: [slideRow, ...] }
  const [slideIndexByPost, setSlideIndexByPost] = useState({})  // { [postId]: currentIndex }

  const loadPosts = useCallback(async () => {
    setLoading(true)
    const statusFilter = filter === 'all' ? null : filter
    const { data } = await fetchPosts(statusFilter, 60)
    setPosts(data || [])
    setLoading(false)

    const carouselPosts = (data || []).filter((p) => p.post_format === 'carousel')
    const slideResults = await Promise.all(
      carouselPosts.map((p) => fetchPostSlides(p.id).then((r) => [p.id, r.data || []]))
    )
    setSlidesByPost(Object.fromEntries(slideResults))
  }, [filter])

  useEffect(() => {
    loadPosts()
  }, [loadPosts])

  const handleAction = async (id, status) => {
    await updatePostStatus(id, status)
    loadPosts()
  }

  const goToSlide = (postId, index) => {
    setSlideIndexByPost((prev) => ({ ...prev, [postId]: index }))
  }

  const handleRemoveSlide = async (postId, slide) => {
    const remaining = slidesByPost[postId] || []
    if (remaining.length <= 2) {
      alert('A carousel needs at least 2 slides - reject the whole post instead if none of it works.')
      return
    }
    if (!window.confirm('Remove this slide from the carousel? This can\'t be undone.')) return
    await deleteSlide(slide.id)
    const updated = remaining.filter((s) => s.id !== slide.id)
    setSlidesByPost((prev) => ({ ...prev, [postId]: updated }))
    setSlideIndexByPost((prev) => ({ ...prev, [postId]: 0 }))
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
          <p>No posts matching filter &quot;{filter}&quot;. Trigger a generation run from GitHub Actions to create posts.</p>
        </div>
      ) : (
        <div className="post-grid">
          {posts.map((post) => {
            const isCarousel = post.post_format === 'carousel'
            const slides = slidesByPost[post.id] || []
            const currentIndex = slideIndexByPost[post.id] || 0
            const currentSlide = isCarousel ? slides[currentIndex] : null
            const displayImageUrl = isCarousel ? (currentSlide?.image_url || post.image_url) : post.image_url

            return (
              <div key={post.id} className="post-card">
                {displayImageUrl ? (
                  <div style={{ position: 'relative' }}>
                    <img src={displayImageUrl} alt="Quote Card" className="post-card-image" />

                    {isCarousel && slides.length > 1 && (
                      <>
                        <button
                          type="button"
                          onClick={() => goToSlide(post.id, (currentIndex - 1 + slides.length) % slides.length)}
                          aria-label="Previous slide"
                          className="carousel-nav-btn carousel-nav-prev"
                        >
                          ‹
                        </button>
                        <button
                          type="button"
                          onClick={() => goToSlide(post.id, (currentIndex + 1) % slides.length)}
                          aria-label="Next slide"
                          className="carousel-nav-btn carousel-nav-next"
                        >
                          ›
                        </button>

                        <div className="carousel-dots">
                          {slides.map((s, i) => (
                            <button
                              key={s.id}
                              type="button"
                              onClick={() => goToSlide(post.id, i)}
                              aria-label={`Go to slide ${i + 1}`}
                              className={`carousel-dot ${i === currentIndex ? 'carousel-dot-active' : ''}`}
                            />
                          ))}
                        </div>

                        {post.status === 'pending' && (
                          <button
                            type="button"
                            className="carousel-remove-btn"
                            onClick={() => handleRemoveSlide(post.id, currentSlide)}
                            title="Remove this slide from the carousel"
                          >
                            🗑 Remove slide {currentIndex + 1} of {slides.length}
                          </button>
                        )}
                      </>
                    )}
                  </div>
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

                {post.status === 'publish_failed' && post.error_message && (
                  <p className="text-sm mt-2" style={{ color: '#f87171' }}>
                    ⚠️ {post.error_message}
                  </p>
                )}

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
            )
          })}
        </div>
      )}
    </div>
  )
}
