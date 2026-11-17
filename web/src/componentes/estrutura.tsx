import { ReactNode, useEffect, useState } from 'react'
import { useEstado } from '../lib/estado'
import { nomeMes } from '../lib/formato'
import { Lancar } from './formularios'

export interface ItemMenu {
  caminho: string
  rotulo: string
  curto?: string
}

/** Mesmas seções do menu do desktop (ui/janela.py). */
export const SECOES: { titulo: string; itens: ItemMenu[] }[] = [
  {
    titulo: 'Geral',
    itens: [
      { caminho: '/', rotulo: 'Visão geral', curto: 'Início' },
      { caminho: '/transacoes', rotulo: 'Transações' },
      { caminho: '/receitas-e-despesas', rotulo: 'Receitas e despesas' },
      { caminho: '/planejamento', rotulo: 'Planejamento' },
      { caminho: '/comparativo', rotulo: 'Comparativo' },
    ],
  },
  {
    titulo: 'Pessoal',
    itens: [
      { caminho: '/emprestimos', rotulo: 'Empréstimos' },
      { caminho: '/caixinhas', rotulo: 'Caixinhas' },
    ],
  },
  {
    titulo: 'Sistema',
    itens: [
      { caminho: '/importar', rotulo: 'Importar extrato' },
      { caminho: '/ferramentas', rotulo: 'Ferramentas' },
    ],
  },
]

const TODOS = SECOES.flatMap((s) => s.itens)

export function useRota(): [string, (c: string) => void] {
  const [caminho, setCaminho] = useState(window.location.pathname)
  useEffect(() => {
    const voltar = () => setCaminho(window.location.pathname)
    window.addEventListener('popstate', voltar)
    return () => window.removeEventListener('popstate', voltar)
  }, [])
  const ir = (c: string) => {
    if (c !== window.location.pathname) window.history.pushState(null, '', c)
    setCaminho(c)
    window.scrollTo(0, 0)
  }
  return [TODOS.some((i) => i.caminho === caminho) ? caminho : '/', ir]
}

function Link({ item, atual, ir, classe }: { item: ItemMenu; atual: string; ir: (c: string) => void; classe: string }) {
  return (
    <a href={item.caminho} className={classe} aria-current={item.caminho === atual ? 'page' : undefined}
      onClick={(e) => {
        e.preventDefault()
        ir(item.caminho)
      }}>
      {item.rotulo}
    </a>
  )
}

export function SeletorMes() {
  const { inicio, mes, escolherMes } = useEstado()
  const i = inicio.meses.indexOf(mes)
  return (
    <div className="seletor-mes">
      <button className="seta" aria-label="Mês anterior" disabled={i <= 0}
        onClick={() => escolherMes(inicio.meses[i - 1])}>‹</button>
      <select aria-label="Mês" value={mes} onChange={(e) => escolherMes(e.target.value)}>
        {inicio.meses.map((m) => (
          <option key={m} value={m}>{nomeMes(m)}{m === inicio.mes_ativo ? ' (atual)' : ''}</option>
        ))}
      </select>
      <button className="seta" aria-label="Próximo mês" disabled={i >= inicio.meses.length - 1}
        onClick={() => escolherMes(inicio.meses[i + 1])}>›</button>
    </div>
  )
}

export function Estrutura({ atual, ir, nome, sair, children }: {
  atual: string
  ir: (c: string) => void
  nome: string
  sair?: () => void
  children: ReactNode
}) {
  const [lancar, setLancar] = useState(false)
  const [mais, setMais] = useState(false)
  const irE = (c: string) => {
    setMais(false)
    ir(c)
  }
  const naBarra = ['/', '/transacoes', '/emprestimos']
  return (
    <div className="estrutura">
      <aside className="lateral" aria-label="Menu">
        <div className="marca">
          <span className="marca-selo" aria-hidden="true">CF</span>
          <div>
            <strong>Controle Financeiro</strong>
            <span>Cartões, empréstimos e caixinhas</span>
          </div>
        </div>
        <nav>
          {SECOES.map((s) => (
            <div key={s.titulo} className="menu-secao">
              <span className="menu-titulo">{s.titulo}</span>
              {s.itens.map((item) => <Link key={item.caminho} item={item} atual={atual} ir={ir} classe="menu-item" />)}
            </div>
          ))}
        </nav>
        <div className="conta">
          <span className="conta-rotulo">Conectado como</span>
          <strong className="conta-nome">{nome}</strong>
          {sair && <button className="conta-botao" onClick={sair}>Sair</button>}
        </div>
      </aside>

      <div className="principal">
        <header className="topo">
          <span className="topo-marca" aria-hidden="true">CF</span>
          <SeletorMes />
        </header>
        <main id="conteudo">{children}</main>
      </div>

      <nav className="barra-inferior" aria-label="Menu principal">
        {naBarra.slice(0, 2).map((c) => {
          const item = TODOS.find((i) => i.caminho === c)!
          return <Link key={c} item={{ ...item, rotulo: item.curto ?? item.rotulo }} atual={atual} ir={irE} classe="aba-inferior" />
        })}
        <button className="aba-lancar" onClick={() => setLancar(true)} aria-label="Lançar">
          <span aria-hidden="true">+</span>
        </button>
        <Link item={TODOS.find((i) => i.caminho === '/emprestimos')!} atual={atual} ir={irE} classe="aba-inferior" />
        <button className="aba-inferior" aria-expanded={mais} aria-current={naBarra.includes(atual) ? undefined : 'page'}
          onClick={() => setMais((m) => !m)}>
          Mais
        </button>
      </nav>

      {mais && (
        <div className="folha-mais" role="dialog" aria-label="Mais páginas" onClick={() => setMais(false)}>
          <div className="folha-mais-corpo" onClick={(e) => e.stopPropagation()}>
            {SECOES.map((s) => (
              <div key={s.titulo} className="menu-secao">
                <span className="menu-titulo">{s.titulo}</span>
                {s.itens.filter((i) => !naBarra.includes(i.caminho)).map((item) => (
                  <Link key={item.caminho} item={item} atual={atual} ir={irE} classe="menu-item" />
                ))}
              </div>
            ))}
            <div className="conta conta-folha">
              <span className="conta-rotulo">Conectado como <strong>{nome}</strong></span>
              {sair && <button className="conta-botao" onClick={sair}>Sair</button>}
            </div>
          </div>
        </div>
      )}

      <Lancar aberto={lancar} fechar={() => setLancar(false)} />
    </div>
  )
}
