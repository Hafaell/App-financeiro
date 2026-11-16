# Passo a passo: colocar no Vercel

O que **você** (Rafael) faz fora do código. Os passos 1 a 3 podem ser feitos já; o deploy
só vai mostrar algo útil a partir da fase 1 (veja `PLANO.md`).

## 1. Conta e projeto no Vercel

1. Crie a conta em vercel.com entrando **com o GitHub**.
2. *Add New… > Project* e importe o repositório `hafaell/app-financeiro`.
   Se ele não aparecer, autorize o app do Vercel a ver esse repositório no GitHub.
3. Na tela de configuração:
   - **Framework Preset**: `Other` (o `vercel.json` já diz como montar).
   - **Root Directory**: deixe a raiz do repositório.
   - Não clique em Deploy ainda se as variáveis do passo 2 não estiverem prontas.
4. Em *Settings > Git*, defina **Production Branch** como a branch da versão web
   (hoje `claude/sharp-mendel-hff020`; ou `vercel`, se você criar uma com esse nome).
   Assim, enviar código para `Develop` ou `master` **não** mexe no site.
   Outras branches ainda geram *previews*; se não quiser, use *Settings > Git > Ignored Build
   Step* com: `if [ "$VERCEL_GIT_COMMIT_REF" = "vercel" ]; then exit 1; else exit 0; fi`
   (troque `vercel` pelo nome da branch web).

## 2. Variáveis de ambiente (Vercel > Settings > Environment Variables)

| Nome | Valor | Onde achar |
|---|---|---|
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Supabase > Project Settings > API |
| `SUPABASE_CHAVE` | chave **pública** (anon / publishable) | mesmo lugar |
| `VITE_SUPABASE_URL` | igual a `SUPABASE_URL` | (o front só enxerga variáveis com `VITE_`) |
| `VITE_SUPABASE_CHAVE` | igual a `SUPABASE_CHAVE` | |
| `FINANCAS_BANCO` | `postgres` | |
| `TZ` | `America/Sao_Paulo` | para o mês atual não virar errado à noite |

**Nunca** coloque a chave `service_role` / secreta no Vercel: o app não precisa dela, porque
toda leitura e gravação usa o login do próprio usuário (RLS) [Certa].

## 3. Supabase

1. *Authentication > URL Configuration*:
   - **Site URL**: o endereço do site (ex.: `https://app-financeiro.vercel.app`).
   - **Redirect URLs**: o mesmo endereço e `https://*.vercel.app` se quiser login nos previews.
2. Confirme que os scripts `01`, `03`, `05`, `06` e `07` de `supabase/migracoes/` já rodaram
   (o app desktop funcionando com histórico de caixinhas indica que sim).
3. Se a decisão das cópias for tabela ou Storage, rodar o script `08_*.sql` que será criado na fase 2.

## 4. Desenvolver e testar no seu PC (a partir da fase 1)

```
npm i -g vercel          # uma vez
vercel login             # uma vez
vercel link              # liga a pasta ao projeto do Vercel
vercel env pull .env     # baixa as variáveis do passo 2 (o .env já está no .gitignore)
vercel dev               # sobe o site e a API juntos em http://localhost:3000
```

## 5. Publicar

- Enviar commits para a branch de produção publica sozinho.
- Cada pull request para ela gera um link de preview para testar antes.
- Para voltar a uma versão anterior: Vercel > Deployments > (versão boa) > *Promote to Production*.

## 6. O que continua no seu PC

- O app desktop (`ControleFinanceiro.exe`) e a Ayla (servidor MCP) continuam iguais e usam os
  mesmos dados. Lançar algo no site aparece no desktop em ~1 s, e vice-versa.
