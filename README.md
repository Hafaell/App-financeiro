# Controle Financeiro

Site (celular e PC) para controlar os gastos dos cartões, os empréstimos para outras
pessoas, as receitas, as despesas e as caixinhas. Os dados ficam no Supabase, e cada conta vê
apenas os próprios dados.

O projeto também tem um servidor (`servidor_claude`) que permite ao Claude consultar e alterar
os mesmos dados.

## Como usar

- **Site:** entre com o e-mail e a senha da conta (veja `docs/vercel/DEPLOY.md`).
- **Ayla (Claude):** rode uma vez `python -m controle_financeiro.servidor_claude entrar` para
  guardar a sessão (só o refresh token, criptografado; a senha não é salva). Depois o Claude
  Desktop inicia o servidor com `python -m controle_financeiro.servidor_claude`.

Para configurar o banco, veja `supabase/README.md`.

## Estrutura

```
controle-financeiro/
  pyproject.toml
  requirements.txt
  src/controle_financeiro/
    config.py              caminhos e constantes
    dados/                 acesso aos dados
      banco.py             banco local (SQLite) e Supabase, com cópia em memória e fila offline
      nuvem.py             cliente HTTP do Supabase (login e comandos SQL)
      conexao.py           URL e chave pública do Supabase, guardadas criptografadas
      contexto.py          quem está conectado (usado pelo servidor do Claude)
      esquema.py           definição das tabelas
    nucleo/                regras de negócio, sem tela
      servico.py           fachada usada pela API do site e pelo servidor do Claude
      compras.py, lancamentos.py, emprestimos.py, caixinhas.py, categorias.py,
      cartoes.py, meses.py, virada.py, planejamento.py, resumo.py,
      ferramentas.py, importacao.py, utilidades.py
    seguranca/             criptografia e login
      cofre.py             criptografia dos arquivos locais
      autenticacao.py      entrar, sair e sessão
    web/                   API (FastAPI) do site, servida pelo Vercel
    servidor_claude/       servidor MCP para o Claude (Ayla)
  web/                     site (React + TypeScript)
  api/                     entrada da API no Vercel
  tests/                   testes automatizados (pytest)
  supabase/migracoes/      scripts SQL, na ordem de execução
```

## Desenvolvimento

```
python -m pip install -e ".[claude,dev]"
python -m pytest
```

Os testes usam um banco SQLite temporário, então não tocam nos dados reais.

## Versão web (Vercel)

A branch `Vercel` tem também um site com as mesmas telas e os mesmos dados (celular e PC),
publicado no Vercel. As regras são as mesmas (`nucleo/`), servidas por uma API em Python
(`src/controle_financeiro/web/api.py`, chamada pelo `api/index.py`) e mostradas pelo site em
`web/` (React + TypeScript). Lançar algo no site aparece na Ayla, e vice-versa.

- Como publicar: `docs/vercel/DEPLOY.md`.
- Rotas da API: `docs/vercel/API.md`. Plano e decisões: `docs/vercel/PLANO.md`.
- Ver o site no PC com dados de exemplo: `python -m controle_financeiro.web.local` e, em outro
  terminal, `cd web && npm install && npm run dev:local`.

## Dados do usuário

Os arquivos locais (chave de criptografia, conexão, sessão e cópia dos dados) ficam em
`%LOCALAPPDATA%\ControleFinanceiro`, fora da pasta do projeto.
