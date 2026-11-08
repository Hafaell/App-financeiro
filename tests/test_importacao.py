from controle_financeiro.nucleo.importacao import ler_csv

EXTRATO_NUBANK = (
    "date,title,amount\n"
    "2026-11-05,Mercado Central,-120.50\n"
    "2026-11-10,Celular Novo Parcela 2/5,-300.00\n"
)


def test_csv_do_nubank_le_as_linhas():
    itens = ler_csv(EXTRATO_NUBANK)
    assert len(itens) == 2
    assert itens[0]["descricao"] == "Mercado Central"


def test_parcela_sai_do_nome():
    itens = ler_csv(EXTRATO_NUBANK)
    assert itens[1]["parcelas"] == "2/5"
    assert "2/5" not in itens[1]["descricao"]
