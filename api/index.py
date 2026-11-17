"""Vercel Function (Python): entrega a API da versão web.

As rotas ficam em src/controle_financeiro/web/api.py (mesmo pacote do desktop, testado pelo
pytest). O Vercel inclui a pasta src pela opção includeFiles do vercel.json.
"""
import os
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("FINANCAS_PASTA", "/tmp/ControleFinanceiro")  # único lugar com escrita
os.environ.setdefault("FINANCAS_BANCO", "postgres")
# O servidor do Vercel roda em UTC e não aceita a variável TZ no painel (nome reservado).
# Sem isto, perto da meia-noite o "mês atual" e a data dos lançamentos sairiam no dia seguinte.
os.environ["TZ"] = os.environ.get("FINANCAS_FUSO", "America/Sao_Paulo")
if hasattr(time, "tzset"):
    time.tzset()

from controle_financeiro.web.api import app  # noqa: E402

__all__ = ["app"]
