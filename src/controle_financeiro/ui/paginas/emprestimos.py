"""Página Empréstimos: quem deve e os detalhes de cada um."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout,
)
from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.componentes import BalaoCartao, ComboPessoa, Formulario, Kpi, nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.dialogos import dialogo_compra
from controle_financeiro.ui.formatacao import _parcela_exibida, brl
from controle_financeiro.ui.paginas.base import Pagina


class DevePage(Pagina):
    """Empréstimos: quanto cada pessoa deve no mês, e o detalhe de cada empréstimo."""

    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(18)

        # Linha de números do mês
        numeros = QHBoxLayout()
        numeros.setSpacing(16)
        self.k_emprestado = Kpi("Emprestado no mês", "azul",
                                "Soma das parcelas de empréstimo deste mês")
        self.k_pago = Kpi("Já pago", "verde", "O que as pessoas devolveram neste mês")
        self.k_aberto = Kpi("Em aberto", "amarelo", "O que ainda falta receber neste mês")
        for k in (self.k_emprestado, self.k_pago, self.k_aberto):
            numeros.addWidget(k)
        lay.addLayout(numeros)

        corpo = QHBoxLayout()
        corpo.setSpacing(24)

        # Lado esquerdo: uma linha por pessoa
        esquerda = QVBoxLayout()
        esquerda.setSpacing(10)
        rotulo_pessoas = QLabel("Quem te deve")
        rotulo_pessoas.setObjectName("secao")
        esquerda.addWidget(rotulo_pessoas)
        self.tab = nova_tabela(["Pessoa", "Emprestado", "Já pago", "Em aberto"])
        self.tab.itemSelectionChanged.connect(self._detalhar)
        esquerda.addWidget(self.tab, 1)
        corpo.addLayout(esquerda, 2)

        # Lado direito: os empréstimos da pessoa selecionada
        direita = QVBoxLayout()
        direita.setSpacing(10)
        cabecalho = QHBoxLayout()
        self.det_titulo = QLabel()
        self.det_titulo.setObjectName("secao")
        cabecalho.addWidget(self.det_titulo)
        cabecalho.addStretch()
        self.botao_pagar = QPushButton("Registrar pagamento")
        self.botao_pagar.setObjectName("primario")
        self.botao_pagar.clicked.connect(self.pagamento)
        cabecalho.addWidget(self.botao_pagar)
        direita.addLayout(cabecalho)
        self.det = nova_tabela(["Item", "Mês", "Cartão", "Parcelas", "Valor"])
        self.det.setItemDelegateForColumn(2, BalaoCartao(self.det))
        self.det.doubleClicked.connect(lambda _i: self.editar_emprestimo())
        direita.addWidget(self.det, 1)
        ajuda = QLabel("Dê duplo clique em um empréstimo para editar.")
        ajuda.setObjectName("rotulo")
        direita.addWidget(ajuda)
        corpo.addLayout(direita, 3)

        lay.addLayout(corpo, 1)

    def atualizar(self):
        r = self.tab.currentRow()
        pessoa_sel = self.tab.item(r, 0).text() if r >= 0 and self.tab.item(r, 0) else None
        dados = fin().quanto_me_devem(self.mes())
        self.k_emprestado.definir(brl(sum(d["emprestado"] for d in dados)))
        self.k_pago.definir(brl(sum(d["ja_pago"] for d in dados)), "verde")
        self.k_aberto.definir(brl(sum(d["em_aberto"] for d in dados)), "amarelo")
        preencher(self.tab, [
            (i, [d["pessoa"], brl(d["emprestado"]), brl(d["ja_pago"]), brl(d["em_aberto"])])
            for i, d in enumerate(dados)])
        if pessoa_sel:
            for i, d in enumerate(dados):
                if d["pessoa"] == pessoa_sel:
                    self.tab.selectRow(i)
                    break
        self._detalhar()

    def _detalhar(self):
        r = self.tab.currentRow()
        if r < 0 or self.tab.item(r, 0) is None:
            self.det_titulo.setText("Selecione uma pessoa")
            preencher(self.det, [])
            return
        pessoa = self.tab.item(r, 0).text()
        self.det_titulo.setText(f"Empréstimos de {pessoa}")
        preencher(self.det, [
            (c["id"], [c["item"], fin().nome_mes(c["mes"]), c["cartao"], _parcela_exibida(c),
                       brl(c["valor_parcela"])])
            for c in fin().emprestimos_de(pessoa, self.mes())], cartao_col=2)

    def editar_emprestimo(self):
        id_ = selecionado(self.det)
        c = fin().obter_compra(id_) if id_ is not None else None
        if c and dialogo_compra(self, c):
            self.mudou()

    def pagamento(self):
        r = self.tab.currentRow()
        pre = self.tab.item(r, 0).text() if r >= 0 and self.tab.item(r, 0) else ""
        dlg = Formulario(self, "Registrar pagamento", [
            ("pessoa", "Pessoa", ComboPessoa(pre, permitir_vazio=False)),
            ("valor", "Valor recebido", texto("", "R$ 0,00")),
            ("descricao", "Observação", texto("", "Opcional")),
        ])
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().registrar_pagamento(v["pessoa"], v["valor"], v["descricao"], mes=self.mes())
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()
