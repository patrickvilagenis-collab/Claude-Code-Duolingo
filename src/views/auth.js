// Pantalla de registro / inicio de sesión.
import { store, STORE_MODE } from '../lib/store.js'
import { navigate } from '../main.js'

export async function html() {
  const demoNote =
    STORE_MODE === 'demo'
      ? `<p class="hint">Modo demo: tu progreso se guarda en este navegador. Prueba con <strong>admin@local / admin</strong> o crea una cuenta.</p>`
      : ''
  return `
    <div class="brand-hero">
      <div class="brand-logo">🟣</div>
      <h1>Claude Code Duolingo</h1>
      <p class="subtitle">Aprende Claude y Claude Code jugando</p>
    </div>

    <div class="tabs" role="tablist">
      <button class="tab-btn active" data-tab="signin" role="tab">Iniciar sesión</button>
      <button class="tab-btn" data-tab="signup" role="tab">Crear cuenta</button>
    </div>

    <form id="auth-form" class="card" autocomplete="on">
      <label class="field" id="username-field" hidden>
        <span>Nombre de usuario</span>
        <input name="username" type="text" autocomplete="username" placeholder="patrick" />
      </label>
      <label class="field">
        <span>Email</span>
        <input name="email" type="email" required autocomplete="email" placeholder="tu@email.com" />
      </label>
      <label class="field">
        <span>Contraseña</span>
        <input name="password" type="password" required minlength="4" autocomplete="current-password" placeholder="••••••" />
      </label>
      <p class="form-error" id="auth-error" role="alert" hidden></p>
      <button type="submit" id="auth-submit">Iniciar sesión</button>
    </form>
    ${demoNote}
  `
}

export function mount(root) {
  let modeTab = 'signin'
  const form = root.querySelector('#auth-form')
  const errorEl = root.querySelector('#auth-error')
  const submit = root.querySelector('#auth-submit')
  const usernameField = root.querySelector('#username-field')

  root.querySelectorAll('[data-tab]').forEach((btn) => {
    btn.addEventListener('click', () => {
      modeTab = btn.dataset.tab
      root.querySelectorAll('[data-tab]').forEach((b) => b.classList.toggle('active', b === btn))
      const signup = modeTab === 'signup'
      usernameField.hidden = !signup
      submit.textContent = signup ? 'Crear cuenta' : 'Iniciar sesión'
      form.password.setAttribute('autocomplete', signup ? 'new-password' : 'current-password')
      errorEl.hidden = true
    })
  })

  form.addEventListener('submit', async (e) => {
    e.preventDefault()
    errorEl.hidden = true
    submit.disabled = true
    const fd = new FormData(form)
    const payload = {
      email: fd.get('email').trim(),
      password: fd.get('password'),
      username: (fd.get('username') || '').toString().trim(),
    }
    try {
      if (modeTab === 'signup') await store.signUp(payload)
      else await store.signIn(payload)
      navigate('#/home')
    } catch (err) {
      errorEl.textContent = err?.message || 'No se pudo completar la acción.'
      errorEl.hidden = false
    } finally {
      submit.disabled = false
    }
  })
}
