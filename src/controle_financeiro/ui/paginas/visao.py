"""Página Visão geral: o saldo do mês em destaque, os outros números, o orçamento e os atalhos."""
from datetime import date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QPainter, QPainterPath
from PySide6.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QVBoxLayout, QWidget,
)
from controle_financeiro.dados.contexto import fin
from controle_financeiro.nucleo.utilidades import MESES_EXIBIR
from controle_financeiro.ui.componentes import FaixaNumeros, Formulario, Metrica, texto
from controle_financeiro.ui.dialogos import CategoriasDialog
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina
from controle_financeiro.ui.tema import DESPESA, MENTA, SEM_CATEGORIA_COR


def _pct(valor):
    return f"{valor:.0f}%"


class BarraUso(QWidget):
    """Barra fina sobre o painel escuro: quanto das receitas as despesas já usaram."""

    def __init__(self):
        super().__init__()
        self.uso = None  # percentual; None = sem receitas para comparar
        self.setFixedHeight(10)

    def definir(self, uso):
        self.uso = uso
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#2A5B58"))
        p.drawRoundedRect(QRectF(self.rect()), 5, 5)
        if self.uso:
            cor = MENTA if self.uso < 80 else (DESPESA if self.uso <= 100 else "#FF8A75")
            largura = self.width() * min(self.uso, 100) / 100
            p.setBrush(QColor(cor))
            p.drawRoundedRect(QRectF(0, 0, max(largura, 10), self.height()), 5, 5)
        p.end()


class BarraCategorias(QWidget):
    """Uma barra só, dividida em pedaços do tamanho do gasto de cada categoria, na cor dela."""

    def __init__(self):
        super().__init__()
        self.partes = []  # [(valor, cor)]
        self.setFixedHeight(14)

    def definir(self, partes):
        self.partes = partes
        self.update()

    def paintEvent(self, evento):
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setPen(Qt.PenStyle.NoPen)
        p.setBrush(QColor("#E5ECE9"))
        p.drawRoundedRect(QRectF(self.rect()), 7, 7)
        total = sum(v for v, _ in self.partes)
        if total > 0:
            # recorta as pontas arredondadas e pinta cada pedaço com 2 px de folga entre eles
            caminho = QPainterPath()
            caminho.addRoundedRect(QRectF(self.rect()), 7, 7)
            p.setClipPath(caminho)
            x = 0.0
            for valor, cor in self.partes:
                largura = self.width() * valor / total
                p.setBrush(QColor(cor))
                p.drawRect(QRectF(x, 0, max(largura - 2, 1), self.height()))
                x += largura
        p.end()


class Fluxo(QFrame):
    """Entrou ou saiu no mês, dentro do painel de saldo. Clicar abre Receitas e despesas."""

    def __init__(self, rotulo, cor, ao_clicar):
        super().__init__()
        self.setObjectName("fluxo")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setToolTip("Abrir Receitas e despesas")
        self._ao_clicar = ao_clicar
        lay = QVBoxLayout(self)
        lay.setContentsMargins(14, 10, 14, 10)
        lay.setSpacing(2)
        topo = QHBoxLayout()
        topo.setSpacing(8)
        ponto = QLabel()
        ponto.setFixedSize(8, 8)
        ponto.setStyleSheet(f"background: {cor}; border-radius: 4px;")
        nome = QLabel(rotulo)
        nome.setObjectName("fluxoRotulo")
        topo.addWidget(ponto)
        topo.addWidget(nome)
        topo.addStretch()
        self.valor = QLabel("—")
        self.valor.setObjectName("fluxoValor")
        self.detalhe = QLabel("")
        self.detalhe.setObjectName("fluxoRotulo")
        lay.addLayout(topo)
        lay.addWidget(self.valor)
        lay.addWidget(self.detalhe)

    def mouseReleaseEvent(self, evento):
        if evento.button() == Qt.MouseButton.LeftButton and self.rect().contains(evento.position().toPoint()):
            self._ao_clicar()
        super().mouseReleaseEvent(evento)

    def definir(self, valor, detalhe=""):
        self.valor.setText(valor)
        self.detalhe.setText(detalhe)
        self.detalhe.setVisible(bool(detalhe))


