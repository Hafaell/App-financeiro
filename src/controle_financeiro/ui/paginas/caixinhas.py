"""Página Caixinhas: valor guardado, meta, progresso e quanto guardar por mês até a data alvo."""
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton, QVBoxLayout
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import BarraProgresso, FaixaNumeros, Formulario, Metrica, nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina


def _percentual(valor):
    return "—" if valor is None else f"{valor:.0f}%".replace(".", ",")


class CaixinhasPage(Pagina):
    COLUNAS = ["Dono", "Caixinha", "Valor", "Meta", "Progresso", "Data alvo", "Por mês"]

    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(18)

        self.k_guardado = Metrica("Guardado", "Soma de todas as caixinhas", "positivo")
        self.k_metas = Metrica("Metas", "Soma das metas definidas")
        self.k_falta = Metrica("Falta para as metas", "Quanto ainda falta guardar", "aviso")
        lay.addWidget(FaixaNumeros(self.k_guardado, self.k_metas, self.k_falta))

        barra = QHBoxLayout()
        ajuda = QLabel("Dê duplo clique em uma caixinha para editar. Meta e data alvo são opcionais.")
        ajuda.setObjectName("rotulo")
        barra.addWidget(ajuda)
        barra.addStretch()
        botao = QPushButton("Nova caixinha")
        botao.setObjectName("primario")
        botao.setToolTip("Ctrl+N")
        botao.clicked.connect(self.nova)
        barra.addWidget(botao)
        lay.addLayout(barra)

        self.tab = nova_tabela(
            self.COLUNAS, "Nenhuma caixinha ainda.\nClique em Nova caixinha para começar a guardar.")
        self.tab.setItemDelegateForColumn(4, BarraProgresso(self.tab))
        self.tab.ao_editar(self.editar)
        lay.addWidget(self.tab, 1)

    def atualizar(self):
        linhas = fin().andamento_caixinhas()
        self.k_guardado.definir(brl(sum(c["valor"] for c in linhas)))
        self.k_metas.definir(brl(sum(c["meta"] or 0 for c in linhas)))
        self.k_falta.definir(brl(sum(c["falta"] or 0 for c in linhas)))
        preencher(self.tab, [
            (c["id"], [c["dono"], c["nome"], brl(c["valor"]),
                       brl(c["meta"]) if c["meta"] else "—",
                       _percentual(c["progresso"]),
                       c["data_alvo"] or "—",
                       brl(c["por_mes"]) if c["por_mes"] is not None else "—"])
            for c in linhas])

    def _formulario(self, titulo, c=None):
        valores = c or {}
        return Formulario(self, titulo, [
            ("dono", "Dono", texto(valores.get("dono", ""), "Ex.: Rafael")),
            ("nome", "Nome da caixinha", texto(valores.get("nome", ""), "Ex.: Viagem")),
            ("valor", "Valor guardado", texto(brl(valores["valor"]) if c else "", "R$ 0,00")),
            ("meta", "Meta (opcional)", texto(brl(valores["meta"]) if c and valores.get("meta") else "",
                                              "Ex.: R$ 5.000,00")),
            ("data_alvo", "Data alvo (opcional)", texto(valores.get("data_alvo") or "",
                                                       "Ex.: 2027-06")),
        ])

    def novo(self):
        self.nova()

    def nova(self):
        dlg = self._formulario("Nova caixinha")
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().definir_caixinha(v["dono"], v["nome"], v["valor"])
            nova = next(c for c in fin().listar_caixinhas()
                        if c["dono"] == v["dono"].strip() and c["nome"] == v["nome"].strip())
            fin().definir_meta_caixinha(nova["id"], v["meta"], v["data_alvo"])
        except (ValueError, StopIteration) as e:
            self.erro(e)
            return
        self.mudou()

    def editar(self):
        id_ = selecionado(self.tab)
        c = fin().obter_caixinha(id_) if id_ is not None else None
        if not c:
            return
        dlg = self._formulario("Editar caixinha", c)
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().atualizar_caixinha(id_, v["dono"], v["nome"], v["valor"], v["meta"], v["data_alvo"])
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()
