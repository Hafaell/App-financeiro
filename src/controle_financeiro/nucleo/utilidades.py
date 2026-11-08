"""Funções puras: valores em reais, nomes de meses e textos."""
import re
import unicodedata
from datetime import date

MESES = ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho",
         "agosto", "setembro", "outubro", "novembro", "dezembro")
MESES_EXIBIR = ("Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho",
                "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro")


def dinheiro(valor) -> float:
    """Aceita 63.19, '63,19' e 'R$ 1.234,56'. Devolve float com 2 casas."""
    if isinstance(valor, (int, float)):
        return round(float(valor), 2)
    texto = str(valor or "").replace("R$", "").replace(" ", "").strip()
    if not texto:
        raise ValueError("Informe um valor.")
    if "," in texto:
        texto = texto.replace(".", "").replace(",", ".")
    return round(float(texto), 2)


def sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto)
                   if unicodedata.category(c) != "Mn")


def mes_do_calendario() -> str:
    hoje = date.today()
    return f"{hoje.year}-{hoje.month:02d}"


def proximo_mes(codigo: str) -> str:
    ano, mes = map(int, codigo.split("-"))
    return f"{ano + 1}-01" if mes == 12 else f"{ano}-{mes + 1:02d}"


def nome_mes(codigo: str) -> str:
    """'2026-11' -> 'Novembro 26', o mesmo nome das abas da planilha."""
    ano, mes = codigo.split("-")
    return f"{MESES_EXIBIR[int(mes) - 1]} {ano[2:]}"


def interpretar_mes(texto) -> str:
    """Aceita '2026-11', '11/2026' ou 'novembro 26'."""
    t = sem_acento(str(texto).strip().lower())
    m = re.fullmatch(r"(\d{4})-(\d{1,2})", t)
    if m:
        return f"{m[1]}-{int(m[2]):02d}"
    nums = re.findall(r"\d+", t)
    nomes = [i + 1 for i, nome in enumerate(MESES) if nome in t]
    if nomes:
        mes, ano = nomes[0], (int(nums[-1]) if nums else date.today().year)
    elif len(nums) == 2:
        mes, ano = int(nums[0]), int(nums[1])
    else:
        raise ValueError(f"Não entendi o mês '{texto}'. Use 2026-11, 11/2026 ou novembro 26.")
    if ano < 100:
        ano += 2000
    if not 1 <= mes <= 12:
        raise ValueError(f"Mês inválido: '{texto}'.")
    return f"{ano}-{mes:02d}"


def avancar_parcela(parcelas: str):
    """'2/5' -> '3/5'. Devolve None quando a parcela chegou ao fim (x >= y)."""
    x, y = (int(n) for n in parcelas.split("/"))
    return None if x >= y else f"{x + 1}/{y}"


def slug(nome: str) -> str:
    base = sem_acento(nome).lower()
    return re.sub(r"[^a-z0-9]+", "_", base).strip("_") or "usuario"


def interpretar_mes_simples(texto: str) -> str:
    """'2027-06', '06/2027' ou 'junho 27' -> '2027-06' (usado pela data alvo das caixinhas)."""
    return interpretar_mes(texto)


def meses_entre(inicio: str, fim: str) -> int:
    """Quantos meses faltam de 'inicio' até 'fim' (inclusive o de fim). Negativo se já passou."""
    ai, mi = map(int, inicio.split("-"))
    af, mf = map(int, fim.split("-"))
    return (af - ai) * 12 + (mf - mi) + 1
