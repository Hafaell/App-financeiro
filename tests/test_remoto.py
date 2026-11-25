"""Servidor MCP pela internet (/api/mcp): autenticação e uma ferramenta chamada pelo protocolo,
com SQLite temporário no lugar do Supabase."""
import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from controle_financeiro.dados.banco import BancoSqlite
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.servidor_claude.remoto import CAMINHO_METADADOS, registrar_mcp

CABECALHOS = {"Accept": "application/json, text/event-stream", "Content-Type": "application/json"}


@pytest.fixture
def cliente(tmp_path):
    banco = BancoSqlite(tmp_path / "remoto.db")
    financas = Financas(banco, pasta_backups=tmp_path)
    usados = []

    def criar(token):
        usados.append(token)
        return financas

    site = FastAPI()
    registrar_mcp(site, criar, lambda token: token == "token-bom")
    cli = TestClient(site, follow_redirects=False)
    cli.usados = usados
    return cli


def _rpc(cliente, metodo, params=None, token="token-bom", req_id=1):
    corpo = {"jsonrpc": "2.0", "id": req_id, "method": metodo, "params": params or {}}
    cab = dict(CABECALHOS)
    if token is not None:
        cab["Authorization"] = f"Bearer {token}"
    return cliente.post("/api/mcp", content=json.dumps(corpo), headers=cab)


def test_sem_token_responde_401_com_aviso_de_oauth(cliente):
    resp = _rpc(cliente, "tools/list", token=None)
    assert resp.status_code == 401
    aviso = resp.headers["www-authenticate"]
    assert aviso.startswith("Bearer resource_metadata=")
    assert CAMINHO_METADADOS in aviso
    assert resp.json()["erro"] == "Entre com seu e-mail e senha."


def test_token_invalido_responde_401(cliente):
    assert _rpc(cliente, "tools/list", token="token-errado").status_code == 401


def test_ferramenta_usa_a_financas_do_token(cliente):
    resp = _rpc(cliente, "tools/call", {"name": "listar_cartoes", "arguments": {}})
    assert resp.status_code == 200
    texto = "".join(b["text"] for b in resp.json()["result"]["content"])
    assert "Inter" in texto and "Nubank" in texto
    assert cliente.usados == ["token-bom"]


def test_lista_as_ferramentas_do_mesmo_servidor(cliente):
    resp = _rpc(cliente, "tools/list")
    nomes = {t["name"] for t in resp.json()["result"]["tools"]}
    assert {"listar_cartoes", "lancar_compra", "resumo_mes", "virar_mes"} <= nomes


def test_metadados_apontam_o_login_para_o_supabase(monkeypatch):
    from controle_financeiro.web import api
    monkeypatch.setenv("SUPABASE_URL", "https://abc.supabase.co")
    monkeypatch.setenv("SUPABASE_CHAVE", "chave-publica")
    cli = TestClient(api.app)
    for caminho in ("/.well-known/oauth-protected-resource", "/.well-known/oauth-protected-resource/api/mcp"):
        dados = cli.get(caminho, headers={"host": "meu-site.vercel.app"}).json()
        assert dados["resource"] == "https://meu-site.vercel.app/api/mcp"
        assert dados["authorization_servers"] == ["https://abc.supabase.co/auth/v1"]


def test_endpoint_montado_no_site_exige_login(monkeypatch):
    from controle_financeiro.web import api
    resp = TestClient(api.app, follow_redirects=False).post("/api/mcp", json={}, headers=CABECALHOS)
    assert resp.status_code == 401  # e não 307: o endereço sem barra final é o que o Claude chama
    assert "resource_metadata" in resp.headers["www-authenticate"]
