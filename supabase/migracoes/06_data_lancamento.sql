-- =====================================================================
-- Data em que cada lançamento foi feito (compras, receitas e despesas).
-- Rode no SQL Editor do Supabase, uma vez, ANTES de usar a versão do app que mostra "Lançado em".
-- Lançamentos antigos ficam sem data (o app mostra "—").
-- É seguro rodar de novo: não altera nada se a coluna já existir.
-- =====================================================================

ALTER TABLE public.compras  ADD COLUMN IF NOT EXISTS data_lancamento TEXT;
ALTER TABLE public.receitas ADD COLUMN IF NOT EXISTS data_lancamento TEXT;
ALTER TABLE public.despesas ADD COLUMN IF NOT EXISTS data_lancamento TEXT;
