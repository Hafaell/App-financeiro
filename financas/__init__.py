"""Regras e dados do Controle Financeiro (sem interface gráfica)."""
from .servico import Financas
from .contexto import auth, fin

__all__ = ["Financas", "auth", "fin"]
