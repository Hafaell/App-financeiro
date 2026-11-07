"""Planejamento: assinaturas (itens recorrentes) e parcelas que ainda vão cair nos próximos meses."""
from .utilidades import nome_mes, proximo_mes


class Planejamento:
    def __init__(self, banco, meses, cartoes):
        self.banco = banco
        self.meses = meses
        self.cartoes = cartoes

    def assinaturas(self, mes=None) -> dict:
        """Itens recorrentes do mês (compras suas e despesas), com o total mensal e anual."""
        m = self.meses.interpretar(mes)
        itens = []
        for c in self.banco.consultar(
                "SELECT item, cartao, valor_parcela FROM compras "
                "WHERE mes = ? AND recorrente = 1 AND emprestimo = 0 ORDER BY item", (m,)):
            itens.append({"item": c["item"], "origem": f"Cartão {c['cartao']}",
                          "valor_mes": round(c["valor_parcela"], 2)})
        for d in self.banco.consultar(
                "SELECT descricao, valor FROM despesas WHERE mes = ? AND recorrente = 1 "
                "ORDER BY descricao", (m,)):
            itens.append({"item": d["descricao"], "origem": "Despesa",
                          "valor_mes": round(d["valor"], 2)})
        total = round(sum(i["valor_mes"] for i in itens), 2)
        return {"itens": itens, "total_mes": total, "total_ano": round(total * 12, 2)}

    def parcelas_futuras(self, mes=None, quantos=6) -> list:
        """Quanto vai cair em cada um dos próximos meses, por cartão.
        Usa as compras suas do mês escolhido com parcelas (x/y): cada mês seguinte soma uma parcela."""
        m = self.meses.interpretar(mes)
        nomes_cartoes = [c["nome"] for c in self.cartoes.listar()]
        compras = self.banco.consultar(
            "SELECT cartao, parcelas, valor_parcela FROM compras "
            "WHERE mes = ? AND emprestimo = 0 AND recorrente = 0", (m,))
        saida = []
        atual = m
        for k in range(1, quantos + 1):
            atual = proximo_mes(atual)
            por_cartao = {n: 0.0 for n in nomes_cartoes}
            for c in compras:
                x, y = (int(p) for p in c["parcelas"].split("/"))
                if x + k <= y:
                    por_cartao[c["cartao"]] = por_cartao.get(c["cartao"], 0) + c["valor_parcela"]
            por_cartao = {n: round(v, 2) for n, v in por_cartao.items()}
            saida.append({"mes": atual, "nome": nome_mes(atual), "por_cartao": por_cartao,
                          "total": round(sum(por_cartao.values()), 2)})
        return saida
