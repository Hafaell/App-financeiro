"""Desempenho: poucas chamadas de rede, nenhuma delas dentro das leituras da interface.
Usa um servidor falso (SQLite em memória) que conta as chamadas; nada vai ao Supabase."""
import sqlite3

import pytest

from controle_financeiro.dados.banco import BancoPostgres
from controle_financeiro.dados.esquema import comandos
from controle_financeiro.dados.nuvem import ClienteSupabase, ErroBanco
from controle_financeiro.nucleo.servico import Financas


class ServidorFalso:
    """Faz o papel do Supabase: executar_sql e executar_lote, contando as chamadas."""
    logado = True

    def __init__(self, sem_tabela=None):
        self.con = sqlite3.connect(":memory:", check_same_thread=False)
        self.con.row_factory = sqlite3.Row
        for c in comandos("sqlite"):
            self.con.execute(c)
        self.con.execute("INSERT OR IGNORE INTO meta (chave, valor) VALUES ('versao', 0)")
        self.con.execute("INSERT OR IGNORE INTO sessoes (mes) VALUES ('2026-11')")
        self.con.execute("INSERT INTO cartoes (nome, cor, cor_texto) VALUES ('Inter', '#000', '#fff')")
        self.con.commit()
        self.chamadas = 0
        self.sem_tabela = sem_tabela

    def _um(self, sql, params):
        if self.sem_tabela and self.sem_tabela in sql:
            raise ErroBanco(f'relation "{self.sem_tabela}" does not exist')
        sql = sql.replace("%s", "?").replace(" RETURNING id", "")
        cur = self.con.execute(sql, params)
        if sql.lstrip().upper().startswith("SELECT"):
            return {"linhas": [dict(r) for r in cur.fetchall()]}
        if not sql.upper().startswith("INSERT INTO SESSOES"):
            self.con.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
        self.con.commit()
        return {"id": cur.lastrowid, "afetadas": cur.rowcount}

    def mudar_por_fora(self):
        """Como se outro aparelho (ou a Ayla) tivesse gravado."""
        self.con.execute("INSERT INTO compras (mes, cartao, item, parcelas, valor_parcela, emprestimo, pessoa) "
                         "VALUES ('2026-11', 'Inter', 'Por fora', '1/1', 5, 0, '.')")
        self.con.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
        self.con.commit()

    def preparar(self):
        self.chamadas += 1

    def executar(self, sql, params=()):
        self.chamadas += 1
        return self._um(sql, list(params))

    def executar_lote(self, comandos_):
        self.chamadas += 1
        return [self._um(s, list(p)) for s, p in comandos_]


@pytest.fixture
def servidor():
    return ServidorFalso()


@pytest.fixture
def banco(servidor, tmp_path):
    return BancoPostgres(servidor, tmp_path / "fila.dat", tmp_path / "cache.dat")


def test_cliente_reaproveita_a_conexao(monkeypatch):
    cliente = ClienteSupabase("http://exemplo.invalido", "chave", prefixo_api="")
    cliente.usar_token("token")
    enviados = []

    class Resposta:
        status_code = 200
        content = b'{"linhas": []}'

        def json(self):
            return {"linhas": []}

    def falso(metodo, url, **kw):
        enviados.append(url)
        return Resposta()

    monkeypatch.setattr(cliente._sessao, "request", falso)
    cliente.executar("SELECT 1")
    cliente.executar("SELECT 2")
    assert len(enviados) == 2  # as duas passaram pela mesma Session (conexão reaproveitada)


def test_sincronizar_tudo_e_uma_chamada_so(banco, servidor):
    banco.consultar("SELECT 1")  # abre: preparar + sincronizar
    servidor.chamadas = 0
    banco._sincronizar()
    assert servidor.chamadas == 1


def test_gravar_online_usa_duas_chamadas(banco, servidor):
    app = Financas(banco)
    app.meses.sessoes()  # abre a cópia
    servidor.chamadas = 0
    app.lancar_compra("Inter", "Mouse", "50,00")
    assert servidor.chamadas == 2  # a gravação e uma sincronização em lote
    assert [c["item"] for c in app.listar_compras()] == ["Mouse"]


def test_sincronizacao_em_lote_sem_tabela_opcional_cai_para_uma_por_vez(tmp_path):
    servidor = ServidorFalso(sem_tabela="movimentos_caixinha")
    banco = BancoPostgres(servidor, tmp_path / "f.dat", tmp_path / "c.dat")
    assert Financas(banco).listar_cartoes()  # abriu normalmente
    assert not banco.disponivel("movimentos_caixinha")


def test_leitura_da_interface_nao_usa_a_rede(banco, servidor):
    banco.consultar("SELECT 1")
    banco.verificar_nas_consultas = False
    banco._ultima_verificacao = 0.0  # já passou muito tempo desde a última checagem
    servidor.chamadas = 0
    for _ in range(20):
        banco.consultar("SELECT * FROM compras")
        banco.versao()
        banco.estado()
    assert servidor.chamadas == 0


def test_leitura_comum_ainda_confere_o_supabase(banco, servidor):
    """O servidor do Claude e os testes seguem conferindo antes de ler."""
    banco.consultar("SELECT 1")
    servidor.mudar_por_fora()
    banco._ultima_verificacao = 0.0
    assert [c["item"] for c in banco.consultar("SELECT item FROM compras")] == ["Por fora"]
