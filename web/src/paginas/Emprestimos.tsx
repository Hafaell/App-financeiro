import { useState } from 'react'
import { FormCompra } from '../componentes/formularios'
import {
  Abas, Campo, Carregando, ErroCarga, FaixaNumeros, Formulario, Metrica, Modal, Pagina, Secao, SeloCartao, Valor, Vazio,
} from '../componentes/ui'
import { get, post, put, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, nomeMes } from '../lib/formato'
import type { Compra, Divida, Pagamento } from '../lib/tipos'

/** Quem te deve no mês, os empréstimos de cada pessoa e os pagamentos recebidos. */
export function Emprestimos() {
  const { mes } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() => get<Divida[]>(`/api/emprestimos${q({ mes })}`))
  const [pessoa, setPessoa] = useState<string | null>(null)
  const [pagar, setPagar] = useState<string | null>(null)

  const soma = (k: keyof Omit<Divida, 'pessoa'>) => (dados ?? []).reduce((s, d) => s + d[k], 0)

  return (
    <Pagina titulo="Empréstimos" descricao="Compras no seu cartão feitas para outras pessoas."
      acoes={<button className="botao primario" onClick={() => setPagar('')}>Registrar pagamento</button>}>
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> : (
        <>
          <FaixaNumeros>
            <Metrica rotulo="Emprestado no mês" valor={brl(soma('emprestado'))} />
            <Metrica rotulo="Já pago" valor={brl(soma('ja_pago'))} tom="positivo"
              detalhe="O que as pessoas devolveram neste mês" />
            <Metrica rotulo="Em aberto" valor={brl(soma('em_aberto'))} tom={soma('em_aberto') > 0 ? 'aviso' : 'normal'}
              detalhe="O que ainda falta receber" />
          </FaixaNumeros>
          <Secao titulo="Quem te deve" descricao={`Em ${nomeMes(mes)}. Toque numa pessoa para ver os detalhes.`}>
            {dados.length === 0 ? <Vazio>Nenhum empréstimo neste mês.</Vazio> : (
              <ul className="linhas">
                {dados.map((d) => (
                  <li key={d.pessoa}>
                    <button className="linha" onClick={() => setPessoa(d.pessoa)}>
                      <span className="linha-principal">
                        <span className="linha-titulo">{d.pessoa}</span>
                        <span className="linha-meta">
                          <span>Emprestado {brl(d.emprestado)}</span>
                          <span>Pago {brl(d.ja_pago)}</span>
                        </span>
                      </span>
                      <Valor v={d.em_aberto} tom={d.em_aberto > 0 ? 'aviso' : 'positivo'} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </Secao>
        </>
      )}
      <Detalhe pessoa={pessoa} fechar={() => setPessoa(null)} pagar={(p) => {
        setPessoa(null)
        setPagar(p)
      }} />
      <Modal titulo="Registrar pagamento" aberto={pagar !== null} fechar={() => setPagar(null)}>
        <FormPagamento pessoaInicial={pagar ?? ''} fechar={() => setPagar(null)} />
      </Modal>
    </Pagina>
  )
}

function Detalhe({ pessoa, fechar, pagar }: { pessoa: string | null; fechar: () => void; pagar: (p: string) => void }) {
  return (
    <Modal titulo={pessoa ? `Empréstimos de ${pessoa}` : ''} aberto={pessoa !== null} fechar={fechar} largo>
      {pessoa && <ConteudoDetalhe pessoa={pessoa} pagar={pagar} />}
    </Modal>
  )
}

function ConteudoDetalhe({ pessoa, pagar }: { pessoa: string; pagar: (p: string) => void }) {
  const { mes, inicio } = useEstado()
  const [todos, setTodos] = useState<'mes' | 'todos'>('mes')
  const [editar, setEditar] = useState<Compra | null>(null)
  const [editarPagamento, setEditarPagamento] = useState<Pagamento | null>(null)
  const { dados, erro, tentarDeNovo } = useDados(
    () => get<Compra[]>(`/api/emprestimos/${encodeURIComponent(pessoa)}${q({ mes: todos === 'mes' ? mes : '' })}`),
    [pessoa, todos],
  )
  const pagamentos = useDados(
    () => get<Pagamento[]>(`/api/pagamentos/${encodeURIComponent(pessoa)}${q({ mes: todos === 'mes' ? mes : '' })}`),
    [pessoa, todos],
  )
  return (
    <>
      <Abas opcoes={[{ valor: 'mes', rotulo: nomeMes(mes) }, { valor: 'todos', rotulo: 'Todos os meses' }]}
        valor={todos} mudar={setTodos} />
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> :
        dados.length === 0 ? <Vazio>Nenhum empréstimo.</Vazio> : (
          <>
            <ul className="linhas">
              {dados.map((c) => (
                <li key={c.id}>
                  <button className="linha" onClick={() => setEditar(c)}>
                    <span className="linha-principal">
                      <span className="linha-titulo">{c.item}</span>
                      <span className="linha-meta">
                        <SeloCartao nome={c.cartao} cartoes={inicio.cartoes} />
                        {c.parcelas !== '1/1' && <span className="etiqueta">{c.parcelas}</span>}
                        {todos === 'todos' && <span>{nomeMes(c.mes)}</span>}
                      </span>
                    </span>
                    <Valor v={c.valor_parcela} />
                  </button>
                </li>
              ))}
            </ul>
            <p className="totais"><span>Total <strong className="num">{brl(dados.reduce((s, c) => s + c.valor_parcela, 0))}</strong></span></p>
          </>
        )}
      {pagamentos.dados && pagamentos.dados.length > 0 && (
        <>
          <h3>Pagamentos recebidos</h3>
          <ul className="linhas">
            {pagamentos.dados.map((p) => (
              <li key={p.id}>
                <button className="linha" onClick={() => setEditarPagamento(p)}>
                  <span className="linha-principal">
                    <span className="linha-titulo">{p.descricao || 'Pagamento'}</span>
                    <span className="linha-meta">
                      <span>{new Date(`${p.data}T12:00:00`).toLocaleDateString('pt-BR')}</span>
                      {todos === 'todos' && p.mes && <span>{nomeMes(p.mes)}</span>}
                    </span>
                  </span>
                  <Valor v={p.valor} tom="positivo" />
                </button>
              </li>
            ))}
          </ul>
        </>
      )}
      <div className="form-acoes">
        <button className="botao primario" onClick={() => pagar(pessoa)}>Registrar pagamento de {pessoa}</button>
      </div>
      <FormCompra key={editar?.id ?? 'nenhuma'} aberto={editar !== null} fechar={() => setEditar(null)}
        compra={editar ?? undefined} />
      <Modal titulo="Editar pagamento" aberto={editarPagamento !== null} fechar={() => setEditarPagamento(null)}>
        {editarPagamento && (
          <FormEditarPagamento pagamento={editarPagamento} fechar={() => setEditarPagamento(null)}
            recarregar={pagamentos.tentarDeNovo} />
        )}
      </Modal>
    </>
  )
}

function FormEditarPagamento({ pagamento, fechar, recarregar }: {
  pagamento: Pagamento; fechar: () => void; recarregar: () => void
}) {
  const { inicio, atualizar, avisar } = useEstado()
  const [pessoa, setPessoa] = useState(pagamento.pessoa)
  const [valor, setValor] = useState(String(pagamento.valor).replace('.', ','))
  const [descricao, setDescricao] = useState(pagamento.descricao)
  return (
    <Formulario rotulo="Salvar" enviar={async () => {
      await put(`/api/pagamentos/${pagamento.id}`, { pessoa, valor, descricao })
      await atualizar()
      recarregar()
      fechar()
      avisar('Pagamento corrigido.')
    }}>
      <Campo rotulo="Pessoa">{(id) => (
        <>
          <input id={id} value={pessoa} onChange={(e) => setPessoa(e.target.value)} list={`${id}-l`} required />
          <datalist id={`${id}-l`}>{inicio.pessoas.map((p) => <option key={p} value={p} />)}</datalist>
        </>
      )}</Campo>
      <Campo rotulo="Valor devolvido">{(id) => (
        <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required
          autoFocus />
      )}</Campo>
      <Campo rotulo="Observação">{(id) => (
        <input id={id} value={descricao} onChange={(e) => setDescricao(e.target.value)} placeholder="Opcional" />
      )}</Campo>
    </Formulario>
  )
}

function FormPagamento({ pessoaInicial, fechar }: { pessoaInicial: string; fechar: () => void }) {
  const { inicio, mes, atualizar, avisar } = useEstado()
  const [pessoa, setPessoa] = useState(pessoaInicial)
  const [valor, setValor] = useState('')
  const [descricao, setDescricao] = useState('')
  return (
    <Formulario rotulo="Registrar pagamento" enviar={async () => {
      await post('/api/pagamentos', { pessoa, valor, descricao, mes })
      await atualizar()
      fechar()
      avisar(`Pagamento de ${pessoa} registrado em ${nomeMes(mes)}.`)
    }}>
      <Campo rotulo="Pessoa">{(id) => (
        <>
          <input id={id} value={pessoa} onChange={(e) => setPessoa(e.target.value)} list={`${id}-l`} required />
          <datalist id={`${id}-l`}>{inicio.pessoas.map((p) => <option key={p} value={p} />)}</datalist>
        </>
      )}</Campo>
      <Campo rotulo="Valor devolvido">{(id) => (
        <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required
          placeholder="R$ 0,00" autoFocus />
      )}</Campo>
      <Campo rotulo="Observação">{(id) => (
        <input id={id} value={descricao} onChange={(e) => setDescricao(e.target.value)} placeholder="Opcional" />
      )}</Campo>
    </Formulario>
  )
}
