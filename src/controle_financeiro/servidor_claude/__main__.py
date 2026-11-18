"""Ponto de entrada do servidor do Claude.

python -m controle_financeiro.servidor_claude          inicia o servidor MCP (stdio)
python -m controle_financeiro.servidor_claude entrar   faz o login que o servidor usa
"""
import sys

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "entrar":
        from controle_financeiro.servidor_claude.entrar import main
        main()
    else:
        from controle_financeiro.servidor_claude.servidor import mcp
        mcp.run()
