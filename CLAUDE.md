# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Briefing do projeto

**O que é:** site (web) do Rafael para controlar cartões de crédito, empréstimos feitos com o cartão para outras pessoas, receitas, despesas e caixinhas. Substitui uma planilha antiga do Google Sheets. Os dados ficam no Supabase (PostgreSQL), isolados por conta.

**Dois jeitos de usar os mesmos dados:**
1. O site (`web/` + API em `src/controle_financeiro/web/`).
2. O Claude, pelo servidor MCP `controle-financeiro` (`servidor_claude/`), usado pela skill **assistente-financeiro** ("Ayla"). Uma alteração feita por um lado aparece no outro em ~1 s.

**Idioma:** código, interface, mensagens e comentários são em português do Brasil. Mantenha esse padrão (com acentos). Valores no formato brasileiro (R$ 1.250,50).

**Vocabulário do domínio:**
- **Cartões:** Inter e Nubank (cadastráveis; cada um tem cor).
- **Compra:** lançamento de cartão num mês, com `parcelas` (`3/12`, vazio = à vista 1/1) e `valor_parcela`.
- **Empréstimo:** compra com `pessoa` preenchida (ex.: Benzinho, Avô, Pai). `pessoa` vazia ou "." é compra do próprio Rafael e entra em "meu cartão". Não existe campo separado de empréstimo para o usuário.
- **Recorrente:** o item continua no mês seguinte na virada, sem avançar parcela (assinaturas, DIZ., Investimento). Não é o mesmo que empréstimo.
- **Receitas / despesas:** lançamentos à parte dos cartões. Só compras e despesas têm categoria; receitas não.
- **Categorias:** Alimentação, Assinaturas, Investimento, Lazer, Outros, Saúde, Transporte (editáveis; cada uma pode ter orçamento mensal). Não crie categoria sem o usuário pedir.
- **Pagamento:** valor que uma pessoa devolveu; abate o "em aberto" dela.
- **Mês aberto (sessão):** só meses abertos recebem lançamentos. Mês vazio nas ferramentas = mês atual (o mais recente aberto).
- **Virada de mês:** abre o mês seguinte copiando o atual (recorrentes ficam, parcelas x<y avançam, x=y e à vista saem, receitas são copiadas, caixinhas não mudam).

## Comandos

```
python -m pip install -e ".[claude,dev]"      # API + Ayla + pytest e pyflakes
python -m pytest                              # todos os testes
python -m pytest tests/test_financas.py::test_nome   # um teste
python -m pyflakes src tests                  # lint
python -m controle_financeiro.web.local       # API local com dados de exemplo (SQLite)
python -m controle_financeiro.servidor_claude # servidor MCP (stdio)
python -m controle_financeiro.servidor_claude entrar  # login do MCP (e-mail e senha; guarda só o refresh token)
```

Os testes (`tests/conftest.py`) forçam `FINANCAS_BANCO=sqlite` e redirecionam `LOCALAPPDATA` para uma pasta temporária, então nunca tocam no Supabase real. Fora dos testes, `fin()` (em `dados/contexto.py`) conecta ao **Supabase de verdade** com a sessão do usuário logado: qualquer script avulso que use `fin()` lê e grava dados reais. Avise o usuário antes de rodar um e prefira só leitura.

## Arquitetura

Três camadas, sempre nesta direção: `web/` (API do site) e `servidor_claude/` → `nucleo/servico.py` (`Financas`) → `nucleo/*` → `dados/banco.py`.

