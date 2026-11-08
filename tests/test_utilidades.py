import pytest

from controle_financeiro.nucleo.utilidades import avancar_parcela, dinheiro


@pytest.mark.parametrize("entrada, esperado", [
    ("63,19", 63.19),
    ("R$ 1.234,56", 1234.56),
    (10, 10.0),
])
def test_dinheiro_aceita_formatos_brasileiros(entrada, esperado):
    assert dinheiro(entrada) == esperado


def test_avancar_parcela():
    assert avancar_parcela("2/5") == "3/5"


def test_avancar_parcela_termina_na_ultima():
    assert avancar_parcela("5/5") is None
