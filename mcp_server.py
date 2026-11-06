"""Servidor MCP do Controle Financeiro.

O Claude Desktop inicia este arquivo sozinho (transporte stdio).
Cada ferramenta lê ou grava no mesmo banco que o app desktop usa,
então a tela do app atualiza em até 2 segundos depois de qualquer mudança.

Mês vazio em qualquer ferramenta = o mês em que você está (o mais recente aberto).
"""
from mcp.server.fastmcp import FastMCP

from financas import fin

mcp = FastMCP("controle-financeiro")


# ----- meses -----

@mcp.tool()
def listar_meses() -> dict:
    """Lista os meses abertos no app e qual é o mês em que você está (o mais recente)."""
    return {
        "meses": [{"mes": m, "nome": fin().nome_mes(m)} for m in fin().sessoes()],
        "mes_atual": fin().mes_ativo(),
        "nome_mes_atual": fin().nome_mes(fin().mes_ativo()),
    }


@mcp.tool()
def virar_mes() -> dict:
    """Virada de mês: abre o mês seguinte ao mês atual, copiando o mês atual.
    Itens recorrentes permanecem no mês novo; os demais avançam uma parcela, e os que
    chegam ao fim ou são à vista saem. Receitas são copiadas.
    Use somente quando o usuário pedir a virada de mês."""
    return fin().virar_mes()


# ----- resumo -----

@mcp.tool()
def resumo_mes(mes: str = "") -> dict:
    """Resumo do mês: total no meu cartão e com empréstimos (Inter e Nubank), receitas,
    despesas lançadas à parte, saldo e quanto as pessoas devem naquele mês.
    O mês aceita '2026-11', '11/2026' ou 'novembro 26'. Vazio = mês atual."""
    return fin().resumo_mes(mes or None)


# ----- cartões -----

@mcp.tool()
def listar_cartoes() -> list[dict]:
    """Lista os cartões cadastrados no app (nome e cor)."""
    return fin().listar_cartoes()


@mcp.tool()
def adicionar_cartao(nome: str, cor: str) -> dict:
    """Cadastra um cartão novo. cor em formato hexadecimal, ex.: '#1F9E89'.
    O cartão passa a aparecer nas transações e nas despesas."""
    return {"ok": fin().adicionar_cartao(nome, cor)}


@mcp.tool()
def listar_categorias() -> list[dict]:
    """Lista as categorias (nome, cor e orçamento mensal; orçamento 0 = sem limite)."""
    return fin().listar_categorias()


@mcp.tool()
def adicionar_categoria(nome: str, cor: str, orcamento: str = "") -> dict:
    """Cria uma categoria. cor em hexadecimal, ex.: '#1F9E89'. orcamento: limite mensal (opcional)."""
    return {"ok": True, "id": fin().adicionar_categoria(nome, cor, orcamento or 0)}


@mcp.tool()
def gasto_por_categoria(mes: str = "") -> dict:
    """Quanto já foi usado em cada categoria no mês (compras suas e despesas). Vazio = mês atual."""
    return {str(k): v for k, v in fin().gasto_por_categoria(mes or None).items()}


@mcp.tool()
def definir_renda(valor: str, mes: str = "") -> dict:
    """Define a renda total do mês. Com ela, o app mostra quanto o cartão consome da renda."""
    return {"ok": fin().definir_renda(valor, mes or None)}


def _id_da_categoria(nome: str):
    """Nome da categoria -> id (None se vazio ou não existir)."""
    if not nome:
        return None
    alvo = nome.strip().lower()
    return next((c["id"] for c in fin().listar_categorias() if c["nome"].lower() == alvo), None)


@mcp.tool()
def listar_compras(cartao: str = "", mes: str = "") -> list[dict]:
    """Lista as compras de cartão do mês. cartao: nome de um cartão cadastrado (vazio = todos)."""
    return fin().listar_compras(cartao or None, mes or None)


