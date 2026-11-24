"""API da versão web (FastAPI), com SQLite temporário no lugar do Supabase."""
import base64

import pytest
from fastapi.testclient import TestClient

from controle_financeiro.dados.banco import BancoSqlite
from controle_financeiro.nucleo.servico import Financas
from controle_financeiro.web import api


@pytest.fixture
def cliente(tmp_path):
    banco = BancoSqlite(tmp_path / "api.db")
    api.app.dependency_overrides[api.financas] = lambda: Financas(banco, copias_no_banco=True)
    yield TestClient(api.app)
    api.app.dependency_overrides.clear()


def test_saude_nao_precisa_de_login():
    assert TestClient(api.app).get("/api/saude").json()["ok"] is True


def test_sem_token_responde_401():
    resp = TestClient(api.app).get("/api/inicio")
    assert resp.status_code == 401
    assert "erro" in resp.json()


def test_inicio_e_painel(cliente):
    inicio = cliente.get("/api/inicio").json()
    assert inicio["mes_ativo"] in inicio["meses"]
    assert [c["nome"] for c in inicio["cartoes"]] == ["Inter", "Nubank"]
    painel = cliente.get("/api/painel").json()
    assert painel["mes"] == inicio["mes_ativo"]
    assert painel["resumo"]["saldo"] == 0


def test_lancar_editar_apagar_e_desfazer_compra(cliente):
    id_ = cliente.post("/api/compras", json={"cartao": "inter", "item": "Mouse",
                                             "valor_parcela": "50,00", "parcelas": "1/3"}).json()["id"]
    editada = cliente.patch(f"/api/compras/{id_}", json={"valor_parcela": 60}).json()
    assert editada["valor_parcela"] == 60 and editada["parcelas"] == "1/3"
    apagada = cliente.delete(f"/api/compras/{id_}").json()["apagada"]
    assert cliente.get("/api/compras").json() == []
    assert cliente.post("/api/recolocar", json={"tabela": "compras", "linha": apagada}).json()["ok"]
    assert [c["id"] for c in cliente.get("/api/compras").json()] == [id_]


def test_erro_de_regra_vira_400_em_portugues(cliente):
    resp = cliente.post("/api/compras", json={"cartao": "Inter", "item": "", "valor_parcela": 10})
    assert resp.status_code == 400
    assert resp.json()["erro"] == "Informe a descrição da compra."


def test_item_inexistente_vira_404(cliente):
    assert cliente.delete("/api/compras/999").status_code == 404


def test_receitas_e_despesas(cliente):
    cliente.post("/api/lancamentos/receitas", json={"descricao": "Salário", "valor": "3.000,00"})
    did = cliente.post("/api/lancamentos/despesas",
                       json={"descricao": "Luz", "valor": 100, "recorrente": True}).json()["id"]
    cliente.patch(f"/api/lancamentos/despesas/{did}", json={"valor": 120})
    resumo = cliente.get("/api/painel").json()["resumo"]
    assert resumo["receitas"] == 3000 and resumo["despesas_manuais"] == 120
    assert cliente.get("/api/lancamentos/outra").status_code == 400


def test_categoria_e_gasto_no_painel(cliente):
    cat = cliente.get("/api/inicio").json()["categorias"][0]["id"]
    cliente.post("/api/lancamentos/despesas", json={"descricao": "Pão", "valor": 10, "categoria_id": cat})
    assert {"categoria_id": cat, "valor": 10} in cliente.get("/api/painel").json()["gasto"]


def test_emprestimos_e_pagamento(cliente):
    cliente.post("/api/compras", json={"cartao": "Nubank", "item": "Tênis", "valor_parcela": 200,
                                       "pessoa": "Pai"})
    cliente.post("/api/pagamentos", json={"pessoa": "Pai", "valor": 50})
    assert cliente.get("/api/emprestimos").json() == [
        {"pessoa": "Pai", "emprestado": 200, "ja_pago": 50, "em_aberto": 150}]
    assert cliente.get("/api/inicio").json()["pessoas"] == ["Pai"]


