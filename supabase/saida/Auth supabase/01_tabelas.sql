-- =====================================================================
-- Controle Financeiro, versão 2 (login do Supabase Auth).
-- Todos os usuários usam as mesmas tabelas. Cada linha tem o dono (user_id),
-- e as regras de acesso (RLS) garantem que cada um só vê e altera os próprios dados.
-- Rode no SQL Editor do Supabase, uma vez.
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.cartoes (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    cor TEXT NOT NULL,
    cor_texto TEXT NOT NULL,
    dia_fechamento BIGINT,
    dia_vencimento BIGINT,
    UNIQUE (user_id, nome),
    UNIQUE (user_id, id)
);

CREATE TABLE IF NOT EXISTS public.categorias (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    nome TEXT NOT NULL,
    cor TEXT NOT NULL,
    orcamento DOUBLE PRECISION NOT NULL DEFAULT 0,
    UNIQUE (user_id, nome),
    UNIQUE (user_id, id)
);

CREATE TABLE IF NOT EXISTS public.compras (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    mes TEXT NOT NULL,
    cartao TEXT NOT NULL,
    item TEXT NOT NULL,
    parcelas TEXT NOT NULL DEFAULT '1/1',
    valor_parcela DOUBLE PRECISION NOT NULL,
    emprestimo BIGINT NOT NULL DEFAULT 0,
    pessoa TEXT NOT NULL DEFAULT '.',
    valor_real DOUBLE PRECISION,
    recorrente BIGINT NOT NULL DEFAULT 0,
    categoria_id BIGINT,
    FOREIGN KEY (user_id, categoria_id) REFERENCES public.categorias (user_id, id)
        ON DELETE SET NULL (categoria_id)
);
CREATE INDEX IF NOT EXISTS compras_user_mes ON public.compras (user_id, mes);

CREATE TABLE IF NOT EXISTS public.receitas (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    mes TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL
);
CREATE INDEX IF NOT EXISTS receitas_user_mes ON public.receitas (user_id, mes);

CREATE TABLE IF NOT EXISTS public.despesas (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    mes TEXT NOT NULL,
    descricao TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL,
    recorrente BIGINT NOT NULL DEFAULT 0,
    categoria_id BIGINT,
    FOREIGN KEY (user_id, categoria_id) REFERENCES public.categorias (user_id, id)
        ON DELETE SET NULL (categoria_id)
);
CREATE INDEX IF NOT EXISTS despesas_user_mes ON public.despesas (user_id, mes);

CREATE TABLE IF NOT EXISTS public.caixinhas (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    dono TEXT NOT NULL,
    nome TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL DEFAULT 0,
    meta DOUBLE PRECISION,
    data_alvo TEXT,
    UNIQUE (user_id, dono, nome)
);

CREATE TABLE IF NOT EXISTS public.pagamentos (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    pessoa TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL,
    data TEXT NOT NULL,
    descricao TEXT NOT NULL DEFAULT '',
    mes TEXT
);
CREATE INDEX IF NOT EXISTS pagamentos_user_mes ON public.pagamentos (user_id, mes);

CREATE TABLE IF NOT EXISTS public.rendas (
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    mes TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL,
    PRIMARY KEY (user_id, mes)
);

CREATE TABLE IF NOT EXISTS public.sessoes (
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    mes TEXT NOT NULL,
    PRIMARY KEY (user_id, mes)
);

-- Versão dos dados de cada usuário (o app confere a cada segundo para atualizar a tela)
CREATE TABLE IF NOT EXISTS public.meta (
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    chave TEXT NOT NULL,
    valor BIGINT NOT NULL,
    PRIMARY KEY (user_id, chave)
);

-- ---------------------------------------------------------------------
-- Cada alteração em uma tabela de dados soma 1 na versão do usuário.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.somar_versao() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    INSERT INTO public.meta (user_id, chave, valor)
    VALUES (COALESCE(NEW.user_id, OLD.user_id), 'versao', 1)
    ON CONFLICT (user_id, chave) DO UPDATE SET valor = public.meta.valor + 1;
    RETURN NULL;
END;
$$;

DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['cartoes', 'categorias', 'compras', 'receitas', 'despesas',
                             'caixinhas', 'pagamentos', 'rendas', 'sessoes'] LOOP
        EXECUTE format('CREATE OR REPLACE TRIGGER somar_versao AFTER INSERT OR UPDATE OR DELETE ON public.%I '
                       'FOR EACH ROW EXECUTE FUNCTION public.somar_versao()', t);
    END LOOP;
END;
$$;

-- ---------------------------------------------------------------------
-- Regras de acesso: cada usuário só enxerga e altera as próprias linhas.
-- ---------------------------------------------------------------------
DO $$
DECLARE t TEXT;
BEGIN
    FOREACH t IN ARRAY ARRAY['cartoes', 'categorias', 'compras', 'receitas', 'despesas',
                             'caixinhas', 'pagamentos', 'rendas', 'sessoes', 'meta'] LOOP
        EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', t);
        IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                       AND tablename = t AND policyname = 'dono_das_linhas') THEN
            EXECUTE format('CREATE POLICY dono_das_linhas ON public.%I FOR ALL TO authenticated '
                           'USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid())', t);
        END IF;
        EXECUTE format('REVOKE ALL ON public.%I FROM anon', t);
        EXECUTE format('GRANT SELECT, INSERT, UPDATE, DELETE ON public.%I TO authenticated', t);
    END LOOP;
END;
$$;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ---------------------------------------------------------------------
-- Chamada pelo app logo após o login: cria os dados iniciais do usuário, se ainda não existirem.
-- ---------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.preparar_usuario() RETURNS void
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public AS $$
BEGIN
    -- Só na primeira vez: se o usuário apagar um cartão ou categoria, ela não volta.
    IF EXISTS (SELECT 1 FROM public.meta WHERE user_id = auth.uid() AND chave = 'versao') THEN
        RETURN;
    END IF;
    INSERT INTO public.meta (user_id, chave, valor) VALUES (auth.uid(), 'versao', 0);
    INSERT INTO public.cartoes (nome, cor, cor_texto) VALUES
        ('Inter', '#F89A3D', '#2B1600'), ('Nubank', '#7B4FD0', '#FFFFFF');
    INSERT INTO public.categorias (nome, cor) VALUES
        ('Alimentação', '#F59E0B'), ('Transporte', '#3B82F6'), ('Assinaturas', '#8B5CF6'),
        ('Saúde', '#10B981'), ('Lazer', '#EC4899'), ('Outros', '#6B7280');
END;
$$;
GRANT EXECUTE ON FUNCTION public.preparar_usuario() TO authenticated;
