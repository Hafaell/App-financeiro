# Apagar em lote (site) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** No site, permitir apagar várias linhas de uma vez (selecionando) ou apagar tudo da lista no mês aberto, em Transações, Despesas e Receitas.

**Architecture:** `Financas.apagar_varios(tabela, ids)` apaga as linhas numa chamada e devolve as linhas apagadas; a API expõe `POST /api/apagar-varios`. No site, um hook/barra de seleção reutilizável (`web/src/componentes/selecao.tsx`) é usado nas três listas; o "Desfazer" de 30 s existente recoloca as linhas com `recolocar`.

**Tech Stack:** Python (FastAPI, pytest, SQLite nos testes), React + TypeScript (Vite).

**Spec:** conversa de 2026-11-17 (sem arquivo de design; resumo na seção Global Constraints).

## Global Constraints

- Só o site (`web/`) e a API/fachada que ele usa. O app desktop (`ui/`) não muda.
- Textos em português do Brasil com acentos; valores no formato brasileiro (`brl`).
- Listas: Transações (`compras`), Despesas (`despesas`), Receitas (`receitas`). Caixinhas e pagamentos de empréstimo ficam de fora.
- **Selecionar:** botão "Selecionar" mostra caixinha em cada linha e "marcar todas"; barra com "N selecionadas · R$ X" e "Apagar selecionadas". No modo seleção, tocar na linha marca/desmarca; fora dele, abre a edição como hoje.
- **Apagar tudo:** apaga todas as linhas da lista no mês aberto, **ignorando a busca por texto**, mas **respeitando o cartão escolhido** (Inter ou Nubank; "Todos" = todos os cartões). Em Despesas/Receitas apaga só a lista daquela aba/coluna. Nunca toca em outras listas nem em outros meses.
- Sempre confirmar com `useConfirmar` mostrando a quantidade e o total em reais.
- Depois de apagar, aviso com "Desfazer" (mesmo mecanismo de `avisar(texto, desfazer)`), que recoloca todas as linhas.
- Mudou rota: atualizar `docs/vercel/API.md`; teste em `tests/test_api.py`.

## Review Focus

- Lista vazia / nenhuma selecionada: botões "Apagar tudo" e "Apagar selecionadas" ficam desativados (não chamam a API).
- `ids` vazio ou com id inexistente na API: não quebra; devolve só o que existia.
- Tabela inválida na API: 400 com mensagem em português (como `/api/lancamentos/outra`).
- Trocar o filtro de cartão ou o mês com itens marcados: a seleção é limpa (não apagar item invisível).
- Desfazer devolve todas as linhas apagadas com os mesmos ids.

---

### Task 1: Fachada e API `apagar_varios`

**Files:**
- Modify: `src/controle_financeiro/nucleo/servico.py` (perto de `apagar_lancamento`, ~linha 154)
- Modify: `src/controle_financeiro/web/api.py` (após `apagar_lancamento`, ~linha 333)
- Modify: `docs/vercel/API.md` (tabela de rotas, junto de `/api/recolocar`)
- Test: `tests/test_api.py`

**Interfaces:**
- Produces: `Financas.apagar_varios(tabela: str, ids: list[int]) -> list[dict]` — `tabela` em `compras|receitas|despesas`; apaga numa só transação e devolve as linhas que existiam (as mesmas que `recolocar` aceita). Tabela inválida → `ValueError("Tabela inválida.")`.
- Produces: `POST /api/apagar-varios` corpo `{"tabela": "compras"|"receitas"|"despesas", "ids": [int]}` → `{"ok": true, "apagadas": [linha, ...]}`.

- [ ] **Step 1: Write the failing tests** em `tests/test_api.py`, usando a fixture `cliente`:
  - `test_apagar_varios_compras_e_desfazer`: lança 3 compras (`/api/compras`), chama `POST /api/apagar-varios` com `{"tabela": "compras", "ids": [a, b]}`; assert `len(resp["apagadas"]) == 2`, `[c["id"] for c in GET /api/compras] == [c]`; recoloca cada linha de `apagadas` via `/api/recolocar` e assert os 3 ids voltaram.
  - `test_apagar_varios_despesas_nao_mexe_em_receitas`: cria 2 despesas e 1 receita; apaga as 2 despesas; assert receita continua em `GET /api/lancamentos/receitas`.
  - `test_apagar_varios_ids_vazios_ou_inexistentes`: `ids: []` e `ids: [9999]` → `apagadas == []`, status 200.
  - `test_apagar_varios_tabela_invalida`: `tabela: "outra"` → 422 ou 400 (o modelo pydantic usa `Literal`, igual a `Recolocar`; assert `status_code in (400, 422)`).
