# Supabase — passo a passo

Estes arquivos levam os seus dados para o Supabase (PostgreSQL na nuvem, plano gratuito).
Depois de configurado, o app e o Claude passam a usar a nuvem. Seu banco local continua
como cópia de segurança.

## 1. Criar o projeto no Supabase

1. Entre em supabase.com e crie uma conta gratuita.
2. Crie um **New project**. Anote a senha do banco (você vai precisar dela).
3. Espere o projeto terminar de ser criado.

## 2. Pegar a URI de conexão

1. No projeto, vá em **Connect** (ou Project Settings > Database).
2. Copie a **Connection string** no modo **URI**. Ela começa com `postgresql://`.
3. Troque `[YOUR-PASSWORD]` pela senha do banco.

## 3. Criar as tabelas

1. No projeto, abra **SQL Editor** > **New query**.
2. Abra o arquivo `supabase/saida/01_criar_banco.sql`, copie tudo e cole.
3. Clique em **Run**. Deve aparecer "Success".

## 4. Enviar os seus dados

No computador, na pasta do projeto, rode:

    python supabase/gerar_sql.py Rafael

Isso cria `supabase/saida/02_dados.sql` com os seus lançamentos. Depois, no SQL Editor,
cole o conteúdo desse arquivo e clique em **Run**.

## 5. Guardar a conexão no app

Na pasta do projeto, rode:

    python supabase/configurar_conexao.py

Cole a URI (com a senha) quando pedir. A tela não mostra o que você digita. O app guarda
a conexão **criptografada**, em `%LOCALAPPDATA%\ControleFinanceiro\conexao.dat`.

## 6. Conferir

Abra o app. Os valores de novembro devem ser os mesmos de antes:
saldo -R$ 167,13 e meu cartão R$ 1.545,13.

## Para voltar ao banco local

Apague o arquivo `conexao.dat` (ou renomeie). O app volta a usar o arquivo local.

## Segurança

- O arquivo `01_criar_banco.sql` e o `02_dados.sql` contêm dados pessoais. Não envie para
  ninguém nem publique.
- As tabelas têm **Row Level Security** ligado. A API pública do Supabase não enxerga os
  dados. Só a conexão feita pelo app acessa.
- Não cole a senha do banco em conversas ou arquivos do projeto.
- Se a senha vazar, troque em Project Settings > Database e rode `configurar_conexao.py` de novo.

## Limites do plano gratuito

Projetos gratuitos podem pausar depois de um tempo sem uso. Se o app avisar que não
conseguiu conectar, abra o painel do Supabase e clique em **Restore**.
