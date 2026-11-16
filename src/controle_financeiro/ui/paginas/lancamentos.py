"""Página Receitas e despesas: as duas listas de lançamentos do mês, lado a lado."""
from PySide6.QtWidgets import (
    QBoxLayout, QCheckBox, QDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)
from controle_financeiro.ui.formatacao import categorias_opcoes, id_categoria, nome_categoria
from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.componentes import Formulario, combo, nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.formatacao import brl, data_br, nomes_cartoes
from controle_financeiro.ui.paginas.base import Pagina


class PainelLancamento(QWidget):
    """Lista de receitas ou despesas. Despesas têm categoria e o campo Recorrente."""

    def __init__(self, pagina, tabela, titulo, singular, com_recorrente=False):
        super().__init__()
        self.pagina = pagina
        self.tabela = tabela
        self.singular = singular
        self.com_recorrente = com_recorrente
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(10)
        rotulo = QLabel(titulo)
        rotulo.setObjectName("secao")
        cabecalho.addWidget(rotulo)
        cabecalho.addStretch()
        apagar = QPushButton("Apagar")
        apagar.setToolTip("Apagar a linha selecionada (Delete)")
        apagar.clicked.connect(self.apagar)
        add = QPushButton(f"Nova {singular}")
        add.setObjectName("primario")
        add.clicked.connect(self.adicionar)
        cabecalho.addWidget(apagar)
        cabecalho.addWidget(add)
        lay.addLayout(cabecalho)
        colunas = ["Descrição", "Valor"] + (["Categoria", "Recorrente"] if com_recorrente else []) + ["Lançado em"]
        self.tab = nova_tabela(
            colunas, f"Nenhuma {singular} neste mês.\nClique em Nova {singular} para lançar a primeira.")
        self.tab.ao_editar(self.editar)
        self.tab.ao_apagar(self.apagar)
        lay.addWidget(self.tab, 1)
        self.total = QLabel()
        self.total.setObjectName("total")
        lay.addWidget(self.total)

    def _campos(self, descricao="", valor="", recorrente=False, categoria_id=None):
        exemplo = "Ex.: Aluguel" if self.com_recorrente else "Ex.: Salário"
        campos = [
            ("descricao", "Descrição", texto(descricao, exemplo)),
            ("valor", "Valor", texto(valor, "R$ 0,00")),
        ]
        if self.com_recorrente:
            campos.append(("categoria", "Categoria", combo(categorias_opcoes(), nome_categoria(categoria_id))))
            caixa = QCheckBox("Recorrente: permanece no próximo mês")
            caixa.setChecked(recorrente)
            campos.append(("recorrente", "", caixa))
        return campos

    def atualizar(self):
        mes = self.pagina.mes()
        linhas = fin().listar_lancamentos(self.tabela, mes)

        def valores(l):
            v = [l["descricao"], brl(l["valor"])]
            if self.com_recorrente:
                v.append(nome_categoria(l.get("categoria_id")))
                v.append("Sim" if l.get("recorrente") else "Não")
            v.append(data_br(l.get("data_lancamento")))
            return v

        itens = []
        total = sum(l["valor"] for l in linhas)
        if self.tabela == "despesas":
            # Compras suas nos cartões (sem os empréstimos). Ids negativos = não editáveis aqui.
            cartoes = fin().resumo_mes(mes)["cartoes"]
            for i, nome in enumerate(nomes_cartoes()):
                valor = cartoes[nome]["meu_cartao"]
                v = [f"Cartão {nome}", brl(valor)]
                if self.com_recorrente:
                    v.append("—")
                    v.append("—")
                v.append("—")
                itens.append((-(i + 1), v))
                total += valor
        preencher(self.tab, itens + [(l["id"], valores(l)) for l in linhas])
        rotulo = "Total de despesas (inclui meu cartão)" if self.tabela == "despesas" else "Total de receitas"
        self.total.setText(f"{rotulo}: {brl(total)}")

    def editar(self):
        id_ = selecionado(self.tab)
        if id_ is not None and id_ < 0:
            QMessageBox.information(
                self, "Cartão",
                "O valor do cartão vem das compras. Para mudar, edite a compra na página Transações.")
            return
        l = fin().obter_lancamento(self.tabela, id_) if id_ is not None else None
        if not l:
            return
        dlg = Formulario(self, f"Editar {self.singular}",
                         self._campos(l["descricao"], brl(l["valor"]),
                                      bool(l.get("recorrente")), l.get("categoria_id")))
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().atualizar_lancamento(self.tabela, id_, v["descricao"], v["valor"],
                                      recorrente=v.get("recorrente", False), categoria_id=id_categoria(v.get("categoria")))
        except ValueError as e:
            QMessageBox.warning(self, "Não consegui salvar", str(e))
            return
        self.pagina.mudou()

    def adicionar(self):
        dlg = Formulario(self, f"Nova {self.singular}", self._campos())
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().adicionar_lancamento(self.tabela, v["descricao"], v["valor"],
                                      self.pagina.mes(), recorrente=v.get("recorrente", False), categoria_id=id_categoria(v.get("categoria")))
        except ValueError as e:
            QMessageBox.warning(self, "Não consegui salvar", str(e))
            return
        self.pagina.mudou()

    def apagar(self):
        id_ = selecionado(self.tab)
        if id_ is not None and id_ < 0:
            QMessageBox.information(
                self, "Cartão",
                "Os cartões não se apagam por aqui. Apague as compras na página Transações.")
            return
        if id_ is None:
            QMessageBox.information(self, "Apagar", f"Selecione uma {self.singular} na lista.")
            return
        l = fin().obter_lancamento(self.tabela, id_)
        descricao = f"{l['descricao']} ({brl(l['valor'])})" if l else f"esta {self.singular}"
        if QMessageBox.question(self, "Apagar", f"Apagar {descricao}? "
                                "Essa ação não pode ser desfeita.") != QMessageBox.Yes:
            return
        fin().apagar_lancamento(self.tabela, id_)
        self.pagina.mudou()


class LancamentosPage(Pagina):
    """Receitas à esquerda e despesas à direita. Em janelas estreitas, uma embaixo da outra."""

    LARGURA_LADO_A_LADO = 860

    def __init__(self, janela):
        super().__init__(janela)
        self._lay = QBoxLayout(QBoxLayout.Direction.LeftToRight, self)
        self._lay.setContentsMargins(0, 0, 0, 0)
        self._lay.setSpacing(24)
        self.receitas = PainelLancamento(self, "receitas", "Receitas", "receita")
        self.despesas = PainelLancamento(self, "despesas", "Despesas", "despesa",
                                         com_recorrente=True)
        # As despesas têm mais colunas (categoria e recorrente), por isso ficam com mais espaço
        self._lay.addWidget(self.receitas, 2)
        self._lay.addWidget(self.despesas, 3)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        lado_a_lado = self.width() >= self.LARGURA_LADO_A_LADO
        direcao = QBoxLayout.Direction.LeftToRight if lado_a_lado else QBoxLayout.Direction.TopToBottom
        if self._lay.direction() != direcao:
            self._lay.setDirection(direcao)

    def novo(self):
        self.despesas.adicionar()

    def atualizar(self):
        self.receitas.atualizar()
        self.despesas.atualizar()
