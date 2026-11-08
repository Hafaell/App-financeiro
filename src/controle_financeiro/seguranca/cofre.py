"""Criptografia dos arquivos locais (chave em chave.key, criada no primeiro uso)."""
import hashlib
import json

from cryptography.fernet import Fernet

from controle_financeiro.config import CHAVE_PATH


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
