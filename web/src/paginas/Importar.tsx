import { useState } from 'react'
import { Pagina, Secao, Vazio } from '../componentes/ui'
import { post } from '../lib/api'
import { useEstado } from '../lib/estado'
import { brl, data, nomeMes } from '../lib/formato'

interface Item {
  data: string
  descricao: string
  parcelas: string
  valor: number
  credito: boolean
  mes_fora: boolean
  situacao: string
  categoria_id?: number | null
  pessoa?: string
}

function base64(arquivo: File): Promise<string> {
  return new Promise((ok, erro) => {
    const leitor = new FileReader()
    leitor.onload = () => ok(String(leitor.result).split(',')[1] ?? '')
    leitor.onerror = () => erro(new Error('Não consegui ler o arquivo.'))
    leitor.readAsDataURL(arquivo)
  })
}

/** Importa o extrato do cartão (CSV ou OFX): mostra o que é novo e lança só o que você marcar. */
export function Importar() {
  const { inicio, mes, atualizar, avisar, falhar } = useEstado()
  const [itens, setItens] = useState<Item[] | null>(null)
  const [marcados, setMarcados] = useState<Set<number>>(new Set())
  const [destino, setDestino] = useState(inicio.cartoes[0]?.nome ?? 'despesas')
  const [arquivo, setArquivo] = useState('')
  const [ocupado, setOcupado] = useState(false)

  const ler = async (f: File | undefined) => {
    if (!f) return
    setOcupado(true)
    try {
      const r = await post<{ itens: Item[]; cartao_sugerido: string | null }>('/api/extrato/ler', {
        nome: f.name, conteudo_base64: await base64(f), mes,
      })
      setArquivo(f.name)
      setItens(r.itens)
      setMarcados(new Set(r.itens.flatMap((it, i) => (it.situacao === 'Novo' ? [i] : []))))
      const sugerido = inicio.cartoes.find((c) => c.nome === r.cartao_sugerido)
      if (sugerido) setDestino(sugerido.nome)
    } catch (e) {
      falhar(e)
    } finally {
      setOcupado(false)
    }
  }

  const mudarItem = (i: number, campo: Partial<Item>) =>
    setItens((l) => l && l.map((it, j) => (j === i ? { ...it, ...campo } : it)))

  const importar = async () => {
    if (!itens) return
    setOcupado(true)
    try {
      const escolhidos = itens.filter((_, i) => marcados.has(i))
      const { importados } = await post<{ importados: number }>('/api/extrato/importar', { itens: escolhidos, destino, mes })
      await atualizar()
      avisar(`${importados} ${importados === 1 ? 'item lançado' : 'itens lançados'} em ${nomeMes(mes)}.`)
      setItens(null)
      setArquivo('')
    } catch (e) {
      falhar(e)
    } finally {
      setOcupado(false)
    }
  }

  const total = (itens ?? []).filter((_, i) => marcados.has(i)).reduce((s, it) => s + it.valor, 0)

  return (
    <Pagina titulo="Importar extrato" descricao={`Lança as compras de um extrato (CSV ou OFX) em ${nomeMes(mes)}.`}>
      <Secao titulo="Arquivo do extrato" descricao="Exporte o extrato no app do banco (Nubank: CSV; Inter: OFX ou CSV).">
        <label className="arquivo">
          <input type="file" accept=".csv,.ofx,.txt" disabled={ocupado} onChange={(e) => {
            void ler(e.target.files?.[0])
            e.target.value = ''
          }} />
          <span className="botao">{ocupado && !itens ? 'Lendo…' : 'Escolher arquivo'}</span>
          <span className="suave">{arquivo || 'Nenhum arquivo escolhido'}</span>
        </label>
      </Secao>

      {itens && (
        <Secao titulo="O que lançar" descricao="Novos vêm marcados. Já lançados e pagamentos ficam de fora.">
          {itens.length === 0 ? <Vazio>Nenhum lançamento encontrado no arquivo.</Vazio> : (
            <>
              <div className="campo campo-linha">
                <label htmlFor="destino">Lançar em</label>
                <select id="destino" value={destino} onChange={(e) => setDestino(e.target.value)}>
                  {inicio.cartoes.map((c) => <option key={c.id} value={c.nome}>Cartão {c.nome}</option>)}
                  <option value="despesas">Despesas</option>
                </select>
              </div>
              <ul className="linhas importacao">
                {itens.map((it, i) => (
                  <li key={i} className={`linha${it.situacao !== 'Novo' ? ' apagada' : ''}`}>
                    <input type="checkbox" aria-label={`Lançar ${it.descricao}`} checked={marcados.has(i)}
                      disabled={it.credito}
                      onChange={(e) => setMarcados((m) => {
                        const n = new Set(m)
                        if (e.target.checked) n.add(i)
                        else n.delete(i)
                        return n
                      })} />
                    <span className="linha-principal">
                      <span className="linha-titulo">{it.descricao}</span>
                      <span className="linha-meta">
                        <span>{data(it.data)}</span>
                        {it.parcelas !== '1/1' && <span className="etiqueta">{it.parcelas}</span>}
                        <span className={it.situacao === 'Novo' ? '' : 'tom-aviso'}>{it.situacao}</span>
                        {it.mes_fora && <span className="tom-aviso">Data fora do mês</span>}
                      </span>
                      {marcados.has(i) && (
                        <span className="importacao-extra">
                          <select aria-label="Categoria" value={it.categoria_id ?? ''}
                            onChange={(e) => mudarItem(i, { categoria_id: e.target.value ? Number(e.target.value) : null })}>
                            <option value="">Sem categoria</option>
                            {inicio.categorias.map((c) => <option key={c.id} value={c.id}>{c.nome}</option>)}
                          </select>
                          {destino !== 'despesas' && (
                            <input aria-label="Pessoa" placeholder="Pessoa (se for empréstimo)" value={it.pessoa ?? ''}
                              list="importar-pessoas" onChange={(e) => mudarItem(i, { pessoa: e.target.value })} />
                          )}
                        </span>
                      )}
                    </span>
                    <span className="num">{brl(it.valor)}</span>
                  </li>
                ))}
              </ul>
              <datalist id="importar-pessoas">{inicio.pessoas.map((p) => <option key={p} value={p} />)}</datalist>
              <div className="form-acoes">
                <span className="suave">{marcados.size} marcados, {brl(total)}</span>
                <button className="botao" onClick={() => setItens(null)}>Cancelar</button>
                <button className="botao primario" disabled={ocupado || marcados.size === 0} onClick={importar}>
                  {ocupado ? 'Lançando…' : `Lançar ${marcados.size}`}
                </button>
              </div>
            </>
          )}
        </Secao>
      )}
    </Pagina>
  )
}