class VisaoPage(Pagina):
    """Visão geral: o saldo do mês em destaque e, abaixo, os outros números e o orçamento.
    As listas ficam nas suas próprias páginas; clicar em um número abre a página do assunto."""

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

        def abrir_lancamentos():
            janela.ir_para(janela.lancamentos)

        def abrir_transacoes():
            janela.ir_para(janela.cartoes)

        # Painel de saldo: o número que mais importa no mês, com o que entrou e o que saiu
        painel = QFrame()
        painel.setObjectName("saldo")
        pl = QHBoxLayout(painel)
        pl.setContentsMargins(30, 26, 22, 26)
        pl.setSpacing(22)
        esquerda = QVBoxLayout()
        esquerda.setSpacing(6)
        self.titulo_mes = QLabel()
        self.titulo_mes.setObjectName("saldoRotulo")
        self.saldo = QLabel("—")
        self.saldo.setObjectName("saldoValor")
        self.frase = QLabel()
        self.frase.setObjectName("saldoFrase")
        self.frase.setWordWrap(True)
        self.uso = BarraUso()
        esquerda.addWidget(self.titulo_mes)
        esquerda.addWidget(self.saldo)
        esquerda.addStretch()
        esquerda.addWidget(self.frase)
        esquerda.addSpacing(4)
        esquerda.addWidget(self.uso)
        pl.addLayout(esquerda, 3)
        divisor = QFrame()
        divisor.setObjectName("saldoDivisor")
        divisor.setFixedWidth(1)
        pl.addWidget(divisor)
        direita = QVBoxLayout()
        direita.setSpacing(4)
        self.receitas = Fluxo("Entrou", MENTA, abrir_lancamentos)
        self.despesas = Fluxo("Saiu", DESPESA, abrir_lancamentos)
        direita.addWidget(self.receitas)
        direita.addWidget(self.despesas)
        pl.addLayout(direita, 2)
        lay.addWidget(painel)

        # Lançamentos mais usados no dia a dia
        acoes = QHBoxLayout()
        acoes.setSpacing(10)
        for rotulo, acao, principal in (
                ("Nova compra", lambda: janela.cartoes.nova(), True),
                ("Nova despesa", lambda: janela.lancamentos.despesas.adicionar(), False),
                ("Nova receita", lambda: janela.lancamentos.receitas.adicionar(), False)):
            botao = QPushButton(rotulo)
            if principal:
                botao.setObjectName("primario")
                botao.setToolTip("Ctrl+N")
            botao.clicked.connect(acao)
            acoes.addWidget(botao)
        acoes.addStretch()
        lay.addLayout(acoes)

        # Cartões e empréstimos numa faixa só
        self.meu_cartao = Metrica("Meu cartão no mês", "Compras suas no cartão, sem empréstimos",
                                  "normal", abrir_transacoes, "Abrir Transações")
        self.com_emp = Metrica("Cartões com empréstimos",
                               "Total nos cartões, incluindo o que as pessoas devem",
                               "normal", abrir_transacoes, "Abrir Transações")
        self.receber = Metrica("A receber de pessoas", "Quanto as pessoas devem neste mês",
                               "positivo", lambda: janela.ir_para(janela.deve), "Abrir Empréstimos")
        lay.addWidget(FaixaNumeros(self.meu_cartao, self.com_emp, self.receber))

        # Para onde foi o dinheiro: todas as categorias, com ou sem limite
        self.categorias_card = QFrame()
        self.categorias_card.setObjectName("painel")
        cc = QVBoxLayout(self.categorias_card)
        cc.setContentsMargins(24, 20, 24, 20)
        cc.setSpacing(14)
        titulo_cat = QLabel("Para onde foi o dinheiro")
        titulo_cat.setObjectName("secao")
        cc.addWidget(titulo_cat)
        self.barra_categorias = BarraCategorias()
        cc.addWidget(self.barra_categorias)
        self._legenda = QGridLayout()
        self._legenda.setHorizontalSpacing(10)
        self._legenda.setVerticalSpacing(8)
        cc.addLayout(self._legenda)
        lay.addWidget(self.categorias_card)

        # Orçamento: uma barra de uso por categoria com limite, e a renda do mês
        self.orcamento_card = QFrame()
        self.orcamento_card.setObjectName("painel")
        orc = QVBoxLayout(self.orcamento_card)
        orc.setContentsMargins(24, 20, 24, 20)
        orc.setSpacing(14)
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
        self._barras.setSpacing(14)
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
            ll.setSpacing(6)
            textos = QHBoxLayout()
            textos.setSpacing(8)
            ponto = QLabel()
            ponto.setFixedSize(10, 10)
            ponto.setStyleSheet(f"background: {c['cor']}; border-radius: 5px;")  # cor da categoria
            nome = QLabel(c["nome"])
            nome.setObjectName("forte")
            if gasto > c["orcamento"]:
                situacao = QLabel(f"{brl(gasto)} de {brl(c['orcamento'])}, passou {brl(gasto - c['orcamento'])}")
                situacao.setObjectName("excedido")
            else:
                situacao = QLabel(f"{brl(gasto)} de {brl(c['orcamento'])} ({_pct(uso)})")
                situacao.setObjectName("rotulo")
            textos.addWidget(ponto)
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

    def _atualizar_categorias(self):
        """Gasto de cada categoria (compras suas e despesas), da maior para a menor."""
        while self._legenda.count():
            item = self._legenda.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        gastos = fin().gasto_por_categoria(self.mes())
        cores = {c["id"]: (c["nome"], c["cor"]) for c in fin().listar_categorias()}
        itens = []
        for id_, valor in gastos.items():
            if valor <= 0:
                continue
            nome, cor = cores.get(id_, ("Sem categoria", SEM_CATEGORIA_COR))
            itens.append((valor, nome, cor))
        itens.sort(key=lambda x: -x[0])
        total = sum(v for v, _, _ in itens)
        self.barra_categorias.definir([(v, cor) for v, _, cor in itens])
        if not itens:
            vazio = QLabel("Nenhum gasto neste mês ainda.")
            vazio.setObjectName("rotulo")
            self._legenda.addWidget(vazio, 0, 0)
            return
        metade = (len(itens) + 1) // 2  # duas colunas: maiores à esquerda
        for i, (valor, nome, cor) in enumerate(itens):
            linha, coluna = (i, 0) if i < metade else (i - metade, 5)
            ponto = QLabel()
            ponto.setFixedSize(10, 10)
            ponto.setStyleSheet(f"background: {cor}; border-radius: 5px;")  # cor da categoria
            rotulo = QLabel(nome)
            pct = QLabel(f"{valor / total * 100:.0f}%")
            pct.setObjectName("rotulo")
            quanto = QLabel(brl(valor))
            quanto.setObjectName("forte")
            self._legenda.addWidget(ponto, linha, coluna)
            self._legenda.addWidget(rotulo, linha, coluna + 1)
            self._legenda.addWidget(pct, linha, coluna + 2, Qt.AlignmentFlag.AlignRight)
            self._legenda.addWidget(quanto, linha, coluna + 3, Qt.AlignmentFlag.AlignRight)
        self._legenda.setColumnStretch(1, 1)
        self._legenda.setColumnMinimumWidth(4, 36)  # respiro entre as duas colunas
        self._legenda.setColumnStretch(6, 1)

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
        mes = MESES_EXIBIR[int(self.mes().split("-")[1]) - 1].lower()
        self.titulo_mes.setText(f"Saldo de {mes}")
        self._atualizar_alertas()
        receitas = r["receitas"]
        # Mesmo total da página Receitas e despesas: despesas lançadas + o que é seu nos cartões
        despesas = r["despesas_manuais"] + r["meu_cartao_total"]
        self.saldo.setText(brl(r["saldo"]))
        self.saldo.setProperty("negativo", "true" if r["saldo"] < 0 else "false")
        self.saldo.style().unpolish(self.saldo)
        self.saldo.style().polish(self.saldo)
        self.receitas.definir(brl(receitas))
        self.despesas.definir(brl(despesas), f"{brl(r['meu_cartao_total'])} nos seus cartões")
        if receitas > 0:
            uso = despesas / receitas * 100
            self.uso.definir(uso)
            if uso <= 100:
                self.frase.setText(f"As despesas usaram {_pct(uso)} do que entrou.")
            else:
                self.frase.setText(f"As despesas passaram as receitas em {brl(despesas - receitas)}.")
        else:
            self.uso.definir(None)
            self.frase.setText("Nada lançado neste mês ainda." if despesas == 0 else
                               "Sem receitas lançadas neste mês: lance-as para ver quanto sobra.")
        self.meu_cartao.definir(brl(r["meu_cartao_total"]))
        self.com_emp.definir(brl(r["cartoes_com_emprestimos_total"]))
        self.receber.definir(brl(r["a_receber_de_pessoas"]))
        self._atualizar_categorias()
        self._atualizar_orcamento(r)
