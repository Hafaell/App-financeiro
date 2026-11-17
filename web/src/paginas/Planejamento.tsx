import { Carregando, ErroCarga, FaixaNumeros, Metrica, Pagina, Secao, Vazio } from '../componentes/ui'
import { get, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, nomeMes } from '../lib/formato'
import type { Previsao } from '../lib/tipos'

interface Plano {
  mes: string
  previsao: Previsao
  parcelas_futuras: { mes: string; nome: string; por_cartao: Record<string, number>; total: number }[]
  assinaturas: { itens: { item: string; origem: string; valor_mes: number }[]; total_mes: number; total_ano: number }
}

export function Planejamento() {
  const { mes, inicio } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() => get<Plano>(`/api/planejamento${q({ mes })}`))

  return (
    <Pagina titulo="Planejamento" descricao="O que vem pela frente: próximo mês, parcelas e assinaturas.">
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> : (
        <>
          <Secao titulo={`Se o mês virar agora, ${dados.previsao.nome} começa assim`}
            descricao={dados.previsao.ja_aberto ? `${dados.previsao.nome} já está aberto; esta é só a simulação.`
              : 'Recorrentes e parceladas que continuam, receitas copiadas. Nada é gravado.'}>
            <FaixaNumeros>
              <Metrica rotulo="Receitas" valor={brl(dados.previsao.receitas)} detalhe="Copiadas na virada" />
              <Metrica rotulo="Despesas" valor={brl(dados.previsao.despesas)} detalhe="Recorrentes e parceladas" />
              <Metrica rotulo="Meu cartão" valor={brl(dados.previsao.meu_cartao)}
                detalhe={`Empréstimos: ${brl(dados.previsao.emprestimos)}`} />
              <Metrica rotulo="Saldo previsto" valor={brl(dados.previsao.saldo)}
                tom={dados.previsao.saldo < 0 ? 'negativo' : 'positivo'} />
            </FaixaNumeros>
          </Secao>

          <Secao titulo="Parcelas dos próximos meses" descricao="Compras suas parceladas que ainda vão cair, por cartão">
            {dados.parcelas_futuras.every((p) => p.total === 0) ? <Vazio>Nenhuma parcela futura.</Vazio> : (
              <div className="tabela-rolagem">
                <table className="tabela">
                  <thead>
                    <tr>
                      <th>Mês</th>
                      {inicio.cartoes.map((c) => <th key={c.id} className="direita">{c.nome}</th>)}
                      <th className="direita">Total</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.parcelas_futuras.map((p) => (
                      <tr key={p.mes}>
                        <td>{p.nome}</td>
                        {inicio.cartoes.map((c) => <td key={c.id} className="direita num">{brl(p.por_cartao[c.nome] ?? 0)}</td>)}
                        <td className="direita num forte">{brl(p.total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </Secao>

          <Secao titulo="Assinaturas e itens recorrentes" descricao={`Itens recorrentes de ${nomeMes(dados.mes)}`}>
            {dados.assinaturas.itens.length === 0 ? <Vazio>Nenhum item recorrente neste mês.</Vazio> : (
              <>
                <ul className="linhas linhas-simples">
                  {dados.assinaturas.itens.map((a, i) => (
                    <li key={i} className="linha">
                      <span className="linha-principal">
                        <span className="linha-titulo">{a.item}</span>
                        <span className="linha-meta">{a.origem}</span>
                      </span>
                      <span className="num">{brl(a.valor_mes)}</span>
                    </li>
                  ))}
                </ul>
                <p className="totais">
                  <span>Por mês <strong className="num">{brl(dados.assinaturas.total_mes)}</strong></span>
                  <span>Por ano <strong className="num">{brl(dados.assinaturas.total_ano)}</strong></span>
                </p>
              </>
            )}
          </Secao>
        </>
      )}
    </Pagina>
  )
}
