// Vista de lección: Concepto → Ejemplo → Reto → Corrección (con el "porqué").
// Soporta retos single-choice, multi-choice, order, fill-blank y free-text.
import { store } from '../lib/store.js'
import { getLesson } from '../lib/content.js'
import { renderMarkdown } from '../lib/markdown.js'
import { badgeById } from '../lib/gamification.js'
import { navigate } from '../main.js'

function escapeHtml(s = '') {
  return s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}

export async function html(id) {
  const lesson = await getLesson(id)
  const example = lesson.example
    ? `<section class="block">
         <h3 class="kicker">Ejemplo</h3>
         <div class="prose">${renderMarkdown(lesson.example.md || '')}</div>
         ${lesson.example.code ? `<pre class="code"><code>${escapeHtml(lesson.example.code.body || '')}</code></pre>` : ''}
       </section>`
    : ''
  return `
    <header class="lesson-bar">
      <button class="icon-btn" data-nav="#/home" aria-label="Volver">◀</button>
      <div class="lesson-title">${escapeHtml(lesson.unit)} · ${escapeHtml(lesson.title)}</div>
    </header>
    <section class="block">
      <h3 class="kicker">Concepto</h3>
      <div class="prose">${renderMarkdown(lesson.concept?.md || '')}</div>
    </section>
    ${example}
    <div id="challenge-area">
      <button class="cta" id="start-challenge">Empezar reto</button>
    </div>
  `
}

export function mount(root, id) {
  root.querySelectorAll('[data-nav]').forEach((el) =>
    el.addEventListener('click', () => navigate(el.dataset.nav)),
  )
  const area = root.querySelector('#challenge-area')
  root.querySelector('#start-challenge')?.addEventListener('click', async () => {
    const lesson = await getLesson(id)
    renderChallenge(area, lesson)
  })
}

function renderChallenge(area, lesson) {
  const ch = lesson.challenge
  let getResult // () => { correct, pickedIndex|null }

  let body = ''
  if (ch.type === 'single-choice' || ch.type === 'multi-choice') {
    const multi = ch.type === 'multi-choice'
    body = `<div class="options" role="group">
      ${ch.options.map((opt, i) => `
        <label class="option">
          <input type="${multi ? 'checkbox' : 'radio'}" name="opt" value="${i}" />
          <span>${escapeHtml(opt)}</span>
        </label>`).join('')}
    </div>`
    getResult = () => {
      const checked = [...area.querySelectorAll('input[name=opt]:checked')].map((el) => +el.value)
      if (checked.length === 0) return null
      if (multi) {
        const want = new Set(ch.answer)
        const correct = checked.length === want.size && checked.every((i) => want.has(i))
        return { correct, pickedIndex: null }
      }
      return { correct: checked[0] === ch.answer, pickedIndex: checked[0] }
    }
  } else if (ch.type === 'order') {
    // El alumno hace clic en los elementos en el orden correcto.
    body = `
      <p class="hint">Toca los pasos en el orden correcto.</p>
      <ol class="order-target" id="order-target"></ol>
      <div class="order-pool">
        ${ch.items.map((it, i) => `<button type="button" class="pill" data-i="${i}">${escapeHtml(it)}</button>`).join('')}
      </div>`
    getResult = () => {
      const seq = [...area.querySelectorAll('#order-target li')].map((li) => +li.dataset.i)
      if (seq.length !== ch.items.length) return null
      const correct = seq.every((v, idx) => v === ch.answer[idx])
      return { correct, pickedIndex: null }
    }
  } else if (ch.type === 'fill-blank') {
    body = `<input class="blank-input" id="blank" type="text" placeholder="Tu respuesta" autocomplete="off" />`
    const norm = (s) => s.trim().toLowerCase().replace(/\s+/g, ' ')
    const accepted = (Array.isArray(ch.answer) ? ch.answer : [ch.answer]).map(norm)
    getResult = () => {
      const val = area.querySelector('#blank')?.value || ''
      if (!val.trim()) return null
      return { correct: accepted.includes(norm(val)), pickedIndex: null }
    }
  } else if (ch.type === 'free-text') {
    body = `
      <textarea class="free-text" id="free" rows="5" placeholder="Escribe tu respuesta…"></textarea>
      <p class="hint">Respuesta abierta: compara tu respuesta con la guía al continuar.</p>`
    getResult = () => {
      const val = area.querySelector('#free')?.value || ''
      if (!val.trim()) return null
      return { correct: true, pickedIndex: null, free: true } // autoevaluada en modo sin IA
    }
  }

  area.innerHTML = `
    <section class="block challenge">
      <h3 class="kicker">Reto</h3>
      <p class="challenge-prompt">${escapeHtml(ch.prompt)}</p>
      ${body}
      <button class="cta" id="check-btn">Comprobar</button>
    </section>`

  if (ch.type === 'order') wireOrder(area)

  area.querySelector('#check-btn').addEventListener('click', () => {
    const result = getResult()
    if (!result) return // nada seleccionado
    showCorrection(area, lesson, result)
  })
}

