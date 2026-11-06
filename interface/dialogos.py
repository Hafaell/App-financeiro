"""Janelas de diálogo: login, novo cartão, meses, compra e edição."""
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QDialog, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton,
    QVBoxLayout, QWidget,
)
from financas.contexto import auth, fin
from .componentes import Formulario, combo, nova_tabela, preencher, selecionado, texto
from .formatacao import categorias_opcoes, id_categoria, nome_categoria, SEM_CATEGORIA, _parcela_exibida, _pessoa_exibida, brl, nomes_cartoes
from .tema import VERMELHO_TEXTO


def campos_compra(c=None):
    """Campos do formulário de compra. Pessoa preenchida = empréstimo."""
    def valor(chave, padrao=""):
        return c[chave] if c is not None else padrao
    recorrente = QCheckBox("Recorrente: permanece no próximo mês")
    recorrente.setChecked(bool(valor("recorrente", 0)))
    return [
        ("cartao", "Cartão", combo(nomes_cartoes(), valor("cartao", None))),
        ("item", "Descrição", texto(valor("item"), "Ex.: Mercado")),
        ("categoria", "Categoria", combo(categorias_opcoes(),
                                         nome_categoria(c["categoria_id"]) if c else SEM_CATEGORIA)),
        ("parcelas", "Parcelas", texto(_parcela_exibida(c) if c else "", "Ex.: 3/12 (vazio = à vista)")),
        ("valor_parcela", "Valor da parcela",
         texto(brl(c["valor_parcela"]) if c else "", "R$ 0,00")),
        ("pessoa", "Pessoa (preencha só se for empréstimo)",
         texto(_pessoa_exibida(c) if c else "", "Ex.: Pai, Avô, Benzinho")),
        ("valor_real", "Valor real",
         texto(brl(c["valor_real"]) if c and c["valor_real"] is not None else "", "Opcional")),
        ("recorrente", "", recorrente),
    ]


def dialogo_compra(pai, c):
    """Abre a janela de edição de uma compra. Só altera o registro existente."""
    dlg = Formulario(pai, "Editar compra", campos_compra(c))
    if dlg.exec() != QDialog.Accepted:
        return False
    v = dlg.valores()
    try:
        fin().atualizar_compra(c["id"], v["cartao"], v["item"], v["parcelas"],
                              v["valor_parcela"], pessoa=v["pessoa"],
                              valor_real=v["valor_real"] or None,
                              recorrente=v["recorrente"], categoria_id=id_categoria(v["categoria"]))
    except ValueError as e:
        QMessageBox.warning(pai, "Não consegui salvar", str(e))
        return False
    return True


