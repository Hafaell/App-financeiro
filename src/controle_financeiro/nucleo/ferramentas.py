"""Ferramentas: busca em todos os meses, comparativo entre meses e backup criptografado."""
import base64
import hashlib
import json
import os
from datetime import date

from cryptography.fernet import Fernet

from controle_financeiro.nucleo.utilidades import nome_mes

MAGICO = b"CFBK1"  # identifica o arquivo de backup do Controle Financeiro
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
