"""Cadastros: cartões, categorias (com orçamento) e meses abertos."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (QColorDialog, QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton,
                               QVBoxLayout, QWidget)

from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.componentes import nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.tema import VERMELHO_TEXTO


class NovoCartao(QDialog):
    """Cadastra um cartão com nome e cor. Ele passa a aparecer em Transações e em Despesas."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Novo cartão")
        self.setMinimumWidth(380)
        self.cor = "#2359D7"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel("Novo cartão")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        lay.addWidget(QLabel("Nome"))
        self.nome = texto("", "Ex.: C6, Itaú, Mercado Pago")
        self.nome.textChanged.connect(self._mostrar_previa)
        lay.addWidget(self.nome)
        lay.addWidget(QLabel("Cor do balão"))
        escolher = QPushButton("Escolher cor")
        escolher.clicked.connect(self._escolher_cor)
        lay.addWidget(escolher, 0, Qt.AlignmentFlag.AlignLeft)
        self.previa = QLabel()
        self.previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previa.setMinimumHeight(48)
        lay.addWidget(self.previa)
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        lay.addWidget(self.erro)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(cancelar)
        botoes.addWidget(salvar)
        lay.addLayout(botoes)
        self._mostrar_previa()

    def _escolher_cor(self):
        cor = QColorDialog.getColor(QColor(self.cor), self, "Cor do cartão")
        if cor.isValid():
            self.cor = cor.name().upper()
            self._mostrar_previa()

    def _mostrar_previa(self):
        nome = self.nome.text().strip() or "Nome do cartão"
        self.previa.setText(nome)
        self.previa.setStyleSheet(
            f"background: {self.cor}; color: {fin().cor_texto_para(self.cor)};"
            "border-radius: 16px; padding: 8px 20px; font-weight: 700;")

    def _salvar(self):
        try:
            fin().adicionar_cartao(self.nome.text(), self.cor)
        except ValueError as e:
            self.erro.setText(str(e))
            self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
            return
        self.accept()


class CategoriaForm(QDialog):
    """Cria ou edita uma categoria: nome, cor, orçamento mensal e prévia."""

    def __init__(self, pai, categoria=None):
        super().__init__(pai)
        self.setWindowTitle("Categoria")
        self.setMinimumWidth(380)
        self.categoria = categoria
        self.cor = categoria["cor"] if categoria else "#2359D7"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Nova categoria" if not categoria else "Editar categoria"))
        self.nome = texto(categoria["nome"] if categoria else "", "Ex.: Mercado, Academia")
        self.nome.textChanged.connect(self._previa)
        lay.addWidget(QLabel("Nome"))
        lay.addWidget(self.nome)
        self.orcamento = texto(brl(categoria["orcamento"]) if categoria and categoria["orcamento"] else "",
                               "Limite mensal, ex.: R$ 800,00 (vazio = sem limite)")
        lay.addWidget(QLabel("Orçamento mensal"))
        lay.addWidget(self.orcamento)
        escolher = QPushButton("Escolher cor")
        escolher.clicked.connect(self._escolher_cor)
        lay.addWidget(escolher, 0, Qt.AlignmentFlag.AlignLeft)
        self.previa = QLabel()
        self.previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previa.setMinimumHeight(40)
        lay.addWidget(self.previa)
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        lay.addWidget(self.erro)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(cancelar)
        botoes.addWidget(salvar)
        lay.addLayout(botoes)
        self._previa()

    def _escolher_cor(self):
        cor = QColorDialog.getColor(QColor(self.cor), self, "Cor da categoria")
        if cor.isValid():
            self.cor = cor.name().upper()
            self._previa()

    def _previa(self):
        nome = self.nome.text().strip() or "Nome da categoria"
        self.previa.setText(nome)
        self.previa.setStyleSheet(f"background: {self.cor}; color: {core_cor_texto(self.cor)};"
                                  "border-radius: 14px; padding: 6px 18px; font-weight: 700;")

    def _salvar(self):
        try:
            if self.categoria:
                fin().atualizar_categoria(self.categoria["id"], self.nome.text(), self.cor,
                                          self.orcamento.text())
            else:
                fin().adicionar_categoria(self.nome.text(), self.cor, self.orcamento.text())
        except ValueError as e:
            self.erro.setText(str(e))
            self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
            return
        self.accept()


