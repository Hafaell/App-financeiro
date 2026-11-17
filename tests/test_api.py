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
    resp = TestClient(api.app).get("/api/meses")
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
    assert cliente.get("/api/compras/999").status_code == 404


def test_receitas_e_despesas(cliente):
    cliente.post("/api/lancamentos/receitas", json={"descricao": "Salário", "valor": "3.000,00"})
    did = cliente.post("/api/lancamentos/despesas",
                       json={"descricao": "Luz", "valor": 100, "recorrente": True}).json()["id"]
    cliente.patch(f"/api/lancamentos/despesas/{did}", json={"valor": 120})
    resumo = cliente.get("/api/resumo").json()
    assert resumo["receitas"] == 3000 and resumo["despesas_manuais"] == 120
    assert cliente.get("/api/lancamentos/outra").status_code == 400


def test_categoria_gasto_e_classificar(cliente):
    cat = cliente.get("/api/categorias").json()[0]["id"]
    did = cliente.post("/api/lancamentos/despesas", json={"descricao": "Pão", "valor": 10}).json()["id"]
    assert cliente.patch(f"/api/classificar/despesas/{did}", json={"categoria_id": cat}).json()["ok"]
    assert {"categoria_id": cat, "valor": 10} in cliente.get("/api/gasto-por-categoria").json()


def test_emprestimos_e_pagamento(cliente):
    cliente.post("/api/compras", json={"cartao": "Nubank", "item": "Tênis", "valor_parcela": 200,
                                       "pessoa": "Pai"})
    cliente.post("/api/pagamentos", json={"pessoa": "Pai", "valor": 50})
    assert cliente.get("/api/emprestimos").json() == [
        {"pessoa": "Pai", "emprestado": 200, "ja_pago": 50, "em_aberto": 150}]
    assert cliente.get("/api/pessoas").json() == ["Pai"]


def test_caixinhas(cliente):
    cliente.post("/api/caixinhas", json={"dono": "Eu", "nome": "Viagem", "valor": 100})
    cid = cliente.get("/api/caixinhas").json()["caixinhas"][0]["id"]
    assert cliente.post(f"/api/caixinhas/{cid}/guardar", json={"valor": "50"}).json()["valor"] == 150
    resp = cliente.post(f"/api/caixinhas/{cid}/retirar", json={"valor": 500})
    assert resp.status_code == 400
    assert len(cliente.get(f"/api/caixinhas/{cid}/historico").json()) == 2


def test_virar_salva_copia_no_banco_e_restaura(cliente):
    cliente.post("/api/compras", json={"cartao": "Inter", "item": "Antes", "valor_parcela": 10})
    mes = cliente.get("/api/meses").json()["mes_ativo"]
    virada = cliente.post("/api/meses/virar").json()
    assert virada["origem"] == mes
    copias = cliente.get("/api/backups").json()
    assert copias[0]["motivo"].startswith("Antes da virada de")
    restaurado = cliente.post("/api/backups/restaurar", json={"id": copias[0]["id"]}).json()
    assert restaurado["copia_antes"]
    assert cliente.get("/api/meses").json()["mes_ativo"] == mes  # voltou para antes da virada
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
    cid = cliente.get("/api/cartoes").json()[-1]["id"]
    assert cliente.patch(f"/api/cartoes/{cid}/datas", json={"dia_fechamento": 3}).json()["ok"]
