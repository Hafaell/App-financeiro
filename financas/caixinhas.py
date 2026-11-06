"""Caixinhas de dinheiro (dono + nome + valor). Não pertencem a nenhum mês."""
from .utilidades import dinheiro


class Caixinhas:
    def __init__(self, banco):
        self.banco = banco

    def listar(self):
        return self.banco.consultar("SELECT * FROM caixinhas ORDER BY dono, nome")

    def obter(self, id_):
        linhas = self.banco.consultar("SELECT * FROM caixinhas WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def definir(self, dono, nome, valor) -> bool:
        """Cria a caixinha ou atualiza o valor de uma existente com o mesmo dono e nome."""
        d, n = self._nomes(dono, nome)
        self.banco.gravar(
            "INSERT INTO caixinhas (dono, nome, valor) VALUES (?,?,?) "
            "ON CONFLICT(dono, nome) DO UPDATE SET valor = excluded.valor",
            (d, n, dinheiro(valor)))
        return True

    def atualizar(self, id_, dono, nome, valor) -> bool:
        d, n = self._nomes(dono, nome)
        try:
            _, linhas = self.banco.gravar(
                "UPDATE caixinhas SET dono = ?, nome = ?, valor = ? WHERE id = ?",
                (d, n, dinheiro(valor), int(id_)))
        except Exception as erro:  # nome repetido para o mesmo dono
            if "UNIQUE" in str(erro).upper() or "duplicate key" in str(erro):
                raise ValueError(f"Já existe uma caixinha de {d} com o nome {n}.") from erro
            raise
        if linhas == 0:
            raise ValueError("Caixinha não encontrada.")
        return True

    @staticmethod
    def _nomes(dono, nome):
        d = str(dono or "").strip()
        n = str(nome or "").strip()
        if not d or not n:
            raise ValueError("Informe o dono e o nome da caixinha.")
        return d, n
