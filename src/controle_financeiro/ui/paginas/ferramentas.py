"""Ferramentas: busca, backup, datas das faturas, relatório PDF, meses, virada de mês e atalhos."""
from PySide6.QtWidgets import QFrame, QGridLayout, QLabel, QPushButton, QVBoxLayout

from controle_financeiro.ui.paginas.base import Pagina

# Atalhos de teclado do app (ligados em ui/janela.py e nas tabelas)
ATALHOS = [
    ("Ctrl+1 a Ctrl+9", "Abrir cada item do menu, na ordem"),
    ("Ctrl+N", "Novo lançamento da página aberta"),
    ("Ctrl+F", "Buscar (em Transações, filtra a tabela)"),
    ("Enter", "Editar a linha selecionada"),
    ("Delete", "Apagar a linha selecionada"),
    ("Alt+← e Alt+→", "Mês anterior e próximo mês"),
    ("F5", "Atualizar os dados"),
]


class FerramentasPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(16)
        grade = QGridLayout()
        grade.setHorizontalSpacing(16)
        grade.setVerticalSpacing(16)
        itens = [
            ("Buscar", "Procurar um item, pessoa ou descrição em todos os meses.",
             "Abrir a busca", janela.abrir_busca),
            ("Relatório PDF", "Gerar o resumo do mês em PDF.", "Gerar o PDF", janela.exportar_pdf),
            ("Backup", "Salvar todos os dados em um arquivo protegido por senha.",
             "Fazer backup", janela.abrir_backup),
            ("Datas das faturas", "Dia de fechamento e vencimento de cada cartão.",
             "Ver as datas", janela.abrir_datas),
            ("Meses abertos", "Ver os meses e apagar os antigos.", "Ver os meses", janela.gerenciar_meses),
            ("Virar o mês", "Abrir o mês seguinte, copiando o atual.", "Virar o mês", janela.virar_mes),
        ]
        for i, (titulo_btn, descricao, rotulo_botao, acao) in enumerate(itens):
            caixa = QFrame()
            caixa.setObjectName("kpi")
            cl = QVBoxLayout(caixa)
            cl.setContentsMargins(20, 18, 20, 18)
            cl.setSpacing(8)
            nome = QLabel(titulo_btn)
            nome.setObjectName("forte")
            cl.addWidget(nome)
            desc = QLabel(descricao)
            desc.setObjectName("rotulo")
            desc.setWordWrap(True)
            cl.addWidget(desc)
            cl.addStretch()
            botao = QPushButton(rotulo_botao)
            if titulo_btn == "Virar o mês":
                botao.setObjectName("primario")
            botao.clicked.connect(acao)
            cl.addWidget(botao, 0)
            grade.addWidget(caixa, i // 3, i % 3)
        for c in range(3):
            grade.setColumnStretch(c, 1)
        lay.addLayout(grade)

        # Atalhos de teclado, em duas colunas
        atalhos = QFrame()
        atalhos.setObjectName("kpi")
        al = QVBoxLayout(atalhos)
        al.setContentsMargins(20, 18, 20, 18)
        al.setSpacing(12)
        titulo = QLabel("Atalhos do teclado")
        titulo.setObjectName("forte")
        al.addWidget(titulo)
        lista = QGridLayout()
        lista.setHorizontalSpacing(14)
        lista.setVerticalSpacing(8)
        metade = (len(ATALHOS) + 1) // 2
        for i, (teclas, efeito) in enumerate(ATALHOS):
            coluna = 0 if i < metade else 3
            linha = i if i < metade else i - metade
            tecla = QLabel(teclas)
            tecla.setObjectName("forte")
            descricao = QLabel(efeito)
            descricao.setObjectName("rotulo")
            lista.addWidget(tecla, linha, coluna)
            lista.addWidget(descricao, linha, coluna + 1)
        lista.setColumnMinimumWidth(2, 28)  # respiro entre as duas colunas
        lista.setColumnStretch(1, 1)
        lista.setColumnStretch(4, 1)
        al.addLayout(lista)
        lay.addWidget(atalhos)
        lay.addStretch()