@mcp.tool()
def lancar_compra(cartao: str, item: str, valor_parcela: str,
                  parcelas: str = "", mes: str = "", pessoa: str = ".",
                  valor_real: str = "", recorrente: bool = False, categoria: str = "") -> dict:
    """Lança uma compra no cartão.
    cartao: nome de um cartão cadastrado (use listar_cartoes). valor_parcela: ex. 'R$ 63,19'.
    parcelas: ex. '3/12'. Vazio = à vista.
    pessoa: preencha só se for empréstimo (ex.: 'Pai'). Com pessoa preenchida, o item vira
    empréstimo dessa pessoa. Vazio ou '.' = compra sua.
    recorrente=True quando o item continua no mês seguinte depois da virada.
    categoria: nome de uma categoria cadastrada (use listar_categorias). Vazio = sem categoria.
    valor_real é opcional. O mês precisa estar aberto."""
    id_ = fin().lancar_compra(cartao, item, valor_parcela, parcelas=parcelas or "1/1",
                             mes=mes or None, pessoa=pessoa, valor_real=valor_real or None,
                             recorrente=recorrente, categoria_id=_id_da_categoria(categoria))
    return {"ok": True, "id": id_}


@mcp.tool()
def apagar_compra(id: int) -> dict:
    """Apaga uma compra de cartão pelo id (veja o id em listar_compras)."""
    return {"ok": fin().apagar_compra(id)}


# ----- receitas e despesas -----

@mcp.tool()
def listar_lancamentos(tabela: str, mes: str = "") -> list[dict]:
    """Lista receitas ou despesas do mês. tabela: 'receitas' ou 'despesas'."""
    return fin().listar_lancamentos(tabela, mes or None)


@mcp.tool()
def adicionar_lancamento(tabela: str, descricao: str, valor: str, mes: str = "",
                         recorrente: bool = False, categoria: str = "") -> dict:
    """Adiciona uma receita ou despesa. tabela: 'receitas' ou 'despesas'.
    recorrente=True (só despesas) faz o item continuar no mês seguinte depois da virada."""
    return {"ok": True, "id": fin().adicionar_lancamento(tabela, descricao, valor, mes or None,
                                                        recorrente=recorrente,
                                                        categoria_id=_id_da_categoria(categoria))}


@mcp.tool()
def apagar_lancamento(tabela: str, id: int) -> dict:
    """Apaga uma receita ou despesa pelo id."""
    return {"ok": fin().apagar_lancamento(tabela, id)}


# ----- quem me deve -----

@mcp.tool()
def quanto_me_devem(mes: str = "") -> list[dict]:
    """Por pessoa, no mês: quanto foi emprestado, quanto já pagou e quanto está em aberto.
    Vazio = mês atual."""
    return fin().quanto_me_devem(mes or None)


@mcp.tool()
def emprestimos_de(pessoa: str, mes: str = "") -> list[dict]:
    """Lista os empréstimos lançados para uma pessoa (ex.: 'Pai') no mês.
    Vazio = mês atual. Use 'todos' para ver todos os meses."""
    if mes.strip().lower() == "todos":
        return fin().emprestimos_de(pessoa, None)
    return fin().emprestimos_de(pessoa, mes or None)


@mcp.tool()
def registrar_pagamento(pessoa: str, valor: str, descricao: str = "", mes: str = "") -> dict:
    """Registra um valor que a pessoa pagou de volta, no mês. Vazio = mês atual."""
    return {"ok": True,
            "id": fin().registrar_pagamento(pessoa, valor, descricao, mes=mes or None)}


# ----- caixinhas -----

@mcp.tool()
def listar_caixinhas() -> list[dict]:
    """Lista as caixinhas (dono, nome e valor)."""
    return fin().listar_caixinhas()


@mcp.tool()
def definir_caixinha(dono: str, nome: str, valor: str) -> dict:
    """Cria uma caixinha ou atualiza o valor de uma existente (ex.: dono 'Rafael', nome 'Reserva')."""
    return {"ok": fin().definir_caixinha(dono, nome, valor)}


if __name__ == "__main__":
    mcp.run()