class NovoCartao(QDialog):
    """Cadastra um cartão com nome e cor. Ele passa a aparecer em Transações e em Despesas."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Novo cartão")
        self.setMinimumWidth(380)
        self.cor = "#2359D7"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel("Novo cartão")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        lay.addWidget(QLabel("Nome"))
        self.nome = texto("", "Ex.: C6, Itaú, Mercado Pago")
        self.nome.textChanged.connect(self._mostrar_previa)
        lay.addWidget(self.nome)
        lay.addWidget(QLabel("Cor do balão"))
        escolher = QPushButton("Escolher cor")
        escolher.clicked.connect(self._escolher_cor)
        lay.addWidget(escolher, 0, Qt.AlignmentFlag.AlignLeft)
        self.previa = QLabel()
        self.previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previa.setMinimumHeight(48)
        lay.addWidget(self.previa)
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        lay.addWidget(self.erro)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(cancelar)
        botoes.addWidget(salvar)
        lay.addLayout(botoes)
        self._mostrar_previa()

    def _escolher_cor(self):
        cor = QColorDialog.getColor(QColor(self.cor), self, "Cor do cartão")
        if cor.isValid():
            self.cor = cor.name().upper()
            self._mostrar_previa()

    def _mostrar_previa(self):
        nome = self.nome.text().strip() or "Nome do cartão"
        self.previa.setText(nome)
        self.previa.setStyleSheet(
            f"background: {self.cor}; color: {fin().cor_texto_para(self.cor)};"
            "border-radius: 16px; padding: 8px 20px; font-weight: 700;")

    def _salvar(self):
        try:
            fin().adicionar_cartao(self.nome.text(), self.cor)
        except ValueError as e:
            self.erro.setText(str(e))
            self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
            return
        self.accept()


class Login(QDialog):
    """Primeira tela do app: entrar em uma conta ou criar uma nova.
    Se ainda não existir nenhum usuário, o app já abre direto em 'Criar conta'."""

    def __init__(self, usuario_inicial="", contas=None):
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.setMinimumWidth(400)
        self.usuario_conectado = None
        self.modo_criar = not auth().listar_usuarios()
        self._pede_contas = contas is not None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(10)
        self.titulo = QLabel()
        self.titulo.setObjectName("secao")
        self.subtitulo = QLabel()
        self.subtitulo.setObjectName("rotulo")
        self.subtitulo.setWordWrap(True)
        self.usuario = texto(usuario_inicial, "Usuário")
        self.senha = texto("", "Senha")
        self.senha.setEchoMode(QLineEdit.EchoMode.Password)
        self.rot_confirma = QLabel("Repita a senha")
        self.confirma = texto("", "Repita a senha")
        self.confirma.setEchoMode(QLineEdit.EchoMode.Password)
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        self.principal = QPushButton()
        self.principal.setObjectName("primario")
        self.principal.setDefault(True)
        self.principal.clicked.connect(self._acao_principal)
        self.alternar = QPushButton()
        self.alternar.clicked.connect(self._alternar)

        lay.addWidget(self.titulo)
        lay.addWidget(self.subtitulo)
        self.rot_contas = QLabel("Contas nesta máquina")
        self.rot_contas.setObjectName("rotulo")
        lay.addWidget(self.rot_contas)
        self.botoes_contas = QVBoxLayout()
        self.botoes_contas.setSpacing(6)
        for nome in (contas or []):
            b = QPushButton(nome)
            b.clicked.connect(lambda _=False, n=nome: self._escolher_conta(n))
            self.botoes_contas.addWidget(b)
        lay.addLayout(self.botoes_contas)
        self.sem_contas = QLabel("Nenhuma outra conta nesta máquina.")
        self.sem_contas.setObjectName("rotulo")
        lay.addWidget(self.sem_contas)
        self._contas = list(contas or [])
        lay.addWidget(QLabel("Usuário"))
        lay.addWidget(self.usuario)
        lay.addWidget(QLabel("Senha"))
        lay.addWidget(self.senha)
        lay.addWidget(self.rot_confirma)
        lay.addWidget(self.confirma)
        lay.addWidget(self.erro)
        lay.addWidget(self.principal)
        lay.addWidget(self.alternar)
        self.senha.returnPressed.connect(self._acao_principal)
        self.confirma.returnPressed.connect(self._acao_principal)
        self._mostrar_modo()

    def _mostrar_modo(self):
        criar = self.modo_criar
        self.titulo.setText("Criar conta" if criar else "Entrar")
        self.subtitulo.setText(
            "Crie um usuário e uma senha. Cada conta tem os seus próprios dados."
            if criar else "Digite seu usuário e senha.")
        mostrar_contas = not criar and bool(self._contas)
        self.rot_contas.setVisible(mostrar_contas)
        for i in range(self.botoes_contas.count()):
            self.botoes_contas.itemAt(i).widget().setVisible(mostrar_contas)
        self.sem_contas.setVisible(not criar and not self._contas and self._pede_contas)
        self.rot_confirma.setVisible(criar)
        self.confirma.setVisible(criar)
        self.principal.setText("Criar conta e entrar" if criar else "Entrar")
        self.alternar.setText("Entrar" if criar else "Criar conta")
        # Sem nenhum usuário cadastrado, só dá para criar conta
        self.alternar.setVisible(bool(auth().listar_usuarios()))
        self.erro.setText("")
        self.senha.clear()
        self.confirma.clear()

    def _escolher_conta(self, nome):
        self.usuario.setText(nome)
        self.senha.clear()
        self.senha.setFocus()

    def _alternar(self):
        self.modo_criar = not self.modo_criar
        self._mostrar_modo()

    def _acao_principal(self):
        if self.modo_criar:
            self._criar()
        else:
            self._entrar()

    def _entrar(self):
        nome = self.usuario.text().strip()
        if auth().verificar_login(nome, self.senha.text()):
            self.usuario_conectado = auth().nome_usuario(nome)
            self.accept()
        else:
            self.senha.clear()
            self._erro("Usuário ou senha incorretos.")

    def _criar(self):
        nome = self.usuario.text().strip()
        senha = self.senha.text()
        if not nome:
            return self._erro("Informe o nome do usuário.")
        if not senha:
            return self._erro("Informe uma senha.")
        if senha != self.confirma.text():
            return self._erro("As senhas não são iguais.")
        try:
            auth().cadastrar_usuario(nome, senha)
        except ValueError as e:
            return self._erro(str(e))
        self.usuario_conectado = auth().nome_usuario(nome)
        self.accept()

    def _erro(self, mensagem):
        self.erro.setText(mensagem)
        self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
        self.senha.setFocus()


class GerenciarMeses(QDialog):
    """Lista os meses abertos. Você pode apagar os antigos; o mês atual não pode ser apagado."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Meses abertos")
        self.setMinimumWidth(380)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        titulo = QLabel("Meses abertos")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        self._linhas = QVBoxLayout()
        self._linhas.setSpacing(8)
        lay.addLayout(self._linhas)
        fechar = QPushButton("Fechar")
        fechar.clicked.connect(self.accept)
        lay.addWidget(fechar, 0, Qt.AlignmentFlag.AlignRight)
        self._montar()

    def _montar(self):
        while self._linhas.count():
            item = self._linhas.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        ativo = fin().mes_ativo()
        for m in reversed(fin().sessoes()):
            linha = QHBoxLayout()
            linha.addWidget(QLabel(fin().nome_mes(m)))
            linha.addStretch()
            if m == ativo:
                atual = QLabel("Mês atual")
                atual.setObjectName("rotulo")
                linha.addWidget(atual)
            else:
                apagar = QPushButton("Apagar")
                apagar.clicked.connect(lambda _=False, mes=m: self._apagar(mes))
                linha.addWidget(apagar)
            caixa = QWidget()
            caixa.setLayout(linha)
            self._linhas.addWidget(caixa)

    def _apagar(self, mes):
        pergunta = (f"Apagar {fin().nome_mes(mes)} e todos os seus lançamentos? "
                    "Essa ação não pode ser desfeita.")
        if QMessageBox.question(self, "Apagar mês", pergunta) != QMessageBox.Yes:
            return
        try:
            fin().apagar_mes(mes)
        except ValueError as e:
            QMessageBox.warning(self, "Não consegui apagar", str(e))
            return
        self._montar()


