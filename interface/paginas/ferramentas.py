"""Ferramentas: busca, backup, datas das faturas, relatório PDF, meses e virada de mês."""
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout

from .base import Pagina


class FerramentasPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        titulo = QLabel("Ferramentas")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(16)
        itens = [
            ("Buscar", "Procurar um item, pessoa ou descrição em todos os meses.", janela.abrir_busca),
            ("Relatório PDF", "Gerar o resumo do mês em PDF.", janela.exportar_pdf),
            ("Backup", "Salvar todos os dados em um arquivo protegido por senha.", janela.abrir_backup),
            ("Datas das faturas", "Dia de fechamento e vencimento de cada cartão.", janela.abrir_datas),
            ("Meses abertos", "Ver os meses e apagar os antigos.", janela.gerenciar_meses),
            ("Virar o mês", "Abrir o mês seguinte, copiando o atual.", janela.virar_mes),
        ]
        for i, (titulo_btn, descricao, acao) in enumerate(itens):
            caixa = QFrame()
            caixa.setObjectName("kpi")
            cl = QVBoxLayout(caixa)
            cl.setContentsMargins(20, 18, 20, 18)
            cl.setSpacing(8)
            cl.addWidget(QLabel(f"<b>{titulo_btn}</b>"))
            desc = QLabel(descricao)
            desc.setObjectName("rotulo")
            desc.setWordWrap(True)
            cl.addWidget(desc)
            botao = QPushButton("Abrir")
            if titulo_btn == "Virar o mês":
                botao.setObjectName("primario")
            botao.clicked.connect(acao)
            cl.addWidget(botao, 0)
            grade.addWidget(caixa, i // 3, i % 3)
        for c in range(3):
            grade.setColumnStretch(c, 1)
        lay.addLayout(grade)
        lay.addStretch()