def test_editar_pagamento(cliente):
    cliente.post("/api/compras", json={"cartao": "Nubank", "item": "Tênis", "valor_parcela": 200,
                                       "pessoa": "Pai"})
    pid = cliente.post("/api/pagamentos", json={"pessoa": "Pai", "valor": 500}).json()["id"]
    antes = cliente.get("/api/pagamentos/Pai").json()
    assert [(p["id"], p["valor"]) for p in antes] == [(pid, 500)]
    resp = cliente.put(f"/api/pagamentos/{pid}", json={"pessoa": "Pai", "valor": "50,00", "descricao": "pix"})
    assert resp.status_code == 200 and resp.json()["valor"] == 50
    depois = cliente.get("/api/pagamentos/Pai").json()
    assert [(p["id"], p["valor"], p["descricao"], p["data"], p["mes"]) for p in depois] == [
        (pid, 50, "pix", antes[0]["data"], antes[0]["mes"])]
    assert cliente.get("/api/emprestimos").json()[0]["em_aberto"] == 150
    assert cliente.put(f"/api/pagamentos/{pid}", json={"pessoa": " ", "valor": 1}).status_code == 400
    assert cliente.put("/api/pagamentos/99999", json={"pessoa": "Pai", "valor": 1}).status_code == 400


def test_apagar_pagamento(cliente):
    cliente.post("/api/compras", json={"cartao": "Nubank", "item": "Tênis", "valor_parcela": 200,
                                       "pessoa": "Pai"})
    pid = cliente.post("/api/pagamentos", json={"pessoa": "Pai", "valor": 50}).json()["id"]
    assert cliente.delete(f"/api/pagamentos/{pid}").json() == {"ok": True}
    assert cliente.get("/api/pagamentos/Pai").json() == []
    assert cliente.get("/api/emprestimos").json()[0]["em_aberto"] == 200
    assert cliente.delete(f"/api/pagamentos/{pid}").status_code == 400


def test_caixinhas(cliente):
    cliente.post("/api/caixinhas", json={"dono": "Eu", "nome": "Viagem", "valor": 100})
    cid = cliente.get("/api/caixinhas").json()["caixinhas"][0]["id"]
    assert cliente.post(f"/api/caixinhas/{cid}/guardar", json={"valor": "50"}).json()["valor"] == 150
    resp = cliente.post(f"/api/caixinhas/{cid}/retirar", json={"valor": 500})
    assert resp.status_code == 400
    assert len(cliente.get(f"/api/caixinhas/{cid}/historico").json()) == 2


def test_virar_salva_copia_no_banco_e_restaura(cliente):
    cliente.post("/api/compras", json={"cartao": "Inter", "item": "Antes", "valor_parcela": 10})
    mes = cliente.get("/api/inicio").json()["mes_ativo"]
    virada = cliente.post("/api/meses/virar").json()
    assert virada["origem"] == mes
    copias = cliente.get("/api/backups").json()
    assert copias[0]["motivo"].startswith("Antes da virada de")
    restaurado = cliente.post("/api/backups/restaurar", json={"id": copias[0]["id"]}).json()
    assert restaurado["copia_antes"]
    assert cliente.get("/api/inicio").json()["mes_ativo"] == mes  # voltou para antes da virada
    assert len(cliente.get("/api/backups").json()) == 2


def test_copias_no_banco_guardam_so_as_6_mais_novas(tmp_path):
    app = Financas(BancoSqlite(tmp_path / "c.db"), copias_no_banco=True)
    for i in range(8):
        app.copias.salvar("antes-da-virada", f"2026-0{i + 1}")
    assert len(app.listar_backups()) == 6


