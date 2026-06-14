// Carga del currículo y las lecciones (contenido como datos).
// El manifest define el orden, prerequisitos y checkpoints; cada lección es un
// JSON independiente bajo /content/levelN/unitX/.

const base = import.meta.env.BASE_URL || './'

let _manifest = null
const _lessonCache = new Map()

export async function getManifest() {
  if (_manifest) return _manifest
  const res = await fetch(`${base}content/manifest.json`)
  if (!res.ok) throw new Error('No se pudo cargar el manifest de contenido')
  _manifest = await res.json()
  return _manifest
}

// Devuelve la lista ordenada de lessonIds tal como aparecen en el currículo.
export async function getLessonOrder() {
  const m = await getManifest()
  const order = []
  for (const level of m.levels) {
    for (const unit of level.units ?? []) {
      for (const id of unit.lessons ?? []) order.push(id)
    }
  }
  return order
}

// Resuelve la ruta de un lessonId: "l1-u1-2" -> content/level1/unit1/l1-u1-2.json
function lessonPath(id) {
  const match = /^l(\d+)-u(\d+)-/.exec(id)
  if (!match) throw new Error(`lessonId con formato inesperado: ${id}`)
  const [, level, unit] = match
  return `${base}content/level${level}/unit${unit}/${id}.json`
}

export async function getLesson(id) {
  if (_lessonCache.has(id)) return _lessonCache.get(id)
  const res = await fetch(lessonPath(id))
  if (!res.ok) throw new Error(`No se pudo cargar la lección ${id}`)
  const data = await res.json()
  _lessonCache.set(id, data)
  return data
}
