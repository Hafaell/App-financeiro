"""API da versão web. Cada rota chama um método da fachada Financas (nucleo/servico.py), sem
regra de negócio própria. O usuário é identificado pelo token (JWT) do Supabase Auth, que vem
no cabeçalho Authorization; o RLS do Supabase garante que cada um só vê os próprios dados.

Erros saem como {"erro": "mensagem em português"} (veja docs/vercel/API.md).
"""
import base64
import json
from datetime import date
from typing import Annotated, Any, Literal, Optional, Union

from fastapi import Depends, FastAPI, Header, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel

from controle_financeiro.dados.nuvem import ErroBanco, ErroConexao, SessaoExpirada
from controle_financeiro.nucleo.importacao import banco_do_arquivo
from controle_financeiro.nucleo.servico import Financas

app = FastAPI(title="Controle Financeiro", docs_url="/api/docs", openapi_url="/api/openapi.json")

Valor = Union[float, str]  # aceita 63.19 ou "63,19" (a fachada converte)
Tabela = Literal["receitas", "despesas"]


# ----- usuário da requisição -----

def _id_do_usuario(token: str):
    """'sub' do JWT (só para cache; quem valida o token é o próprio Supabase a cada chamada)."""
    try:
        payload = token.split(".")[1]
        payload += "=" * (-len(payload) % 4)
        return json.loads(base64.urlsafe_b64decode(payload)).get("sub")
    except Exception:
        return None


def financas(authorization: Annotated[Optional[str], Header()] = None) -> Financas:
    """Financas do usuário dono do token. Os testes trocam esta função (dependency_overrides)."""
    from controle_financeiro.dados.banco import configuracao_supabase
    from controle_financeiro.dados.banco_web import BancoWeb
    from controle_financeiro.dados.nuvem import ClienteSupabase

    if not authorization or not authorization.lower().startswith("bearer "):
        raise SessaoExpirada("Entre com seu e-mail e senha.")
    token = authorization.split(" ", 1)[1].strip()
    url, chave = configuracao_supabase()
    cliente = ClienteSupabase(url, chave)
    cliente.usar_token(token)
    return Financas(BancoWeb(cliente, usuario_id=_id_do_usuario(token)), copias_no_banco=True)


Fin = Annotated[Financas, Depends(financas)]


# ----- erros -----

class NaoEncontrado(Exception):
    pass


def _erro(status, mensagem):
    return JSONResponse({"erro": str(mensagem)}, status_code=status)


@app.exception_handler(ValueError)
def _valor(_req: Request, e: ValueError):
    return _erro(400, e)


@app.exception_handler(NaoEncontrado)
def _nao_encontrado(_req: Request, e: NaoEncontrado):
    return _erro(404, e)


@app.exception_handler(SessaoExpirada)
def _sessao(_req: Request, e: SessaoExpirada):
    return _erro(401, e)


@app.exception_handler(ErroBanco)
def _banco(_req: Request, e: ErroBanco):
    return _erro(422, e)


@app.exception_handler(ErroConexao)
def _conexao(_req: Request, e: ErroConexao):
    return _erro(503, e)


@app.exception_handler(RuntimeError)
def _interno(_req: Request, e: RuntimeError):
    return _erro(500, e)


@app.exception_handler(RequestValidationError)
def _validacao(_req: Request, e: RequestValidationError):
    campos = ", ".join(str(err["loc"][-1]) for err in e.errors())
    return _erro(400, f"Dados inválidos no pedido: {campos}.")


def _existe(item, mensagem):
    if not item:
        raise NaoEncontrado(mensagem)
    return item


# ----- sistema -----

@app.get("/api/saude")
def saude():
    """Confere se a função está no ar (não toca no Supabase). Mostra o fuso em uso."""
    import time
    return {"ok": True, "fuso": time.strftime("%Z %z")}


@app.get("/api/versao")
def versao(fin: Fin):
    """Versão dos dados. O site compara com a anterior para saber se precisa recarregar."""
    remota = getattr(fin.banco, "versao_remota", None)
    return {"versao": remota() if remota else fin.versao()}


@app.get("/api/inicio")
def inicio(fin: Fin):
    """Listas que várias telas usam (uma requisição só ao abrir o site)."""
    return {"meses": fin.sessoes(), "mes_ativo": fin.mes_ativo(), "cartoes": fin.listar_cartoes(),
            "categorias": fin.listar_categorias(), "pessoas": fin.pessoas(),
            "tem_historico_caixinhas": fin.caixinhas_tem_historico(), "versao": fin.versao()}


@app.get("/api/painel")
def painel(fin: Fin, mes: str = ""):
    """Tudo da Visão geral numa requisição: resumo, gasto por categoria, orçamento e alertas."""
    m = fin.meses.interpretar(mes)
    return {"mes": m, "resumo": fin.resumo_mes(m), "gasto": _gasto(fin, m),
            "categorias": fin.listar_categorias(), "alertas": fin.alertas_faturas(date.today()),
            "renda": fin.obter_renda(m)}


