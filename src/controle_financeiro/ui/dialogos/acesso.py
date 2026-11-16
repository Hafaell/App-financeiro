"""Entrar no app, conectar ao Supabase e Minha conta."""
from PySide6.QtWidgets import QComboBox, QDialog, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout

from controle_financeiro.dados.contexto import auth
from controle_financeiro.dados.nuvem import ErroConexao
from controle_financeiro.ui.componentes import texto
from controle_financeiro.ui.tema import VERMELHO_TEXTO


class Login(QDialog):
    """Primeira tela do app: entrar em uma conta ou criar uma nova.
    Se ainda não existir nenhum usuário, o app já abre direto em 'Criar conta'."""

    def __init__(self, usuario_inicial="", contas=None):
        super().__init__()
        self.setWindowTitle("Controle Financeiro")
        self.setMinimumWidth(400)
        self.usuario_conectado = None
        self.modo_criar = (not auth().nuvem) and not auth().listar_usuarios()
        self._cadastro_pendente = False
        self._pede_contas = contas is not None

        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(10)
        self.titulo = QLabel()
        self.titulo.setObjectName("secao")
        self.subtitulo = QLabel()
        self.subtitulo.setObjectName("rotulo")
        self.subtitulo.setWordWrap(True)
        self.usuario = texto(usuario_inicial, "E-mail" if auth().nuvem else "Usuário")
        self.rot_nome = QLabel("Seu nome")
        self.nome_cadastro = texto("", "Como você quer ser chamado")
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
        lay.addWidget(self.rot_nome)
        lay.addWidget(self.nome_cadastro)
        lay.addWidget(QLabel("E-mail" if auth().nuvem else "Usuário"))
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
        if auth().nuvem:
            self.subtitulo.setText(
                "Use seu e-mail. Só e-mails autorizados podem criar conta." if criar
                else "Digite seu e-mail e senha.")
        else:
            self.subtitulo.setText(
                "Crie um usuário e uma senha. Cada conta tem os seus próprios dados."
                if criar else "Digite seu usuário e senha.")
        mostrar_contas = not criar and bool(self._contas)
        self.rot_contas.setVisible(mostrar_contas)
        for i in range(self.botoes_contas.count()):
            self.botoes_contas.itemAt(i).widget().setVisible(mostrar_contas)
        self.sem_contas.setVisible(not criar and not self._contas and self._pede_contas)
        self.rot_nome.setVisible(criar and auth().nuvem)
        self.nome_cadastro.setVisible(criar and auth().nuvem)
        self.rot_confirma.setVisible(criar)
        self.confirma.setVisible(criar)
        self.principal.setText("Criar conta e entrar" if criar else "Entrar")
        self.alternar.setText("Entrar" if criar else "Criar conta")
        # Sem nenhum usuário cadastrado, só dá para criar conta
        self.alternar.setVisible(auth().nuvem or bool(auth().listar_usuarios()))
        self.erro.setText("")
        self.senha.clear()
        self.confirma.clear()
        if auth().nuvem:
            self.rot_contas.setVisible(False)

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
        try:
            entrou = auth().entrar(nome, self.senha.text())
        except ErroConexao as e:
            return self._erro(str(e))
        if entrou:
            self.usuario_conectado = entrou
            self.accept()
        else:
            self.senha.clear()
            self._erro("E-mail ou senha incorretos." if auth().nuvem else "Usuário ou senha incorretos.")

    def _criar(self):
        nome = self.usuario.text().strip()
        senha = self.senha.text()
        if not nome:
            return self._erro("Informe o e-mail." if auth().nuvem else "Informe o nome do usuário.")
        if not senha:
            return self._erro("Informe uma senha.")
        if len(senha) < 6:
            return self._erro("A senha precisa ter pelo menos 6 caracteres.")
        if senha != self.confirma.text():
            return self._erro("As senhas não são iguais.")
        if auth().nuvem:
            try:
                ja_entrou = auth().cadastrar(nome, senha, self.nome_cadastro.text())
            except (ValueError, ErroConexao) as e:
                return self._erro(str(e))
            if ja_entrou:
                self.usuario_conectado = nome
                return self.accept()
            # confirmação de e-mail ligada: volta para a tela de entrar
            self.modo_criar = False
            self._mostrar_modo()
            self.usuario.setText(nome)
            self.erro.setStyleSheet("color: #15803D;")
            self.erro.setText("Conta criada. Enviamos um e-mail para você confirmar. "
                              "Depois, entre com seu e-mail e senha.")
            return
        try:
            auth().cadastrar_usuario(nome, senha)
            self.usuario_conectado = auth().entrar(nome, senha)
        except (ValueError, ErroConexao) as e:
            return self._erro(str(e))
        self.accept()

    def _erro(self, mensagem):
        self.erro.setText(mensagem)
        self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")
        self.senha.setFocus()


