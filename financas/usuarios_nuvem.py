"""Usuários guardados no Supabase (esquema financeiro_sistema, tabela usuarios).

Qualquer computador com a conexão do Supabase configurada enxerga os mesmos usuários.
Só ficam guardados o nome, o salt e o hash da senha (PBKDF2). A senha em texto nunca é salva.
"""
import psycopg
from psycopg.rows import dict_row

from .banco import url_do_supabase

ESQUEMA_SISTEMA = "financeiro_sistema"

SQL_PREPARAR = [
    f'CREATE SCHEMA IF NOT EXISTS "{ESQUEMA_SISTEMA}"',
    f'CREATE TABLE IF NOT EXISTS "{ESQUEMA_SISTEMA}".usuarios ('
    "chave TEXT PRIMARY KEY, "
    "nome TEXT NOT NULL, "
    "salt TEXT NOT NULL, "
    "hash TEXT NOT NULL, "
    "criado_em TIMESTAMPTZ NOT NULL DEFAULT now())",
    f'ALTER TABLE "{ESQUEMA_SISTEMA}".usuarios ENABLE ROW LEVEL SECURITY',
]


class ErroConexaoNuvem(RuntimeError):
    """Não foi possível falar com o Supabase (sem internet ou conexão errada)."""


def chave_do_nome(nome) -> str:
    return str(nome or "").strip().lower()


class RepositorioNuvem:
    def __init__(self, url=None):
        self._url = url

    def _con(self):
        try:
            return psycopg.connect(self._url or url_do_supabase(), row_factory=dict_row,
                                   autocommit=True, connect_timeout=5)
        except psycopg.OperationalError as e:
            raise ErroConexaoNuvem(
                "Não consegui conectar ao Supabase. Verifique a internet e a conexão "
                "(supabase/configurar_conexao.py).") from e

    def preparar(self):
        with self._con() as con:
            for comando in SQL_PREPARAR:
                con.execute(comando)

    def listar(self):
        with self._con() as con:
            return con.execute(f'SELECT chave, nome, salt, hash FROM "{ESQUEMA_SISTEMA}".usuarios '
                               "ORDER BY nome").fetchall()

    def buscar(self, nome):
        with self._con() as con:
            return con.execute(f'SELECT chave, nome, salt, hash FROM "{ESQUEMA_SISTEMA}".usuarios '
                               "WHERE chave = %s", (chave_do_nome(nome),)).fetchone()

    def inserir(self, nome, salt, hash_):
        try:
            with self._con() as con:
                con.execute(f'INSERT INTO "{ESQUEMA_SISTEMA}".usuarios (chave, nome, salt, hash) '
                            "VALUES (%s, %s, %s, %s)",
                            (chave_do_nome(nome), nome, salt, hash_))
        except psycopg.errors.UniqueViolation as e:
            raise ValueError(f"O usuário {nome} já existe.") from e
