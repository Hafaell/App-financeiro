# Banco de dados no Supabase

Rode os scripts de `migracoes/` no SQL Editor do Supabase, **na ordem**:

| Arquivo | O que faz | Quando rodar |
|---|---|---|
| `01_tabelas.sql` | Cria as tabelas, as regras de acesso (cada usuário vê só o que é dele) e a função que prepara a conta | Uma vez |
| `02_migrar_esquema_antigo.sql` | Copia os dados do esquema antigo (`financeiro_<nome>`) para as tabelas novas | Só na migração de dados antigos |
| `03_executar_sql.sql` | Funções que o app usa para ler e gravar (`executar_sql` e `executar_lote`) | Uma vez |
| `04_cadastro_permitido.sql` | Lista de e-mails autorizados (versão antiga do cadastro) | Não é mais necessário |
| `05_liberar_cadastro.sql` | Libera o cadastro de contas pelo app | Uma vez |

A conexão do app com o projeto é feita dentro do próprio app, na primeira abertura,
com o token de acesso pessoal do Supabase (Account > Access Tokens).
