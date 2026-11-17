import { useEffect, useState } from 'react'
import {
  Campo, Carregando, ErroCarga, Formulario, Modal, Pagina, Secao, SeloCartao, Vazio, useConfirmar,
} from '../componentes/ui'
import { baixar, del, get, patch, post, put, q } from '../lib/api'
import { useDados, useEstado } from '../lib/estado'
import { brl, dataHora, nomeMes, valorCampo } from '../lib/formato'
import { supabase } from '../lib/supabase'
import type { Cartao, Categoria, Gasto, Previsao, Resumo } from '../lib/tipos'

/** Manutenção: busca, meses e virada, renda, cartões, categorias, cópias, backup, relatório e conta. */
export function Ferramentas() {
  const [perguntar, confirmacao] = useConfirmar()
  return (
    <Pagina titulo="Ferramentas" descricao="Cadastros, virada de mês, cópias de segurança e sua conta.">
      <div className="indice-ferramentas">
        {[['busca', 'Buscar'], ['meses', 'Meses'], ['renda', 'Renda'], ['cartoes', 'Cartões'], ['categorias', 'Categorias'],
          ['copias', 'Cópias'], ['backup', 'Backup'], ['relatorio', 'Relatório'], ['conta', 'Conta']].map(([id, r]) => (
          <a key={id} href={`#${id}`} className="chip">{r}</a>
        ))}
      </div>
      <Busca />
      <Meses perguntar={perguntar} />
      <Renda />
      <Cartoes />
      <Categorias perguntar={perguntar} />
      <Copias perguntar={perguntar} />
      <Backup />
      <Relatorio />
      <Conta />
      {confirmacao}
    </Pagina>
  )
}

type Perguntar = (texto: string, acao: () => Promise<void>, botao?: string) => void

function Busca() {
  const [texto, setTexto] = useState('')
  const [resultado, setResultado] = useState<{ itens: { mes: string; mes_nome: string; origem: string; texto: string; valor: number; extra: string }[]; total: number } | null>(null)
  const { falhar } = useEstado()
  return (
    <div id="busca"><Secao titulo="Buscar" descricao="Procurar um item, pessoa ou descrição em todos os meses.">
      <form className="linha-form" onSubmit={async (e) => {
        e.preventDefault()
        try {
          setResultado(await get(`/api/buscar${q({ texto })}`))
        } catch (err) {
          falhar(err)
        }
      }}>
        <input type="search" value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Ex.: Uber"
          aria-label="Texto para buscar" />
        <button className="botao primario">Buscar</button>
      </form>
      {resultado && (resultado.itens.length === 0 ? <Vazio>Nada encontrado.</Vazio> : (
        <>
          <ul className="linhas linhas-simples">
            {resultado.itens.map((l, i) => (
              <li key={i} className="linha">
                <span className="linha-principal">
                  <span className="linha-titulo">{l.texto}</span>
                  <span className="linha-meta">
                    <span>{l.mes_nome}</span><span>{l.origem}</span>
                    {l.extra && l.extra !== '.' && <span className="etiqueta etiqueta-pessoa">{l.extra}</span>}
                  </span>
                </span>
                <span className="num">{brl(l.valor)}</span>
              </li>
            ))}
          </ul>
          <p className="totais"><span>{resultado.itens.length} itens, total <strong className="num">{brl(resultado.total)}</strong></span></p>
        </>
      ))}
    </Secao></div>
  )
}

