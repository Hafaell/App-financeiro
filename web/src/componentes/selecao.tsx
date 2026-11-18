import { useEffect, useState } from 'react'
import { post } from '../lib/api'
import { recolocar, useEstado } from '../lib/estado'
import { brl } from '../lib/formato'
import { useConfirmar } from './ui'

type TabelaLote = 'compras' | 'receitas' | 'despesas'
export interface ItemLote { id: number; valor: number }

/** Modo "Selecionar": marca linhas para apagar em lote. Zera quando `chaveReset` muda (mês, cartão...). */
export function useSelecao(chaveReset: unknown) {
  const [ativo, setAtivo] = useState(false)
  const [ids, setIds] = useState<Set<number>>(new Set())

  useEffect(() => {
    setAtivo(false)
    setIds(new Set())
  }, [chaveReset])

  return {
    ativo,
    ids,
    alternarModo: () => {
      setAtivo((a) => !a)
      setIds(new Set())
    },
    alternar: (id: number) => setIds((atual) => {
      const novo = new Set(atual)
      if (!novo.delete(id)) novo.add(id)
      return novo
    }),
    marcarTodas: (todos: number[]) => setIds(new Set(todos)),
    limpar: () => {
      setAtivo(false)
      setIds(new Set())
    },
  }
}

export type Selecao = ReturnType<typeof useSelecao>

/** Caixinha de marcar de uma linha; só aparece no modo seleção. */
export function CaixaLinha({ selecao, id }: { selecao: Selecao; id: number }) {
  if (!selecao.ativo) return null
  return (
    <label className="caixa-linha">
      <input type="checkbox" checked={selecao.ids.has(id)} onChange={() => selecao.alternar(id)}
        aria-label="Selecionar linha" />
    </label>
  )
}

/**
 * Botões de apagar em lote de uma lista.
 * `visiveis`: o que está na tela (base do "Apagar selecionadas" e do "Marcar todas").
 * `todas`: o que o "Apagar tudo" apaga (a lista do mês, sem a busca por texto).
 */
export function BarraLote({ tabela, itens, selecao, visiveis, todas }: {
  tabela: TabelaLote
  itens: [string, string] // [singular, plural], ex.: ['compra', 'compras']
  selecao: Selecao
  visiveis: ItemLote[]
  todas: ItemLote[]
}) {
  const { atualizar, avisar } = useEstado()
  const [perguntar, janela] = useConfirmar()

  const marcadas = visiveis.filter((l) => selecao.ids.has(l.id))
  const todasMarcadas = visiveis.length > 0 && marcadas.length === visiveis.length

  const apagar = (alvo: ItemLote[]) => {
    const n = alvo.length
    const nome = itens[n === 1 ? 0 : 1]
    const total = alvo.reduce((s, l) => s + l.valor, 0)
    perguntar(`Apagar ${n} ${nome} (${brl(total)})? Dá para desfazer logo depois.`, async () => {
      const { apagadas } = await post<{ apagadas: unknown[] }>('/api/apagar-varios', {
        tabela, ids: alvo.map((l) => l.id),
      })
      selecao.limpar()
      await atualizar()
      avisar(`Apagou ${apagadas.length} ${itens[apagadas.length === 1 ? 0 : 1]}.`, async () => {
        await Promise.all(apagadas.map((l) => recolocar(tabela, l)))
      })
    }, n === 1 ? 'Apagar' : `Apagar ${n}`)
  }

  return (
    <div className="barra-lote">
      {selecao.ativo ? (
        <>
          <span className="barra-lote-info" aria-live="polite">
            {marcadas.length} selecionada{marcadas.length === 1 ? '' : 's'}
            {marcadas.length > 0 && ` · ${brl(marcadas.reduce((s, l) => s + l.valor, 0))}`}
          </span>
          <button className="botao" disabled={visiveis.length === 0}
            onClick={() => (todasMarcadas ? selecao.marcarTodas([]) : selecao.marcarTodas(visiveis.map((l) => l.id)))}>
            {todasMarcadas ? 'Desmarcar todas' : 'Marcar todas'}
          </button>
          <button className="botao perigo" disabled={marcadas.length === 0} onClick={() => apagar(marcadas)}>
            Apagar selecionadas
          </button>
          <button className="botao" onClick={selecao.alternarModo}>Cancelar</button>
        </>
      ) : (
        <>
          <button className="botao" disabled={visiveis.length === 0} onClick={selecao.alternarModo}>Selecionar</button>
          <button className="botao perigo-texto" disabled={todas.length === 0} onClick={() => apagar(todas)}>
            Apagar tudo{todas.length > 0 ? ` (${todas.length})` : ''}
          </button>
        </>
      )}
      {janela}
    </div>
  )
}
