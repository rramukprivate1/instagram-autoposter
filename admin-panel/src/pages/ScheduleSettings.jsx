import React, { useState, useEffect } from 'react'
import { fetchSettings, updateSetting } from '../lib/supabase'

export default function ScheduleSettings() {
  const [loading, setLoading] = useState(true)
  const [postsPerDay, setPostsPerDay] = useState(2)
  const [autoPost, setAutoPost] = useState(false)
  const [customContext, setCustomContext] = useState('')
  const [igHandle, setIgHandle] = useState('@yourhandle')
  const [ctaText, setCtaText] = useState('')
  const [timezone, setTimezone] = useState('Asia/Kolkata')
  const [postingWindows, setPostingWindows] = useState([])
  const [jitterMinutes, setJitterMinutes] = useState(20)
  const [newWindowTime, setNewWindowTime] = useState('09:00')
  const [carouselProbability, setCarouselProbability] = useState(25)
  const [minSlides, setMinSlides] = useState(3)
  const [maxSlides, setMaxSlides] = useState(6)
  const [saved, setSaved] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    loadSettingsData()
  }, [])

  const loadSettingsData = async () => {
    setLoading(true)
    try {
      const settings = await fetchSettings()
      if (settings.posts_per_day) setPostsPerDay(parseInt(settings.posts_per_day))
      if (settings.auto_post) setAutoPost(settings.auto_post === 'true')
      if (settings.custom_context) setCustomContext(settings.custom_context)
      if (settings.ig_handle) setIgHandle(settings.ig_handle)
      if (settings.cta_text !== undefined) setCtaText(settings.cta_text)
      if (settings.timezone) setTimezone(settings.timezone)
      if (settings.posting_windows) {
        try { setPostingWindows(JSON.parse(settings.posting_windows)) }
        catch { setPostingWindows([]) }
      }
      if (settings.posting_time_jitter_minutes !== undefined) {
        setJitterMinutes(parseInt(settings.posting_time_jitter_minutes))
      }
      if (settings.carousel_probability) setCarouselProbability(Math.round(parseFloat(settings.carousel_probability) * 100))
      if (settings.carousel_min_slides) setMinSlides(parseInt(settings.carousel_min_slides))
      if (settings.carousel_max_slides) setMaxSlides(parseInt(settings.carousel_max_slides))
    } catch (err) {
      console.error('Error loading settings:', err)
    } finally {
      setLoading(false)
    }
  }

  const addWindow = () => {
    if (!newWindowTime || postingWindows.includes(newWindowTime)) return
    setPostingWindows([...postingWindows, newWindowTime].sort())
  }

  const removeWindow = (time) => {
    setPostingWindows(postingWindows.filter((t) => t !== time))
  }

  const spreadEvenly = () => {
    // Spreads postsPerDay windows between 8am and 10pm - a starting point,
    // not a requirement, you can still add/remove individual times after.
    const startMin = 8 * 60
    const endMin = 22 * 60
    const count = Math.max(1, postsPerDay)
    const step = count > 1 ? (endMin - startMin) / (count - 1) : 0
    const windows = Array.from({ length: count }, (_, i) => {
      const total = Math.round(startMin + step * i)
      const h = String(Math.floor(total / 60)).padStart(2, '0')
      const m = String(total % 60).padStart(2, '0')
      return `${h}:${m}`
    })
    setPostingWindows([...new Set(windows)].sort())
  }

  const handleSave = async (e) => {
    e.preventDefault()
    setSaving(true)
    setSaved(false)
    try {
      await Promise.all([
        updateSetting('posts_per_day', postsPerDay.toString()),
        updateSetting('auto_post', autoPost.toString()),
        updateSetting('custom_context', customContext),
        updateSetting('ig_handle', igHandle),
        updateSetting('cta_text', ctaText),
        updateSetting('timezone', timezone),
        updateSetting('posting_windows', JSON.stringify(postingWindows)),
        updateSetting('posting_time_jitter_minutes', jitterMinutes.toString()),
        updateSetting('carousel_probability', (carouselProbability / 100).toString()),
        updateSetting('carousel_min_slides', minSlides.toString()),
        updateSetting('carousel_max_slides', maxSlides.toString()),
      ])
      setSaved(true)
      setTimeout(() => setSaved(false), 3000)
    } catch (err) {
      alert('Error saving settings: ' + err.message)
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="loading-screen"><div className="loading-spinner" /><p>Loading Settings...</p></div>

  return (
    <div>
      <div className="page-header">
        <div>
          <h1>Schedule & Global Settings</h1>
          <p>Control post frequency, approval mode, and AI context</p>
        </div>
      </div>

      {saved && <div className="alert alert-success">✅ Settings updated successfully!</div>}

      <form onSubmit={handleSave}>
        {/* Posts per day slider */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>📊 Daily Post Target</h2>
          <p className="text-sm text-muted mb-6">
            Start low (2-3/day) for new accounts to warm up with Instagram anti-spam algorithms, then scale up.
          </p>

          <div className="slider-wrapper">
            <div className="slider-row">
              <input
                type="range"
                min="1"
                max="10"
                value={postsPerDay}
                onChange={(e) => setPostsPerDay(parseInt(e.target.value))}
                className="slider"
              />
              <span className="slider-value">{postsPerDay} / day</span>
            </div>
          </div>
          <button type="button" className="btn btn-secondary" style={{ marginTop: 12 }} onClick={spreadEvenly}>
            ↻ Spread {postsPerDay} times evenly into Posting Times below
          </button>
        </div>

        {/* Posting Time Windows */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>🗓️ Posting Times</h2>
          <p className="text-sm text-muted mb-4">
            The exact clock times a post is allowed to go out. The generator checks every 15 minutes
            and only creates a post when it&apos;s close to one of these times - add, remove, or retime
            these whenever you want without touching any code.
          </p>

          <div className="form-group mb-4">
            <label className="form-label">Timezone (IANA name)</label>
            <input
              type="text"
              className="form-input"
              value={timezone}
              onChange={(e) => setTimezone(e.target.value)}
              placeholder="Asia/Kolkata"
            />
          </div>

          <div className="tag-list mb-4">
            {postingWindows.length === 0 && <p className="text-sm text-muted">No posting times set yet.</p>}
            {postingWindows.map((time) => (
              <span key={time} className="tag-pill">
                {time}
                <button type="button" onClick={() => removeWindow(time)} aria-label={`Remove ${time}`}>×</button>
              </span>
            ))}
          </div>

          <div className="slider-row">
            <input
              type="time"
              className="form-input"
              value={newWindowTime}
              onChange={(e) => setNewWindowTime(e.target.value)}
            />
            <button type="button" className="btn btn-secondary" onClick={addWindow}>+ Add time</button>
          </div>

          <div className="form-group mt-4">
            <label className="form-label">Randomize each time by up to (minutes)</label>
            <div className="slider-row">
              <input
                type="range"
                min="0"
                max="45"
                step="5"
                value={jitterMinutes}
                onChange={(e) => setJitterMinutes(parseInt(e.target.value))}
                className="slider"
              />
              <span className="slider-value">
                {jitterMinutes === 0 ? 'Off - exact times' : `± ${jitterMinutes} min`}
              </span>
            </div>
            <p className="text-sm text-muted mt-2">
              Posting at the exact same minute every single day is a mechanical pattern.
              This shifts each time by a different random amount each day (e.g. 08:00 might
              land at 07:44 today, 08:19 tomorrow) so the schedule doesn't look automated.
            </p>
          </div>
        </div>

        {/* Carousel / Sequence Posts */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>🎠 Carousel / Sequence Posts</h2>
          <p className="text-sm text-muted mb-6">
            A carousel is one post with several swipeable slides on the same topic (e.g. &quot;5 signs you need
            rest&quot;). These tend to get more time-on-post than a single image, which genuinely helps reach -
            this is a legitimate Instagram-native format, not a workaround.
          </p>

          <div className="slider-wrapper mb-4">
            <div className="slider-row">
              <input
                type="range"
                min="0"
                max="100"
                step="5"
                value={carouselProbability}
                onChange={(e) => setCarouselProbability(parseInt(e.target.value))}
                className="slider"
              />
              <span className="slider-value">{carouselProbability}% of posts</span>
            </div>
          </div>

          <div className="slider-row">
            <div className="form-group">
              <label className="form-label">Min slides</label>
              <input type="number" min="2" max="10" className="form-input" value={minSlides}
                     onChange={(e) => setMinSlides(parseInt(e.target.value))} />
            </div>
            <div className="form-group">
              <label className="form-label">Max slides</label>
              <input type="number" min="2" max="10" className="form-input" value={maxSlides}
                     onChange={(e) => setMaxSlides(parseInt(e.target.value))} />
            </div>
          </div>
          <p className="text-sm text-muted mt-2">
            Turn this off for a specific topic from the Topics page if a short/punchy topic never suits a multi-slide series.
          </p>
        </div>

        {/* Approval Mode Toggle */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>🛡️ Posting & Approval Mode</h2>
          <p className="text-sm text-muted mb-6">
            Choose whether posts require your explicit manual email approval before going live on Instagram.
          </p>

          <div className="toggle-wrapper">
            <label className="toggle">
              <input
                type="checkbox"
                checked={autoPost}
                onChange={(e) => setAutoPost(e.target.checked)}
              />
              <span className="toggle-track"><span className="toggle-thumb" /></span>
            </label>
            <div>
              <div style={{ fontWeight: 600 }}>{autoPost ? '⚡ Automatic Posting (No Email Approval)' : '📧 Manual Email Approval Required'}</div>
              <div className="text-sm text-muted">
                {autoPost
                  ? 'Posts will publish directly to Instagram as soon as they are generated.'
                  : 'You will receive an email preview with Approve/Reject buttons for every generated post.'}
              </div>
            </div>
          </div>
        </div>

        {/* Global AI Context Input */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>🧠 Global System Prompt Context</h2>
          <p className="text-sm text-muted mb-4">
            Add any overarching instruction, mood, or context that will be injected into every post generation prompt.
          </p>

          <div className="form-group">
            <label className="form-label">Custom Context / Style Guide</label>
            <textarea
              className="form-textarea"
              rows={4}
              value={customContext}
              onChange={(e) => setCustomContext(e.target.value)}
              placeholder="e.g. Focus heavily on mindset shifts for college students and young professionals. Keep tone relatable and avoid toxic positivity."
            />
          </div>
        </div>

        {/* Watermark Handle */}
        <div className="card mb-6">
          <h2 style={{ fontSize: 18, fontWeight: 700, marginBottom: 8 }}>🏷️ Instagram Handle / Watermark</h2>
          <div className="form-group mb-4">
            <label className="form-label">Handle (Shown on card footer)</label>
            <input
              type="text"
              className="form-input"
              value={igHandle}
              onChange={(e) => setIgHandle(e.target.value)}
              placeholder="@yourhandle"
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">Caption CTA (optional, appended to every caption)</label>
            <input
              type="text"
              className="form-input"
              value={ctaText}
              onChange={(e) => setCtaText(e.target.value)}
              placeholder="🔗 Link in bio for more"
            />
            <p className="text-sm text-muted mt-2">Leave blank to skip. Useful once you have a link-in-bio page to send people to.</p>
          </div>
        </div>

        <button type="submit" className="btn btn-primary btn-lg" disabled={saving}>
          {saving ? 'Saving...' : '💾 Save Settings'}
        </button>
      </form>
    </div>
  )
}