- [ ] **Step 2: Run** `python -m pytest tests/test_api.py -k apagar_varios -v` — Expected: FAIL (404 na rota).
- [ ] **Step 3: Implement** `Financas.apagar_varios` em `servico.py` (usa `self.compras.obter/apagar` ou `self.lancamentos.obter/apagar`, dentro de `self.banco.transacao()` se for o padrão do arquivo) e a rota em `api.py` com modelo `ApagarVarios(BaseModel)`: `tabela: Literal["compras","receitas","despesas"]`, `ids: list[int]`.
- [ ] **Step 4: Run** `python -m pytest tests/test_api.py -v && python -m pyflakes src tests` — Expected: tudo PASS, sem avisos.
- [ ] **Step 5: Docs e commit**: adicionar a linha da rota em `docs/vercel/API.md`.

```bash
git add src tests docs
git commit -m "Apagar várias linhas de uma vez (fachada e API)"
```

---

### Task 2: Componente de seleção e Transações

**Files:**
- Create: `web/src/componentes/selecao.tsx`
- Modify: `web/src/paginas/Transacoes.tsx`
- Modify: `web/src/estilo.css` (junto de `.linha`, ~linha 191)

**Interfaces:**
- Consumes: `POST /api/apagar-varios` (Task 1); `useConfirmar` (`ui.tsx`); `avisar`, `atualizar`, `recolocar` de `lib/estado.tsx`; `brl` de `lib/formato`.
- Produces em `selecao.tsx`:
  - `useSelecao(chaveReset: unknown): { ativo: boolean; ids: Set<number>; alternarModo(): void; alternar(id: number): void; marcarTodas(ids: number[]): void; limpar(): void }` — `ids` e `ativo` zeram quando `chaveReset` muda (mês ou filtro de cartão).
  - `BarraLote({ tabela, rotuloItem, selecao, visiveis, todas }: { tabela: 'compras'|'receitas'|'despesas'; rotuloItem: string; selecao: ReturnType<typeof useSelecao>; visiveis: {id: number; valor: number}[]; todas: {id: number; valor: number}[] })` — renderiza os botões "Selecionar"/"Cancelar", "Marcar todas", "Apagar selecionadas" (sobre `visiveis` marcadas) e "Apagar tudo" (sobre `todas`). Cada apagar abre `useConfirmar` com texto "Apagar N {rotuloItem} (R$ total)? " e, ao confirmar, chama a API, `atualizar()`, `limpar()` e `avisar(..., () => Promise.all(apagadas.map(l => recolocar(tabela, l))))` depois `atualizar()`.
  - `CaixaLinha({ selecao, id }: ...)` — checkbox acessível (`aria-label="Selecionar linha"`) mostrado só quando `selecao.ativo`.

- [ ] **Step 1: Implement `selecao.tsx`** conforme as interfaces acima. Botões desativados quando a lista alvo está vazia.
- [ ] **Step 2: Integrar em `Transacoes.tsx`**: `useSelecao(`${mes}|${cartao}`)`; `todas` = compras do cartão escolhido ignorando `busca` (`(dados ?? []).filter(c => !cartao || c.cartao === cartao)`); `visiveis` = `filtradas`. Em cada `<li>`, o `button.linha` chama `selecao.alternar(c.id)` quando `selecao.ativo`, senão `setEditar(c)`; `CaixaLinha` à esquerda. `BarraLote` entre os filtros e a lista, `rotuloItem="compras"`.
- [ ] **Step 3: CSS** — `.barra-lote` (flex, gap, quebra no celular, fundo `var(--superficie)`), `.caixa-linha` (checkbox 20px, alvo de toque ≥ 40px), linha marcada com fundo `var(--primaria-clara)`. Usar só os tokens existentes de `estilo.css`.
- [ ] **Step 4: Verify** `cd web && npm run build` — Expected: sem erros de tipo. Depois `python -m controle_financeiro.web.local` + `npm run dev:local`, abrir Transações, e conferir: Selecionar → marcar 2 → apagar → aviso com Desfazer → desfazer volta; filtro Inter + "Apagar tudo" não apaga Nubank; busca ativa não restringe "Apagar tudo".
- [ ] **Step 5: Commit**

```bash
git add web docs
git commit -m "Site: selecionar e apagar várias compras ou apagar tudo do cartão"
```

---

### Task 3: Despesas e Receitas

**Files:**
- Modify: `web/src/paginas/ReceitasDespesas.tsx` (componente `Lista`)

**Interfaces:**
- Consumes: `useSelecao`, `BarraLote`, `CaixaLinha` (Task 2).

- [ ] **Step 1: Integrar em `Lista`**: cada lista (despesas e receitas) tem seu próprio `useSelecao(`${mes}|${tabela}`)`; `visiveis` = `todas` = `itens` (valor = `l.valor`); `rotuloItem` = "despesas" / "receitas"; `BarraLote` no cabeçalho da `Secao`; clique na linha alterna a seleção no modo seleção, senão `abrir(l)`.
- [ ] **Step 2: Verify** `cd web && npm run build` e no modo local: apagar tudo em Despesas não altera Receitas e vice-versa; Desfazer recoloca com os mesmos valores.
- [ ] **Step 3: Rodar tudo** `python -m pytest && python -m pyflakes src tests` — Expected: PASS.
- [ ] **Step 4: Commit**

```bash
git add web
git commit -m "Site: apagar em lote em despesas e receitas"
```
