"""Acesso aos dados de um usuário.

Dois bancos, com a mesma interface:
- BancoSqlite: arquivo local (padrão).
- BancoPostgres: Supabase (PostgreSQL). Cada usuário tem um esquema próprio, `financeiro_<usuario>`.

O restante do projeto não sabe qual dos dois está sendo usado.
"""
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path

from .config import (BANCO_FORCADO, CARTOES_INICIAIS, CATEGORIAS_INICIAIS, CONEXAO_PATH, DATABASE_URL,
                     PASTA, TIPO_BANCO)
from .seguranca import Cofre
from .esquema import TABELAS_COM_ID, comandos
from .utilidades import mes_do_calendario, slug


TABELAS_SINCRONIA = ("cartoes", "categorias", "rendas", "sessoes", "compras", "receitas",
                     "despesas", "caixinhas", "pagamentos", "meta")
INTERVALO_VERIFICACAO = 1.0  # segundos entre verificações de mudança no Supabase
INTERVALO_TENTATIVA = 5.0    # segundos entre tentativas de reconectar, quando offline
try:
    import psycopg
    ERROS_CONEXAO = (psycopg.OperationalError,)
except ImportError:  # psycopg só é necessário com o Supabase
    ERROS_CONEXAO = ()
_TABELA_RE = re.compile(r"(?:INTO|UPDATE|FROM)\s+([A-Za-z_]\w*)", re.IGNORECASE)


def _tabelas_do_sql(sql):
    return set(_TABELA_RE.findall(sql)) & set(TABELAS_SINCRONIA)


class _Adaptador:
    """Executa dentro da transação do Supabase e anota quais tabelas foram tocadas."""

    def __init__(self, con, tocadas):
        self.con = con
        self.tocadas = tocadas

    def execute(self, sql, args=()):
        self.tocadas |= _tabelas_do_sql(sql)
        return self.con.execute(sql.replace("?", "%s"), args)


