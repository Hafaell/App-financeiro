"""API da versão web (Vercel Function em Python).

Fase 0: só o esqueleto. Cada rota chamará um método da fachada Financas (nucleo/servico.py),
com o JWT do usuário vindo do cabeçalho Authorization. Veja docs/vercel/PLANO.md e API.md.
"""
import sys
from pathlib import Path

# O pacote do app fica em src/ (mesmo código do desktop); o Vercel inclui essa pasta
# pela opção includeFiles do vercel.json.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from fastapi import FastAPI  # noqa: E402

app = FastAPI(title="Controle Financeiro", docs_url="/api/docs", openapi_url="/api/openapi.json")


@app.get("/api/saude")
def saude():
    """Confere se a função está no ar (não toca no Supabase)."""
    return {"ok": True}


# Fase 1 (a fazer):
# def financas_da_requisicao(authorization: str = Header(...)) -> Financas:
#     cliente = ClienteSupabase(*configuracao_supabase()); cliente.usar_token(<jwt>)
#     return Financas(BancoWeb(cliente), pasta_backups=...)
#
# @app.get("/api/meses")   -> sessoes(), mes_ativo()
# @app.get("/api/resumo")  -> resumo_mes(mes)
