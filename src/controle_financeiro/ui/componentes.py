"""Componentes reutilizáveis: menu lateral, tabelas, números, formulários e balões."""
import re

from PySide6.QtCore import QPointF, QRect, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QAbstractItemView, QApplication, QButtonGroup, QCheckBox, QComboBox,
    QDialog, QDialogButtonBox, QFormLayout, QFrame,
    QHeaderView, QInputDialog, QLabel, QLineEdit, QPushButton, QStyle,
    QStyleOptionViewItem, QStyledItemDelegate, QTableWidget, QTableWidgetItem,
    QHBoxLayout, QVBoxLayout, QWidget,
)
from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.tema import PRIMARIA, TEXTO, TEXTO_SUAVE, VERDE_TEXTO


class MenuLateral(QWidget):
    """Menu da lateral, dividido em seções. Cada item abre uma página; `mudou` avisa o índice.
    As setas do teclado andam entre os itens."""
    mudou = Signal(int)

    def __init__(self):
        super().__init__()
        self._grupo = QButtonGroup(self)
        self._grupo.setExclusive(True)
        self._grupo.idToggled.connect(self._ao_marcar)
        self._lay = QVBoxLayout(self)
        self._lay.setContentsMargins(14, 0, 14, 10)
        self._lay.setSpacing(2)
        self._lay.addStretch()

    def _incluir(self, widget):
        self._lay.insertWidget(self._lay.count() - 1, widget)  # antes do espaço do fim

    def secao(self, nome):
        rotulo = QLabel(nome)
        rotulo.setObjectName("menuSecao")
        self._incluir(rotulo)

    def item(self, nome, dica=""):
        """Acrescenta um item e devolve o índice dele (o mesmo da página)."""
        botao = QPushButton(nome)
        botao.setObjectName("menuItem")
        botao.setCheckable(True)
        botao.setCursor(Qt.CursorShape.PointingHandCursor)
        botao.setToolTip(dica)
        indice = len(self._grupo.buttons())
        self._grupo.addButton(botao, indice)
        self._incluir(botao)
        return indice

    def _ao_marcar(self, indice, marcado):
        if marcado:
            self.mudou.emit(indice)

    def selecionar(self, indice):
        botao = self._grupo.button(indice)
        if botao:
            botao.setChecked(True)

    def atual(self):
        return self._grupo.checkedId()

    def nome(self, indice):
        return self._grupo.button(indice).text()

    def quantidade(self):
        return len(self._grupo.buttons())


def icone_seta(direcao, cor=PRIMARIA, lado=16):
    """Seta desenhada (esquerda ou direita) para os botões do seletor de mês."""
    escala = 2  # desenha no dobro do tamanho para ficar nítida em telas com escala
    imagem = QPixmap(lado * escala, lado * escala)
    imagem.setDevicePixelRatio(escala)
    imagem.fill(Qt.GlobalColor.transparent)
    p = QPainter(imagem)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    p.setPen(QPen(QColor(cor), 2, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap,
                  Qt.PenJoinStyle.RoundJoin))
    meio = lado / 2
    ponta, base = (meio - 3, meio + 2.5) if direcao == "esquerda" else (meio + 3, meio - 2.5)
    p.drawPolyline([QPointF(base, meio - 5), QPointF(ponta, meio), QPointF(base, meio + 5)])
    p.end()
    return QIcon(imagem)


