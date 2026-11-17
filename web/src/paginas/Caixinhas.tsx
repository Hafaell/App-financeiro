import { useState } from 'react'
import {
  Barra, Campo, Carregando, ErroCarga, FaixaNumeros, Formulario, Metrica, Modal, Pagina, Vazio,
} from '../componentes/ui'
import { get, post, put } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, data, nomeMes, valorCampo } from '../lib/formato'
import type { Caixinha, Movimento } from '../lib/tipos'

type Acao = { tipo: 'nova' } | { tipo: 'editar' | 'guardar' | 'retirar' | 'historico'; c: Caixinha }

/** O que você guarda, com meta opcional. As caixinhas não pertencem a nenhum mês. */
export function Caixinhas() {
  const { dados, erro, tentarDeNovo } = useDados(() =>
    get<{ caixinhas: Caixinha[]; tem_historico: boolean }>('/api/caixinhas'))
  const [acao, setAcao] = useState<Acao | null>(null)
  const fechar = () => setAcao(null)
  const lista = dados?.caixinhas ?? []
  const total = lista.reduce((s, c) => s + c.valor, 0)
  const falta = lista.reduce((s, c) => s + (c.falta ?? 0), 0)

  return (
    <Pagina titulo="Caixinhas" descricao="Dinheiro guardado. Não muda na virada de mês."
      acoes={<button className="botao primario" onClick={() => setAcao({ tipo: 'nova' })}>Nova caixinha</button>}>
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> : (
        <>
          <FaixaNumeros>
            <Metrica rotulo="Guardado" valor={brl(total)} tom="positivo" detalhe={`${lista.length} caixinhas`} />
            <Metrica rotulo="Falta para as metas" valor={brl(falta)} detalhe="Quanto ainda falta guardar" />
          </FaixaNumeros>
          {lista.length === 0 ? <Vazio>Nenhuma caixinha ainda. Use "Nova caixinha".</Vazio> : (
            <ul className="caixinhas">
              {lista.map((c) => (
                <li key={c.id} className="caixinha">
                  <div className="cx-topo">
                    <div>
                      <span className="cx-dono">{c.dono}</span>
                      <h3>{c.nome}</h3>
                    </div>
                    <strong className="num cx-valor">{brl(c.valor)}</strong>
                  </div>
                  {c.meta ? (
                    <div className="cx-meta">
                      <Barra valor={c.valor} total={c.meta} cor="var(--primaria)" />
                      <span className="suave pequeno">
                        {c.progresso}% de {brl(c.meta)}
                        {c.data_alvo && ` até ${nomeMes(c.data_alvo)}`}
                        {c.por_mes ? `, guardar ${brl(c.por_mes)} por mês` : ''}
                      </span>
                    </div>
                  ) : <span className="suave pequeno">Sem meta</span>}
                  <div className="cx-acoes">
                    <button className="botao" onClick={() => setAcao({ tipo: 'guardar', c })}>Guardar</button>
                    <button className="botao" onClick={() => setAcao({ tipo: 'retirar', c })} disabled={c.valor <= 0}>Retirar</button>
                    {dados.tem_historico && (
                      <button className="botao-link" onClick={() => setAcao({ tipo: 'historico', c })}>Histórico</button>
                    )}
                    <button className="botao-link" onClick={() => setAcao({ tipo: 'editar', c })}>Editar</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
      <Modal titulo="Nova caixinha" aberto={acao?.tipo === 'nova'} fechar={fechar}><FormNova fechar={fechar} /></Modal>
      {acao && acao.tipo !== 'nova' && (
        <>
          <Modal titulo="Editar caixinha" aberto={acao.tipo === 'editar'} fechar={fechar}>
            <FormEditar c={acao.c} fechar={fechar} />
          </Modal>
          <Modal titulo={`${acao.tipo === 'guardar' ? 'Guardar em' : 'Retirar de'} ${acao.c.nome}`}
            aberto={acao.tipo === 'guardar' || acao.tipo === 'retirar'} fechar={fechar}>
            <FormMovimento c={acao.c} retirar={acao.tipo === 'retirar'} fechar={fechar} />
          </Modal>
          <Modal titulo={`Histórico: ${acao.c.nome}`} aberto={acao.tipo === 'historico'} fechar={fechar}>
            <Historico c={acao.c} />
          </Modal>
        </>
      )}
    </Pagina>
  )
}

function FormNova({ fechar }: { fechar: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [dono, setDono] = useState('')
  const [nome, setNome] = useState('')
  const [valor, setValor] = useState('')
  return (
    <Formulario rotulo="Criar caixinha" enviar={async () => {
      await post('/api/caixinhas', { dono, nome, valor: valor || 0 })
      await atualizar()
      fechar()
      avisar(`Caixinha ${nome} criada.`)
    }}>
      <Campo rotulo="Dono">{(id) => <input id={id} value={dono} onChange={(e) => setDono(e.target.value)} required placeholder="Ex.: Rafael" autoFocus />}</Campo>
      <Campo rotulo="Nome da caixinha">{(id) => <input id={id} value={nome} onChange={(e) => setNome(e.target.value)} required placeholder="Ex.: Viagem" />}</Campo>
      <Campo rotulo="Valor guardado">{(id) => <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" placeholder="R$ 0,00" />}</Campo>
    </Formulario>
  )
}

function FormEditar({ c, fechar }: { c: Caixinha; fechar: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [dono, setDono] = useState(c.dono)
  const [nome, setNome] = useState(c.nome)
  const [valor, setValor] = useState(valorCampo(c.valor))
  const [meta, setMeta] = useState(valorCampo(c.meta))
  const [alvo, setAlvo] = useState(c.data_alvo ?? '')
  return (
    <Formulario enviar={async () => {
      await put(`/api/caixinhas/${c.id}`, { dono, nome, valor, meta: meta || null, data_alvo: alvo || null })
      await atualizar()
      fechar()
      avisar('Caixinha salva.')
    }}>
      <div className="duas-colunas">
        <Campo rotulo="Dono">{(id) => <input id={id} value={dono} onChange={(e) => setDono(e.target.value)} required />}</Campo>
        <Campo rotulo="Nome">{(id) => <input id={id} value={nome} onChange={(e) => setNome(e.target.value)} required />}</Campo>
      </div>
      <Campo rotulo="Valor guardado" dica="Mudar aqui fica no histórico como ajuste.">{(id) => (
        <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required />
      )}</Campo>
      <div className="duas-colunas">
        <Campo rotulo="Meta (opcional)">{(id) => <input id={id} value={meta} onChange={(e) => setMeta(e.target.value)} inputMode="decimal" placeholder="R$ 0,00" />}</Campo>
        <Campo rotulo="Data alvo (opcional)">{(id) => <input id={id} type="month" value={alvo} onChange={(e) => setAlvo(e.target.value)} />}</Campo>
      </div>
    </Formulario>
  )
}

function FormMovimento({ c, retirar, fechar }: { c: Caixinha; retirar: boolean; fechar: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [valor, setValor] = useState('')
  const [descricao, setDescricao] = useState('')
  return (
    <Formulario rotulo={retirar ? 'Retirar' : 'Guardar'} enviar={async () => {
      const nova = await post<Caixinha>(`/api/caixinhas/${c.id}/${retirar ? 'retirar' : 'guardar'}`, { valor, descricao })
      await atualizar()
      fechar()
      avisar(`${c.nome} ficou com ${brl(nova.valor)}.`)
    }}>
      <p className="suave">Hoje: <strong className="num">{brl(c.valor)}</strong></p>
      <Campo rotulo="Valor">{(id) => <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required placeholder="R$ 0,00" autoFocus />}</Campo>
      <Campo rotulo="Descrição">{(id) => <input id={id} value={descricao} onChange={(e) => setDescricao(e.target.value)} placeholder="Opcional" />}</Campo>
    </Formulario>
  )
}

function Historico({ c }: { c: Caixinha }) {
  const { dados, erro, tentarDeNovo } = useDados(() => get<Movimento[]>(`/api/caixinhas/${c.id}/historico`), [c.id])
  if (erro && !dados) return <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} />
  if (!dados) return <Carregando />
  if (dados.length === 0) return <Vazio>Nenhum movimento ainda.</Vazio>
  return (
    <ul className="linhas linhas-simples">
      {dados.map((m) => (
        <li key={m.id} className="linha">
          <span className="linha-principal">
            <span className="linha-titulo">{m.descricao || (m.valor > 0 ? 'Guardado' : 'Retirada')}</span>
            <span className="linha-meta">{data(m.data)}, ficou com {brl(m.saldo)}</span>
          </span>
          <span className={`num ${m.valor > 0 ? 'tom-positivo' : 'tom-negativo'}`}>{m.valor > 0 ? '+' : ''}{brl(m.valor)}</span>
        </li>
      ))}
    </ul>
  )
}
