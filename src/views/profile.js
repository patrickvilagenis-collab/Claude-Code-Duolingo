// Perfil: XP, racha, barras de progreso por nivel, insignias e historial.
import { store } from '../lib/store.js'
import { getManifest } from '../lib/content.js'
import { BADGES, badgeById } from '../lib/gamification.js'
import { navigate } from '../main.js'

function escapeHtml(s = '') {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

function activityLabel(a) {
  if (a.event === 'lesson_completed') return `Completaste «${escapeHtml(a.payload?.title || a.payload?.lesson || 'una lección')}»`
  if (a.event === 'badge_earned') { const b = badgeById(a.payload?.badge_id); return `Insignia ${b ? b.icon + ' ' + b.name : a.payload?.badge_id}` }
  if (a.event === 'xp_earned') return `+${a.payload?.amount ?? 0} XP`
  return escapeHtml(a.event)
}

export async function html() {
  const [profile, progress, manifest, badges, activity] = await Promise.all([
    store.getProfile(),
    store.getProgress(),
    getManifest(),
    store.getBadges(),
    store.getActivity(),
  ])
  const isCompleted = (id) => progress.get(id)?.status === 'completed'

  const levelBars = manifest.levels
    .map((level) => {
      const ids = (level.units ?? []).flatMap((u) => u.lessons ?? [])
      const done = ids.filter(isCompleted).length
      const pct = ids.length ? Math.round((done / ids.length) * 100) : 0
      return `
        <div class="level-progress">
          <div class="level-progress-row"><span>Nivel ${level.level}</span><span>${pct}%</span></div>
          <div class="progress"><div class="progress-bar" style="width:${pct}%"></div></div>
        </div>`
    })
    .join('')

  const earned = new Set(badges.map((b) => b.badge_id))
  const badgesHtml = BADGES.map((b) => {
    const has = earned.has(b.id)
    return `<div class="badge ${has ? 'earned' : 'locked'}" title="${escapeHtml(b.desc)}">
              <div class="badge-icon">${has ? b.icon : '🔒'}</div>
              <div class="badge-name">${escapeHtml(b.name)}</div>
            </div>`
  }).join('')

  const historyHtml = activity.length
    ? `<ul class="history">${activity.map((a) => `<li>${activityLabel(a)}</li>`).join('')}</ul>`
    : `<p class="hint">Aún no hay actividad. ¡Empieza una lección!</p>`

  const adminLink = profile?.is_admin ? `<button class="secondary" data-nav="#/admin">Panel de admin 🛠️</button>` : ''

  return `
    <header class="profile-head">
      <div class="avatar-lg">👤</div>
      <div>
        <h1>${escapeHtml(profile?.username || 'usuario')}</h1>
        <p class="profile-stats">⭐ ${profile?.xp ?? 0} XP · 🔥 ${profile?.streak_days ?? 0} días</p>
      </div>
    </header>

    <section class="block"><h2>Progreso</h2>${levelBars}</section>
    <section class="block"><h2>Logros</h2><div class="badges-grid">${badgesHtml}</div></section>
    <section class="block"><h2>Historial</h2>${historyHtml}</section>
    <section class="block actions-col">
      ${adminLink}
      <button class="secondary danger" id="logout-btn">Cerrar sesión</button>
    </section>
  `
}

export function mount(root) {
  root.querySelectorAll('[data-nav]').forEach((el) =>
    el.addEventListener('click', () => navigate(el.dataset.nav)),
  )
  root.querySelector('#logout-btn')?.addEventListener('click', async () => {
    await store.signOut()
    navigate('#/login')
  })
}
