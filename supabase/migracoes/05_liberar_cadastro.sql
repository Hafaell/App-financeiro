-- =====================================================================
-- Libera o cadastro de contas pelo app, sem precisar cadastrar o e-mail antes.
-- Os dados continuam separados: cada conta só vê e altera os próprios dados.
-- Recomendado: deixar a confirmação de e-mail ligada (Authentication > Sign In / Providers > Email).
-- =====================================================================

CREATE OR REPLACE FUNCTION public.verificar_cadastro() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    RETURN NEW;  -- qualquer e-mail pode criar conta
END;
$$;
