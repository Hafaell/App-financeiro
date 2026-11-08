"""Seletor de mês com setas (navega só pelos meses abertos)."""
from PySide6.QtCore import QSize, Signal
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton,
    QStyle, QVBoxLayout,
)
from controle_financeiro.dados.contexto import fin
from controle_financeiro.nucleo.utilidades import MESES_EXIBIR


class MesSeletor(QFrame):
    """Navega entre os meses abertos com as setas. Não avança além do mês atual,
    que é o mais recente aberto. Depois de uma virada, o mês novo vira o atual."""
    mudou = Signal()

    def __init__(self):
        super().__init__()
        self.setObjectName("seletor")
        self._codigos = []
        self._i = 0

        lay = QHBoxLayout(self)
        lay.setContentsMargins(8, 6, 8, 6)
        lay.setSpacing(10)
        self.antes = QPushButton()
        self.depois = QPushButton()
        self.antes.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack))
        self.depois.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward))
        for b in (self.antes, self.depois):
            b.setObjectName("setaMes")
            b.setFixedSize(38, 38)
            b.setIconSize(QSize(16, 16))
            b.setToolTip("Mês anterior" if b is self.antes else "Próximo mês")
        textos = QVBoxLayout()
        textos.setSpacing(0)
        self.nome = QLabel()
        self.nome.setObjectName("mesNome")
        self.situacao = QLabel()
        self.situacao.setObjectName("rotulo")
        textos.addWidget(self.nome)
        textos.addWidget(self.situacao)
        self.voltar = QPushButton("Ir ao atual")
        self.voltar.setObjectName("voltar")
        lay.addWidget(self.antes)
        lay.addLayout(textos)
        lay.addWidget(self.depois)
        lay.addSpacing(8)
        lay.addWidget(self.voltar)

        self.antes.clicked.connect(lambda: self._mover(-1))
        self.depois.clicked.connect(lambda: self._mover(1))
        self.voltar.clicked.connect(self._ir_atual)
        self.recarregar()

    def codigo(self):
        return self._codigos[self._i]

    def recarregar(self):
        """Relê os meses abertos. Quem estava no mês atual passa para o novo mês atual
        (depois de uma virada). Quem estava em um mês anterior continua nele."""
        anterior_ativo = self._codigos[-1] if self._codigos else None
        selecionado = self._codigos[self._i] if self._codigos else None
        self._codigos = fin().sessoes()
        if selecionado in self._codigos and selecionado != anterior_ativo:
            self._i = self._codigos.index(selecionado)
        else:
            self._i = len(self._codigos) - 1
        self._mostrar()

    def _mover(self, passo):
        self._i = min(max(self._i + passo, 0), len(self._codigos) - 1)
        self._mostrar()
        self.mudou.emit()

    def _ir_atual(self):
        self._i = len(self._codigos) - 1
        self._mostrar()
        self.mudou.emit()

    def _mostrar(self):
        c = self.codigo()
        ano, mes = c.split("-")
        self.nome.setText(f"{MESES_EXIBIR[int(mes) - 1]} de {ano}")
        e_atual = self._i == len(self._codigos) - 1
        self.situacao.setText("Mês atual" if e_atual else "Mês anterior")
        self.antes.setEnabled(self._i > 0)
        self.depois.setEnabled(not e_atual)
        self.voltar.setEnabled(not e_atual)