class Tabela(QTableWidget):
    """Tabela do app. As colunas se ajustam ao conteúdo (título e valores sempre inteiros) e o
    espaço que sobra é dividido entre elas. Vazia, mostra um texto de orientação.
    Enter edita e Delete apaga a linha selecionada, quando a tela liga essas ações."""

    FOLGA = 4  # respiro de cada coluna, além do texto e do recuo das células (tema)

    def __init__(self, colunas, vazio=""):
        super().__init__(0, len(colunas))
        self.vazio = vazio          # texto quando não há linhas
        self.vazio_busca = ""       # texto quando a busca escondeu todas as linhas
        self._editar = None
        self._apagar = None
        self._ajustando = False
        self.setHorizontalHeaderLabels(colunas)
        self.verticalHeader().setVisible(False)
        self.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setShowGrid(False)
        self.setAlternatingRowColors(False)
        self.setWordWrap(False)
        self.verticalHeader().setDefaultSectionSize(44)
        self.horizontalHeader().setDefaultAlignment(Qt.AlignCenter)
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Fixed)
        self.horizontalHeader().setHighlightSections(False)
        self.doubleClicked.connect(lambda _i: self._chamar(self._editar))

    def ao_editar(self, acao):
        """Duplo clique ou Enter na linha selecionada."""
        self._editar = acao

    def ao_apagar(self, acao):
        """Tecla Delete na linha selecionada."""
        self._apagar = acao

    @staticmethod
    def _chamar(acao):
        if acao:
            acao()

    def keyPressEvent(self, evento):
        tecla = evento.key()
        if self.currentRow() >= 0:
            if tecla in (Qt.Key.Key_Return, Qt.Key.Key_Enter) and self._editar:
                self._editar()
                return
            if tecla == Qt.Key.Key_Delete and self._apagar:
                self._apagar()
                return
        super().keyPressEvent(evento)

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self.ajustar_colunas()

    def setHorizontalHeaderLabels(self, colunas):
        super().setHorizontalHeaderLabels(colunas)
        self.ajustar_colunas()

    def ajustar_colunas(self):
        """Largura de cada coluna = o que o conteúdo pede + uma parte igual do espaço que sobra.
        Se nem o conteúdo couber, aparece a barra de rolagem horizontal (nada é cortado)."""
        n = self.columnCount()
        if self._ajustando or n == 0:
            return
        self._ajustando = True
        try:
            cabecalho = self.horizontalHeader()
            titulos = [cabecalho.sectionSizeHint(c) for c in range(n)]
            celulas = [self.sizeHintForColumn(c) for c in range(n)]
            pedidas = [max(t, c + self.FOLGA) for t, c in zip(titulos, celulas)]
            livre = self.viewport().width() - sum(pedidas)
            if livre < 0:  # apertado: abre mão do respiro antes de precisar de rolagem
                pedidas = [max(t, c + 4) for t, c in zip(titulos, celulas)]
                livre = self.viewport().width() - sum(pedidas)
            extra = max(livre // n, 0)
            larguras = [p + extra for p in pedidas]
            if livre > 0:
                larguras[-1] += livre - extra * n  # a última coluna fecha a conta
            for c, largura in enumerate(larguras):
                if self.columnWidth(c) != largura:
                    self.setColumnWidth(c, largura)
        finally:
            self._ajustando = False

    def _texto_vazio(self):
        if self.rowCount() == 0:
            return self.vazio
        if all(self.isRowHidden(r) for r in range(self.rowCount())):
            return self.vazio_busca
        return ""

    def paintEvent(self, evento):
        super().paintEvent(evento)
        aviso = self._texto_vazio()
        if aviso:
            p = QPainter(self.viewport())
            p.setPen(QColor(TEXTO_SUAVE))
            area = self.viewport().rect().adjusted(24, 12, -24, -12)
            p.drawText(area, Qt.AlignmentFlag.AlignCenter | Qt.TextFlag.TextWordWrap, aviso)
            p.end()


def nova_tabela(colunas, vazio=""):
    return Tabela(colunas, vazio)


CORES_CARTAO = {}


def carregar_cores():
    CORES_CARTAO.clear()
    for c in fin().listar_cartoes():
        CORES_CARTAO[c["nome"]] = (QColor(c["cor"]), QColor(c["cor_texto"]))


def _pintar_fundo(painter, option, index, delegate):
    """Pinta a célula sem o texto (listra, seleção), para o desenho próprio ir por cima."""
    opt = QStyleOptionViewItem(option)
    delegate.initStyleOption(opt, index)
    opt.text = ""
    estilo = opt.widget.style() if opt.widget else QApplication.style()
    estilo.drawControl(QStyle.ControlElement.CE_ItemViewItem, opt, painter, opt.widget)


class BalaoCartao(QStyledItemDelegate):
    """Desenha o nome do banco num balão colorido. A célula continua com a cor da listra."""

    def sizeHint(self, option, index):
        tamanho = super().sizeHint(option, index)
        return QSize(tamanho.width() + 30, tamanho.height())  # o balão é mais largo que o texto

    def paint(self, painter, option, index):
        nome = index.data(Qt.ItemDataRole.DisplayRole)
        if nome not in CORES_CARTAO:
            return super().paint(painter, option, index)
        _pintar_fundo(painter, option, index, self)

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


class BarraProgresso(QStyledItemDelegate):
    """Desenha um percentual ("46%") como barra de progresso com o número ao lado.
    Células sem percentual ("—") ficam como texto comum."""

    LARGURA = 150

    def sizeHint(self, option, index):
        tamanho = super().sizeHint(option, index)
        return QSize(max(tamanho.width(), self.LARGURA), tamanho.height())

    def paint(self, painter, option, index):
        texto_celula = str(index.data(Qt.ItemDataRole.DisplayRole) or "")
        try:
            pct = float(texto_celula.rstrip("%").replace(",", "."))
        except ValueError:
            return super().paint(painter, option, index)
        _pintar_fundo(painter, option, index, self)
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        medida = painter.fontMetrics()
        largura_texto = medida.horizontalAdvance("100%")
        largura_barra = min(option.rect.width() - largura_texto - 28, 110)
        total = largura_barra + 8 + largura_texto
        x = option.rect.center().x() - total / 2
        y = option.rect.center().y() - 3
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor("#E5ECE9"))
        painter.drawRoundedRect(QRectF(x, y, largura_barra, 8), 4, 4)
        cheio = largura_barra * min(max(pct, 0), 100) / 100
        if cheio > 0:
            painter.setBrush(QColor(VERDE_TEXTO if pct >= 100 else PRIMARIA))
            painter.drawRoundedRect(QRectF(x, y, max(cheio, 8), 8), 4, 4)
        painter.setPen(QColor(TEXTO))
        painter.drawText(QRectF(x + largura_barra + 8, option.rect.top(), largura_texto,
                                option.rect.height()),
                         Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight, texto_celula)
        painter.restore()


