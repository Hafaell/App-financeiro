import { useState } from 'react'
import { del, patch, post } from '../lib/api'
import { recolocar, useEstado } from '../lib/estado'
import { nomeMes, valorCampo } from '../lib/formato'
import type { Compra, Lancamento, Tabela } from '../lib/tipos'
import { Campo, Formulario, Modal } from './ui'

function SeletorCategoria({ id, valor, mudar }: { id: string; valor: string; mudar: (v: string) => void }) {
  const { inicio } = useEstado()
  return (
    <select id={id} value={valor} onChange={(e) => mudar(e.target.value)}>
      <option value="">Sem categoria</option>
      {inicio.categorias.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
    </select>
  )
}

/** Nova compra (compra = undefined) ou edição de uma existente. */
export function FormCompra({ aberto, fechar, compra }: { aberto: boolean; fechar: () => void; compra?: Compra }) {
  return (
    <Modal titulo={compra ? 'Editar compra' : 'Nova compra no cartão'} aberto={aberto} fechar={fechar}>
      <CamposCompra compra={compra} fechar={fechar} />
    </Modal>
  )
}

function CamposCompra({ compra, fechar }: { compra?: Compra; fechar: () => void }) {
  const { inicio, mes, atualizar, avisar } = useEstado()
  const [cartao, setCartao] = useState(compra?.cartao ?? inicio.cartoes[0]?.nome ?? '')
  const [item, setItem] = useState(compra?.item ?? '')
  const [valor, setValor] = useState(valorCampo(compra?.valor_parcela))
  const [parcelas, setParcelas] = useState(compra && compra.parcelas !== '1/1' ? compra.parcelas : '')
  const [pessoa, setPessoa] = useState(compra && compra.pessoa !== '.' ? compra.pessoa : '')
  const [categoria, setCategoria] = useState(compra?.categoria_id ? String(compra.categoria_id) : '')
  const [recorrente, setRecorrente] = useState(Boolean(compra?.recorrente))

  const enviar = async () => {
    const dados = {
      cartao, item, valor_parcela: valor, parcelas: parcelas.trim() || '1/1', pessoa: pessoa.trim() || '.',
      recorrente, categoria_id: categoria ? Number(categoria) : null,
    }
    if (compra) {
      await patch(`/api/compras/${compra.id}`, dados)
      avisar('Compra salva.')
    } else {
      await post('/api/compras', { ...dados, mes })
      avisar(`Compra lançada em ${nomeMes(mes)}.`)
    }
    await atualizar()
    fechar()
  }

  const apagar = async () => {
    if (!compra) return
    const { apagada } = await del<{ apagada: Compra }>(`/api/compras/${compra.id}`)
    await atualizar()
    fechar()
    avisar(`Compra apagada: ${compra.item}.`, () => recolocar('compras', apagada))
  }

  return (
    <Formulario enviar={enviar} extra={compra && <BotaoApagar apagar={apagar} />}>
      <Campo rotulo="Cartão">{(id) => (
        <select id={id} value={cartao} onChange={(e) => setCartao(e.target.value)}>
          {inicio.cartoes.map((c) => <option key={c.id}>{c.nome}</option>)}
        </select>
      )}</Campo>
      <Campo rotulo="Descrição">{(id) => (
        <input id={id} value={item} onChange={(e) => setItem(e.target.value)} maxLength={80} required
          placeholder="Ex.: Mercado" autoFocus={!compra} />
      )}</Campo>
      <div className="duas-colunas">
        <Campo rotulo="Valor da parcela">{(id) => (
          <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required
            placeholder="R$ 0,00" />
        )}</Campo>
        <Campo rotulo="Parcelas" dica="Vazio = à vista">{(id) => (
          <input id={id} value={parcelas} onChange={(e) => setParcelas(e.target.value)} placeholder="Ex.: 1/3"
            inputMode="numeric" pattern="\d+/\d+" />
        )}</Campo>
      </div>
      <Campo rotulo="Pessoa" dica="Preencha se a compra é de outra pessoa (empréstimo). Vazio = sua.">{(id) => (
        <>
          <input id={id} value={pessoa} onChange={(e) => setPessoa(e.target.value)} list={`${id}-pessoas`}
            placeholder="Opcional" />
          <datalist id={`${id}-pessoas`}>{inicio.pessoas.map((p) => <option key={p} value={p} />)}</datalist>
        </>
      )}</Campo>
      <Campo rotulo="Categoria">{(id) => <SeletorCategoria id={id} valor={categoria} mudar={setCategoria} />}</Campo>
      <label className="marcar">
        <input type="checkbox" checked={recorrente} onChange={(e) => setRecorrente(e.target.checked)} />
        Recorrente: continua no próximo mês sem avançar parcela
      </label>
    </Formulario>
  )
}

export function FormLancamento({ aberto, fechar, tabela, lancamento }: {
  aberto: boolean
  fechar: () => void
  tabela: Tabela
  lancamento?: Lancamento
}) {
  const singular = tabela === 'receitas' ? 'receita' : 'despesa'
  return (
    <Modal titulo={lancamento ? `Editar ${singular}` : `Nova ${singular}`} aberto={aberto} fechar={fechar}>
      <CamposLancamento tabela={tabela} lancamento={lancamento} fechar={fechar} />
    </Modal>
  )
}

function CamposLancamento({ tabela, lancamento, fechar }: { tabela: Tabela; lancamento?: Lancamento; fechar: () => void }) {
  const { mes, atualizar, avisar } = useEstado()
  const [descricao, setDescricao] = useState(lancamento?.descricao ?? '')
  const [valor, setValor] = useState(valorCampo(lancamento?.valor))
  const [categoria, setCategoria] = useState(lancamento?.categoria_id ? String(lancamento.categoria_id) : '')
  const [recorrente, setRecorrente] = useState(Boolean(lancamento?.recorrente))
  const despesa = tabela === 'despesas'
  const singular = despesa ? 'Despesa' : 'Receita'

  const enviar = async () => {
    const dados = despesa
      ? { descricao, valor, recorrente, categoria_id: categoria ? Number(categoria) : null }
      : { descricao, valor }
    if (lancamento) await patch(`/api/lancamentos/${tabela}/${lancamento.id}`, dados)
    else await post(`/api/lancamentos/${tabela}`, { ...dados, mes })
    await atualizar()
    fechar()
    avisar(lancamento ? `${singular} salva.` : `${singular} lançada em ${nomeMes(mes)}.`)
  }

  const apagar = async () => {
    if (!lancamento) return
    const { apagada } = await del<{ apagada: Lancamento }>(`/api/lancamentos/${tabela}/${lancamento.id}`)
    await atualizar()
    fechar()
    avisar(`${singular} apagada: ${lancamento.descricao}.`, () => recolocar(tabela, apagada))
  }

  return (
    <Formulario enviar={enviar} extra={lancamento && <BotaoApagar apagar={apagar} />}>
      <Campo rotulo="Descrição" dica={despesa ? 'Com parcela no nome, como "Dentista (2/5)", ela avança na virada.' : undefined}>
        {(id) => (
          <input id={id} value={descricao} onChange={(e) => setDescricao(e.target.value)} required
            placeholder={despesa ? 'Ex.: Aluguel' : 'Ex.: Salário'} autoFocus={!lancamento} />
        )}
      </Campo>
      <Campo rotulo="Valor">{(id) => (
        <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required
          placeholder="R$ 0,00" />
      )}</Campo>
      {despesa && (
        <>
          <Campo rotulo="Categoria">{(id) => <SeletorCategoria id={id} valor={categoria} mudar={setCategoria} />}</Campo>
          <label className="marcar">
            <input type="checkbox" checked={recorrente} onChange={(e) => setRecorrente(e.target.checked)} />
            Recorrente: permanece no próximo mês
          </label>
        </>
      )}
    </Formulario>
  )
}

function BotaoApagar({ apagar }: { apagar: () => Promise<void> }) {
  const { falhar } = useEstado()
  const [ocupado, setOcupado] = useState(false)
  return (
    <button type="button" className="botao perigo-texto" disabled={ocupado}
      onClick={async () => {
        setOcupado(true)
        try {
          await apagar()
        } catch (e) {
          falhar(e)
        } finally {
          setOcupado(false)
        }
      }}>
      Apagar
    </button>
  )
}

/** Escolha rápida do botão "Lançar" (celular): compra, despesa ou receita. */
export function Lancar({ aberto, fechar }: { aberto: boolean; fechar: () => void }) {
  const [tipo, setTipo] = useState<'compra' | Tabela | null>(null)
  const sair = () => {
    setTipo(null)
    fechar()
  }
  return (
    <>
      <Modal titulo="O que você quer lançar?" aberto={aberto && tipo === null} fechar={sair}>
        <div className="escolha-lancar">
          <button className="botao primario" onClick={() => setTipo('compra')}>Compra no cartão</button>
          <button className="botao" onClick={() => setTipo('despesas')}>Despesa</button>
          <button className="botao" onClick={() => setTipo('receitas')}>Receita</button>
        </div>
      </Modal>
      <FormCompra aberto={tipo === 'compra'} fechar={sair} />
      <FormLancamento aberto={tipo === 'despesas'} fechar={sair} tabela="despesas" />
      <FormLancamento aberto={tipo === 'receitas'} fechar={sair} tabela="receitas" />
    </>
  )
}
