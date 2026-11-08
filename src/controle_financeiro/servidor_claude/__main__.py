"""Ponto de entrada do servidor do Claude: python -m controle_financeiro.servidor_claude."""
from controle_financeiro.servidor_claude.servidor import mcp

if __name__ == "__main__":
    mcp.run()