function Meses({ perguntar }: { perguntar: Perguntar }) {
  const { inicio, atualizar, avisar } = useEstado()
  const [previsao, setPrevisao] = useState<Previsao | null>(null)
  const [virando, setVirando] = useState(false)
  const atual = inicio.mes_ativo

  useEffect(() => {
    if (virando) get<Previsao>('/api/previsao').then(setPrevisao).catch(() => setPrevisao(null))
  }, [virando])

  return (
    <div id="meses"><Secao titulo="Meses abertos" descricao="Só meses abertos recebem lançamentos. O mês atual é o mais recente."
      acoes={<button className="botao primario" onClick={() => setVirando(true)}>Virar o mês</button>}>
      <ul className="linhas linhas-simples">
        {[...inicio.meses].reverse().map((m) => (
          <li key={m} className="linha">
            <span className="linha-principal"><span className="linha-titulo">{nomeMes(m)}</span></span>
            {m === atual ? <span className="etiqueta">Atual</span> : (
              <button className="botao-link perigo-texto" onClick={() => perguntar(
                `Apagar ${nomeMes(m)} com todas as compras, receitas, despesas e pagamentos dele? Não dá para desfazer.`,
                async () => {
                  await del(`/api/meses/${m}`)
                  await atualizar()
                  avisar(`${nomeMes(m)} apagado.`)
                }, 'Apagar o mês')}>Apagar</button>
            )}
          </li>
        ))}
      </ul>
      <Modal titulo="Virar o mês" aberto={virando} fechar={() => setVirando(false)}>
        <p>Abre o mês seguinte copiando {nomeMes(atual)}: recorrentes ficam, parcelas avançam, à vista e última parcela saem,
          receitas são copiadas e caixinhas não mudam. Antes, uma cópia de segurança de tudo é salva.</p>
        {previsao ? (
          <dl className="resumo-previsao">
            <div><dt>{previsao.nome} começa com receitas</dt><dd className="num">{brl(previsao.receitas)}</dd></div>
            <div><dt>Despesas</dt><dd className="num">{brl(previsao.despesas)}</dd></div>
            <div><dt>Meu cartão</dt><dd className="num">{brl(previsao.meu_cartao)}</dd></div>
            <div><dt>Saldo previsto</dt><dd className="num">{brl(previsao.saldo)}</dd></div>
          </dl>
        ) : <Carregando />}
        <Formulario rotulo={previsao ? `Abrir ${previsao.nome}` : 'Virar o mês'} enviar={async () => {
          const r = await post<{ novo: string; avancadas: unknown[]; removidas: unknown[] }>('/api/meses/virar')
          await atualizar()
          setVirando(false)
          avisar(`${nomeMes(r.novo)} aberto: ${r.avancadas.length} parcelas avançaram e ${r.removidas.length} itens saíram.`)
        }}>{null}</Formulario>
      </Modal>
    </Secao></div>
  )
}

function Renda() {
  const { mes, atualizar, avisar } = useEstado()
  const { dados } = useDados(() => get<{ valor: number | null }>(`/api/renda${q({ mes })}`))
  const [valor, setValor] = useState('')
  useEffect(() => setValor(valorCampo(dados?.valor)), [dados])
  return (
    <div id="renda"><Secao titulo="Renda do mês" descricao={`Quanto você recebe no total em ${nomeMes(mes)}. Serve para medir quanto o cartão consome.`}>
      <Formulario rotulo="Salvar renda" enviar={async () => {
        await put('/api/renda', { valor, mes })
        await atualizar()
        avisar(`Renda de ${nomeMes(mes)} salva.`)
      }}>
        <Campo rotulo="Renda total do mês">{(id) => (
          <input id={id} value={valor} onChange={(e) => setValor(e.target.value)} inputMode="decimal" required placeholder="Ex.: R$ 5.000,00" />
        )}</Campo>
      </Formulario>
    </Secao></div>
  )
}

