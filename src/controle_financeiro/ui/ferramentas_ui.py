"""Telas das ferramentas: busca, backup, datas das faturas e relatório em PDF."""
from datetime import date

from PySide6.QtCore import QRectF, Qt, QUrl
from PySide6.QtGui import QBrush, QColor, QDesktopServices, QFont, QPainter, QPdfWriter, QPageSize, QPen
from PySide6.QtWidgets import (QApplication, QDialog, QFileDialog, QHBoxLayout, QLabel, QLineEdit,
                               QMessageBox, QPushButton, QVBoxLayout)
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import Formulario, nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.formatacao import brl


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
        self.tab = nova_tabela(["Mês", "Origem", "Descrição", "Valor", "Pessoa"],
                               "Digite o que procura e aperte Enter.")
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
        self.tab.vazio = f"Nada encontrado para “{self.campo.text().strip()}”."
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


class CopiasDialog(QDialog):
    """Cópias automáticas (feitas antes de cada virada): ver e voltar os dados para uma delas."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Cópias automáticas")
        self.setMinimumSize(560, 420)
        self.restaurou = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel("Cópias automáticas")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        ajuda = QLabel("O app salva uma cópia de todos os dados antes de cada virada de mês e antes "
                       "de restaurar. Ficam as 6 mais novas de cada tipo, neste computador.")
        ajuda.setObjectName("rotulo")
        ajuda.setWordWrap(True)
        lay.addWidget(ajuda)
        self.tab = nova_tabela(["Quando", "Feita"],
                               "Nenhuma cópia ainda. A primeira é feita na próxima virada de mês.")
        self.tab.ao_editar(self.restaurar)
        lay.addWidget(self.tab, 1)
        botoes = QHBoxLayout()
        pasta = QPushButton("Abrir a pasta")
        pasta.clicked.connect(self._abrir_pasta)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        self.botao_restaurar = QPushButton("Restaurar esta cópia")
        self.botao_restaurar.setObjectName("primario")
        self.botao_restaurar.clicked.connect(self.restaurar)
        botoes.addWidget(pasta)
        botoes.addStretch()
        botoes.addWidget(fechar)
        botoes.addWidget(self.botao_restaurar)
        lay.addLayout(botoes)
        self._carregar()

    def _carregar(self):
        self._copias = fin().listar_backups()
        preencher(self.tab, [(i, [f"{c['quando']:%d/%m/%Y às %H:%M}", c["motivo"]])
                             for i, c in enumerate(self._copias)])
        if self._copias:
            self.tab.selectRow(0)
        self.botao_restaurar.setEnabled(bool(self._copias))

    def _abrir_pasta(self):
        pasta = fin().pasta_backups
        pasta.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(pasta)))

    def restaurar(self):
        i = selecionado(self.tab)
        if i is None:
            QMessageBox.information(self, "Restaurar", "Selecione uma cópia na lista.")
            return
        c = self._copias[i]
        pergunta = (f"Voltar os dados para a cópia de {c['quando']:%d/%m/%Y às %H:%M} ({c['motivo'].lower()})?\n\n"
                    "Todos os dados atuais (compras, receitas, despesas, empréstimos, caixinhas e meses) "
                    "serão trocados pelos da cópia. O que foi lançado depois dela some.\n\n"
                    "Antes, o app salva uma cópia de como está agora, para você poder voltar atrás.")
        if QMessageBox.question(self, "Restaurar cópia", pergunta) != QMessageBox.Yes:
            return
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            seguranca = fin().restaurar_backup(c["caminho"])
        except ValueError as e:
            QApplication.restoreOverrideCursor()
            QMessageBox.warning(self, "Não consegui restaurar", str(e))
            return
        QApplication.restoreOverrideCursor()
        self.restaurou = True
        QMessageBox.information(self, "Cópia restaurada",
                                "Os dados voltaram para a cópia escolhida.\n\n"
                                f"Os dados de antes foram salvos em:\n{seguranca}")
        self._carregar()


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
        self.tab.ao_editar(self.editar)
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

    from controle_financeiro.ui import tema
    TEXTO, CINZA = tema.TEXTO, tema.TEXTO_SUAVE
    x_int = REL_MARGEM + REL_PAD
    larg_int = REL_LARGURA - 2 * REL_PAD

    def caixa(yy, altura, x, largura, fundo="#FFFFFF", borda=tema.BORDA, raio=10):
        pintor.setPen(QPen(QColor(borda), 1))
        pintor.setBrush(QBrush(QColor(fundo)))
        pintor.drawRoundedRect(QRectF(x, yy, largura, altura), raio, raio)

    def txt(yy, x, largura, t, tam=10, negrito=False, cor=TEXTO,
            alinha=Qt.AlignLeft, altura=REL_LINHA, quebra=False):
        fonte = QFont(tema.FONTE, tam)  # sem a fonte do app, o Qt usa a padrão
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

    # Cabeçalho em verde petróleo, como a lateral do app
    altura_topo = 84
    garantir(altura_topo)
    caixa(y, altura_topo, REL_MARGEM, REL_LARGURA, tema.TINTA, tema.TINTA, raio=14)
    txt(y + 12, x_int, larg_int, "Controle Financeiro", 8, True, tema.MENTA, altura=14)
    txt(y + 26, x_int, larg_int, "Relatório financeiro", 20, True, "#FFFFFF", altura=28)
    txt(y + 54, x_int, larg_int, "Dívidas e despesas consolidadas", 10, False, "#C5DAD5", altura=16)
    txt(y + 68, x_int, larg_int, f"Mês consultado: {r['mes']}", 9, False, "#C5DAD5", altura=14)
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
        "#EAF6EE" if r["saldo"] >= 0 else "#FDF0EE",
        "#BFE3CB" if r["saldo"] >= 0 else "#F1C4BD",
        tema.VERDE_TEXTO if r["saldo"] >= 0 else tema.VERMELHO_TEXTO,
    ))

    linhas_despesas = [(f"Cartão {c}", brl(r["cartoes"][c]["meu_cartao"])) for c in cartoes]
    linhas_despesas += [(d["descricao"], brl(d["valor"])) for d in lancadas]
    secao("Rafael: minhas despesas", linhas_despesas, rodape=(
        "Total de despesas", brl(total_despesas), "#FDF4E3", "#F0D9A8", "#6E4306"))

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
        caixa(yy, alt_pessoa, x_int, larg_int, "#F3F8F6", tema.BORDA, raio=8)
        txt(yy + REL_PAD, x_int + REL_PAD, larg_int - 2 * REL_PAD, pessoa, 11, True, tema.TINTA,
            altura=20)
        ly = yy + REL_PAD + 20
        for c in cartoes:
            txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, c, 10, False, TEXTO)
            txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, brl(dados.get(c, 0)), 10, True,
                tema.TINTA, Qt.AlignRight)
            ly += REL_LINHA
        txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, "Total", 10, True, tema.TINTA)
        txt(ly, x_int + REL_PAD, larg_int - 2 * REL_PAD, brl(sum(dados.values())), 10, True,
            tema.TINTA, Qt.AlignRight)
        yy += alt_pessoa + 8
    faixa(yy + 2, "Total geral de terceiros", brl(total_terceiros),
          tema.PRIMARIA_CLARA, tema.PRIMARIA, tema.TINTA)
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
