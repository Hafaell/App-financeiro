"""Página Visão geral: os números do mês, o orçamento e os atalhos para lançar."""
from datetime import date

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.componentes import Formulario, Kpi, texto
from controle_financeiro.ui.dialogos import CategoriasDialog
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina
from controle_financeiro.ui.tema import VERMELHO_TEXTO


class VisaoPage(Pagina):
    """Visão geral: resumo do mês e orçamento. As listas ficam nas suas próprias páginas;
    clicar em um card abre a página do assunto."""

    def __init__(self, janela):
        super().__init__(janela)
        conteudo = QWidget()
        lay = QVBoxLayout(conteudo)
        lay.setSpacing(18)
        lay.setContentsMargins(0, 0, 8, 0)
        self.alerta = QLabel()
        self.alerta.setObjectName("alerta")
        self.alerta.setWordWrap(True)
        self.alerta.hide()
        lay.addWidget(self.alerta)

        # Título do resumo e, na mesma linha, os lançamentos mais usados no dia a dia
        cabecalho = QHBoxLayout()
        cabecalho.setSpacing(10)
        self.titulo_mes = QLabel()
        self.titulo_mes.setObjectName("secao")
        cabecalho.addWidget(self.titulo_mes)
        cabecalho.addStretch()
        for rotulo, acao, principal in (
                ("Nova receita", lambda: janela.lancamentos.receitas.adicionar(), False),
                ("Nova despesa", lambda: janela.lancamentos.despesas.adicionar(), False),
                ("Nova compra", lambda: janela.cartoes.nova(), True)):
            botao = QPushButton(rotulo)
            if principal:
                botao.setObjectName("primario")
                botao.setToolTip("Ctrl+N")
            botao.clicked.connect(acao)
            cabecalho.addWidget(botao)
        lay.addLayout(cabecalho)

        # Cards em grade de 3 colunas: quebram de linha em vez de empurrar a tela para o lado
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(16)

        def abrir_lancamentos():
            janela.ir_para(janela.lancamentos)

        def abrir_transacoes():
            janela.ir_para(janela.cartoes)

        self.receitas = Kpi("Receitas", "verde", "Entradas que você recebeu no mês",
                            abrir_lancamentos, "Abrir Receitas e despesas")
        self.despesas = Kpi("Despesas do mês", "amarelo",
                            "Despesas lançadas, mais o que é seu nos cartões",
                            abrir_lancamentos, "Abrir Receitas e despesas")
        self.saldo = Kpi("Saldo", "verde", "Receitas, menos o total de despesas")
        self.meu_cartao = Kpi("Meu cartão no mês", "azul",
                              "Compras suas no cartão, sem empréstimos",
                              abrir_transacoes, "Abrir Transações")
        self.com_emp = Kpi("Cartões com empréstimos", "branco",
                           "Total nos cartões, incluindo o que as pessoas devem",
                           abrir_transacoes, "Abrir Transações")
        self.receber = Kpi("A receber de pessoas", "azul",
                           "Quanto as pessoas devem neste mês",
                           lambda: janela.ir_para(janela.deve), "Abrir Empréstimos")
        self._cards = [self.receitas, self.despesas, self.saldo,
                       self.meu_cartao, self.com_emp, self.receber]
        self._grade = grade
        self._colunas = None
        lay.addLayout(grade)

        # Orçamento: uma barra de uso por categoria com limite, e a renda do mês
        self.orcamento_card = QFrame()
        self.orcamento_card.setObjectName("kpi")
        orc = QVBoxLayout(self.orcamento_card)
        orc.setContentsMargins(22, 18, 22, 18)
        orc.setSpacing(12)
        topo = QHBoxLayout()
        topo.setSpacing(10)
        titulo = QLabel("Orçamento do mês")
        titulo.setObjectName("secao")
        topo.addWidget(titulo)
        topo.addStretch()
        categorias = QPushButton("Categorias e limites")
        categorias.clicked.connect(self._abrir_categorias)
        renda = QPushButton("Definir renda")
        renda.clicked.connect(self._definir_renda)
        topo.addWidget(categorias)
        topo.addWidget(renda)
        orc.addLayout(topo)
        self._barras = QVBoxLayout()
        self._barras.setSpacing(12)
        orc.addLayout(self._barras)
        self.renda = QLabel()
        self.renda.setObjectName("rotulo")
        self.renda.setWordWrap(True)
        orc.addWidget(self.renda)
        lay.addWidget(self.orcamento_card)
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
        for c in range(3):
            self._grade.setColumnStretch(c, 1 if c < colunas else 0)

    def _atualizar_alertas(self):
        avisos = fin().alertas_faturas(date.today(), 5)
        if not avisos:
            self.alerta.hide()
            return
        textos = []
        for a in avisos:
            acao = "fecha" if a["tipo"] == "fecha" else "vence"
            quando = "hoje" if a["faltam"] == 0 else f"em {a['faltam']} dia(s)"
            textos.append(f"Fatura do {a['cartao']} {acao} {quando} ({a['data']})")
        self.alerta.setText("\n".join(textos))
        self.alerta.show()

    def _atualizar_orcamento(self, r):
        """Orçamento de cada categoria (barra de uso) e renda do mês."""
        while self._barras.count():
            item = self._barras.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        gastos = fin().gasto_por_categoria(self.mes())
        limites = [c for c in fin().listar_categorias() if c["orcamento"] > 0]
        if not limites:
            aviso = QLabel("Nenhuma categoria tem limite mensal ainda. Defina os limites em "
                           "Categorias e limites para acompanhar o uso aqui.")
            aviso.setObjectName("rotulo")
            aviso.setWordWrap(True)
            self._barras.addWidget(aviso)
        for c in limites:
            gasto = gastos.get(c["id"], 0.0)
            uso = gasto / c["orcamento"] * 100
            linha = QWidget()
            linha.setObjectName("transparente")
            ll = QVBoxLayout(linha)
            ll.setContentsMargins(0, 0, 0, 0)
            ll.setSpacing(5)
            textos = QHBoxLayout()
            nome = QLabel(c["nome"])
            nome.setObjectName("forte")
            if gasto > c["orcamento"]:
                situacao = QLabel(f"{brl(gasto)} de {brl(c['orcamento'])}: "
                                  f"passou {brl(gasto - c['orcamento'])}")
                situacao.setStyleSheet(f"color: {VERMELHO_TEXTO}; font-weight: 600;")
            else:
                situacao = QLabel(f"{brl(gasto)} de {brl(c['orcamento'])}")
                situacao.setObjectName("rotulo")
            textos.addWidget(nome)
            textos.addStretch()
            textos.addWidget(situacao)
            barra = QProgressBar()
            barra.setRange(0, 100)
            barra.setValue(int(round(min(uso, 100))))
            barra.setTextVisible(False)
            barra.setProperty("nivel", "passou" if uso > 100 else ("alerta" if uso >= 80 else "normal"))
            ll.addLayout(textos)
            ll.addWidget(barra)
            self._barras.addWidget(linha)
        renda = r.get("renda")
        if renda:
            self.renda.setText(f"Renda do mês: {brl(renda)}. O cartão consome "
                               f"{str(r['cartao_percentual_renda']).replace('.', ',')}% da renda.")
        else:
            self.renda.setText("Renda do mês não informada. Com ela, o app mostra quanto da renda "
                               "o cartão consome.")

    def _abrir_categorias(self):
        CategoriasDialog(self).exec()
        self.mudou()

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
        self._atualizar_alertas()
        self.receitas.definir(brl(r["receitas"]))
        # Mesmo total da página Receitas e despesas: despesas lançadas + o que é seu nos cartões
        self.despesas.definir(brl(r["despesas_manuais"] + r["meu_cartao_total"]))
        if r["saldo"] >= 0:
            self.saldo.definir(brl(r["saldo"]), "verde")
        else:
            self.saldo.definir(brl(r["saldo"]), "branco", VERMELHO_TEXTO)
        self.meu_cartao.definir(brl(r["meu_cartao_total"]))
        self.com_emp.definir(brl(r["cartoes_com_emprestimos_total"]))
        self.receber.definir(brl(r["a_receber_de_pessoas"]))
        self._atualizar_orcamento(r)
