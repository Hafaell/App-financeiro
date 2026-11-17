export interface Cartao {
  id: number
  nome: string
  cor: string
  cor_texto: string
  dia_fechamento: number | null
  dia_vencimento: number | null
}

export interface Categoria {
  id: number
  nome: string
  cor: string
  orcamento: number
}

export interface Inicio {
  meses: string[]
  mes_ativo: string
  cartoes: Cartao[]
  categorias: Categoria[]
  pessoas: string[]
  tem_historico_caixinhas: boolean
  versao: number
}

export interface Compra {
  id: number
  mes: string
  cartao: string
  item: string
  parcelas: string
  valor_parcela: number
  emprestimo: number
  pessoa: string
  recorrente: number
  categoria_id: number | null
  data_lancamento: string | null
}

export interface Lancamento {
  id: number
  mes: string
  descricao: string
  valor: number
  recorrente?: number
  categoria_id?: number | null
  data_lancamento: string | null
}

export interface Resumo {
  mes: string
  cartoes: Record<string, { meu_cartao: number; com_emprestimos: number }>
  meu_cartao_total: number
  cartoes_com_emprestimos_total: number
  receitas: number
  despesas_manuais: number
  saldo: number
  a_receber_de_pessoas: number
  renda: number | null
  cartao_percentual_renda: number | null
}

export interface Alerta {
  cartao: string
  tipo: 'fecha' | 'vence'
  faltam: number
  data: string
}

export interface Gasto {
  categoria_id: number | null
  valor: number
}

export interface Divida {
  pessoa: string
  emprestado: number
  ja_pago: number
  em_aberto: number
}

export interface Caixinha {
  id: number
  dono: string
  nome: string
  valor: number
  meta: number | null
  data_alvo: string | null
  progresso: number | null
  falta: number | null
  meses_restantes: number | null
  por_mes: number | null
}

export interface Movimento {
  id: number
  data: string
  valor: number
  saldo: number
  descricao: string
}

export interface Previsao {
  origem: string
  mes: string
  nome: string
  ja_aberto: boolean
  receitas: number
  despesas: number
  meu_cartao: number
  meu_cartao_por_cartao: Record<string, number>
  emprestimos: number
  saldo: number
}

export type Tabela = 'receitas' | 'despesas'
