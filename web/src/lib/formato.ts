const reais = new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' })

/** 1250.5 -> "R$ 1.250,50" */
export const brl = (v: number | null | undefined) => reais.format(v ?? 0)

export const pct = (v: number | null | undefined) =>
  v == null ? '—' : `${v.toLocaleString('pt-BR', { maximumFractionDigits: 1 })}%`

const MESES = ['Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho', 'Julho', 'Agosto',
  'Setembro', 'Outubro', 'Novembro', 'Dezembro']

/** "2026-11" -> "Novembro 26" (o mesmo nome do app desktop) */
export function nomeMes(codigo: string) {
  const [ano, mes] = codigo.split('-')
  return `${MESES[Number(mes) - 1]} ${ano.slice(2)}`
}

/** "2026-11" -> "novembro de 2026" */
export function nomeMesLongo(codigo: string) {
  const [ano, mes] = codigo.split('-')
  return `${MESES[Number(mes) - 1].toLowerCase()} de ${ano}`
}

/** "2026-11-05" -> "05/11/2026" */
export function data(iso: string | null | undefined) {
  if (!iso) return '—'
  const [a, m, d] = iso.slice(0, 10).split('-')
  return `${d}/${m}/${a}`
}

/** "2026-11-05T14:30:00" -> "05/11/2026 às 14:30" */
export function dataHora(iso: string) {
  const hora = iso.slice(11, 16)
  return hora ? `${data(iso)} às ${hora}` : data(iso)
}

/** Converte "1.250,50", "1250.5" ou "R$ 10" em número (para validar antes de enviar). */
export function lerValor(texto: string): number | null {
  const t = texto.replace(/R\$|\s/g, '')
  if (!t) return null
  const n = Number(t.includes(',') ? t.replace(/\./g, '').replace(',', '.') : t)
  return Number.isFinite(n) ? n : null
}

/** Valor para preencher um campo de edição: 1250.5 -> "1250,50" */
export const valorCampo = (v: number | null | undefined) => (v == null ? '' : v.toFixed(2).replace('.', ','))
