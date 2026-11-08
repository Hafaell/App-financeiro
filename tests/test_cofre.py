from controle_financeiro.seguranca.cofre import Cofre


def test_cifrar_e_decifrar_volta_o_mesmo_dado(tmp_path):
    cofre = Cofre(tmp_path / "chave.key")
    dados = {"usuario": "rafael@exemplo.com", "refresh": "token-secreto"}
    assert cofre.decifrar(cofre.cifrar(dados)) == dados


def test_texto_cifrado_nao_mostra_o_conteudo(tmp_path):
    cofre = Cofre(tmp_path / "chave.key")
    cifrado = cofre.cifrar({"refresh": "token-secreto"})
    assert b"token-secreto" not in cifrado
