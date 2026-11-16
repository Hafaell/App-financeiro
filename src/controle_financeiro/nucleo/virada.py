"""Virada de mês: abre o mês seguinte copiando o mês atual com as regras de parcela.
As mesmas regras servem à previsão do próximo mês (que só calcula, sem gravar)."""
import re

from controle_financeiro.nucleo.utilidades import avancar_parcela, proximo_mes, nome_mes

_PARCELA_NA_DESCRICAO = re.compile(r"\((\d+)/(\d+)\)")


def parcelas_seguintes(compra):
    """Parcelas da compra no mês seguinte, ou None se ela não continua.
    Recorrente fica igual; parcelada x/y avança; última parcela e à vista saem."""
    return compra["parcelas"] if compra["recorrente"] else avancar_parcela(compra["parcelas"])


def descricao_seguinte(despesa):
    """Descrição da despesa no mês seguinte, ou None se ela não continua.
    Recorrente fica igual; com parcela no nome, como "Dentista (2/5)", avança; as outras saem."""
    if despesa["recorrente"]:
        return despesa["descricao"]
    m = _PARCELA_NA_DESCRICAO.search(despesa["descricao"])
    nova = avancar_parcela(f"{m[1]}/{m[2]}") if m else None
    return despesa["descricao"].replace(m[0], f"({nova})") if nova else None


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
                nova = parcelas_seguintes(c)
                if nova is None:
                    removidas.append((c["item"], c["cartao"]))
                    continue
                con.execute(
                    "INSERT INTO compras (mes, cartao, item, parcelas, valor_parcela, "
                    "emprestimo, pessoa, valor_real, recorrente, categoria_id, data_lancamento) "
                    "VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                    (novo, c["cartao"], c["item"], nova, c["valor_parcela"],
                     c["emprestimo"], c["pessoa"], c["valor_real"], c["recorrente"], c["categoria_id"],
                     c["data_lancamento"]))
                if nova != c["parcelas"]:
                    avancadas.append((c["item"], c["cartao"], nova))

            for d in con.execute("SELECT * FROM despesas WHERE mes = ?", (origem,)).fetchall():
                desc = descricao_seguinte(d)
                if desc is None:
                    removidas.append((d["descricao"], "Despesa"))
                    continue
                if desc != d["descricao"]:
                    avancadas.append((desc, "Despesa", _PARCELA_NA_DESCRICAO.search(desc)[0][1:-1]))
                con.execute("INSERT INTO despesas (mes, descricao, valor, recorrente, categoria_id, data_lancamento) "
                            "VALUES (?,?,?,?,?,?)",
                            (novo, desc, d["valor"], int(bool(d["recorrente"])), d["categoria_id"],
                             d["data_lancamento"]))

            for r in con.execute("SELECT * FROM receitas WHERE mes = ?", (origem,)).fetchall():
                con.execute("INSERT INTO receitas (mes, descricao, valor, data_lancamento) VALUES (?,?,?,?)",
                            (novo, r["descricao"], r["valor"], r["data_lancamento"]))
        return {"origem": origem, "novo": novo, "avancadas": avancadas, "removidas": removidas}

    def prever(self, mes=None) -> dict:
        """Como o mês seguinte começaria se a virada fosse feita agora a partir de `mes`
        (vazio = mês atual). Só calcula: nada é gravado. Os totais seguem o resumo do mês
        (meu cartão = compras sem empréstimo; saldo = receitas - despesas - meu cartão)."""
        origem = self.meses.interpretar(mes)
        novo = proximo_mes(origem)
        meu_cartao = emprestimos = 0.0
        por_cartao = {}
        for c in self.banco.consultar("SELECT * FROM compras WHERE mes = ?", (origem,)):
            if parcelas_seguintes(c) is None:
                continue
            if c["emprestimo"]:
                emprestimos += c["valor_parcela"]
            else:
                meu_cartao += c["valor_parcela"]
                por_cartao[c["cartao"]] = por_cartao.get(c["cartao"], 0) + c["valor_parcela"]
        despesas = sum(d["valor"] for d in self.banco.consultar(
            "SELECT * FROM despesas WHERE mes = ?", (origem,)) if descricao_seguinte(d) is not None)
        receitas = self.banco.consultar(
            "SELECT COALESCE(SUM(valor), 0) AS total FROM receitas WHERE mes = ?", (origem,))[0]["total"]
        return {
            "origem": origem, "mes": novo, "nome": nome_mes(novo),
            "ja_aberto": novo in self.meses.sessoes(),
            "receitas": round(receitas, 2),
            "despesas": round(despesas, 2),
            "meu_cartao": round(meu_cartao, 2),
            "meu_cartao_por_cartao": {k: round(v, 2) for k, v in por_cartao.items()},
            "emprestimos": round(emprestimos, 2),
            "saldo": round(receitas - despesas - meu_cartao, 2),
        }
