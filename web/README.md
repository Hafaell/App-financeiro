# web/ (frontend da versão Vercel)

Ainda vazio. Na fase 3 (veja `docs/vercel/PLANO.md`) esta pasta recebe o projeto
Vite + React + TypeScript:

```
npm create vite@latest web -- --template react-ts
cd web && npm install @supabase/supabase-js
```

O `vercel.json` da raiz já espera `web/package.json` com o script `build` gerando `web/dist`.
Enquanto a pasta não tiver o projeto, o deploy no Vercel falha no passo de build (esperado).
