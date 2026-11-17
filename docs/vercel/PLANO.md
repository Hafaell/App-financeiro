# Versão web no Vercel: plano

Este documento descreve como levar o Controle Financeiro (hoje um app desktop em PySide6)
para um site hospedado no Vercel, usando **os mesmos dados do Supabase** e **as mesmas regras
de negócio** do app desktop e da Ayla.

Status: **fases 0 a 3 prontas** na branch `Vercel` (API completa, `BancoWeb`, cópias no Supabase e o site
em `web/`). Falta a fase 4 (publicar): veja `DEPLOY.md`.

Documentos desta pasta:

| Arquivo | Conteúdo |
|---|---|
| `PLANO.md` | Este arquivo: diagnóstico, arquitetura escolhida, fases e checklist |
| `API.md` | Lista das rotas HTTP do backend, uma por método da fachada `Financas` |
| `DEPLOY.md` | Passo a passo do que o Rafael faz no Vercel e no Supabase |

---

## 1. Diagnóstico: o que impede o app de rodar no Vercel hoje

O Vercel hospeda **sites estáticos** (HTML/CSS/JS) e **funções serverless** (pequenos
programas que rodam a cada requisição e somem depois). Ele não roda programas de janela.

| Parte do projeto | Roda no Vercel? | Por quê |
|---|---|---|
| `ui/` (PySide6, Qt) | **Não** | É interface de desktop. Precisa ser refeita em HTML/JS. |
| `nucleo/` (regras: compras, virada, empréstimos...) | **Sim** | Python puro, sem dependência de tela. Roda numa função Python do Vercel. |
| `dados/nuvem.py` (cliente HTTP do Supabase) | **Sim** | Só usa `requests`. |
| `dados/banco.py` → `BancoPostgres` | **Com ajuste** | Grava fila offline e cache em `%LOCALAPPDATA%`. No Vercel o disco é temporário e só `/tmp` aceita escrita. Precisa de uma variante sem arquivos. |
| `seguranca/autenticacao.py` e `cofre.py` | **Não do jeito atual** | Guardam sessão criptografada em arquivo. Na web, a sessão fica no navegador (Supabase Auth). |
| `dados/conexao.py` (token pessoal para achar o projeto) | **Não precisa** | No site, a URL e a chave pública do Supabase vêm de variáveis de ambiente do Vercel. |
| Cópias automáticas antes da virada (`.cfauto` em disco) | **Com ajuste** | Disco do Vercel não guarda nada. Precisa ir para o Supabase (Storage ou tabela). |
| `servidor_claude/` (MCP da Ayla, stdio) | **Fica no PC** | Continua igual. Pode virar MCP remoto no futuro (fora do escopo). |
| `requirements.txt` com `PySide6` | **Quebrava o deploy** | O Vercel instala o `requirements.txt` ou o `pyproject.toml`; o PySide6 é enorme. Resolvido: os dois têm só o da web, e o desktop instala os extras `desktop` e `claude`. |

Ponto a favor [Certa]: o app já fala com o Supabase **só por HTTP** (funções `executar_sql` e
`executar_lote`, com RLS por `user_id`). Ou seja, a parte difícil (banco na nuvem, isolamento
por usuário, login pelo Supabase Auth) já está pronta e serve igual para a web.

---

## 2. Arquitetura escolhida

```
 Navegador (celular / PC)
 ┌─────────────────────────────┐
 │  web/  (Vite + React + TS)  │── login ──► Supabase Auth (supabase-js)
 │  telas: Visão geral, etc.   │
 └──────────────┬──────────────┘
                │ fetch /api/...  (cabeçalho Authorization: Bearer <JWT do usuário>)
                ▼
 Vercel Function (Python)
 ┌─────────────────────────────┐
 │  api/index.py  (FastAPI)    │
 │   └─ Financas (nucleo/)     │  ← mesmas regras do desktop e da Ayla
 │       └─ BancoWeb           │  ← BancoPostgres sem arquivos (novo)
 └──────────────┬──────────────┘
                │ RPC executar_sql / executar_lote (com o JWT do usuário)
                ▼
 Supabase (PostgreSQL + RLS)  ◄──── app desktop e Ayla (MCP) usam os mesmos dados
```

### Por que não reescrever tudo em JavaScript

