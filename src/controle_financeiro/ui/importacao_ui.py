"""Importação de extrato (CSV ou OFX): arraste o arquivo ou escolha no computador,
confira cada linha e só então grave."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QComboBox, QFileDialog, QHBoxLayout, QHeaderView, QLineEdit,
                               QLabel, QMessageBox, QPushButton, QTableWidget, QTableWidgetItem,
                               QVBoxLayout)
from controle_financeiro.dados.contexto import fin

from controle_financeiro.nucleo.importacao import banco_do_arquivo
from controle_financeiro.ui.componentes import ComboPessoa
from controle_financeiro.ui.formatacao import brl, categorias_opcoes, id_categoria, nomes_cartoes
from controle_financeiro.ui.paginas.base import Pagina

DESPESAS = "Despesas (à parte)"


class ZonaArrastar(QLabel):
    """Área para arrastar o arquivo do extrato; clicar nela abre a escolha de arquivo."""

    def __init__(self, ao_receber, ao_clicar):
        super().__init__("Arraste o extrato (CSV ou OFX) aqui\nou clique para escolher no computador")
        self.ao_receber = ao_receber
        self.ao_clicar = ao_clicar
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(120)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setAcceptDrops(True)
        self.setStyleSheet("QLabel { border: 2px dashed #9DB8F2; border-radius: 14px; background: #FFFFFF; "
                           "color: #5A6B8C; font-size: 11pt; }")

    def dragEnterEvent(self, evento):
        if evento.mimeData().hasUrls():
            evento.acceptProposedAction()

    def dropEvent(self, evento):
        urls = evento.mimeData().urls()
        if urls:
            self.ao_receber(urls[0].toLocalFile())

    def mousePressEvent(self, evento):
        self.ao_clicar()


class ImportarPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        self.itens = []
        lay = QVBoxLayout(self)
        lay.setSpacing(12)
        titulo = QLabel("Importar extrato")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        self.zona = ZonaArrastar(self._carregar, self.escolher)
        lay.addWidget(self.zona)

        linha = QHBoxLayout()
        self.arquivo = QLabel("Nenhum arquivo carregado")
        self.arquivo.setObjectName("rotulo")
        linha.addWidget(self.arquivo)
        linha.addStretch()
        linha.addWidget(QLabel("Destino:"))
        self.destino = QComboBox()
        self.destino.addItems([DESPESAS] + nomes_cartoes())
        linha.addWidget(self.destino)
        lay.addLayout(linha)

        self.tabela = QTableWidget(0, 7)
        self.tabela.setHorizontalHeaderLabels(["Importar", "Data", "Descrição", "Parcela", "Valor",
                                               "Pessoa (empréstimo)", "Categoria"])
        self.tabela.verticalHeader().setVisible(False)
        self.tabela.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.tabela.setAlternatingRowColors(True)
        self.tabela.setShowGrid(False)
        # Colunas curtas se ajustam ao conteúdo (nada cortado); a descrição usa o espaço que sobrar
        # e quebra em várias linhas, com a linha crescendo para mostrar o texto inteiro.
        cabecalho = self.tabela.horizontalHeader()
        cabecalho.setMinimumSectionSize(60)
        cabecalho.setStretchLastSection(False)
        for coluna in (0, 1, 3, 4, 5, 6):
            cabecalho.setSectionResizeMode(coluna, QHeaderView.ResizeMode.ResizeToContents)
        cabecalho.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.tabela.setWordWrap(True)
        self.tabela.verticalHeader().setMinimumSectionSize(40)
        self.tabela.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        self.tabela.setMinimumHeight(340)
        lay.addWidget(self.tabela, 1)

        rodape = QHBoxLayout()
        self.resumo = QLabel("")
        self.resumo.setObjectName("rotulo")
        rodape.addWidget(self.resumo)
        rodape.addStretch()
        self.botao = QPushButton("Importar selecionados")
        self.botao.setObjectName("primario")
        self.botao.setEnabled(False)
        self.botao.clicked.connect(self.importar)
        rodape.addWidget(self.botao)
        lay.addLayout(rodape)

    def escolher(self):
        caminho, _ = QFileDialog.getOpenFileName(self, "Escolher extrato", "",
                                                 "Extratos (*.csv *.ofx *.txt);;Todos (*.*)")
        if caminho:
            self._carregar(caminho)

    def _carregar(self, caminho):
        try:
            with open(caminho, "rb") as f:
                conteudo = f.read()
            self.itens = fin().ler_extrato(caminho, conteudo, self.mes())
        except (ValueError, OSError) as e:
            QMessageBox.warning(self, "Extrato", str(e))
            return
        self.arquivo.setText(caminho.replace("\\", "/").split("/")[-1])
        sugerido = banco_do_arquivo(caminho)
        if sugerido and sugerido in nomes_cartoes():
            self.destino.setCurrentText(sugerido)
        self._preencher()

    def _preencher(self):
        self.tabela.setRowCount(0)
        for linha, it in enumerate(self.itens):
            self.tabela.insertRow(linha)
            marca = QTableWidgetItem("")
            marca.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            marca.setCheckState(Qt.CheckState.Checked if it["situacao"] == "Novo" else Qt.CheckState.Unchecked)
            self.tabela.setItem(linha, 0, marca)
            data = it["data"][8:] + "/" + it["data"][5:7] + "/" + it["data"][:4]
            for col, valor in ((1, data), (2, it["descricao"]), (3, it["parcelas"]), (4, brl(it["valor"]))):
                cel = QTableWidgetItem(valor)
                cel.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                cel.setToolTip(valor)  # texto completo ao passar o mouse
                self.tabela.setItem(linha, col, cel)
            pessoa = ComboPessoa()
            pessoa.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            self.tabela.setCellWidget(linha, 5, pessoa)
            combo = QComboBox()
            combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContents)
            combo.addItems(categorias_opcoes())
            self.tabela.setCellWidget(linha, 6, combo)
        self.botao.setEnabled(bool(self.itens))
        novos = sum(1 for i in self.itens if i["situacao"] == "Novo")
        self.resumo.setText(f"{len(self.itens)} linha(s) no arquivo · {novos} nova(s) marcada(s)")

    def _selecionados(self):
        escolhidos = []
        for linha, it in enumerate(self.itens):
            if self.tabela.item(linha, 0).checkState() == Qt.CheckState.Checked:
                cat = self.tabela.cellWidget(linha, 6).currentText()
                pessoa = self.tabela.cellWidget(linha, 5).currentText()
                escolhidos.append({"data": it["data"], "descricao": it["descricao"],
                                   "parcelas": it["parcelas"], "valor": it["valor"],
                                   "pessoa": pessoa or ".", "categoria_id": id_categoria(cat)})
        return escolhidos

    def importar(self):
        escolhidos = self._selecionados()
        if not escolhidos:
            QMessageBox.information(self, "Importar", "Marque ao menos uma linha.")
            return
        destino = self.destino.currentText()
        destino = "despesas" if destino == DESPESAS else destino
        alvo = "Despesas" if destino == "despesas" else "o cartão " + destino
        pergunta = f"Importar {len(escolhidos)} lançamento(s) para {alvo} em {fin().nome_mes(self.mes())}?"
        if QMessageBox.question(self, "Importar extrato", pergunta) != QMessageBox.Yes:
            return
        try:
            feitos = fin().importar_extrato(escolhidos, destino, self.mes())
        except ValueError as e:
            QMessageBox.warning(self, "Importar", str(e))
            return
        QMessageBox.information(self, "Importar", f"{feitos} lançamento(s) importado(s).")
        self.itens = []
        self.tabela.setRowCount(0)
        self.botao.setEnabled(False)
        self.resumo.setText("")
        self.arquivo.setText("Nenhum arquivo carregado")
        self.mudou()
