"""Login do servidor da Ayla sem o app desktop: python -m controle_financeiro.servidor_claude entrar.

Pede (uma vez) a URL e a chave pública do projeto Supabase, depois o e-mail e a senha da conta.
Guarda só a conexão e o refresh token, criptografados em %LOCALAPPDATA%/ControleFinanceiro;
a senha nunca é salva. É o mesmo arquivo de sessão que o servidor MCP já lê.
"""
import getpass

from controle_financeiro.dados.conexao import ler_conexao, salvar_conexao


def _pedir_conexao():
    conexao = ler_conexao()
    if conexao.get("url") and conexao.get("chave"):
        return
    print("Informe os dados do projeto (Supabase > Project Settings > API).")
    url = input("URL do projeto (https://xxxx.supabase.co): ").strip().rstrip("/")
    chave = input("Chave pública (anon/publishable): ").strip()
    if not url or not chave:
        raise SystemExit("URL e chave são obrigatórias.")
    salvar_conexao({**conexao, "url": url, "chave": chave})


def main():
    from controle_financeiro.dados.contexto import auth
    _pedir_conexao()
    email = input("E-mail da conta: ").strip()
    senha = getpass.getpass("Senha: ")
    try:
        nome = auth().entrar(email, senha)
    except Exception as erro:
        raise SystemExit(f"Não consegui entrar: {erro}") from erro
    if not nome:
        raise SystemExit("E-mail ou senha incorretos.")
    print(f"Pronto: {nome} conectado. Reinicie o Claude Desktop para o servidor usar a sessão.")
