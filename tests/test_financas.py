"""Regras do app com banco SQLite local (mesmas regras do Supabase)."""
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.dados.banco import criar_banco


def _app():
    return Financas(criar_banco("teste"))


def test_compra_propria_entra_no_meu_cartao():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    app.lancar_compra(cartao, "Mercado", "R$ 100,00", parcelas="", pessoa=".")
    resumo = app.resumo_mes()
    assert resumo["meu_cartao_total"] >= 100.0


def test_compra_com_pessoa_vira_emprestimo_e_nao_entra_no_meu_cartao():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    antes = app.resumo_mes()
    app.lancar_compra(cartao, "Presente", "R$ 50,00", parcelas="", pessoa="Pai")
    depois = app.resumo_mes()
    assert depois["meu_cartao_total"] == antes["meu_cartao_total"]
    assert depois["cartoes_com_emprestimos_total"] >= antes["cartoes_com_emprestimos_total"] + 50.0


def test_lancamentos_guardam_a_data_do_dia_e_a_virada_mantem():
    from datetime import date
    app = _app()
    hoje = date.today().isoformat()
    cartao = app.listar_cartoes()[0]["nome"]
    cid = app.lancar_compra(cartao, "Cinema", "R$ 40,00", parcelas="1/3", pessoa=".")
    rid = app.adicionar_lancamento("receitas", "Salário teste", "R$ 100,00")
    did = app.adicionar_lancamento("despesas", "Luz teste", "R$ 50,00", recorrente=True)
    assert app.obter_compra(cid)["data_lancamento"] == hoje
    assert app.obter_lancamento("receitas", rid)["data_lancamento"] == hoje
    assert app.obter_lancamento("despesas", did)["data_lancamento"] == hoje
    app.virar_mes()
    novas = [c for c in app.listar_compras() if c["item"] == "Cinema"]
    assert novas and novas[0]["data_lancamento"] == hoje


def test_classificar_troca_so_a_categoria_sem_recriar():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Mercado", "R$ 100,00", parcelas="", pessoa=".")
    cat = app.listar_categorias()[0]["id"]
    assert app.classificar("compras", id_, cat)
    compra = app.obter_compra(id_)
    assert compra["id"] == id_ and compra["categoria_id"] == cat and compra["item"] == "Mercado"
    app.classificar("compras", id_, None)
    assert app.obter_compra(id_)["categoria_id"] is None


# ----- virada de mês: uma regra por teste -----

def _virada(tmp_path, compras=(), despesas=(), receitas=()):
    """Lança os itens no mês atual, vira o mês e devolve (app, origem, novo, resultado).
    Cada item ganha um nome único, porque o banco de teste é compartilhado entre os testes."""
    import uuid
    app = Financas(criar_banco("teste"), pasta_backups=tmp_path)
    marca = uuid.uuid4().hex[:6]
    cartao = app.listar_cartoes()[0]["nome"]
    for nome, parcelas, extra in compras:
        app.lancar_compra(cartao, f"{nome} {marca}", "R$ 10,00", parcelas=parcelas, **extra)
    for nome, extra in despesas:
        app.adicionar_lancamento("despesas", f"{nome} {marca}", "R$ 20,00", **extra)
    for nome in receitas:
        app.adicionar_lancamento("receitas", f"{nome} {marca}", "R$ 30,00")
    origem = app.mes_ativo()
    r = app.virar_mes()
    return app, origem, r["novo"], r, marca


def _compras_do(app, mes, marca):
    return {c["item"].rsplit(" ", 1)[0]: c for c in app.listar_compras(mes=mes) if c["item"].endswith(marca)}


def _despesas_do(app, mes, marca):
    return {d["descricao"].replace(f" {marca}", ""): d for d in app.listar_lancamentos("despesas", mes)
            if marca in d["descricao"]}


def test_virada_avanca_parcela_e_mantem_o_resto_da_compra(tmp_path):
    app, origem, novo, r, marca = _virada(tmp_path, compras=[
        ("Notebook", "3/12", {"pessoa": "Pai", "categoria_id": None})])
    nova = _compras_do(app, novo, marca)["Notebook"]
    assert nova["parcelas"] == "4/12"
    assert nova["pessoa"] == "Pai" and nova["valor_parcela"] == 10.0
    assert _compras_do(app, origem, marca)["Notebook"]["parcelas"] == "3/12"  # o mês de origem não muda


def test_virada_tira_ultima_parcela_e_compra_a_vista(tmp_path):
    app, _, novo, r, marca = _virada(tmp_path, compras=[
        ("Geladeira", "12/12", {}), ("Mercado", "", {})])
    assert _compras_do(app, novo, marca) == {}
    removidos = {item for item, _ in r["removidas"]}
    assert {f"Geladeira {marca}", f"Mercado {marca}"} <= removidos


