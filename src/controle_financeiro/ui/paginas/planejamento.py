"""Planejamento: previsão do próximo mês, assinaturas (itens recorrentes) e parcelas futuras."""
from PySide6.QtWidgets import QLabel, QVBoxLayout
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import FaixaNumeros, Metrica, nova_tabela, preencher
from controle_financeiro.ui.formatacao import brl
from controle_financeiro.ui.paginas.base import Pagina


class PlanejamentoPage(Pagina):
    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(12)

        # Previsão: como o próximo mês começa se virar agora (mesmas regras da virada)
        self.titulo_previsao = self._titulo("")
        lay.addWidget(self.titulo_previsao)
        self.p_receitas = Metrica("Receitas", "Copiadas na virada", "positivo")
        self.p_despesas = Metrica("Despesas", "Recorrentes e parceladas que continuam", "aviso")
        self.p_cartao = Metrica("Meu cartão", "Parcelas e recorrentes que continuam")
        self.p_saldo = Metrica("Saldo previsto", "Receitas, menos despesas e meu cartão")
        lay.addWidget(FaixaNumeros(self.p_receitas, self.p_despesas, self.p_cartao, self.p_saldo))
        self.aviso_previsao = QLabel()
        self.aviso_previsao.setObjectName("rotulo")
        self.aviso_previsao.setWordWrap(True)
        lay.addWidget(self.aviso_previsao)

        lay.addSpacing(8)
        lay.addWidget(self._titulo("Assinaturas e itens recorrentes"))
        self.total_assinaturas = QLabel()
        self.total_assinaturas.setObjectName("rotulo")
        lay.addWidget(self.total_assinaturas)
        self.tab_assinaturas = nova_tabela(
            ["Item", "Origem", "Por mês", "Por ano"],
            "Nenhum item recorrente neste mês.\nMarque Recorrente em uma compra ou despesa para ela aparecer aqui.")
        self.tab_assinaturas.setMinimumHeight(150)
        lay.addWidget(self.tab_assinaturas, 1)

        lay.addSpacing(8)
        lay.addWidget(self._titulo("Parcelas dos próximos meses"))
        self.aviso_parcelas = QLabel("Soma das parcelas que ainda vão cair em cada mês, por cartão "
                                     "(compras suas com parcelas).")
        self.aviso_parcelas.setObjectName("rotulo")
        lay.addWidget(self.aviso_parcelas)
        self.tab_parcelas = nova_tabela(["Mês", "Total"])
        self.tab_parcelas.setMinimumHeight(170)
        lay.addWidget(self.tab_parcelas, 1)

    @staticmethod
    def _titulo(texto):
        rotulo = QLabel(texto)
        rotulo.setObjectName("secao")
        return rotulo

    def _atualizar_previsao(self, mes):
        p = fin().previsao_proximo_mes(mes)
        self.titulo_previsao.setText(f"Se o mês virar agora, {p['nome']} começa assim")
        self.p_receitas.definir(brl(p["receitas"]))
        self.p_despesas.definir(brl(p["despesas"]))
        self.p_cartao.definir(brl(p["meu_cartao"]))
        self.p_saldo.definir(brl(p["saldo"]), "positivo" if p["saldo"] >= 0 else "negativo")
        partes = []
        if p["emprestimos"]:
            partes.append(f"Fora isso, {brl(p['emprestimos'])} em parcelas de empréstimo continuam "
                          "a cair nos cartões (as pessoas devem te pagar).")
        if p["ja_aberto"]:
            partes.append(f"{p['nome']} já está aberto: os números de verdade estão na Visão geral.")
        self.aviso_previsao.setText(" ".join(partes))
        self.aviso_previsao.setVisible(bool(partes))

    def atualizar(self):
        mes = self.mes()
        self._atualizar_previsao(mes)
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
