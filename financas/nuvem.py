"""Conexão com o Supabase pela API (HTTP), com o login do próprio Supabase Auth.

Não há senha do banco no computador: só a URL do projeto e a chave pública (anon).
Cada comando SQL vai à função executar_sql (ou executar_lote), que roda com as permissões
do usuário logado. As regras de acesso (RLS) garantem que cada um só vê os próprios dados.
"""
import requests

TEMPO_LIMITE = 10  # segundos


class ErroConexao(RuntimeError):
    """Sem internet ou Supabase fora do ar."""


class SessaoExpirada(RuntimeError):
    """O login expirou ou é inválido: é preciso entrar de novo."""


class ErroBanco(RuntimeError):
    """O Supabase recusou o comando (SQL inválido, regra de acesso, valor errado)."""


class ClienteSupabase:
    def __init__(self, url: str, chave_publica: str, prefixo_api: str = "/rest/v1",
                 ao_renovar=None):
        self.url = url.rstrip("/")
        self.prefixo_api = prefixo_api  # o Supabase usa /rest/v1; testes locais usam vazio
        self.chave = chave_publica
        self._token = None
        self._refresh = None
        self.usuario_email = None
        self.ao_renovar = ao_renovar  # função(refresh, email): guarda o novo refresh token

    # ----- login -----

    def entrar(self, email: str, senha: str):
        """Login pelo Supabase Auth. Guarda o token só na memória (nada vai para o disco)."""
        dados = self._chamar("POST", "/auth/v1/token?grant_type=password",
                             {"email": email, "password": senha}, autenticar=False)
        self._token = dados["access_token"]
        self._refresh = dados.get("refresh_token")
        self.usuario_email = email
        self._avisar_renovacao()

    def cadastrar(self, email: str, senha: str) -> bool:
        """Cria a conta. Devolve True se já entrou (confirmação de e-mail desligada) ou
        False se é preciso confirmar o e-mail antes de entrar."""
        dados = self._chamar("POST", "/auth/v1/signup", {"email": email, "password": senha},
                             autenticar=False)
        if dados and dados.get("access_token"):
            self._token = dados["access_token"]
            self._refresh = dados.get("refresh_token")
            self.usuario_email = email
            self._avisar_renovacao()
            return True
        return False

    def restaurar(self, refresh_token: str, email: str) -> bool:
        """Retoma uma sessão guardada, usando só o refresh token (nunca a senha)."""
        self._refresh = refresh_token
        self.usuario_email = email
        if self._renovar():
            return True
        self.sair()
        return False

    def _avisar_renovacao(self):
        if self.ao_renovar and self._refresh:
            self.ao_renovar(self._refresh, self.usuario_email)

    def usar_token(self, token: str):
        """Para testes e para o caso em que o token já é conhecido."""
        self._token = token

    def sair(self):
        self._token = None
        self._refresh = None
        self.usuario_email = None

    @property
    def logado(self) -> bool:
        return self._token is not None

    def _renovar(self) -> bool:
        if not self._refresh:
            return False
        try:
            dados = self._chamar("POST", "/auth/v1/token?grant_type=refresh_token",
                                 {"refresh_token": self._refresh}, autenticar=False)
        except SessaoExpirada:
            return False
        self._token = dados["access_token"]
        self._refresh = dados.get("refresh_token", self._refresh)
        self._avisar_renovacao()
        return True

    # ----- chamadas -----

    def _chamar(self, metodo, caminho, corpo=None, autenticar=True):
        cabecalhos = {"apikey": self.chave, "Content-Type": "application/json"}
        if autenticar:
            if not self._token:
                raise SessaoExpirada("Entre com seu usuário e senha.")
            cabecalhos["Authorization"] = f"Bearer {self._token}"
        try:
            resp = requests.request(metodo, self.url + caminho, json=corpo,
                                    headers=cabecalhos, timeout=TEMPO_LIMITE)
        except requests.RequestException as e:
            raise ErroConexao("Não consegui falar com o Supabase. Verifique a internet.") from e
        if resp.status_code == 401 or (not autenticar and resp.status_code in (400, 401)
                                       and caminho.startswith("/auth/v1/token")):
            raise SessaoExpirada("Usuário ou senha incorretos, ou sessão expirada.")
        if resp.status_code >= 400:
            mensagem = ""
            try:
                dados = resp.json()
                mensagem = dados.get("message") or dados.get("msg") or dados.get("error_description") or ""
            except ValueError:
                pass
            raise ErroBanco(mensagem or f"O Supabase recusou o pedido (código {resp.status_code}).")
        return resp.json() if resp.content else None

    def _rpc(self, nome, corpo):
        try:
            return self._chamar("POST", f"{self.prefixo_api}/rpc/{nome}", corpo)
        except SessaoExpirada:
            if self._renovar():
                return self._chamar("POST", f"{self.prefixo_api}/rpc/{nome}", corpo)
            raise

    def executar(self, sql: str, params=()):
        """Executa um comando. Devolve {'linhas': [...]} para SELECT, ou {'id', 'afetadas'}."""
        return self._rpc("executar_sql", {"consulta": sql, "parametros": _json_params(params)})

    def executar_lote(self, comandos):
        """Vários comandos numa só transação no servidor: tudo ou nada."""
        lista = [{"sql": s, "params": _json_params(p)} for s, p in comandos]
        return self._rpc("executar_lote", {"comandos": lista})

    def preparar(self):
        """Primeiro acesso do usuário: cartões e categorias padrão (só na primeira vez)."""
        self._rpc("preparar_usuario", {})


def _json_params(params):
    """Valores em formato que o JSON aceita (sem tipos do Python que o JSON não tem)."""
    saida = []
    for v in params:
        if v is None or isinstance(v, (int, float, str)):
            saida.append(v)
        else:
            saida.append(str(v))
    return saida
