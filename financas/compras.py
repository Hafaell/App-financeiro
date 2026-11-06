"""Compras nos cartões. Pessoa preenchida = empréstimo daquela pessoa."""
import re

from .utilidades import dinheiro


class Compras:
    def __init__(self, banco, meses, cartoes):
        self.banco = banco
        self.meses = meses
        self.cartoes = cartoes

    def listar(self, cartao=None, mes=None):
        sql = "SELECT * FROM compras WHERE mes = ?"
        args = [self.meses.interpretar(mes)]
        if cartao:
            sql += " AND cartao = ?"
            args.append(self.cartoes.canonico(cartao))
        return self.banco.consultar(sql + " ORDER BY cartao, id", args)

    def obter(self, id_):
        linhas = self.banco.consultar("SELECT * FROM compras WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def lancar(self, cartao, item, valor_parcela, parcelas="1/1", mes=None,
               pessoa=".", valor_real=None, recorrente=False, categoria_id=None) -> int:
        m = self.meses.interpretar(mes)
        self.meses.exigir(m)
        dados = self._validar(cartao, item, parcelas, valor_parcela, pessoa, valor_real,
                              recorrente, categoria_id)
        id_, _ = self.banco.gravar(
            "INSERT INTO compras (mes, cartao, item, parcelas, valor_parcela, emprestimo, "
            "pessoa, valor_real, recorrente, categoria_id) VALUES (?,?,?,?,?,?,?,?,?,?)", (m,) + dados)
        return id_

    def atualizar(self, id_, cartao, item, parcelas, valor_parcela, pessoa=".",
                  valor_real=None, recorrente=False, categoria_id=None) -> bool:
        dados = self._validar(cartao, item, parcelas, valor_parcela, pessoa, valor_real,
                              recorrente, categoria_id)
        _, n = self.banco.gravar(
            "UPDATE compras SET cartao = ?, item = ?, parcelas = ?, valor_parcela = ?, "
            "emprestimo = ?, pessoa = ?, valor_real = ?, recorrente = ?, categoria_id = ? WHERE id = ?",
            dados + (int(id_),))
        if n == 0:
            raise ValueError("Compra não encontrada.")
        return True

    def apagar(self, id_) -> bool:
        _, n = self.banco.gravar("DELETE FROM compras WHERE id = ?", (int(id_),))
        return n > 0

    def _validar(self, cartao, item, parcelas, valor_parcela, pessoa, valor_real, recorrente,
                 categoria_id=None):
        """Confere os campos e devolve a tupla na ordem das colunas (sem mês e id)."""
        cartao = self.cartoes.canonico(cartao)
        item = str(item or "").strip()
        if not item:
            raise ValueError("Informe a descrição da compra.")
        parcelas = str(parcelas or "").strip() or "1/1"
        if not re.fullmatch(r"\d+/\d+", parcelas):
            raise ValueError("Parcelas deve ser no formato 3/12.")
        valor = dinheiro(valor_parcela)
        if valor <= 0:
            raise ValueError("O valor da parcela precisa ser maior que zero.")
        pessoa = str(pessoa or "").strip() or "."
        if isinstance(recorrente, str):
            recorrente = recorrente.strip().lower() in ("1", "sim", "s", "true", "yes")
        real = None if valor_real in (None, "") else dinheiro(valor_real)
        emprestimo = 1 if pessoa != "." else 0
        cat = int(categoria_id) if categoria_id not in (None, "") else None
        return cartao, item, parcelas, valor, emprestimo, pessoa, real, int(bool(recorrente)), cat
