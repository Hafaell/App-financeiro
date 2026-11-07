"""Leitura de extratos (CSV e OFX). Só lê e organiza; quem grava é a fachada, após confirmação."""
import csv
import io
import re
from datetime import datetime

from .utilidades import dinheiro

PALAVRAS_CREDITO = ("pagamento", "estorno", "credito", "crédito", "cashback", "reembolso")


def _achar(cabecalho, opcoes):
    for i, nome in enumerate(cabecalho):
        if any(o in nome for o in opcoes):
            return i
    return None


def _data(texto):
    t = str(texto or "").strip()[:10]
    for formato in ("%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(t, formato).date().isoformat()
        except ValueError:
            continue
    return None


PARCELA_RE = re.compile(r"\s*-?\s*parcela\s+(\d+)\s*/\s*(\d+)\s*$", re.IGNORECASE)


def _separar_parcela(descricao):
    """'Youcom Fl129 - Parcela 1/3' -> ('Youcom Fl129', '1/3'). Sem parcela: '1/1'."""
    m = PARCELA_RE.search(descricao)
    if not m:
        return descricao.strip(), "1/1"
    return descricao[:m.start()].strip(), f"{m.group(1)}/{m.group(2)}"


def _item(data, descricao, valor, credito_por_sinal=False):
    """Padroniza um lançamento. Crédito = pagamento/estorno (sinal negativo no CSV do Nubank,
    ou valor positivo com palavra de crédito)."""
    texto, parcelas = _separar_parcela(descricao or "")
    credito = credito_por_sinal or (valor > 0 and any(p in texto.lower() for p in PALAVRAS_CREDITO))
    return {"data": data, "descricao": texto or "(sem descrição)", "parcelas": parcelas,
            "valor": round(abs(valor), 2), "credito": credito}


def banco_do_arquivo(nome_arquivo):
    """Nome do cartão sugerido pelo arquivo ('Nubank_2026-11-15.csv' -> 'Nubank')."""
    base = nome_arquivo.replace("\\", "/").split("/")[-1].lower()
    for banco in ("nubank", "inter"):
        if banco in base:
            return banco.capitalize()
    return None


def ler_csv(texto):
    amostra = texto[:4096]
    delimitador = max([",", ";", "\t"], key=amostra.count)
    linhas = [l for l in csv.reader(io.StringIO(texto), delimiter=delimitador) if any(c.strip() for c in l)]
    if not linhas:
        raise ValueError("O arquivo está vazio.")
    cabecalho = [c.strip().lower() for c in linhas[0]]
    if _data(linhas[0][0]):  # sem cabeçalho: data, descrição e valor nas primeiras colunas
        cabecalho, corpo = None, linhas
        i_data, i_desc, i_val = 0, 1, len(linhas[0]) - 1
    else:
        corpo = linhas[1:]
        i_data = _achar(cabecalho, ["data", "date"])
        i_desc = _achar(cabecalho, ["descri", "histórico", "historico", "estabelec", "lançamento", "lancamento", "nome", "title"])
        i_val = _achar(cabecalho, ["valor", "value", "amount", "montante"])
        if None in (i_data, i_desc, i_val):
            raise ValueError("Não encontrei as colunas de data, descrição e valor no CSV.")
    itens = []
    for linha in corpo:
        if len(linha) <= max(i_data, i_desc, i_val):
            continue
        data = _data(linha[i_data])
        if not data:
            continue
        try:
            valor = dinheiro(linha[i_val])
        except ValueError:
            continue
        # No CSV do Nubank, pagamentos vêm com sinal negativo; compras, positivo
        itens.append(_item(data, linha[i_desc], valor, credito_por_sinal=valor < 0))
    return itens


def ler_ofx(texto):
    itens = []
    for bloco in re.findall(r"<STMTTRN>(.*?)(?:</STMTTRN>|(?=<STMTTRN>)|$)", texto, re.S | re.I):
        def campo(nome):
            m = re.search(rf"<{nome}>([^<\r\n]*)", bloco, re.I)
            return m.group(1).strip() if m else ""
        data = _data(f"{campo('DTPOSTED')[:4]}-{campo('DTPOSTED')[4:6]}-{campo('DTPOSTED')[6:8]}")
        try:
            valor = float(campo("TRNAMT").replace(",", "."))
        except ValueError:
            continue
        if not data:
            continue
        descricao = campo("MEMO") or campo("NAME")
        # No OFX, compras de cartão vêm negativas: o sinal indica gasto, não crédito
        item = _item(data, descricao, valor, credito_por_sinal=valor > 0)
        itens.append(item)
    return itens


def ler_extrato(nome_arquivo, conteudo: bytes):
    texto = conteudo.decode("utf-8-sig", errors="replace")
    if nome_arquivo.lower().endswith(".ofx") or "<STMTTRN>" in texto.upper():
        return ler_ofx(texto)
    return ler_csv(texto)


def marcar_situacao(itens, existentes_compras, existentes_despesas, mes):
    """Diz o que fazer com cada linha: novo, já lançado (mesma descrição e valor no mês) ou crédito."""
    chaves_c = {(e["item"].strip().lower(), round(e["valor_parcela"], 2)) for e in existentes_compras}
    chaves_d = {(e["descricao"].strip().lower(), round(e["valor"], 2)) for e in existentes_despesas}
    for it in itens:
        chave = (it["descricao"].strip().lower(), it["valor"])
        it["mes_fora"] = it["data"][:7] != mes
        if it["credito"]:
            it["situacao"] = "Pagamento / crédito (não importar)"
        elif chave in chaves_c or chave in chaves_d:
            it["situacao"] = "Já lançado"
        else:
            it["situacao"] = "Novo"
    return itens