class ConectarSupabase(QDialog):
    """Conexão com o Supabase: o token de acesso pessoal lista os projetos e o app guarda
    o projeto escolhido (criptografado). modo: 'inicio', 'token' ou 'projeto'."""

    def __init__(self, modo="inicio"):
        super().__init__()
        from controle_financeiro.dados.conexao import ler_conexao
        self.modo = modo
        self.dados_antigos = ler_conexao()
        self.token_usado = None
        self.trocou_projeto = False
        self.setWindowTitle("Controle Financeiro")
        self.setMinimumWidth(480)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(10)
        self.titulo = QLabel()
        self.titulo.setObjectName("secao")
        self.ajuda = QLabel()
        self.ajuda.setObjectName("rotulo")
        self.ajuda.setWordWrap(True)
        self.rot_token = QLabel("Token de acesso pessoal")
        self.token = QLineEdit()
        self.token.setPlaceholderText("sbp_...")
        self.token.setEchoMode(QLineEdit.EchoMode.Password)
        self.rot_projeto = QLabel("Projeto")
        self.projetos = QComboBox()
        self.erro = QLabel("")
        self.erro.setWordWrap(True)
        self.principal = QPushButton()
        self.principal.setObjectName("primario")
        self.principal.setDefault(True)
        self.principal.clicked.connect(self._acao)
        self.cancelar = QPushButton("Cancelar")
        self.cancelar.clicked.connect(self.reject)
        for w in (self.titulo, self.ajuda, self.rot_token, self.token, self.rot_projeto,
                  self.projetos, self.erro, self.principal, self.cancelar):
            lay.addWidget(w)

        if modo == "projeto" and self.dados_antigos.get("token"):
            self.token_usado = self.dados_antigos["token"]
            self._carregar_projetos()
        self._mostrar()

    def _lista_carregada(self):
        return self.projetos.count() > 0

    def _mostrar(self):
        carregada = self._lista_carregada()
        titulos = {"inicio": "Conectar ao Supabase", "token": "Trocar token de acesso",
                   "projeto": "Trocar projeto"}
        self.titulo.setText(titulos.get(self.modo, "Conectar ao Supabase"))
        self.ajuda.setText(
            "Crie um token em supabase.com > Account > Access Tokens e cole aqui. "
            "O app guarda o token criptografado neste computador, então você só precisa fazer isso "
            "uma vez. Depois, escolha o projeto." if not carregada else
            "Escolha o projeto que você quer usar.")
        self.rot_token.setVisible(not carregada and self.modo != "projeto")
        self.token.setVisible(not carregada and self.modo != "projeto")
        self.rot_projeto.setVisible(carregada)
        self.projetos.setVisible(carregada)
        self.principal.setText("Usar este projeto" if carregada else "Continuar")
        self.erro.setText("")

    def _acao(self):
        if self._lista_carregada():
            return self._usar_projeto()
        token = self.token.text().strip() or (self.dados_antigos.get("token") if self.modo == "projeto" else "")
        if not token:
            return self._erro("Cole o token de acesso.")
        self.token_usado = token
        self._carregar_projetos()

    def _carregar_projetos(self):
        from controle_financeiro.dados.conexao import listar_projetos
        from controle_financeiro.dados.nuvem import ErroConexao
        from controle_financeiro.dados.conexao import ErroProjeto
        try:
            lista = listar_projetos(self.token_usado)
        except (ErroConexao, ErroProjeto) as e:
            self.token_usado = None
            return self._erro(str(e))
        if not lista:
            self.token_usado = None
            return self._erro("Nenhum projeto encontrado nesta conta.")
        self.projetos.clear()
        for p in lista:
            self.projetos.addItem(p["nome"], p["ref"])
        self._mostrar()

    def _usar_projeto(self):
        from controle_financeiro.dados.conexao import ErroProjeto, credenciais_projeto, salvar_conexao
        from controle_financeiro.dados.nuvem import ErroConexao
        ref = self.projetos.currentData()
        nome = self.projetos.currentText()
        try:
            url, chave = credenciais_projeto(self.token_usado, ref)
        except (ErroConexao, ErroProjeto) as e:
            return self._erro(str(e))
        salvar_conexao({"token": self.token_usado, "ref": ref, "nome_projeto": nome,
                        "url": url, "chave": chave})
        self.trocou_projeto = ref != self.dados_antigos.get("ref")
        self.accept()

    def _erro(self, mensagem):
        self.erro.setText(mensagem)
        self.erro.setStyleSheet(f"color: {VERMELHO_TEXTO};")


