-- =====================================================================
-- Cadastro pelo app, mas só para e-mails autorizados.
-- Sem isso, qualquer pessoa com a chave pública do app poderia criar uma conta no seu projeto.
-- Rode no SQL Editor. Depois, adicione os e-mails (ver a última linha).
-- =====================================================================

CREATE TABLE IF NOT EXISTS public.emails_permitidos (
    email TEXT PRIMARY KEY
);
-- Sem políticas: a API nunca lê nem altera esta lista. Só o SQL Editor mexe nela.
ALTER TABLE public.emails_permitidos ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.emails_permitidos FROM anon, authenticated;

-- Bloqueia a criação de qualquer conta cujo e-mail não esteja na lista.
-- Vale para o cadastro pelo app e também para contas criadas no painel.
CREATE OR REPLACE FUNCTION public.verificar_cadastro() RETURNS trigger
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.emails_permitidos
                   WHERE lower(email) = lower(NEW.email)) THEN
        RAISE EXCEPTION 'Este e-mail não está autorizado a criar conta.';
    END IF;
    RETURN NEW;
END;
$$;
REVOKE ALL ON FUNCTION public.verificar_cadastro() FROM PUBLIC, anon, authenticated;

CREATE OR REPLACE TRIGGER verificar_cadastro
    BEFORE INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.verificar_cadastro();

-- Para autorizar um e-mail, rode (troque pelo e-mail real):
--   INSERT INTO public.emails_permitidos (email) VALUES ('rafael@exemplo.com') ON CONFLICT DO NOTHING;
