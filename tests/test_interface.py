"""Interface: menu em seções, páginas separadas e atalhos.
Usa o Qt fora da tela e o banco SQLite dos testes (nada vai ao Supabase)."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PySide6.QtWidgets")  # sem Qt nesta máquina, os testes são pulados


@pytest.fixture(scope="module")
def janela():
    from controle_financeiro.dados.contexto import auth
    app = QtWidgets.QApplication.instance() or QtWidgets.QApplication([])
    if "Teste" not in auth().listar_usuarios():
        auth().cadastrar_usuario("Teste", "segredo1")
    auth().entrar("Teste", "segredo1")
    from controle_financeiro.ui.janela import Janela
    j = Janela()
    j.timer.stop()
    yield j
    j.close()
    app.processEvents()


def test_menu_tem_as_paginas_na_ordem_das_secoes(janela):
    nomes = [janela.menu.nome(i) for i in range(janela.menu.quantidade())]
    assert nomes == ["Visão geral", "Transações", "Receitas e despesas", "Planejamento", "Comparativo",
                     "Empréstimos", "Caixinhas", "Importar extrato", "Ferramentas"]
    assert janela.paginas.count() == len(nomes)
    secoes = [r.text() for r in janela.menu.findChildren(QtWidgets.QLabel)]
    assert secoes == ["Geral", "Pessoal", "Sistema"]


def test_cada_item_do_menu_abre_a_sua_pagina(janela):
    for i in range(janela.menu.quantidade()):
        janela.menu.selecionar(i)
        assert janela.paginas.currentIndex() == i
        assert janela.titulo.text() == janela.menu.nome(i)
    janela.menu.selecionar(0)


def test_receitas_despesas_e_caixinhas_ficam_fora_da_visao_geral(janela):
    tabelas = QtWidgets.QTableWidget
    assert janela.visao.findChildren(tabelas) == []
    assert len(janela.lancamentos.findChildren(tabelas)) == 2
    assert len(janela.caixinhas.findChildren(tabelas)) == 1
    assert janela.paginas.indexOf(janela.lancamentos) >= 0
    assert janela.paginas.indexOf(janela.caixinhas) >= 0


def test_card_da_visao_geral_abre_a_pagina_do_assunto(janela):
    janela.menu.selecionar(0)
    janela.visao.receber._ao_clicar()
    assert janela.paginas.currentWidget() is janela.deve
    janela.menu.selecionar(0)
    janela.visao.receitas._ao_clicar()
    assert janela.paginas.currentWidget() is janela.lancamentos
    janela.menu.selecionar(0)


def test_ctrl_n_abre_o_lancamento_da_pagina_aberta(janela, monkeypatch):
    chamadas = []
    monkeypatch.setattr(janela.cartoes, "nova", lambda: chamadas.append("compra"))
    monkeypatch.setattr(janela.lancamentos.despesas, "adicionar", lambda: chamadas.append("despesa"))
    monkeypatch.setattr(janela.deve, "pagamento", lambda: chamadas.append("pagamento"))
    monkeypatch.setattr(janela.caixinhas, "nova", lambda: chamadas.append("caixinha"))
    for pagina in (janela.visao, janela.cartoes, janela.lancamentos, janela.deve,
                   janela.caixinhas, janela.ferramentas):
        janela.ir_para(pagina)
        janela.novo()
    assert chamadas == ["compra", "compra", "despesa", "pagamento", "caixinha", "compra"]
    janela.menu.selecionar(0)


def test_enter_edita_e_delete_apaga_a_linha_selecionada(janela):
    from PySide6.QtCore import Qt
    from PySide6.QtTest import QTest
    from controle_financeiro.ui.componentes import nova_tabela, preencher
    feitos = []
    tabela = nova_tabela(["Descrição", "Valor"])
    tabela.ao_editar(lambda: feitos.append("editar"))
    tabela.ao_apagar(lambda: feitos.append("apagar"))
    QTest.keyClick(tabela, Qt.Key.Key_Delete)  # sem linha selecionada, não faz nada
    preencher(tabela, [(7, ["Mercado", "R$ 10,00"])])
    tabela.selectRow(0)
    QTest.keyClick(tabela, Qt.Key.Key_Return)
    QTest.keyClick(tabela, Qt.Key.Key_Delete)
    assert feitos == ["editar", "apagar"]