Alternativa considerada: Next.js falando direto com o Supabase, sem Python.
Descartada porque duplicaria as regras de `nucleo/` (virada de mês, avanço de parcelas,
empréstimos, orçamento) em outra linguagem. Com duas cópias das regras, o site, o desktop e a
Ayla começariam a discordar nos totais. Reaproveitar `nucleo/` mantém **uma só fonte da verdade**.

### Peças

1. **Frontend `web/`**: Vite + React + TypeScript, gerado como site estático (`web/dist`).
   Login com `@supabase/supabase-js` (e-mail e senha, as mesmas contas do desktop).
   Mobile primeiro (o uso principal no site deve ser pelo celular) [Provável].
2. **Backend `api/index.py`**: FastAPI rodando como Vercel Function em Python 3.12.
   Cada requisição:
   1. lê o JWT do cabeçalho `Authorization`;
   2. cria `ClienteSupabase` e chama `usar_token(jwt)`;
   3. cria `Financas(BancoWeb(cliente))`;
   4. chama o método da fachada e devolve JSON.
3. **`BancoWeb`** (novo, em `src/controle_financeiro/dados/banco_web.py`): herda de
   `BancoPostgres` e desliga tudo que mexe em disco:
   - `_salvar_cache` e `_carregar_cache` viram no-op;
   - fila offline só em memória; se o Supabase falhar, a requisição **falha** (sem modo offline:
     o navegador mostra o erro e o usuário tenta de novo);
   - cópia em memória carregada **uma vez por requisição**. O `BancoPostgres._buscar` já baixa
     todas as tabelas num `executar_lote` só (e cai para uma por vez se faltar uma tabela
     opcional), então o `BancoWeb` só reaproveita;
   - `verificar_nas_consultas = False`: a cópia acabou de ser baixada, não precisa conferir
     `meta.versao` a cada leitura (mesma chave que a interface desktop desliga para ler sem rede).
   Assim as consultas continuam rodando na cópia SQLite em memória, exatamente como no desktop,
   e nenhuma linha de SQL de `nucleo/` precisa mudar.
4. **Cópias antes da virada**: `Ferramentas.backup_automatico` hoje grava arquivo. Na web,
   gravar numa tabela `backups` do Supabase (JSON, isolada por usuário pelo RLS). Feito em
   `nucleo/copias.py` (`CopiasNoBanco`); o desktop segue com arquivos (`CopiasEmPasta`).

### O que muda em cada camada

| Camada | Mudança |
|---|---|
| `nucleo/` | Nenhuma nas regras. `virar_mes` e `restaurar_backup` usam `self.copias` (pasta ou tabela); `gerar_backup` devolve o `.cfbak` em bytes. |
| `dados/` | Novo `banco_web.py`. `banco.py` e `nuvem.py` ficam como estão: o lote de SELECTs, a `Session` HTTP reaproveitada e a conferência em segundo plano (`buscar_mudancas` / `aplicar_mudancas`, só do desktop) já servem. |
| `seguranca/` | Não usado pela web. |
| `ui/` | Não usado pela web (fica no repositório para o desktop; o `.vercelignore` exclui). |
| `servidor_claude/` | Não muda. |
| Supabase | Adicionar o domínio do Vercel em Authentication > URL Configuration. Script `08_backups_web.sql` (tabela `backups`). |

---

## 3. Estrutura da branch

```
app-financeiro/
├── api/index.py              # Vercel Function: só importa o app de src/controle_financeiro/web/api.py
├── web/                      # site (Vite + React + TypeScript); npm run build gera web/dist
│   ├── src/paginas/          # uma tela por arquivo, as mesmas do desktop
│   ├── src/componentes/      # estrutura (menu, seletor de mês), formulários e peças de tela
│   ├── src/lib/              # api.ts (fetch com o token), estado.tsx, formato.ts, supabase.ts
│   └── public/fontes/        # Manrope CF (a mesma fonte do desktop)
├── src/controle_financeiro/
│   ├── web/api.py            # rotas FastAPI (uma por método da fachada)
│   ├── web/local.py          # API local com SQLite e dados de exemplo
│   ├── dados/banco_web.py    # BancoPostgres sem disco e sem modo offline
│   └── nucleo/copias.py      # cópias: arquivo (desktop) ou tabela backups (web)
├── supabase/migracoes/08_backups_web.sql
├── docs/vercel/              # esta documentação
├── vercel.json               # build do site, rewrites e config da função Python
├── .vercelignore             # deixa de fora ui/, assets/, tests/, instalador...
├── requirements.txt          # só o da web (o Vercel instala este)
└── requirements.desktop.txt  # app desktop e Ayla (build_exe.bat)
```

