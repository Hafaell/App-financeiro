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
    """Cadastro de usuários, conferência de login e sessão atual."""

    def __init__(self, cofre: Cofre = None, repositorio=None):
        self.cofre = cofre or Cofre()
        self._nuvem = repositorio if repositorio is not None else _repositorio_padrao()
        self._pronto = False
        if self._nuvem is None:
            self._preparar_local()
            self._pronto = True
        else:
            from .usuarios_nuvem import ErroConexaoNuvem  # import tardio: evita ciclo com banco.py
            try:
                self._preparar_nuvem()
                self._pronto = True
            except ErroConexaoNuvem:
                pass  # sem internet: tenta de novo quando precisar (ex.: ao entrar)

    def _garantir(self):
        """Na nuvem, prepara os usuários na primeira vez que for preciso (exige internet)."""
        if not self._pronto:
            self._preparar_nuvem()
            self._pronto = True

    # ----- preparo -----

    def _preparar_local(self):
        """Modo local: traz os usuários do formato antigo e cria o usuário inicial."""
        antigo = PASTA / "usuarios.json"
        if antigo.exists() and not USUARIOS_PATH.exists():
            dados = json.loads(antigo.read_text(encoding="utf-8"))
            self._gravar_usuarios([{"nome": n, "salt": d["salt"], "hash": d["hash"]}
                                   for n, d in dados.items()])
            antigo.unlink()  # não deixa cópia em texto puro
        (PASTA / "sessao.json").unlink(missing_ok=True)  # sessão antiga, em texto puro
        if not USUARIOS_PATH.exists():
            self._novo_usuario_local(*USUARIO_INICIAL)

    def _preparar_nuvem(self):
        """Supabase: cria a tabela, envia os usuários que estavam neste computador e
        cria o usuário inicial se a tabela estiver vazia."""
        self._nuvem.preparar()
        if USUARIOS_PATH.exists():
            for u in self._ler_usuarios():
                if not self._nuvem.buscar(u["nome"]):
                    self._nuvem.inserir(u["nome"], u["salt"], u["hash"])
            USUARIOS_PATH.unlink()  # senhas saem deste computador: ficam só no Supabase
        (PASTA / "sessao.json").unlink(missing_ok=True)
        if not self._nuvem.listar():
            self._novo_usuario(*USUARIO_INICIAL)

    # ----- leitura dos usuários (nuvem ou arquivo local) -----

    def _ler_usuarios(self):
        if not USUARIOS_PATH.exists():
            return []
        return self.cofre.decifrar(USUARIOS_PATH.read_bytes())

    def _gravar_usuarios(self, lista):
        USUARIOS_PATH.parent.mkdir(parents=True, exist_ok=True)
        USUARIOS_PATH.write_bytes(self.cofre.cifrar(lista))

    def _achar(self, nome):
        if self._nuvem is not None:
            return self._nuvem.buscar(nome)
        alvo = str(nome or "").strip().lower()
        return next((u for u in self._ler_usuarios() if u["nome"].lower() == alvo), None)

    def listar_usuarios(self):
        self._garantir()
        if self._nuvem is not None:
            return sorted(u["nome"] for u in self._nuvem.listar())
        return sorted(u["nome"] for u in self._ler_usuarios())

    def nome_usuario(self, nome):
        self._garantir()
        usuario = self._achar(nome)
        return usuario["nome"] if usuario else None

    # ----- cadastro -----

    def cadastrar_usuario(self, nome, senha):
        self._garantir()
        self._novo_usuario(nome, senha)

    def _novo_usuario(self, nome, senha):
        nome = str(nome or "").strip()
        if not nome or not senha:
            raise ValueError("Informe usuário e senha.")
        salt = os.urandom(16).hex()
        self._nuvem.inserir(nome, salt, _hash_senha(senha, salt))

    def _novo_usuario_local(self, nome, senha):
        nome = str(nome or "").strip()
        if not nome or not senha:
            raise ValueError("Informe usuário e senha.")
        if self._achar(nome):
            raise ValueError(f"O usuário {nome} já existe.")
        salt = os.urandom(16).hex()
        lista = self._ler_usuarios()
        lista.append({"nome": nome, "salt": salt, "hash": _hash_senha(senha, salt)})
        self._gravar_usuarios(lista)

    def verificar_login(self, nome, senha) -> bool:
        self._garantir()
        usuario = self._achar(nome)
        return bool(usuario) and hmac.compare_digest(
            _hash_senha(senha or "", usuario["salt"]), usuario["hash"])

    # ----- sessão (só o nome de quem está logado, criptografado neste computador) -----

    def definir_sessao(self, nome):
        real = self.nome_usuario(nome)
        if not real:
            raise ValueError("Usuário não encontrado.")
        self._gravar_sessao(real)

    def encerrar_sessao(self):
        self._gravar_sessao(None)

    def usuario_logado(self):
        if not SESSAO_PATH.exists():
            return None
        return self.cofre.decifrar(SESSAO_PATH.read_bytes()).get("usuario")

    def _gravar_sessao(self, usuario):
        SESSAO_PATH.write_bytes(self.cofre.cifrar({"usuario": usuario}))


def _repositorio_padrao():
    """Supabase quando o app está configurado para ele; None no modo local."""
    if TIPO_BANCO != "postgres":
        return None
    from .usuarios_nuvem import RepositorioNuvem
    return RepositorioNuvem()

