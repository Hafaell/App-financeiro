-- =====================================================================
-- Funções que o app chama para executar SQL no Supabase.
-- Rodam com as permissões do próprio usuário logado (SECURITY INVOKER),
-- então as regras de acesso (RLS) continuam valendo: cada um só altera as próprias linhas.
-- Só aceitam um comando por vez, e os valores são sempre tratados como texto literal.
-- Parâmetros: no SQL use %s no lugar de cada valor, e passe a lista em JSON, ex.: '["2026-11", 1]'.
-- =====================================================================

-- Monta o SQL final trocando cada %s pelo valor (já escapado).
CREATE OR REPLACE FUNCTION public.montar_sql(consulta TEXT, parametros JSONB) RETURNS TEXT
LANGUAGE plpgsql IMMUTABLE SET search_path = public AS $$
DECLARE
    partes TEXT[];
    saida TEXT := '';
    i INTEGER;
    valor JSONB;
    literal TEXT;
BEGIN
    IF parametros IS NULL OR jsonb_typeof(parametros) <> 'array' THEN
        RAISE EXCEPTION 'Os parâmetros precisam ser uma lista JSON.';
    END IF;
    -- Um comando só: aceita ';' apenas no fim
    IF position(';' IN regexp_replace(consulta, ';\s*$', '')) > 0 THEN
        RAISE EXCEPTION 'Envie um comando por vez.';
    END IF;

    partes := string_to_array(consulta, '%s');
    IF array_length(partes, 1) - 1 <> jsonb_array_length(parametros) THEN
        RAISE EXCEPTION 'A quantidade de valores não bate com a quantidade de marcadores do comando.';
    END IF;

    FOR i IN 1 .. array_length(partes, 1) LOOP
        saida := saida || partes[i];
        IF i <= jsonb_array_length(parametros) THEN
            valor := parametros -> (i - 1);
            IF jsonb_typeof(valor) = 'null' THEN
                literal := 'NULL';
            ELSE
                literal := quote_literal(valor #>> '{}');
            END IF;
            saida := saida || literal;
        END IF;
    END LOOP;
    RETURN saida;
END;
$$;

-- Executa um comando.
--   SELECT / WITH  -> {"linhas": [ {...}, {...} ]}
--   INSERT/UPDATE/DELETE -> {"id": <id do RETURNING id, se houver>, "afetadas": <nº de linhas>}
CREATE OR REPLACE FUNCTION public.executar_sql(consulta TEXT, parametros JSONB DEFAULT '[]'::jsonb)
RETURNS JSONB LANGUAGE plpgsql SECURITY INVOKER SET search_path = public AS $$
DECLARE
    sql_final TEXT := public.montar_sql(consulta, parametros);
    tipo TEXT := upper(ltrim(consulta));
    linhas JSONB;
    id_novo BIGINT;
    afetadas BIGINT;
BEGIN
    IF tipo LIKE 'SELECT%' OR tipo LIKE 'WITH%' THEN
        EXECUTE format('SELECT COALESCE(jsonb_agg(t), ''[]''::jsonb) FROM (%s) t', sql_final)
            INTO linhas;
        RETURN jsonb_build_object('linhas', linhas);
    END IF;

    IF upper(consulta) LIKE '%RETURNING ID%' THEN
        EXECUTE sql_final INTO id_novo;
    ELSE
        EXECUTE sql_final;
    END IF;
    GET DIAGNOSTICS afetadas = ROW_COUNT;
    RETURN jsonb_build_object('id', id_novo, 'afetadas', afetadas);
END;
$$;

-- Executa vários comandos numa só transação: se um falhar, nada é gravado.
-- Entrada: [ {"sql": "...", "params": [...]}, ... ]   Saída: lista com o resultado de cada um.
CREATE OR REPLACE FUNCTION public.executar_lote(comandos JSONB) RETURNS JSONB
LANGUAGE plpgsql SECURITY INVOKER SET search_path = public AS $$
DECLARE
    item JSONB;
    saida JSONB := '[]'::jsonb;
BEGIN
    IF jsonb_typeof(comandos) <> 'array' THEN
        RAISE EXCEPTION 'O lote precisa ser uma lista de comandos.';
    END IF;
    FOR item IN SELECT value FROM jsonb_array_elements(comandos) LOOP
        saida := saida || jsonb_build_array(
            public.executar_sql(item ->> 'sql', COALESCE(item -> 'params', '[]'::jsonb)));
    END LOOP;
    RETURN saida;
END;
$$;

-- Permissões: só usuários logados podem usar; anônimos não.
REVOKE ALL ON FUNCTION public.montar_sql(TEXT, JSONB) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.executar_sql(TEXT, JSONB) FROM PUBLIC, anon;
REVOKE ALL ON FUNCTION public.executar_lote(JSONB) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.montar_sql(TEXT, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION public.executar_sql(TEXT, JSONB) TO authenticated;
GRANT EXECUTE ON FUNCTION public.executar_lote(JSONB) TO authenticated;
