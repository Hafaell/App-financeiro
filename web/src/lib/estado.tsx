import { createContext, ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { get, post } from './api'
import type { Inicio } from './tipos'

interface Aviso {
  id: number
  texto: string
  tipo: 'ok' | 'erro'
  desfazer?: () => Promise<void>
}

interface Estado {
  inicio: Inicio
  mes: string
  escolherMes: (mes: string) => void
  /** Aumenta a cada alteração (sua ou de outro aparelho): as páginas recarregam ao mudar. */
  versao: number
  /** Chame depois de gravar algo: recarrega as listas e avisa as páginas. */
  atualizar: () => Promise<void>
  avisar: (texto: string, desfazer?: () => Promise<void>) => void
  falhar: (erro: unknown) => void
  nomeCategoria: (id: number | null | undefined) => string
}

const Contexto = createContext<Estado | null>(null)

export function useEstado() {
  const e = useContext(Contexto)
  if (!e) throw new Error('useEstado fora do ProvedorEstado')
  return e
}

const INTERVALO_VERSAO = 15_000 // confere se outro aparelho (ou a Ayla) mudou algo

export function ProvedorEstado({ inicio: inicial, children }: { inicio: Inicio; children: ReactNode }) {
  const [inicio, setInicio] = useState(inicial)
  const [mes, setMes] = useState(inicial.mes_ativo)
  const [versao, setVersao] = useState(0)
  const [avisos, setAvisos] = useState<Aviso[]>([])
  const versaoRemota = useRef(inicial.versao)
  const contador = useRef(0)

  const atualizar = useCallback(async () => {
    const novo = await get<Inicio>('/api/inicio')
    versaoRemota.current = novo.versao
    setInicio(novo)
    // Se o mês escolhido sumiu (apagado) ou a virada abriu um novo, vai para o atual
    setMes((m) => (novo.meses.includes(m) && novo.mes_ativo === inicio.mes_ativo ? m : novo.mes_ativo))
    setVersao((v) => v + 1)
  }, [inicio.mes_ativo])

  useEffect(() => {
    const conferir = async () => {
      if (document.hidden) return
      try {
        const { versao: v } = await get<{ versao: number }>('/api/versao')
        if (v !== versaoRemota.current) await atualizar()
      } catch {
        /* sem rede agora: tenta na próxima */
      }
    }
    const id = window.setInterval(conferir, INTERVALO_VERSAO)
    document.addEventListener('visibilitychange', conferir)
    return () => {
      window.clearInterval(id)
      document.removeEventListener('visibilitychange', conferir)
    }
  }, [atualizar])

  const tirar = (id: number) => setAvisos((l) => l.filter((a) => a.id !== id))

  const avisar = useCallback((texto: string, desfazer?: () => Promise<void>) => {
    const id = ++contador.current
    setAvisos((l) => [...l.slice(-2), { id, texto, tipo: 'ok', desfazer }])
    window.setTimeout(() => tirar(id), desfazer ? 30_000 : 4_000) // "Desfazer" fica 30 s, como no desktop
  }, [])

  const falhar = useCallback((erro: unknown) => {
    const id = ++contador.current
    const texto = erro instanceof Error ? erro.message : String(erro)
    setAvisos((l) => [...l.slice(-2), { id, texto, tipo: 'erro' }])
    window.setTimeout(() => tirar(id), 7_000)
  }, [])

  const nomeCategoria = useCallback(
    (id: number | null | undefined) => inicio.categorias.find((c) => c.id === id)?.nome ?? 'Sem categoria',
    [inicio.categorias],
  )

  const estado: Estado = {
    inicio, mes, escolherMes: setMes, versao, atualizar, avisar, falhar, nomeCategoria,
  }

  return (
    <Contexto.Provider value={estado}>
      {children}
      <div className="avisos" role="status" aria-live="polite">
        {avisos.map((a) => (
          <div key={a.id} className={`aviso aviso-${a.tipo}`}>
            <span>{a.texto}</span>
            {a.desfazer && (
              <button
                className="aviso-acao"
                onClick={async () => {
                  tirar(a.id)
                  try {
                    await a.desfazer!()
                    await atualizar()
                    avisar('Exclusão desfeita.')
                  } catch (e) {
                    falhar(e)
                  }
                }}
              >
                Desfazer
              </button>
            )}
            <button className="aviso-fechar" aria-label="Fechar aviso" onClick={() => tirar(a.id)}>×</button>
          </div>
        ))}
      </div>
    </Contexto.Provider>
  )
}

/** Recolocar uma linha apagada (o "Desfazer" depois de apagar compra, receita ou despesa). */
export const recolocar = (tabela: 'compras' | 'receitas' | 'despesas', linha: unknown) =>
  post('/api/recolocar', { tabela, linha }).then(() => undefined)

/** Carrega dados de uma página e recarrega quando o mês ou a versão mudam. */
export function useDados<T>(carregar: () => Promise<T>, deps: unknown[] = []) {
  const { mes, versao, falhar } = useEstado()
  const [dados, setDados] = useState<T | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState<string | null>(null)
  const [tentativa, setTentativa] = useState(0)

  useEffect(() => {
    let vivo = true
    setCarregando(true)
    carregar()
      .then((d) => {
        if (!vivo) return
        setDados(d)
        setErro(null)
      })
      .catch((e) => {
        if (!vivo) return
        setErro(e instanceof Error ? e.message : String(e))
        if (dados !== null) falhar(e)
      })
      .finally(() => vivo && setCarregando(false))
    return () => {
      vivo = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [mes, versao, tentativa, ...deps])

  return { dados, carregando, erro, tentarDeNovo: () => setTentativa((t) => t + 1) }
}
