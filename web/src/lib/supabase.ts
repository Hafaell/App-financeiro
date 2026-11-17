import { createClient, SupabaseClient } from '@supabase/supabase-js'

// URL e chave pública do Supabase (as mesmas do app desktop). No Vercel, vêm das variáveis
// VITE_SUPABASE_URL e VITE_SUPABASE_CHAVE; no PC, de web/.env.local.
const url = import.meta.env.VITE_SUPABASE_URL as string | undefined
const chave = import.meta.env.VITE_SUPABASE_CHAVE as string | undefined

// Modo local: sem login, contra a API local com dados de teste (python -m controle_financeiro.web.local)
export const MODO_LOCAL = import.meta.env.VITE_MODO_LOCAL === '1'

export const configurado = MODO_LOCAL || Boolean(url && chave)

export const supabase: SupabaseClient | null =
  url && chave && !MODO_LOCAL ? createClient(url, chave, { auth: { persistSession: true } }) : null
