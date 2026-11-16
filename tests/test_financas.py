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


# ----- restaurar uma cópia e desfazer exclusão -----

def _banco_proprio(tmp_path):
    """Banco SQLite só deste teste: restaurar troca TODOS os dados, então não pode usar o compartilhado."""
    from controle_financeiro.dados.banco import BancoSqlite
    return Financas(BancoSqlite(tmp_path / "proprio.db"), pasta_backups=tmp_path / "copias")


def test_restaurar_volta_os_dados_da_copia_com_os_mesmos_ids(tmp_path):
    app = _banco_proprio(tmp_path)
    cartao = app.listar_cartoes()[0]["nome"]
    lazer = next(c["id"] for c in app.listar_categorias() if c["nome"] == "Lazer")
    cinema = app.lancar_compra(cartao, "Cinema", "R$ 40,00", parcelas="", pessoa=".", categoria_id=lazer)
    app.adicionar_lancamento("receitas", "Salário", "R$ 1.000,00")
    copia = app.ferramentas.backup_automatico(app.pasta_backups, "antes-da-virada", app.mes_ativo())
    antes = {t: app.banco.consultar(f"SELECT * FROM {t} ORDER BY 1") for t in ("compras", "receitas", "categorias")}

    app.apagar_compra(cinema)
    app.lancar_compra(cartao, "Lançada depois", "R$ 5,00", parcelas="", pessoa=".")
    app.virar_mes()
    seguranca = app.restaurar_backup(copia)

    depois = {t: app.banco.consultar(f"SELECT * FROM {t} ORDER BY 1") for t in antes}
    assert depois == antes  # mesmas linhas, mesmos ids, categoria ligada à compra
    assert len(app.sessoes()) == 1
    assert app.obter_compra(cinema)["categoria_id"] == lazer
    assert any(b["caminho"] == seguranca for b in app.listar_backups())  # dá para voltar atrás


def test_restaurar_recusa_arquivo_que_nao_e_copia(tmp_path):
    import pytest
    app = _banco_proprio(tmp_path)
    falso = tmp_path / "falso.cfauto"
    falso.write_bytes(b"qualquer coisa")
    with pytest.raises(ValueError, match="Não consegui abrir"):
        app.restaurar_backup(falso)


def test_listar_copias_da_mais_nova_para_a_mais_antiga(tmp_path):
    app = _banco_proprio(tmp_path)
    app.ferramentas.backup_automatico(app.pasta_backups, "antes-da-virada", "2026-11")
    app.ferramentas.backup_automatico(app.pasta_backups, "antes-de-restaurar")
    lista = app.listar_backups()
    assert len(lista) == 2
    assert {b["motivo"] for b in lista} == {"Antes da virada de Novembro 26", "Antes de restaurar uma cópia"}
    assert lista[0]["quando"] >= lista[1]["quando"]


def test_desfazer_exclusao_volta_a_compra_igual(tmp_path):
    app = _banco_proprio(tmp_path)
    cartao = app.listar_cartoes()[0]["nome"]
    id_ = app.lancar_compra(cartao, "Celular", "R$ 250,00", parcelas="2/10", pessoa="Benzinho")
    linha = app.obter_compra(id_)
    app.apagar_compra(id_)
    assert app.obter_compra(id_) is None
    app.recolocar("compras", linha)
    assert app.obter_compra(id_) == linha


def test_desfazer_exclusao_de_despesa_e_receita(tmp_path):
    app = _banco_proprio(tmp_path)
    for tabela in ("despesas", "receitas"):
        id_ = app.adicionar_lancamento(tabela, "Item", "R$ 10,00")
        linha = app.obter_lancamento(tabela, id_)
        app.apagar_lancamento(tabela, id_)
        app.recolocar(tabela, linha)
        assert app.obter_lancamento(tabela, id_) == linha


def test_fila_offline_nao_repete_o_id_quando_o_comando_ja_traz():
    from controle_financeiro.dados.banco import _sql_para_envio
    sql, args = _sql_para_envio({"tabela": "compras", "sql": "INSERT INTO compras (id, item) VALUES (?, ?)",
                                 "args": [7, "X"], "id": 7})
    assert sql == "INSERT INTO compras (id, item) VALUES (%s, %s)" and args == [7, "X"]
    sql, args = _sql_para_envio({"tabela": "compras", "sql": "INSERT INTO compras (item) VALUES (?)",
                                 "args": ["X"], "id": 7})
    assert sql == "INSERT INTO compras (id, item) VALUES (%s, %s)" and args == [7, "X"]


# ----- previsão do próximo mês -----

