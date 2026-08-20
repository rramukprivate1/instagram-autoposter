import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY

if (!supabaseUrl || !supabaseAnonKey) {
  // Fails loudly instead of silently falling back to a placeholder value -
  // an invalid key used to cause a confusing JSON parse error deep inside
  // the Supabase SDK instead of a clear message. If you see this screen,
  // it means these two variables weren't available when Vercel BUILT this
  // app. Fix: Vercel dashboard -> Project Settings -> Environment Variables
  // -> confirm both exist with no typos -> then trigger a fresh deploy
  // (Deployments -> ... menu -> Redeploy). Vite bakes these in at build
  // time, so adding/editing them alone does not update an already-built
  // deployment - it only affects the NEXT build.
  document.body.innerHTML = `
    <div style="font-family:ui-monospace,monospace;background:#150505;color:#ff8a8a;
      padding:48px;min-height:100vh;box-sizing:border-box;line-height:1.6;">
      <h1 style="color:#fff;">Missing Supabase configuration</h1>
      <p>VITE_SUPABASE_URL and/or VITE_SUPABASE_ANON_KEY were not set when this app was built.</p>
      <p><strong>Fix:</strong> Vercel dashboard &rarr; Project Settings &rarr; Environment Variables
      &rarr; confirm both are set correctly &rarr; then Deployments &rarr; (latest) &rarr; &hellip;
      &rarr; Redeploy. These are baked in at build time, so simply adding them isn't enough -
      the next deploy after adding them is what actually picks them up.</p>
    </div>`
  throw new Error('Missing VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY at build time')
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// ── Auth helpers ──────────────────────────────────────────────────────────────

export const signIn = (email, password) =>
  supabase.auth.signInWithPassword({ email, password })

export const signOut = () => supabase.auth.signOut()

export const getSession = () => supabase.auth.getSession()

// ── Topics ────────────────────────────────────────────────────────────────────

export const fetchTopics = () =>
  supabase.from('topics').select('*').order('name')

export const createTopic = (data) =>
  supabase.from('topics').insert(data).select().single()

export const updateTopic = (id, data) =>
  supabase.from('topics').update(data).eq('id', id).select().single()

export const deleteTopic = (id) =>
  supabase.from('topics').delete().eq('id', id)

// ── Tones ─────────────────────────────────────────────────────────────────────

export const fetchTones = () =>
  supabase.from('tones').select('*').order('name')

export const createTone = (data) =>
  supabase.from('tones').insert(data).select().single()

export const updateTone = (id, data) =>
  supabase.from('tones').update(data).eq('id', id).select().single()

export const deleteTone = (id) =>
  supabase.from('tones').delete().eq('id', id)

// ── Posts ─────────────────────────────────────────────────────────────────────

export const fetchPosts = (status = null, limit = 50) => {
  let query = supabase
    .from('posts')
    .select(`*, topics(name, emoji), tones(name)`)
    .order('created_at', { ascending: false })
    .limit(limit)
  if (status) query = query.eq('status', status)
  return query
}

export const updatePostStatus = (id, status) =>
  supabase.from('posts').update({ status }).eq('id', id)

// ── Carousel slides ───────────────────────────────────────────────────────────

export const fetchPostSlides = (postId) =>
  supabase.from('post_slides').select('*').eq('post_id', postId).order('slide_index')

export const deleteSlide = (slideId) =>
  supabase.from('post_slides').delete().eq('id', slideId)

// ── Logo upload ───────────────────────────────────────────────────────────────
// Reuses the existing post-images bucket under a logos/ prefix, rather than
// requiring a brand-new bucket with its own storage policies.

export const uploadLogo = async (file) => {
  const ext = file.name.split('.').pop()
  const path = `logos/brand-logo-${Date.now()}.${ext}`
  const { error } = await supabase.storage.from('post-images').upload(path, file, { upsert: true })
  if (error) throw error
  const { data } = supabase.storage.from('post-images').getPublicUrl(path)
  return data.publicUrl
}

// ── Settings ──────────────────────────────────────────────────────────────────

export const fetchSettings = async () => {
  const { data, error } = await supabase.from('settings').select('*')
  if (error) throw error
  return Object.fromEntries(data.map((row) => [row.key, row.value]))
}

export const updateSetting = (key, value) =>
  supabase.from('settings').update({ value }).eq('key', key)

// ── Logs ──────────────────────────────────────────────────────────────────────

export const fetchLogs = (limit = 30) =>
  supabase.from('logs').select('*').order('created_at', { ascending: false }).limit(limit)
