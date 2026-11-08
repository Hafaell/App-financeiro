"""Login. Com Supabase, os usuários ficam na nuvem (qualquer computador enxerga os mesmos).
Sem Supabase (modo local de testes), ficam criptografados em arquivo.
A sessão (só o nome do usuário logado) fica criptografada neste computador.
"""
import hashlib
import hmac
import json
import os

from cryptography.fernet import Fernet

from .config import CHAVE_PATH, PASTA, SESSAO_PATH, TIPO_BANCO, USUARIO_INICIAL, USUARIOS_PATH


def _hash_senha(senha: str, salt_hex: str) -> str:
    return hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"),
                               bytes.fromhex(salt_hex), 200_000).hex()


class Cofre:
    """Criptografa e descriptografa dados (Fernet, AES). A chave fica em um arquivo local."""

    def __init__(self, chave_path=CHAVE_PATH):
        if not chave_path.exists():
            chave_path.parent.mkdir(parents=True, exist_ok=True)
            chave_path.write_bytes(Fernet.generate_key())
        self._fernet = Fernet(chave_path.read_bytes())

    def cifrar(self, dados) -> bytes:
        return self._fernet.encrypt(json.dumps(dados).encode("utf-8"))

    def decifrar(self, token: bytes):
        return json.loads(self._fernet.decrypt(token).decode("utf-8"))


