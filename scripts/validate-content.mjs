// Valida el contenido (content/**.json) antes de fusionar un PR.
// Comprueba: campos requeridos, tipo de reto válido y campos propios de cada
// tipo, y que toda lección referenciada en el manifest exista como archivo.
import { readdirSync, readFileSync, statSync, existsSync } from 'node:fs'
import { join } from 'node:path'

const ROOT = 'content'
const REQUIRED = ['id', 'level', 'unit', 'title', 'concept', 'challenge']
const CHALLENGE_TYPES = ['single-choice', 'multi-choice', 'order', 'fill-blank', 'free-text']

let errors = 0
const fail = (msg) => { console.error(`✗ ${msg}`); errors++ }

// Valida los campos propios de cada tipo de reto.
function validateChallenge(p, ch) {
  if (!ch || typeof ch !== 'object') return fail(`${p}: 'challenge' debe ser un objeto`)
  if (!ch.type || !CHALLENGE_TYPES.includes(ch.type)) return fail(`${p}: challenge.type '${ch.type}' no válido`)
  if (!ch.prompt) fail(`${p}: challenge.prompt vacío`)
  switch (ch.type) {
    case 'single-choice':
      if (!Array.isArray(ch.options)) fail(`${p}: single-choice requiere 'options'`)
      if (!Number.isInteger(ch.answer)) fail(`${p}: single-choice requiere 'answer' (índice)`)
      break
    case 'multi-choice':
      if (!Array.isArray(ch.options)) fail(`${p}: multi-choice requiere 'options'`)
      if (!Array.isArray(ch.answer)) fail(`${p}: multi-choice requiere 'answer' (array de índices)`)
      break
    case 'order':
      if (!Array.isArray(ch.items)) fail(`${p}: order requiere 'items'`)
      if (!Array.isArray(ch.answer) || (ch.items && ch.answer.length !== ch.items.length))
        fail(`${p}: order requiere 'answer' con el mismo nº de elementos que 'items'`)
      break
    case 'fill-blank':
      if (ch.answer == null) fail(`${p}: fill-blank requiere 'answer'`)
      break
    case 'free-text':
      if (!ch.why) fail(`${p}: free-text debería incluir 'why' (rúbrica/guía)`)
      break
  }
}

const lessonFiles = new Set()

function walk(dir) {
  for (const name of readdirSync(dir)) {
    const p = join(dir, name)
    if (statSync(p).isDirectory()) { walk(p); continue }
    if (!p.endsWith('.json') || p.endsWith('manifest.json')) continue
    let data
    try { data = JSON.parse(readFileSync(p, 'utf8')) }
    catch (e) { fail(`JSON inválido: ${p}\n  ${e.message}`); continue }
    for (const field of REQUIRED) if (!(field in data)) fail(`${p}: falta '${field}'`)
    validateChallenge(p, data.challenge)
    if (data.id) lessonFiles.add(data.id)
  }
}

walk(ROOT)

// Cruce con el manifest: cada lección listada debe existir como archivo.
try {
  const manifest = JSON.parse(readFileSync(join(ROOT, 'manifest.json'), 'utf8'))
  for (const level of manifest.levels ?? []) {
    for (const unit of level.units ?? []) {
      for (const id of unit.lessons ?? []) {
        if (!lessonFiles.has(id)) fail(`manifest: la lección '${id}' (unidad ${unit.unit}) no tiene archivo JSON`)
      }
    }
  }
} catch (e) {
  fail(`No se pudo leer content/manifest.json: ${e.message}`)
}

if (errors) { console.error(`\n${errors} error(es) de contenido.`); process.exit(1) }
console.log(`✓ Contenido válido (${lessonFiles.size} lecciones).`)
