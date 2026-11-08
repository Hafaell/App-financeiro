"""Caixinhas de dinheiro (dono + nome + valor), com meta opcional e data para alcançá-la.
Não pertencem a nenhum mês."""
from controle_financeiro.nucleo.utilidades import dinheiro, interpretar_mes_simples, meses_entre


class Caixinhas:
    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

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

    def atualizar(self, id_, dono, nome, valor, meta=None, data_alvo=None) -> bool:
        d, n = self._nomes(dono, nome)
        m, dt = self._meta(meta, data_alvo)
        try:
            _, linhas = self.banco.gravar(
                "UPDATE caixinhas SET dono = ?, nome = ?, valor = ?, meta = ?, data_alvo = ? WHERE id = ?",
                (d, n, dinheiro(valor), m, dt, int(id_)))
        except Exception as erro:  # nome repetido para o mesmo dono
            if "UNIQUE" in str(erro).upper() or "duplicate key" in str(erro):
                raise ValueError(f"Já existe uma caixinha de {d} com o nome {n}.") from erro
            raise
        if linhas == 0:
            raise ValueError("Caixinha não encontrada.")
        return True

    def andamento(self) -> list:
        """Para cada caixinha com meta: quanto falta e quanto guardar por mês até a data alvo."""
        hoje = self.meses.ativo()
        saida = []
        for c in self.listar():
            item = dict(c, progresso=None, falta=None, meses_restantes=None, por_mes=None)
            if c["meta"]:
                item["progresso"] = min(round(c["valor"] / c["meta"] * 100, 1), 100.0)
                item["falta"] = round(max(c["meta"] - c["valor"], 0), 2)
                if c["data_alvo"]:
                    restantes = max(meses_entre(hoje, c["data_alvo"]), 1)
                    item["meses_restantes"] = restantes
                    item["por_mes"] = round(item["falta"] / restantes, 2)
            saida.append(item)
        return saida

    def definir_meta(self, id_, meta, data_alvo) -> bool:
        m, dt = self._meta(meta, data_alvo)
        _, linhas = self.banco.gravar("UPDATE caixinhas SET meta = ?, data_alvo = ? WHERE id = ?",
                                      (m, dt, int(id_)))
        if linhas == 0:
            raise ValueError("Caixinha não encontrada.")
        return True

    @staticmethod
    def _meta(meta, data_alvo):
        """Meta opcional em reais e data alvo opcional no formato AAAA-MM."""
        m = None if meta in (None, "", 0, "0") else dinheiro(meta)
        if m is not None and m <= 0:
            raise ValueError("A meta precisa ser maior que zero.")
        dt = str(data_alvo or "").strip() or None
        if dt:
            dt = interpretar_mes_simples(dt)
        return m, dt

    @staticmethod
    def _nomes(dono, nome):
        d = str(dono or "").strip()
        n = str(nome or "").strip()
        if not d or not n:
            raise ValueError("Informe o dono e o nome da caixinha.")
        return d, n