ESQUERDA = Qt.AlignLeft | Qt.AlignVCenter
DIREITA = Qt.AlignRight | Qt.AlignVCenter


_CODIGO = re.compile(r"^[\d/%,.\-]+$")  # datas, parcelas (3/12), percentuais, dias


def _alinhamentos(t, linhas):
    """Valores em reais à direita (as casas decimais ficam uma embaixo da outra); datas, parcelas,
    Sim/Não, percentuais e balões no centro; nomes e descrições à esquerda, como numa planilha."""
    saida = []
    for c in range(t.columnCount()):
        textos = [str(v[c]) for _, v in linhas if c < len(v) and str(v[c]) not in ("", "—")]
        if isinstance(t.itemDelegateForColumn(c), (BalaoCartao, BarraProgresso)):
            saida.append(Qt.AlignCenter)
        elif textos and all(x.startswith(("R$", "-R$", "+R$")) for x in textos):
            saida.append(DIREITA)
        elif textos and all(_CODIGO.match(x) or x in ("Sim", "Não") for x in textos):
            saida.append(Qt.AlignCenter)
        else:
            saida.append(ESQUERDA)
    return saida


def preencher(t, linhas, cartao_col=None):
    """Preenche a tabela. Valores em reais ficam à direita, textos curtos no centro e o resto
    à esquerda (o título da coluna acompanha). Na coluna do cartão, cada banco ganha o balão da sua cor.
    linhas: lista de (id, [valores]). O id fica guardado na coluna 0."""
    anterior = selecionado(t)
    t.setRowCount(0)
    alinhamentos = _alinhamentos(t, linhas) if linhas else None
    if alinhamentos:
        for c, alinhamento in enumerate(alinhamentos):
            if t.horizontalHeaderItem(c):
                t.horizontalHeaderItem(c).setTextAlignment(alinhamento)
    for id_, valores in linhas:
        r = t.rowCount()
        t.insertRow(r)
        for c, v in enumerate(valores):
            it = QTableWidgetItem(str(v))
            if c == 0:
                it.setData(Qt.UserRole, id_)
            it.setTextAlignment(alinhamentos[c] if alinhamentos and c < len(alinhamentos) else Qt.AlignCenter)
            t.setItem(r, c, it)
    if anterior is not None:
        for r in range(t.rowCount()):
            if t.item(r, 0).data(Qt.UserRole) == anterior:
                t.selectRow(r)
                break
    if isinstance(t, Tabela):
        t.ajustar_colunas()
        t.viewport().update()


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


