"""URL e chave pública do Supabase, guardadas criptografadas neste computador."""
from controle_financeiro.config import CONEXAO_PATH
from controle_financeiro.seguranca.cofre import Cofre


def ler_conexao() -> dict:
    if not CONEXAO_PATH.exists():
        return {}
    return Cofre().decifrar(CONEXAO_PATH.read_bytes())


def salvar_conexao(dados: dict):
    CONEXAO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONEXAO_PATH.write_bytes(Cofre().cifrar(dados))