# ----- meses e resumo -----

@app.get("/api/meses")
def meses(fin: Fin):
    return {"meses": fin.sessoes(), "mes_ativo": fin.mes_ativo()}


@app.post("/api/meses/virar")
def virar(fin: Fin):
    return fin.virar_mes()


@app.delete("/api/meses/{mes}")
def apagar_mes(fin: Fin, mes: str):
    return {"ok": fin.apagar_mes(mes)}


@app.get("/api/resumo")
def resumo(fin: Fin, mes: str = ""):
    return fin.resumo_mes(mes or None)


@app.get("/api/previsao")
def previsao(fin: Fin, mes: str = ""):
    return fin.previsao_proximo_mes(mes or None)


@app.get("/api/planejamento")
def planejamento(fin: Fin, mes: str = "", quantos: int = 6):
    """Previsão do próximo mês, parcelas futuras e assinaturas (a tela Planejamento)."""
    m = fin.meses.interpretar(mes)
    return {"mes": m, "previsao": fin.previsao_proximo_mes(m),
            "parcelas_futuras": fin.parcelas_futuras(m, quantos), "assinaturas": fin.assinaturas(m)}


@app.get("/api/parcelas-futuras")
def parcelas_futuras(fin: Fin, mes: str = "", quantos: int = 6):
    return fin.parcelas_futuras(mes or None, quantos)


@app.get("/api/assinaturas")
def assinaturas(fin: Fin, mes: str = ""):
    return fin.assinaturas(mes or None)


@app.get("/api/comparativo")
def comparativo(fin: Fin, quantos: int = 6):
    return fin.comparar_meses(quantos)


@app.get("/api/buscar")
def buscar(fin: Fin, texto: str = ""):
    linhas = fin.buscar(texto)
    return {"itens": linhas, "total": round(sum(l["valor"] or 0 for l in linhas), 2)}


@app.get("/api/alertas-faturas")
def alertas_faturas(fin: Fin, dias: int = 5):
    return fin.alertas_faturas(date.today(), dias)


# ----- cartões e compras -----

class NovoCartao(BaseModel):
    nome: str
    cor: str


class DatasCartao(BaseModel):
    dia_fechamento: Optional[int] = None
    dia_vencimento: Optional[int] = None


class NovaCompra(BaseModel):
    cartao: str
    item: str
    valor_parcela: Valor
    parcelas: str = "1/1"
    mes: Optional[str] = None
    pessoa: str = "."
    recorrente: bool = False
    categoria_id: Optional[int] = None


class EdicaoCompra(BaseModel):
    cartao: Optional[str] = None
    item: Optional[str] = None
    parcelas: Optional[str] = None
    valor_parcela: Optional[Valor] = None
    pessoa: Optional[str] = None
    recorrente: Optional[bool] = None
    categoria_id: Optional[int] = None


@app.get("/api/cartoes")
def cartoes(fin: Fin):
    return fin.listar_cartoes()


@app.post("/api/cartoes")
def adicionar_cartao(fin: Fin, dados: NovoCartao):
    return {"ok": fin.adicionar_cartao(dados.nome, dados.cor)}


@app.patch("/api/cartoes/{id_}/datas")
def datas_cartao(fin: Fin, id_: int, dados: DatasCartao):
    return {"ok": fin.definir_datas_cartao(id_, dados.dia_fechamento, dados.dia_vencimento)}


@app.get("/api/compras")
def compras(fin: Fin, mes: str = "", cartao: str = ""):
    return fin.listar_compras(cartao or None, mes or None)


@app.get("/api/compras/{id_}")
def compra(fin: Fin, id_: int):
    return _existe(fin.obter_compra(id_), "Compra não encontrada.")


@app.post("/api/compras")
def lancar_compra(fin: Fin, dados: NovaCompra):
    id_ = fin.lancar_compra(dados.cartao, dados.item, dados.valor_parcela, dados.parcelas or "1/1",
                            mes=dados.mes or None, pessoa=dados.pessoa or ".",
                            recorrente=dados.recorrente, categoria_id=dados.categoria_id)
    return {"id": id_}


@app.patch("/api/compras/{id_}")
def editar_compra(fin: Fin, id_: int, dados: EdicaoCompra):
    return fin.editar_compra(id_, **dados.model_dump(exclude_unset=True))


@app.delete("/api/compras/{id_}")
def apagar_compra(fin: Fin, id_: int):
    linha = _existe(fin.obter_compra(id_), "Compra não encontrada.")
    fin.apagar_compra(id_)
    return {"ok": True, "apagada": linha}  # o site guarda a linha para o "Desfazer"