---

## 4. Fases

### Fase 0: estrutura e documentação (feita)
- [x] Diagnóstico, arquitetura, mapa de rotas (`API.md`) e passo a passo (`DEPLOY.md`)

### Fase 1: backend mínimo (feita)
- [x] Dependências: o PySide6 e o `mcp` viraram extras (`desktop`, `claude`) no `pyproject.toml`;
      o `requirements.txt` da raiz tem só o da web, e o desktop usa `requirements.desktop.txt`
- [x] `dados/banco_web.py` (`BancoWeb`) + `tests/test_banco_web.py` (abrir = 3 chamadas na primeira
      vez, 1 depois; gravar sem rede falha em vez de ir para a fila; nada em disco)
- [x] `config.py`: `FINANCAS_PASTA` (o `api/index.py` aponta para `/tmp`)

### Fase 2: API completa (feita)
- [x] Todas as rotas de `API.md` em `web/api.py`, com validação (Pydantic) e erros em português
- [x] Testes das rotas em `tests/test_api.py` (`fastapi.testclient` + SQLite)
- [x] Cópia antes da virada na tabela `backups` (`nucleo/copias.py`, script `08_backups_web.sql`);
      o desktop continua com arquivos (`CopiasEmPasta`)

### Fase 3: frontend (feita)
- [x] `web/`: Vite + React + TypeScript, login e cadastro pelo supabase-js
- [x] Todas as telas do desktop: Visão geral, Transações, Receitas e despesas, Planejamento,
      Comparativo, Empréstimos, Caixinhas, Importar extrato e Ferramentas (busca, meses e virada,
      renda, cartões, categorias, cópias, backup com senha, relatório para imprimir/PDF, conta)
- [x] Celular primeiro: barra inferior com botão "Lançar"; no PC, a lateral com as seções do desktop
- [x] Tema com os tokens de `ui/tema.py` e a fonte Manrope CF (`web/public/fontes`, OFL)
- [x] "Desfazer" depois de apagar (30 s), atualização automática quando outro aparelho muda algo
- [x] Modo local com dados de exemplo (`python -m controle_financeiro.web.local` + `npm run dev:local`)
- [x] CI: job `site` no `testes.yml` roda `npm ci && npm run build`

### Fase 4: produção (com você)
- [ ] Rodar `08_backups_web.sql`, criar o projeto no Vercel, variáveis e URL no Supabase (`DEPLOY.md`)
- [ ] Domínio próprio, se quiser

---

## 5. Decisões tomadas

1. **Branch**: `Vercel` (produção do site).
2. **Cópias antes da virada na web**: tabela `backups` no Supabase (JSON, RLS por usuário, 6 por motivo).
3. **Importar extrato, exportar backup com senha e restaurar cópias**: no site também.
4. **Cadastro de conta pelo site**: liberado (login e cadastro).
5. **Escopo**: todas as telas.

---

## 6. Riscos e limites conhecidos

- **Tempo de resposta** [Provável]: cada requisição carrega a cópia inteira do usuário
  (todas as tabelas). Com poucos milhares de linhas é rápido (um `executar_lote`). Se crescer
  muito, filtrar a cópia por mês ou cachear por versão (`meta.versao`).
- **Cold start** [Provável]: a primeira chamada depois de um tempo parado leva 1 a 2 s.
- **Sem modo offline** na web na primeira versão.
- **Limite da função**: 250 MB descompactada. Sem PySide6 a API fica bem abaixo disso [Certa].
- **Fuso horário**: o servidor do Vercel roda em UTC. `mes_do_calendario()` e datas de
  lançamento usam o relógio do servidor; perto da meia-noite do dia 1 o mês pode sair errado.
  Resolvido no `api/index.py` (define `TZ=America/Sao_Paulo` e chama `time.tzset()`), porque o
  Vercel reserva o nome `TZ` nas variáveis de ambiente.
- **Branches divergentes**: correções em `nucleo/` feitas na `Develop` precisam ser trazidas
  para a `Vercel` com `git merge Develop` de tempos em tempos.
