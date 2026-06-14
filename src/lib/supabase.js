import { createClient } from '@supabase/supabase-js'

const url = import.meta.env.VITE_SUPABASE_URL
const anon = import.meta.env.VITE_SUPABASE_ANON_KEY

// La app funciona en dos modos:
//  • Conectada: si hay URL + anon key de Supabase → auth y progreso en la nube.
//  • Demo:      sin configurar → todo en localStorage (para probar/desplegar sin backend).
// La lógica de negocio (perfil, progreso, badges) vive en src/lib/store.js, que
// elige el backend según este flag.
export const isSupabaseConfigured = Boolean(url && anon)

export const supabase = isSupabaseConfigured ? createClient(url, anon) : null
