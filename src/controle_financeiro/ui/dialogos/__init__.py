"""Janelas de diálogo, separadas por assunto. Importe daqui: from controle_financeiro.ui.dialogos import Login"""
from controle_financeiro.ui.dialogos.acesso import ConectarSupabase, ContaDialog, Login
from controle_financeiro.ui.dialogos.cadastros import CategoriaForm, CategoriasDialog, GerenciarMeses, NovoCartao
from controle_financeiro.ui.dialogos.compra import campos_compra, dialogo_compra

__all__ = ["CategoriaForm", "CategoriasDialog", "ConectarSupabase", "ContaDialog", "GerenciarMeses", "Login",
           "NovoCartao", "campos_compra", "dialogo_compra"]
