"""Receitas e despesas (lista de lançamentos)."""
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QHBoxLayout, QLabel,
    QMessageBox, QPushButton, QVBoxLayout, QWidget,
)
from ..formatacao import categorias_opcoes, id_categoria, nome_categoria
from financas.contexto import fin
from ..componentes import Formulario, combo, nova_tabela, preencher, selecionado, texto
from ..formatacao import brl, nomes_cartoes
from .base import Pagina


class PainelLancamento(QWidget):
    """Lista de receitas ou despesas. Despesas têm o campo Recorrente."""

    def __init__(self, pagina, tabela, titulo, singular, com_recorrente=False):
        super().__init__()
        self.pagina = pagina
        self.tabela = tabela
        self.singular = singular
        self.com_recorrente = com_recorrente
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        rotulo = QLabel(titulo)
        rotulo.setObjectName("secao")
        lay.addWidget(rotulo)
        botoes = QHBoxLayout()
        botoes.addStretch()
        apagar = QPushButton("Apagar")
        apagar.clicked.connect(self.apagar)
        add = QPushButton(f"Nova {singular}")
        add.setObjectName("primario")
        add.clicked.connect(self.adicionar)
        botoes.addWidget(apagar)
        botoes.addWidget(add)
        lay.addLayout(botoes)
        colunas = ["Descrição", "Valor"] + (["Categoria", "Recorrente"] if com_recorrente else [])
        self.tab = nova_tabela(colunas)
        self.tab.doubleClicked.connect(lambda _i: self.editar())
        lay.addWidget(self.tab)
        self.total = QLabel()
        self.total.setObjectName("rotulo")
        lay.addWidget(self.total)

    def _campos(self, descricao="", valor="", recorrente=False, categoria_id=None):
        campos = [
            ("descricao", "Descrição", texto(descricao, "Ex.: Salário")),
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
                itens.append((-(i + 1), v))
                total += valor
        preencher(self.tab, itens + [(l["id"], valores(l)) for l in linhas])
        rotulo = "Total de despesas (inclui meu cartão)" if self.tabela == "despesas" else "Total"
        self.total.setText(f"{rotulo}: {brl(total)}")

    def editar(self):
        id_ = selecionado(self.tab)
        if id_ is not None and id_ < 0:
            QMessageBox.information(
                self, "Cartão",
                "O valor do cartão vem das compras. Para mudar, edite a compra na aba Cartões.")
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
                self, "Cartão", "Os cartões não se apagam por aqui. Apague as compras na aba Cartões.")
            return
        if id_ is None:
            QMessageBox.information(self, "Apagar", "Selecione um lançamento na lista.")
            return
        if QMessageBox.question(self, "Apagar", "Apagar este lançamento?") != QMessageBox.Yes:
            return
        fin().apagar_lancamento(self.tabela, id_)
        self.pagina.mudou()


class LancamentosPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QHBoxLayout(self)
        lay.setSpacing(24)
        self.receitas = PainelLancamento(self, "receitas", "Receitas", "receita")
        self.despesas = PainelLancamento(self, "despesas", "Despesas", "despesa",
                                         com_recorrente=True)
        lay.addWidget(self.receitas)
        lay.addWidget(self.despesas)

    def atualizar(self):
        self.receitas.atualizar()
        self.despesas.atualizar()
