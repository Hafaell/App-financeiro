import { FormEvent, ReactNode, useEffect, useId, useRef, useState } from 'react'
import { brl } from '../lib/formato'
import type { Cartao } from '../lib/tipos'

export function Pagina({ titulo, descricao, acoes, children }: {
  titulo: string
  descricao?: string
  acoes?: ReactNode
  children: ReactNode
}) {
  useEffect(() => {
    document.title = `${titulo} · Controle Financeiro`
  }, [titulo])
  return (
    <section className="pagina">
      <header className="pagina-topo">
        <div>
          <h1>{titulo}</h1>
          {descricao && <p className="suave">{descricao}</p>}
        </div>
        {acoes && <div className="pagina-acoes">{acoes}</div>}
      </header>
      {children}
    </section>
  )
}

export function Secao({ titulo, descricao, acoes, children }: {
  titulo: string
  descricao?: string
  acoes?: ReactNode
  children: ReactNode
}) {
  return (
    <section className="secao">
      <header className="secao-topo">
        <div>
          <h2>{titulo}</h2>
          {descricao && <p className="suave pequeno">{descricao}</p>}
        </div>
        {acoes}
      </header>
      {children}
    </section>
  )
}

export type Tom = 'normal' | 'positivo' | 'aviso' | 'negativo'

/** Painel único com divisórias (o FaixaNumeros do desktop). */
export function FaixaNumeros({ children }: { children: ReactNode }) {
  return <div className="faixa">{children}</div>
}

export function Metrica({ rotulo, valor, detalhe, tom = 'normal' }: {
  rotulo: string
  valor: ReactNode
  detalhe?: ReactNode
  tom?: Tom
}) {
  return (
    <div className="metrica">
      <span className="metrica-rotulo">{rotulo}</span>
      <strong className={`metrica-valor tom-${tom}`}>{valor}</strong>
      {detalhe && <span className="metrica-detalhe">{detalhe}</span>}
    </div>
  )
}

export function Barra({ valor, total, cor, excedida }: { valor: number; total: number; cor?: string; excedida?: boolean }) {
  const largura = total > 0 ? Math.min(100, (valor / total) * 100) : 0
  return (
    <div className="barra" aria-hidden="true">
      <div className={`barra-cheia${excedida ? ' excedida' : ''}`}
        style={{ width: `${largura}%`, background: excedida ? undefined : cor }} />
    </div>
  )
}

export function SeloCartao({ nome, cartoes }: { nome: string; cartoes: Cartao[] }) {
  const c = cartoes.find((x) => x.nome === nome)
  return (
    <span className="selo" style={c ? { background: c.cor, color: c.cor_texto } : undefined}>{nome}</span>
  )
}

export function Valor({ v, tom }: { v: number; tom?: Tom }) {
  return <span className={`num${tom ? ` tom-${tom}` : ''}`}>{brl(v)}</span>
}

export function Carregando() {
  return <div className="carregando" role="status"><span className="giro" />Carregando…</div>
}

export function ErroCarga({ mensagem, tentarDeNovo }: { mensagem: string; tentarDeNovo: () => void }) {
  return (
    <div className="erro-carga" role="alert">
      <p>{mensagem}</p>
      <button className="botao" onClick={tentarDeNovo}>Tentar de novo</button>
    </div>
  )
}

export function Vazio({ children }: { children: ReactNode }) {
  return <p className="vazio">{children}</p>
}

/** Janela sobre a página (no celular, sobe de baixo). Fecha com Esc ou clicando fora. */
export function Modal({ titulo, aberto, fechar, children, largo }: {
  titulo: string
  aberto: boolean
  fechar: () => void
  children: ReactNode
  largo?: boolean
}) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => {
    const d = ref.current
    if (!d) return
    if (aberto && !d.open) d.showModal()
    if (!aberto && d.open) d.close()
  }, [aberto])
  return (
    <dialog
      ref={ref}
      className={`modal${largo ? ' modal-largo' : ''}`}
      onClose={fechar}
      onClick={(e) => e.target === ref.current && fechar()}
      aria-label={titulo}
    >
      {aberto && (
        <div className="modal-corpo">
          <header className="modal-topo">
            <h2>{titulo}</h2>
            <button type="button" className="icone-botao" aria-label="Fechar" onClick={fechar}>×</button>
          </header>
          {children}
        </div>
      )}
    </dialog>
  )
}

/** Formulário de modal: mostra o erro do servidor embaixo e trava o botão enquanto salva. */
export function Formulario({ enviar, rotulo = 'Salvar', children, extra }: {
  enviar: () => Promise<void>
  rotulo?: string
  children: ReactNode
  extra?: ReactNode
}) {
  const [erro, setErro] = useState<string | null>(null)
  const [salvando, setSalvando] = useState(false)
  const aoEnviar = async (e: FormEvent) => {
    e.preventDefault()
    setSalvando(true)
    setErro(null)
    try {
      await enviar()
    } catch (err) {
      setErro(err instanceof Error ? err.message : String(err))
    } finally {
      setSalvando(false)
    }
  }
  return (
    <form className="formulario" onSubmit={aoEnviar}>
      {children}
      {erro && <p className="erro-form" role="alert">{erro}</p>}
      <div className="form-acoes">
        {extra}
        <button className="botao primario" disabled={salvando}>{salvando ? 'Salvando…' : rotulo}</button>
      </div>
    </form>
  )
}

export function Campo({ rotulo, dica, children }: { rotulo: string; dica?: string; children: (id: string) => ReactNode }) {
  const id = useId()
  return (
    <div className="campo">
      <label htmlFor={id}>{rotulo}</label>
      {children(id)}
      {dica && <span className="dica">{dica}</span>}
    </div>
  )
}

/** Pergunta antes de uma ação sem volta. Uso: const [perguntar, janela] = useConfirmar() */
export function useConfirmar(): [(texto: string, acao: () => Promise<void>, botao?: string) => void, ReactNode] {
  const [pedido, setPedido] = useState<{ texto: string; acao: () => Promise<void>; botao: string } | null>(null)
  const [erro, setErro] = useState<string | null>(null)
  const [ocupado, setOcupado] = useState(false)
  const fechar = () => {
    setPedido(null)
    setErro(null)
  }
  const janela = (
    <Modal titulo="Confirmar" aberto={pedido !== null} fechar={fechar}>
      <p className="confirmar-texto">{pedido?.texto}</p>
      {erro && <p className="erro-form" role="alert">{erro}</p>}
      <div className="form-acoes">
        <button className="botao" onClick={fechar}>Cancelar</button>
        <button
          className="botao perigo"
          disabled={ocupado}
          onClick={async () => {
            if (!pedido) return
            setOcupado(true)
            try {
              await pedido.acao()
              fechar()
            } catch (e) {
              setErro(e instanceof Error ? e.message : String(e))
            } finally {
              setOcupado(false)
            }
          }}
        >
          {ocupado ? 'Aguarde…' : pedido?.botao}
        </button>
      </div>
    </Modal>
  )
  return [(texto, acao, botao = 'Apagar') => setPedido({ texto, acao, botao }), janela]
}

export function Abas<T extends string>({ opcoes, valor, mudar }: {
  opcoes: { valor: T; rotulo: string }[]
  valor: T
  mudar: (v: T) => void
}) {
  return (
    <div className="abas" role="tablist">
      {opcoes.map((o) => (
        <button key={o.valor} role="tab" aria-selected={o.valor === valor}
          className={`aba${o.valor === valor ? ' ativa' : ''}`} onClick={() => mudar(o.valor)}>
          {o.rotulo}
        </button>
      ))}
    </div>
  )
}
