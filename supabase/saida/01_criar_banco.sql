CREATE SCHEMA IF NOT EXISTS "financeiro_rafael";
SET search_path TO "financeiro_rafael";

CREATE TABLE IF NOT EXISTS compras (
        id BIGSERIAL PRIMARY KEY,
        mes TEXT NOT NULL,
        cartao TEXT NOT NULL,
        item TEXT NOT NULL,
        parcelas TEXT NOT NULL DEFAULT '1/1',
        valor_parcela DOUBLE PRECISION NOT NULL,
        emprestimo INTEGER NOT NULL DEFAULT 0,
        pessoa TEXT NOT NULL DEFAULT '.',
        valor_real DOUBLE PRECISION,
        recorrente INTEGER NOT NULL DEFAULT 0
    );
CREATE TABLE IF NOT EXISTS receitas (
        id BIGSERIAL PRIMARY KEY,
        mes TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL
    );
CREATE TABLE IF NOT EXISTS despesas (
        id BIGSERIAL PRIMARY KEY,
        mes TEXT NOT NULL,
        descricao TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL,
        recorrente INTEGER NOT NULL DEFAULT 0
    );
CREATE TABLE IF NOT EXISTS caixinhas (
        id BIGSERIAL PRIMARY KEY,
        dono TEXT NOT NULL,
        nome TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL DEFAULT 0,
        UNIQUE (dono, nome)
    );
CREATE TABLE IF NOT EXISTS pagamentos (
        id BIGSERIAL PRIMARY KEY,
        pessoa TEXT NOT NULL,
        valor DOUBLE PRECISION NOT NULL,
        data TEXT NOT NULL,
        descricao TEXT NOT NULL DEFAULT '',
        mes TEXT
    );
CREATE TABLE IF NOT EXISTS cartoes (
        id BIGSERIAL PRIMARY KEY,
        nome TEXT NOT NULL UNIQUE,
        cor TEXT NOT NULL,
        cor_texto TEXT NOT NULL
    );
CREATE TABLE IF NOT EXISTS sessoes (
        mes TEXT PRIMARY KEY
    );
CREATE TABLE IF NOT EXISTS meta (
        chave TEXT PRIMARY KEY,
        valor INTEGER NOT NULL
    );
INSERT INTO meta (chave, valor) VALUES ('versao', 0) ON CONFLICT DO NOTHING;
INSERT INTO cartoes (nome, cor, cor_texto) VALUES ('Inter', '#F89A3D', '#2B1600') ON CONFLICT DO NOTHING;
INSERT INTO cartoes (nome, cor, cor_texto) VALUES ('Nubank', '#7B4FD0', '#FFFFFF') ON CONFLICT DO NOTHING;
ALTER TABLE "financeiro_rafael"."compras" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."receitas" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."despesas" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."caixinhas" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."pagamentos" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."cartoes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."sessoes" ENABLE ROW LEVEL SECURITY;
ALTER TABLE "financeiro_rafael"."meta" ENABLE ROW LEVEL SECURITY;