def test_virada_mantem_recorrente_sem_avancar_parcela(tmp_path):
    app, _, novo, _, marca = _virada(tmp_path, compras=[
        ("Spotify", "", {"recorrente": True}), ("Academia", "2/6", {"recorrente": True})])
    novas = _compras_do(app, novo, marca)
    assert novas["Spotify"]["parcelas"] == "1/1" and novas["Spotify"]["recorrente"]
    assert novas["Academia"]["parcelas"] == "2/6"


def test_virada_de_despesas(tmp_path):
    app, _, novo, _, marca = _virada(tmp_path, despesas=[
        ("Aluguel", {"recorrente": True}), ("Feira", {}), ("Dentista (2/5)", {})])
    novas = _despesas_do(app, novo, marca)
    assert set(novas) == {"Aluguel", "Dentista (3/5)"}  # recorrente fica, avulsa sai, parcela avança
    assert novas["Aluguel"]["recorrente"]


def test_virada_copia_receitas_e_nao_mexe_nas_caixinhas(tmp_path):
    import uuid
    app = Financas(criar_banco("teste"), pasta_backups=tmp_path)
    caixa = f"Viagem {uuid.uuid4().hex[:6]}"
    app.definir_caixinha("Rafael", caixa, "R$ 500,00")
    antes = [c for c in app.listar_caixinhas() if c["nome"] == caixa]
    app, _, novo, _, marca = _virada(tmp_path, receitas=["Salário"])
    receitas = [x for x in app.listar_lancamentos("receitas", novo) if x["descricao"] == f"Salário {marca}"]
    assert len(receitas) == 1 and receitas[0]["valor"] == 30.0
    assert [c for c in app.listar_caixinhas() if c["nome"] == caixa] == antes


# ----- cópia de segurança antes da virada -----

def test_virada_salva_copia_com_os_dados_de_antes(tmp_path):
    from controle_financeiro.nucleo.ferramentas import ler_backup_automatico
    app, origem, novo, r, marca = _virada(tmp_path, compras=[("Cinema", "", {})])
    copia = ler_backup_automatico(r["backup"])
    assert r["backup"].startswith(str(tmp_path))
    meses = {s["mes"] for s in copia["sessoes"]}
    assert origem in meses and novo not in meses  # a cópia é de antes da virada
    assert any(c["item"] == f"Cinema {marca}" for c in copia["compras"])


def test_copias_automaticas_guardam_so_as_6_mais_novas(tmp_path):
    app = Financas(criar_banco("teste"), pasta_backups=tmp_path)
    for i in range(8):
        app.ferramentas.backup_automatico(tmp_path, "antes-da-virada", f"teste{i}")
    assert len(list(tmp_path.glob("antes-da-virada_*.cfauto"))) == 6


def test_sem_copia_de_seguranca_o_mes_nao_vira(tmp_path):
    import pytest
    arquivo = tmp_path / "nao_e_pasta"
    arquivo.write_text("x")  # a pasta de cópias não pode ser criada
    app = Financas(criar_banco("teste"), pasta_backups=arquivo)
    antes = app.sessoes()
    with pytest.raises(ValueError, match="cópia de segurança"):
        app.virar_mes()
    assert app.sessoes() == antes


# ----- editar compra sem apagar nem recriar -----

def test_editar_compra_muda_so_o_que_foi_pedido():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Tênis", "R$ 100,00", parcelas="2/5", pessoa=".")
    antes = app.obter_compra(id_)
    depois = app.editar_compra(id_, valor_parcela="R$ 120,50")
    assert depois["id"] == id_ and depois["valor_parcela"] == 120.5
    for campo in ("cartao", "item", "parcelas", "pessoa", "mes", "data_lancamento", "recorrente"):
        assert depois[campo] == antes[campo]


def test_editar_compra_para_emprestimo_e_de_volta():
    app = _app()
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Presente", "R$ 80,00", parcelas="", pessoa=".")
    assert app.editar_compra(id_, pessoa="Avô")["emprestimo"] == 1
    voltou = app.editar_compra(id_, pessoa=".")
    assert voltou["emprestimo"] == 0 and voltou["valor_real"] == 80.0


def test_editar_compra_recusa_campo_desconhecido_e_id_inexistente():
    import pytest
    app = _app()
    with pytest.raises(ValueError):
        app.editar_compra(999999, item="Nada")
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Livro", "R$ 50,00", parcelas="", pessoa=".")
    with pytest.raises(ValueError):
        app.editar_compra(id_, mes="2020-01")