# ----- receitas e despesas -----

class NovoLancamento(BaseModel):
    descricao: str
    valor: Valor
    mes: Optional[str] = None
    recorrente: bool = False
    categoria_id: Optional[int] = None


class EdicaoLancamento(BaseModel):
    descricao: Optional[str] = None
    valor: Optional[Valor] = None
    recorrente: Optional[bool] = None
    categoria_id: Optional[int] = None


class Recolocar(BaseModel):
    tabela: Literal["compras", "receitas", "despesas"]
    linha: dict[str, Any]


@app.get("/api/lancamentos/{tabela}")
def lancamentos(fin: Fin, tabela: Tabela, mes: str = ""):
    return fin.listar_lancamentos(tabela, mes or None)


@app.get("/api/lancamentos/{tabela}/{id_}")
def lancamento(fin: Fin, tabela: Tabela, id_: int):
    return _existe(fin.obter_lancamento(tabela, id_), "Lançamento não encontrado.")


@app.post("/api/lancamentos/{tabela}")
def adicionar_lancamento(fin: Fin, tabela: Tabela, dados: NovoLancamento):
    id_ = fin.adicionar_lancamento(tabela, dados.descricao, dados.valor, dados.mes or None,
                                   recorrente=dados.recorrente, categoria_id=dados.categoria_id)
    return {"id": id_}


@app.patch("/api/lancamentos/{tabela}/{id_}")
def editar_lancamento(fin: Fin, tabela: Tabela, id_: int, dados: EdicaoLancamento):
    campos = dados.model_dump(exclude_unset=True)
    if tabela == "receitas":  # receitas não têm recorrente nem categoria
        campos = {k: v for k, v in campos.items() if k in ("descricao", "valor")}
    return fin.editar_lancamento(tabela, id_, **campos)


@app.delete("/api/lancamentos/{tabela}/{id_}")
def apagar_lancamento(fin: Fin, tabela: Tabela, id_: int):
    linha = _existe(fin.obter_lancamento(tabela, id_), "Lançamento não encontrado.")
    fin.apagar_lancamento(tabela, id_)
    return {"ok": True, "apagada": linha}


class ApagarVarios(BaseModel):
    tabela: Literal["compras", "receitas", "despesas"]
    ids: list[int]


@app.post("/api/apagar-varios")
def apagar_varios(fin: Fin, dados: ApagarVarios):
    """Apaga várias linhas de uma vez; devolve as linhas para o "Desfazer"."""
    return {"ok": True, "apagadas": fin.apagar_varios(dados.tabela, dados.ids)}


@app.post("/api/recolocar")
def recolocar(fin: Fin, dados: Recolocar):
    """Desfaz a exclusão: grava a linha de novo, com o mesmo id."""
    fin.recolocar(dados.tabela, dados.linha)
    return {"ok": True}


# ----- categorias e renda -----

class Categoria(BaseModel):
    nome: str
    cor: str
    orcamento: Valor = 0


class Classificacao(BaseModel):
    categoria_id: Optional[int] = None


class Renda(BaseModel):
    valor: Valor
    mes: Optional[str] = None


def _gasto(fin, mes):
    """{categoria_id: valor} vira lista (o JSON não tem chave nula)."""
    return [{"categoria_id": k, "valor": v} for k, v in fin.gasto_por_categoria(mes).items()]


@app.get("/api/categorias")
def categorias(fin: Fin):
    return fin.listar_categorias()


@app.post("/api/categorias")
def adicionar_categoria(fin: Fin, dados: Categoria):
    return {"id": fin.adicionar_categoria(dados.nome, dados.cor, dados.orcamento)}


@app.put("/api/categorias/{id_}")
def atualizar_categoria(fin: Fin, id_: int, dados: Categoria):
    return {"ok": fin.atualizar_categoria(id_, dados.nome, dados.cor, dados.orcamento)}


@app.delete("/api/categorias/{id_}")
def apagar_categoria(fin: Fin, id_: int):
    return {"ok": fin.apagar_categoria(id_)}


@app.patch("/api/classificar/{tabela}/{id_}")
def classificar(fin: Fin, tabela: Literal["compras", "despesas"], id_: int, dados: Classificacao):
    return {"ok": fin.classificar(tabela, id_, dados.categoria_id)}


@app.get("/api/gasto-por-categoria")
def gasto_por_categoria(fin: Fin, mes: str = ""):
    return _gasto(fin, mes or None)


@app.get("/api/renda")
def renda(fin: Fin, mes: str = ""):
    return {"valor": fin.obter_renda(mes or None)}


@app.put("/api/renda")
def definir_renda(fin: Fin, dados: Renda):
    return {"ok": fin.definir_renda(dados.valor, dados.mes or None)}


# ----- empréstimos -----

