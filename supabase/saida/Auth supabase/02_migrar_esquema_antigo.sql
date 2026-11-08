-- =====================================================================
-- Copia os dados do esquema antigo (financeiro_<usuario>) para as tabelas novas,
-- com o dono (user_id) do usuário do Supabase Auth.
-- Rode DEPOIS de 01_tabelas.sql e de criar o usuário no Supabase (Authentication > Users).
-- Uso (no SQL Editor, trocando o nome e o id):
--   SELECT public.migrar_esquema_antigo('financeiro_rafael', 'ID-DO-USUARIO-NO-AUTH');
-- Não pode ser chamada pelo app: a permissão é retirada no fim do arquivo.
-- =====================================================================

CREATE OR REPLACE FUNCTION public.migrar_esquema_antigo(origem TEXT, uid UUID) RETURNS TEXT
LANGUAGE plpgsql SET search_path = public AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM public.compras WHERE user_id = uid)
       OR EXISTS (SELECT 1 FROM public.despesas WHERE user_id = uid) THEN
        RAISE EXCEPTION 'Este usuário já tem dados nas tabelas novas. Nada foi copiado.';
    END IF;

    EXECUTE format('INSERT INTO public.cartoes (user_id, nome, cor, cor_texto, dia_fechamento, dia_vencimento) '
                   'SELECT %1$L, nome, cor, cor_texto, dia_fechamento, dia_vencimento FROM %2$I.cartoes '
                   'ON CONFLICT (user_id, nome) DO NOTHING', uid, origem);

    EXECUTE format('INSERT INTO public.categorias (user_id, nome, cor, orcamento) '
                   'SELECT %1$L, nome, cor, orcamento FROM %2$I.categorias '
                   'ON CONFLICT (user_id, nome) DO NOTHING', uid, origem);

    -- Lançamentos guardam a categoria pelo id; aqui ela é trocada pelo id novo (mesmo nome).
    EXECUTE format('INSERT INTO public.compras (user_id, mes, cartao, item, parcelas, valor_parcela, '
                   'emprestimo, pessoa, valor_real, recorrente, categoria_id) '
                   'SELECT %1$L, c.mes, c.cartao, c.item, c.parcelas, c.valor_parcela, c.emprestimo, '
                   'c.pessoa, c.valor_real, c.recorrente, nova.id '
                   'FROM %2$I.compras c '
                   'LEFT JOIN %2$I.categorias oc ON oc.id = c.categoria_id '
                   'LEFT JOIN public.categorias nova ON nova.user_id = %1$L AND nova.nome = oc.nome '
                   'ORDER BY c.id', uid, origem);

    EXECUTE format('INSERT INTO public.despesas (user_id, mes, descricao, valor, recorrente, categoria_id) '
                   'SELECT %1$L, d.mes, d.descricao, d.valor, d.recorrente, nova.id '
                   'FROM %2$I.despesas d '
                   'LEFT JOIN %2$I.categorias oc ON oc.id = d.categoria_id '
                   'LEFT JOIN public.categorias nova ON nova.user_id = %1$L AND nova.nome = oc.nome '
                   'ORDER BY d.id', uid, origem);

    EXECUTE format('INSERT INTO public.receitas (user_id, mes, descricao, valor) '
                   'SELECT %1$L, mes, descricao, valor FROM %2$I.receitas ORDER BY id', uid, origem);

    EXECUTE format('INSERT INTO public.caixinhas (user_id, dono, nome, valor, meta, data_alvo) '
                   'SELECT %1$L, dono, nome, valor, meta, data_alvo FROM %2$I.caixinhas '
                   'ON CONFLICT (user_id, dono, nome) DO NOTHING', uid, origem);

    EXECUTE format('INSERT INTO public.pagamentos (user_id, pessoa, valor, data, descricao, mes) '
                   'SELECT %1$L, pessoa, valor, data, descricao, mes FROM %2$I.pagamentos ORDER BY id',
                   uid, origem);

    EXECUTE format('INSERT INTO public.rendas (user_id, mes, valor) '
                   'SELECT %1$L, mes, valor FROM %2$I.rendas ON CONFLICT (user_id, mes) DO NOTHING',
                   uid, origem);

    EXECUTE format('INSERT INTO public.sessoes (user_id, mes) '
                   'SELECT %1$L, mes FROM %2$I.sessoes ON CONFLICT (user_id, mes) DO NOTHING',
                   uid, origem);

    -- Versão inicial do usuário (o app compara esse número para atualizar a tela)
    INSERT INTO public.meta (user_id, chave, valor) VALUES (uid, 'versao', 0)
        ON CONFLICT (user_id, chave) DO NOTHING;

    RETURN 'Dados copiados para o usuário ' || uid::TEXT || ' a partir de ' || origem;
END;
$$;

-- Só quem administra o banco (SQL Editor) pode usar esta função.
REVOKE ALL ON FUNCTION public.migrar_esquema_antigo(TEXT, UUID) FROM PUBLIC, anon, authenticated;
