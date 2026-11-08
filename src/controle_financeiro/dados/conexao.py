"""Conexão com o Supabase, guardada criptografada neste computador.

Guarda: o token de acesso pessoal (para listar os projetos), o projeto escolhido,
e a URL e a chave pública desse projeto. A senha do banco nunca é usada.
O token só serve para listar projetos e chaves: não substitui o login do usuário.
"""
import requests

from controle_financeiro.config import CONEXAO_PATH
from controle_financeiro.dados.nuvem import ErroConexao
from controle_financeiro.seguranca.cofre import Cofre

API = "https://api.supabase.com/v1"
TEMPO_LIMITE = 10


class ErroProjeto(RuntimeError):
    """O token foi recusado, ou o projeto não tem a chave pública."""


def ler_conexao() -> dict:
    if not CONEXAO_PATH.exists():
        return {}
    return Cofre().decifrar(CONEXAO_PATH.read_bytes())


def salvar_conexao(dados: dict):
    CONEXAO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONEXAO_PATH.write_bytes(Cofre().cifrar(dados))


def conexao_configurada() -> bool:
    dados = ler_conexao()
    return bool(dados.get("url") and dados.get("chave"))


def _api(token: str, caminho: str):
    try:
        resp = requests.get(API + caminho, headers={"Authorization": f"Bearer {token}"},
                            timeout=TEMPO_LIMITE)
    except requests.RequestException as e:
        raise ErroConexao("Não consegui falar com o Supabase. Verifique a internet.") from e
    if resp.status_code in (401, 403):
        raise ErroProjeto("Token inválido ou sem permissão. Crie um novo token no Supabase "
                          "(Account > Access Tokens).")
    if resp.status_code >= 400:
        raise ErroProjeto(f"O Supabase recusou o pedido (código {resp.status_code}).")
    return resp.json()


def listar_projetos(token: str) -> list:
    """[{'ref': ..., 'nome': ...}] ordenado pelo nome."""
    dados = _api(token, "/projects")
    projetos = [{"ref": p["id"], "nome": p.get("name") or p["id"]} for p in dados]
    return sorted(projetos, key=lambda p: p["nome"].lower())


def credenciais_projeto(token: str, ref: str) -> tuple:
    """(URL, chave pública) do projeto. Nunca devolve a chave secreta."""
    chaves = _api(token, f"/projects/{ref}/api-keys?reveal=true")
    escolhida = (next((k for k in chaves if k.get("type") == "publishable"), None)
                 or next((k for k in chaves if k.get("name") == "anon"), None))
    if not escolhida or not escolhida.get("api_key"):
        raise ErroProjeto("Não encontrei a chave pública deste projeto.")
    return f"https://{ref}.supabase.co", escolhida["api_key"]
