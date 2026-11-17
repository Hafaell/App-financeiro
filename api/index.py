"""Vercel Function (Python): entrega a API da versão web.

As rotas ficam em src/controle_financeiro/web/api.py (mesmo pacote do desktop, testado pelo
pytest). O Vercel inclui a pasta src pela opção includeFiles do vercel.json.
"""
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
os.environ.setdefault("FINANCAS_PASTA", "/tmp/ControleFinanceiro")  # único lugar com escrita
os.environ.setdefault("FINANCAS_BANCO", "postgres")

from controle_financeiro.web.api import app  # noqa: E402

__all__ = ["app"]
