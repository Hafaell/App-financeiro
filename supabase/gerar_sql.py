"""Gera os arquivos SQL para colar no Supabase, a partir do banco local de um usuário.

    python supabase/gerar_sql.py Rafael

Cria duas pastas de saída (supabase/saida/):
  01_criar_banco.sql  -> cria o esquema e as tabelas (sem dados pessoais)
  02_dados.sql        -> copia os seus lançamentos do banco local
"""
import os
import sqlite3
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from financas.config import CARTOES_INICIAIS, PASTA  # noqa: E402
from financas.esquema import comandos  # noqa: E402
from financas.utilidades import slug  # noqa: E402

SAIDA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "saida")


def literal(valor):
    if valor is None:
        return "NULL"
    if isinstance(valor, (int, float)):
        return repr(valor)
    return "'" + str(valor).replace("'", "''") + "'"


def criar_banco_sql(esquema):
    linhas = [f'CREATE SCHEMA IF NOT EXISTS "{esquema}";', f'SET search_path TO "{esquema}";', ""]
    linhas += [c + ";" for c in comandos("postgres")]
    linhas.append("INSERT INTO meta (chave, valor) VALUES ('versao', 0) ON CONFLICT DO NOTHING;")
    for nome, cor, cor_texto in CARTOES_INICIAIS:
        linhas.append(f"INSERT INTO cartoes (nome, cor, cor_texto) VALUES "
                      f"({literal(nome)}, {literal(cor)}, {literal(cor_texto)}) ON CONFLICT DO NOTHING;")
    # Segurança: a API pública do Supabase não enxerga estas tabelas
    for tabela in ("compras", "receitas", "despesas", "caixinhas", "pagamentos",
                   "cartoes", "sessoes", "meta"):
        linhas.append(f'ALTER TABLE "{esquema}"."{tabela}" ENABLE ROW LEVEL SECURITY;')
    return "\n".join(linhas) + "\n"


def dados_sql(esquema, caminho_sqlite):
    con = sqlite3.connect(caminho_sqlite)
    con.row_factory = sqlite3.Row
    linhas = [f'SET search_path TO "{esquema}";', ""]

    def copiar(tabela, colunas, extra=""):
        for r in con.execute(f"SELECT {', '.join(colunas)} FROM {tabela} ORDER BY 1"):
            valores = ", ".join(literal(r[c]) for c in colunas)
            linhas.append(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES ({valores}){extra};")

    copiar("sessoes", ["mes"], " ON CONFLICT DO NOTHING")
    copiar("cartoes", ["nome", "cor", "cor_texto"], " ON CONFLICT DO NOTHING")
    copiar("compras", ["mes", "cartao", "item", "parcelas", "valor_parcela", "emprestimo",
                       "pessoa", "valor_real", "recorrente"])
    copiar("receitas", ["mes", "descricao", "valor"])
    copiar("despesas", ["mes", "descricao", "valor", "recorrente"])
    copiar("caixinhas", ["dono", "nome", "valor"],
           " ON CONFLICT (dono, nome) DO UPDATE SET valor = EXCLUDED.valor")
    copiar("pagamentos", ["pessoa", "valor", "data", "descricao", "mes"])
    con.close()
    return "\n".join(linhas) + "\n"


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: python supabase/gerar_sql.py <Usuario>   (ex.: Rafael)")
    usuario = sys.argv[1]
    esquema = f"financeiro_{slug(usuario)}"
    caminho = os.path.join(PASTA, f"financas_{slug(usuario)}.db")
    if not os.path.exists(caminho):
        sys.exit(f"Banco local não encontrado: {caminho}")
    os.makedirs(SAIDA, exist_ok=True)
    with open(os.path.join(SAIDA, "01_criar_banco.sql"), "w", encoding="utf-8") as f:
        f.write(criar_banco_sql(esquema))
    with open(os.path.join(SAIDA, "02_dados.sql"), "w", encoding="utf-8") as f:
        f.write(dados_sql(esquema, caminho))
    print(f"Pronto. Arquivos em {SAIDA}: 01_criar_banco.sql e 02_dados.sql")


if __name__ == "__main__":
    main()
