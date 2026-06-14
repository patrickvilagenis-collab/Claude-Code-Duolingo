// Capa de datos unificada. Abstrae el backend para que las vistas no sepan si
// están sobre Supabase (nube) o sobre localStorage (modo demo).
//
//   store.mode            → 'cloud' | 'demo'
//   store.getUser()       → { id, email, username, is_admin } | null
//   store.signUp/​signIn/​signOut
//   store.getProfile()    → { username, is_admin, xp, streak_days, ... }
//   store.getProgress()   → Map(lessonId → { status, score, attempts, completed_at })
//   store.completeLesson(lesson, passed) → { xpGained, newBadges }
//   store.getBadges()/​getActivity()/​getAdminStats()

import { supabase, isSupabaseConfigured } from './supabase.js'
import { getManifest } from './content.js'
import { evaluateBadges } from './gamification.js'

const mode = isSupabaseConfigured ? 'cloud' : 'demo'

function todayStr(d = new Date()) {
  return d.toISOString().slice(0, 10)
}

// Nueva racha a partir de la última fecha activa.
function nextStreak(prevStreak, lastActive) {
  const today = todayStr()
  if (!lastActive) return 1
  const last = lastActive.slice(0, 10)
  if (last === today) return prevStreak || 1 // ya practicó hoy
  const diff = (new Date(today) - new Date(last)) / 86400000
  return diff === 1 ? (prevStreak || 0) + 1 : 1 // consecutivo suma; hueco reinicia
}

// Construye el contexto que evalúan las insignias.
async function badgeContext(profile, progressMap) {
  const completed = new Set(
    [...progressMap.entries()].filter(([, p]) => p.status === 'completed').map(([id]) => id),
  )
  const manifest = await getManifest()
  const levelCompleted = {}
  for (const level of manifest.levels) {
    const ids = (level.units ?? []).flatMap((u) => u.lessons ?? [])
    levelCompleted[level.level] = ids.length > 0 && ids.every((id) => completed.has(id))
  }
  return { profile, completed, completedCount: completed.size, levelCompleted }
}

// ───────────────────────── Backend DEMO (localStorage) ─────────────────────────

const DEMO_USERS = 'ccd_demo_users'
const DEMO_SESSION = 'ccd_demo_session'
const demoDataKey = (id) => `ccd_demo_data_${id}`

function demoRead(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback } catch { return fallback }
}
function demoWrite(key, value) { localStorage.setItem(key, JSON.stringify(value)) }

function demoUsers() { return demoRead(DEMO_USERS, {}) }

function demoSeedAdmin() {
  const users = demoUsers()
  if (!users['admin@local']) {
    users['admin@local'] = { id: 'demo-admin', email: 'admin@local', username: 'admin', password: 'admin', is_admin: true }
    demoWrite(DEMO_USERS, users)
    demoWrite(demoDataKey('demo-admin'), { xp: 0, streak_days: 0, last_active: null, progress: {}, badges: [], activity: [] })
  }
}

