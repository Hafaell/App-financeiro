"""Caixinhas de dinheiro (dono + nome + valor), com meta opcional e data para alcançá-la.
Não pertencem a nenhum mês. Cada mudança no valor fica no histórico (movimentos_caixinha),
quando a tabela existe no banco."""
from datetime import date

from controle_financeiro.nucleo.utilidades import dinheiro, interpretar_mes_simples, meses_entre

HISTORICO = "movimentos_caixinha"


class Caixinhas:
    def __init__(self, banco, meses):
        self.banco = banco
        self.meses = meses

    def listar(self):
        return self.banco.consultar("SELECT * FROM caixinhas ORDER BY dono, nome")

    def obter(self, id_):
        linhas = self.banco.consultar("SELECT * FROM caixinhas WHERE id = ?", (int(id_),))
        return linhas[0] if linhas else None

    def tem_historico(self) -> bool:
        """False enquanto o script 07 não foi rodado no Supabase."""
        return self.banco.disponivel(HISTORICO)

    def _anotar(self, con, caixinha_id, valor, saldo, descricao):
        if self.tem_historico() and round(valor, 2) != 0:
            con.execute(f"INSERT INTO {HISTORICO} (caixinha_id, data, valor, saldo, descricao) "
                        "VALUES (?,?,?,?,?)",
                        (int(caixinha_id), date.today().isoformat(), round(valor, 2), round(saldo, 2),
                         str(descricao or "").strip()))

    def _por_nome(self, dono, nome):
        linhas = self.banco.consultar("SELECT * FROM caixinhas WHERE dono = ? AND nome = ?", (dono, nome))
        return linhas[0] if linhas else None

    def definir(self, dono, nome, valor) -> bool:
        """Cria a caixinha ou atualiza o valor de uma existente com o mesmo dono e nome.
        A diferença para o valor anterior vai para o histórico."""
        d, n = self._nomes(dono, nome)
        novo = dinheiro(valor)
        antes = self._por_nome(d, n)
        if antes:
            with self.banco.transacao() as con:
                con.execute("UPDATE caixinhas SET valor = ? WHERE id = ?", (novo, antes["id"]))
                self._anotar(con, antes["id"], novo - antes["valor"], novo, "Ajuste do valor")
            return True
        # Caixinha nova: em dois passos, porque no Supabase o id só existe depois de gravar
        # (dentro de uma transação, o id da cópia local pode não ser o do servidor).
        id_, _ = self.banco.gravar("INSERT INTO caixinhas (dono, nome, valor) VALUES (?,?,?)", (d, n, novo))
        if id_ is not None and self.tem_historico() and novo:
            self.banco.gravar(f"INSERT INTO {HISTORICO} (caixinha_id, data, valor, saldo, descricao) "
                              "VALUES (?,?,?,?,?)", (int(id_), date.today().isoformat(), novo, novo,
                                                     "Valor inicial"))
        return True

    def movimentar(self, id_, valor, descricao="", retirar=False) -> dict:
        """Guarda (ou retira, com retirar=True) um valor na caixinha e anota no histórico.
        Devolve a caixinha como ficou."""
        quanto = dinheiro(valor)
        if quanto <= 0:
            raise ValueError("Informe um valor maior que zero.")
        c = self.obter(id_)
        if not c:
            raise ValueError("Caixinha não encontrada.")
        if retirar and quanto > c["valor"] + 0.001:
            raise ValueError(f"A caixinha {c['nome']} só tem {c['valor']:.2f}".replace(".", ",")
                             + ": não dá para retirar mais que isso.")
        delta = -quanto if retirar else quanto
        saldo = round(c["valor"] + delta, 2)
        padrao = "Retirada" if retirar else "Guardado"
        with self.banco.transacao() as con:
            con.execute("UPDATE caixinhas SET valor = ? WHERE id = ?", (saldo, int(id_)))
            self._anotar(con, id_, delta, saldo, descricao or padrao)
        return self.obter(id_)

    def historico(self, id_) -> list:
        """Movimentos da caixinha, do mais novo para o mais antigo (vazio sem a tabela)."""
        if not self.tem_historico():
            return []
        return self.banco.consultar(f"SELECT * FROM {HISTORICO} WHERE caixinha_id = ? "
                                    "ORDER BY data DESC, id DESC", (int(id_),))

    def atualizar(self, id_, dono, nome, valor, meta=None, data_alvo=None) -> bool:
        d, n = self._nomes(dono, nome)
        m, dt = self._meta(meta, data_alvo)
        novo = dinheiro(valor)
        antes = self.obter(id_)
        if not antes:
            raise ValueError("Caixinha não encontrada.")
        try:
            with self.banco.transacao() as con:
                con.execute(
                    "UPDATE caixinhas SET dono = ?, nome = ?, valor = ?, meta = ?, data_alvo = ? WHERE id = ?",
                    (d, n, novo, m, dt, int(id_)))
                self._anotar(con, id_, novo - antes["valor"], novo, "Ajuste do valor")
        except Exception as erro:  # nome repetido para o mesmo dono
            if "UNIQUE" in str(erro).upper() or "duplicate key" in str(erro):
                raise ValueError(f"Já existe uma caixinha de {d} com o nome {n}.") from erro
            raise
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