def test_planejamento_comparativo_e_busca(cliente):
    cliente.post("/api/compras", json={"cartao": "Inter", "item": "Curso", "valor_parcela": 100,
                                       "parcelas": "1/3"})
    plano = cliente.get("/api/planejamento").json()
    assert plano["previsao"]["meu_cartao"] == 100
    assert plano["parcelas_futuras"][0]["total"] == 100
    assert len(cliente.get("/api/comparativo").json()) == 1
    assert cliente.get("/api/buscar", params={"texto": "curso"}).json()["total"] == 100


def test_extrato_ler_e_importar(cliente):
    csv = "data,descricao,valor\n05/11/2026,Padaria,12.50\n06/11/2026,Pagamento recebido,-100\n"
    lido = cliente.post("/api/extrato/ler", json={
        "nome": "Nubank_2026-11.csv", "conteudo_base64": base64.b64encode(csv.encode()).decode()}).json()
    assert lido["cartao_sugerido"] == "Nubank"
    novos = [i for i in lido["itens"] if i["situacao"] == "Novo"]
    assert [i["descricao"] for i in novos] == ["Padaria"]
    feito = cliente.post("/api/extrato/importar", json={"itens": novos, "destino": "Nubank"}).json()
    assert feito["importados"] == 1


def test_exportar_backup_com_senha(cliente):
    assert cliente.post("/api/backups/exportar", json={"senha": "123"}).status_code == 400
    resp = cliente.post("/api/backups/exportar", json={"senha": "segredo1"})
    assert resp.content.startswith(b"CFBK1")
    assert "attachment" in resp.headers["content-disposition"]


def test_renda_e_cartao(cliente):
    cliente.put("/api/renda", json={"valor": "5000"})
    assert cliente.get("/api/renda").json()["valor"] == 5000
    assert cliente.post("/api/cartoes", json={"nome": "C6", "cor": "#222222"}).json()["ok"]
    cid = cliente.get("/api/inicio").json()["cartoes"][-1]["id"]
    assert cliente.patch(f"/api/cartoes/{cid}/datas", json={"dia_fechamento": 3}).json()["ok"]


def _compra(cliente, item):
    return cliente.post("/api/compras", json={"cartao": "inter", "item": item,
                                              "valor_parcela": 10}).json()["id"]


def test_apagar_varios_compras_e_desfazer(cliente):
    a, b, c = (_compra(cliente, i) for i in ("A", "B", "C"))
    resp = cliente.post("/api/apagar-varios", json={"tabela": "compras", "ids": [a, b]}).json()
    assert resp["ok"] and sorted(l["id"] for l in resp["apagadas"]) == sorted([a, b])
    assert [x["id"] for x in cliente.get("/api/compras").json()] == [c]
    for linha in resp["apagadas"]:
        cliente.post("/api/recolocar", json={"tabela": "compras", "linha": linha})
    assert sorted(x["id"] for x in cliente.get("/api/compras").json()) == sorted([a, b, c])


def test_apagar_varios_despesas_nao_mexe_em_receitas(cliente):
    d1 = cliente.post("/api/lancamentos/despesas", json={"descricao": "Luz", "valor": 10}).json()["id"]
    d2 = cliente.post("/api/lancamentos/despesas", json={"descricao": "Água", "valor": 20}).json()["id"]
    cliente.post("/api/lancamentos/receitas", json={"descricao": "Salário", "valor": 100})
    cliente.post("/api/apagar-varios", json={"tabela": "despesas", "ids": [d1, d2]})
    assert cliente.get("/api/lancamentos/despesas").json() == []
    assert len(cliente.get("/api/lancamentos/receitas").json()) == 1


def test_apagar_varios_ids_vazios_ou_inexistentes(cliente):
    for ids in ([], [9999]):
        resp = cliente.post("/api/apagar-varios", json={"tabela": "compras", "ids": ids})
        assert resp.status_code == 200 and resp.json()["apagadas"] == []


def test_apagar_varios_tabela_invalida(cliente):
    resp = cliente.post("/api/apagar-varios", json={"tabela": "outra", "ids": [1]})
    assert resp.status_code in (400, 422)
