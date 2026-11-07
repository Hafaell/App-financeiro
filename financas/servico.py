"""Ponto de entrada das regras: reúne todos os módulos de um usuário.

A interface e o servidor do Claude conversam só com esta classe.
"""
from datetime import date

from .banco import criar_banco
from .caixinhas import Caixinhas
from .ferramentas import Ferramentas
from .importacao import ler_extrato, marcar_situacao
from .planejamento import Planejamento
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
        self.caixinhas = Caixinhas(banco, self.meses)
        self.planejamento = Planejamento(banco, self.meses, self.cartoes)
        self.categorias = Categorias(banco, self.meses)
        self.rendas = Rendas(banco, self.meses)
        self.resumo = Resumo(banco, self.cartoes, self.meses, self.emprestimos)
        self.ferramentas = Ferramentas(banco, self.meses, self.resumo)
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

    def andamento_caixinhas(self):
        return self.caixinhas.andamento()

    def definir_meta_caixinha(self, id_, meta, data_alvo):
        return self.caixinhas.definir_meta(id_, meta, data_alvo)

    def definir_datas_cartao(self, id_, fechamento=None, vencimento=None):
        return self.cartoes.definir_datas(id_, fechamento, vencimento)

    def alertas_faturas(self, hoje=None, dias=5):
        return self.cartoes.alertas(hoje or date.today(), dias)

    def buscar(self, texto):
        return self.ferramentas.buscar(texto)

    def comparar_meses(self, quantos=6):
        return self.ferramentas.comparar_meses(quantos)

    def ler_extrato(self, nome_arquivo, conteudo, mes=None):
        """Lê o extrato e marca o que já está lançado no mês escolhido."""
        m = self.meses.interpretar(mes)
        itens = ler_extrato(nome_arquivo, conteudo)
        return marcar_situacao(itens, self.compras.listar(None, m),
                               self.lancamentos.listar("despesas", m), m)

    def importar_extrato(self, itens, destino, mes=None):
        """Grava os itens escolhidos. destino: nome de um cartão, ou 'despesas'.
        Cada item: {'data','descricao','valor','categoria_id'}."""
        m = self.meses.interpretar(mes)
        self.meses.exigir(m)
        feitos = 0
        for it in itens:
            if destino == "despesas":
                self.lancamentos.adicionar("despesas", it["descricao"], it["valor"], m,
                                           categoria_id=it.get("categoria_id"))
            else:
                self.compras.lancar(destino, it["descricao"][:80], it["valor"], "1/1", mes=m,
                                    categoria_id=it.get("categoria_id"))
            feitos += 1
        return feitos

    def exportar_backup(self, caminho, senha):
        return self.ferramentas.exportar_backup(caminho, senha)

    def assinaturas(self, mes=None):
        return self.planejamento.assinaturas(mes)

    def parcelas_futuras(self, mes=None, quantos=6):
        return self.planejamento.parcelas_futuras(mes, quantos)

    def obter_caixinha(self, id_):
        return self.caixinhas.obter(id_)

    def definir_caixinha(self, dono, nome, valor):
        return self.caixinhas.definir(dono, nome, valor)

    def atualizar_caixinha(self, id_, dono, nome, valor, meta=None, data_alvo=None):
        return self.caixinhas.atualizar(id_, dono, nome, valor, meta, data_alvo)

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