function wireOrder(area) {
  const target = area.querySelector('#order-target')
  area.querySelectorAll('.order-pool .pill').forEach((btn) => {
    btn.addEventListener('click', () => {
      if (btn.classList.contains('used')) return
      btn.classList.add('used')
      btn.disabled = true
      const li = document.createElement('li')
      li.dataset.i = btn.dataset.i
      li.textContent = btn.textContent
      const undo = document.createElement('button')
      undo.type = 'button'
      undo.className = 'undo'
      undo.textContent = '✕'
      undo.addEventListener('click', () => {
        li.remove()
        btn.classList.remove('used')
        btn.disabled = false
      })
      li.appendChild(undo)
      target.appendChild(li)
    })
  })
}

async function showCorrection(area, lesson, result) {
  const ch = lesson.challenge
  let whyHtml = `<div class="prose">${renderMarkdown(ch.why || '')}</div>`

  if (!result.correct && result.pickedIndex != null) {
    const mistake = (lesson.commonMistakes || []).find((m) => m.pick === result.pickedIndex)
    if (mistake) {
      whyHtml = `<div class="prose mistake-note"><strong>Por qué tu elección no es la mejor:</strong> ${renderMarkdown(mistake.why)}</div>` + whyHtml
    }
  }

  const passed = result.correct
  const heading = result.free
    ? '📝 Respuesta registrada'
    : passed
      ? '✅ ¡Correcto!'
      : '❌ No exactamente'

  area.innerHTML = `
    <section class="block correction ${passed ? 'ok' : 'bad'}">
      <h3 class="result-heading">${heading}</h3>
      <h4 class="kicker">Por qué</h4>
      ${whyHtml}
      <div id="reward"></div>
      <div class="correction-actions">
        ${passed ? '' : '<button class="secondary" id="retry-btn">Reintentar</button>'}
        <button class="cta" id="continue-btn">${passed ? 'Continuar' : 'Continuar de todas formas'}</button>
      </div>
    </section>`

  area.querySelector('#retry-btn')?.addEventListener('click', () => renderChallenge(area, lesson))

  area.querySelector('#continue-btn').addEventListener('click', async (e) => {
    e.target.disabled = true
    const { xpGained, newBadges } = await store.completeLesson(lesson, passed)
    const reward = area.querySelector('#reward')
    const parts = []
    if (xpGained > 0) parts.push(`<div class="reward-xp">+${xpGained} XP ⭐</div>`)
    for (const id of newBadges) {
      const b = badgeById(id)
      if (b) parts.push(`<div class="reward-badge">${b.icon} Nueva insignia: <strong>${b.name}</strong></div>`)
    }
    if (parts.length) {
      reward.innerHTML = parts.join('')
      setTimeout(() => navigate('#/home'), 1200)
    } else {
      navigate('#/home')
    }
  })
}
