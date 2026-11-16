"""Servidor MCP do Controle Financeiro.

O Claude Desktop inicia este arquivo sozinho (transporte stdio).
Cada ferramenta lê ou grava no mesmo banco que o app desktop usa,
então a tela do app atualiza em até 2 segundos depois de qualquer mudança.

Mês vazio em qualquer ferramenta = o mês em que você está (o mais recente aberto).
"""
from mcp.server.fastmcp import FastMCP

from controle_financeiro.dados.contexto import fin

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
    Antes de virar, o app salva uma cópia de segurança de todos os dados (o caminho vem em
    "backup"); se a cópia falhar, o mês não é virado.
    Use somente quando o usuário pedir a virada de mês."""
    return fin().virar_mes()


@mcp.tool()
def previsao_proximo_mes(mes: str = "") -> dict:
    """Previsão do mês seguinte: como ele começaria se a virada fosse feita agora, com as mesmas
    regras da virada (recorrentes ficam, parcelas avançam, receitas são copiadas). Só calcula,
    não grava nada. Traz receitas, despesas, meu cartão (total e por cartão), empréstimos a
    receber e o saldo previsto. mes vazio = mês atual (a previsão é do mês seguinte a ele)."""
    return fin().previsao_proximo_mes(mes or None)


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
def definir_categoria(tabela: str, id: int, categoria: str) -> dict:
    """Troca SÓ a categoria de uma compra ou despesa que já existe (não apaga nem recria).
    tabela: 'compras' ou 'despesas'. id: veja em listar_compras / listar_lancamentos.
    categoria: nome de uma categoria cadastrada (use listar_categorias). Vazio = sem categoria."""
    if categoria and _id_da_categoria(categoria) is None:
        return {"ok": False, "erro": f"Categoria '{categoria}' não existe."}
    return {"ok": fin().classificar(tabela, id, _id_da_categoria(categoria))}


@mcp.tool()
def listar_compras(cartao: str = "", mes: str = "") -> list[dict]:
    """Lista as compras de cartão do mês. cartao: nome de um cartão cadastrado (vazio = todos)."""
    return fin().listar_compras(cartao or None, mes or None)


@mcp.tool()
def lancar_compra(cartao: str, item: str, valor_parcela: str,
                  parcelas: str = "", mes: str = "", pessoa: str = ".",
                  recorrente: bool = False, categoria: str = "") -> dict:
    """Lança uma compra no cartão.
    cartao: nome de um cartão cadastrado (use listar_cartoes). valor_parcela: ex. 'R$ 63,19'.
    parcelas: ex. '3/12'. Vazio = à vista.
    pessoa: preencha só se for empréstimo (ex.: 'Pai'). Com pessoa preenchida, o item vira
    empréstimo dessa pessoa. Vazio ou '.' = compra sua.
    recorrente=True quando o item continua no mês seguinte depois da virada.
    categoria: nome de uma categoria cadastrada (use listar_categorias). Vazio = sem categoria.
    O mês precisa estar aberto."""
    id_ = fin().lancar_compra(cartao, item, valor_parcela, parcelas=parcelas or "1/1",
                             mes=mes or None, pessoa=pessoa,
                             recorrente=recorrente, categoria_id=_id_da_categoria(categoria))
    return {"ok": True, "id": id_}


@mcp.tool()
def editar_compra(id: int, cartao: str = "", item: str = "", parcelas: str = "",
                  valor_parcela: str = "", pessoa: str = "", recorrente: bool | None = None,
                  categoria: str = "") -> dict:
    """Corrige uma compra de cartão que já existe, sem apagar nem recriar: o id, o mês e a
    data de lançamento continuam os mesmos. Passe só o que muda; campo vazio fica como está.
    id: veja em listar_compras. valor_parcela: ex. 'R$ 63,19'. parcelas: ex. '4/12' ('1/1' = à vista).
    pessoa: nome de quem deve (vira empréstimo) ou '.' para a compra voltar a ser sua.
    recorrente: True ou False (omitido = não muda).
    categoria: nome de uma categoria cadastrada; para tirar a categoria, use definir_categoria.
    Confirme com o usuário qual compra é antes de editar."""
    campos = {chave: valor for chave, valor in (
        ("cartao", cartao), ("item", item), ("parcelas", parcelas),
        ("valor_parcela", valor_parcela), ("pessoa", pessoa)) if str(valor).strip()}
    if recorrente is not None:
        campos["recorrente"] = recorrente
    if categoria:
        id_categoria = _id_da_categoria(categoria)
        if id_categoria is None:
            return {"ok": False, "erro": f"Categoria '{categoria}' não existe."}
        campos["categoria_id"] = id_categoria
    if not campos:
        return {"ok": False, "erro": "Nada para mudar: informe ao menos um campo."}
    return {"ok": True, "compra": fin().editar_compra(id, **campos)}


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
def editar_lancamento(tabela: str, id: int, descricao: str = "", valor: str = "",
                      recorrente: bool | None = None, categoria: str = "") -> dict:
    """Corrige uma receita ou despesa que já existe, sem apagar nem recriar: o id, o mês e a
    data de lançamento continuam os mesmos. Passe só o que muda; campo vazio fica como está.
    tabela: 'receitas' ou 'despesas'. id: veja em listar_lancamentos. valor: ex. 'R$ 1.200,00'.
    recorrente e categoria valem só para despesas (receitas não têm). recorrente omitido = não muda.
    categoria: nome de uma categoria cadastrada; para tirar a categoria, use definir_categoria.
    Confirme com o usuário qual lançamento é antes de editar."""
    campos = {chave: valor_ for chave, valor_ in (("descricao", descricao), ("valor", valor))
              if str(valor_).strip()}
    if recorrente is not None:
        campos["recorrente"] = recorrente
    if categoria:
        id_categoria = _id_da_categoria(categoria)
        if id_categoria is None:
            return {"ok": False, "erro": f"Categoria '{categoria}' não existe."}
        campos["categoria_id"] = id_categoria
    if not campos:
        return {"ok": False, "erro": "Nada para mudar: informe ao menos um campo."}
    return {"ok": True, "lancamento": fin().editar_lancamento(tabela, id, **campos)}


@mcp.tool()
def buscar(texto: str) -> dict:
    """Procura um texto em todos os meses: itens de compras, pessoas e descrições de receitas e
    despesas (sem diferenciar maiúsculas). Ex.: 'uber', 'Pai', 'Netflix'. Devolve até 200
    resultados, do mês mais novo para o mais antigo, e o total somado.
    Útil para perguntas como "quanto gastei com Uber esse ano?". Só leitura."""
    resultados = fin().buscar(texto)
    return {"resultados": resultados, "quantidade": len(resultados),
            "total": round(sum(r["valor"] or 0 for r in resultados), 2)}


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
def definir_meta_caixinha(dono: str, nome: str, meta: str = "", data_alvo: str = "") -> dict:
    """Define a meta de uma caixinha e a data alvo (AAAA-MM). Vazio = remove a meta."""
    c = next((x for x in fin().listar_caixinhas()
              if x["dono"] == dono.strip() and x["nome"] == nome.strip()), None)
    if not c:
        return {"ok": False, "erro": "Caixinha não encontrada."}
    return {"ok": fin().definir_meta_caixinha(c["id"], meta or None, data_alvo or None)}


@mcp.tool()
def assinaturas(mes: str = "") -> dict:
    """Itens recorrentes do mês (assinaturas e despesas fixas), com total por mês e por ano."""
    return fin().assinaturas(mes or None)


@mcp.tool()
def parcelas_futuras(mes: str = "", quantos: int = 6) -> list[dict]:
    """Quanto ainda vai cair nos próximos meses, por cartão (compras suas com parcelas)."""
    return fin().parcelas_futuras(mes or None, quantos)


def _caixinha(dono, nome):
    alvo = (dono.strip().lower(), nome.strip().lower())
    return next((c for c in fin().listar_caixinhas()
                 if (c["dono"].lower(), c["nome"].lower()) == alvo), None)


@mcp.tool()
def guardar_na_caixinha(dono: str, nome: str, valor: str, descricao: str = "") -> dict:
    """Guarda dinheiro numa caixinha que já existe: soma o valor e anota no histórico.
    Ex.: dono 'Rafael', nome 'Viagem', valor 'R$ 200,00'. Só a pedido do usuário."""
    c = _caixinha(dono, nome)
    if not c:
        return {"ok": False, "erro": f"Não achei a caixinha {nome} de {dono}. Veja listar_caixinhas."}
    return {"ok": True, "caixinha": fin().guardar_na_caixinha(c["id"], valor, descricao)}


@mcp.tool()
def retirar_da_caixinha(dono: str, nome: str, valor: str, descricao: str = "") -> dict:
    """Retira dinheiro de uma caixinha: subtrai o valor e anota no histórico.
    Não deixa retirar mais do que tem. Só a pedido do usuário."""
    c = _caixinha(dono, nome)
    if not c:
        return {"ok": False, "erro": f"Não achei a caixinha {nome} de {dono}. Veja listar_caixinhas."}
    return {"ok": True, "caixinha": fin().retirar_da_caixinha(c["id"], valor, descricao)}


@mcp.tool()
def historico_caixinha(dono: str, nome: str) -> dict:
    """Movimentos de uma caixinha (guardado, retirado, ajustes), do mais novo para o mais antigo.
    valor positivo = guardado, negativo = retirado; saldo = valor da caixinha depois. Só leitura."""
    c = _caixinha(dono, nome)
    if not c:
        return {"ok": False, "erro": f"Não achei a caixinha {nome} de {dono}. Veja listar_caixinhas."}
    if not fin().caixinhas_tem_historico():
        return {"ok": False, "erro": "O histórico ainda não está ativo: falta rodar o script "
                                     "07_historico_caixinhas.sql no Supabase."}
    return {"ok": True, "caixinha": c, "movimentos": fin().historico_caixinha(c["id"])}


@mcp.tool()
def listar_caixinhas() -> list[dict]:
    """Lista as caixinhas (dono, nome e valor)."""
    return fin().listar_caixinhas()


@mcp.tool()
def definir_caixinha(dono: str, nome: str, valor: str) -> dict:
    """Cria uma caixinha ou atualiza o valor de uma existente (ex.: dono 'Rafael', nome 'Reserva')."""
    return {"ok": fin().definir_caixinha(dono, nome, valor)}
