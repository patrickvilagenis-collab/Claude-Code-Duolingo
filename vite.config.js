import { defineConfig } from 'vite'
import { cpSync, existsSync } from 'node:fs'
import { resolve } from 'node:path'

// El contenido (lecciones) vive en /content en la raíz del repo para poder
// editarlo por Pull Request. En dev, Vite ya lo sirve desde la raíz; en build
// hay que copiarlo a /dist para que se publique junto a la app.
function copyContent() {
  return {
    name: 'copy-content',
    closeBundle() {
      const src = resolve(__dirname, 'content')
      const dest = resolve(__dirname, 'dist/content')
      if (existsSync(src)) cpSync(src, dest, { recursive: true })
    },
  }
}

// base relativa para que funcione en GitHub Pages bajo /Claude-Code-Duolingo/
export default defineConfig({
  base: './',
  build: { outDir: 'dist' },
  plugins: [copyContent()],
})
