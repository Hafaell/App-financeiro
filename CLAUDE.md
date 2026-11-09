# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Briefing do projeto

**O que é:** app desktop Windows (PySide6) do Rafael para controlar cartões de crédito, empréstimos feitos com o cartão para outras pessoas, receitas, despesas e caixinhas. Substitui uma planilha antiga do Google Sheets. Os dados ficam no Supabase (PostgreSQL), isolados por conta.

**Dois jeitos de usar os mesmos dados:**
1. A interface gráfica (`ui/`).
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
python -m pip install -e ".[dev]"            # instala o app + pytest e pyflakes
python -m pytest                              # todos os testes
python -m pytest tests/test_financas.py::test_nome   # um teste
python -m pyflakes src tests                  # lint
python -m controle_financeiro                 # abre o app (ou iniciar.pyw, sem terminal)
python -m controle_financeiro.servidor_claude # servidor MCP (stdio)
build_exe.bat                                 # PyInstaller: dist\ControleFinanceiro.zip
```

Os testes (`tests/conftest.py`) forçam `FINANCAS_BANCO=sqlite` e redirecionam `LOCALAPPDATA` para uma pasta temporária, então nunca tocam no Supabase real. Fora dos testes, `fin()` (em `dados/contexto.py`) conecta ao **Supabase de verdade** com a sessão do usuário logado: qualquer script avulso que use `fin()` lê e grava dados reais. Avise o usuário antes de rodar um e prefira só leitura.

## Arquitetura

Três camadas, sempre nesta direção: `ui/` e `servidor_claude/` → `nucleo/servico.py` (`Financas`) → `nucleo/*` → `dados/banco.py`.

- **`nucleo/servico.py` é a fachada única.** Tanto a interface quanto o servidor MCP chamam só `Financas`, que delega para um módulo por assunto (`compras`, `lancamentos`, `categorias`, `virada`...). Funcionalidade nova entra no módulo de `nucleo/`, ganha um método na fachada e só então vira tela ou ferramenta MCP.
- **Dois bancos, mesma interface** (`dados/banco.py`): `BancoSqlite` (testes/local) e `BancoPostgres` (Supabase via HTTP, `dados/nuvem.py`). O SQL é escrito com `?` (estilo SQLite) e convertido para `%s` no Postgres. O banco Supabase mantém cópia em memória, fila offline e detecta mudanças externas por versão (`meta.versao`).
- **Esquema em um só lugar** (`dados/esquema.py`), com marcadores `{ID}`, `{REAL}`, `{INT}` trocados por dialeto. Mudar uma tabela exige **duas coisas**: editar `esquema.py` (e o ajuste de bancos antigos em `_preparar`, no SQLite) **e** criar um novo script em `supabase/migracoes/NN_*.sql` para rodar à mão no SQL Editor do Supabase (veja `supabase/README.md`, que lista a ordem).
- **Multiusuário no Supabase:** todos os usuários compartilham as mesmas tabelas; cada linha tem `user_id` e o RLS isola os dados.
- **Dados locais** (chave, conexão, sessão) ficam criptografados em `%LOCALAPPDATA%\ControleFinanceiro` (`config.py`, `seguranca/cofre.py`), nunca no projeto.

## Servidor MCP e skill assistente-financeiro

Cada `@mcp.tool()` em `servidor_claude/servidor.py` é uma ferramenta do Claude Desktop; ao criar ou alterar uma, o servidor precisa ser reiniciado. Categorias e cartões são passados por **nome** nas ferramentas (`_id_da_categoria` converte para id).

Ferramentas por assunto:
- Meses e resumo: `listar_meses`, `virar_mes`, `resumo_mes`, `parcelas_futuras`, `assinaturas`.
- Cartões e compras: `listar_cartoes`, `adicionar_cartao`, `listar_compras`, `lancar_compra`, `apagar_compra`.
- Receitas e despesas: `listar_lancamentos`, `adicionar_lancamento`, `apagar_lancamento`.
- Categorias: `listar_categorias`, `adicionar_categoria`, `definir_categoria` (troca só a categoria de um lançamento existente), `gasto_por_categoria`, `definir_renda`.
- Empréstimos: `quanto_me_devem`, `emprestimos_de`, `registrar_pagamento`.
- Caixinhas: `listar_caixinhas`, `definir_caixinha`, `definir_meta_caixinha`.

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

## Fluxo de trabalho

- Branch de trabalho: `Develop` (remoto `origin/Develop`); `master` é a base.
- Mudou regra de negócio: adicione teste em `tests/test_financas.py` (usa SQLite temporário via `criar_banco("teste")`).
- O working tree pode ter alterações do usuário não commitadas: não reverta nem commite sem ele pedir.
