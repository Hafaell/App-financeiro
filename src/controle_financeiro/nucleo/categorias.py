"""Categorias das compras e despesas, orçamento mensal por categoria e renda do mês."""
import re

from controle_financeiro.nucleo.utilidades import dinheiro


class Categorias:
    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    def listar(self):
        return self.banco.consultar("SELECT * FROM categorias ORDER BY nome")

    def obter(self, id_):
        linhas = self.banco.consultar("SELECT * FROM categorias WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def adicionar(self, nome, cor, orcamento=0) -> int:
        n, c, o = self._validar(nome, cor, orcamento)
        id_, _ = self.banco.gravar("INSERT INTO categorias (nome, cor, orcamento) VALUES (?,?,?)",
                                   (n, c, o))
        return id_

    def atualizar(self, id_, nome, cor, orcamento=0) -> bool:
        n, c, o = self._validar(nome, cor, orcamento)
        try:
            _, linhas = self.banco.gravar(
                "UPDATE categorias SET nome = ?, cor = ?, orcamento = ? WHERE id = ?",
                (n, c, o, int(id_)))
        except Exception as erro:  # nome repetido
            if "UNIQUE" in str(erro).upper() or "duplicate key" in str(erro):
                raise ValueError(f"Já existe uma categoria chamada {n}.") from erro
            raise
        if linhas == 0:
            raise ValueError("Categoria não encontrada.")
        return True

    def apagar(self, id_) -> bool:
        """Apagar uma categoria não apaga os lançamentos: eles ficam sem categoria."""
        with self.banco.transacao() as con:
            con.execute("UPDATE compras SET categoria_id = NULL WHERE categoria_id = ?", (int(id_),))
            con.execute("UPDATE despesas SET categoria_id = NULL WHERE categoria_id = ?", (int(id_),))
            con.execute("DELETE FROM categorias WHERE id = ?", (int(id_),))
        return True

    def gasto_do_mes(self, mes=None) -> dict:
        """Quanto já foi usado em cada categoria no mês: {categoria_id: valor}.
        Conta compras que são suas (sem empréstimo) e despesas lançadas à parte."""
        m = self.meses.interpretar(mes)
        gasto = {}
        for r in self.banco.consultar(
                "SELECT categoria_id, SUM(valor_parcela) AS total FROM compras "
                "WHERE mes = ? AND emprestimo = 0 GROUP BY categoria_id", (m,)):
            gasto[r["categoria_id"]] = gasto.get(r["categoria_id"], 0) + r["total"]
        for r in self.banco.consultar(
                "SELECT categoria_id, SUM(valor) AS total FROM despesas "
                "WHERE mes = ? GROUP BY categoria_id", (m,)):
            gasto[r["categoria_id"]] = gasto.get(r["categoria_id"], 0) + r["total"]
        return {k: round(v, 2) for k, v in gasto.items()}

    @staticmethod
    def _validar(nome, cor, orcamento):
        n = str(nome or "").strip()
        if not n:
            raise ValueError("Informe o nome da categoria.")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(cor or "")):
            raise ValueError("Escolha uma cor para a categoria.")
        o = dinheiro(orcamento) if str(orcamento or "").strip() not in ("", "0") else 0.0
        if o < 0:
            raise ValueError("O orçamento não pode ser negativo.")
        return n, cor.upper(), o


class Rendas:
    """Renda do mês (quanto você recebe no total), usada para medir o quanto o cartão consome."""

    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    def obter(self, mes=None):
        linhas = self.banco.consultar("SELECT valor FROM rendas WHERE mes = ?",
                                      (self.meses.interpretar(mes),))
        return linhas[0]["valor"] if linhas else None

    def definir(self, valor, mes=None) -> bool:
        m = self.meses.interpretar(mes)
        self.meses.exigir(m)
        self.banco.gravar(
            "INSERT INTO rendas (mes, valor) VALUES (?,?) "
            "ON CONFLICT(mes) DO UPDATE SET valor = excluded.valor", (m, dinheiro(valor)))
        return True
