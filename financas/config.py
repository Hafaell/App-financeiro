"""Caminhos e constantes do projeto."""
import os
from pathlib import Path

PASTA = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "ControleFinanceiro"
BANCO_FORCADO = os.environ.get("FINANCAS_DB")  # usado só em testes
CHAVE_PATH = PASTA / "chave.key"
USUARIOS_PATH = PASTA / "usuarios.dat"
SESSAO_PATH = PASTA / "sessao.dat"

USUARIO_INICIAL = ("Rafael", "030426")  # criado no primeiro acesso
CARTOES_INICIAIS = (("Inter", "#F89A3D", "#2B1600"), ("Nubank", "#7B4FD0", "#FFFFFF"))
TABELAS_LANCAMENTO = ("receitas", "despesas")
# Categorias criadas no primeiro uso (o usuário pode renomear, mudar cor, orçamento e apagar)
CATEGORIAS_INICIAIS = (("Alimentação", "#F59E0B"), ("Transporte", "#3B82F6"),
                       ("Assinaturas", "#8B5CF6"), ("Saúde", "#10B981"),
                       ("Lazer", "#EC4899"), ("Outros", "#6B7280"))

# Banco de dados: SQLite local (padrão) ou Supabase/PostgreSQL.
# A conexão do Supabase fica criptografada em conexao.dat (gerada por supabase/configurar_conexao.py).
CONEXAO_PATH = PASTA / "conexao.dat"
TIPO_BANCO = os.environ.get("FINANCAS_BANCO") or ("postgres" if CONEXAO_PATH.exists() else "sqlite")
DATABASE_URL = os.environ.get("DATABASE_URL")  # opcional: sobrescreve a conexão guardada
