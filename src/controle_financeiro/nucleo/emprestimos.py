"""Empréstimos: o que cada pessoa deve no mês e os pagamentos recebidos."""
from datetime import date

from controle_financeiro.nucleo.utilidades import dinheiro


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

    def pessoas(self):
        """Nomes de todas as pessoas que já tiveram empréstimo ou pagamento, em ordem alfabética."""
        nomes = {r["pessoa"] for r in self.banco.consultar(
            "SELECT DISTINCT pessoa FROM compras WHERE emprestimo = 1")}
        nomes |= {r["pessoa"] for r in self.banco.consultar("SELECT DISTINCT pessoa FROM pagamentos")}
        return sorted((n for n in nomes if n and n != "."), key=str.lower)

    def detalhe(self, pessoa, mes=None):
        """Empréstimos de uma pessoa. Com mes=None, traz todos os meses."""
        if mes is None:
            return self.banco.consultar(
                "SELECT * FROM compras WHERE emprestimo = 1 AND pessoa = ? ORDER BY mes, id",
                (pessoa,))
        return self.banco.consultar(
            "SELECT * FROM compras WHERE emprestimo = 1 AND pessoa = ? AND mes = ? ORDER BY id",
            (pessoa, self.meses.interpretar(mes)))

    def listar_pagamentos(self, pessoa, mes=None):
        """Pagamentos recebidos de uma pessoa. Com mes=None, traz todos os meses."""
        if mes is None:
            return self.banco.consultar(
                "SELECT * FROM pagamentos WHERE pessoa = ? ORDER BY mes, id", (pessoa,))
        return self.banco.consultar(
            "SELECT * FROM pagamentos WHERE pessoa = ? AND mes = ? ORDER BY id",
            (pessoa, self.meses.interpretar(mes)))

    def obter_pagamento(self, id_):
        linhas = self.banco.consultar("SELECT * FROM pagamentos WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def editar_pagamento(self, id_, **campos) -> dict:
        """Muda só os campos informados (pessoa, valor, descricao) de um pagamento.
        Mantém o id, o mês e a data em que foi registrado. Devolve o pagamento como ficou."""
        desconhecidos = set(campos) - {"pessoa", "valor", "descricao"}
        if desconhecidos:
            raise ValueError(f"Campo que não pode ser editado em pagamento: {', '.join(sorted(desconhecidos))}.")
        atual = self.obter_pagamento(id_)
        if not atual:
            raise ValueError("Pagamento não encontrado.")
        if atual["mes"]:
            self.meses.exigir(atual["mes"])
        novos = {k: atual[k] for k in ("pessoa", "valor", "descricao")}
        novos.update(campos)
        pessoa = str(novos["pessoa"] or "").strip()
        if not pessoa:
            raise ValueError("Informe a pessoa.")
        self.banco.gravar("UPDATE pagamentos SET pessoa = ?, valor = ?, descricao = ? WHERE id = ?",
                          (pessoa, dinheiro(novos["valor"]), novos["descricao"] or "", int(id_)))
        return self.obter_pagamento(id_)

    def apagar_pagamento(self, id_) -> bool:
        """Apaga um pagamento registrado (o valor volta a ficar em aberto para a pessoa)."""
        atual = self.obter_pagamento(id_)
        if not atual:
            raise ValueError("Pagamento não encontrado.")
        if atual["mes"]:
            self.meses.exigir(atual["mes"])
        _, n = self.banco.gravar("DELETE FROM pagamentos WHERE id = ?", (int(id_),))
        return n > 0

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
