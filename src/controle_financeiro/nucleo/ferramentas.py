"""Ferramentas: busca em todos os meses, comparativo entre meses e backup criptografado."""
import base64
import hashlib
import json
import os
from datetime import date, datetime
from pathlib import Path

from cryptography.fernet import Fernet

from controle_financeiro.nucleo.utilidades import nome_mes

MAGICO = b"CFBK1"  # identifica o arquivo de backup do Controle Financeiro
MAGICO_AUTO = b"CFAUTO1"  # cópia automática (criptografada com a chave deste computador)
TABELAS_BACKUP = ("cartoes", "categorias", "rendas", "sessoes", "compras", "receitas",
                  "despesas", "caixinhas", "pagamentos")


class Ferramentas:
    def __init__(self, banco, meses, resumo):
        self.banco = banco
        self.meses = meses
        self.resumo = resumo

    def buscar(self, texto, limite=200) -> list:
        """Procura um texto em itens, pessoas e descrições, em todos os meses."""
        t = f"%{str(texto or '').strip().lower()}%"
        if t == "%%":
            return []
        linhas = self.banco.consultar(
            "SELECT mes, cartao AS origem, item AS texto, valor_parcela AS valor, pessoa AS extra "
            "FROM compras WHERE lower(item) LIKE ? OR lower(pessoa) LIKE ? "
            "UNION ALL SELECT mes, 'Despesa' AS origem, descricao AS texto, valor, '' AS extra "
            "FROM despesas WHERE lower(descricao) LIKE ? "
            "UNION ALL SELECT mes, 'Receita' AS origem, descricao AS texto, valor, '' AS extra "
            "FROM receitas WHERE lower(descricao) LIKE ? "
            "ORDER BY mes DESC LIMIT ?", (t, t, t, t, limite))
        for l in linhas:
            l["mes_nome"] = nome_mes(l["mes"])
        return linhas

    def comparar_meses(self, quantos=6) -> list:
        """Resumo dos últimos meses abertos (até o mês atual), para comparar."""
        abertos = self.meses.sessoes()[-quantos:]
        saida = []
        for m in abertos:
            r = self.resumo.do_mes(m)
            saida.append({"mes": m, "nome": r["mes"], "receitas": r["receitas"],
                          "despesas": round(r["despesas_manuais"] + r["meu_cartao_total"], 2),
                          "saldo": r["saldo"], "meu_cartao": r["meu_cartao_total"],
                          "a_receber": r["a_receber_de_pessoas"]})
        return saida

    # ----- backup -----

    def _chave(self, senha: str, salt: bytes) -> bytes:
        bruta = hashlib.pbkdf2_hmac("sha256", senha.encode("utf-8"), salt, 200_000)
        return base64.urlsafe_b64encode(bruta)

    def exportar_backup(self, caminho, senha: str) -> str:
        """Salva todos os dados do usuário num arquivo criptografado com a senha informada."""
        if len(str(senha or "")) < 6:
            raise ValueError("Use uma senha de pelo menos 6 caracteres para o backup.")
        dados = {t: self.banco.consultar(f"SELECT * FROM {t}") for t in TABELAS_BACKUP}
        dados["_gerado_em"] = date.today().isoformat()
        salt = os.urandom(16)
        token = Fernet(self._chave(senha, salt)).encrypt(json.dumps(dados, default=str).encode("utf-8"))
        with open(caminho, "wb") as f:
            f.write(MAGICO + salt + token)
        return str(caminho)

    # ----- cópia automática (antes de ações que não têm volta, como a virada) -----

    def _todos_os_dados(self) -> dict:
        dados = {t: self.banco.consultar(f"SELECT * FROM {t}") for t in TABELAS_BACKUP}
        dados["_gerado_em"] = datetime.now().isoformat(timespec="seconds")
        return json.loads(json.dumps(dados, default=str))  # datas e decimais viram texto

    def backup_automatico(self, pasta, prefixo: str, detalhe: str = "", manter: int = 6) -> Path:
        """Salva todos os dados em `pasta`, criptografados com a chave deste computador
        (a mesma dos outros arquivos locais), sem pedir senha. Guarda só as `manter`
        cópias mais novas com o mesmo prefixo. Devolve o caminho do arquivo."""
        from controle_financeiro.seguranca.cofre import Cofre

        pasta = Path(pasta)
        pasta.mkdir(parents=True, exist_ok=True)
        nome = f"{prefixo}_{detalhe + '_' if detalhe else ''}{datetime.now():%Y-%m-%d_%H%M%S}.cfauto"
        destino = pasta / nome
        extra = 2
        while destino.exists():  # duas cópias no mesmo segundo
            destino = pasta / nome.replace(".cfauto", f"-{extra}.cfauto")
            extra += 1
        temporario = destino.with_suffix(".tmp")
        temporario.write_bytes(MAGICO_AUTO + Cofre().cifrar(self._todos_os_dados()))
        temporario.replace(destino)  # o arquivo só aparece completo
        antigos = sorted(pasta.glob(f"{prefixo}_*.cfauto"), key=lambda a: a.stat().st_mtime)
        for velho in antigos[:-manter] if manter > 0 else []:
            velho.unlink(missing_ok=True)
        return destino

    def listar_backups(self, pasta) -> list:
        """Cópias automáticas da pasta, da mais nova para a mais antiga."""
        pasta = Path(pasta)
        saida = []
        for arquivo in pasta.glob("*.cfauto") if pasta.is_dir() else []:
            partes = arquivo.stem.split("_")
            prefixo, detalhe = partes[0], (partes[1] if len(partes) == 4 else "")
            motivo = MOTIVOS.get(prefixo, prefixo)
            if prefixo == "antes-da-virada" and detalhe:
                try:
                    motivo = f"{motivo} {nome_mes(detalhe)}"
                except (ValueError, IndexError):
                    motivo = f"{motivo} {detalhe}"
            try:
                quando = datetime.strptime("_".join(partes[-2:])[:17], "%Y-%m-%d_%H%M%S")
            except ValueError:
                quando = datetime.fromtimestamp(arquivo.stat().st_mtime)
            saida.append({"caminho": str(arquivo), "quando": quando, "motivo": motivo})
        return sorted(saida, key=lambda b: (b["quando"], b["caminho"]), reverse=True)

    def _colunas(self, tabela) -> list:
        """Colunas que a tabela tem hoje. Os dois bancos leem de um SQLite (o Supabase,
        da cópia em memória), então o PRAGMA serve para ambos."""
        return [c["name"] for c in self.banco.consultar(f"PRAGMA table_info({tabela})")]

    def restaurar(self, dados: dict):
        """Troca todos os dados do usuário pelos de uma cópia, numa transação só (tudo ou nada).
        Mantém os ids da cópia, porque compras e despesas apontam para as categorias pelo id."""
        faltando = [t for t in TABELAS_BACKUP if not isinstance(dados.get(t), list)]
        if faltando:
            raise ValueError("A cópia está incompleta: faltam " + ", ".join(faltando) + ".")
        if not dados["sessoes"]:
            raise ValueError("A cópia não tem nenhum mês aberto.")
        atuais_por_tabela = {t: self._colunas(t) for t in ORDEM_APAGAR}  # antes de abrir a transação
        with self.banco.transacao() as con:
            for tabela in ORDEM_APAGAR:
                con.execute(f"DELETE FROM {tabela}")
            for tabela in reversed(ORDEM_APAGAR):
                linhas = dados[tabela]
                if not linhas:
                    continue
                atuais = atuais_por_tabela[tabela]
                # id primeiro, para a fila offline reconhecer que o comando já traz o id
                colunas = sorted((c for c in linhas[0] if c in atuais), key=lambda c: c != "id")
                marcas = "(" + ",".join("?" * len(colunas)) + ")"
                for i in range(0, len(linhas), LOTE):
                    parte = linhas[i:i + LOTE]
                    con.execute(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES "
                                + ",".join([marcas] * len(parte)),
                                [l.get(c) for l in parte for c in colunas])

    def recolocar(self, tabela, linha: dict):
        """Desfazer: grava de novo uma linha apagada (compra, receita ou despesa), com o mesmo id."""
        if tabela not in TABELAS_DESFAZER:
            raise ValueError("Só dá para desfazer compras, receitas e despesas.")
        if linha.get("mes") not in self.meses.sessoes():
            raise ValueError("O mês desse lançamento não está mais aberto.")
        atuais = self._colunas(tabela)
        colunas = sorted((c for c in linha if c in atuais), key=lambda c: c != "id")
        self.banco.gravar(f"INSERT INTO {tabela} ({', '.join(colunas)}) VALUES "
                          f"({','.join('?' * len(colunas))})", [linha[c] for c in colunas])


# Ordem para apagar (quem aponta para outra tabela sai antes) e para regravar (ao contrário)
ORDEM_APAGAR = ("compras", "despesas", "receitas", "pagamentos", "caixinhas", "rendas", "sessoes",
                "categorias", "cartoes")
MOTIVOS = {"antes-da-virada": "Antes da virada de", "antes-de-restaurar": "Antes de restaurar uma cópia"}
TABELAS_DESFAZER = ("compras", "receitas", "despesas")
LOTE = 200  # linhas por comando INSERT ao regravar


def ler_backup_automatico(caminho) -> dict:
    """Abre uma cópia automática (.cfauto) neste computador e devolve os dados por tabela."""
    from controle_financeiro.seguranca.cofre import Cofre

    conteudo = Path(caminho).read_bytes()
    if not conteudo.startswith(MAGICO_AUTO):
        raise ValueError("Este arquivo não é uma cópia automática do Controle Financeiro.")
    return Cofre().decifrar(conteudo[len(MAGICO_AUTO):])
