# Banco de dados no Supabase

Rode os scripts de `migracoes/` no SQL Editor do Supabase, **na ordem**:

| Arquivo | O que faz | Quando rodar |
|---|---|---|
| `01_tabelas.sql` | Cria as tabelas, as regras de acesso (cada usuário vê só o que é dele) e a função que prepara a conta | Uma vez |
| `02_migrar_esquema_antigo.sql` | Copia os dados do esquema antigo (`financeiro_<nome>`) para as tabelas novas | Só na migração de dados antigos |
| `03_executar_sql.sql` | Funções que o app usa para ler e gravar (`executar_sql` e `executar_lote`) | Uma vez |
| `04_cadastro_permitido.sql` | Lista de e-mails autorizados (versão antiga do cadastro) | Não é mais necessário |
| `05_liberar_cadastro.sql` | Libera o cadastro de contas pelo app | Uma vez |
| `06_data_lancamento.sql` | Adiciona a coluna com a data em que cada lançamento foi feito | Uma vez, antes de usar a versão com "Lançado em" |
| `07_historico_caixinhas.sql` | Cria o histórico das caixinhas (cada valor guardado, retirado ou ajustado) | Uma vez; depois feche e abra o app. Sem ele, o app funciona, só sem histórico |
| `08_backups_web.sql` | Cria a tabela das cópias de segurança da versão web (antes da virada e antes de restaurar) | Uma vez, antes de usar o site. Sem ele, o site não deixa virar o mês |

O site usa `VITE_SUPABASE_URL` e `VITE_SUPABASE_CHAVE` (veja `docs/vercel/DEPLOY.md`); a Ayla guarda a conexão
com `python -m controle_financeiro.servidor_claude entrar`.