- **`nucleo/servico.py` é a fachada única.** Tanto a API do site quanto o servidor MCP chamam só `Financas`, que delega para um módulo por assunto (`compras`, `lancamentos`, `categorias`, `virada`...). Funcionalidade nova entra no módulo de `nucleo/`, ganha um método na fachada e só então vira tela ou ferramenta MCP.
- **Dois bancos, mesma interface** (`dados/banco.py`): `BancoSqlite` (testes/local) e `BancoPostgres` (Supabase via HTTP, `dados/nuvem.py`). O SQL é escrito com `?` (estilo SQLite) e convertido para `%s` no Postgres. O banco Supabase mantém cópia em memória, fila offline e detecta mudanças externas por versão (`meta.versao`). Por padrão cada leitura confere a versão antes (servidor MCP, testes); o servidor MCP e os testes fazem assim. O site usa `BancoWeb` (sem cópia em disco). `tests/test_desempenho.py` conta as chamadas de rede com um servidor falso.
- **Esquema em um só lugar** (`dados/esquema.py`), com marcadores `{ID}`, `{REAL}`, `{INT}` trocados por dialeto. Mudar uma tabela exige **duas coisas**: editar `esquema.py` (e o ajuste de bancos antigos em `_preparar`, no SQLite) **e** criar um novo script em `supabase/migracoes/NN_*.sql` para rodar à mão no SQL Editor do Supabase (veja `supabase/README.md`, que lista a ordem).
- **Tabelas opcionais** (`TABELAS_OPCIONAIS` em `esquema.py`): dependem de um script novo no Supabase. Enquanto ele não roda, `BancoPostgres` marca a tabela como indisponível (`disponivel()`), o sistema abre normal e só a função dela fica desligada. Hoje: `movimentos_caixinha` (script `07_historico_caixinhas.sql`), o histórico das caixinhas (guardar, retirar, ajustes).
- **Ids de linhas novas no Supabase:** dentro de `transacao()`, o `lastrowid` é da cópia local e pode não ser o do servidor. Para usar o id de uma linha recém-criada, grave com `gravar()` (que devolve o id real) e só então grave o que depende dele.
- **Multiusuário no Supabase:** todos os usuários compartilham as mesmas tabelas; cada linha tem `user_id` e o RLS isola os dados.
- **Dados locais** (chave, conexão, sessão) ficam criptografados em `%LOCALAPPDATA%\ControleFinanceiro` (`config.py`, `seguranca/cofre.py`), nunca no projeto.
- **Cópia antes da virada:** `Financas.virar_mes()` salva todos os dados em `%LOCALAPPDATA%\ControleFinanceiro\backups\<usuário>\antes-da-virada_*.cfauto` (criptografado com a chave local, sem senha; guarda as 6 mais novas) e só então vira. Se a cópia falhar, o mês não vira. Em Ferramentas > Cópias automáticas o usuário restaura uma delas (`Financas.restaurar_backup`): troca todos os dados numa transação só, mantendo os ids, e antes salva outra cópia (`antes-de-restaurar_*`). Restaurar exige estar online no Supabase.
- **Desfazer exclusão:** `Financas.recolocar` grava a linha de novo com o mesmo id. Comandos que já trazem a coluna `id` são reenviados assim pela fila offline (`_sql_para_envio`).

## Versão web (branch `Vercel`)

- **Dois lados com os mesmos dados:** o site e a Ayla. O app desktop (PySide6) foi removido. O site chama a API FastAPI
  (`web/api.py`, rotas só do que o site usa, cada uma chamando um método de `Financas`; erros como `{"erro": ...}`); `api/index.py`
  só a importa para o Vercel. Rota nova: método na fachada primeiro, depois a rota, teste em
  `tests/test_api.py` (troca `api.financas` por um `Financas` com SQLite) e a linha em `docs/vercel/API.md`.
- **`BancoWeb`** (`dados/banco_web.py`): o `BancoPostgres` sem disco e sem modo offline. Cada
  requisição cria um com o JWT do usuário; sem rede, a requisição falha (503) em vez de ir para fila.
- **Cópias antes da virada:** `Financas(..., copias_no_banco=True)` usa a tabela `backups`
  (`nucleo/copias.py`, script `08_backups_web.sql`); o servidor MCP segue com arquivos. A tabela fica fora
  da cópia em memória: é lida e gravada com `consultar_direto` / `gravar_direto`.
- **Dependências:** a base do `pyproject.toml` e o `requirements.txt` têm só o da web (o Vercel lê os
  dois). `mcp` é o extra `claude`.
- **Site (`web/`):** Vite + React + TypeScript, sem biblioteca de componentes. Cores e fonte nos tokens de
  `web/src/estilo.css`; celular primeiro (barra inferior com "Lançar"), lateral
  com as seções (Geral, Pessoal, Sistema) no PC. Login e cadastro pelo supabase-js. `npm run build` checa os tipos.
- **Ver no PC sem Supabase:** `python -m controle_financeiro.web.local` (SQLite com dados de exemplo) e
  `cd web && npm run dev:local`.

## Servidor MCP e skill assistente-financeiro

Cada `@mcp.tool()` em `servidor_claude/servidor.py` é uma ferramenta do Claude Desktop; ao criar ou alterar uma, o servidor precisa ser reiniciado. Categorias e cartões são passados por **nome** nas ferramentas (`_id_da_categoria` converte para id).

