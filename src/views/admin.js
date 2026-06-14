// Panel de admin (sólo is_admin): estadísticas básicas y acceso a edición de contenido.
import { store, STORE_MODE } from '../lib/store.js'
import { getManifest } from '../lib/content.js'
import { navigate } from '../main.js'

export async function html() {
  const [stats, manifest] = await Promise.all([store.getAdminStats(), getManifest()])
  const totalLessons = manifest.levels.reduce(
    (n, l) => n + (l.units ?? []).reduce((m, u) => m + (u.lessons ?? []).length, 0),
    0,
  )
  const modeNote =
    STORE_MODE === 'demo'
      ? `<p class="hint">Modo demo: las estadísticas reflejan las cuentas creadas en este navegador.</p>`
      : ''
  return `
    <header class="profile-head"><div class="avatar-lg">🛠️</div><div><h1>Admin</h1><p class="profile-stats">Estadísticas de la plataforma</p></div></header>
    <section class="block stats-grid">
      <div class="stat-card"><div class="stat-num">${stats.users}</div><div class="stat-label">Usuarios</div></div>
      <div class="stat-card"><div class="stat-num">${stats.active7d}</div><div class="stat-label">Activos 7d</div></div>
      <div class="stat-card"><div class="stat-num">${totalLessons}</div><div class="stat-label">Lecciones</div></div>
    </section>
    <section class="block">
      <h2>Contenido</h2>
      <p>El contenido vive como datos en <code>content/**.json</code> y se edita por Pull Request. CI valida el esquema antes de fusionar.</p>
      <a class="link-btn" href="https://github.com/patrickvilagenis-collab/Claude-Code-Duolingo/tree/main/content" target="_blank" rel="noopener">Editar lecciones en GitHub →</a>
    </section>
    ${modeNote}
    <section class="block"><button class="secondary" data-nav="#/home">Volver al inicio</button></section>
  `
}

export function mount(root) {
  root.querySelectorAll('[data-nav]').forEach((el) =>
    el.addEventListener('click', () => navigate(el.dataset.nav)),
  )
}
