"""Banco da versão web (Vercel): o BancoPostgres sem nada em disco e sem modo offline.

Cada requisição da API cria um BancoWeb com o token (JWT) do usuário. Na primeira leitura, a
cópia em memória é baixada do Supabase numa chamada só (lote de SELECTs) e as regras de
nucleo/ rodam sobre ela, exatamente como no desktop. Gravações vão direto ao Supabase.

Diferenças para o BancoPostgres:
- sem cópia criptografada e sem fila em arquivo (o disco do Vercel é temporário);
- sem modo offline: se o Supabase não responder, a requisição falha e o site mostra o erro;
- sem conferir a versão a cada leitura (a cópia acabou de ser baixada).
"""
import sqlite3
import sys
import threading

from controle_financeiro.dados.banco import BancoPostgres
from controle_financeiro.dados.esquema import comandos
from controle_financeiro.nucleo.utilidades import mes_do_calendario

# Usuários já preparados neste processo (a função do Vercel fica "quente" entre requisições).
# Chave: (id do usuário, mês do calendário). Evita duas chamadas ao Supabase por requisição.
_preparados = set()
_trava = threading.Lock()


class BancoWeb(BancoPostgres):
    def __init__(self, cliente, usuario_id=None):
        super().__init__(cliente, caminho_fila="", caminho_cache="")
        self.usuario_id = usuario_id
        self.verificar_nas_consultas = False
        self._fila = []

    def _copia(self):
        if self._local is None:
            # A API pode montar o objeto numa thread e usá-lo em outra (FastAPI)
            local = sqlite3.connect(":memory:", check_same_thread=False)
            local.row_factory = sqlite3.Row
            for comando in comandos("sqlite"):
                local.execute(comando)
            local.execute("INSERT OR IGNORE INTO meta (chave, valor) VALUES ('versao', 0)")
            self._local = local
            try:
                self._preparar_nuvem()
                self._sincronizar()
            except Exception:
                self._local = None
                raise
        return self._local

    def _preparar_nuvem(self):
        chave = (self.usuario_id, mes_do_calendario())
        if self.usuario_id and chave in _preparados:
            return
        super()._preparar_nuvem()
        if self.usuario_id:
            with _trava:
                _preparados.add(chave)

    def _cair_offline(self):
        """Sem modo offline: o erro de conexão (ou de sessão) segue para a API responder."""
        erro = sys.exc_info()[1]
        if erro is not None:
            raise erro
        raise RuntimeError("Sem conexão com o Supabase.")

    def _tentar_reconectar(self):
        return False

    # Nada vai para o disco
    def _salvar_cache(self):
        pass

    def _carregar_cache(self):
        return False

    def _fila_lista(self):
        return self._fila

    def _fila_salvar(self):
        pass

    def versao_remota(self):
        """Versão dos dados no Supabase, sem baixar a cópia (o site usa para saber se atualiza)."""
        linhas = self.cliente.executar("SELECT valor FROM meta WHERE chave = %s", ["versao"])["linhas"]
        return linhas[0]["valor"] if linhas else 0
