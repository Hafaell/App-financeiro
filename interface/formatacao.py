"""Formatação de valores, parcelas e ordem da tabela de transações."""
from financas.contexto import fin


def brl(v) -> str:
    """1234.5 -> 'R$ 1.234,50'"""
    s = f"{float(v or 0):,.2f}".replace(",", "§").replace(".", ",").replace("§", ".")
    return f"R$ {s}"


def nomes_cartoes():
    return [c["nome"] for c in fin().listar_cartoes()]


TODOS = "Todos os cartões"


NOVO_CARTAO = "+ Novo cartão"


def _parcela_exibida(c):
    """Compra à vista (1/1) aparece com a coluna vazia."""
    return "" if c["parcelas"] == "1/1" else c["parcelas"]


def _pessoa_exibida(c):
    """'.' significa que é você, então a coluna fica vazia."""
    return "" if c["pessoa"] == "." else c["pessoa"]


def _ordem_cartoes(c):
    """Parcelados que mais demoram a acabar primeiro, depois os que faltam menos,
    e por último as compras à vista."""
    x, y = (int(n) for n in c["parcelas"].split("/"))
    if y <= 1:
        return (2, 0, c["id"])
    restantes = y - x
    return (0 if restantes > 0 else 1, -restantes, c["id"])


SEM_CATEGORIA = "Sem categoria"


def categorias_opcoes():
    """Nomes das categorias, com 'Sem categoria' primeiro (para os formulários)."""
    return [SEM_CATEGORIA] + [c["nome"] for c in fin().listar_categorias()]


def id_categoria(nome):
    """Nome escolhido no formulário -> id da categoria (None = sem categoria)."""
    if not nome or nome == SEM_CATEGORIA:
        return None
    for c in fin().listar_categorias():
        if c["nome"] == nome:
            return c["id"]
    return None


def nome_categoria(categoria_id, mapa=None):
    """id -> nome da categoria, ou 'Sem categoria'."""
    if categoria_id is None:
        return SEM_CATEGORIA
    mapa = mapa if mapa is not None else {c["id"]: c["nome"] for c in fin().listar_categorias()}
    return mapa.get(categoria_id, SEM_CATEGORIA)