Ferramentas por assunto:
- Meses e resumo: `listar_meses`, `virar_mes`, `resumo_mes`, `previsao_proximo_mes` (simula a virada sem gravar), `parcelas_futuras`, `assinaturas`, `buscar` (texto em todos os meses, com total).
- Cartões e compras: `listar_cartoes`, `adicionar_cartao`, `listar_compras`, `lancar_compra`, `editar_compra` (muda só os campos informados, mantém id e data de lançamento), `apagar_compra`.
- Receitas e despesas: `listar_lancamentos`, `adicionar_lancamento`, `editar_lancamento` (muda só os campos informados), `apagar_lancamento`.
- Categorias: `listar_categorias`, `adicionar_categoria`, `definir_categoria` (troca só a categoria de um lançamento existente), `gasto_por_categoria`, `definir_renda`.
- Empréstimos: `quanto_me_devem`, `emprestimos_de`, `registrar_pagamento`.
- Caixinhas: `listar_caixinhas`, `definir_caixinha`, `definir_meta_caixinha`, `guardar_na_caixinha`, `retirar_da_caixinha`, `historico_caixinha`.

A skill **assistente-financeiro** (a "Ayla", em português, respostas curtas) vive na pasta sincronizada da conta do Claude, **fora deste repositório**. Rotinas:

| Rotina | Tipo | O que faz |
|---|---|---|
| Consultar empréstimos | leitura | `quanto_me_devem` + `emprestimos_de`; apelidos: benzinho/amor → `Benzinho`, vô/avô → `Avô`, pai → `Pai`; resposta em até 4 linhas |
| Relatório financeiro | leitura | resumo do mês em HTML mobile, com PNG de página inteira e link publicado; totais devem bater com `resumo_mes` |
| Verificar Gmail | leitura | lê emails "Transações recentes Inter/Nubank", compara com `listar_compras` e só lança após confirmação |
| Transações | escrita | lançar/apagar compras e despesas; checar duplicata antes de lançar; confirmar antes de apagar |
| Categorizar transações | escrita | `definir_categoria` em lançamentos sem categoria, sem apagar nem recriar |
| Virada de mês | escrita | `virar_mes`, só a pedido explícito |

Regras da Ayla que o código deve preservar: consultas nunca alteram dados; escritas só a pedido do usuário; nunca inventar dados e perguntar quando pessoa, cartão, valor ou mês forem ambíguos. Ao adicionar ou renomear uma ferramenta MCP, atualize a skill lá.

## Ambiente e configuração

- **Variáveis (Python):** `FINANCAS_BANCO` (`postgres` padrão, `sqlite` nos testes), `FINANCAS_DB` (arquivo SQLite), `FINANCAS_PASTA` (pasta de dados; `/tmp` no Vercel), `FINANCAS_FUSO` (padrão America/Sao_Paulo, aplicado em `api/index.py`), `SUPABASE_URL`/`SUPABASE_CHAVE`/`SUPABASE_PREFIXO` (o Vercel precisa das duas primeiras; o MCP lê `conexao.dat` se não houver).
- **Variáveis (site):** `VITE_SUPABASE_URL` e `VITE_SUPABASE_CHAVE` no Vercel (ou `web/.env.local`); `VITE_MODO_LOCAL=1` (`web/.env.demo`) liga o modo sem login.
- **Login da Ayla:** `python -m controle_financeiro.servidor_claude entrar` (guarda só o refresh token; `dados/contexto.py` → `seguranca/autenticacao.py`). Só funciona com Supabase.
- **Hook do projeto:** `.claude/hooks/pyflakes_hook.py` roda o pyflakes em todo `.py` editado (`.claude/settings.json`); corrija os avisos antes de seguir.
- **Código removido:** o app desktop (PySide6), seu empacotamento e o login local de testes não existem mais; não recrie.
- **Docs:** `docs/vercel/` (DEPLOY, API); `supabase/migracoes/` são scripts já executados, não edite.

## Agentes do projeto (`.claude/agents/`)

- **programador** (Opus, esforço médio): regra de negócio, API, servidor MCP, lógica do front e testes.
- **designer** (Sonnet): só o visual de `web/` (`estilo.css`, markup das telas, `public/`).
- **banco-de-dados** (Opus): esquema, migrações, RLS e Supabase; aplica scripts pelo Chrome ou anota em `supabase/PENDENTES.md`.

## Fluxo de trabalho

- Branch de trabalho: `Develop` (remoto `origin/Develop`); `master` é a base. A `Vercel` é a produção do
  site: traga a `Develop` para ela com `git merge Develop`.
- CI: `.github/workflows/testes.yml` roda pyflakes e pytest no Windows e no Linux, e o build do site, a cada push e pull request.
- Mudou regra de negócio: adicione teste em `tests/test_financas.py` (usa SQLite temporário via `criar_banco("teste")`). O banco de teste é compartilhado entre os testes: use nomes únicos (veja `_virada`) e passe `pasta_backups=tmp_path` ao criar `Financas`. As ferramentas MCP são testadas em `tests/test_servidor.py`.
- O working tree pode ter alterações do usuário não commitadas: não reverta nem commite sem ele pedir.
