"""Página Caixinhas: valor guardado, meta, progresso e quanto guardar por mês até a data alvo."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QDialog, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout
from controle_financeiro.dados.contexto import fin

from controle_financeiro.ui.componentes import BarraProgresso, FaixaNumeros, Formulario, Metrica, nova_tabela, preencher, selecionado, texto
from controle_financeiro.ui.formatacao import brl, data_br
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
        barra.setSpacing(10)
        ajuda = QLabel("Dê duplo clique em uma caixinha para editar. Meta e data alvo são opcionais.")
        ajuda.setObjectName("rotulo")
        ajuda.setWordWrap(True)
        barra.addWidget(ajuda, 1)
        for rotulo_botao, acao in (("Histórico", self.ver_historico), ("Retirar", self.retirar),
                                   ("Guardar", self.guardar)):
            b = QPushButton(rotulo_botao)
            b.clicked.connect(acao)
            barra.addWidget(b)
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
        self.aviso_historico = QLabel("O histórico das caixinhas ainda não está ativo: rode o script "
                                      "07_historico_caixinhas.sql no Supabase e abra o app de novo.")
        self.aviso_historico.setObjectName("rotulo")
        self.aviso_historico.setWordWrap(True)
        self.aviso_historico.hide()
        lay.addWidget(self.aviso_historico)

    def atualizar(self):
        self.aviso_historico.setVisible(not fin().caixinhas_tem_historico())
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

    # ----- guardar, retirar e histórico -----

    def _escolhida(self):
        id_ = selecionado(self.tab)
        c = fin().obter_caixinha(id_) if id_ is not None else None
        if not c:
            QMessageBox.information(self, "Caixinhas", "Selecione uma caixinha na lista.")
        return c

    def guardar(self):
        self._movimentar(retirar=False)

    def retirar(self):
        self._movimentar(retirar=True)

    def _movimentar(self, retirar):
        c = self._escolhida()
        if not c:
            return
        acao = "Retirar de" if retirar else "Guardar em"
        dlg = Formulario(self, f"{acao} {c['nome']}", [
            ("valor", f"Valor (hoje tem {brl(c['valor'])})", texto("", "R$ 0,00")),
            ("descricao", "Observação", texto("", "Opcional, ex.: salário de novembro")),
        ])
        if dlg.exec() != QDialog.Accepted:
            return
        v = dlg.valores()
        try:
            if retirar:
                fin().retirar_da_caixinha(c["id"], v["valor"], v["descricao"])
            else:
                fin().guardar_na_caixinha(c["id"], v["valor"], v["descricao"])
        except ValueError as e:
            self.erro(e)
            return
        self.mudou()

    def ver_historico(self):
        c = self._escolhida()
        if c:
            HistoricoCaixinha(self, c).exec()


class HistoricoCaixinha(QDialog):
    """Cada valor guardado, retirado ou ajustado numa caixinha, do mais novo para o mais antigo."""

    def __init__(self, pai, caixinha):
        super().__init__(pai)
        self.setWindowTitle(f"Histórico: {caixinha['nome']}")
        self.setMinimumSize(560, 420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel(f"{caixinha['nome']} ({caixinha['dono']})")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        saldo = QLabel(f"Valor hoje: {brl(caixinha['valor'])}")
        saldo.setObjectName("total")
        lay.addWidget(saldo)
        if fin().caixinhas_tem_historico():
            vazio = "Nenhum movimento ainda. Use Guardar ou Retirar para registrar."
        else:
            vazio = "O histórico ainda não está ativo: falta rodar o script 07 no Supabase."
        tab = nova_tabela(["Data", "Movimento", "Valor", "Ficou com"], vazio)
        preencher(tab, [(m["id"], [data_br(m["data"]), m["descricao"] or "—",
                                   ("+" if m["valor"] > 0 else "-") + brl(abs(m["valor"])),
                                   brl(m["saldo"])])
                        for m in fin().historico_caixinha(caixinha["id"])])
        lay.addWidget(tab, 1)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        lay.addWidget(fechar, 0, Qt.AlignmentFlag.AlignRight)