class BancoSqlite:
    """Arquivo SQLite local, um por usuário."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)

    def _abrir(self):
        self.caminho.parent.mkdir(parents=True, exist_ok=True)
        con = sqlite3.connect(self.caminho, timeout=10)
        con.row_factory = sqlite3.Row
        for comando in comandos("sqlite"):
            con.execute(comando)
        con.execute("INSERT OR IGNORE INTO meta (chave, valor) VALUES ('versao', 0)")
        self._preparar(con)
        con.commit()
        return con

    def _preparar(self, con):
        """Dados iniciais e ajustes de bancos criados em versões antigas."""
        colunas = lambda t: [r[1] for r in con.execute(f"PRAGMA table_info({t})")]  # noqa: E731
        if "mes" not in colunas("pagamentos"):
            con.execute("ALTER TABLE pagamentos ADD COLUMN mes TEXT")
            con.execute("UPDATE pagamentos SET mes = substr(data, 1, 7) WHERE mes IS NULL")
        for tabela in ("compras", "despesas"):
            if "recorrente" not in colunas(tabela):
                con.execute(f"ALTER TABLE {tabela} ADD COLUMN recorrente INTEGER NOT NULL DEFAULT 0")
        for tabela in ("compras", "despesas"):
            if "categoria_id" not in colunas(tabela):
                con.execute(f"ALTER TABLE {tabela} ADD COLUMN categoria_id INTEGER")
        for coluna, tipo in (("meta", "REAL"), ("data_alvo", "TEXT")):
            if coluna not in colunas("caixinhas"):
                con.execute(f"ALTER TABLE caixinhas ADD COLUMN {coluna} {tipo}")
        for coluna in ("dia_fechamento", "dia_vencimento"):
            if coluna not in colunas("cartoes"):
                con.execute(f"ALTER TABLE cartoes ADD COLUMN {coluna} INTEGER")
        if con.execute("SELECT COUNT(*) AS n FROM categorias").fetchone()["n"] == 0:
            con.executemany("INSERT INTO categorias (nome, cor, orcamento) VALUES (?,?,0)",
                            CATEGORIAS_INICIAIS)
        if con.execute("SELECT COUNT(*) AS n FROM cartoes").fetchone()["n"] == 0:
            con.executemany("INSERT INTO cartoes (nome, cor, cor_texto) VALUES (?,?,?)",
                            CARTOES_INICIAIS)
        if con.execute("SELECT COUNT(*) AS n FROM sessoes").fetchone()["n"] == 0:
            meses = {mes_do_calendario()}
            for tabela in ("compras", "receitas", "despesas"):
                meses |= {r["mes"] for r in con.execute(f"SELECT DISTINCT mes FROM {tabela}")}
            con.executemany("INSERT OR IGNORE INTO sessoes (mes) VALUES (?)",
                            [(m,) for m in sorted(meses)])

    def consultar(self, sql, args=()):
        con = self._abrir()
        try:
            return [dict(r) for r in con.execute(sql, args).fetchall()]
        finally:
            con.close()

    def gravar(self, sql, args=()):
        with self.transacao() as con:
            cur = con.execute(sql, args)
            return cur.lastrowid, cur.rowcount

    @contextmanager
    def transacao(self):
        con = self._abrir()
        try:
            with con:
                yield con
                con.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
        finally:
            con.close()

    def versao(self):
        return self.consultar("SELECT valor FROM meta WHERE chave = 'versao'")[0]["valor"]

    def estado(self):
        return {"tipo": "local", "online": True, "pendentes": 0, "falhas": 0}


def _sql_para_envio(op):
    """Monta o comando de uma alteração pendente para o Supabase (com o id original)."""
    sql, args = op["sql"], list(op["args"])
    if op["tabela"] == "sessoes" and sql.upper().startswith("INSERT"):
        sql = sql + " ON CONFLICT DO NOTHING"
    elif op.get("id") is not None and op["tabela"] in TABELAS_COM_ID and "ON CONFLICT" not in sql.upper():
        sql = re.sub(r"INSERT INTO (\w+) \(([^)]*)\) VALUES \(",
                     lambda m: f"INSERT INTO {m.group(1)} (id, {m.group(2)}) VALUES (?, ", sql, count=1)
        args = [op["id"]] + args
    return sql.replace("?", "%s"), args


class BancoPostgres:
    """Supabase (PostgreSQL) como fonte de verdade, com cópia em memória e modo offline.

    Online:  leituras vêm da cópia; alterações vão ao Supabase primeiro e depois a cópia é atualizada.
    Offline: alterações são aplicadas na cópia e anotadas numa fila criptografada.
             Quando a conexão volta, a fila é enviada na ordem e a cópia é recarregada.
    """

    def __init__(self, url, esquema, caminho_fila, caminho_cache):
        self.url = url
        self.esquema = esquema
        self.caminho_fila = Path(caminho_fila)
        self.caminho_cache = Path(caminho_cache)
        self._pg = None
        self._local = None
        self._fila = None
        self._cofre = None
        self._online = True
        self._em_transacao = False
        self._ultima_verificacao = 0.0
        self._ultima_tentativa = 0.0
        self.falhas = 0  # alterações que o Supabase recusou ao enviar

    # ----- conexão -----

    def _preparar_esquema(self):
        """Comandos de preparação, enviados de uma vez só (uma ida e volta)."""
        def texto(valor):
            return "'" + str(valor).replace("'", "''") + "'"
        partes = [f'CREATE SCHEMA IF NOT EXISTS "{self.esquema}"',
                  f'SET search_path TO "{self.esquema}"']
        partes += comandos("postgres")
        partes.append("INSERT INTO meta (chave, valor) VALUES ('versao', 0) ON CONFLICT DO NOTHING")
        for nome, cor, cor_texto in CARTOES_INICIAIS:
            partes.append("INSERT INTO cartoes (nome, cor, cor_texto) VALUES "
                          f"({texto(nome)}, {texto(cor)}, {texto(cor_texto)}) ON CONFLICT DO NOTHING")
        partes += ["ALTER TABLE compras ADD COLUMN IF NOT EXISTS categoria_id BIGINT",
                   "ALTER TABLE despesas ADD COLUMN IF NOT EXISTS categoria_id BIGINT",
                   "ALTER TABLE caixinhas ADD COLUMN IF NOT EXISTS meta DOUBLE PRECISION",
                   "ALTER TABLE caixinhas ADD COLUMN IF NOT EXISTS data_alvo TEXT",
                   "ALTER TABLE cartoes ADD COLUMN IF NOT EXISTS dia_fechamento BIGINT",
                   "ALTER TABLE cartoes ADD COLUMN IF NOT EXISTS dia_vencimento BIGINT"]
        for nome, cor in CATEGORIAS_INICIAIS:
            partes.append("INSERT INTO categorias (nome, cor, orcamento) VALUES "
                          f"({texto(nome)}, {texto(cor)}, 0) ON CONFLICT (nome) DO NOTHING")
        partes.append(f"INSERT INTO sessoes (mes) VALUES ({texto(mes_do_calendario())}) "
                      "ON CONFLICT DO NOTHING")
        return ";\n".join(partes) + ";"

    def _pg_conexao(self):
        import psycopg
        from psycopg.rows import dict_row
        if self._pg is None or self._pg.closed:
            con = psycopg.connect(self.url, row_factory=dict_row, autocommit=True, connect_timeout=5)
            con.execute(self._preparar_esquema())
            self._pg = con
        return self._pg

    def _cair_offline(self):
        self._online = False
        self._ultima_tentativa = time.time()
        if self._pg is not None:
            try:
                self._pg.close()
            except Exception:
                pass
        self._pg = None

    def _tentar_reconectar(self):
        """Quando offline, tenta voltar no máximo a cada INTERVALO_TENTATIVA segundos."""
        agora = time.time()
        if agora - self._ultima_tentativa < INTERVALO_TENTATIVA:
            return False
        self._ultima_tentativa = agora
        try:
            self._pg_conexao()
        except ERROS_CONEXAO:
            return False
        self._online = True
        self._enviar_fila()
        self._sincronizar()
        return True

    # ----- cópia em memória -----

    def _copia(self):
        """Cópia em memória. Na abertura, tenta o Supabase; sem conexão, usa a última cópia salva."""
        if self._local is None:
            local = sqlite3.connect(":memory:")
            local.row_factory = sqlite3.Row
            for comando in comandos("sqlite"):
                local.execute(comando)
            local.execute("INSERT OR IGNORE INTO meta (chave, valor) VALUES ('versao', 0)")
            self._local = local
            try:
                self._pg_conexao()
                self._online = True
                if self._fila_lista():
                    self._enviar_fila()
                self._sincronizar()
            except ERROS_CONEXAO:
                self._cair_offline()
                if not self._carregar_cache():
                    raise RuntimeError(
                        "Sem conexão com o Supabase e sem cópia local. "
                        "Conecte-se à internet para abrir o app pela primeira vez.")
        return self._local

    # ----- cópia de segurança para abrir sem internet (criptografada) -----

    def _salvar_cache(self):
        local = self._local
        dados = {t: [dict(r) for r in local.execute(f"SELECT * FROM {t}").fetchall()]
                 for t in TABELAS_SINCRONIA}
        self._cofre = self._cofre or Cofre()
        self.caminho_cache.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_cache.write_bytes(self._cofre.cifrar(dados))

    def _carregar_cache(self):
        if not self.caminho_cache.exists():
            return False
        self._cofre = self._cofre or Cofre()
        dados = self._cofre.decifrar(self.caminho_cache.read_bytes())
        local = self._local
        for tabela in TABELAS_SINCRONIA:
            local.execute(f"DELETE FROM {tabela}")
            linhas = dados.get(tabela, [])
            if linhas:
                colunas = list(linhas[0].keys())
                marcas = ",".join("?" * len(colunas))
                local.executemany(f"INSERT INTO {tabela} ({','.join(colunas)}) VALUES ({marcas})",
                                  [tuple(l[c] for c in colunas) for l in linhas])
        local.commit()
        return True

    def _sincronizar(self, tabelas=TABELAS_SINCRONIA):
        """Copia as tabelas do Supabase para a memória. Só funciona online."""
        pg = self._pg_conexao()
        local = self._copia()
        for tabela in tabelas:
            linhas = pg.execute(f"SELECT * FROM {tabela}").fetchall()
            colunas = [r[1] for r in local.execute(f"PRAGMA table_info({tabela})")]
            local.execute(f"DELETE FROM {tabela}")
            if linhas:
                marcas = ",".join("?" * len(colunas))
                local.executemany(f"INSERT INTO {tabela} ({','.join(colunas)}) VALUES ({marcas})",
                                  [tuple(l[c] for c in colunas) for l in linhas])
        local.commit()
        self._salvar_cache()

    # ----- fila de pendências (criptografada) -----

    def _fila_lista(self):
        if self._fila is None:
            self._cofre = self._cofre or Cofre()
            self._fila = (self._cofre.decifrar(self.caminho_fila.read_bytes())
                          if self.caminho_fila.exists() else [])
        return self._fila

    def _fila_salvar(self):
        self._cofre = self._cofre or Cofre()
        self.caminho_fila.parent.mkdir(parents=True, exist_ok=True)
        self.caminho_fila.write_bytes(self._cofre.cifrar(self._fila_lista()))

    def _enviar_fila(self):
        """Envia as alterações pendentes ao Supabase, na ordem em que foram feitas."""
        fila = self._fila_lista()
        pg = self._pg_conexao()
        while fila:
            op = fila[0]
            sql, args = _sql_para_envio(op)
            try:
                with pg.transaction():
                    pg.execute(sql, args)
                    pg.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
            except ERROS_CONEXAO:
                self._fila_salvar()
                raise
            except Exception:  # o Supabase recusou esta alteração: descarta e conta
                self.falhas += 1
            fila.pop(0)
            self._fila_salvar()

    def _anotar(self, tabela, sql, args, novo_id):
        self._fila_lista().append({"tabela": tabela, "sql": sql, "args": list(args), "id": novo_id})
        self._fila_salvar()

    # ----- verificações -----

    def _verificar(self):
        """Online: confere se o Supabase mudou por fora. Offline: tenta reconectar."""
        if not self._online:
            self._tentar_reconectar()
            return
        agora = time.time()
        if agora - self._ultima_verificacao < INTERVALO_VERIFICACAO:
            return
        self._ultima_verificacao = agora
        try:
            remota = self._pg_conexao().execute(
                "SELECT valor FROM meta WHERE chave = 'versao'").fetchone()["valor"]
        except ERROS_CONEXAO:
            self._cair_offline()
            return
        local = self._copia().execute("SELECT valor FROM meta WHERE chave = 'versao'").fetchone()["valor"]
        if remota != local:
            self._sincronizar()

    # ----- interface usada pelo resto do projeto -----

    def consultar(self, sql, args=()):
        if self._em_transacao:  # leitura dentro de transação: direto no Supabase, se online
            return [dict(r) for r in self._pg_conexao().execute(sql.replace("?", "%s"), args).fetchall()]
        self._verificar()
        return [dict(r) for r in self._copia().execute(sql, args).fetchall()]

    def gravar(self, sql, args=()):
        tabela = sql.split()[2] if sql.upper().startswith("INSERT INTO ") else ""
        if self._online or self._tentar_reconectar():
            try:
                return self._gravar_online(sql, args, tabela)
            except ERROS_CONEXAO:
                self._cair_offline()
        return self._gravar_offline(sql, args, tabela)

    def _gravar_online(self, sql, args, tabela):
        pg = self._pg_conexao()
        sql_pg = sql.replace("?", "%s")
        if tabela in TABELAS_COM_ID and "ON CONFLICT" not in sql.upper():
            sql_pg += " RETURNING id"
        with pg.transaction():
            cur = pg.execute(sql_pg, args)
            novo_id = None
            if " RETURNING id" in sql_pg:
                linha = cur.fetchone()
                novo_id = linha["id"] if linha else None
            pg.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
            rowcount = cur.rowcount
        self._sincronizar(_tabelas_do_sql(sql) | {"meta"})
        return novo_id, rowcount

    def _gravar_offline(self, sql, args, tabela):
        local = self._copia()
        cur = local.execute(sql, args)
        novo_id = cur.lastrowid if (tabela in TABELAS_COM_ID and sql.upper().startswith("INSERT")
                                    and "ON CONFLICT" not in sql.upper()) else None
        local.commit()
        self._anotar(tabela, sql, args, novo_id)
        self._salvar_cache()
        return novo_id, cur.rowcount

    @contextmanager
    def transacao(self):
        if not (self._online or self._tentar_reconectar()):
            yield from self._transacao_offline()
            return
        pg = self._pg_conexao()
        tocadas = set()
        self._em_transacao = True
        try:
            with pg.transaction():  # confirma no fim; desfaz se der erro
                yield _Adaptador(pg, tocadas)
                pg.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
        finally:
            self._em_transacao = False
        self._sincronizar((tocadas | {"meta"}) or TABELAS_SINCRONIA)

    def _transacao_offline(self):
        """Offline: a transação roda na cópia e cada alteração vai para a fila."""
        local = self._copia()
        registros = []

        class _Local:
            def execute(self_, sql, args=()):
                cur = local.execute(sql, args)
                if sql.upper().lstrip().startswith(("INSERT", "UPDATE", "DELETE")):
                    tabela = (sql.split()[2] if sql.upper().startswith("INSERT INTO ")
                              else next(iter(_tabelas_do_sql(sql)), ""))
                    novo_id = cur.lastrowid if (tabela in TABELAS_COM_ID and
                                                sql.upper().startswith("INSERT")) else None
                    registros.append((tabela, sql, args, novo_id))
                return cur
        self._em_transacao = True
        try:
            yield _Local()
            registros.append(("meta", "UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'", (), None))
            local.execute("UPDATE meta SET valor = valor + 1 WHERE chave = 'versao'")
            local.commit()
            fila = self._fila_lista()
            fila.extend({"tabela": t, "sql": s_, "args": list(a), "id": i} for t, s_, a, i in registros)
            self._fila_salvar()
            self._salvar_cache()
        except Exception:
            local.rollback()
            raise
        finally:
            self._em_transacao = False

    def versao(self):
        self._verificar()
        return self._copia().execute("SELECT valor FROM meta WHERE chave = 'versao'").fetchone()["valor"]

    def estado(self):
        """Usado pela tela para mostrar o aviso de sincronização."""
        self._copia()  # garante que a conexão já foi tentada antes de informar o estado
        self._verificar()
        pendentes = len(self._fila_lista())
        return {"tipo": "supabase", "online": self._online, "pendentes": pendentes,
                "falhas": self.falhas}


def url_do_supabase() -> str:
    """Conexão do Supabase: variável DATABASE_URL, ou o arquivo criptografado."""
    if DATABASE_URL:
        return DATABASE_URL
    if not CONEXAO_PATH.exists():
        raise RuntimeError("Supabase não configurado. Rode supabase/configurar_conexao.py.")
    from .seguranca import Cofre
    return Cofre().decifrar(CONEXAO_PATH.read_bytes())["url"]


def criar_banco(usuario: str):
    """Banco do usuário, conforme a configuração (SQLite local ou Supabase)."""
    if TIPO_BANCO == "postgres":
        return BancoPostgres(url_do_supabase(), esquema=f"financeiro_{slug(usuario)}",
                             caminho_fila=PASTA / f"pendentes_{slug(usuario)}.dat",
                             caminho_cache=PASTA / f"cache_{slug(usuario)}.dat")
    caminho = BANCO_FORCADO or PASTA / f"financas_{slug(usuario)}.db"
    return BancoSqlite(caminho)