class ComboPessoa(QComboBox):
    """Lista de pessoas já cadastradas, com a opção de criar uma nova.
    Com permitir_vazio, a primeira opção significa "sem empréstimo" e devolve texto vazio."""
    VAZIO = "Eu (não é empréstimo)"
    NOVA = "+ Nova pessoa…"

    def __init__(self, atual="", permitir_vazio=True):
        super().__init__()
        self._vazio = permitir_vazio
        self._anterior = 0
        nomes = list(fin().pessoas())
        if atual and atual not in nomes:
            nomes.append(atual)
        if permitir_vazio:
            self.addItem(self.VAZIO)
        self.addItems(nomes)
        self.addItem(self.NOVA)
        if atual:
            self.setCurrentText(atual)
        self._anterior = self.currentIndex()
        self.activated.connect(self._ao_escolher)

    def _ao_escolher(self, indice):
        if self.itemText(indice) != self.NOVA:
            self._anterior = indice
            return
        nome, ok = QInputDialog.getText(self, "Nova pessoa", "Nome da pessoa:")
        nome = nome.strip()
        if not ok or not nome or nome == ".":
            self.setCurrentIndex(self._anterior)
            return
        existente = self.findText(nome, Qt.MatchFixedString)
        if existente < 0:
            existente = self.count() - 1
            self.insertItem(existente, nome)
        self.setCurrentIndex(existente)
        self._anterior = existente

    def currentText(self):
        texto_atual = super().currentText()
        return "" if self._vazio and texto_atual == self.VAZIO else texto_atual


def texto(valor="", dica=""):
    e = QLineEdit(valor)
    e.setPlaceholderText(dica)
    return e


class Metrica(QFrame):
    """Um número com rótulo e descrição. O tom (normal, positivo, aviso, negativo) muda a cor do
    valor e da bolinha ao lado do rótulo. Com ao_clicar, vira atalho para a página do assunto."""

    def __init__(self, rotulo, descricao="", tom="normal", ao_clicar=None, dica=""):
        super().__init__()
        self.setObjectName("metrica")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(18, 14, 18, 14)
        lay.setSpacing(4)
        topo = QHBoxLayout()
        topo.setSpacing(8)
        self.ponto = QLabel()
        self.ponto.setObjectName("metricaPonto")
        self.ponto.setFixedSize(8, 8)
        self.rotulo = QLabel(rotulo)
        self.rotulo.setObjectName("metricaRotulo")
        topo.addWidget(self.ponto)
        topo.addWidget(self.rotulo)
        topo.addStretch()
        self.valor = QLabel("—")
        self.valor.setObjectName("metricaValor")
        self.descricao = QLabel(descricao)
        self.descricao.setObjectName("descricao")
        self.descricao.setWordWrap(True)
        lay.addLayout(topo)
        lay.addWidget(self.valor)
        lay.addWidget(self.descricao)
        lay.addStretch()
        self._ao_clicar = ao_clicar
        if ao_clicar:
            self.setProperty("clicavel", "true")
            self.setCursor(Qt.CursorShape.PointingHandCursor)
            self.setToolTip(dica)
        self._tom(tom)

    def mouseReleaseEvent(self, evento):
        if self._ao_clicar and evento.button() == Qt.MouseButton.LeftButton \
                and self.rect().contains(evento.position().toPoint()):
            self._ao_clicar()
        super().mouseReleaseEvent(evento)

    def _tom(self, tom):
        for w in (self.valor, self.ponto):
            w.setProperty("tom", tom)
            w.style().unpolish(w)
            w.style().polish(w)

    def definir(self, texto_valor, tom=None):
        if tom:
            self._tom(tom)
        self.valor.setText(texto_valor)


class FaixaNumeros(QFrame):
    """Painel branco com várias métricas lado a lado, separadas por linhas finas."""

    def __init__(self, *metricas):
        super().__init__()
        self.setObjectName("faixa")
        lay = QHBoxLayout(self)
        lay.setContentsMargins(6, 6, 6, 6)
        lay.setSpacing(6)
        for i, m in enumerate(metricas):
            if i:
                divisor = QFrame()
                divisor.setObjectName("divisor")
                divisor.setFixedWidth(1)
                lay.addWidget(divisor)
            lay.addWidget(m, 1)


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
