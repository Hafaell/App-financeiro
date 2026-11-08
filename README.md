# Controle Financeiro

Aplicativo desktop (Windows) para controlar os gastos dos cartões, os empréstimos para outras
pessoas, as receitas, as despesas e as caixinhas. Os dados ficam no Supabase, e cada conta vê
apenas os próprios dados.

O app também tem um servidor (`servidor_claude`) que permite ao Claude consultar e alterar
os mesmos dados.

## Como usar

1. Na primeira abertura, cole o token de acesso pessoal do Supabase e escolha o projeto.
2. Entre com o e-mail e a senha da conta.
3. Em **Minha conta** (barra lateral), troque o token ou o projeto quando precisar.

Para configurar o banco, veja `supabase/README.md`.

## Estrutura

```
controle-financeiro/
  iniciar.pyw              abre o app sem janela de terminal
  build_exe.bat            gera o app em pasta + dist\ControleFinanceiro.zip
  pyproject.toml
  requirements.txt
  src/controle_financeiro/
    __main__.py            ponto de entrada (python -m controle_financeiro)
    config.py              caminhos e constantes
    dados/                 acesso aos dados
      banco.py             banco local (SQLite) e Supabase, com cópia em memória e fila offline
      nuvem.py             cliente HTTP do Supabase (login e comandos SQL)
      conexao.py           token, projeto e chave pública, guardados criptografados
      contexto.py          quem está logado nesta janela
      esquema.py           definição das tabelas
    nucleo/                regras de negócio, sem tela
      servico.py           fachada usada pela interface e pelo servidor do Claude
      compras.py, lancamentos.py, emprestimos.py, caixinhas.py, categorias.py,
      cartoes.py, meses.py, virada.py, planejamento.py, resumo.py,
      ferramentas.py, importacao.py, utilidades.py
    seguranca/             criptografia e login
      cofre.py             criptografia dos arquivos locais
      autenticacao.py      entrar, sair e sessão
    ui/                    interface gráfica (PySide6)
      app.py               inicialização e tela de entrada
      janela.py            janela principal
      dialogos.py          telas de entrada, cadastro, conexão e Minha conta
      paginas/             uma página por aba
    servidor_claude/       servidor MCP para o Claude
  tests/                   testes automatizados (pytest)
  supabase/migracoes/      scripts SQL, na ordem de execução
```

## Desenvolvimento

```
python -m pip install -e ".[dev]"
python -m pytest
python -m controle_financeiro
```

Os testes usam um banco SQLite temporário, então não tocam nos dados reais.

Para gerar o executável no Windows, rode `build_exe.bat`.

## Dados do usuário

Os arquivos locais (chave de criptografia, conexão, sessão e cópia dos dados) ficam em
`%LOCALAPPDATA%\ControleFinanceiro`, fora da pasta do projeto.
