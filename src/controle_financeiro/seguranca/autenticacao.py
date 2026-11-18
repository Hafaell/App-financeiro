"""Login do servidor da Ayla pelo Supabase Auth (e-mail e senha).

O token de acesso fica só na memória. A sessão guardada é só o refresh token, criptografado em
%LOCALAPPDATA%/ControleFinanceiro: é ela que mantém o servidor logado (criada por
`python -m controle_financeiro.servidor_claude entrar`). Nenhuma senha é salva.
"""
from controle_financeiro.config import SESSAO_PATH
from controle_financeiro.seguranca.cofre import Cofre


class Autenticacao:
    def __init__(self, cofre: Cofre = None):
        import os
        from controle_financeiro.dados.banco import configuracao_supabase
        from controle_financeiro.dados.nuvem import ClienteSupabase
        self.cofre = cofre or Cofre()
        url, chave = configuracao_supabase()
        prefixo = os.environ.get("SUPABASE_PREFIXO", "/rest/v1")  # vazio só nos testes locais
        self.cliente = ClienteSupabase(url, chave, prefixo_api=prefixo, ao_renovar=self._guardar_sessao)

    def entrar(self, email: str, senha: str):
        """Devolve o e-mail de quem entrou, ou None se o login estiver errado.
        Erros de conexão (sem internet) são levantados."""
        from controle_financeiro.dados.nuvem import SessaoExpirada
        try:
            self.cliente.entrar(email.strip(), senha)
        except SessaoExpirada:
            return None
        return self.cliente.usuario_email

    def usuario_servico(self):
        """E-mail do usuário conectado, usando a sessão guardada (sem pedir senha), ou None."""
        if self.cliente.logado:
            return self.cliente.usuario_email
        sessao = self._ler_sessao()
        if not sessao:
            return None
        from controle_financeiro.dados.nuvem import ErroConexao
        try:
            return sessao["email"] if self.cliente.restaurar(sessao["refresh"], sessao["email"]) else None
        except ErroConexao:
            return None

    def _guardar_sessao(self, refresh, email):
        SESSAO_PATH.parent.mkdir(parents=True, exist_ok=True)
        SESSAO_PATH.write_bytes(self.cofre.cifrar({"refresh": refresh, "email": email}))

    def _ler_sessao(self):
        if not SESSAO_PATH.exists():
            return None
        try:
            dados = self.cofre.decifrar(SESSAO_PATH.read_bytes())
        except Exception:
            return None
        return dados if dados.get("refresh") else None