class Pagamento(BaseModel):
    pessoa: str
    valor: Valor
    descricao: str = ""
    mes: Optional[str] = None


@app.get("/api/emprestimos")
def emprestimos(fin: Fin, mes: str = ""):
    return fin.quanto_me_devem(mes or None)


@app.get("/api/pessoas")
def pessoas(fin: Fin):
    return fin.pessoas()


@app.get("/api/emprestimos/{pessoa}")
def emprestimos_de(fin: Fin, pessoa: str, mes: str = ""):
    """Com mes vazio, traz todos os meses."""
    return fin.emprestimos_de(pessoa, mes or None)


@app.post("/api/pagamentos")
def registrar_pagamento(fin: Fin, dados: Pagamento):
    return {"id": fin.registrar_pagamento(dados.pessoa, dados.valor, dados.descricao, dados.mes or None)}


# ----- caixinhas -----

class NovaCaixinha(BaseModel):
    dono: str
    nome: str
    valor: Valor = 0


class EdicaoCaixinha(BaseModel):
    dono: str
    nome: str
    valor: Valor
    meta: Optional[Valor] = None
    data_alvo: Optional[str] = None


class Meta(BaseModel):
    meta: Optional[Valor] = None
    data_alvo: Optional[str] = None


class Movimento(BaseModel):
    valor: Valor
    descricao: str = ""


@app.get("/api/caixinhas")
def caixinhas(fin: Fin):
    """Cada caixinha com o andamento da meta (progresso, falta, por mês)."""
    return {"caixinhas": fin.andamento_caixinhas(), "tem_historico": fin.caixinhas_tem_historico()}


@app.get("/api/caixinhas/{id_}")
def caixinha(fin: Fin, id_: int):
    return _existe(fin.obter_caixinha(id_), "Caixinha não encontrada.")


@app.post("/api/caixinhas")
def definir_caixinha(fin: Fin, dados: NovaCaixinha):
    return {"ok": fin.definir_caixinha(dados.dono, dados.nome, dados.valor)}


@app.put("/api/caixinhas/{id_}")
def atualizar_caixinha(fin: Fin, id_: int, dados: EdicaoCaixinha):
    return {"ok": fin.atualizar_caixinha(id_, dados.dono, dados.nome, dados.valor, dados.meta,
                                         dados.data_alvo)}


@app.patch("/api/caixinhas/{id_}/meta")
def meta_caixinha(fin: Fin, id_: int, dados: Meta):
    return {"ok": fin.definir_meta_caixinha(id_, dados.meta, dados.data_alvo)}


@app.post("/api/caixinhas/{id_}/guardar")
def guardar(fin: Fin, id_: int, dados: Movimento):
    return fin.guardar_na_caixinha(id_, dados.valor, dados.descricao)


@app.post("/api/caixinhas/{id_}/retirar")
def retirar(fin: Fin, id_: int, dados: Movimento):
    return fin.retirar_da_caixinha(id_, dados.valor, dados.descricao)


@app.get("/api/caixinhas/{id_}/historico")
def historico(fin: Fin, id_: int):
    return fin.historico_caixinha(id_)


# ----- importar extrato -----

class Extrato(BaseModel):
    nome: str
    conteudo_base64: str
    mes: Optional[str] = None


class Importacao(BaseModel):
    itens: list[dict[str, Any]]
    destino: str  # nome de um cartão, ou "despesas"
    mes: Optional[str] = None


@app.post("/api/extrato/ler")
def ler_extrato(fin: Fin, dados: Extrato):
    try:
        conteudo = base64.b64decode(dados.conteudo_base64)
    except ValueError as e:
        raise ValueError("Não consegui ler o arquivo enviado.") from e
    return {"itens": fin.ler_extrato(dados.nome, conteudo, dados.mes or None),
            "cartao_sugerido": banco_do_arquivo(dados.nome)}


@app.post("/api/extrato/importar")
def importar_extrato(fin: Fin, dados: Importacao):
    return {"importados": fin.importar_extrato(dados.itens, dados.destino, dados.mes or None)}


# ----- cópias de segurança -----

class Restaurar(BaseModel):
    id: int


class Exportar(BaseModel):
    senha: str


@app.get("/api/backups")
def backups(fin: Fin):
    return fin.listar_backups()


@app.post("/api/backups/restaurar")
def restaurar(fin: Fin, dados: Restaurar):
    return {"copia_antes": fin.restaurar_backup(dados.id)}


@app.post("/api/backups/exportar")
def exportar(fin: Fin, dados: Exportar):
    """Arquivo .cfbak protegido por senha, para baixar."""
    nome = f"controle-financeiro_{date.today().isoformat()}.cfbak"
    return Response(fin.gerar_backup(dados.senha), media_type="application/octet-stream",
                    headers={"Content-Disposition": f'attachment; filename="{nome}"'})