const demoBackend = {
  mode: 'demo',
  getUser() {
    const id = localStorage.getItem(DEMO_SESSION)
    if (!id) return null
    const u = Object.values(demoUsers()).find((x) => x.id === id)
    return u ? { id: u.id, email: u.email, username: u.username, is_admin: u.is_admin } : null
  },
  async signUp({ email, password, username }) {
    const users = demoUsers()
    if (users[email]) throw new Error('Ese email ya está registrado.')
    const id = 'demo-' + Math.random().toString(36).slice(2, 10)
    users[email] = { id, email, username: username || email.split('@')[0], password, is_admin: false }
    demoWrite(DEMO_USERS, users)
    demoWrite(demoDataKey(id), { xp: 0, streak_days: 0, last_active: null, progress: {}, badges: [], activity: [] })
    localStorage.setItem(DEMO_SESSION, id)
    return this.getUser()
  },
  async signIn({ email, password }) {
    const u = demoUsers()[email]
    if (!u || u.password !== password) throw new Error('Email o contraseña incorrectos.')
    localStorage.setItem(DEMO_SESSION, u.id)
    return this.getUser()
  },
  async signOut() { localStorage.removeItem(DEMO_SESSION) },
  async getProfile() {
    const user = this.getUser()
    if (!user) return null
    const d = demoRead(demoDataKey(user.id), {})
    return { username: user.username, is_admin: user.is_admin, xp: d.xp ?? 0, streak_days: d.streak_days ?? 0, last_active: d.last_active }
  },
  async getProgress() {
    const user = this.getUser()
    const map = new Map()
    if (!user) return map
    const d = demoRead(demoDataKey(user.id), { progress: {} })
    for (const [id, p] of Object.entries(d.progress ?? {})) map.set(id, p)
    return map
  },
  async completeLesson(lesson, passed) {
    const user = this.getUser()
    if (!user) return { xpGained: 0, newBadges: [] }
    const key = demoDataKey(user.id)
    const d = demoRead(key, { xp: 0, streak_days: 0, last_active: null, progress: {}, badges: [], activity: [] })
    const prev = d.progress[lesson.id]
    const firstTime = !prev || prev.status !== 'completed'
    const xpGained = passed && firstTime ? (lesson.xp ?? 10) : 0
    d.progress[lesson.id] = {
      status: passed ? 'completed' : 'in_progress',
      score: passed ? 100 : prev?.score ?? 0,
      attempts: (prev?.attempts ?? 0) + 1,
      completed_at: passed ? new Date().toISOString() : prev?.completed_at ?? null,
    }
    if (passed) {
      d.streak_days = nextStreak(d.streak_days, d.last_active)
      d.xp = (d.xp ?? 0) + xpGained
      d.last_active = new Date().toISOString()
      d.activity.unshift({ event: 'lesson_completed', payload: { lesson: lesson.id, title: lesson.title }, created_at: d.last_active })
    }
    // Badges
    const progressMap = new Map(Object.entries(d.progress))
    const profile = { username: user.username, is_admin: user.is_admin, xp: d.xp, streak_days: d.streak_days }
    const earned = await badgeContext(profile, progressMap).then(evaluateBadges)
    const have = new Set((d.badges ?? []).map((b) => b.badge_id))
    const newBadges = earned.filter((id) => !have.has(id))
    for (const id of newBadges) {
      d.badges.push({ badge_id: id, earned_at: new Date().toISOString() })
      d.activity.unshift({ event: 'badge_earned', payload: { badge_id: id }, created_at: new Date().toISOString() })
    }
    demoWrite(key, d)
    return { xpGained, newBadges }
  },
  async getBadges() {
    const user = this.getUser()
    if (!user) return []
    return demoRead(demoDataKey(user.id), { badges: [] }).badges ?? []
  },
  async getActivity() {
    const user = this.getUser()
    if (!user) return []
    return (demoRead(demoDataKey(user.id), { activity: [] }).activity ?? []).slice(0, 20)
  },
  async getAdminStats() {
    const users = Object.values(demoUsers())
    const today = todayStr()
    let active7d = 0
    for (const u of users) {
      const la = demoRead(demoDataKey(u.id), {}).last_active
      if (la && (new Date(today) - new Date(la.slice(0, 10))) / 86400000 <= 7) active7d++
    }
    return { users: users.length, active7d }
  },
}

// ───────────────────────── Backend NUBE (Supabase) ─────────────────────────

