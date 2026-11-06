"""Componentes reutilizáveis: tabelas, cartões de número, formulários e balões."""
from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QColor, QPainter
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHeaderView, QLabel, QLineEdit, QStyle,
    QStyleOptionViewItem, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QVBoxLayout,
)
from financas.contexto import fin


TONS = {"branco": "kpi", "verde": "kpi_verde", "amarelo": "kpi_amarelo", "azul": "kpi_azul"}


def nova_tabela(colunas):
    t = QTableWidget(0, len(colunas))
    t.setHorizontalHeaderLabels(colunas)
    t.verticalHeader().setVisible(False)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers)
    t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setSelectionMode(QAbstractItemView.SingleSelection)
    t.setShowGrid(False)
    t.setAlternatingRowColors(True)
    t.verticalHeader().setDefaultSectionSize(40)
    t.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
    t.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    return t


CORES_CARTAO = {}


def carregar_cores():
    CORES_CARTAO.clear()
    for c in fin().listar_cartoes():
        CORES_CARTAO[c["nome"]] = (QColor(c["cor"]), QColor(c["cor_texto"]))


class BalaoCartao(QStyledItemDelegate):
    """Desenha o nome do banco num balão colorido. A célula continua com a cor da listra."""

    def paint(self, painter, option, index):
        nome = index.data(Qt.ItemDataRole.DisplayRole)
        if nome not in CORES_CARTAO:
            return super().paint(painter, option, index)
        opt = QStyleOptionViewItem(option)
        self.initStyleOption(opt, index)
        opt.text = ""
        estilo = opt.widget.style() if opt.widget else QApplication.style()
        estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)

        fundo, letra = CORES_CARTAO[nome]
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        fonte = painter.font()
        fonte.setBold(True)
        painter.setFont(fonte)
        medida = painter.fontMetrics()
        largura = medida.horizontalAdvance(nome) + 28
        altura = min(medida.height() + 8, option.rect.height() - 12)
        balao = QRect(0, 0, largura, altura)
        balao.moveCenter(option.rect.center())
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(fundo)
        painter.drawRoundedRect(balao, altura / 2, altura / 2)
        painter.setPen(letra)
        painter.drawText(balao, Qt.AlignmentFlag.AlignCenter, nome)
        painter.restore()


def preencher(t, linhas, cartao_col=None):
    """Preenche a tabela. Todo texto fica centralizado.
    Na coluna do cartão, Inter fica laranja e Nubank roxo.
    linhas: lista de (id, [valores]). O id fica guardado na coluna 0."""
    anterior = selecionado(t)
    t.setRowCount(0)
    for id_, valores in linhas:
        r = t.rowCount()
        t.insertRow(r)
        for c, v in enumerate(valores):
            it = QTableWidgetItem(str(v))
            if c == 0:
                it.setData(Qt.UserRole, id_)
            it.setTextAlignment(Qt.AlignCenter)
            t.setItem(r, c, it)
    if anterior is not None:
        for r in range(t.rowCount()):
            if t.item(r, 0).data(Qt.UserRole) == anterior:
                t.selectRow(r)
                break


def selecionado(t):
    r = t.currentRow()
    item = t.item(r, 0) if r >= 0 else None
    return item.data(Qt.UserRole) if item else None


def combo(itens, atual=None):
    c = QComboBox()
    c.addItems(list(itens))
    if atual in itens:
        c.setCurrentText(atual)
    return c


def texto(valor="", dica=""):
    e = QLineEdit(valor)
    e.setPlaceholderText(dica)
    return e


class Kpi(QFrame):
    """Card de número. O tom (branco, verde, amarelo, azul) segue as cores do relatório."""

    def __init__(self, rotulo, tom="branco", descricao=""):
        super().__init__()
        self.rotulo = QLabel(rotulo)
        self.rotulo.setObjectName("rotulo")
        self.valor = QLabel("—")
        self.valor.setObjectName("valor")
        self.descricao = QLabel(descricao)
        self.descricao.setObjectName("descricao")
        self.descricao.setWordWrap(True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 18, 22, 18)
        lay.setSpacing(4)
        lay.addWidget(self.rotulo)
        lay.addWidget(self.valor)
        lay.addWidget(self.descricao)
        lay.addStretch()
        self._aplicar_tom(tom)

    def _aplicar_tom(self, tom):
        self.setObjectName(TONS[tom])
        self.style().unpolish(self)
        self.style().polish(self)

    def definir(self, texto_valor, tom=None, cor=None):
        if tom:
            self._aplicar_tom(tom)
        self.valor.setText(texto_valor)
        self.valor.setStyleSheet(f"color: {cor};" if cor else "")


class Formulario(QDialog):
    """Diálogo genérico. campos: lista de (chave, rótulo, widget)."""

    def __init__(self, pai, titulo, campos):
        super().__init__(pai)
        self.setWindowTitle(titulo)
        self.setMinimumWidth(440)
        self._campos = campos
        lay = QFormLayout(self)
        lay.setSpacing(14)
        lay.setContentsMargins(24, 24, 24, 20)
        for _, rotulo, widget in campos:
            lay.addRow(rotulo, widget)
        caixa = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        caixa.button(QDialogButtonBox.Save).setText("Salvar")
        caixa.button(QDialogButtonBox.Save).setObjectName("primario")
        caixa.button(QDialogButtonBox.Cancel).setText("Cancelar")
        caixa.accepted.connect(self.accept)
        caixa.rejected.connect(self.reject)
        lay.addRow(caixa)

    def valores(self):
        out = {}
        for chave, _, w in self._campos:
            if isinstance(w, QCheckBox):
                out[chave] = w.isChecked()
            elif isinstance(w, QComboBox):
                out[chave] = w.currentText()
            else:
                out[chave] = w.text().strip()
        return out
