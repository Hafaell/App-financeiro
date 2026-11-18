import { useState } from 'react'
import { FormLancamento } from '../componentes/formularios'
import { BarraLote, CaixaLinha, useSelecao } from '../componentes/selecao'
import { Abas, Carregando, ErroCarga, FaixaNumeros, Metrica, Pagina, Secao, Valor, Vazio } from '../componentes/ui'
import { get, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, data } from '../lib/formato'
import type { Lancamento, Tabela } from '../lib/tipos'

export function ReceitasDespesas() {
  const { mes } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(async () => {
    const [receitas, despesas] = await Promise.all([
      get<Lancamento[]>(`/api/lancamentos/receitas${q({ mes })}`),
      get<Lancamento[]>(`/api/lancamentos/despesas${q({ mes })}`),
    ])
    return { receitas, despesas }
  })
  const [aba, setAba] = useState<Tabela>('despesas')
  const [form, setForm] = useState<{ tabela: Tabela; item?: Lancamento } | null>(null)

  const soma = (l: Lancamento[]) => l.reduce((s, x) => s + x.valor, 0)

  return (
    <Pagina titulo="Receitas e despesas" descricao="Lançamentos à parte dos cartões. Receitas são copiadas na virada.">
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> : (
        <>
          <FaixaNumeros>
            <Metrica rotulo="Receitas" valor={brl(soma(dados.receitas))} tom="positivo" />
            <Metrica rotulo="Despesas" valor={brl(soma(dados.despesas))} />
            <Metrica rotulo="Diferença" valor={brl(soma(dados.receitas) - soma(dados.despesas))}
              detalhe="Sem contar o cartão" />
          </FaixaNumeros>
          <div className="so-celular">
            <Abas opcoes={[{ valor: 'despesas', rotulo: 'Despesas' }, { valor: 'receitas', rotulo: 'Receitas' }]}
              valor={aba} mudar={setAba} />
          </div>
          <div className="colunas">
            {(['despesas', 'receitas'] as Tabela[]).map((t) => (
              <div key={t} className={aba === t ? '' : 'so-pc'}>
                <Lista tabela={t} itens={dados[t]} abrir={(item) => setForm({ tabela: t, item })} />
              </div>
            ))}
          </div>
        </>
      )}
      <FormLancamento key={form ? `${form.tabela}-${form.item?.id ?? 'novo'}` : 'nada'} aberto={form !== null}
        fechar={() => setForm(null)} tabela={form?.tabela ?? 'despesas'} lancamento={form?.item} />
    </Pagina>
  )
}

function Lista({ tabela, itens, abrir }: { tabela: Tabela; itens: Lancamento[]; abrir: (l?: Lancamento) => void }) {
  const { mes, nomeCategoria } = useEstado()
  const despesa = tabela === 'despesas'
  const selecao = useSelecao(`${mes}|${tabela}`)
  const lote = itens.map((l) => ({ id: l.id, valor: l.valor }))
  return (
    <Secao titulo={despesa ? 'Despesas' : 'Receitas'}
      acoes={<button className="botao" onClick={() => abrir()}>{despesa ? 'Nova despesa' : 'Nova receita'}</button>}>
      <BarraLote tabela={tabela} itens={despesa ? ['despesa', 'despesas'] : ['receita', 'receitas']}
        selecao={selecao} visiveis={lote} todas={lote} />
      {itens.length === 0 ? <Vazio>{despesa ? 'Nenhuma despesa neste mês.' : 'Nenhuma receita neste mês.'}</Vazio> : (
        <ul className="linhas">
          {itens.map((l) => (
            <li key={l.id} className={selecao.ativo ? `com-caixa${selecao.ids.has(l.id) ? ' marcada' : ''}` : undefined}>
              <CaixaLinha selecao={selecao} id={l.id} />
              <button className="linha" onClick={() => (selecao.ativo ? selecao.alternar(l.id) : abrir(l))}>
                <span className="linha-principal">
                  <span className="linha-titulo">{l.descricao}</span>
                  <span className="linha-meta">
                    {despesa && <span>{nomeCategoria(l.categoria_id)}</span>}
                    {l.recorrente ? <span className="etiqueta">Recorrente</span> : null}
                    <span>Lançado em {data(l.data_lancamento)}</span>
                  </span>
                </span>
                <Valor v={l.valor} tom={despesa ? undefined : 'positivo'} />
              </button>
            </li>
          ))}
        </ul>
      )}
    </Secao>
  )
}
