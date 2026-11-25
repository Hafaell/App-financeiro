"""Servidor MCP pela internet (Streamable HTTP), para o Claude no celular e na web.

O Claude (que roda na nuvem da Anthropic) chama /api/mcp com o token de acesso do Supabase no
cabeçalho Authorization. Cada chamada:
  1. confere o token no Supabase (sem token válido: 401, com o aviso de OAuth no WWW-Authenticate);
  2. cria a Financas desse usuário (o mesmo caminho da API do site, sem disco);
  3. roda a ferramenta com essa Financas (contexto.fin() a devolve).
Não há sessão guardada nem estado entre chamadas, então funciona em serverless (Vercel).
"""
import json
from typing import Awaitable, Callable

import requests
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager

from controle_financeiro.dados.contexto import desfazer_financas_remoto, usar_financas_remoto
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.servidor_claude.servidor import mcp

CAMINHO_METADADOS = "/.well-known/oauth-protected-resource"


def validar_token_supabase(url: str, chave: str) -> Callable[[str], bool]:
    """Devolve uma função que diz se o token é de um usuário logado (pergunta ao próprio Supabase)."""
    def validar(token: str) -> bool:
        try:
            resp = requests.get(f"{url}/auth/v1/user", timeout=10,
                                headers={"apikey": chave, "Authorization": f"Bearer {token}"})
        except requests.RequestException:
            return False
        return resp.status_code == 200
    return validar


def criar_app_mcp(criar_financas: Callable[[str], Financas], validar_token: Callable[[str], bool]):
    """App ASGI do servidor MCP remoto. criar_financas(token) -> Financas do usuário do token."""

    async def chamar(scope, receive, send):
        if scope["type"] != "http":
            return
        cabecalhos = {k.decode("latin-1").lower(): v.decode("latin-1") for k, v in scope["headers"]}
        autorizacao = cabecalhos.get("authorization", "")
        token = autorizacao[7:].strip() if autorizacao.lower().startswith("bearer ") else ""
        if not token or not validar_token(token):
            host = cabecalhos.get("host", "")
            aviso = f'Bearer resource_metadata="https://{host}{CAMINHO_METADADOS}"'
            await _responder(send, 401, {"erro": "Entre com seu e-mail e senha."},
                             [(b"www-authenticate", aviso.encode("latin-1"))])
            return
        # Gerenciador novo a cada chamada: no modo sem estado ele só precisa de um run() ativo,
        # e isso não depende do lifespan do servidor (que o Vercel pode não executar).
        gerenciador = StreamableHTTPSessionManager(app=mcp._mcp_server, json_response=True, stateless=True)
        ficha = usar_financas_remoto(criar_financas(token))
        try:
            async with gerenciador.run():
                await gerenciador.handle_request(scope, receive, send)
        finally:
            desfazer_financas_remoto(ficha)

    return _AppAsgi(chamar)


class _AppAsgi:
    """Objeto ASGI: o Starlette trata uma função como handler de requisição, mas um objeto como app."""

    def __init__(self, chamar):
        self._chamar = chamar

    async def __call__(self, scope, receive, send):
        await self._chamar(scope, receive, send)


def registrar_mcp(site, criar_financas, validar_token, caminho: str = "/api/mcp") -> None:
    """Põe o servidor MCP em uma rota exata (Mount faria /api/mcp redirecionar para /api/mcp/)."""
    site.add_route(caminho, criar_app_mcp(criar_financas, validar_token), methods=["GET", "POST", "DELETE"])


async def _responder(send: Callable[..., Awaitable], status: int, corpo: dict, extras=()):
    dados = json.dumps(corpo, ensure_ascii=False).encode("utf-8")
    cabecalhos = [(b"content-type", b"application/json; charset=utf-8"), *extras]
    await send({"type": "http.response.start", "status": status, "headers": cabecalhos})
    await send({"type": "http.response.body", "body": dados})
