# Claude Code Duolingo — Especificación Técnica y de Contenido

> Plataforma web de e-learning interactivo (estilo Duolingo / Lingoda) para dominar
> **Claude** y **Claude Code** desde cero hasta ecosistemas avanzados (conectores, skills,
> tools, MCP, subagentes).
> Mobile-first · gratuita · perfiles en la nube · gamificada.

**Versión:** 1.0 · **Fecha:** 2026-06-14 · **Repositorio objetivo:** `Claude Code Duolingo`

---

## 0. Resumen ejecutivo

| Dimensión | Decisión recomendada |
|---|---|
| **Frontend** | HTML + CSS + JavaScript vanilla con [Vite](https://vitejs.dev) (o PWA). Sin framework pesado para mantenerlo simple, rápido en móvil e instalable. |
| **Backend / Auth / Datos** | [Supabase](https://supabase.com) (capa gratuita): Postgres + Auth (email/contraseña) + Row Level Security + Realtime. Cero servidor que mantener. |
| **Servidor local** | `npm run dev` (Vite) o `python -m http.server`. Cero coste. |
| **Despliegue** | GitHub Pages (gratis) vía GitHub Actions (CI/CD). |
| **Código y contenido** | Todo versionado en el repo **Claude Code Duolingo**. El contenido de lecciones vive como **archivos JSON/Markdown** en `/content`, no en la base de datos → escalable y editable por PR. |
| **IA opcional** | Claude API (`claude-haiku-4-5` para corrección de retos abiertos por bajo coste; `claude-opus-4-8` para generación/curación de contenido). Detalle en §9. |
| **Admin** | Usuario `admin/admin` predefinido + panel de estadísticas y gestión de contenido. |

**Principio rector de arquitectura:** *contenido como datos*. Las lecciones son archivos
declarativos en el repo; el progreso del usuario es estado en la nube. Esta separación permite
añadir lecciones sin tocar código ni reorganizar la base de datos.

---

## 1. Estructura de contenido por niveles

El currículo se organiza en **3 niveles → unidades → micro-lecciones**. Cada micro-lección
dura **5–10 min** y sigue siempre la estructura pedagógica:

```
Concepto  →  Ejemplo práctico  →  Reto  →  Corrección con el "porqué"
```

Antes de avanzar de unidad hay un **checkpoint de comprensión** (3–5 preguntas) que debe
aprobarse (≥ 80 %). El sistema guarda el nivel/unidad/lección actual y permite retomar siempre.

### Nivel 1 — Básico: "¿Qué es Claude?"
*Objetivo: que el usuario entienda qué es Claude, para qué sirve, y haga su primer prompt.*

| Unidad | Micro-lecciones | Reto tipo |
|---|---|---|
| 1.1 ¿Qué es un LLM y qué es Claude? | Modelos actuales (Fable 5, Opus 4.8, Sonnet 4.6, Haiku 4.5), qué los diferencia, casos de uso | Elegir el modelo adecuado para 3 escenarios |
| 1.2 Anatomía de un buen prompt | Contexto, instrucción, formato de salida, ejemplos | Reescribir un prompt vago para que sea claro |
| 1.3 Claude en la práctica | Resumir, extraer, clasificar, traducir, escribir | Diseñar un prompt para extraer datos de un texto |
| 1.4 Conversaciones y contexto | Memoria de la conversación, ventana de contexto, límites | Identificar por qué Claude "olvidó" algo |
| 1.5 Pensar mejor: razonamiento | Adaptive thinking, esfuerzo (effort), cuándo conviene | Marcar cuándo activar más razonamiento |

### Nivel 2 — Intermedio: "Claude Code en acción"
*Objetivo: instalar, abrir y trabajar con Claude Code en un proyecto real.*

| Unidad | Micro-lecciones | Reto tipo |
|---|---|---|
| 2.1 ¿Qué es Claude Code? | CLI agéntica en terminal; también app de escritorio, web (claude.ai/code) e IDE (VS Code, JetBrains) | Emparejar superficie ↔ caso de uso |
| 2.2 Instalación y primer arranque | Instalar, `claude`, autenticación, primer prompt en un repo | Checklist de instalación |
| 2.3 El bucle agéntico | Cómo lee archivos, edita, ejecuta comandos, itera | Ordenar los pasos de un bucle agéntico |
| 2.4 Herramientas integradas | Read, Edit, Bash, Glob, Grep, Web search | Elegir la herramienta correcta para una tarea |
| 2.5 `CLAUDE.md` y memoria del proyecto | Documentar el repo para Claude; `/init` | Escribir un `CLAUDE.md` mínimo |
| 2.6 Slash commands | Comandos integrados y personalizados (`/review`, `/init`...) | Crear un slash command propio |
| 2.7 Permisos y seguridad | Modos de permiso, qué aprobar, trabajo en ramas | Decidir aprobar/denegar en 4 casos |
| 2.8 Plan mode y verificación | Planificar antes de actuar; verificar el cambio | Detectar cuándo conviene Plan Mode |

### Nivel 3 — Avanzado: "Ecosistemas con Claude Code"
*Objetivo: construir sistemas reales con MCP, skills, subagentes, hooks y conectores.*

| Unidad | Micro-lecciones | Reto tipo |
|---|---|---|
| 3.1 MCP (Model Context Protocol) | Qué es, servidores MCP, conectar GitHub/Drive/Slack | Configurar un servidor MCP en JSON |
| 3.2 Skills | Carpeta + `SKILL.md`, divulgación progresiva, cuándo usarlas | Escribir el `SKILL.md` de una skill |
| 3.3 Tools personalizadas | Definir herramientas con esquema; tools cliente vs servidor | Diseñar el `input_schema` de una tool |
| 3.4 Subagentes | Delegar trabajo en paralelo, agentes especializados | Decidir cuándo lanzar un subagente |
| 3.5 Hooks | Automatizar acciones en eventos (SessionStart, etc.) | Configurar un hook en `settings.json` |
| 3.6 Conectores y ecosistema | GitHub MCP, conectores de apps, despliegue, CI/CD | Diagramar un flujo PR → review → deploy |
| 3.7 Proyecto final | Construir un mini-ecosistema end-to-end | Entregar un proyecto evaluado por rúbrica |

> **Progresión ramificada:** dentro de cada nivel, el usuario puede tomar una *ruta rápida*
> (solo lecciones núcleo) o una *ruta completa* (con retos extra). El checkpoint de fin de
> unidad es obligatorio en ambas rutas.

---

## 2. Modelo de datos del contenido (contenido como datos)

Cada lección es un archivo JSON en `/content/levelN/unitX/lessonY.json`. Esto permite añadir
contenido por **Pull Request** sin tocar la app.

```jsonc
// content/level1/unit1/1-1-que-es-claude.json
{
  "id": "l1-u1-1",
  "level": 1,
  "unit": "1.1",
  "title": "¿Qué es un LLM y qué es Claude?",
  "estMinutes": 7,
  "xp": 20,
  "concept": {
    "md": "Claude es un asistente de IA de Anthropic... (Markdown)"
  },
  "example": {
    "md": "Ejemplo: pedimos a Claude que resuma un correo...",
    "code": { "lang": "text", "body": "Prompt:\nResume este correo en 3 puntos..." }
  },
  "challenge": {
    "type": "single-choice",          // single-choice | multi-choice | order | fill-blank | free-text
    "prompt": "¿Qué modelo elegirías para clasificar 10.000 reseñas baratas y rápido?",
    "options": ["Claude Opus 4.8", "Claude Haiku 4.5", "Claude Fable 5"],
    "answer": 1,
    "why": "Haiku 4.5 es el más rápido y económico; ideal para tareas simples de alto volumen. Opus/Fable son más capaces pero más caros y lentos para esta tarea."
  },
  "commonMistakes": [
    { "pick": 0, "why": "Opus es muy capaz pero excede lo necesario y cuesta más por token." }
  ]
}
```

**Tipos de reto soportados** y cómo se corrigen:

| `type` | Corrección | Explica el "porqué" |
|---|---|---|
| `single-choice` / `multi-choice` | Cliente, comparación con `answer` | `why` + `commonMistakes[]` |
| `order` | Cliente, comparación de secuencia | Explicación por paso mal ordenado |
| `fill-blank` | Cliente, normalización de texto | `why` |
| `free-text` | **Claude API** evalúa contra una rúbrica (§9) | Feedback generado + `why` curado |

El índice del currículo (`content/manifest.json`) define el orden, prerequisitos y checkpoints,
de modo que el frontend solo lee un manifest para construir el mapa de niveles.

---

## 3. Arquitectura técnica

```
┌──────────────────────────────────────────────────────────────┐
│  Cliente (móvil / tablet / desktop) — PWA responsive          │
│  HTML + CSS + JS (Vite). Service worker para offline básico.  │
│   • Renderiza el "árbol" de niveles desde /content            │
│   • Maneja retos y corrección local                           │
│   • Guarda/lee progreso vía SDK de Supabase                   │
└───────────────┬───────────────────────────┬──────────────────┘
                │ supabase-js (HTTPS)        │ fetch /content/*.json
                ▼                            ▼
┌───────────────────────────┐   ┌──────────────────────────────┐
│  Supabase (nube, gratis)  │   │  Contenido estático (repo)    │
│  • Auth (email/contraseña)│   │  servido por GitHub Pages     │
│  • Postgres + RLS         │   │  /content/**.json + manifest  │
│  • Edge Function (opc.):  │   └──────────────────────────────┘
│    corrección free-text   │
│    llamando a Claude API  │
└───────────────────────────┘
                ▲
                │  GitHub Actions (CI/CD): lint + validar JSON + deploy a Pages
┌───────────────┴──────────────────────────────────────────────┐
│  Repositorio  "Claude Code Duolingo"  (GitHub)                │
│  código + contenido + workflows + docs                        │
└──────────────────────────────────────────────────────────────┘
```

### Por qué Supabase (vs Firebase)
- **Postgres real + RLS**: cada usuario solo ve/edita su propio progreso, con políticas SQL
  declarativas y seguras. Encaja con "perfil propio por usuario".
- **Auth integrada gratuita** con email/contraseña (registro directo, sin GitHub).
- **SDK JS sencillo** que funciona desde HTML estático (no requiere backend propio).
- Firebase es válido también; la elección es intercambiable. La spec usa Supabase como
  recomendación principal por el modelo relacional y RLS.

### Esquema de base de datos (Postgres)

```sql
-- Perfil (1:1 con auth.users). El progreso vive en la nube → multidispositivo.
create table profiles (
  id          uuid primary key references auth.users(id) on delete cascade,
  username    text unique not null,
  is_admin    boolean not null default false,
  xp          integer not null default 0,
  streak_days integer not null default 0,
  created_at  timestamptz not null default now(),
  last_active timestamptz not null default now()
);

-- Progreso por lección.
create table lesson_progress (
  user_id     uuid references profiles(id) on delete cascade,
  lesson_id   text not null,            -- p.ej. "l1-u1-1"
  status      text not null default 'in_progress', -- in_progress | completed | mastered
  score       integer,                  -- 0..100
  attempts    integer not null default 0,
  completed_at timestamptz,
  primary key (user_id, lesson_id)
);

-- Badges obtenidos.
create table user_badges (
  user_id   uuid references profiles(id) on delete cascade,
  badge_id  text not null,
  earned_at timestamptz not null default now(),
  primary key (user_id, badge_id)
);

-- Historial de eventos (para "historial de progreso" en el perfil).
create table activity_log (
  id         bigint generated always as identity primary key,
  user_id    uuid references profiles(id) on delete cascade,
  event      text not null,             -- lesson_completed | checkpoint_passed | badge_earned
  payload    jsonb,
  created_at timestamptz not null default now()
);
```

### Row Level Security (cada usuario su propio perfil; admin ve todo)

```sql
alter table profiles        enable row level security;
alter table lesson_progress enable row level security;

-- Un usuario solo lee/escribe su propia fila.
create policy "own_profile" on profiles
  for all using (auth.uid() = id) with check (auth.uid() = id);

create policy "own_progress" on lesson_progress
  for all using (auth.uid() = user_id) with check (auth.uid() = user_id);

-- Admin puede leer todo (para estadísticas).
create policy "admin_reads_all" on profiles
  for select using (
    exists (select 1 from profiles p where p.id = auth.uid() and p.is_admin)
  );
```

> **Usuario admin/admin:** se crea en un script de *seed* (`supabase/seed.sql` + función SQL)
> que inserta el usuario `admin` con `is_admin = true`. En producción se recomienda forzar el
> cambio de contraseña en el primer login (se documenta como advertencia de seguridad, ya que
> `admin/admin` es una credencial débil pensada solo para arranque/demo).

---

## 4. Wireframes conceptuales (mobile-first)

Diseñados primero para **360 px** de ancho (móvil) y luego ampliados a tablet/desktop con
*media queries*. Componentes grandes, táctiles, una acción primaria por pantalla.

### 4.1 Onboarding / Registro
```
┌─────────────────────┐
│      🟣 Claude       │
│   Code Duolingo      │
│                     │
│  Aprende Claude y    │
│  Claude Code jugando │
│                     │
│ ┌─────────────────┐ │
│ │  Crear cuenta   │ │  ← gratis, email + contraseña
│ └─────────────────┘ │
│ ┌─────────────────┐ │
│ │  Iniciar sesión │ │
│ └─────────────────┘ │
└─────────────────────┘
```

### 4.2 Home / Mapa de niveles (el "árbol")
```
┌─────────────────────┐
│ 🔥3   ⭐240xp   👤  │  ← racha, XP, perfil
├─────────────────────┤
│  NIVEL 1 · Básico   │
│   ✅ ─ ✅ ─ ✅       │
│         │           │
│   🟢 (lección actual)│  ← botón grande, "Continuar"
│         │           │
│   🔒 ─ 🔒           │
├─────────────────────┤
│  NIVEL 2 · 🔒        │  ← se desbloquea al pasar checkpoint N1
└─────────────────────┘
[ Inicio ] [ Logros ] [ Perfil ]   ← barra inferior fija (táctil)
```

### 4.3 Lección (Concepto → Ejemplo → Reto)
```
┌─────────────────────┐
│ ◀  Lección 1.3   ▓▓▓░│  ← progreso dentro de la lección
├─────────────────────┤
│  CONCEPTO            │
│  Claude puede        │
│  resumir, extraer... │
│                     │
│  EJEMPLO             │
│ ┌─ código ─────────┐ │
│ │ Prompt: ...      │ │
│ └──────────────────┘ │
│                     │
│ ┌─────────────────┐ │
│ │   Empezar reto  │ │  ← acción primaria
│ └─────────────────┘ │
└─────────────────────┘
```

### 4.4 Reto + Corrección
```
┌─────────────────────┐         ┌─────────────────────┐
│  RETO               │         │  ✅ ¡Correcto!       │
│  ¿Qué modelo para   │   →     │                     │
│  10k reseñas?       │         │  PORQUÉ:            │
│  ◯ Opus 4.8         │         │  Haiku 4.5 es el    │
│  ⬤ Haiku 4.5        │         │  más rápido y       │
│  ◯ Fable 5          │         │  barato para tareas │
│                     │         │  simples de volumen.│
│ ┌─────────────────┐ │         │ ┌─────────────────┐ │
│ │   Comprobar     │ │         │ │   Continuar     │ │
│ └─────────────────┘ │         │ └─────────────────┘ │
└─────────────────────┘         └─────────────────────┘
```
Si falla: la corrección muestra el **error común** seleccionado y *por qué* es incorrecto,
además de la respuesta correcta y su razonamiento.

### 4.5 Perfil (progreso + historial)
```
┌─────────────────────┐
│   👤  patrick        │
│   ⭐ 240 XP · 🔥 3d  │
├─────────────────────┤
│  Progreso           │
│  Nivel 1 ▓▓▓▓▓ 100% │
│  Nivel 2 ▓▓░░░  40% │
│  Nivel 3 ░░░░░   0% │
├─────────────────────┤
│  Logros 🏅🏅🏅       │
├─────────────────────┤
│  Historial          │
│  • Completaste 2.3  │
│  • Insignia "MCP"   │
└─────────────────────┘
```

### 4.6 Panel de Admin (solo `is_admin`)
```
┌─────────────────────┐
│  ADMIN              │
│  Usuarios: 128      │
│  Activos 7d: 54     │
│  Lección + difícil: │
│   2.7 (38% acierto) │
├─────────────────────┤
│  Contenido          │
│  Editar lecciones → │  (abre PR en GitHub / editor)
└─────────────────────┘
```

**Reglas de UX (criterios de calidad):**
- Una acción primaria por pantalla; botones ≥ 44 px de alto.
- Barra de navegación inferior fija en móvil (Inicio · Logros · Perfil).
- Feedback inmediato (correcto/incorrecto en < 200 ms para retos locales).
- Sin jerga innecesaria; cada término técnico se introduce con una frase simple.
- Modo oscuro/claro automático (`prefers-color-scheme`).
- Accesible: contraste AA, navegación por teclado, `aria-labels`.

---

## 5. Gamificación

| Mecánica | Implementación |
|---|---|
| **Progreso visual** | Barras por nivel/unidad y % global, calculado desde `lesson_progress`. |
| **XP** | Cada lección otorga `xp`; checkpoints y retos extra dan bonus. |
| **Badges** | Insignias por hitos: "Primer prompt", "Instalé Claude Code", "Configuré un MCP", "Maestro de Skills", etc. Guardadas en `user_badges`. |
| **Racha (streak)** | `streak_days` se incrementa con actividad diaria; se reinicia si hay un día sin actividad. |
| **Dificultad creciente** | Retos ordenados por dificultad dentro de cada unidad; el proyecto final (3.7) se evalúa por rúbrica. |
| **Correcciones con "porqué"** | Cada reto incluye `why` + `commonMistakes[]` → el usuario entiende el razonamiento, no solo el resultado. |
| **Historial** | `activity_log` alimenta la sección Historial del perfil. |

---

## 6. Flujo de usuario (de extremo a extremo)

1. Llega a la app → **Crear cuenta** (email + contraseña, gratis, sin GitHub).
2. Se crea su `profile` en Supabase → empieza en **Nivel 1**.
3. Completa micro-lecciones (Concepto → Ejemplo → Reto) con **feedback inmediato y el porqué**.
4. Al terminar una unidad, pasa el **checkpoint** (≥ 80 %) para avanzar.
5. El progreso se guarda automáticamente en la nube tras cada reto (`lesson_progress`).
6. Abre la app en **otro dispositivo**, inicia sesión y **continúa donde lo dejó**.
7. Avanza a Nivel 3 e implementa un **ecosistema real** (MCP + skills + subagentes + conectores).
8. Obtiene badges y mantiene su racha; el admin observa estadísticas globales.

---

## 7. Plan de implementación (frontend + backend + GitHub)

### Fase 0 — Andamiaje (repo + CI)
- Crear repo **Claude Code Duolingo** en GitHub.
- Estructura inicial (§8) + `README` + licencia.
- GitHub Actions: validar JSON de contenido y desplegar a Pages.

### Fase 1 — Backend (Supabase)
- Crear proyecto Supabase, aplicar `schema.sql` y políticas RLS.
- Activar Auth email/contraseña.
- `seed.sql`: crear `admin/admin` con `is_admin = true`.

### Fase 2 — Frontend núcleo
- Scaffold Vite + PWA (manifest + service worker).
- Pantallas: Registro/Login, Home (mapa), Lección, Reto/Corrección, Perfil.
- Integrar `supabase-js`: registro, login, leer/escribir progreso.
- Cargar contenido desde `/content/manifest.json` y archivos de lección.

### Fase 3 — Gamificación + Admin
- XP, badges, racha, barras de progreso, historial.
- Panel admin (estadísticas + acceso a edición de contenido).

### Fase 4 — Contenido
- Redactar Nivel 1 completo (verificado), luego Niveles 2 y 3.
- Incluir los **10 casos prácticos** (§10) como lecciones del Nivel 2–3.

### Fase 5 — IA opcional (corrección de retos abiertos)
- Edge Function de Supabase que llama a la Claude API para evaluar `free-text` (§9).

### Fase 6 — Pulido y QA
- Responsive en móvil/tablet/desktop; pruebas de accesibilidad; pruebas de flujo multidispositivo.

---

## 8. Estrategia de almacenamiento en el repo `Claude Code Duolingo`

```
Claude Code Duolingo/
├─ README.md
├─ docs/
│  └─ ESPECIFICACION_CLAUDE_CODE_DUOLINGO.md   ← este documento
├─ public/                      # estáticos servidos tal cual
│  ├─ manifest.webmanifest      # PWA
│  └─ icons/
├─ src/
│  ├─ index.html
│  ├─ main.js                   # bootstrap + router
│  ├─ lib/supabase.js           # cliente Supabase
│  ├─ views/                    # home, lesson, challenge, profile, admin
│  ├─ components/               # botones, barras de progreso, etc.
│  └─ styles/                   # CSS mobile-first
├─ content/                     # CONTENIDO COMO DATOS (editable por PR)
│  ├─ manifest.json             # orden, prerequisitos, checkpoints
│  ├─ level1/unit1/*.json
│  ├─ level2/...
│  └─ level3/...
├─ supabase/
│  ├─ schema.sql                # tablas + RLS
│  ├─ seed.sql                  # usuario admin
│  └─ functions/grade-free-text/ # Edge Function (Claude API)
├─ scripts/
│  └─ validate-content.mjs      # valida JSON contra un esquema
├─ .github/workflows/
│  ├─ ci.yml                    # lint + validar contenido en cada PR
│  └─ deploy.yml                # build + deploy a GitHub Pages
└─ .env.example                 # SUPABASE_URL, SUPABASE_ANON_KEY (públicas)
```

**Convenciones:**
- El contenido nuevo se añade por **Pull Request**; CI valida el esquema JSON antes de fusionar.
- Secretos (Claude API key) viven en **GitHub Actions Secrets** / variables de entorno de la
  Edge Function — **nunca** en el repo. El `.env.example` solo lista claves públicas (anon key).
- `main` protegida; los agentes/colaboradores trabajan en ramas y abren PR.

### CI/CD (GitHub Actions) — ejemplos

```yaml
# .github/workflows/ci.yml
name: CI
on: { pull_request: { branches: [main] } }
jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci
      - run: node scripts/validate-content.mjs   # valida todos los content/**.json
      - run: npm run build
```

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: { push: { branches: [main] } }
permissions: { contents: read, pages: write, id-token: write }
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: github-pages
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: 20 }
      - run: npm ci && npm run build
      - uses: actions/upload-pages-artifact@v3
        with: { path: dist }
      - uses: actions/deploy-pages@v4
```

---

## 9. IA dentro de la app (opcional, para retos abiertos)

Para corregir retos `free-text` (p. ej. "escribe un `CLAUDE.md` mínimo") se usa la **Claude API**
desde una Edge Function de Supabase (la clave nunca toca el cliente).

- **Modelo recomendado:** `claude-haiku-4-5` — rápido y económico, suficiente para evaluar
  contra una rúbrica corta. Si se quiere feedback de mayor calidad, `claude-sonnet-4-6`.
- **Para generar/curar contenido del curso** (fuera de runtime): `claude-opus-4-8`.
- Se usa **salida estructurada** (`output_config.format`) para obtener `{ correcto, puntuacion, feedback }`.

```python
# supabase/functions/grade-free-text  (pseudocódigo Python equivalente)
import anthropic
client = anthropic.Anthropic()

resp = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=1024,
    system="Eres un evaluador. Compara la respuesta del alumno con la rúbrica. "
           "Devuelve JSON con correcto (bool), puntuacion (0-100) y feedback breve y amable.",
    messages=[{"role": "user", "content": f"RÚBRICA:\n{rubric}\n\nRESPUESTA:\n{answer}"}],
    output_config={"format": {"type": "json_schema", "schema": {
        "type": "object",
        "properties": {
            "correcto":   {"type": "boolean"},
            "puntuacion": {"type": "integer"},
            "feedback":   {"type": "string"}
        },
        "required": ["correcto", "puntuacion", "feedback"],
        "additionalProperties": False
    }}},
)
```

> El "porqué" mostrado al alumno combina el `feedback` generado con un `why` curado por el
> autor de la lección, para garantizar precisión pedagógica.

---

## 10. Primeros 10 casos prácticos (para enseñar Claude Code desde cero)

Cada caso es una lección práctica e **implementable directamente** en Claude Code. Siguen la
estructura Concepto → Ejemplo → Reto → Corrección.

| # | Caso práctico | Qué aprende | Reto |
|---|---|---|---|
| 1 | **Instalar y abrir Claude Code en un repo** | Instalación, autenticación, primer prompt en un proyecto real | Hacer que Claude resuma qué hace el repo |
| 2 | **Crear el `CLAUDE.md` con `/init`** | Documentar el proyecto para que Claude tenga contexto | Añadir al `CLAUDE.md` cómo se ejecutan los tests |
| 3 | **Arreglar un bug guiado** | Bucle agéntico: leer → editar → ejecutar tests → iterar | Pedir el fix + verificar que los tests pasan |
| 4 | **Añadir una feature pequeña** | Plan Mode, edición multi-archivo, verificación | Implementar una función y su test |
| 5 | **Buscar en el código con Grep/Glob** | Herramientas de búsqueda y navegación | Encontrar dónde se define una función |
| 6 | **Crear un slash command personalizado** | Comandos reutilizables del proyecto | Crear `/test` que ejecute la suite |
| 7 | **Conectar el MCP de GitHub** | MCP + conectores: ver PRs, issues, crear PR | Configurar el servidor MCP y listar PRs |
| 8 | **Escribir una Skill** | Carpeta + `SKILL.md`, divulgación progresiva | Crear una skill para "generar changelog" |
| 9 | **Definir una Tool personalizada** | Esquema de entrada, tool cliente vs servidor | Diseñar el `input_schema` de una tool |
| 10 | **Flujo completo PR → review → deploy** | Subagentes + hooks + GitHub Actions; ecosistema end-to-end | Diagramar y configurar el flujo CI/CD |

Estos 10 casos cubren la progresión Nivel 2 → Nivel 3 y desembocan en el **proyecto final (3.7)**.

---

## 11. Conectores y herramientas externas recomendados

Para **operacionalizar la plataforma** (desarrollo, versionado, despliegue y sincronización):

| Necesidad | Herramienta / conector | Capa gratuita | Rol |
|---|---|---|---|
| Código + contenido + issues + PR | **GitHub** | Sí | Fuente de verdad; todo en el repo `Claude Code Duolingo`. |
| CI/CD | **GitHub Actions** | Sí | Validar contenido, build, deploy. |
| Hosting | **GitHub Pages** | Sí | Servir la PWA estática. |
| Auth + DB + perfiles en la nube | **Supabase** (o Firebase) | Sí | Registro, login, progreso multidispositivo, RLS. |
| Funciones serverless (corrección IA) | **Supabase Edge Functions** | Sí | Llamar a la Claude API sin exponer la clave. |
| IA de corrección / generación de contenido | **Claude API** (Anthropic) | De pago por uso | Evaluar `free-text`, curar contenido. |
| Conector GitHub para Claude Code (enseñanza) | **GitHub MCP server** | Sí | Que el alumno practique PRs/issues desde Claude Code. |
| Conectores adicionales (didácticos) | **MCP servers** (Drive, Slack, etc.) | Según servicio | Ejemplos reales de ecosistema en Nivel 3. |

### Integración con GitHub para gestionar el desarrollo
- **Versionado:** ramas + PR; `main` protegida; revisión por PR (puede usar `/review` de Claude Code).
- **Sincronización de datos:** webhooks de GitHub → Actions para revalidar/desplegar contenido al fusionar.
- **Automatización:** Actions para lint, validación de JSON, build y deploy continuo.
- **Enseñanza in-app:** el conector GitHub MCP se usa como *contenido* del Nivel 3 (caso #7 y #10),
  de modo que el alumno aprende exactamente el flujo que mantiene la propia plataforma.

---

## 12. Mapa de criterios de calidad → cómo se cumplen

| Criterio del encargo | Cómo lo cumple esta spec |
|---|---|
| Interfaz amigable, no abrumadora | Una acción por pantalla, navegación inferior, estilo Duolingo (§4). |
| Totalmente usable en móvil | Mobile-first, PWA instalable, botones táctiles, offline básico (§3, §4). |
| Contenido verificable y práctico | Casos reales implementables en Claude Code; contenido revisado por PR (§10, §8). |
| Lenguaje accesible | Cada término se introduce con una frase simple; sin jerga innecesaria (§1). |
| Cada corrección explica el "porqué" | Campos `why` + `commonMistakes[]` en cada reto (§2, §4.4). |
| Guardar/recuperar perfiles robusto | Supabase + RLS; progreso por lección en la nube (§3). |
| Escalable sin reorganizar | Contenido como datos: nuevas lecciones = nuevos JSON + manifest (§2, §8). |
| Registro directo y gratuito sin GitHub | Auth email/contraseña de Supabase (§3, §6). |
| Admin predefinido | `admin/admin` por seed + panel de estadísticas/gestión (§3, §4.6). |
| Multidispositivo | Estado en la nube; iniciar sesión y continuar (§6). |

---

## 13. Notas de seguridad

- `admin/admin` es solo para arranque/demo: forzar cambio de contraseña en el primer login.
- Claves de Claude API y service-role de Supabase solo en secretos de servidor/Actions; nunca en el cliente ni en el repo.
- RLS activa por defecto en todas las tablas con datos de usuario.
- Validación de entrada en la Edge Function antes de llamar a la Claude API.
- La `anon key` de Supabase es pública por diseño; la seguridad la dan las políticas RLS, no ocultar la key.

---

*Fin de la especificación.*
