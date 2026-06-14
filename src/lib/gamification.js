// Definición de insignias (badges). Cada badge tiene una condición evaluada
// contra el estado del usuario (perfil + progreso) tras completar una lección.

export const BADGES = [
  {
    id: 'first-prompt',
    name: 'Primer prompt',
    icon: '✍️',
    desc: 'Completaste tu primera lección.',
    earned: ({ completedCount }) => completedCount >= 1,
  },
  {
    id: 'level1-done',
    name: 'Fundamentos de Claude',
    icon: '🎓',
    desc: 'Terminaste todo el Nivel 1.',
    earned: ({ levelCompleted }) => levelCompleted[1],
  },
  {
    id: 'installed-cc',
    name: 'Instalé Claude Code',
    icon: '⚡',
    desc: 'Completaste la unidad de instalación (2.2).',
    earned: ({ completed }) => completed.has('l2-u2-1'),
  },
  {
    id: 'mcp-master',
    name: 'Configuré un MCP',
    icon: '🔌',
    desc: 'Completaste la lección de MCP (3.1).',
    earned: ({ completed }) => completed.has('l3-u1-1'),
  },
  {
    id: 'skill-master',
    name: 'Maestro de Skills',
    icon: '🧩',
    desc: 'Completaste la lección de Skills (3.2).',
    earned: ({ completed }) => completed.has('l3-u2-1'),
  },
  {
    id: 'streak-3',
    name: 'Racha de 3 días',
    icon: '🔥',
    desc: 'Practicaste 3 días seguidos.',
    earned: ({ profile }) => (profile?.streak_days ?? 0) >= 3,
  },
  {
    id: 'xp-100',
    name: '100 XP',
    icon: '⭐',
    desc: 'Acumulaste 100 puntos de experiencia.',
    earned: ({ profile }) => (profile?.xp ?? 0) >= 100,
  },
]

// Devuelve los ids de badge que el usuario CUMPLE dado su estado actual.
export function evaluateBadges(ctx) {
  return BADGES.filter((b) => {
    try { return b.earned(ctx) } catch { return false }
  }).map((b) => b.id)
}

export function badgeById(id) {
  return BADGES.find((b) => b.id === id)
}
