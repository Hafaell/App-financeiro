"""Regras do app com banco SQLite local (mesmas regras do Supabase)."""
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.dados.banco import criar_banco


def _app():
    return Financas(criar_banco("teste"))


def test_compra_propria_entra_no_meu_cartao():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    app.lancar_compra(cartao, "Mercado", "R$ 100,00", parcelas="", pessoa=".")
    resumo = app.resumo_mes()
    assert resumo["meu_cartao_total"] >= 100.0


def test_compra_com_pessoa_vira_emprestimo_e_nao_entra_no_meu_cartao():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    antes = app.resumo_mes()
    app.lancar_compra(cartao, "Presente", "R$ 50,00", parcelas="", pessoa="Pai")
    depois = app.resumo_mes()
    assert depois["meu_cartao_total"] == antes["meu_cartao_total"]
    assert depois["cartoes_com_emprestimos_total"] >= antes["cartoes_com_emprestimos_total"] + 50.0


def test_lancamentos_guardam_a_data_do_dia_e_a_virada_mantem():
    from datetime import date
    app = _app()
    hoje = date.today().isoformat()
    cartao = app.listar_cartoes()[0]["nome"]
    cid = app.lancar_compra(cartao, "Cinema", "R$ 40,00", parcelas="1/3", pessoa=".")
    rid = app.adicionar_lancamento("receitas", "Salário teste", "R$ 100,00")
    did = app.adicionar_lancamento("despesas", "Luz teste", "R$ 50,00", recorrente=True)
    assert app.obter_compra(cid)["data_lancamento"] == hoje
    assert app.obter_lancamento("receitas", rid)["data_lancamento"] == hoje
    assert app.obter_lancamento("despesas", did)["data_lancamento"] == hoje
    app.virar_mes()
    novas = [c for c in app.listar_compras() if c["item"] == "Cinema"]
    assert novas and novas[0]["data_lancamento"] == hoje


def test_classificar_troca_so_a_categoria_sem_recriar():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Mercado", "R$ 100,00", parcelas="", pessoa=".")
    cat = app.listar_categorias()[0]["id"]
    assert app.classificar("compras", id_, cat)
    compra = app.obter_compra(id_)
    assert compra["id"] == id_ and compra["categoria_id"] == cat and compra["item"] == "Mercado"
    app.classificar("compras", id_, None)
    assert app.obter_compra(id_)["categoria_id"] is None
