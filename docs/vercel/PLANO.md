# Versão web no Vercel: plano

Este documento descreve como levar o Controle Financeiro (hoje um app desktop em PySide6)
para um site hospedado no Vercel, usando **os mesmos dados do Supabase** e **as mesmas regras
de negócio** do app desktop e da Ayla.

Status: **fase 0 (estrutura e documentação)**. Nada aqui ainda funciona como site.

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
| `requirements.txt` com `PySide6` | **Quebra o deploy** | O Vercel instala o `requirements.txt` da raiz; o PySide6 passa de 250 MB (limite da função). Nesta branch ele terá só as dependências da API. |

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
   - cópia em memória carregada **uma vez por requisição** (um `executar_lote` com todos os
     `SELECT`, uma ida só ao Supabase em vez de 11).
   Assim as consultas continuam rodando na cópia SQLite em memória, exatamente como no desktop,
   e nenhuma linha de SQL de `nucleo/` precisa mudar.
4. **Cópias antes da virada**: `Ferramentas.backup_automatico` hoje grava arquivo. Na web,
   gravar no Supabase Storage (bucket privado `backups`, pasta por `user_id`) ou numa tabela
   `backups` (JSON). Decisão pendente (veja seção 5).

### O que muda em cada camada

| Camada | Mudança |
|---|---|
| `nucleo/` | Nenhuma nas regras. Só `virar_mes` / `backup_automatico` ganham destino alternativo para a cópia. |
| `dados/` | Novo `banco_web.py`. `banco.py` e `nuvem.py` ficam iguais. |
| `seguranca/` | Não usado pela web. |
| `ui/` | Não usado pela web (fica no repositório para o desktop; o `.vercelignore` exclui). |
| `servidor_claude/` | Não muda. |
| Supabase | Adicionar o domínio do Vercel em Authentication > URL Configuration. Talvez um script `08_backups_web.sql`. |

---

## 3. Estrutura da branch

```
App-financeiro/
├── api/
│   └── index.py              # FastAPI (esqueleto; rotas na fase 2)
├── web/                      # frontend React (criado na fase 3)
│   └── README.md
├── src/controle_financeiro/  # mesmo pacote do desktop (nucleo/ é reaproveitado)
├── docs/vercel/              # esta documentação
├── vercel.json               # build do front, rewrites e config da função Python
├── .vercelignore             # deixa de fora ui/, assets/, tests/, instalador...
└── requirements.web.txt      # dependências só da API (vira requirements.txt na fase 1)
```

---

## 4. Fases

### Fase 0: estrutura e documentação (esta)
- [x] Diagnóstico do que roda ou não no Vercel
- [x] Arquitetura e mapa de rotas (`API.md`)
- [x] Passo a passo de deploy (`DEPLOY.md`)
- [x] Esqueleto: `vercel.json`, `.vercelignore`, `api/index.py`, `requirements.web.txt`

### Fase 1: backend mínimo no ar
- [ ] Trocar `requirements.txt` da raiz pelo conteúdo de `requirements.web.txt`
      (sem PySide6 e sem `mcp`) **somente nesta branch**
- [ ] Conferir se o Vercel instala pelo `requirements.txt` ou pelo `pyproject.toml` (que lista
      PySide6). Se usar o `pyproject.toml` [Adivinhando qual tem prioridade], mover o PySide6
      para um extra `desktop` nesta branch
- [ ] Criar `dados/banco_web.py` (`BancoWeb`) + testes em `tests/test_banco_web.py`
      (com um servidor falso, como `tests/test_nuvem.py` já faz)
- [ ] `api/index.py`: `GET /api/saude`, `GET /api/meses`, `GET /api/resumo`
- [ ] Conferir que `config.py` não quebra no Vercel (`LOCALAPPDATA` não existe; cai em `~`, que
      é só leitura). Na web, apontar `PASTA` para `/tmp` por variável de ambiente
- [ ] Primeiro deploy de teste (preview) e chamada com um JWT real

### Fase 2: API completa
- [ ] Todas as rotas de `API.md`, com validação (Pydantic) e erros em português
- [ ] `ValueError` das regras → HTTP 400 com a mensagem; `SessaoExpirada` → 401;
      `ErroConexao` → 503
- [ ] Testes das rotas com `fastapi.testclient` + SQLite (mesmo esquema de `tests/conftest.py`)
- [ ] Cópia antes da virada no Supabase (Storage ou tabela)

### Fase 3: frontend
- [ ] `npm create vite@latest web -- --template react-ts`
- [ ] Login / cadastro (supabase-js), sessão guardada pelo próprio supabase-js
- [ ] Telas na ordem de uso: Visão geral → Transações → Receitas e despesas → Empréstimos →
      Caixinhas → Planejamento → Comparativo → Ferramentas (as mesmas seções do menu do desktop)
- [ ] Tema com os mesmos tokens de `ui/tema.py` (`TINTA`, `PRIMARIA`, `MENTA`, `DESPESA`) e
      fonte Manrope (`assets/fontes/`, licença OFL)
- [ ] Valores em R$ no formato brasileiro (`Intl.NumberFormat('pt-BR', {style:'currency', currency:'BRL'})`)
- [ ] "Desfazer" após apagar: o front guarda a linha apagada por 30 s e chama `POST /api/recolocar`

### Fase 4: produção
- [ ] Domínio, variáveis de ambiente de produção, URL do site no Supabase Auth
- [ ] CI: job extra no `testes.yml` para `npm run build` do `web/`
- [ ] Atualizar README e CLAUDE.md com a existência da versão web

---

## 5. Decisões pendentes (perguntar ao Rafael antes de implementar)

1. **Nome da branch**: hoje o trabalho está em `claude/sharp-mendel-hff020` (branch exigida
   por esta sessão). Se quiser uma branch chamada `vercel`, basta criar a partir desta.
2. **Cópias antes da virada na web**: Supabase Storage (arquivo criptografado, igual ao
   desktop) ou tabela `backups` (mais simples, sem criptografia própria; o RLS isola por usuário).
3. **Importar extrato** e **exportar backup com senha** (`.cfbak`): entram na fase 2/3 ou
   ficam só no desktop?
4. **Cadastro de conta pelo site**: liberado (como no desktop, script `05`) ou só login?
5. **Escopo do celular**: o site precisa de todas as telas ou só consulta + lançar compra?

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
  Definir `TZ=America/Sao_Paulo` nas variáveis de ambiente [Provável que resolva].
- **Branches divergentes**: correções em `nucleo/` feitas na `Develop` precisam ser trazidas
  para esta branch com `git merge Develop` de tempos em tempos.
