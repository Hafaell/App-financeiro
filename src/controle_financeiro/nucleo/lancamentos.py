"""Receitas e despesas lançadas por mês. Só despesas podem ser recorrentes."""
from datetime import date

from controle_financeiro.config import TABELAS_LANCAMENTO
from controle_financeiro.nucleo.utilidades import dinheiro


class Lancamentos:
    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    @staticmethod
    def _tabela(tabela) -> str:
        if tabela not in TABELAS_LANCAMENTO:
            raise ValueError("Use 'receitas' ou 'despesas'.")
        return tabela

    def listar(self, tabela, mes=None):
        return self.banco.consultar(
            f"SELECT * FROM {self._tabela(tabela)} WHERE mes = ? ORDER BY id",
            (self.meses.interpretar(mes),))

    def obter(self, tabela, id_):
        linhas = self.banco.consultar(
            f"SELECT * FROM {self._tabela(tabela)} WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def adicionar(self, tabela, descricao, valor, mes=None, recorrente=False, categoria_id=None) -> int:
        t = self._tabela(tabela)
        m = self.meses.interpretar(mes)
        self.meses.exigir(m)
        desc = self._descricao(descricao)
        hoje = date.today().isoformat()  # dia em que foi lançado
        if t == "despesas":
            id_, _ = self.banco.gravar(
                "INSERT INTO despesas (mes, descricao, valor, recorrente, categoria_id, data_lancamento) "
                "VALUES (?,?,?,?,?,?)",
                (m, desc, dinheiro(valor), int(bool(recorrente)), self._cat(categoria_id), hoje))
        else:
            id_, _ = self.banco.gravar(
                "INSERT INTO receitas (mes, descricao, valor, data_lancamento) VALUES (?,?,?,?)",
                (m, desc, dinheiro(valor), hoje))
        return id_

    def atualizar(self, tabela, id_, descricao, valor, recorrente=False, categoria_id=None) -> bool:
        t = self._tabela(tabela)
        desc = self._descricao(descricao)
        if t == "despesas":
            _, n = self.banco.gravar(
                "UPDATE despesas SET descricao = ?, valor = ?, recorrente = ?, categoria_id = ? WHERE id = ?",
                (desc, dinheiro(valor), int(bool(recorrente)), self._cat(categoria_id), int(id_)))
        else:
            _, n = self.banco.gravar(f"UPDATE {t} SET descricao = ?, valor = ? WHERE id = ?",
                                     (desc, dinheiro(valor), int(id_)))
        if n == 0:
            raise ValueError("Lançamento não encontrado.")
        return True

    def apagar(self, tabela, id_) -> bool:
        _, n = self.banco.gravar(f"DELETE FROM {self._tabela(tabela)} WHERE id = ?", (int(id_),))
        return n > 0

    @staticmethod
    def _cat(categoria_id):
        return int(categoria_id) if categoria_id not in (None, "") else None

    @staticmethod
    def _descricao(descricao) -> str:
        desc = str(descricao or "").strip()
        if not desc:
            raise ValueError("Informe a descrição.")
        return desc
