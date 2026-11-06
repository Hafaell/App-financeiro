"""Página Visão geral."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QGridLayout, QLabel, QScrollArea,
    QVBoxLayout, QWidget,
)
from PySide6.QtWidgets import QDialog, QHBoxLayout, QProgressBar, QPushButton
from ..componentes import Formulario, texto
from financas.contexto import fin
from ..componentes import Kpi
from ..formatacao import brl
from .base import Pagina
from .caixinhas import CaixinhasPage
from .lancamentos import LancamentosPage
from ..tema import VERMELHO_TEXTO


class VisaoPage(Pagina):
    """Visão geral: resumo do mês, receitas e despesas e caixinhas, tudo na mesma tela."""

    def __init__(self, janela):
        super().__init__(janela)
        conteudo = QWidget()
        lay = QVBoxLayout(conteudo)
        lay.setSpacing(18)
        lay.setContentsMargins(0, 0, 8, 0)
        # Cards em grade de 3 colunas: quebram de linha em vez de empurrar a tela para o lado
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(16)
        self.titulo_mes = QLabel()
        self.titulo_mes.setObjectName("secao")
        lay.addWidget(self.titulo_mes)
        self.receitas = Kpi("Receitas", "verde", "Entradas que você recebeu no mês")
        self.despesas = Kpi("Despesas do mês", "amarelo",
                            "Total da aba Despesas, com seus cartões")
        self.saldo = Kpi("Saldo", "verde", "Receitas, menos o total de despesas")
        self.meu_cartao = Kpi("Meu cartão no mês", "azul",
                              "Compras suas no cartão, sem empréstimos")
        self.com_emp = Kpi("Cartões com empréstimos", "branco",
                           "Total nos cartões, incluindo o que as pessoas devem")
        self.receber = Kpi("A receber de pessoas", "azul",
                           "Quanto as pessoas devem neste mês")
        self._cards = [self.receitas, self.despesas, self.saldo,
                       self.meu_cartao, self.com_emp, self.receber]
        self._grade = grade
        self._colunas = None
        lay.addLayout(grade)
        self.orcamento_card = QFrame()
        self.orcamento_card.setObjectName("kpi")
        self._orc_lay = QVBoxLayout(self.orcamento_card)
        self._orc_lay.setContentsMargins(22, 18, 22, 18)
        self._orc_lay.setSpacing(10)
        lay.addWidget(self.orcamento_card)
        self.lancamentos = LancamentosPage(janela)
        lay.addWidget(self.lancamentos)
        titulo_cx = QLabel("Caixinhas")
        titulo_cx.setObjectName("secao")
        lay.addWidget(titulo_cx)
        self.caixinhas = CaixinhasPage(janela)
        lay.addWidget(self.caixinhas)
        lay.addStretch()

        rolagem = QScrollArea()
        rolagem.setWidgetResizable(True)
        rolagem.setFrameShape(QFrame.NoFrame)
        rolagem.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rolagem.setWidget(conteudo)
        principal = QVBoxLayout(self)
        principal.setContentsMargins(0, 0, 0, 0)
        principal.addWidget(rolagem)
        self._organizar_cards()

    def resizeEvent(self, evento):
        super().resizeEvent(evento)
        self._organizar_cards()

    def _organizar_cards(self):
        """3 colunas em telas largas, 2 em médias e 1 em estreitas, para nunca passar da largura."""
        largura = self.width()
        colunas = 3 if largura >= 780 else (2 if largura >= 520 else 1)
        if colunas == self._colunas:
            return
        self._colunas = colunas
        while self._grade.count():
            self._grade.takeAt(0)
        for i, card in enumerate(self._cards):
            self._grade.addWidget(card, i // colunas, i % colunas)
        for c in range(colunas):
            self._grade.setColumnStretch(c, 1)

    def _atualizar_orcamento(self, r):
        """Orçamento de cada categoria (barra de uso) e renda do mês."""
        while self._orc_lay.count():
            item = self._orc_lay.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        titulo = QLabel("Orçamento do mês")
        titulo.setObjectName("secao")
        self._orc_lay.addWidget(titulo)
        gastos = fin().gasto_por_categoria(self.mes())
        limites = [c for c in fin().listar_categorias() if c["orcamento"] > 0]
        if not limites:
            aviso = QLabel("Defina um limite mensal nas categorias (botão Categorias, em Transações).")
            aviso.setObjectName("rotulo")
            self._orc_lay.addWidget(aviso)
        for c in limites:
            gasto = gastos.get(c["id"], 0.0)
            pct = min(gasto / c["orcamento"] * 100, 100)
            cor = "#B5483A" if gasto > c["orcamento"] else ("#B07A00" if pct >= 80 else "#2359D7")
            linha = QWidget()
            ll = QVBoxLayout(linha)
            ll.setContentsMargins(0, 0, 0, 0)
            ll.setSpacing(4)
            rotulo = QLabel(f"{c['nome']}: {brl(gasto)} de {brl(c['orcamento'])}")
            rotulo.setObjectName("rotulo")
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setValue(int(round(pct)))
            barra.setTextVisible(False)
            barra.setFixedHeight(10)
            barra.setStyleSheet(f"QProgressBar {{ background: #E3EEFF; border: none; border-radius: 5px; }}"
                                f"QProgressBar::chunk {{ background: {cor}; border-radius: 5px; }}")
            ll.addWidget(rotulo)
            ll.addWidget(barra)
            self._orc_lay.addWidget(linha)
        renda = r.get("renda")
        if renda:
            texto_renda = (f"Renda do mês: {brl(renda)}  ·  o cartão consome "
                           f"{r['cartao_percentual_renda']}% da renda")
        else:
            texto_renda = "Renda do mês: não informada"
        cabecalho = QWidget()
        cl = QHBoxLayout(cabecalho)
        cl.setContentsMargins(0, 6, 0, 0)
        cl.addWidget(QLabel(texto_renda))
        cl.addStretch()
        botao = QPushButton("Definir renda")
        botao.clicked.connect(self._definir_renda)
        cl.addWidget(botao)
        self._orc_lay.addWidget(cabecalho)

    def _definir_renda(self):
        atual = fin().obter_renda(self.mes())
        dlg = Formulario(self, "Renda do mês", [
            ("valor", "Renda total do mês", texto(brl(atual) if atual else "", "R$ 0,00")),
        ])
        if dlg.exec() != QDialog.Accepted:
            return
        try:
            fin().definir_renda(dlg.valores()["valor"], self.mes())
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()

    def atualizar(self):
        r = fin().resumo_mes(self.mes())
        self.titulo_mes.setText(f"Resumo de {r['mes']}")
        self.receitas.definir(brl(r["receitas"]))
        # Mesmo total da aba Despesas: despesas lançadas + o que é seu nos cartões
        self.despesas.definir(brl(r["despesas_manuais"] + r["meu_cartao_total"]))
        if r["saldo"] >= 0:
            self.saldo.definir(brl(r["saldo"]), "verde")
        else:
            self.saldo.definir(brl(r["saldo"]), "branco", VERMELHO_TEXTO)
        self.meu_cartao.definir(brl(r["meu_cartao_total"]))
        self.com_emp.definir(brl(r["cartoes_com_emprestimos_total"]))
        self.receber.definir(brl(r["a_receber_de_pessoas"]))
        self._atualizar_orcamento(r)
        self.lancamentos.atualizar()
        self.caixinhas.atualizar()
