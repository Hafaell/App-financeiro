"""Ponto de entrada das regras: reúne todos os módulos de um usuário.

A interface e o servidor do Claude conversam só com esta classe.
"""
from .banco import criar_banco
from .caixinhas import Caixinhas
from .categorias import Categorias, Rendas
from .cartoes import Cartoes
from .compras import Compras
from .emprestimos import Emprestimos
from .lancamentos import Lancamentos
from .meses import Meses
from .resumo import Resumo
from .utilidades import nome_mes, proximo_mes
from .virada import Virada


class Financas:
    def __init__(self, banco):
        self.banco = banco
        self.meses = Meses(banco)
        self.cartoes = Cartoes(banco)
        self.compras = Compras(banco, self.meses, self.cartoes)
        self.lancamentos = Lancamentos(banco, self.meses)
        self.emprestimos = Emprestimos(banco, self.meses)
        self.caixinhas = Caixinhas(banco)
        self.categorias = Categorias(banco, self.meses)
        self.rendas = Rendas(banco, self.meses)
        self.resumo = Resumo(banco, self.cartoes, self.meses, self.emprestimos)
        self.virada = Virada(banco, self.meses)

    @classmethod
    def do_usuario(cls, usuario: str) -> "Financas":
        return cls(criar_banco(usuario))

    def versao(self) -> int:
        return self.banco.versao()

    # ----- cartões -----
    def listar_cartoes(self):
        return self.cartoes.listar()

    def adicionar_cartao(self, nome, cor):
        return self.cartoes.adicionar(nome, cor)

    cor_texto_para = staticmethod(Cartoes.cor_texto)

    # ----- meses -----
    def sessoes(self):
        return self.meses.sessoes()

    def mes_ativo(self):
        return self.meses.ativo()

    def virar_mes(self):
        return self.virada.executar()

    def apagar_mes(self, mes):
        return self.meses.apagar(mes)

    nome_mes = staticmethod(nome_mes)
    proximo_mes = staticmethod(proximo_mes)

    # ----- transações (compras de cartão) -----
    def listar_compras(self, cartao=None, mes=None):
        return self.compras.listar(cartao, mes)

    def obter_compra(self, id_):
        return self.compras.obter(id_)

    def lancar_compra(self, *args, **kwargs):
        return self.compras.lancar(*args, **kwargs)

    def atualizar_compra(self, *args, **kwargs):
        return self.compras.atualizar(*args, **kwargs)

    def apagar_compra(self, id_):
        return self.compras.apagar(id_)

    # ----- receitas e despesas -----
    def listar_lancamentos(self, tabela, mes=None):
        return self.lancamentos.listar(tabela, mes)

    def obter_lancamento(self, tabela, id_):
        return self.lancamentos.obter(tabela, id_)

    def adicionar_lancamento(self, tabela, descricao, valor, mes=None, recorrente=False,
                             categoria_id=None):
        return self.lancamentos.adicionar(tabela, descricao, valor, mes, recorrente, categoria_id)

    def atualizar_lancamento(self, tabela, id_, descricao, valor, recorrente=False,
                             categoria_id=None):
        return self.lancamentos.atualizar(tabela, id_, descricao, valor, recorrente, categoria_id)

    def apagar_lancamento(self, tabela, id_):
        return self.lancamentos.apagar(tabela, id_)

    # ----- empréstimos -----
    def quanto_me_devem(self, mes=None):
        return self.emprestimos.por_pessoa(mes)

    def emprestimos_de(self, pessoa, mes=None):
        return self.emprestimos.detalhe(pessoa, mes)

    def registrar_pagamento(self, pessoa, valor, descricao="", mes=None):
        return self.emprestimos.pagar(pessoa, valor, descricao, mes)

    # ----- caixinhas -----
    def listar_caixinhas(self):
        return self.caixinhas.listar()

    def obter_caixinha(self, id_):
        return self.caixinhas.obter(id_)

    def definir_caixinha(self, dono, nome, valor):
        return self.caixinhas.definir(dono, nome, valor)

    def atualizar_caixinha(self, id_, dono, nome, valor):
        return self.caixinhas.atualizar(id_, dono, nome, valor)

    # ----- categorias, orçamento e renda -----
    def listar_categorias(self):
        return self.categorias.listar()

    def adicionar_categoria(self, nome, cor, orcamento=0):
        return self.categorias.adicionar(nome, cor, orcamento)

    def atualizar_categoria(self, id_, nome, cor, orcamento=0):
        return self.categorias.atualizar(id_, nome, cor, orcamento)

    def apagar_categoria(self, id_):
        return self.categorias.apagar(id_)

    def gasto_por_categoria(self, mes=None):
        return self.categorias.gasto_do_mes(mes)

    def obter_renda(self, mes=None):
        return self.rendas.obter(mes)

    def definir_renda(self, valor, mes=None):
        return self.rendas.definir(valor, mes)

    # ----- resumo -----
    def resumo_mes(self, mes=None):
        return self.resumo.do_mes(mes)
