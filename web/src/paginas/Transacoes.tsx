import { useMemo, useState } from 'react'
import { FormCompra } from '../componentes/formularios'
import { Carregando, ErroCarga, FaixaNumeros, Metrica, Pagina, SeloCartao, Valor, Vazio } from '../componentes/ui'
import { get, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, data } from '../lib/formato'
import type { Compra } from '../lib/tipos'

/** Compras de todos os cartões no mês, com filtro por cartão e busca. */
export function Transacoes() {
  const { mes, inicio, nomeCategoria } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() => get<Compra[]>(`/api/compras${q({ mes })}`))
  const [cartao, setCartao] = useState('')
  const [busca, setBusca] = useState('')
  const [editar, setEditar] = useState<Compra | null>(null)
  const [nova, setNova] = useState(false)

  const filtradas = useMemo(() => {
    const t = busca.trim().toLowerCase()
    return (dados ?? []).filter((c) => (!cartao || c.cartao === cartao)
      && (!t || c.item.toLowerCase().includes(t) || c.pessoa.toLowerCase().includes(t)))
  }, [dados, cartao, busca])

  const meu = filtradas.filter((c) => !c.emprestimo).reduce((s, c) => s + c.valor_parcela, 0)
  const total = filtradas.reduce((s, c) => s + c.valor_parcela, 0)

  return (
    <Pagina titulo="Transações" descricao="Compras nos cartões neste mês. Toque numa compra para editar ou apagar."
      acoes={<button className="botao primario" onClick={() => setNova(true)}>Nova compra</button>}>
      <div className="filtros">
        <div className="chips" role="group" aria-label="Cartão">
          <button className={`chip${cartao === '' ? ' ativo' : ''}`} onClick={() => setCartao('')}>Todos</button>
          {inicio.cartoes.map((c) => (
            <button key={c.id} className={`chip${cartao === c.nome ? ' ativo' : ''}`} onClick={() => setCartao(c.nome)}>
              <span className="ponto" style={{ background: c.cor }} />{c.nome}
            </button>
          ))}
        </div>
        <input type="search" className="busca" placeholder="Buscar item ou pessoa" value={busca}
          onChange={(e) => setBusca(e.target.value)} aria-label="Buscar item ou pessoa" />
      </div>

      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> : (
        <>
          <FaixaNumeros>
            <Metrica rotulo="Meu cartão" valor={brl(meu)} detalhe="Compras suas, sem empréstimos" />
            <Metrica rotulo="Com empréstimos" valor={brl(total)} detalhe={`${filtradas.length} compras`} />
            <Metrica rotulo="Empréstimos" valor={brl(total - meu)} detalhe="Compras de outras pessoas" />
          </FaixaNumeros>
          {filtradas.length === 0 ? (
            <Vazio>{dados.length === 0 ? 'Nada lançado neste mês ainda. Use "Nova compra".' : 'Nenhuma compra com esse filtro.'}</Vazio>
          ) : (
            <ul className="linhas">
              {filtradas.map((c) => (
                <li key={c.id}>
                  <button className="linha" onClick={() => setEditar(c)}>
                    <span className="linha-principal">
                      <span className="linha-titulo">{c.item}</span>
                      <span className="linha-meta">
                        <SeloCartao nome={c.cartao} cartoes={inicio.cartoes} />
                        {c.parcelas !== '1/1' && <span className="etiqueta">{c.parcelas}</span>}
                        {c.recorrente ? <span className="etiqueta">Recorrente</span> : null}
                        {c.emprestimo ? <span className="etiqueta etiqueta-pessoa">{c.pessoa}</span> : null}
                        <span>{nomeCategoria(c.categoria_id)}</span>
                        <span className="so-pc">Lançado em {data(c.data_lancamento)}</span>
                      </span>
                    </span>
                    <Valor v={c.valor_parcela} />
                  </button>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <FormCompra key={`nova-${nova}`} aberto={nova} fechar={() => setNova(false)} />
      <FormCompra key={editar?.id ?? 'nenhuma'} aberto={editar !== null} fechar={() => setEditar(null)}
        compra={editar ?? undefined} />
    </Pagina>
  )
}
