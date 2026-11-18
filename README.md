# Controle Financeiro

Site (celular e PC) para controlar cartões, empréstimos feitos com o cartão, receitas, despesas e
caixinhas. Os dados ficam no Supabase, isolados por conta. O Claude (Ayla) acessa os mesmos dados
pelo servidor MCP em `servidor_claude/`.

- Publicar o site: `docs/vercel/DEPLOY.md`. Rotas da API: `docs/vercel/API.md`.
- Banco: `supabase/README.md` (scripts SQL na ordem).
- Arquitetura, comandos e convenções: `CLAUDE.md`.

## Rodar

```
python -m pip install -e ".[claude,dev]"
python -m pytest                                    # SQLite temporário, não toca no Supabase
python -m controle_financeiro.web.local             # API local com dados de exemplo
cd web && npm install && npm run dev:local          # site contra a API local
python -m controle_financeiro.servidor_claude entrar  # login da Ayla (uma vez)
```