class CategoriaForm(QDialog):
    """Cria ou edita uma categoria: nome, cor, orçamento mensal e prévia."""

    def __init__(self, pai, categoria=None):
        super().__init__(pai)
        self.setWindowTitle("Categoria")
        self.setMinimumWidth(380)
        self.categoria = categoria
        self.cor = categoria["cor"] if categoria else "#2359D7"
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Nova categoria" if not categoria else "Editar categoria"))
        self.nome = texto(categoria["nome"] if categoria else "", "Ex.: Mercado, Academia")
        self.nome.textChanged.connect(self._previa)
        lay.addWidget(QLabel("Nome"))
        lay.addWidget(self.nome)
        self.orcamento = texto(brl(categoria["orcamento"]) if categoria and categoria["orcamento"] else "",
                               "Limite mensal, ex.: R$ 800,00 (vazio = sem limite)")
        lay.addWidget(QLabel("Orçamento mensal"))
        lay.addWidget(self.orcamento)
        escolher = QPushButton("Escolher cor")
        escolher.clicked.connect(self._escolher_cor)
        lay.addWidget(escolher, 0, Qt.AlignmentFlag.AlignLeft)
        self.previa = QLabel()
        self.previa.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.previa.setMinimumHeight(40)
        lay.addWidget(self.previa)
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        lay.addWidget(self.erro)
        botoes = QHBoxLayout()
        botoes.addStretch()
        cancelar = QPushButton("Cancelar")
        cancelar.clicked.connect(self.reject)
        salvar = QPushButton("Salvar")
        salvar.setObjectName("primario")
        salvar.clicked.connect(self._salvar)
        botoes.addWidget(cancelar)
        botoes.addWidget(salvar)
        lay.addLayout(botoes)
        self._previa()

    def _escolher_cor(self):
        cor = QColorDialog.getColor(QColor(self.cor), self, "Cor da categoria")
        if cor.isValid():
            self.cor = cor.name().upper()
            self._previa()

    def _previa(self):
        nome = self.nome.text().strip() or "Nome da categoria"
        self.previa.setText(nome)
        self.previa.setStyleSheet(f"background: {self.cor}; color: {core_cor_texto(self.cor)};"
                                  "border-radius: 14px; padding: 6px 18px; font-weight: 700;")

    def _salvar(self):
        try:
            if self.categoria:
                fin().atualizar_categoria(self.categoria["id"], self.nome.text(), self.cor,
                                          self.orcamento.text())
            else:
                fin().adicionar_categoria(self.nome.text(), self.cor, self.orcamento.text())
        except ValueError as e:
            self.erro.setText(str(e))
            self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
            return
        self.accept()


