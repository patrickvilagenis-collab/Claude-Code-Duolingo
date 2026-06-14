// Home: mapa de niveles ("árbol"). Renderiza el currículo desde el manifest y
// marca cada lección como completada / actual / bloqueada según el progreso.
import { store } from '../lib/store.js'
import { getManifest } from '../lib/content.js'
import { navigate } from '../main.js'

export async function html() {
  const [manifest, profile, progress] = await Promise.all([
    getManifest(),
    store.getProfile(),
    store.getProgress(),
  ])

  // Orden lineal de todas las lecciones para calcular desbloqueo.
  const order = manifest.levels.flatMap((l) => (l.units ?? []).flatMap((u) => u.lessons ?? []))
  const isCompleted = (id) => progress.get(id)?.status === 'completed'
  const currentId = order.find((id) => !isCompleted(id)) || null

  const header = `
    <header class="topbar">
      <div class="stat">🔥 <strong>${profile?.streak_days ?? 0}</strong></div>
      <div class="stat">⭐ <strong>${profile?.xp ?? 0}</strong> XP</div>
      <button class="avatar-btn" data-nav="#/profile" aria-label="Perfil">👤</button>
    </header>`

  const continueBtn = currentId
    ? `<button class="cta" id="continue-btn">Continuar lección</button>`
    : `<p class="all-done">🎉 ¡Has completado todo el contenido disponible!</p>`

  const levelsHtml = manifest.levels
    .map((level) => {
      const units = level.units ?? []
      const levelLessons = units.flatMap((u) => u.lessons ?? [])
      const done = levelLessons.filter(isCompleted).length
      const pct = levelLessons.length ? Math.round((done / levelLessons.length) * 100) : 0
      const empty = levelLessons.length === 0

      const unitsHtml = units
        .map((unit) => {
          const nodes = (unit.lessons ?? [])
            .map((id) => {
              const completed = isCompleted(id)
              const current = id === currentId
              const locked = !completed && !current
              const icon = completed ? '✅' : current ? '🟢' : '🔒'
              const cls = completed ? 'done' : current ? 'current' : 'locked'
              return `<button class="node ${cls}" data-lesson="${id}" ${locked ? 'disabled' : ''} title="${id}">
                        <span class="node-icon">${icon}</span>
                      </button>`
            })
            .join('<span class="node-link"></span>')
          return `
            <div class="unit">
              <div class="unit-head">${unit.unit} · ${unit.title}</div>
              <div class="node-row">${nodes}</div>
            </div>`
        })
        .join('')

      return `
        <section class="level ${empty ? 'level-empty' : ''}">
          <div class="level-head">
            <h2>Nivel ${level.level} · ${level.title}</h2>
            <span class="level-pct">${pct}%</span>
          </div>
          <div class="progress"><div class="progress-bar" style="width:${pct}%"></div></div>
          ${empty ? '<p class="hint">Próximamente.</p>' : unitsHtml}
        </section>`
    })
    .join('')

  return `${header}<div class="continue-wrap">${continueBtn}</div>${levelsHtml}`
}

export function mount(root) {
  const cont = root.querySelector('#continue-btn')
  if (cont) {
    cont.addEventListener('click', async () => {
      const manifest = await getManifest()
      const progress = await store.getProgress()
      const order = manifest.levels.flatMap((l) => (l.units ?? []).flatMap((u) => u.lessons ?? []))
      const next = order.find((id) => progress.get(id)?.status !== 'completed')
      if (next) navigate(`#/lesson/${next}`)
    })
  }
  root.querySelectorAll('[data-lesson]').forEach((btn) => {
    if (btn.disabled) return
    btn.addEventListener('click', () => navigate(`#/lesson/${btn.dataset.lesson}`))
  })
  root.querySelectorAll('[data-nav]').forEach((el) =>
    el.addEventListener('click', () => navigate(el.dataset.nav)),
  )
}
