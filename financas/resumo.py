"""Totais de um mês: cartões, receitas, despesas, saldo e o que as pessoas devem."""
from .utilidades import nome_mes


class Resumo:
    def __init__(self, banco, cartoes, meses, emprestimos):
        self.banco = banco
        self.cartoes = cartoes
        self.meses = meses
        self.emprestimos = emprestimos

    def do_mes(self, mes=None) -> dict:
        m = self.meses.interpretar(mes)
        por_cartao = {c["nome"]: {"meu_cartao": 0.0, "com_emprestimos": 0.0}
                      for c in self.cartoes.listar()}
        for r in self.banco.consultar(
                "SELECT cartao, SUM(valor_parcela) AS total, "
                "SUM(CASE WHEN emprestimo = 0 THEN valor_parcela ELSE 0 END) AS meu "
                "FROM compras WHERE mes = ? GROUP BY cartao", (m,)):
            por_cartao[r["cartao"]] = {"meu_cartao": round(r["meu"], 2),
                                       "com_emprestimos": round(r["total"], 2)}
        meu_total = round(sum(c["meu_cartao"] for c in por_cartao.values()), 2)
        com_total = round(sum(c["com_emprestimos"] for c in por_cartao.values()), 2)
        renda_linhas = self.banco.consultar("SELECT valor FROM rendas WHERE mes = ?", (m,))
        renda = renda_linhas[0]["valor"] if renda_linhas else None
        receitas = round(self._soma("receitas", m), 2)
        despesas = round(self._soma("despesas", m), 2)
        return {
            "mes": nome_mes(m),
            "cartoes": por_cartao,
            "meu_cartao_total": meu_total,
            "cartoes_com_emprestimos_total": com_total,
            "receitas": receitas,
            "despesas_manuais": despesas,
            "saldo": round(receitas - despesas - meu_total, 2),
            "a_receber_de_pessoas": round(
                sum(d["em_aberto"] for d in self.emprestimos.por_pessoa(m)), 2),
            "renda": renda,
            "cartao_percentual_renda": (round(meu_total / renda * 100, 1)
                                        if renda else None),
        }

    def _soma(self, tabela, mes) -> float:
        return self.banco.consultar(
            f"SELECT COALESCE(SUM(valor), 0) AS total FROM {tabela} WHERE mes = ?",
            (mes,))[0]["total"]
