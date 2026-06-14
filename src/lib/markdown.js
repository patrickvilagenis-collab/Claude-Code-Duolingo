// Mini-renderer de Markdown (sin dependencias). Soporta lo justo para las
// lecciones: **negrita**, *cursiva*, `código`, saltos de línea y listas simples.
// Escapa HTML primero para evitar inyección desde el contenido.

function escapeHtml(s) {
  return s
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
}

function inline(s) {
  return escapeHtml(s)
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
}

export function renderMarkdown(md = '') {
  const blocks = md.split(/\n{2,}/)
  return blocks
    .map((block) => {
      const lines = block.split('\n')
      // Lista con viñetas "- " o "* "
      if (lines.every((l) => /^\s*[-*]\s+/.test(l))) {
        const items = lines.map((l) => `<li>${inline(l.replace(/^\s*[-*]\s+/, ''))}</li>`).join('')
        return `<ul>${items}</ul>`
      }
      return `<p>${lines.map(inline).join('<br>')}</p>`
    })
    .join('')
}
