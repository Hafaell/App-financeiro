"""Telas das ferramentas: busca, backup, datas das faturas e relatório em PDF."""
from datetime import date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QFont, QPainter, QPdfWriter, QPageSize
from PySide6.QtWidgets import (QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout)
from financas.contexto import fin

from .componentes import Formulario, nova_tabela, preencher, selecionado, texto
from .formatacao import brl


class BuscaDialog(QDialog):
    """Procura um texto em todos os meses (itens, pessoas e descrições)."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Buscar")
        self.setMinimumSize(640, 460)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Buscar em todos os meses"))
        self.campo = texto("", "Ex.: mercado, Pai, Netflix")
        self.campo.returnPressed.connect(self.procurar)
        lay.addWidget(self.campo)
        self.tab = nova_tabela(["Mês", "Origem", "Descrição", "Valor", "Pessoa"])
        lay.addWidget(self.tab, 1)
        self.contagem = QLabel("")
        self.contagem.setObjectName("rotulo")
        lay.addWidget(self.contagem)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        lay.addWidget(fechar, 0, Qt.AlignmentFlag.AlignRight)

    def procurar(self):
        resultados = fin().buscar(self.campo.text())
        preencher(self.tab, [(i, [r["mes_nome"], r["origem"], r["texto"], brl(r["valor"]),
                                  r["extra"] or "—"]) for i, r in enumerate(resultados)])
        self.contagem.setText(f"{len(resultados)} resultado(s)")


class BackupDialog(QDialog):
    """Salva um backup criptografado com uma senha escolhida por você."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Backup")
        self.setMinimumWidth(420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Gerar backup"))
        self.senha = texto("", "Senha do backup (mínimo 6 caracteres)")
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.repetir = texto("", "Repita a senha")
        self.repetir.setEchoMode(QLineEdit.EchoMode.Password)
        lay.addWidget(self.senha)
        lay.addWidget(self.repetir)
        aviso = QLabel("Guarde a senha: sem ela o backup não pode ser aberto.")
        aviso.setObjectName("rotulo")
        aviso.setWordWrap(True)
        lay.addWidget(aviso)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        gerar = QPushButton("Salvar backup")
        gerar.setObjectName("primario")
        gerar.clicked.connect(self._gerar)
        botoes.addWidget(cancelar)
        botoes.addWidget(gerar)
        lay.addLayout(botoes)

    def _gerar(self):
        if self.senha.text() != self.repetir.text():
            QMessageBox.warning(self, "Backup", "As senhas não são iguais.")
            return
        nome = f"backup-controle-financeiro-{date.today().isoformat()}.cfbk"
        caminho, _ = QFileDialog.getSaveFileName(self, "Salvar backup", nome, "Backup (*.cfbk)")
        if not caminho:
            return
        try:
            fin().exportar_backup(caminho, self.senha.text())
        except ValueError as e:
            QMessageBox.warning(self, "Backup", str(e))
            return
        QMessageBox.information(self, "Backup", f"Backup salvo em:\n{caminho}")
        self.accept()


class DatasCartoesDialog(QDialog):
    """Dia de fechamento e de vencimento da fatura de cada cartão (duplo clique para editar)."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Datas das faturas")
        self.setMinimumSize(460, 360)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(22, 20, 22, 18)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Datas das faturas"))
        self.tab = nova_tabela(["Cartão", "Fechamento (dia)", "Vencimento (dia)"])
        self.tab.doubleClicked.connect(lambda _i: self.editar())
        lay.addWidget(self.tab, 1)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        lay.addWidget(fechar, 0, Qt.AlignmentFlag.AlignRight)
        self._carregar()

    def _carregar(self):
        preencher(self.tab, [(c["id"], [c["nome"], c["dia_fechamento"] or "—", c["dia_vencimento"] or "—"])
                             for c in fin().listar_cartoes()])

    def editar(self):
        id_ = selecionado(self.tab)
        c = next((x for x in fin().listar_cartoes() if x["id"] == id_), None)
        if not c:
            return
        dlg = Formulario(self, f"Datas da fatura: {c['nome']}", [
            ("fechamento", "Dia do fechamento (1 a 31)", texto(str(c["dia_fechamento"] or ""), "Ex.: 10")),
            ("vencimento", "Dia do vencimento (1 a 31)", texto(str(c["dia_vencimento"] or ""), "Ex.: 17")),
        ])
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().definir_datas_cartao(id_, v["fechamento"], v["vencimento"])
        except ValueError as e:
            QMessageBox.warning(self, "Datas", str(e))
            return
        self._carregar()


def gerar_relatorio_pdf(caminho, mes):
    """Relatório do mês em PDF: resumo, despesas, dívidas, caixinhas e assinaturas."""
    r = fin().resumo_mes(mes)
    writer = QPdfWriter(caminho)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    pintor = QPainter(writer)
    y = 80
    largura = writer.width()

    def linha(texto_, tamanho=11, negrito=False, espaco=18):
        nonlocal y
        if y > writer.height() - 120:
            writer.newPage()
            y = 80
        fonte = QFont("Segoe UI", tamanho)
        fonte.setBold(negrito)
        pintor.setFont(fonte)
        pintor.drawText(QRectF(60, y, largura - 120, espaco + 8), texto_)
        y += espaco + 6

    linha("Controle Financeiro", 18, True, 26)
    linha(f"Relatório de {r['mes']}", 13, True, 22)
    y += 8
    linha("Resumo", 13, True, 20)
    linha(f"Receitas: {brl(r['receitas'])}")
    linha(f"Despesas do mês (inclui meu cartão): {brl(r['despesas_manuais'] + r['meu_cartao_total'])}")
    linha(f"Saldo: {brl(r['saldo'])}")
    linha(f"Meu cartão: {brl(r['meu_cartao_total'])}")
    linha(f"Cartões com empréstimos: {brl(r['cartoes_com_emprestimos_total'])}")
    linha(f"A receber de pessoas: {brl(r['a_receber_de_pessoas'])}")
    if r["renda"]:
        linha(f"Renda do mês: {brl(r['renda'])}  (cartão consome {r['cartao_percentual_renda']}%)")
    y += 10
    linha("Cartões", 13, True, 20)
    for nome, valores in r["cartoes"].items():
        linha(f"{nome}: meu {brl(valores['meu_cartao'])}  ·  com empréstimos {brl(valores['com_emprestimos'])}")
    y += 10
    linha("Quem deve neste mês", 13, True, 20)
    devem = fin().quanto_me_devem(mes)
    if not devem:
        linha("Ninguém com empréstimo neste mês.")
    for d in devem:
        linha(f"{d['pessoa']}: emprestado {brl(d['emprestado'])} · pago {brl(d['ja_pago'])} · "
              f"em aberto {brl(d['em_aberto'])}")
    y += 10
    linha("Caixinhas", 13, True, 20)
    for c in fin().listar_caixinhas():
        linha(f"{c['dono']} · {c['nome']}: {brl(c['valor'])}")
    y += 10
    a = fin().assinaturas(mes)
    linha("Assinaturas (itens recorrentes)", 13, True, 20)
    linha(f"Total por mês: {brl(a['total_mes'])}  ·  por ano: {brl(a['total_ano'])}")
    pintor.end()
    return caminho