def test_previsao_bate_com_o_mes_que_a_virada_abre(tmp_path):
    app = _banco_proprio(tmp_path)
    cartao = app.listar_cartoes()[0]["nome"]
    app.lancar_compra(cartao, "Notebook", "R$ 300,00", parcelas="3/12", pessoa=".")
    app.lancar_compra(cartao, "Última", "R$ 50,00", parcelas="12/12", pessoa=".")
    app.lancar_compra(cartao, "Mercado", "R$ 400,00", parcelas="", pessoa=".")
    app.lancar_compra(cartao, "Spotify", "R$ 21,90", parcelas="", pessoa=".", recorrente=True)
    app.lancar_compra(cartao, "Celular", "R$ 250,00", parcelas="2/10", pessoa="Benzinho")
    app.adicionar_lancamento("despesas", "Aluguel", "R$ 1.100,00", recorrente=True)
    app.adicionar_lancamento("despesas", "Dentista (2/5)", "R$ 150,00")
    app.adicionar_lancamento("despesas", "Feira", "R$ 80,00")
    app.adicionar_lancamento("receitas", "Salário", "R$ 4.000,00")
    antes = app.sessoes()

    previsao = app.previsao_proximo_mes()
    assert app.sessoes() == antes  # prever não grava nada
    assert previsao["meu_cartao"] == 321.9 and previsao["emprestimos"] == 250.0
    assert previsao["despesas"] == 1250.0 and previsao["receitas"] == 4000.0
    assert previsao["saldo"] == round(4000 - 1250 - 321.9, 2) and not previsao["ja_aberto"]

    novo = app.virar_mes()["novo"]
    real = app.resumo_mes(novo)
    assert previsao["mes"] == novo
    assert (real["meu_cartao_total"], real["despesas_manuais"], real["receitas"], real["saldo"]) == \
        (previsao["meu_cartao"], previsao["despesas"], previsao["receitas"], previsao["saldo"])
    assert real["cartoes_com_emprestimos_total"] == round(previsao["meu_cartao"] + previsao["emprestimos"], 2)
    assert app.previsao_proximo_mes(previsao["origem"])["ja_aberto"]


# ----- histórico das caixinhas -----

def test_guardar_e_retirar_anotam_no_historico(tmp_path):
    import pytest
    app = _banco_proprio(tmp_path)
    app.definir_caixinha("Rafael", "Viagem", "R$ 100,00")
    cx = next(c for c in app.listar_caixinhas() if c["nome"] == "Viagem")
    app.guardar_na_caixinha(cx["id"], "R$ 250,00", "salário")
    assert app.retirar_da_caixinha(cx["id"], "R$ 50,00")["valor"] == 300.0
    with pytest.raises(ValueError, match="não dá para retirar"):
        app.retirar_da_caixinha(cx["id"], "R$ 1.000,00")
    with pytest.raises(ValueError):
        app.guardar_na_caixinha(cx["id"], "0")
    movimentos = [(m["valor"], m["saldo"], m["descricao"]) for m in app.historico_caixinha(cx["id"])]
    assert movimentos == [(-50.0, 300.0, "Retirada"), (250.0, 350.0, "salário"), (100.0, 100.0, "Valor inicial")]


def test_ajustar_o_valor_da_caixinha_anota_a_diferenca(tmp_path):
    app = _banco_proprio(tmp_path)
    app.definir_caixinha("Rafael", "Reserva", "R$ 1.000,00")
    cx = next(c for c in app.listar_caixinhas() if c["nome"] == "Reserva")
    app.definir_caixinha("Rafael", "Reserva", "R$ 1.200,00")      # pela Ayla
    app.atualizar_caixinha(cx["id"], "Rafael", "Reserva", "R$ 1.150,00")  # pelo formulário
    app.atualizar_caixinha(cx["id"], "Rafael", "Reserva", "R$ 1.150,00", "R$ 5.000,00")  # só a meta: sem movimento
    assert [m["valor"] for m in app.historico_caixinha(cx["id"])] == [-50.0, 200.0, 1000.0]


def test_restaurar_copia_antiga_sem_historico_de_caixinhas(tmp_path):
    app = _banco_proprio(tmp_path)
    app.definir_caixinha("Rafael", "Viagem", "R$ 100,00")
    caminho = app.ferramentas.backup_automatico(app.pasta_backups, "antes-da-virada", app.mes_ativo())
    from controle_financeiro.nucleo.ferramentas import ler_backup_automatico
    dados = ler_backup_automatico(caminho)
    del dados["movimentos_caixinha"]  # como uma cópia feita antes desta versão
    app.ferramentas.restaurar(dados)
    assert [c["nome"] for c in app.listar_caixinhas()] == ["Viagem"]
    assert app.historico_caixinha(app.listar_caixinhas()[0]["id"]) == []


def test_supabase_sem_o_script_07_abre_e_desliga_so_o_historico(tmp_path):
    from controle_financeiro.dados.banco import BancoPostgres
    from controle_financeiro.dados.nuvem import ErroBanco

    class ClienteFalso:
        logado = True

        def preparar(self):
            pass

        def executar(self, sql, params=()):
            if "movimentos_caixinha" in sql:
                raise ErroBanco('relation "movimentos_caixinha" does not exist')
            if sql.startswith("SELECT valor FROM meta"):
                return {"linhas": [{"valor": 0}]}
            if sql == "SELECT * FROM meta":  # o Supabase sempre tem a linha da versão
                return {"linhas": [{"chave": "versao", "valor": 0}]}
            if sql.startswith("SELECT"):
                return {"linhas": []}
            return {"id": 1, "afetadas": 1}

        def executar_lote(self, comandos):
            if any("movimentos_caixinha" in s for s, _ in comandos):
                raise ErroBanco("tabela não existe")
            return [{"id": None, "afetadas": 1} for _ in comandos]

    banco = BancoPostgres(ClienteFalso(), tmp_path / "fila.dat", tmp_path / "cache.dat")
    app = Financas(banco, pasta_backups=tmp_path)
    assert app.listar_caixinhas() == []  # abriu normalmente
    assert not app.caixinhas_tem_historico()
    app.definir_caixinha("Rafael", "Viagem", "R$ 10,00")  # grava sem tentar o histórico
