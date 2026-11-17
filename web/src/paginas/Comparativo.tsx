import { useState } from 'react'
import { Carregando, ErroCarga, Pagina, Secao, Vazio } from '../componentes/ui'
import { get, q } from '../lib/api'
import { useDados } from '../lib/estado'
import { brl } from '../lib/formato'

interface Linha {
  mes: string
  nome: string
  receitas: number
  despesas: number
  saldo: number
  meu_cartao: number
  a_receber: number
}

/** Receitas e despesas (despesas + meu cartão) dos últimos meses abertos. */
export function Comparativo() {
  const [quantos, setQuantos] = useState(6)
  const { dados, erro, tentarDeNovo } = useDados(() => get<Linha[]>(`/api/comparativo${q({ quantos })}`), [quantos])
  const maior = Math.max(1, ...(dados ?? []).flatMap((l) => [l.receitas, l.despesas]))

  return (
    <Pagina titulo="Comparativo" descricao="Receitas e despesas dos últimos meses (despesas incluem o seu cartão)."
      acoes={
        <select aria-label="Quantos meses" value={quantos} onChange={(e) => setQuantos(Number(e.target.value))}>
          {[3, 6, 12, 24].map((n) => <option key={n} value={n}>Últimos {n} meses</option>)}
        </select>
      }>
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> :
        dados.length === 0 ? <Vazio>Ainda não há meses para comparar.</Vazio> : (
          <>
            <Secao titulo="Entrou e saiu por mês">
              <div className="legenda">
                <span><span className="ponto cor-receita" />Receitas</span>
                <span><span className="ponto cor-despesa" />Despesas</span>
              </div>
              <ul className="barras-meses">
                {dados.map((l) => (
                  <li key={l.mes}>
                    <span className="bm-nome">{l.nome}</span>
                    <div className="bm-barras" aria-hidden="true">
                      <span className="cor-receita" style={{ width: `${(l.receitas / maior) * 100}%` }} />
                      <span className="cor-despesa" style={{ width: `${(l.despesas / maior) * 100}%` }} />
                    </div>
                    <span className={`num bm-saldo${l.saldo < 0 ? ' tom-negativo' : ''}`}>{brl(l.saldo)}</span>
                  </li>
                ))}
              </ul>
            </Secao>
            <Secao titulo="Números de cada mês">
              <div className="tabela-rolagem">
                <table className="tabela">
                  <thead>
                    <tr>
                      <th>Mês</th><th className="direita">Receitas</th><th className="direita">Despesas</th>
                      <th className="direita">Meu cartão</th><th className="direita">A receber</th>
                      <th className="direita">Saldo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {dados.map((l) => (
                      <tr key={l.mes}>
                        <td>{l.nome}</td>
                        <td className="direita num">{brl(l.receitas)}</td>
                        <td className="direita num">{brl(l.despesas)}</td>
                        <td className="direita num">{brl(l.meu_cartao)}</td>
                        <td className="direita num">{brl(l.a_receber)}</td>
                        <td className={`direita num forte${l.saldo < 0 ? ' tom-negativo' : ''}`}>{brl(l.saldo)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </Secao>
          </>
        )}
    </Pagina>
  )
}
