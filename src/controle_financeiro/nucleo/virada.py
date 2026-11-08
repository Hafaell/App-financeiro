"""Virada de mês: abre o mês seguinte copiando o mês atual com as regras de parcela."""
import re

from controle_financeiro.nucleo.utilidades import avancar_parcela, proximo_mes, nome_mes


class Virada:
    """Regras:
    - Recorrente (cartões e despesas) permanece, sem avançar parcela.
    - Não recorrente parcelado x/y avança para (x+1)/y; com x >= y, sai.
    - Não recorrente à vista sai. Despesa não recorrente sem parcela sai.
    - Receitas são copiadas. Caixinhas não mudam. O mês de origem não muda.
    """

    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    def executar(self) -> dict:
        origem = self.meses.ativo()
        novo = proximo_mes(origem)
        avancadas, removidas = [], []
        with self.banco.transacao() as con:
            if novo in self.meses.sessoes():
                raise ValueError(f"{nome_mes(novo)} já está aberto.")
            con.execute("INSERT INTO sessoes (mes) VALUES (?)", (novo,))

            for c in con.execute("SELECT * FROM compras WHERE mes = ?", (origem,)).fetchall():
                nova = c["parcelas"] if c["recorrente"] else avancar_parcela(c["parcelas"])
                if nova is None:
                    removidas.append((c["item"], c["cartao"]))
                    continue
                con.execute(
                    "INSERT INTO compras (mes, cartao, item, parcelas, valor_parcela, "
                    "emprestimo, pessoa, valor_real, recorrente, categoria_id) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?)",
                    (novo, c["cartao"], c["item"], nova, c["valor_parcela"],
                     c["emprestimo"], c["pessoa"], c["valor_real"], c["recorrente"], c["categoria_id"]))
                if nova != c["parcelas"]:
                    avancadas.append((c["item"], c["cartao"], nova))

            for d in con.execute("SELECT * FROM despesas WHERE mes = ?", (origem,)).fetchall():
                desc = d["descricao"]
                if d["recorrente"]:
                    con.execute("INSERT INTO despesas (mes, descricao, valor, recorrente, categoria_id) "
                                "VALUES (?,?,?,1,?)", (novo, desc, d["valor"], d["categoria_id"]))
                    continue
                m = re.search(r"\((\d+)/(\d+)\)", desc)
                nova = avancar_parcela(f"{m[1]}/{m[2]}") if m else None
                if nova is None:
                    removidas.append((desc, "Despesa"))
                    continue
                desc = desc.replace(m[0], f"({nova})")
                avancadas.append((desc, "Despesa", nova))
                con.execute("INSERT INTO despesas (mes, descricao, valor, recorrente, categoria_id) "
                            "VALUES (?,?,?,0,?)", (novo, desc, d["valor"], d["categoria_id"]))

            for r in con.execute("SELECT * FROM receitas WHERE mes = ?", (origem,)).fetchall():
                con.execute("INSERT INTO receitas (mes, descricao, valor) VALUES (?,?,?)",
                            (novo, r["descricao"], r["valor"]))
        return {"origem": origem, "novo": novo, "avancadas": avancadas, "removidas": removidas}
