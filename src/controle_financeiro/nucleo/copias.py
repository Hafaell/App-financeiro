"""Onde ficam as cópias automáticas (antes da virada e antes de restaurar).

- CopiasEmPasta: desktop. Arquivos .cfauto criptografados em %LOCALAPPDATA% (ref = caminho).
- CopiasNoBanco: versão web. Tabela `backups` no Supabase, isolada por usuário (ref = id).
  Depende do script supabase/migracoes/08_backups_web.sql.

As duas têm a mesma interface: salvar(prefixo, detalhe) -> ref, listar() e ler(ref).
"""
import json
from datetime import datetime

from controle_financeiro.dados.esquema import SCRIPT_BACKUPS, TABELA_BACKUPS
from controle_financeiro.nucleo.ferramentas import MOTIVOS, ler_backup_automatico
from controle_financeiro.nucleo.utilidades import nome_mes

MANTER = 6  # cópias guardadas por motivo


def descrever_motivo(prefixo, detalhe=""):
    motivo = MOTIVOS.get(prefixo, prefixo)
    if prefixo == "antes-da-virada" and detalhe:
        try:
            return f"{motivo} {nome_mes(detalhe)}"
        except (ValueError, IndexError):
            return f"{motivo} {detalhe}"
    return motivo


class CopiasEmPasta:
    def __init__(self, ferramentas, pasta):
        self.ferramentas = ferramentas
        self.pasta = pasta

    def salvar(self, prefixo, detalhe=""):
        return str(self.ferramentas.backup_automatico(self.pasta, prefixo, detalhe, MANTER))

    def listar(self):
        return self.ferramentas.listar_backups(self.pasta)

    def ler(self, ref):
        return ler_backup_automatico(ref)


class CopiasNoBanco:
    def __init__(self, banco, ferramentas):
        self.banco = banco
        self.ferramentas = ferramentas

    def _sem_tabela(self, erro):
        texto = str(erro).lower()
        if TABELA_BACKUPS in texto and ("does not exist" in texto or "no such table" in texto):
            return ValueError("As cópias de segurança da versão web ainda não estão ligadas: rode o "
                              f"script {SCRIPT_BACKUPS} no SQL Editor do Supabase.")
        return erro

    def salvar(self, prefixo, detalhe=""):
        dados = json.dumps(self.ferramentas.todos_os_dados(), ensure_ascii=False)
        try:
            id_, _ = self.banco.gravar_direto(
                f"INSERT INTO {TABELA_BACKUPS} (criado_em, motivo, detalhe, dados) VALUES (?,?,?,?)",
                (datetime.now().isoformat(timespec="seconds"), prefixo, detalhe or "", dados))
            # Guarda só as MANTER mais novas deste motivo
            self.banco.gravar_direto(
                f"DELETE FROM {TABELA_BACKUPS} WHERE motivo = ? AND id NOT IN "
                f"(SELECT id FROM {TABELA_BACKUPS} WHERE motivo = ? ORDER BY id DESC LIMIT {MANTER})",
                (prefixo, prefixo))
        except Exception as erro:
            raise self._sem_tabela(erro) from erro
        return id_

    def listar(self):
        try:
            linhas = self.banco.consultar_direto(
                f"SELECT id, criado_em, motivo, detalhe FROM {TABELA_BACKUPS} ORDER BY id DESC")
        except Exception as erro:
            if isinstance(self._sem_tabela(erro), ValueError):
                return []  # script ainda não rodado: só não há cópias para mostrar
            raise
        return [{"id": l["id"], "quando": l["criado_em"],
                 "motivo": descrever_motivo(l["motivo"], l["detalhe"])} for l in linhas]

    def ler(self, ref):
        try:
            linhas = self.banco.consultar_direto(
                f"SELECT dados FROM {TABELA_BACKUPS} WHERE id = ?", (int(ref),))
        except Exception as erro:
            raise self._sem_tabela(erro) from erro
        if not linhas:
            raise ValueError("Cópia não encontrada.")
        dados = linhas[0]["dados"]
        return json.loads(dados) if isinstance(dados, str) else dados
