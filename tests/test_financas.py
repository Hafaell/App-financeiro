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
