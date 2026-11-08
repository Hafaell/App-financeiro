"""Caminhos e constantes do aplicativo.

Os dados ficam em %LOCALAPPDATA%\\ControleFinanceiro, fora da pasta do projeto.
"""
import os
from pathlib import Path

PASTA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ControleFinanceiro"

# Arquivos criptografados (a chave de criptografia fica em chave.key)
CHAVE_PATH = PASTA / "chave.key"
CONEXAO_PATH = PASTA / "conexao.dat"   # token, projeto e chave pública do Supabase
SESSAO_PATH = PASTA / "sessao.dat"     # refresh token para o Claude (sem senha)
USUARIOS_PATH = PASTA / "usuarios.dat"  # usuários do modo local (só testes)

# Banco: "postgres" (Supabase, padrão) ou "sqlite" (local, para testes)
TIPO_BANCO = os.environ.get("FINANCAS_BANCO") or "postgres"
BANCO_FORCADO = os.environ.get("FINANCAS_DB")  # caminho de um SQLite de teste

TABELAS_LANCAMENTO = ("receitas", "despesas")
CARTOES_INICIAIS = (("Inter", "#F89A3D", "#2B1600"), ("Nubank", "#7B4FD0", "#FFFFFF"))
# Categorias criadas no primeiro uso (o usuário pode renomear, mudar cor, orçamento e apagar)
CATEGORIAS_INICIAIS = (("Alimentação", "#F59E0B"), ("Transporte", "#3B82F6"),
                       ("Assinaturas", "#8B5CF6"), ("Saúde", "#10B981"),
                       ("Lazer", "#EC4899"), ("Outros", "#6B7280"))
