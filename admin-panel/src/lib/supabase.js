import { createClient } from '@supabase/supabase-js'

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL || 'https://placeholder.supabase.co'
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY || 'placeholder'

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
