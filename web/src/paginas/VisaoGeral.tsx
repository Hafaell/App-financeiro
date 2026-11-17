import { useState } from 'react'
import { FormCompra, FormLancamento } from '../componentes/formularios'
import { Barra, Carregando, ErroCarga, FaixaNumeros, Metrica, Pagina, Secao, Vazio } from '../componentes/ui'
import { get, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, nomeMes, pct } from '../lib/formato'
import type { Alerta, Categoria, Gasto, Resumo, Tabela } from '../lib/tipos'

interface Painel {
  mes: string
  resumo: Resumo
  gasto: Gasto[]
  categorias: Categoria[]
  alertas: Alerta[]
  renda: number | null
}

const SEM_CATEGORIA = '#A9B7B3'

/** Visão geral: só os números do mês, para onde foi o dinheiro, orçamento e os botões de lançar. */
export function VisaoGeral() {
  const { mes } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() => get<Painel>(`/api/painel${q({ mes })}`))
  const [form, setForm] = useState<'compra' | Tabela | null>(null)

  const acoes = (
    <>
      <button className="botao primario" onClick={() => setForm('compra')}>Nova compra</button>
      <button className="botao" onClick={() => setForm('despesas')}>Nova despesa</button>
      <button className="botao" onClick={() => setForm('receitas')}>Nova receita</button>
    </>
  )

  return (
    <Pagina titulo="Visão geral" acoes={<div className="so-pc">{acoes}</div>}>
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} />
        : !dados ? <Carregando /> : <Conteudo p={dados} />}
      <FormCompra aberto={form === 'compra'} fechar={() => setForm(null)} />
      <FormLancamento aberto={form === 'despesas'} fechar={() => setForm(null)} tabela="despesas" />
      <FormLancamento aberto={form === 'receitas'} fechar={() => setForm(null)} tabela="receitas" />
    </Pagina>
  )
}

function Conteudo({ p }: { p: Painel }) {
  const r = p.resumo
  const saiu = r.despesas_manuais + r.meu_cartao_total
  const usoReceita = r.receitas > 0 ? (saiu / r.receitas) * 100 : null

  return (
    <>
      {p.alertas.length > 0 && (
        <div className="alerta" role="note">
          {p.alertas.map((a) => (
            <p key={a.cartao + a.tipo}>
              Fatura do {a.cartao} {a.tipo} {a.faltam === 0 ? 'hoje' : a.faltam === 1 ? 'amanhã' : `em ${a.faltam} dias`} ({a.data})
            </p>
          ))}
        </div>
      )}

      <section className="painel-saldo" aria-label={`Saldo de ${nomeMes(p.mes)}`}>
        <div className="saldo-principal">
          <span className="saldo-rotulo">Saldo de {nomeMes(p.mes)}</span>
          <strong className={`saldo-valor${r.saldo < 0 ? ' negativo' : ''}`}>{brl(r.saldo)}</strong>
          <span className="saldo-nota">Receitas, menos despesas e meu cartão</span>
        </div>
        <div className="saldo-fluxo">
          <div className="fluxo-linha">
            <span>Entrou</span>
            <strong>{brl(r.receitas)}</strong>
          </div>
          <div className="fluxo-barra" aria-hidden="true">
            <div className="fluxo-saiu" style={{ width: `${Math.min(100, usoReceita ?? (saiu > 0 ? 100 : 0))}%` }} />
          </div>
          <div className="fluxo-linha">
            <span>Saiu</span>
            <strong>{brl(saiu)}</strong>
          </div>
          {usoReceita !== null && <span className="saldo-nota">As despesas usaram {pct(usoReceita)} do que entrou.</span>}
        </div>
      </section>

      <FaixaNumeros>
        <Metrica rotulo="Meu cartão" valor={brl(r.meu_cartao_total)}
          detalhe={`Com empréstimos: ${brl(r.cartoes_com_emprestimos_total)}`} />
        <Metrica rotulo="Despesas" valor={brl(r.despesas_manuais)} detalhe="Lançadas à parte dos cartões" />
        <Metrica rotulo="A receber" valor={brl(r.a_receber_de_pessoas)} detalhe="O que as pessoas ainda devem"
          tom={r.a_receber_de_pessoas > 0 ? 'aviso' : 'normal'} />
        <Metrica rotulo="Renda do mês" valor={r.renda ? brl(r.renda) : '—'}
          detalhe={r.cartao_percentual_renda != null ? `O cartão consome ${pct(r.cartao_percentual_renda)}` : 'Defina em Ferramentas'}
          tom={r.cartao_percentual_renda != null && r.cartao_percentual_renda > 50 ? 'negativo' : 'normal'} />
      </FaixaNumeros>

      <div className="colunas">
        <ParaOndeFoi p={p} total={saiu} />
        <Orcamento p={p} />
      </div>
    </>
  )
}

function ParaOndeFoi({ p, total }: { p: Painel; total: number }) {
  const cor = (id: number | null) => p.categorias.find((c) => c.id === id)?.cor ?? SEM_CATEGORIA
  const nome = (id: number | null) => p.categorias.find((c) => c.id === id)?.nome ?? 'Sem categoria'
  const linhas = [...p.gasto].filter((g) => g.valor > 0).sort((a, b) => b.valor - a.valor)
  return (
    <Secao titulo="Para onde foi o dinheiro" descricao="Compras suas no cartão e despesas, por categoria">
      {linhas.length === 0 ? <Vazio>Nenhum gasto neste mês ainda.</Vazio> : (
        <>
          <div className="pilha" aria-hidden="true">
            {linhas.map((g) => (
              <span key={String(g.categoria_id)} style={{ flexGrow: g.valor, background: cor(g.categoria_id) }} />
            ))}
          </div>
          <ul className="lista-categorias">
            {linhas.map((g) => (
              <li key={String(g.categoria_id)}>
                <span className="ponto" style={{ background: cor(g.categoria_id) }} />
                <span className="lc-nome">{nome(g.categoria_id)}</span>
                <span className="lc-pct">{pct(total > 0 ? (g.valor / total) * 100 : 0)}</span>
                <span className="num">{brl(g.valor)}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </Secao>
  )
}

function Orcamento({ p }: { p: Painel }) {
  const comLimite = p.categorias.filter((c) => c.orcamento > 0)
  const gasto = (id: number) => p.gasto.find((g) => g.categoria_id === id)?.valor ?? 0
  return (
    <Secao titulo="Orçamento do mês" descricao="Limite de cada categoria e quanto já foi usado">
      {comLimite.length === 0 ? (
        <Vazio>Nenhuma categoria com limite. Defina em Ferramentas &gt; Categorias.</Vazio>
      ) : (
        <ul className="lista-orcamento">
          {comLimite.map((c) => {
            const usado = gasto(c.id)
            const passou = usado > c.orcamento
            return (
              <li key={c.id}>
                <div className="lo-topo">
                  <span>{c.nome}</span>
                  <span className={`num${passou ? ' tom-negativo' : ''}`}>{brl(usado)} de {brl(c.orcamento)}</span>
                </div>
                <Barra valor={usado} total={c.orcamento} cor={c.cor} excedida={passou} />
                {passou && <span className="excedido">Passou {brl(usado - c.orcamento)} do limite</span>}
              </li>
            )
          })}
        </ul>
      )}
    </Secao>
  )
}
