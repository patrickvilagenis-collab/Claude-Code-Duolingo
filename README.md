# Claude Code Duolingo

Plataforma e-learning estilo **Duolingo** para aprender **Claude** y **Claude Code** desde
cero hasta ecosistemas avanzados (MCP, skills, tools, subagentes). Mobile-first, gamificada
y con perfiles en la nube.

## Arquitectura (resumen)

- **Frontend:** PWA responsive (HTML + CSS + JS) con [Vite](https://vitejs.dev).
- **Backend / Auth / Datos:** [Supabase](https://supabase.com) (Postgres + Auth + RLS).
- **Contenido como datos:** lecciones en `content/**.json`, editables por Pull Request.
- **Despliegue:** GitHub Pages vía GitHub Actions.

> Especificación completa en [`docs/ESPECIFICACION_CLAUDE_CODE_DUOLINGO.md`](docs/ESPECIFICACION_CLAUDE_CODE_DUOLINGO.md).

## Puesta en marcha (local, gratis)

```bash
npm install
npm run dev            # servidor local de desarrollo (http://localhost:5173)
```

### Modo demo (sin backend)

La app arranca en **modo demo** si no hay credenciales de Supabase: el registro, el
progreso, la XP, la racha y las insignias se guardan en `localStorage` de tu navegador.
Ideal para probar o desplegar en GitHub Pages sin servidor. Usuario de prueba:
**`admin@local` / `admin`**, o crea tu propia cuenta.

Para usar la nube, copia `.env.example` a `.env` y rellena `VITE_SUPABASE_URL` y
`VITE_SUPABASE_ANON_KEY`; la app cambia automáticamente a modo conectado.

### Backend (Supabase)

1. Crea un proyecto en https://supabase.com
2. Ejecuta `supabase/schema.sql` (tablas + RLS) en el SQL editor.
3. Ejecuta `supabase/seed.sql` (crea el usuario `admin`).
4. Activa Auth con email/contraseña.

## Estructura

```
src/        # frontend (Vite + PWA)
content/    # lecciones como JSON (contenido como datos)
supabase/   # schema.sql, seed.sql, edge functions
scripts/    # validador de contenido
docs/       # especificación
.github/    # CI/CD
```

## Niveles

1. **Básico** — qué es Claude, prompts, casos de uso.
2. **Intermedio** — Claude Code en acción (instalar, bucle agéntico, CLAUDE.md, slash commands).
3. **Avanzado** — MCP, skills, tools, subagentes, hooks, ecosistemas completos.

## Licencia

MIT
