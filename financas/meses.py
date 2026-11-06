"""Meses abertos. O mês atual é o mais recente aberto."""
from .utilidades import interpretar_mes, nome_mes


class Meses:
    def __init__(self, banco):
        self.banco = banco

    def sessoes(self):
        return [r["mes"] for r in self.banco.consultar("SELECT mes FROM sessoes ORDER BY mes")]

    def ativo(self) -> str:
        return self.sessoes()[-1]

    def interpretar(self, texto=None) -> str:
        """Vazio = mês atual."""
        if not texto or not str(texto).strip():
            return self.ativo()
        return interpretar_mes(texto)

    def exigir(self, codigo):
        if codigo not in self.sessoes():
            raise ValueError(f"{nome_mes(codigo)} ainda não foi aberto. "
                             "Use a virada de mês para abri-lo.")

    def apagar(self, codigo) -> bool:
        """Apaga um mês antigo com todos os seus lançamentos. O mês atual não pode ser apagado."""
        if codigo == self.ativo():
            raise ValueError("Não é possível apagar o mês atual.")
        if codigo not in self.sessoes():
            raise ValueError("Esse mês não está aberto.")
        with self.banco.transacao() as con:
            for tabela in ("compras", "receitas", "despesas", "pagamentos"):
                con.execute(f"DELETE FROM {tabela} WHERE mes = ?", (codigo,))
            con.execute("DELETE FROM sessoes WHERE mes = ?", (codigo,))
        return True