const cloudBackend = {
  mode: 'cloud',
  _user: null,
  getUser() { return this._user },
  async _loadUser() {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) { this._user = null; return null }
    const { data: profile } = await supabase.from('profiles').select('username, is_admin').eq('id', user.id).single()
    this._user = { id: user.id, email: user.email, username: profile?.username ?? user.email, is_admin: profile?.is_admin ?? false }
    return this._user
  },
  async signUp({ email, password, username }) {
    const { data, error } = await supabase.auth.signUp({ email, password })
    if (error) throw error
    if (data.user) {
      await supabase.from('profiles').upsert({ id: data.user.id, username: username || email.split('@')[0] })
    }
    return this._loadUser()
  },
  async signIn({ email, password }) {
    const { error } = await supabase.auth.signInWithPassword({ email, password })
    if (error) throw error
    return this._loadUser()
  },
  async signOut() { await supabase.auth.signOut(); this._user = null },
  async getProfile() {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return null
    const { data } = await supabase.from('profiles').select('*').eq('id', user.id).single()
    return data
  },
  async getProgress() {
    const { data } = await supabase.from('lesson_progress').select('*')
    const map = new Map()
    for (const row of data ?? []) map.set(row.lesson_id, row)
    return map
  },
  async completeLesson(lesson, passed) {
    const { data: { user } } = await supabase.auth.getUser()
    if (!user) return { xpGained: 0, newBadges: [] }
    const { data: prev } = await supabase.from('lesson_progress').select('*').eq('user_id', user.id).eq('lesson_id', lesson.id).maybeSingle()
    const firstTime = !prev || prev.status !== 'completed'
    const xpGained = passed && firstTime ? (lesson.xp ?? 10) : 0
    await supabase.from('lesson_progress').upsert({
      user_id: user.id,
      lesson_id: lesson.id,
      status: passed ? 'completed' : 'in_progress',
      score: passed ? 100 : prev?.score ?? 0,
      attempts: (prev?.attempts ?? 0) + 1,
      completed_at: passed ? new Date().toISOString() : prev?.completed_at ?? null,
    })
    let newBadges = []
    if (passed) {
      const { data: profile } = await supabase.from('profiles').select('*').eq('id', user.id).single()
      const streak = nextStreak(profile?.streak_days ?? 0, profile?.last_active)
      await supabase.from('profiles').update({
        xp: (profile?.xp ?? 0) + xpGained, streak_days: streak, last_active: new Date().toISOString(),
      }).eq('id', user.id)
      await supabase.from('activity_log').insert({ user_id: user.id, event: 'lesson_completed', payload: { lesson: lesson.id, title: lesson.title } })

      const progressMap = await this.getProgress()
      const updatedProfile = { ...profile, xp: (profile?.xp ?? 0) + xpGained, streak_days: streak }
      const earned = await badgeContext(updatedProfile, progressMap).then(evaluateBadges)
      const { data: existing } = await supabase.from('user_badges').select('badge_id').eq('user_id', user.id)
      const have = new Set((existing ?? []).map((b) => b.badge_id))
      newBadges = earned.filter((id) => !have.has(id))
      for (const id of newBadges) {
        await supabase.from('user_badges').insert({ user_id: user.id, badge_id: id })
        await supabase.from('activity_log').insert({ user_id: user.id, event: 'badge_earned', payload: { badge_id: id } })
      }
    }
    return { xpGained, newBadges }
  },
  async getBadges() {
    const { data } = await supabase.from('user_badges').select('*').order('earned_at', { ascending: false })
    return data ?? []
  },
  async getActivity() {
    const { data } = await supabase.from('activity_log').select('*').order('created_at', { ascending: false }).limit(20)
    return data ?? []
  },
  async getAdminStats() {
    const { count } = await supabase.from('profiles').select('*', { count: 'exact', head: true })
    const since = new Date(Date.now() - 7 * 86400000).toISOString()
    const { count: active7d } = await supabase.from('profiles').select('*', { count: 'exact', head: true }).gte('last_active', since)
    return { users: count ?? 0, active7d: active7d ?? 0 }
  },
}

export const store = mode === 'cloud' ? cloudBackend : demoBackend

// Inicialización del modo demo: garantiza el usuario admin/admin.
export async function initStore() {
  if (mode === 'demo') demoSeedAdmin()
  else await cloudBackend._loadUser()
}

export const STORE_MODE = mode
