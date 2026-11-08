"""Configuração dos testes: dados em pasta temporária e banco SQLite local (nada vai ao Supabase)."""
import os
import tempfile
from pathlib import Path

_TMP = Path(tempfile.mkdtemp(prefix="cf_testes_"))
os.environ["LOCALAPPDATA"] = str(_TMP)
os.environ["FINANCAS_BANCO"] = "sqlite"
os.environ["FINANCAS_DB"] = str(_TMP / "teste.db")