function Cartoes() {
  const { inicio } = useEstado()
  const [novo, setNovo] = useState(false)
  const [datas, setDatas] = useState<Cartao | null>(null)
  return (
    <div id="cartoes"><Secao titulo="Cartões" descricao="Cores e dias de fechamento e vencimento (para os avisos da Visão geral)."
      acoes={<button className="botao" onClick={() => setNovo(true)}>Novo cartão</button>}>
      <ul className="linhas">
        {inicio.cartoes.map((c) => (
          <li key={c.id}>
            <button className="linha" onClick={() => setDatas(c)}>
              <span className="linha-principal">
                <span className="linha-titulo"><SeloCartao nome={c.nome} cartoes={inicio.cartoes} /></span>
                <span className="linha-meta">
                  <span>Fecha dia {c.dia_fechamento ?? '—'}</span><span>Vence dia {c.dia_vencimento ?? '—'}</span>
                </span>
              </span>
              <span className="suave pequeno">Editar datas</span>
            </button>
          </li>
        ))}
      </ul>
      <Modal titulo="Novo cartão" aberto={novo} fechar={() => setNovo(false)}><FormCartao fechar={() => setNovo(false)} /></Modal>
      <Modal titulo={`Datas do ${datas?.nome ?? ''}`} aberto={datas !== null} fechar={() => setDatas(null)}>
        {datas && <FormDatas c={datas} fechar={() => setDatas(null)} />}
      </Modal>
    </Secao></div>
  )
}

