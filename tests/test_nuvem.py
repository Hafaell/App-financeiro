import pytest

from controle_financeiro.dados.nuvem import ClienteSupabase, ErroConexao, _json_params


def test_parametros_viram_tipos_aceitos_pelo_json():
    assert _json_params([1, 2.5, "texto", None]) == [1, 2.5, "texto", None]


def test_sem_internet_levanta_erro_de_conexao():
    cliente = ClienteSupabase("http://127.0.0.1:1", "chave", prefixo_api="")
    cliente.usar_token("token")
    with pytest.raises(ErroConexao):
        cliente.executar("SELECT 1", [])


def test_sem_login_nao_envia_nada():
    from controle_financeiro.dados.nuvem import SessaoExpirada
    cliente = ClienteSupabase("http://127.0.0.1:1", "chave", prefixo_api="")
    with pytest.raises(SessaoExpirada):
        cliente.executar("SELECT 1", [])
