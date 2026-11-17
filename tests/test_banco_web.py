"""BancoWeb (versão web): sem disco, sem modo offline e poucas chamadas por requisição."""
import pytest

from controle_financeiro.dados import banco_web
from controle_financeiro.dados.banco_web import BancoWeb
from controle_financeiro.dados.nuvem import ErroConexao, SessaoExpirada
from controle_financeiro.nucleo.servico import Financas
from test_desempenho import ServidorFalso


@pytest.fixture(autouse=True)
def _limpar_preparados():
    banco_web._preparados.clear()


def test_abrir_custa_tres_chamadas_e_depois_uma_so(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)  # nada pode ser gravado em disco
    servidor = ServidorFalso()
    app = Financas(BancoWeb(servidor, usuario_id="u1"))
    assert app.listar_cartoes()
    assert servidor.chamadas == 3  # preparar, abrir o mês e baixar tudo em lote
    # Outra requisição do mesmo usuário (função quente): não prepara de novo
    servidor.chamadas = 0
    assert Financas(BancoWeb(servidor, usuario_id="u1")).listar_cartoes()
    assert servidor.chamadas == 1
    assert list(tmp_path.iterdir()) == []


def test_gravar_vai_direto_ao_servidor(tmp_path):
    servidor = ServidorFalso()
    app = Financas(BancoWeb(servidor, usuario_id="u2"))
    app.lancar_compra("Inter", "Mouse", "50,00")
    linhas = servidor.con.execute("SELECT item FROM compras").fetchall()
    assert [l["item"] for l in linhas] == ["Mouse"]
    assert [c["item"] for c in app.listar_compras()] == ["Mouse"]


class _ServidorQueCai(ServidorFalso):
    def __init__(self, erro):
        super().__init__()
        self.erro = erro
        self.cair = False

    def executar(self, sql, params=()):
        if self.cair:
            raise self.erro("fora do ar")
        return super().executar(sql, params)

    def executar_lote(self, comandos_):
        if self.cair:
            raise self.erro("fora do ar")
        return super().executar_lote(comandos_)


@pytest.mark.parametrize("erro", [ErroConexao, SessaoExpirada])
def test_sem_conexao_a_gravacao_falha_em_vez_de_ir_para_a_fila(erro):
    servidor = _ServidorQueCai(erro)
    app = Financas(BancoWeb(servidor, usuario_id="u3"))
    app.listar_cartoes()
    servidor.cair = True
    with pytest.raises(erro):
        app.lancar_compra("Inter", "Mouse", "50,00")
    with pytest.raises(erro):  # transação (várias alterações juntas)
        app.definir_caixinha("Eu", "Viagem", "100")
        app.guardar_na_caixinha(1, "10")
    assert app.banco._fila == []


def test_sem_conexao_ao_abrir_o_erro_aparece():
    servidor = _ServidorQueCai(ErroConexao)
    servidor.cair = True
    with pytest.raises(ErroConexao):
        Financas(BancoWeb(servidor, usuario_id="u4")).listar_cartoes()


def test_versao_remota_nao_baixa_a_copia():
    servidor = ServidorFalso()
    banco = BancoWeb(servidor, usuario_id="u5")
    assert banco.versao_remota() == 0
    assert servidor.chamadas == 1
    assert banco._local is None
