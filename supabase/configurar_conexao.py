"""Guarda a conexão com o Supabase de forma criptografada (conexao.dat).

Rode uma vez em cada computador, na pasta do projeto:
    python supabase/configurar_conexao.py
Você precisa de dois dados, que ficam no painel do Supabase em Project Settings > API:
  - Project URL (https://xxxx.supabase.co)
  - Chave publica "anon" (a chave pública, não a secret/service_role)
Nenhuma senha do banco é usada nem guardada.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from financas.config import CONEXAO_PATH  # noqa: E402
from financas.seguranca import Cofre  # noqa: E402


def main():
    url = input("Project URL do Supabase (https://...supabase.co): ").strip().rstrip("/")
    chave = input("Chave pública anon: ").strip()
    if not url.startswith("https://") or not chave:
        sys.exit("Informe a URL (começando com https://) e a chave pública anon.")
    if chave.startswith("sb_secret") or "service_role" in chave:
        sys.exit("Essa chave é secreta. Use a chave pública (anon).")
    CONEXAO_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONEXAO_PATH.write_bytes(Cofre().cifrar({"url": url, "chave": chave}))
    print(f"Conexão guardada, criptografada, em {CONEXAO_PATH}")
    print("Agora abra o app e entre com seu e-mail e senha do Supabase.")


if __name__ == "__main__":
    main()
