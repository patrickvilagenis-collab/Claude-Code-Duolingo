import './styles/main.css'
import { store, initStore, STORE_MODE } from './lib/store.js'
import * as auth from './views/auth.js'
import * as home from './views/home.js'
import * as lesson from './views/lesson.js'
import * as profile from './views/profile.js'
import * as admin from './views/admin.js'

const app = document.getElementById('app')

// Router por hash: "#/lesson/l1-u1-1" → { name: 'lesson', param: 'l1-u1-1' }
function parseRoute() {
  const raw = location.hash.replace(/^#\/?/, '')
  const [name, param] = raw.split('/')
  return { name: name || 'home', param }
}

const VIEWS = { login: auth, home, lesson, profile, admin }

export function navigate(hash) { location.hash = hash }

function shell(inner, active, user) {
  const tab = (icon, label, hash, key) =>
    `<button class="nav-item ${active === key ? 'active' : ''}" data-nav="${hash}">
       <span class="nav-icon">${icon}</span><span class="nav-label">${label}</span>
     </button>`
  const adminTab = user?.is_admin ? tab('🛠️', 'Admin', '#/admin', 'admin') : ''
  return `
    <div class="app-shell">
      <main class="screen">${inner}</main>
      <nav class="bottom-nav">
        ${tab('🏠', 'Inicio', '#/home', 'home')}
        ${tab('👤', 'Perfil', '#/profile', 'profile')}
        ${adminTab}
      </nav>
    </div>`
}

async function render() {
  const { name, param } = parseRoute()
  const user = store.getUser()

  // Guard de autenticación.
  if (!user && name !== 'login') { navigate('#/login'); return }
  if (user && name === 'login') { navigate('#/home'); return }

  const view = VIEWS[name] || home

  if (name === 'login') {
    app.innerHTML = '<div class="screen auth-screen">' + (await view.html(param)) + '</div>'
    view.mount?.(app, param)
    return
  }

  // Admin sólo para is_admin.
  if (name === 'admin' && !user.is_admin) { navigate('#/home'); return }

  const navKey = name === 'admin' ? 'admin' : name === 'profile' ? 'profile' : 'home'
  app.innerHTML = shell(await view.html(param), navKey, user)
  view.mount?.(app, param)

  app.querySelectorAll('[data-nav]').forEach((el) =>
    el.addEventListener('click', () => navigate(el.dataset.nav)),
  )
}

window.addEventListener('hashchange', render)
window.addEventListener('load', async () => {
  await initStore()
  if (STORE_MODE === 'demo') {
    console.info('Claude Code Duolingo — modo DEMO (progreso guardado en este navegador). Configura Supabase para la nube.')
  }
  if (!location.hash) navigate('#/home')
  render()
})

// PWA: registra el service worker (offline básico) sólo en producción.
if ('serviceWorker' in navigator && import.meta.env.PROD) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register(`${import.meta.env.BASE_URL}sw.js`).catch(() => {})
  })
}
