"""Planejamento: assinaturas (itens recorrentes) e parcelas dos próximos meses."""
from PySide6.QtWidgets import QLabel, QVBoxLayout
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import nova_tabela, preencher
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina


class PlanejamentoPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(12)

        lay.addWidget(self._titulo("Assinaturas e itens recorrentes"))
        self.total_assinaturas = QLabel()
        self.total_assinaturas.setObjectName("rotulo")
        lay.addWidget(self.total_assinaturas)
        self.tab_assinaturas = nova_tabela(["Item", "Origem", "Por mês", "Por ano"])
        self.tab_assinaturas.setMinimumHeight(190)
        lay.addWidget(self.tab_assinaturas)

        lay.addWidget(self._titulo("Parcelas dos próximos meses"))
        self.aviso_parcelas = QLabel("Soma das parcelas que ainda vão cair em cada mês, por cartão "
                                     "(compras suas com parcelas).")
        self.aviso_parcelas.setObjectName("rotulo")
        lay.addWidget(self.aviso_parcelas)
        self.tab_parcelas = nova_tabela(["Mês", "Total"])
        self.tab_parcelas.setMinimumHeight(230)
        lay.addWidget(self.tab_parcelas)

    @staticmethod
    def _titulo(texto):
        rotulo = QLabel(texto)
        rotulo.setObjectName("secao")
        return rotulo

    def atualizar(self):
        mes = self.mes()
        a = fin().assinaturas(mes)
        preencher(self.tab_assinaturas, [
            (i, [x["item"], x["origem"], brl(x["valor_mes"]), brl(x["valor_mes"] * 12)])
            for i, x in enumerate(a["itens"])])
        self.total_assinaturas.setText(
            f"Total por mês: {brl(a['total_mes'])}     Total por ano: {brl(a['total_ano'])}")

        cartoes = [c["nome"] for c in fin().listar_cartoes()]
        self.tab_parcelas.setColumnCount(2 + len(cartoes))
        self.tab_parcelas.setHorizontalHeaderLabels(["Mês", "Total"] + cartoes)
        linhas = []
        for i, p in enumerate(fin().parcelas_futuras(mes, 6)):
            linhas.append((i, [p["nome"], brl(p["total"])] + [brl(p["por_cartao"].get(c, 0)) for c in cartoes]))
        preencher(self.tab_parcelas, linhas)
