-- =====================================================================
-- Histórico das caixinhas: cada valor guardado, retirado ou ajustado.
-- Rode no SQL Editor do Supabase, uma vez. Depois, feche e abra o app de novo.
-- Enquanto não rodar, o app funciona normalmente, só sem o histórico.
-- É seguro rodar de novo: não altera nada se a tabela já existir.
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.movimentos_caixinha (
    id BIGSERIAL PRIMARY KEY,
    user_id UUID NOT NULL DEFAULT auth.uid() REFERENCES auth.users(id) ON DELETE CASCADE,
    caixinha_id BIGINT NOT NULL,
    data TEXT NOT NULL,
    valor DOUBLE PRECISION NOT NULL,      -- positivo = guardado, negativo = retirado
    saldo DOUBLE PRECISION NOT NULL,      -- valor da caixinha depois do movimento
    descricao TEXT NOT NULL DEFAULT ''
);
CREATE INDEX IF NOT EXISTS movimentos_caixinha_user ON public.movimentos_caixinha (user_id, caixinha_id);

-- Cada alteração soma 1 na versão do usuário (o app atualiza a tela sozinho)
CREATE OR REPLACE TRIGGER somar_versao AFTER INSERT OR UPDATE OR DELETE ON public.movimentos_caixinha
    FOR EACH ROW EXECUTE FUNCTION public.somar_versao();

-- Cada usuário só enxerga e altera as próprias linhas
ALTER TABLE public.movimentos_caixinha ENABLE ROW LEVEL SECURITY;
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE schemaname = 'public'
                   AND tablename = 'movimentos_caixinha' AND policyname = 'dono_das_linhas') THEN
        CREATE POLICY dono_das_linhas ON public.movimentos_caixinha FOR ALL TO authenticated
            USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());
    END IF;
END;
$$;
REVOKE ALL ON public.movimentos_caixinha FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.movimentos_caixinha TO authenticated;
GRANT USAGE, SELECT ON SEQUENCE public.movimentos_caixinha_id_seq TO authenticated;
