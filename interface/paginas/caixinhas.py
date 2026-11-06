"""Página Caixinhas."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout,
)
from financas.contexto import fin
from ..componentes import Formulario, nova_tabela, preencher, selecionado, texto
from ..formatacao import brl
from .base import Pagina


class CaixinhasPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        barra = QHBoxLayout()
        barra.addStretch()
        botao = QPushButton("Nova caixinha")
        botao.setObjectName("primario")
        botao.clicked.connect(self.nova)
        barra.addWidget(botao)
        lay.addLayout(barra)
        self.tab = nova_tabela(["Dono", "Caixinha", "Valor"])
        self.tab.doubleClicked.connect(lambda _i: self.editar())
        lay.addWidget(self.tab)
        ajuda = QLabel("Dê duplo clique em uma caixinha para editar.")
        ajuda.setObjectName("rotulo")
        lay.addWidget(ajuda)

    def atualizar(self):
        linhas = fin().listar_caixinhas()
        preencher(self.tab, [(c["id"], [c["dono"], c["nome"], brl(c["valor"])]) for c in linhas])

    def _formulario(self, titulo, dono="", nome="", valor=""):
        return Formulario(self, titulo, [
            ("dono", "Dono", texto(dono, "Ex.: Rafael")),
            ("nome", "Nome da caixinha", texto(nome, "Ex.: Reserva")),
            ("valor", "Valor", texto(valor, "R$ 0,00")),
        ])

    def nova(self):
        dlg = self._formulario("Nova caixinha")
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().definir_caixinha(v["dono"], v["nome"], v["valor"])
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()

    def editar(self):
        id_ = selecionado(self.tab)
        c = fin().obter_caixinha(id_) if id_ is not None else None
        if not c:
            return
        dlg = self._formulario("Editar caixinha", c["dono"], c["nome"], brl(c["valor"]))
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().atualizar_caixinha(id_, v["dono"], v["nome"], v["valor"])
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()