class Autenticacao:
    """Entrar no app.

    Com Supabase (TIPO_BANCO postgres): login pelo Supabase Auth (e-mail e senha).
    O token fica só na memória: nada de usuário ou senha no computador.
    Modo local (testes): usuários criptografados em arquivo, como antes.
    """

    def __init__(self, cofre: Cofre = None):
        self.cofre = cofre or Cofre()
        self.nuvem = TIPO_BANCO == "postgres"
        self.cliente = None
        if self.nuvem:
            import os
            from .banco import configuracao_supabase
            from .nuvem import ClienteSupabase
            url, chave = configuracao_supabase()
            prefixo = os.environ.get("SUPABASE_PREFIXO", "/rest/v1")  # vazio só nos testes locais
            self.cliente = ClienteSupabase(url, chave, prefixo_api=prefixo,
                                           ao_renovar=self._guardar_sessao_nuvem)
        else:
            self._preparar_local()

    # ----- modo local (testes) -----

    def _preparar_local(self):
        antigo = PASTA / "usuarios.json"
        if antigo.exists() and not USUARIOS_PATH.exists():
            dados = json.loads(antigo.read_text(encoding="utf-8"))
            self._gravar_usuarios([{"nome": n, "salt": d["salt"], "hash": d["hash"]}
                                   for n, d in dados.items()])
            antigo.unlink()  # não deixa cópia em texto puro
        (PASTA / "sessao.json").unlink(missing_ok=True)
        if not USUARIOS_PATH.exists():
            self._novo_usuario_local(*USUARIO_INICIAL)

    def _ler_usuarios(self):
        if not USUARIOS_PATH.exists():
            return []
        return self.cofre.decifrar(USUARIOS_PATH.read_bytes())

    def _gravar_usuarios(self, lista):
        USUARIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USUARIOS_PATH.write_bytes(self.cofre.cifrar(lista))

    def _achar_local(self, nome):
        alvo = str(nome or "").strip().lower()
        return next((u for u in self._ler_usuarios() if u["nome"].lower() == alvo), None)

    def _novo_usuario_local(self, nome, senha):
        nome = str(nome or "").strip()
        if not nome or not senha:
            raise ValueError("Informe usuário e senha.")
        if self._achar_local(nome):
            raise ValueError(f"O usuário {nome} já existe.")
        salt = os.urandom(16).hex()
        lista = self._ler_usuarios()
        lista.append({"nome": nome, "salt": salt, "hash": _hash_senha(senha, salt)})
        self._gravar_usuarios(lista)

    def nome_exibicao(self):
        """Nome para mostrar na tela (o nome do cadastro, ou o e-mail)."""
        if self.nuvem:
            if self.cliente and self.cliente.logado:
                return self.cliente.nome_exibicao()
            return ""
        return self.usuario_logado() or ""

    def cadastrar(self, email, senha, nome=None) -> bool:
        """Com Supabase: cria a conta. True = já entrou; False = confirme o e-mail antes."""
        if not self.nuvem:
            raise ValueError("Cadastro pelo app só existe com o Supabase.")
        from .nuvem import ErroBanco
        try:
            return self.cliente.cadastrar(email.strip(), senha, (nome or "").strip() or None)
        except ErroBanco as e:
            m = str(e).lower()
            if "already" in m or "registered" in m or "já" in m:
                raise ValueError("Este e-mail já tem conta. Use Entrar.") from e
            if "rate" in m or "too many" in m or "limit" in m:
                raise ValueError("Muitas tentativas seguidas. Espere alguns minutos e tente de novo.") from e
            if "database error" in m:
                raise ValueError("Este e-mail não está autorizado a criar conta. "
                                 "Peça para liberar o e-mail na lista de autorizados.") from e
            if "password" in m:
                raise ValueError("A senha não atende às regras do Supabase. Use pelo menos 6 caracteres.") from e
            if "invalid" in m and "email" in m:
                raise ValueError("E-mail inválido. Confira o endereço digitado.") from e
            raise ValueError(f"Não foi possível criar a conta: {e}") from e

    def cadastrar_usuario(self, nome, senha):
        """Só no modo local. Com Supabase, os usuários são criados no painel do Supabase."""
        if self.nuvem:
            raise ValueError("Crie os usuários no painel do Supabase (Authentication > Users).")
        self._novo_usuario_local(nome, senha)

    def listar_usuarios(self):
        if self.nuvem:
            return []
        return sorted(u["nome"] for u in self._ler_usuarios())

    # ----- entrar e sair -----

    def entrar(self, identificacao: str, senha: str):
        """Confere o login. Devolve o nome de quem entrou, ou None se estiver errado.
        Erros de conexão (sem internet) são levantados para a tela mostrar."""
        if self.nuvem:
            from .nuvem import SessaoExpirada
            try:
                self.cliente.entrar(identificacao.strip(), senha)
            except SessaoExpirada:
                return None
            return self.cliente.usuario_email
        usuario = self._achar_local(identificacao)
        if usuario and hmac.compare_digest(_hash_senha(senha or "", usuario["salt"]), usuario["hash"]):
            self._gravar_sessao(usuario["nome"])
            return usuario["nome"]
        return None

    def usuario_logado(self):
        """Quem entrou nesta janela do app (a tela pede login a cada abertura)."""
        if self.nuvem:
            return self.cliente.usuario_email if self.cliente and self.cliente.logado else None
        if not SESSAO_PATH.exists():
            return None
        return self.cofre.decifrar(SESSAO_PATH.read_bytes()).get("usuario")

    def usuario_servico(self):
        """Para o Claude (servidor MCP): usa a sessão guardada neste computador, se houver.
        Não pede senha; usa só o refresh token guardado de forma criptografada."""
        if not self.nuvem:
            return self.usuario_logado()
        if self.cliente.logado:
            return self.cliente.usuario_email
        sessao = self._ler_sessao_nuvem()
        if not sessao:
            return None
        from .nuvem import ErroConexao
        try:
            return sessao["email"] if self.cliente.restaurar(sessao["refresh"], sessao["email"]) else None
        except ErroConexao:
            return None

    def sair(self):
        if self.nuvem:
            self.cliente.sair()
            SESSAO_PATH.unlink(missing_ok=True)  # o Claude também perde o acesso
        else:
            self._gravar_sessao(None)

    def _guardar_sessao_nuvem(self, refresh, email):
        SESSAO_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSAO_PATH.write_bytes(self.cofre.cifrar({"refresh": refresh, "email": email}))

    def _ler_sessao_nuvem(self):
        if not SESSAO_PATH.exists():
            return None
        try:
            dados = self.cofre.decifrar(SESSAO_PATH.read_bytes())
        except Exception:
            return None
        return dados if dados.get("refresh") else None

    def _gravar_sessao(self, usuario):
        SESSAO_PATH.write_bytes(self.cofre.cifrar({"usuario": usuario}))
