"""Roda a API da versão web no PC, sem Supabase: SQLite temporário com dados de exemplo.
Serve para ver e testar o site sem tocar nos dados reais.

    python -m controle_financeiro.web.local          (API em http://127.0.0.1:8000)
    cd web && npm run dev:local                      (site em http://localhost:5173)
"""
import tempfile
from pathlib import Path

from controle_financeiro.dados.banco import BancoSqlite
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.web import api


def _exemplo(fin: Financas):
    """Alguns lançamentos para as telas não ficarem vazias."""
    cats = {c["nome"]: c["id"] for c in fin.listar_categorias()}
    fin.adicionar_lancamento("receitas", "Salário", "5200")
    fin.adicionar_lancamento("despesas", "Aluguel", "1450", recorrente=True, categoria_id=cats.get("Outros"))
    fin.adicionar_lancamento("despesas", "Dentista (2/5)", "180", categoria_id=cats.get("Saúde"))
    compras = [
        ("Inter", "Mercado Extra", "412,37", "1/1", ".", "Alimentação"),
        ("Nubank", "Notebook", "389,90", "3/10", ".", "Outros"),
        ("Inter", "Uber", "86,40", "1/1", ".", "Transporte"),
        ("Nubank", "Spotify", "21,90", "1/1", ".", "Assinaturas"),
        ("Nubank", "Tênis", "249,99", "1/2", "Pai", None),
        ("Inter", "Presente", "120", "1/1", "Benzinho", None),
        ("Inter", "Cinema", "64", "1/1", ".", "Lazer"),
    ]
    for cartao, item, valor, parcelas, pessoa, cat in compras:
        fin.lancar_compra(cartao, item, valor, parcelas, pessoa=pessoa, recorrente=item == "Spotify",
                          categoria_id=cats.get(cat) if cat else None)
    fin.registrar_pagamento("Pai", "100")
    fin.definir_renda("5200")
    fin.atualizar_categoria(cats["Alimentação"], "Alimentação", "#F59E0B", 400)
    fin.atualizar_categoria(cats["Lazer"], "Lazer", "#EC4899", 150)
    fin.definir_caixinha("Rafael", "Viagem", "1800")
    caixa = fin.listar_caixinhas()[0]["id"]
    fin.definir_meta_caixinha(caixa, "5000", "2027-07")
    fin.definir_caixinha("Rafael", "Reserva", "6200")


def main():
    import uvicorn

    pasta = Path(tempfile.mkdtemp(prefix="cf_web_local_"))
    banco = BancoSqlite(pasta / "local.db")
    fin = Financas(banco, copias_no_banco=True)
    _exemplo(fin)
    api.app.dependency_overrides[api.financas] = lambda: Financas(banco, copias_no_banco=True)
    print(f"Dados de teste em {pasta}")
    uvicorn.run(api.app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
