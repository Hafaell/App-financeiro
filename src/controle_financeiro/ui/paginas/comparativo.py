"""Comparativo entre meses: receitas, despesas e saldo dos últimos meses, em barras."""
from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QFont
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import nova_tabela, preencher
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina


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
        p.fillRect(self.rect(), QColor("#FFFFFF"))
        if not self.dados:
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "Sem meses para comparar")
            return
        largura, altura = self.width(), self.height()
        base_y = altura - 40
        topo = 20
        maximo = max(max(d["receitas"], d["despesas"], 1) for d in self.dados)
        escala = (base_y - topo) / maximo
        grupo = (largura - 40) / len(self.dados)
        barra = min(grupo * 0.3, 42)
        fonte = QFont("Segoe UI", 8)
        p.setFont(fonte)
        for i, d in enumerate(self.dados):
            x = 20 + i * grupo + grupo / 2
            for dx, valor, cor in ((-barra * 0.6, d["receitas"], "#1E7A4A"),
                                   (barra * 0.6, d["despesas"], "#2359D7")):
                h = valor * escala
                p.fillRect(QRectF(x + dx - barra / 2, base_y - h, barra, h), QColor(cor))
            p.setPen(QColor("#5A6B8C"))
            p.drawText(QRectF(x - grupo / 2, base_y + 6, grupo, 20), Qt.AlignmentFlag.AlignCenter,
                       d["nome"].split(" ")[0][:3])
            p.setPen(QColor("#1B2A4A"))
        p.end()


class ComparativoPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        titulo = QLabel("Comparativo entre meses")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        legenda = QLabel("Verde: receitas   ·   Azul: despesas (incluem meu cartão)")
        legenda.setObjectName("rotulo")
        lay.addWidget(legenda)
        self.grafico = BarrasWidget()
        lay.addWidget(self.grafico)
        self.tab = nova_tabela(["Mês", "Receitas", "Despesas", "Saldo", "Meu cartão", "A receber"])
        self.tab.setMinimumHeight(220)
        lay.addWidget(self.tab)

    def atualizar(self):
        dados = fin().comparar_meses(6)
        self.grafico.definir(dados)
        preencher(self.tab, [(i, [d["nome"], brl(d["receitas"]), brl(d["despesas"]), brl(d["saldo"]),
                                  brl(d["meu_cartao"]), brl(d["a_receber"])])
                             for i, d in enumerate(dados)])
