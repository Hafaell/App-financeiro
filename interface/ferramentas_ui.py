"""Telas das ferramentas: busca, backup, datas das faturas e relatório em PDF."""
from datetime import date

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QBrush, QColor, QFont, QPainter, QPdfWriter, QPageSize, QPen
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


# Layout do relatório PDF (medidas em pontos; A4 = 595 x 842)
REL_MARGEM = 40
REL_LARGURA = 595 - 2 * REL_MARGEM
REL_PAD = 14
REL_TITULO = 22
REL_LINHA = 20
REL_FAIXA = 40
REL_GAP = 12


def gerar_relatorio_pdf(caminho, mes):
    """Relatório do mês em PDF, no modelo aprovado: cabeçalho, resumo, despesas do Rafael,
    dívidas de outras pessoas e limitação mensal."""
    app = fin()
    r = app.resumo_mes(mes)
    cartoes = list(r["cartoes"].keys())
    total_despesas = round(r["despesas_manuais"] + r["meu_cartao_total"], 2)
    lancadas = app.lancamentos.listar("despesas", mes)

    # Dívidas de outras pessoas: {pessoa: {cartao: valor}} (compras com pessoa preenchida)
    terceiros = {}
    for c in app.compras.listar(None, mes):
        if c["emprestimo"]:
            por_cartao = terceiros.setdefault(c["pessoa"], {})
            por_cartao[c["cartao"]] = por_cartao.get(c["cartao"], 0) + c["valor_parcela"]
    total_terceiros = round(sum(sum(v.values()) for v in terceiros.values()), 2)

    writer = QPdfWriter(caminho)
    writer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
    writer.setResolution(72)
    pintor = QPainter(writer)
    topo = 36
    limite = writer.height() - 36
    y = topo

    AZUL, TEXTO, CINZA = "#2563EB", "#1F2937", "#6B7280"
    x_int = REL_MARGEM + REL_PAD
    larg_int = REL_LARGURA - 2 * REL_PAD

    def caixa(yy, altura, x, largura, fundo="#FFFFFF", borda="#E5E7EB", raio=10):
        pintor.setPen(QPen(QColor(borda), 1))
        pintor.setBrush(QBrush(QColor(fundo)))
        pintor.drawRoundedRect(QRectF(x, yy, largura, altura), raio, raio)

    def txt(yy, x, largura, t, tam=10, negrito=False, cor=TEXTO,
            alinha=Qt.AlignLeft, altura=REL_LINHA, quebra=False):
        fonte = QFont("Segoe UI", tam)
        fonte.setBold(negrito)
        pintor.setFont(fonte)
        pintor.setPen(QColor(cor))
        flags = int(alinha | Qt.AlignVCenter)
        if quebra:
            flags |= int(Qt.TextWordWrap)
        pintor.drawText(QRectF(x, yy, largura, altura), flags, t)

    def linha(yy, rotulo, valor, negrito=False, cor=TEXTO):
        txt(yy, x_int, larg_int * 0.7, rotulo, 10, negrito, cor)
        txt(yy, x_int, larg_int, valor, 10, True, cor, Qt.AlignRight)

    def faixa(yy, rotulo, valor, fundo, borda, cor):
        x = x_int + 8
        largura = larg_int - 16
        caixa(yy, REL_FAIXA, x, largura, fundo, borda, raio=8)
        txt(yy, x + 12, largura * 0.6, rotulo, 10, True, cor, altura=REL_FAIXA)
        txt(yy, x + 12, largura - 24, valor, 13, True, cor, Qt.AlignRight, altura=REL_FAIXA)

    def garantir(altura):
        nonlocal y
        if y + altura > limite:
            writer.newPage()
            y = topo

    # Cabeçalho azul
    altura_topo = 84
    garantir(altura_topo)
    caixa(y, altura_topo, REL_MARGEM, REL_LARGURA, AZUL, AZUL, raio=14)
    txt(y + 12, x_int, larg_int, "CONTROLE FINANCEIRO", 8, False, "#DBEAFE", altura=14)
    txt(y + 26, x_int, larg_int, "Relatório financeiro", 20, True, "#FFFFFF", altura=28)
    txt(y + 54, x_int, larg_int, "Dívidas e despesas consolidadas", 10, False, "#DBEAFE", altura=16)
    txt(y + 68, x_int, larg_int, f"Mês consultado: {r['mes']}", 9, False, "#DBEAFE", altura=14)
    y += altura_topo + REL_GAP

    def secao(titulo, linhas, rodape=None):
        """Cartão com título, linhas (rótulo, valor) e, opcionalmente, uma faixa (rótulo, valor, cores)."""
        nonlocal y
        altura = REL_PAD + REL_TITULO + len(linhas) * REL_LINHA + REL_PAD
        if rodape:
            altura += 10 + REL_FAIXA
        garantir(altura)
        caixa(y, altura, REL_MARGEM, REL_LARGURA)
        txt(y + REL_PAD, x_int, larg_int, titulo, 12, True, altura=REL_TITULO)
        yy = y + REL_PAD + REL_TITULO
        for rot, val in linhas:
            linha(yy, rot, val)
            yy += REL_LINHA
        if rodape:
            faixa(yy + 10, *rodape)
        y += altura + REL_GAP

    secao("Resumo do Rafael", [
        ("Receitas", brl(r["receitas"])),
        ("Total de despesas", brl(total_despesas)),
    ], rodape=(
        "Saldo final após despesas", brl(r["saldo"]),
        "#E8F7EE" if r["saldo"] >= 0 else "#FDECEC",
        "#22A35A" if r["saldo"] >= 0 else "#DC2626",
        "#15803D" if r["saldo"] >= 0 else "#B91C1C",
    ))

    linhas_despesas = [(f"Cartão {c}", brl(r["cartoes"][c]["meu_cartao"])) for c in cartoes]
    linhas_despesas += [(d["descricao"], brl(d["valor"])) for d in lancadas]
    secao("Rafael — minhas despesas", linhas_despesas, rodape=(
        "Total de despesas", brl(total_despesas), "#FFF7DB", "#E5B53A", TEXTO))

    # Dívidas de outras pessoas: um bloco por pessoa e faixa de total geral
    alt_pessoa = REL_PAD + 20 + (len(cartoes) + 1) * REL_LINHA + REL_PAD
    alt_terceiros = REL_PAD + REL_TITULO + (len(terceiros) * (alt_pessoa + 8)
                                            if terceiros else REL_LINHA) + 10 + REL_FAIXA + REL_PAD
    garantir(alt_terceiros)
    caixa(y, alt_terceiros, REL_MARGEM, REL_LARGURA)
    txt(y + REL_PAD, x_int, larg_int, "Dívidas de outras pessoas", 12, True, altura=REL_TITULO)
    yy = y + REL_PAD + REL_TITULO
    if not terceiros:
        txt(yy, x_int, larg_int, "Ninguém com empréstimo neste mês.", 10, False, CINZA)
        yy += REL_LINHA
    for pessoa in sorted(terceiros):
        dados = terceiros[pessoa]
        caixa(yy, alt_pessoa, x_int, larg_int, "#F3F7FD", "#C9D9F5", raio=8)
        txt(yy + REL_PAD, x_int + REL_PAD, larg_int - 2 * REL_PAD, pessoa, 11, True, "#1E40AF",
            altura=20)
        ly = yy + REL_PAD + 20
        for c in cartoes:
            txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, c, 10, False, TEXTO)
            txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, brl(dados.get(c, 0)), 10, True,
                "#1E40AF", Qt.AlignRight)
            ly += REL_LINHA
        txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, "Total", 10, True, "#1E40AF")
        txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, brl(sum(dados.values())), 10, True,
            "#1E40AF", Qt.AlignRight)
        yy += alt_pessoa + 8
    faixa(yy + 2, "Total geral de terceiros", brl(total_terceiros),
          "#E8F0FD", "#2563EB", "#1E3A8A")
    y += alt_terceiros + REL_GAP

    # Limitação mensal
    avisos = [
        "Este relatório consolida os valores do mês consultado no aplicativo.",
        "Não são aplicados filtros de período personalizados.",
        "Privacidade: este arquivo contém dados financeiros pessoais. Compartilhe apenas com quem deve vê-lo.",
    ]
    alt_lim = REL_PAD + REL_TITULO + len(avisos) * 30 + REL_PAD
    garantir(alt_lim)
    caixa(y, alt_lim, REL_MARGEM, REL_LARGURA)
    txt(y + REL_PAD, x_int, larg_int, "Limitação mensal", 12, True, altura=REL_TITULO)
    ay = y + REL_PAD + REL_TITULO
    for aviso in avisos:
        txt(ay, x_int, larg_int, aviso, 9, False, CINZA, altura=30, quebra=True)
        ay += 30
    y += alt_lim

    pintor.end()
    return caminho
