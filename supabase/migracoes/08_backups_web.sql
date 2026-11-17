-- =====================================================================
-- Cópias de segurança da versão web (site no Vercel).
-- O site salva aqui todos os dados antes de virar o mês e antes de restaurar uma cópia
-- (o app desktop continua salvando em arquivo no PC). Guarda as 6 mais novas de cada tipo.
-- Rode no SQL Editor do Supabase, uma vez. É seguro rodar de novo.
-- Enquanto não rodar, o site funciona, mas não deixa virar o mês (a cópia falharia).
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.backups (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    criado_em TEXT NOT NULL,              -- data e hora (AAAA-MM-DDTHH:MM:SS)
    motivo TEXT NOT NULL,                 -- antes-da-virada / antes-de-restaurar
    detalhe TEXT NOT NULL DEFAULT '',     -- mês virado, quando houver
    dados TEXT NOT NULL                   -- todas as tabelas do usuário, em JSON
);
CREATE INDEX IF NOT EXISTS backups_user ON public.backups (user_id, motivo, id);

-- Sem gatilho de versão: salvar uma cópia não muda os dados, então o app não precisa recarregar.

-- Cada usuário só enxerga e altera as próprias cópias
ALTER TABLE public.backups ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'backups' AND policyname = 'dono_das_linhas') THEN
        CREATE POLICY dono_das_linhas ON public.backups FOR ALL TO authenticated
            USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
    END IF;
END;
$$;
REVOKE ALL ON public.backups FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.backups TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.backups_id_seq TO authenticated;
