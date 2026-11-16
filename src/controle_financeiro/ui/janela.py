"""Janela principal: menu em seções, mês, conta, atalhos e atualização automática."""
from datetime import datetime

from PySide6.QtCore import QSettings, QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QStackedWidget, QStatusBar, QVBoxLayout, QWidget,
)
from controle_financeiro.config import PASTA
from controle_financeiro.dados.contexto import auth, fin
from controle_financeiro.ui.componentes import MenuLateral, carregar_cores
from controle_financeiro.ui.dialogos import ContaDialog, GerenciarMeses, Login
from controle_financeiro.ui.paginas.caixinhas import CaixinhasPage
from controle_financeiro.ui.paginas.emprestimos import DevePage
from controle_financeiro.ui.paginas.lancamentos import LancamentosPage
from controle_financeiro.ui.paginas.planejamento import PlanejamentoPage
from controle_financeiro.ui.paginas.comparativo import ComparativoPage
from controle_financeiro.ui.importacao_ui import ImportarPage
from controle_financeiro.ui.paginas.ferramentas import FerramentasPage
from controle_financeiro.ui.ferramentas_ui import BuscaDialog, BackupDialog, DatasCartoesDialog, gerar_relatorio_pdf
from controle_financeiro.ui.paginas.transacoes import CartoesPage
from controle_financeiro.ui.paginas.visao import VisaoPage
from controle_financeiro.ui.seletor_mes import MesSeletor
from controle_financeiro.ui.tema import AMARELO_TEXTO, TEXTO_SUAVE, VERDE_TEXTO, VERMELHO_TEXTO