function FormCartao({ fechar }: { fechar: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [nome, setNome] = useState('')
  const [cor, setCor] = useState('#0E6B66')
  return (
    <Formulario rotulo="Cadastrar cartão" enviar={async () => {
      await post('/api/cartoes', { nome, cor })
      await atualizar()
      fechar()
      avisar(`Cartão ${nome} cadastrado.`)
    }}>
      <Campo rotulo="Nome">{(id) => <input id={id} value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus placeholder="Ex.: C6" />}</Campo>
      <Campo rotulo="Cor">{(id) => <input id={id} type="color" value={cor} onChange={(e) => setCor(e.target.value)} />}</Campo>
    </Formulario>
  )
}

function FormDatas({ c, fechar }: { c: Cartao; fechar: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [fecha, setFecha] = useState(c.dia_fechamento?.toString() ?? '')
  const [vence, setVence] = useState(c.dia_vencimento?.toString() ?? '')
  return (
    <Formulario enviar={async () => {
      await patch(`/api/cartoes/${c.id}/datas`, {
        dia_fechamento: fecha ? Number(fecha) : null, dia_vencimento: vence ? Number(vence) : null,
      })
      await atualizar()
      fechar()
      avisar(`Datas do ${c.nome} salvas.`)
    }}>
      <div className="duas-colunas">
        <Campo rotulo="Dia do fechamento">{(id) => <input id={id} type="number" min={1} max={31} value={fecha} onChange={(e) => setFecha(e.target.value)} />}</Campo>
        <Campo rotulo="Dia do vencimento">{(id) => <input id={id} type="number" min={1} max={31} value={vence} onChange={(e) => setVence(e.target.value)} />}</Campo>
      </div>
    </Formulario>
  )
}

function Categorias({ perguntar }: { perguntar: Perguntar }) {
  const { inicio, atualizar, avisar } = useEstado()
  const [editar, setEditar] = useState<Categoria | 'nova' | null>(null)
  return (
    <div id="categorias"><Secao titulo="Categorias e limites" descricao="Limite mensal de cada categoria (aparece no orçamento da Visão geral)."
      acoes={<button className="botao" onClick={() => setEditar('nova')}>Nova categoria</button>}>
      <ul className="linhas">
        {inicio.categorias.map((c) => (
          <li key={c.id}>
            <button className="linha" onClick={() => setEditar(c)}>
              <span className="linha-principal">
                <span className="linha-titulo"><span className="ponto" style={{ background: c.cor }} />{c.nome}</span>
              </span>
              <span className="num suave">{c.orcamento > 0 ? `Limite ${brl(c.orcamento)}` : 'Sem limite'}</span>
            </button>
          </li>
        ))}
      </ul>
      <Modal titulo={editar === 'nova' ? 'Nova categoria' : 'Editar categoria'} aberto={editar !== null} fechar={() => setEditar(null)}>
        {editar && (
          <FormCategoria c={editar === 'nova' ? undefined : editar} fechar={() => setEditar(null)}
            apagar={editar === 'nova' ? undefined : () => {
              const c = editar
              setEditar(null)
              perguntar(`Apagar a categoria ${c.nome}? Os lançamentos dela ficam sem categoria.`, async () => {
                await del(`/api/categorias/${c.id}`)
                await atualizar()
                avisar(`Categoria ${c.nome} apagada.`)
              })
            }} />
        )}
      </Modal>
    </Secao></div>
  )
}

function FormCategoria({ c, fechar, apagar }: { c?: Categoria; fechar: () => void; apagar?: () => void }) {
  const { atualizar, avisar } = useEstado()
  const [nome, setNome] = useState(c?.nome ?? '')
  const [cor, setCor] = useState(c?.cor ?? '#6B7280')
  const [orcamento, setOrcamento] = useState(c && c.orcamento > 0 ? valorCampo(c.orcamento) : '')
  return (
    <Formulario enviar={async () => {
      const dados = { nome, cor, orcamento: orcamento || 0 }
      if (c) await put(`/api/categorias/${c.id}`, dados)
      else await post('/api/categorias', dados)
      await atualizar()
      fechar()
      avisar(`Categoria ${nome} salva.`)
    }} extra={apagar && <button type="button" className="botao perigo-texto" onClick={apagar}>Apagar</button>}>
      <Campo rotulo="Nome">{(id) => <input id={id} value={nome} onChange={(e) => setNome(e.target.value)} required autoFocus={!c} />}</Campo>
      <div className="duas-colunas">
        <Campo rotulo="Cor">{(id) => <input id={id} type="color" value={cor} onChange={(e) => setCor(e.target.value)} />}</Campo>
        <Campo rotulo="Limite por mês" dica="Vazio = sem limite">{(id) => (
          <input id={id} value={orcamento} onChange={(e) => setOrcamento(e.target.value)} inputMode="decimal" placeholder="R$ 0,00" />
        )}</Campo>
      </div>
    </Formulario>
  )
}

function Copias({ perguntar }: { perguntar: Perguntar }) {
  const { atualizar, avisar } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() => get<{ id: number; quando: string; motivo: string }[]>('/api/backups'))
  return (
    <div id="copias"><Secao titulo="Cópias automáticas"
      descricao="Salvas pelo site antes de virar o mês e antes de restaurar (as 6 mais novas de cada). As cópias do app do computador ficam no computador.">
      {erro && !dados ? <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} /> : !dados ? <Carregando /> :
        dados.length === 0 ? <Vazio>Nenhuma cópia ainda. A primeira é salva na próxima virada de mês.</Vazio> : (
          <ul className="linhas linhas-simples">
            {dados.map((b) => (
              <li key={b.id} className="linha">
                <span className="linha-principal">
                  <span className="linha-titulo">{b.motivo}</span>
                  <span className="linha-meta">{dataHora(b.quando)}</span>
                </span>
                <button className="botao" onClick={() => perguntar(
                  `Voltar todos os seus dados para como estavam em ${dataHora(b.quando)}? O que foi feito depois some. Antes, uma cópia do estado atual é salva.`,
                  async () => {
                    await post('/api/backups/restaurar', { id: b.id })
                    await atualizar()
                    avisar('Cópia restaurada.')
                  }, 'Restaurar')}>Restaurar</button>
              </li>
            ))}
          </ul>
        )}
    </Secao></div>
  )
}

function Backup() {
  const { avisar } = useEstado()
  const [senha, setSenha] = useState('')
  return (
    <div id="backup"><Secao titulo="Backup com senha" descricao="Baixa um arquivo .cfbak com todos os seus dados, protegido pela senha que você escolher.">
      <Formulario rotulo="Baixar backup" enviar={async () => {
        await baixar('/api/backups/exportar', { senha }, 'controle-financeiro.cfbak')
        setSenha('')
        avisar('Backup baixado. Guarde a senha: sem ela o arquivo não abre.')
      }}>
        <Campo rotulo="Senha do arquivo" dica="Pelo menos 6 caracteres.">{(id) => (
          <input id={id} type="password" value={senha} onChange={(e) => setSenha(e.target.value)} minLength={6} required autoComplete="new-password" />
        )}</Campo>
      </Formulario>
    </Secao></div>
  )
}

