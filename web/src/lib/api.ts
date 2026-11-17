import { MODO_LOCAL, supabase } from './supabase'

export class ErroApi extends Error {
  constructor(mensagem: string, public status: number) {
    super(mensagem)
  }
}

async function token(): Promise<string | null> {
  if (MODO_LOCAL || !supabase) return null
  const { data } = await supabase.auth.getSession()
  return data.session?.access_token ?? null
}

async function chamar(metodo: string, caminho: string, corpo?: unknown, renovado = false): Promise<Response> {
  const cabecalhos: Record<string, string> = {}
  const t = await token()
  if (t) cabecalhos.Authorization = `Bearer ${t}`
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json'
  let resp: Response
  try {
    resp = await fetch(caminho, {
      method: metodo,
      headers: cabecalhos,
      body: corpo === undefined ? undefined : JSON.stringify(corpo),
    })
  } catch {
    throw new ErroApi('Sem conexão. Verifique a internet e tente de novo.', 0)
  }
  if (resp.status === 401 && supabase && !renovado) {
    // Token vencido: renova uma vez e repete; se não der, volta para o login
    const { error } = await supabase.auth.refreshSession()
    if (!error) return chamar(metodo, caminho, corpo, true)
    await supabase.auth.signOut()
  }
  if (!resp.ok) {
    let mensagem = `Algo deu errado (código ${resp.status}).`
    try {
      const dados = await resp.json()
      if (dados?.erro) mensagem = dados.erro
    } catch {
      /* resposta sem JSON */
    }
    throw new ErroApi(mensagem, resp.status)
  }
  return resp
}

export async function api<T = unknown>(metodo: string, caminho: string, corpo?: unknown): Promise<T> {
  const resp = await chamar(metodo, caminho, corpo)
  return (await resp.json()) as T
}

export const get = <T = unknown>(caminho: string) => api<T>('GET', caminho)
export const post = <T = unknown>(caminho: string, corpo: unknown = {}) => api<T>('POST', caminho, corpo)
export const patch = <T = unknown>(caminho: string, corpo: unknown) => api<T>('PATCH', caminho, corpo)
export const put = <T = unknown>(caminho: string, corpo: unknown) => api<T>('PUT', caminho, corpo)
export const del = <T = unknown>(caminho: string) => api<T>('DELETE', caminho)

/** Baixa um arquivo gerado pela API (ex.: backup com senha). */
export async function baixar(caminho: string, corpo: unknown, nomePadrao: string) {
  const resp = await chamar('POST', caminho, corpo)
  const blob = await resp.blob()
  const disposicao = resp.headers.get('content-disposition') ?? ''
  const nome = /filename="([^"]+)"/.exec(disposicao)?.[1] ?? nomePadrao
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = nome
  link.click()
  URL.revokeObjectURL(link.href)
}

export function q(params: Record<string, string | number | undefined>) {
  const p = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') p.set(k, String(v))
  const s = p.toString()
  return s ? `?${s}` : ''
}
