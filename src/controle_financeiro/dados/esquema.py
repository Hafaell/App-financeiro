"""Estrutura das tabelas. Uma só definição, usada pelo SQLite (local) e pelo PostgreSQL (Supabase)."""

# Cada tabela é um modelo com marcadores que mudam conforme o banco:
#   {ID}   chave primária com numeração automática
#   {REAL} número com centavos
TABELAS = [
    """CREATE TABLE IF NOT EXISTS compras (
        id {ID},
        mes TEXT NOT NULL,
        cartao TEXT NOT NULL,
        item TEXT NOT NULL,
        parcelas TEXT NOT NULL DEFAULT '1/1',
        valor_parcela {REAL} NOT NULL,
        emprestimo INTEGER NOT NULL DEFAULT 0,
        pessoa TEXT NOT NULL DEFAULT '.',
        valor_real {REAL},
        recorrente INTEGER NOT NULL DEFAULT 0,
        categoria_id {INT}
    )""",
    """CREATE TABLE IF NOT EXISTS receitas (
        id {ID},
        mes TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor {REAL} NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS despesas (
        id {ID},
        mes TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor {REAL} NOT NULL,
        recorrente INTEGER NOT NULL DEFAULT 0,
        categoria_id {INT}
    )""",
    """CREATE TABLE IF NOT EXISTS caixinhas (
        id {ID},
        dono TEXT NOT NULL,
        nome TEXT NOT NULL,
        valor {REAL} NOT NULL DEFAULT 0,
        meta {REAL},
        data_alvo TEXT,
        UNIQUE (dono, nome)
    )""",
    """CREATE TABLE IF NOT EXISTS pagamentos (
        id {ID},
        pessoa TEXT NOT NULL,
        valor {REAL} NOT NULL,
        data TEXT NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        mes TEXT
    )""",
    """CREATE TABLE IF NOT EXISTS cartoes (
        id {ID},
        nome TEXT NOT NULL UNIQUE,
        cor TEXT NOT NULL,
        cor_texto TEXT NOT NULL,
        dia_fechamento {INT},
        dia_vencimento {INT}
    )""",
    """CREATE TABLE IF NOT EXISTS categorias (
        id {ID},
        nome TEXT NOT NULL UNIQUE,
        cor TEXT NOT NULL,
        orcamento {REAL} NOT NULL DEFAULT 0
    )""",
    """CREATE TABLE IF NOT EXISTS rendas (
        mes TEXT PRIMARY KEY,
        valor {REAL} NOT NULL
    )""",
    """CREATE TABLE IF NOT EXISTS sessoes (
        mes TEXT PRIMARY KEY
    )""",
    """CREATE TABLE IF NOT EXISTS meta (
        chave TEXT PRIMARY KEY,
        valor INTEGER NOT NULL
    )""",
]

# Tabelas com coluna id (usadas para devolver o id de um lançamento novo)
TABELAS_COM_ID = ("compras", "receitas", "despesas", "caixinhas", "pagamentos", "cartoes", "categorias")


def comandos(dialeto: str):
    """Devolve a lista de comandos CREATE TABLE para 'sqlite' ou 'postgres'."""
    if dialeto == "sqlite":
        subs = {"{ID}": "INTEGER PRIMARY KEY AUTOINCREMENT", "{REAL}": "REAL", "{INT}": "INTEGER"}
    else:
        subs = {"{ID}": "BIGSERIAL PRIMARY KEY", "{REAL}": "DOUBLE PRECISION", "{INT}": "BIGINT"}
    saida = []
    for modelo in TABELAS:
        comando = modelo
        for marca, valor in subs.items():
            comando = comando.replace(marca, valor)
        saida.append(comando)
    return saida
