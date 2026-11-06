# Controle Financeiro

Aplicativo desktop para Windows, com o servidor que permite ao Claude consultar e alterar os mesmos dados.

## Estrutura

```
iniciar.pyw              abre o app sem janela de terminal (use este arquivo)
mcp_server.py            servidor que o Claude Desktop usa
importar_novembro26.py   importa a planilha Novembro 26 (uma vez)
requirements.txt
build_exe.bat            gera os .exe
supabase/                guia e scripts para levar os dados ao Supabase (ver supabase/README.md)

financas/                regras e dados (sem tela)
  servico.py             Financas: ponto de entrada das regras
  contexto.py            usuário conectado (fin() e auth())
  seguranca.py           login: usuários e sessão criptografados
  banco.py               acesso ao SQLite e migrações
  cartoes.py  compras.py  lancamentos.py  emprestimos.py
  caixinhas.py  meses.py  virada.py  resumo.py
  utilidades.py          funções puras (valores, meses)
  config.py              caminhos e constantes

interface/               telas (PySide6)
  janela.py              janela principal
  app.py                 entrada da interface
  tema.py  formatacao.py  componentes.py  dialogos.py  seletor_mes.py
  paginas/               Visão geral, Transações, Empréstimos, Lançamentos, Caixinhas
```

## Instalação

    pip install -r requirements.txt

## Login e segurança

- Nomes de usuário, senhas (como resumo protegido) e a sessão ficam criptografados em
  `%LOCALAPPDATA%\ControleFinanceiro\usuarios.dat` e `sessao.dat`.
- A chave de criptografia fica em `chave.key` na mesma pasta. **Faça uma cópia dela.**
  Sem essa chave, os usuários não podem ser lidos.
- Os dados de transações ficam em SQLite local (um arquivo por usuário) ou no Supabase, se
  `conexao.dat` existir. A conexão do Supabase também fica criptografada.

## Primeira execução depois da atualização

- Se existir o arquivo antigo `usuarios.json`, os usuários são convertidos para o formato
  criptografado e o arquivo em texto puro é apagado.
- Será preciso fazer login uma vez de novo.

## Claude Desktop

Veja o caminho do Python e da pasta do projeto no `claude_desktop_config.json`, como antes.
Reinicie o Claude Desktop depois de atualizar.