def core_cor_texto(cor):
    return fin().cor_texto_para(cor)


class CategoriasDialog(QDialog):
    """Lista as categorias: criar, editar (duplo clique) e apagar."""

    def __init__(self, pai):
        super().__init__(pai)
        self.setWindowTitle("Categorias")
        self.setMinimumSize(460, 420)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(24, 22, 24, 20)
        lay.setSpacing(12)
        lay.addWidget(QLabel("Categorias"))
        self.tab = nova_tabela(["Nome", "Orçamento mensal"])
        self.tab.doubleClicked.connect(lambda _i: self.editar())
        lay.addWidget(self.tab, 1)
        botoes = QHBoxLayout()
        apagar = QPushButton("Apagar")
        apagar.clicked.connect(self.apagar)
        nova = QPushButton("Nova categoria")
        nova.setObjectName("primario")
        nova.clicked.connect(self.nova)
        botoes.addWidget(apagar)
        botoes.addStretch()
        botoes.addWidget(nova)
        lay.addLayout(botoes)
        self._carregar()

    def _carregar(self):
        preencher(self.tab, [(c["id"], [c["nome"], brl(c["orcamento"]) if c["orcamento"] else "Sem limite"])
                             for c in fin().listar_categorias()])

    def nova(self):
        if CategoriaForm(self).exec() == QDialog.Accepted:
            self._carregar()

    def editar(self):
        id_ = selecionado(self.tab)
        c = fin().listar_categorias()
        atual = next((x for x in c if x["id"] == id_), None)
        if atual and CategoriaForm(self, atual).exec() == QDialog.Accepted:
            self._carregar()

    def apagar(self):
        id_ = selecionado(self.tab)
        if id_ is None:
            return
        pergunta = "Apagar esta categoria? Os lançamentos dela ficam sem categoria."
        if QMessageBox.question(self, "Apagar categoria", pergunta) != QMessageBox.Yes:
            return
        fin().apagar_categoria(id_)
        self._carregar()