class ContaDialog(QDialog):
    """Minha conta: mostra o nome e o projeto, e permite trocar o token ou o projeto."""

    def __init__(self, pai):
        super().__init__(pai)
        from controle_financeiro.dados.conexao import ler_conexao
        self.reiniciar = False
        self.setWindowTitle("Minha conta")
        self.setMinimumWidth(420)
        conf = ler_conexao()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(32, 28, 32, 28)
        lay.setSpacing(8)
        titulo = QLabel("Minha conta")
        titulo.setObjectName("secao")
        lay.addWidget(titulo)
        lay.addWidget(QLabel(f"Nome: {auth().nome_exibicao()}"))
        lay.addWidget(QLabel(f"E-mail: {auth().usuario_logado() or ''}"))
        lay.addWidget(QLabel(f"Projeto Supabase: {conf.get('nome_projeto') or 'não escolhido'}"))
        for texto_botao, acao in (("Trocar token de acesso", self._trocar_token),
                                  ("Trocar projeto", self._trocar_projeto),
                                  ("Fechar", self.accept)):
            b = QPushButton(texto_botao)
            b.clicked.connect(acao)
            lay.addWidget(b)

    def _trocar_token(self):
        if ConectarSupabase("token").exec() == QDialog.Accepted:
            QMessageBox.information(self, "Minha conta", "Token atualizado.")

    def _trocar_projeto(self):
        if self._ha_pendencias():
            QMessageBox.warning(self, "Minha conta",
                                "Há alterações esperando para serem enviadas ao projeto atual. "
                                "Conecte-se à internet e aguarde o envio antes de trocar o projeto.")
            return
        dialogo = ConectarSupabase("projeto")
        if dialogo.exec() != QDialog.Accepted:
            return
        if dialogo.trocou_projeto:
            self._limpar_cache()
            self.reiniciar = True
            self.accept()
        else:
            QMessageBox.information(self, "Minha conta", "Você continua no mesmo projeto.")

    def _ha_pendencias(self):
        from controle_financeiro.config import PASTA
        from controle_financeiro.seguranca.cofre import Cofre
        for arquivo in PASTA.glob("pendentes_*.dat"):
            try:
                if Cofre().decifrar(arquivo.read_bytes()):
                    return True
            except Exception:
                return True
        return False

    def _limpar_cache(self):
        from controle_financeiro.config import PASTA
        for arquivo in PASTA.glob("cache_*.dat"):
            arquivo.unlink(missing_ok=True)
