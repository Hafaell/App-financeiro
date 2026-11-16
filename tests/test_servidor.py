"""Ferramentas do servidor MCP (as que a Ayla usa), com o banco SQLite dos testes."""
import pytest

from controle_financeiro.dados.banco import criar_banco
from controle_financeiro.nucleo.servico import Financas

servidor = pytest.importorskip("controle_financeiro.servidor_claude.servidor")


@pytest.fixture
def app(monkeypatch, tmp_path):
    a = Financas(criar_banco("teste"), pasta_backups=tmp_path)
    monkeypatch.setattr(servidor, "fin", lambda: a)
    return a


def test_editar_compra_pela_ayla_muda_so_os_campos_informados(app):
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Mercado", "R$ 100,00", parcelas="", pessoa=".")
    r = servidor.editar_compra(id_, valor_parcela="R$ 95,40", categoria="Lazer")
    assert r["ok"] and r["compra"]["id"] == id_
    assert r["compra"]["valor_parcela"] == 95.4 and r["compra"]["item"] == "Mercado"
    lazer = next(c["id"] for c in app.listar_categorias() if c["nome"] == "Lazer")
    assert app.obter_compra(id_)["categoria_id"] == lazer


def test_editar_compra_pela_ayla_avisa_categoria_errada_e_nada_para_mudar(app):
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Uber", "R$ 20,00", parcelas="", pessoa=".")
    assert servidor.editar_compra(id_, categoria="Não existe")["ok"] is False
    assert servidor.editar_compra(id_)["ok"] is False
    assert app.obter_compra(id_)["valor_parcela"] == 20.0


def test_virar_mes_pela_ayla_devolve_a_copia(app, tmp_path):
    r = servidor.virar_mes()
    assert r["backup"].startswith(str(tmp_path))
