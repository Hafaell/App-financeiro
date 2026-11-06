"""Página Transações: compras de todos os cartões."""
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QMessageBox,
    QPushButton, QVBoxLayout,
)
from ..formatacao import id_categoria, nome_categoria
from ..dialogos import CategoriasDialog
from financas.contexto import fin
from ..componentes import BalaoCartao, Formulario, carregar_cores, combo, nova_tabela, preencher, selecionado
from ..dialogos import NovoCartao, campos_compra, dialogo_compra
from ..formatacao import NOVO_CARTAO, TODOS, _ordem_cartoes, _parcela_exibida, _pessoa_exibida, brl, nomes_cartoes
from .base import Pagina


class CartoesPage(Pagina):
    """Transações: compras de todos os cartões, com cadastro de cartões novos."""

    COLUNAS = ["Cartão", "Item", "Categoria", "Parcelas", "Valor da parcela",
               "Recorrente", "Pessoa", "Valor real"]

    def __init__(self, janela):
        super().__init__(janela)
        lay = QVBoxLayout(self)
        lay.setSpacing(14)
        barra = QHBoxLayout()
        self.filtro = combo([])
        self.filtro.setMinimumWidth(190)
        self.filtro.currentIndexChanged.connect(self._filtro_mudou)
        novo = QPushButton("Novo cartão")
        novo.clicked.connect(lambda: self.novo_cartao(selecionar=False))
        apagar = QPushButton("Apagar selecionada")
        apagar.clicked.connect(self.apagar)
        nova = QPushButton("Nova compra")
        nova.setObjectName("primario")
        nova.clicked.connect(self.nova)
        barra.addWidget(self.filtro)
        barra.addStretch()
        cats = QPushButton("Categorias")
        cats.clicked.connect(self.abrir_categorias)
        barra.addWidget(cats)
        barra.addWidget(novo)
        barra.addWidget(apagar)
        barra.addWidget(nova)
        lay.addLayout(barra)
        self.tab = nova_tabela(self.COLUNAS)
        self.tab.setItemDelegateForColumn(0, BalaoCartao(self.tab))
        self.tab.doubleClicked.connect(lambda _i: self.editar())
        lay.addWidget(self.tab)
        self.totais = QLabel()
        self.totais.setObjectName("rotulo")
        lay.addWidget(self.totais)

    def _recarregar_filtro(self, escolhido=None):
        atual = escolhido or self.filtro.currentText()
        self.filtro.blockSignals(True)
        self.filtro.clear()
        self.filtro.addItem(TODOS)
        self.filtro.addItems(nomes_cartoes())
        self.filtro.addItem(NOVO_CARTAO)
        indice = self.filtro.findText(atual)
        self.filtro.setCurrentIndex(indice if indice >= 0 else 0)
        self.filtro.blockSignals(False)

    def _filtro_mudou(self, _indice=None):
        if self.filtro.currentText() == NOVO_CARTAO:
            self.novo_cartao(selecionar=True)
            return
        self.atualizar()

    def abrir_categorias(self):
        CategoriasDialog(self).exec()
        self.janela.atualizar_tudo()

    def novo_cartao(self, selecionar=False):
        dlg = NovoCartao(self)
        if dlg.exec() != QDialog.Accepted:
            if selecionar:
                self._recarregar_filtro(TODOS)
                self.atualizar()
            return
        carregar_cores()
        self._recarregar_filtro(dlg.nome.text().strip() if selecionar else None)
        self.janela.atualizar_tudo()

    def atualizar(self):
        self._recarregar_filtro()
        escolha = self.filtro.currentText()
        cartao = None if escolha == TODOS else escolha
        linhas = sorted(fin().listar_compras(cartao, self.mes()), key=_ordem_cartoes)
        mapa = {c["id"]: c["nome"] for c in fin().listar_categorias()}
        preencher(self.tab, [
            (c["id"], [
                c["cartao"], c["item"], nome_categoria(c["categoria_id"], mapa), _parcela_exibida(c), brl(c["valor_parcela"]),
                "Sim" if c["recorrente"] else "Não", _pessoa_exibida(c),
                brl(c["valor_real"]) if c["valor_real"] is not None else "—",
            ]) for c in linhas], cartao_col=0)
        r = fin().resumo_mes(self.mes())
        self.totais.setText(
            f"Meu cartão: {brl(r['meu_cartao_total'])}      "
            f"Com empréstimos: {brl(r['cartoes_com_emprestimos_total'])}")

    def editar(self):
        id_ = selecionado(self.tab)
        c = fin().obter_compra(id_) if id_ is not None else None
        if c and dialogo_compra(self, c):
            self.mudou()

    def nova(self):
        dlg = Formulario(self, "Nova compra no cartão", campos_compra())
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            fin().lancar_compra(
                cartao=v["cartao"], item=v["item"], parcelas=v["parcelas"],
                valor_parcela=v["valor_parcela"], mes=self.mes(),
                pessoa=v["pessoa"], valor_real=v["valor_real"] or None,
                recorrente=v["recorrente"], categoria_id=id_categoria(v["categoria"]))
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()

    def apagar(self):
        id_ = selecionado(self.tab)
        if id_ is None:
            QMessageBox.information(self, "Apagar compra", "Selecione uma compra na lista.")
            return
        if QMessageBox.question(self, "Apagar compra",
                                "Apagar esta compra? Essa ação não pode ser desfeita.") != QMessageBox.Yes:
            return
        fin().apagar_compra(id_)
        self.mudou()
