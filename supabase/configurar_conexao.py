"""Guarda a conexão do Supabase de forma criptografada (conexao.dat).

Rode uma vez, na pasta do projeto:
    python supabase/configurar_conexao.py
Cole a URI de conexão do Supabase quando pedir (ela não aparece na tela).
"""
import getpass
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financas.config import CONEXAO_PATH  # noqa: E402
from financas.seguranca import Cofre  # noqa: E402


def main():
    url = getpass.getpass("Cole a URI de conexão do Supabase (não aparece na tela): ").strip()
    if not url.startswith("postgres"):
        sys.exit("A URI precisa começar com postgresql:// ou postgres://")
    CONEXAO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONEXAO_PATH.write_bytes(Cofre().cifrar({"url": url}))
    print(f"Conexão guardada, criptografada, em {CONEXAO_PATH}")
    print("Agora abra o app: ele passa a usar o Supabase.")


if __name__ == "__main__":
    main()
