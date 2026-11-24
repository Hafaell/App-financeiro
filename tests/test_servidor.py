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


def test_editar_pagamento_pela_ayla(app):
    id_ = app.registrar_pagamento("Pai", "R$ 500,00", "pix")
    assert [p["id"] for p in servidor.listar_pagamentos("Pai")] == [id_]
    r = servidor.editar_pagamento(id_, valor="R$ 50,00")
    assert r["ok"] and r["pagamento"]["valor"] == 50 and r["pagamento"]["descricao"] == "pix"
    assert servidor.editar_pagamento(id_)["ok"] is False


def test_virar_mes_pela_ayla_devolve_a_copia(app, tmp_path):
    r = servidor.virar_mes()
    assert r["backup"].startswith(str(tmp_path))


def test_editar_lancamento_pela_ayla(app):
    id_ = app.adicionar_lancamento("despesas", "Luz", "R$ 120,00", recorrente=True)
    antes = app.obter_lancamento("despesas", id_)
    r = servidor.editar_lancamento("despesas", id_, valor="R$ 135,10", categoria="Outros")
    assert r["ok"] and r["lancamento"]["valor"] == 135.1
    depois = app.obter_lancamento("despesas", id_)
    assert depois["descricao"] == "Luz" and depois["recorrente"] == 1
    assert depois["data_lancamento"] == antes["data_lancamento"] and depois["mes"] == antes["mes"]


def test_editar_receita_pela_ayla_nao_aceita_categoria(app):
    id_ = app.adicionar_lancamento("receitas", "Freela", "R$ 300,00")
    assert servidor.editar_lancamento("receitas", id_, descricao="Freela site")["ok"]
    assert app.obter_lancamento("receitas", id_)["descricao"] == "Freela site"
    with pytest.raises(ValueError):
        servidor.editar_lancamento("receitas", id_, categoria="Lazer")


def test_buscar_pela_ayla_soma_os_resultados(app):
    cartao = app.listar_cartoes()[0]["nome"]
    app.lancar_compra(cartao, "Uber busca-ayla", "R$ 20,00", parcelas="", pessoa=".")
    app.adicionar_lancamento("despesas", "uber busca-ayla trabalho", "R$ 15,50")
    r = servidor.buscar("BUSCA-AYLA")
    assert r["quantidade"] == 2 and r["total"] == 35.5


def test_caixinhas_pela_ayla(app):
    import uuid
    nome = f"Carro {uuid.uuid4().hex[:6]}"
    app.definir_caixinha("Rafael", nome, "R$ 500,00")
    assert servidor.guardar_na_caixinha("rafael", nome.lower(), "R$ 100,00")["caixinha"]["valor"] == 600.0
    assert servidor.retirar_da_caixinha("Rafael", nome, "R$ 40,00", "IPVA")["caixinha"]["valor"] == 560.0
    movimentos = servidor.historico_caixinha("Rafael", nome)["movimentos"]
    assert [m["descricao"] for m in movimentos] == ["IPVA", "Guardado", "Valor inicial"]
    assert servidor.guardar_na_caixinha("Rafael", "Não existe", "R$ 1,00")["ok"] is False


def test_previsao_pela_ayla(app):
    r = servidor.previsao_proximo_mes()
    assert set(r) >= {"mes", "receitas", "despesas", "meu_cartao", "emprestimos", "saldo"}
