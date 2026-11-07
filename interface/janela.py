"""Janela principal: menu, mês, conta e atualização automática."""
from datetime import datetime

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QApplication, QDialog, QFileDialog, QHBoxLayout, QLabel,
    QListWidget, QMainWindow, QMessageBox, QPushButton,
    QStackedWidget, QVBoxLayout, QWidget,
)
from financas.contexto import auth, fin
from .componentes import carregar_cores
from .dialogos import GerenciarMeses, Login
from .paginas.emprestimos import DevePage
from .paginas.planejamento import PlanejamentoPage
from .paginas.comparativo import ComparativoPage
from .importacao_ui import ImportarPage
from .paginas.ferramentas import FerramentasPage
from .ferramentas_ui import BuscaDialog, BackupDialog, DatasCartoesDialog, gerar_relatorio_pdf
from .paginas.transacoes import CartoesPage
from .paginas.visao import VisaoPage
from .seletor_mes import MesSeletor


class Janela(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.resize(1240, 800)

        raiz = QWidget()
        linha = QHBoxLayout(raiz)
        linha.setContentsMargins(0, 0, 0, 0)
        linha.setSpacing(0)

        # Lateral azul com a marca e o menu
        lateral = QWidget()
        lateral.setObjectName("lateral")
        lateral.setFixedWidth(230)
        sl = QVBoxLayout(lateral)
        sl.setContentsMargins(0, 0, 0, 0)
        sl.setSpacing(0)
        marca = QLabel("Controle\nFinanceiro")
        marca.setObjectName("marca")
        self.menu = QListWidget()
        self.menu.setObjectName("menu")
        sl.addWidget(marca)
        sl.addWidget(self.menu, 1)

        conta = QWidget()
        conta.setObjectName("conta")
        cl = QVBoxLayout(conta)
        cl.setContentsMargins(18, 14, 18, 18)
        cl.setSpacing(8)
        rotulo_conta = QLabel("Conectado como")
        rotulo_conta.setObjectName("contaRotulo")
        self.conta_nome = QLabel(auth().usuario_logado() or "")
        self.conta_nome.setObjectName("contaNome")
        trocar = QPushButton("Trocar usuário")
        trocar.setObjectName("contaBtn")
        trocar.clicked.connect(self.trocar_usuario)
        sair = QPushButton("Sair")
        sair.setObjectName("contaBtn")
        sair.clicked.connect(self.sair)
        cl.addWidget(rotulo_conta)
        cl.addWidget(self.conta_nome)
        cl.addWidget(trocar)
        cl.addWidget(sair)
        sl.addWidget(conta)

        self.paginas = QStackedWidget()
        self.visao = VisaoPage(self)
        self.cartoes = CartoesPage(self)
        self.deve = DevePage(self)
        self.planejamento = PlanejamentoPage(self)
        self.comparativo = ComparativoPage(self)
        self.importar = ImportarPage(self)
        self.ferramentas = FerramentasPage(self)
        for nome, pagina in [("Visão geral", self.visao), ("Transações", self.cartoes),
                             ("Empréstimos", self.deve), ("Planejamento", self.planejamento), ("Comparativo", self.comparativo),
                             ("Importar extrato", self.importar), ("Ferramentas", self.ferramentas)]:
            self.menu.addItem(nome)
            self.paginas.addWidget(pagina)

        area = QWidget()
        col = QVBoxLayout(area)
        col.setContentsMargins(40, 32, 40, 24)
        col.setSpacing(22)
        topo = QHBoxLayout()
        self.titulo = QLabel()
        self.titulo.setObjectName("titulo")
        self.seletor = MesSeletor()
        self.botao_meses = QPushButton("Meses")
        self.botao_meses.clicked.connect(self.gerenciar_meses)
        self.botao_virar = QPushButton("Virar o mês")
        self.botao_virar.setObjectName("primario")
        self.botao_virar.clicked.connect(self.virar_mes)
        topo.addWidget(self.titulo)
        topo.addStretch()
        topo.addWidget(self.seletor)
        col.addLayout(topo)
        col.addWidget(self.paginas, 1)

        linha.addWidget(lateral)
        linha.addWidget(area, 1)
        self.setCentralWidget(raiz)
        self.estado_label = QLabel()
        self.statusBar().addPermanentWidget(self.estado_label)

        self.seletor.mudou.connect(self.atualizar_tudo)
        self.menu.currentRowChanged.connect(self._trocar)
        self._versao = None
        self._desatualizadas = set()
        self.menu.setCurrentRow(0)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self._verificar)
        self.timer.start(1500)
        self.atualizar_tudo()

    def trocar_usuario(self):
        atual = auth().usuario_logado()
        outras = [u for u in auth().listar_usuarios() if u != atual]
        login = Login("", contas=outras)
        if login.exec() != QDialog.Accepted:
            return
        auth().definir_sessao(login.usuario_conectado)
        self._mudou_usuario()

    def sair(self):
        if QMessageBox.question(
                self, "Sair",
                "Sair do Controle Financeiro? Na próxima vez, o app vai pedir usuário e senha.",
        ) != QMessageBox.Yes:
            return
        auth().encerrar_sessao()
        QApplication.quit()

    def _mudou_usuario(self):
        self.conta_nome.setText(auth().usuario_logado() or "")
        self.seletor.recarregar()
        self.atualizar_tudo()

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
                    "As parcelas avançam uma vez, as que chegaram ao fim saem e as compras "
                    "à vista saem (a smartfit fica). Essa ação não pode ser desfeita.")
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
        QMessageBox.information(self, "Virada concluída", "\n".join(linhas))
        self.seletor.recarregar()
        self.atualizar_tudo()

    def _trocar(self, indice):
        self.paginas.setCurrentIndex(indice)
        self.titulo.setText(self.menu.item(indice).text())
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
            texto, cor = "● Banco local", "#6B7A99"
        elif not e["online"]:
            texto = f"● Sem conexão: usando a cópia salva · {e['pendentes']} aguardando envio"
            cor = "#B07A00"
        elif e["pendentes"]:
            texto, cor = f"● Enviando {e['pendentes']} alteração(ões)…", "#B07A00"
        else:
            texto, cor = "● Sincronizado com o Supabase", "#1E7A4A"
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
            self.statusBar().showMessage(f"Atualizado às {datetime.now():%H:%M}", 5000)
        self._atualizar_estado()


def _metodos_ferramentas():
    pass
