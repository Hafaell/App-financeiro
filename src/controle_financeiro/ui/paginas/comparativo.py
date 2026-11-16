"""Comparativo entre meses: receitas, despesas e saldo dos últimos meses, em barras."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QFont, QPainter, QPainterPath, QPen
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import nova_tabela, preencher
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina
from controle_financeiro.ui.tema import BORDA, DESPESA, PRIMARIA, SUPERFICIE, TEXTO, TEXTO_SUAVE

SERIES = (("Receitas", "receitas", PRIMARIA), ("Despesas", "despesas", DESPESA))


class BarrasWidget(QWidget):
    """Gráfico de barras: para cada mês, uma barra de receitas e uma de despesas."""

    def __init__(self):
        super().__init__()
        self.dados = []
        self.setMinimumHeight(260)

    def definir(self, dados):
        self.dados = dados
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        # fundo em card, igual às tabelas
        p.setPen(QPen(QColor(BORDA), 1))
        p.setBrush(QColor(SUPERFICIE))
        p.drawRoundedRect(QRectF(self.rect()).adjusted(0.5, 0.5, -0.5, -0.5), 16, 16)
        fonte = QFont(self.font())
        fonte.setPointSizeF(9)
        p.setFont(fonte)
        if not self.dados:
            p.setPen(QColor(TEXTO_SUAVE))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter,
                       "Ainda não há meses para comparar.")
            p.end()
            return
        largura, altura = self.width(), self.height()

        # legenda: um quadradinho da cor de cada série, com o nome ao lado
        x = 22.0
        for nome, _chave, cor in SERIES:
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QColor(cor))
            p.drawRoundedRect(QRectF(x, 19, 10, 10), 3, 3)
            p.setPen(QColor(TEXTO))
            largura_nome = p.fontMetrics().horizontalAdvance(nome)
            p.drawText(QRectF(x + 16, 14, largura_nome + 4, 20), Qt.AlignmentFlag.AlignVCenter, nome)
            x += 16 + largura_nome + 22

        base_y = altura - 40
        topo = 62
        maximo = max(max(d["receitas"], d["despesas"], 1) for d in self.dados)
        escala = (base_y - topo) / maximo
        grupo = (largura - 44) / len(self.dados)
        barra = min(grupo * 0.3, 42)
        p.setPen(QPen(QColor(BORDA), 1))
        p.drawLine(22, base_y, largura - 22, base_y)
        for i, d in enumerate(self.dados):
            x = 22 + i * grupo + grupo / 2
            for dx, (_nome, chave, cor) in zip((-barra * 0.55, barra * 0.55), SERIES):
                h = d[chave] * escala
                if h <= 0:
                    continue
                # barra com o topo arredondado e a base reta, apoiada na linha
                raio = min(5, h, barra / 2)
                forma = QPainterPath()
                forma.setFillRule(Qt.FillRule.WindingFill)
                forma.addRoundedRect(QRectF(x + dx - barra / 2, base_y - h, barra, h), raio, raio)
                forma.addRect(QRectF(x + dx - barra / 2, base_y - h + raio, barra, h - raio))
                p.fillPath(forma.simplified(), QColor(cor))
            p.setPen(QColor(TEXTO_SUAVE))
            p.drawText(QRectF(x - grupo / 2, base_y + 8, grupo, 20), Qt.AlignmentFlag.AlignCenter,
                       d["nome"].split(" ")[0][:3])
        p.end()


class ComparativoPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)
        titulo = QLabel("Receitas e despesas dos últimos meses")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        legenda = QLabel("As despesas incluem o que é seu nos cartões. Aparecem até 6 meses abertos.")
        legenda.setObjectName("rotulo")
        lay.addWidget(legenda)
        self.grafico = BarrasWidget()
        lay.addWidget(self.grafico)
        self.tab = nova_tabela(["Mês", "Receitas", "Despesas", "Saldo", "Meu cartão", "A receber"])
        self.tab.setMinimumHeight(220)
        lay.addWidget(self.tab, 1)

    def atualizar(self):
        dados = fin().comparar_meses(6)
        self.grafico.definir(dados)
        preencher(self.tab, [(i, [d["nome"], brl(d["receitas"]), brl(d["despesas"]), brl(d["saldo"]),
                                  brl(d["meu_cartao"]), brl(d["a_receber"])])
                             for i, d in enumerate(dados)])