function Relatorio() {
  const [aberto, setAberto] = useState(false)
  return (
    <div id="relatorio"><Secao titulo="Relatório do mês" descricao="Resumo do mês para imprimir ou salvar em PDF."
      acoes={<button className="botao" onClick={() => setAberto(true)}>Abrir relatório</button>}>
      <Modal titulo="Relatório do mês" aberto={aberto} fechar={() => setAberto(false)} largo>
        <ConteudoRelatorio />
      </Modal>
    </Secao></div>
  )
}

function ConteudoRelatorio() {
  const { mes, nomeCategoria } = useEstado()
  const { dados, erro, tentarDeNovo } = useDados(() =>
    get<{ resumo: Resumo; gasto: Gasto[] }>(`/api/painel${q({ mes })}`))
  if (erro && !dados) return <ErroCarga mensagem={erro} tentarDeNovo={tentarDeNovo} />
  if (!dados) return <Carregando />
  const r = dados.resumo
  const linhas: [string, number][] = [
    ['Receitas', r.receitas], ['Despesas', r.despesas_manuais], ['Meu cartão', r.meu_cartao_total],
    ...Object.entries(r.cartoes).map(([n, v]) => [`  Cartão ${n} (com empréstimos: ${brl(v.com_emprestimos)})`, v.meu_cartao] as [string, number]),
    ['A receber de pessoas', r.a_receber_de_pessoas], ['Saldo', r.saldo],
  ]
  return (
    <div className="relatorio">
      <h2>Resumo de {nomeMes(mes)}</h2>
      <table className="tabela">
        <tbody>{linhas.map(([k, v]) => <tr key={k}><td>{k}</td><td className="direita num">{brl(v)}</td></tr>)}</tbody>
      </table>
      <h3>Por categoria</h3>
      <table className="tabela">
        <tbody>
          {[...dados.gasto].sort((a, b) => b.valor - a.valor).map((g) => (
            <tr key={String(g.categoria_id)}><td>{nomeCategoria(g.categoria_id)}</td><td className="direita num">{brl(g.valor)}</td></tr>
          ))}
        </tbody>
      </table>
      <div className="form-acoes nao-imprimir">
        <button className="botao primario" onClick={() => window.print()}>Imprimir ou salvar PDF</button>
      </div>
    </div>
  )
}

function Conta() {
  const { avisar } = useEstado()
  const [email, setEmail] = useState('')
  const [senha, setSenha] = useState('')
  useEffect(() => {
    supabase?.auth.getUser().then(({ data }) => setEmail(data.user?.email ?? ''))
  }, [])
  if (!supabase) return null
  return (
    <div id="conta"><Secao titulo="Minha conta" descricao={email ? `Conectado como ${email}. A mesma conta do app do computador.` : undefined}
      acoes={<button className="botao" onClick={() => void supabase!.auth.signOut()}>Sair</button>}>
      <Formulario rotulo="Trocar senha" enviar={async () => {
        if (senha.length < 6) throw new Error('Use uma senha de pelo menos 6 caracteres.')
        const { error } = await supabase!.auth.updateUser({ password: senha })
        if (error) throw new Error(error.message)
        setSenha('')
        avisar('Senha trocada. Use a nova no site e no app do computador.')
      }}>
        <Campo rotulo="Nova senha">{(id) => (
          <input id={id} type="password" value={senha} onChange={(e) => setSenha(e.target.value)} autoComplete="new-password" required />
        )}</Campo>
      </Formulario>
    </Secao></div>
  )
}
