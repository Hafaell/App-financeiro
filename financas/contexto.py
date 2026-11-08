"""Quem está conectado agora. A interface e o servidor do Claude usam estas duas funções.

Quando o usuário muda (login, troca ou saída), a próxima chamada já usa os dados certos.
"""
from .seguranca import Autenticacao
from .servico import Financas

_auth = None
_cache = {"usuario": None, "financas": None}


def auth() -> Autenticacao:
    """Login, cadastro de usuários e sessão."""
    global _auth
    if _auth is None:
        _auth = Autenticacao()
    return _auth


def fin() -> Financas:
    """Regras e dados do usuário conectado."""
    usuario = auth().usuario_servico()  # app já logado, ou sessão guardada para o Claude
    if not usuario:
        raise RuntimeError("Nenhum usuário conectado. Abra o app Controle Financeiro e faça login.")
    if _cache["usuario"] != usuario:
        _cache["financas"] = Financas.do_usuario(usuario, auth().cliente)
        _cache["usuario"] = usuario
    return _cache["financas"]
