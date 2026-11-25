"""Quem está conectado agora. A interface e o servidor do Claude usam estas duas funções.

Quando o usuário muda (login, troca ou saída), a próxima chamada já usa os dados certos.
"""
from contextvars import ContextVar

from controle_financeiro.seguranca.autenticacao import Autenticacao
from controle_financeiro.nucleo.servico import Financas

_auth = None
_cache = {"usuario": None, "app": None}

# Na versão na internet (servidor MCP em /api/mcp), cada requisição traz o próprio usuário:
# a Financas dela fica aqui enquanto a ferramenta roda. Fora disso (o servidor no PC) vale o login guardado.
_remoto = ContextVar("financas_remoto", default=None)


def usar_financas_remoto(financas: Financas):
    """Define a Financas da requisição atual. Devolve a ficha para desfazer com desfazer_financas_remoto."""
    return _remoto.set(financas)


def desfazer_financas_remoto(ficha) -> None:
    _remoto.reset(ficha)


def auth() -> Autenticacao:
    """Login, cadastro de usuários e sessão."""
    global _auth
    if _auth is None:
        _auth = Autenticacao()
    return _auth


def fin() -> Financas:
    """Regras e dados do usuário conectado."""
    remoto = _remoto.get()
    if remoto is not None:
        return remoto
    usuario = auth().usuario_servico()  # app já logado, ou sessão guardada para o Claude
    if not usuario:
        raise RuntimeError("Nenhum usuário conectado. Abra o app Controle Financeiro e faça login.")
    if _cache["usuario"] != usuario:
        _cache["app"] = Financas.do_usuario(usuario, auth().cliente)
        _cache["usuario"] = usuario
    return _cache["app"]