class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.setMinimumSize(1060, 680)
        self.resize(1240, 800)

        raiz = QWidget()
        linha = QHBoxLayout(raiz)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(0)

        # Lateral azul com a marca, o menu em seções e a conta
        lateral = QWidget()
        lateral.setObjectName("lateral")
        lateral.setFixedWidth(230)
        sl = QVBoxLayout(lateral)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        marca = QWidget()
        ml = QHBoxLayout(marca)
        ml.setContentsMargins(22, 26, 18, 10)
        ml.setSpacing(12)
        selo = QLabel("R$")
        selo.setObjectName("marcaSelo")
        selo.setFixedSize(38, 38)
        selo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nomes = QVBoxLayout()
        nomes.setSpacing(0)
        nome_app = QLabel("Controle")
        nome_app.setObjectName("marca")
        sub = QLabel("Financeiro")
        sub.setObjectName("marcaSub")
        nomes.addWidget(nome_app)
        nomes.addWidget(sub)
        ml.addWidget(selo)
        ml.addLayout(nomes)
        ml.addStretch()
        self.menu = MenuLateral()
        rolagem_menu = QScrollArea()  # em janelas baixas o menu rola, sem esconder a conta
        rolagem_menu.setWidgetResizable(True)
        rolagem_menu.setFrameShape(QFrame.Shape.NoFrame)
        rolagem_menu.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        rolagem_menu.setWidget(self.menu)
        sl.addWidget(marca)
        sl.addWidget(rolagem_menu, 1)
        sl.addWidget(self._montar_conta())

        self.paginas = QStackedWidget()
        self.visao = VisaoPage(self)
        self.cartoes = CartoesPage(self)
        self.lancamentos = LancamentosPage(self)
        self.planejamento = PlanejamentoPage(self)
        self.comparativo = ComparativoPage(self)
        self.deve = DevePage(self)
        self.caixinhas = CaixinhasPage(self)
        self.importar = ImportarPage(self)
        self.ferramentas = FerramentasPage(self)
        # Geral: o dia a dia do mês. Pessoal: o que é só seu (quem te deve, o que você guarda).
        # Sistema: entrada de dados em lote e manutenção do app.
        secoes = [
            ("Geral", [("Visão geral", self.visao), ("Transações", self.cartoes),
                       ("Receitas e despesas", self.lancamentos),
                       ("Planejamento", self.planejamento), ("Comparativo", self.comparativo)]),
            ("Pessoal", [("Empréstimos", self.deve), ("Caixinhas", self.caixinhas)]),
            ("Sistema", [("Importar extrato", self.importar), ("Ferramentas", self.ferramentas)]),
        ]
        for secao, itens in secoes:
            self.menu.secao(secao)
            for nome, pagina in itens:
                indice = self.menu.item(nome, f"Ctrl+{self.paginas.count() + 1}")
                self.paginas.addWidget(pagina)
                QShortcut(QKeySequence(f"Ctrl+{indice + 1}"), self,
                          lambda i=indice: self.menu.selecionar(i))

        area = QWidget()
        col = QVBoxLayout(area)
        col.setContentsMargins(40, 32, 40, 24)
        col.setSpacing(22)
        topo = QHBoxLayout()
        self.titulo = QLabel()
        self.titulo.setObjectName("titulo")
        self.seletor = MesSeletor()
        topo.addWidget(self.titulo)
        topo.addStretch()
        topo.addWidget(self.seletor)
        col.addLayout(topo)
        col.addWidget(self.paginas, 1)
        # barra de estado dentro da área de conteúdo, para a lateral azul ir até o fim da janela
        self.barra_estado = QStatusBar()
        self.barra_estado.setSizeGripEnabled(False)
        col.addWidget(self.barra_estado)

        linha.addWidget(lateral)
        linha.addWidget(area, 1)
        self.setCentralWidget(raiz)
        self.estado_label = QLabel()
        self.statusBar().hide()
        self.barra_estado.addPermanentWidget(self.estado_label)

        QShortcut(QKeySequence("Ctrl+N"), self, self.novo)
        QShortcut(QKeySequence("Ctrl+F"), self, self.buscar)
        QShortcut(QKeySequence("F5"), self, self.atualizar_tudo)
        QShortcut(QKeySequence("Alt+Left"), self, self.seletor.anterior)
        QShortcut(QKeySequence("Alt+Right"), self, self.seletor.proximo)

        self.seletor.mudou.connect(self.atualizar_tudo)
        self.menu.mudou.connect(self._trocar)
        self._versao = None
        self._desatualizadas = set()
        self.menu.selecionar(0)

        self._restaurar_janela()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._verificar)
        self.timer.start(1500)
        self.atualizar_tudo()

    def _montar_conta(self):
        """Rodapé da lateral: quem está conectado e as ações da conta."""
        conta = QWidget()
        cl = QVBoxLayout(conta)
        cl.setContentsMargins(18, 0, 18, 16)
        cl.setSpacing(6)
        divisor = QFrame()
        divisor.setObjectName("contaLinha")
        divisor.setFixedHeight(1)
        rotulo_conta = QLabel("Conectado como")
        rotulo_conta.setObjectName("contaRotulo")
        self.conta_nome = QLabel(auth().nome_exibicao())
        self.conta_nome.setObjectName("contaNome")
        conta_btn = QPushButton("Minha conta")
        conta_btn.setObjectName("contaBtn")
        conta_btn.clicked.connect(self.abrir_conta)
        trocar = QPushButton("Trocar usuário")
        sair = QPushButton("Sair")
        for botao, acao in ((trocar, self.trocar_usuario), (sair, self.sair)):
            botao.setObjectName("contaLink")
            botao.setCursor(Qt.CursorShape.PointingHandCursor)
            botao.clicked.connect(acao)
        links = QHBoxLayout()
        links.setContentsMargins(0, 2, 0, 0)
        links.addWidget(trocar)
        links.addStretch()
        links.addWidget(sair)
        cl.addWidget(divisor)
        cl.addSpacing(8)
        cl.addWidget(rotulo_conta)
        cl.addWidget(self.conta_nome)
        cl.addSpacing(4)
        cl.addWidget(conta_btn)
        cl.addLayout(links)
        return conta

    # ----- tamanho e posição da janela (lembrados entre uma abertura e outra) -----

    @staticmethod
    def _preferencias():
        return QSettings(str(PASTA / "janela.ini"), QSettings.Format.IniFormat)

    def _restaurar_janela(self):
        geometria = self._preferencias().value("geometria")
        if geometria:
            self.restoreGeometry(geometria)

    def closeEvent(self, evento):
        self._preferencias().setValue("geometria", self.saveGeometry())
        super().closeEvent(evento)

    # ----- conta -----

    def trocar_usuario(self):
        atual = auth().usuario_logado()
        if auth().nuvem:
            auth().sair()
            login = Login("")
            if login.exec() != QDialog.Accepted:
                QApplication.quit()
                return
        else:
            outras = [u for u in auth().listar_usuarios() if u != atual]
            login = Login("", contas=outras)
            if login.exec() != QDialog.Accepted:
                return
        self._mudou_usuario()

    def abrir_conta(self):
        dialogo = ContaDialog(self)
        dialogo.exec()
        if dialogo.reiniciar:
            QMessageBox.information(
                self, "Projeto trocado",
                "O app vai fechar. Abra de novo e entre com o e-mail e a senha do novo projeto.")
            auth().sair()
            QApplication.quit()

    def sair(self):
        if QMessageBox.question(
                self, "Sair",
                "Sair do Controle Financeiro? Na próxima vez, o app vai pedir e-mail e senha.",
        ) != QMessageBox.Yes:
            return
        auth().sair()
        QApplication.quit()

    def _mudou_usuario(self):
        self.conta_nome.setText(auth().nome_exibicao())
        self.seletor.recarregar()
        self.atualizar_tudo()

    # ----- atalhos e ferramentas -----

    def ir_para(self, pagina):
        """Abre uma página pelo menu (usado pelos cards da Visão geral)."""
        self.menu.selecionar(self.paginas.indexOf(pagina))

    def novo(self):
        """Ctrl+N: novo lançamento da página aberta."""
        self.paginas.currentWidget().novo()

    def buscar(self):
        """Ctrl+F: em Transações filtra a tabela; nas outras páginas busca em todos os meses."""
        if self.paginas.currentWidget() is self.cartoes:
            self.cartoes.busca.setFocus()
            self.cartoes.busca.selectAll()
        else:
            self.abrir_busca()

    def abrir_busca(self):
        BuscaDialog(self).exec()

    def abrir_backup(self):
        BackupDialog(self).exec()

    def abrir_datas(self):
        DatasCartoesDialog(self).exec()
        self.atualizar_tudo()

    def exportar_pdf(self):
        caminho, _ = QFileDialog.getSaveFileName(
            self, "Salvar relatório", f"relatorio-{self.mes_atual()}.pdf", "PDF (*.pdf)")
        if caminho:
            gerar_relatorio_pdf(caminho, self.mes_atual())
            QMessageBox.information(self, "Relatório", f"Relatório salvo em:\n{caminho}")

    def gerenciar_meses(self):
        GerenciarMeses(self).exec()
        self.seletor.recarregar()
        self.atualizar_tudo()

    def virar_mes(self):
        ativo = fin().mes_ativo()
        novo = fin().proximo_mes(ativo)
        pergunta = (f"Abrir {fin().nome_mes(novo)} copiando {fin().nome_mes(ativo)}?\n\n"
                    "O que acontece:\n"
                    "• Itens marcados como Recorrente continuam no mês novo, sem avançar parcela.\n"
                    "• Parcelas avançam uma vez; as que chegaram ao fim saem.\n"
                    "• Compras à vista e despesas não recorrentes saem.\n\n"
                    "Antes de virar, o app salva uma cópia de segurança de todos os dados.")
        if QMessageBox.question(self, "Virar o mês", pergunta) != QMessageBox.Yes:
            return
        try:
            r = fin().virar_mes()
        except ValueError as e:
            QMessageBox.warning(self, "Não consegui virar o mês", str(e))
            return
        linhas = [f"Mês aberto: {fin().nome_mes(r['novo'])}.", ""]
        linhas.append(f"Parcelas avançadas: {len(r['avancadas'])}")
        for item, cartao, nova in r["avancadas"][:15]:
            linhas.append(f"   {item} ({cartao}): agora {nova}")
        linhas.append("")
        linhas.append(f"Lançamentos removidos: {len(r['removidas'])}")
        for item, cartao in r["removidas"][:15]:
            linhas.append(f"   {item} ({cartao})")
        linhas += ["", "Cópia de segurança de antes da virada:", f"   {r['backup']}"]
        QMessageBox.information(self, "Virada concluída", "\n".join(linhas))
        self.seletor.recarregar()
        self.atualizar_tudo()

    # ----- páginas e atualização -----

    def _trocar(self, indice):
        self.paginas.setCurrentIndex(indice)
        self.titulo.setText(self.menu.nome(indice))
        if indice in self._desatualizadas:  # só carrega a página quando ela é aberta
            self._atualizar_pagina(indice)

    def mes_atual(self):
        return self.seletor.codigo()

    def atualizar_tudo(self):
        """Marca todas as páginas como desatualizadas e atualiza só a que está aberta.
        As outras são atualizadas quando forem abertas (menos consultas ao Supabase)."""
        carregar_cores()
        self._desatualizadas = set(range(self.paginas.count()))
        self._atualizar_pagina(self.paginas.currentIndex())
        self._versao = fin().versao()
        self._atualizar_estado()

    def _atualizar_estado(self):
        """Aviso no canto da tela: se os dados estão sincronizados com o Supabase."""
        e = fin().banco.estado()
        if e["tipo"] == "local":
            texto, cor = "● Banco local", TEXTO_SUAVE
        elif e.get("sessao_expirada"):
            texto = (f"● Sessão expirada: feche e entre de novo para sincronizar · "
                     f"{e['pendentes']} aguardando envio")
            cor = VERMELHO_TEXTO
        elif not e["online"]:
            texto = f"● Sem conexão: usando a cópia salva · {e['pendentes']} aguardando envio"
            cor = AMARELO_TEXTO
        elif e["pendentes"]:
            texto, cor = f"● Enviando {e['pendentes']} alteração(ões)…", AMARELO_TEXTO
        else:
            texto, cor = "● Sincronizado com o Supabase", VERDE_TEXTO
        if e["falhas"]:
            texto += f" · {e['falhas']} não enviada(s)"
        self.estado_label.setText(texto)
        self.estado_label.setStyleSheet(f"color: {cor}; font-weight: 600; padding-right: 8px;")

    def _atualizar_pagina(self, indice):
        self.paginas.widget(indice).atualizar()
        self._desatualizadas.discard(indice)

    def _verificar(self):
        v = fin().versao()
        if v != self._versao:
            self.seletor.recarregar()
            self.atualizar_tudo()
            self.barra_estado.showMessage(f"Atualizado às {datetime.now():%H:%M}", 5000)
        self._atualizar_estado()
