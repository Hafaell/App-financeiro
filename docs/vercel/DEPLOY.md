# Passo a passo: colocar no Vercel

O que **você** (Rafael) faz fora do código. O código da branch `Vercel` já está pronto para isso.

## 1. Supabase: rodar o script novo

No SQL Editor do Supabase, rode `supabase/migracoes/08_backups_web.sql` (uma vez). Ele cria a
tabela das cópias de segurança que o site salva antes de virar o mês. Sem ele o site funciona,
mas não deixa virar o mês (a cópia falharia e, por segurança, o mês não vira).

Confira também se os scripts `01`, `03`, `05`, `06` e `07` já rodaram (o app desktop funcionando
com histórico de caixinhas indica que sim). O `05` é o que libera o cadastro de contas novas.

## 2. Conta e projeto no Vercel

1. Crie a conta em vercel.com entrando **com o GitHub**.
2. *Add New… > Project* e importe o repositório `hafaell/app-financeiro`.
   Se ele não aparecer, autorize o app do Vercel a ver esse repositório no GitHub.
3. Na tela de configuração:
   - **Framework Preset**: `Other` (o `vercel.json` já diz como montar).
   - **Root Directory**: deixe a raiz do repositório.
   - Abra **Environment Variables** e cadastre as do passo 3 **antes** de clicar em Deploy.
4. Depois de criado, em *Settings > Git*, defina **Production Branch** como `Vercel`.
   Assim, enviar código para `Develop` ou `master` **não** mexe no site.
   As outras branches ainda geram *previews*; se não quiser, use *Settings > Git > Ignored Build
   Step* com: `if [ "$VERCEL_GIT_COMMIT_REF" = "Vercel" ]; then exit 1; else exit 0; fi`

## 3. Variáveis de ambiente (Vercel > Settings > Environment Variables)

| Nome | Valor | Onde achar |
|---|---|---|
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Supabase > Project Settings > API |
| `SUPABASE_CHAVE` | chave **pública** (anon / publishable) | mesmo lugar |
| `VITE_SUPABASE_URL` | igual a `SUPABASE_URL` | (o site só enxerga variáveis com `VITE_`) |
| `VITE_SUPABASE_CHAVE` | igual a `SUPABASE_CHAVE` | |

O fuso de São Paulo é definido no `api/index.py` (o Vercel não deixa cadastrar `TZ`, nome
reservado); para outro fuso, use a variável `FINANCAS_FUSO`.

**Nunca** coloque a chave `service_role` / secreta no Vercel: o site não precisa dela, porque
toda leitura e gravação usa o login do próprio usuário (RLS).

As variáveis `VITE_` entram no site na hora do build: se mudar alguma, faça *Redeploy*.

## 4. Supabase: endereço do site (login e cadastro)

Depois do primeiro deploy, em *Authentication > URL Configuration*:
- **Site URL**: o endereço do site (ex.: `https://app-financeiro.vercel.app`).
- **Redirect URLs**: o mesmo endereço, e `https://*.vercel.app` se quiser login nos previews.

O link do e-mail de confirmação de cadastro leva para a **Site URL**. Se a confirmação de e-mail
estiver desligada (*Authentication > Providers > Email > Confirm email*), a conta nova já entra
direto.

## 5. Testar

1. Abra `https://<seu-site>/api/saude`: deve responder `{"ok":true,"fuso":"-03 -0300"}` (a API está no ar,
   no fuso de São Paulo).
2. Abra o site e entre com o e-mail e a senha do app desktop.
3. Lance algo no site e veja aparecer no desktop (e vice-versa).

Se a tela disser "Falta configurar o site", faltam as variáveis `VITE_` (passo 3) ou o redeploy.
Se o login funcionar mas os dados não abrirem, confira `SUPABASE_URL` e `SUPABASE_CHAVE` e veja
o erro em *Vercel > Deployments > (o deploy) > Functions / Logs*.

## 6. Publicar mudanças

- Enviar commits para a branch `Vercel` publica sozinho.
- Para trazer correções da `Develop`: `git checkout Vercel && git merge Develop && git push`.
- Para voltar a uma versão anterior: Vercel > Deployments > (versão boa) > *Promote to Production*.

## 7. Rodar no seu PC

Sem Supabase, com dados de exemplo (bom para mexer no visual):

```
python -m pip install -e ".[dev]"
python -m controle_financeiro.web.local            # API em http://127.0.0.1:8000
cd web && npm install
npm run dev:local                                  # site em http://localhost:5173
```

Com os seus dados reais (cuidado: grava de verdade):

```
npm i -g vercel && vercel login && vercel link     # uma vez
vercel env pull web/.env.local                     # baixa as variáveis do passo 3
vercel dev                                         # site e API juntos em http://localhost:3000
```

## 8. O que continua no seu PC

O app desktop (`ControleFinanceiro.exe`) e a Ayla (servidor MCP) continuam iguais e usam os
mesmos dados. Lançar algo no site aparece no desktop em ~1 s; o site confere mudanças de fora a
cada 15 s (e ao voltar para a aba).

As cópias antes da virada ficam em lugares diferentes: o desktop salva em arquivo no PC
(Ferramentas > Cópias automáticas do app) e o site salva na tabela `backups` do Supabase
(Ferramentas > Cópias automáticas do site).