def core_cor_texto(cor):
    return fin().cor_texto_para(cor)


class CategoriasDialog(QDialog):
    """Lista as categorias: criar, editar (duplo clique) e apagar."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Categorias")
        self.setMinimumSize(460, 420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Categorias"))
        self.tab = nova_tabela(["Nome", "Orçamento mensal"])
        self.tab.ao_editar(self.editar)
        self.tab.ao_apagar(self.apagar)
        lay.addWidget(self.tab, 1)
        botoes = QHBoxLayout()
        apagar = QPushButton("Apagar")
        apagar.setObjectName("perigo")
        apagar.clicked.connect(self.apagar)
        nova = QPushButton("Nova categoria")
        nova.setObjectName("primario")
        nova.clicked.connect(self.nova)
        botoes.addWidget(apagar)
        botoes.addStretch()
        botoes.addWidget(nova)
        lay.addLayout(botoes)
        self._carregar()

    def _carregar(self):
        preencher(self.tab, [(c["id"], [c["nome"], brl(c["orcamento"]) if c["orcamento"] else "Sem limite"])
                             for c in fin().listar_categorias()])

    def nova(self):
        if CategoriaForm(self).exec() == QDialog.Accepted:
            self._carregar()

    def editar(self):
        id_ = selecionado(self.tab)
        c = fin().listar_categorias()
        atual = next((x for x in c if x["id"] == id_), None)
        if atual and CategoriaForm(self, atual).exec() == QDialog.Accepted:
            self._carregar()

    def apagar(self):
        id_ = selecionado(self.tab)
        if id_ is None:
            return
        pergunta = "Apagar esta categoria? Os lançamentos dela ficam sem categoria."
        if QMessageBox.question(self, "Apagar categoria", pergunta) != QMessageBox.Yes:
            return
        fin().apagar_categoria(id_)
        self._carregar()


class GerenciarMeses(QDialog):
    """Lista os meses abertos. Você pode apagar os antigos; o mês atual não pode ser apagado."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Meses abertos")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel("Meses abertos")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        self._linhas = QVBoxLayout()
        self._linhas.setSpacing(8)
        lay.addLayout(self._linhas)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        lay.addWidget(fechar, 0, Qt.AlignmentFlag.AlignRight)
        self._montar()

    def _montar(self):
        while self._linhas.count():
            item = self._linhas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        ativo = fin().mes_ativo()
        for m in reversed(fin().sessoes()):
            linha = QHBoxLayout()
            linha.addWidget(QLabel(fin().nome_mes(m)))
            linha.addStretch()
            if m == ativo:
                atual = QLabel("Mês atual")
                atual.setObjectName("rotulo")
                linha.addWidget(atual)
            else:
                apagar = QPushButton("Apagar")
                apagar.setObjectName("perigo")
                apagar.clicked.connect(lambda _=False, mes=m: self._apagar(mes))
                linha.addWidget(apagar)
            caixa = QWidget()
            caixa.setLayout(linha)
            self._linhas.addWidget(caixa)

    def _apagar(self, mes):
        pergunta = (f"Apagar {fin().nome_mes(mes)} e todos os seus lançamentos? "
                    "Essa ação não pode ser desfeita.")
        if QMessageBox.question(self, "Apagar mês", pergunta) != QMessageBox.Yes:
            return
        try:
            fin().apagar_mes(mes)
        except ValueError as e:
            QMessageBox.warning(self, "Não consegui apagar", str(e))
            return
        self._montar()
