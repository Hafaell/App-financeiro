"""Empréstimos: o que cada pessoa deve no mês e os pagamentos recebidos."""
from datetime import date

from .utilidades import dinheiro


class Emprestimos:
    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    def por_pessoa(self, mes=None):
        """Por pessoa, no mês: emprestado, já pago e em aberto.
        A dívida é a soma do valor da parcela. Pagamentos contam no mês em que foram registrados."""
        m = self.meses.interpretar(mes)
        dividas = self.banco.consultar(
            "SELECT pessoa, SUM(valor_parcela) AS total FROM compras "
            "WHERE emprestimo = 1 AND mes = ? GROUP BY pessoa ORDER BY pessoa", (m,))
        pago = {r["pessoa"]: r["total"] for r in self.banco.consultar(
            "SELECT pessoa, SUM(valor) AS total FROM pagamentos WHERE mes = ? GROUP BY pessoa",
            (m,))}
        resultado = []
        for r in dividas:
            total = round(r["total"], 2)
            recebido = round(pago.get(r["pessoa"], 0), 2)
            resultado.append({"pessoa": r["pessoa"], "emprestado": total,
                              "ja_pago": recebido, "em_aberto": round(total - recebido, 2)})
        return resultado

    def detalhe(self, pessoa, mes=None):
        """Empréstimos de uma pessoa. Com mes=None, traz todos os meses."""
        if mes is None:
            return self.banco.consultar(
                "SELECT * FROM compras WHERE emprestimo = 1 AND pessoa = ? ORDER BY mes, id",
                (pessoa,))
        return self.banco.consultar(
            "SELECT * FROM compras WHERE emprestimo = 1 AND pessoa = ? AND mes = ? ORDER BY id",
            (pessoa, self.meses.interpretar(mes)))

    def pagar(self, pessoa, valor, descricao="", mes=None) -> int:
        p = str(pessoa or "").strip()
        if not p:
            raise ValueError("Informe a pessoa.")
        m = self.meses.interpretar(mes)
        self.meses.exigir(m)
        id_, _ = self.banco.gravar(
            "INSERT INTO pagamentos (pessoa, valor, data, descricao, mes) VALUES (?,?,?,?,?)",
            (p, dinheiro(valor), date.today().isoformat(), descricao or "", m))
        return id_
