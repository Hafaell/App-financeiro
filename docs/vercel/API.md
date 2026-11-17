# API da versão web

Código: `src/controle_financeiro/web/api.py` (o `api/index.py` da raiz só o importa para o Vercel).
Testes: `tests/test_api.py` (SQLite temporário no lugar do Supabase).

Todas as rotas ficam em `/api/...`, exigem `Authorization: Bearer <JWT do Supabase>` (menos
`/api/saude`) e chamam **um método da fachada `Financas`** (`nucleo/servico.py`), sem regra de
negócio própria. Parâmetro `mes` vazio = mês atual (o mais recente aberto), igual às ferramentas
da Ayla. Valores em reais aceitam número (`63.19`) ou texto (`"63,19"`, `"R$ 1.250,50"`).

Erros (formato `{"erro": "mensagem em português"}`):

| Exceção no Python | HTTP |
|---|---|
| `ValueError` (regra de negócio) ou pedido com campo inválido | 400 |
| `SessaoExpirada` (sem token ou token vencido) | 401 |
| item não encontrado | 404 |
| `ErroBanco` (o Supabase recusou) | 422 |
| `RuntimeError` (configuração, ex.: falta `SUPABASE_URL`) | 500 |
| `ErroConexao` (Supabase fora do ar) | 503 |

Cada requisição baixa a cópia do usuário numa chamada só ao Supabase (`BancoWeb`); gravações vão
direto. Por isso há rotas que juntam o que uma tela precisa (`/api/inicio`, `/api/painel`,
`/api/planejamento`): uma requisição por tela.

## Sistema

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/saude` | (nenhuma; `{"ok": true}`) |
| GET | `/api/versao` | versão dos dados no Supabase, sem baixar a cópia (o site confere a cada 15 s) |
| GET | `/api/inicio` | `sessoes`, `mes_ativo`, `listar_cartoes`, `listar_categorias`, `pessoas`, `caixinhas_tem_historico`, `versao` |
| GET | `/api/painel?mes=` | Visão geral: `resumo_mes`, `gasto_por_categoria`, `listar_categorias`, `alertas_faturas`, `obter_renda` |

## Meses e resumo

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/meses` | `sessoes()`, `mes_ativo()` |
| POST | `/api/meses/virar` | `virar_mes()` (salva cópia na tabela `backups` antes) |
| DELETE | `/api/meses/{mes}` | `apagar_mes(mes)` |
| GET | `/api/resumo?mes=` | `resumo_mes(mes)` |
| GET | `/api/previsao?mes=` | `previsao_proximo_mes(mes)` |
| GET | `/api/planejamento?mes=&quantos=6` | previsão + `parcelas_futuras` + `assinaturas` |
| GET | `/api/parcelas-futuras?mes=&quantos=6` | `parcelas_futuras(mes, quantos)` |
| GET | `/api/assinaturas?mes=` | `assinaturas(mes)` |
| GET | `/api/comparativo?quantos=6` | `comparar_meses(quantos)` |
| GET | `/api/buscar?texto=` | `buscar(texto)` (com o total) |
| GET | `/api/alertas-faturas?dias=5` | `alertas_faturas()` |

## Cartões e compras

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/cartoes` | `listar_cartoes()` |
| POST | `/api/cartoes` | `adicionar_cartao(nome, cor)` |
| PATCH | `/api/cartoes/{id}/datas` | `definir_datas_cartao(id, fechamento, vencimento)` |
| GET | `/api/compras?mes=&cartao=` | `listar_compras(cartao, mes)` |
| GET | `/api/compras/{id}` | `obter_compra(id)` |
| POST | `/api/compras` | `lancar_compra(...)` |
| PATCH | `/api/compras/{id}` | `editar_compra(id, **campos)` (só os campos enviados) |
| DELETE | `/api/compras/{id}` | `apagar_compra(id)`; devolve a linha apagada em `apagada` (para o "Desfazer") |

## Receitas e despesas (`tabela` = `receitas` ou `despesas`)

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/lancamentos/{tabela}?mes=` | `listar_lancamentos(tabela, mes)` |
| GET | `/api/lancamentos/{tabela}/{id}` | `obter_lancamento(tabela, id)` |
| POST | `/api/lancamentos/{tabela}` | `adicionar_lancamento(...)` |
| PATCH | `/api/lancamentos/{tabela}/{id}` | `editar_lancamento(tabela, id, **campos)` |
| DELETE | `/api/lancamentos/{tabela}/{id}` | `apagar_lancamento(tabela, id)`; devolve `apagada` |
| POST | `/api/recolocar` | `recolocar(tabela, linha)` (desfazer exclusão, mesmo id) |

## Categorias e renda

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/categorias` | `listar_categorias()` |
| POST | `/api/categorias` | `adicionar_categoria(nome, cor, orcamento)` |
| PUT | `/api/categorias/{id}` | `atualizar_categoria(id, nome, cor, orcamento)` |
| DELETE | `/api/categorias/{id}` | `apagar_categoria(id)` |
| PATCH | `/api/classificar/{compras\|despesas}/{id}` | `classificar(tabela, id, categoria_id)` |
| GET | `/api/gasto-por-categoria?mes=` | `gasto_por_categoria(mes)` como lista `[{categoria_id, valor}]` |
| GET | `/api/renda?mes=` | `obter_renda(mes)` |
| PUT | `/api/renda` | `definir_renda(valor, mes)` |

## Empréstimos

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/emprestimos?mes=` | `quanto_me_devem(mes)` |
| GET | `/api/pessoas` | `pessoas()` |
| GET | `/api/emprestimos/{pessoa}?mes=` | `emprestimos_de(pessoa, mes)` (mes vazio = todos os meses) |
| POST | `/api/pagamentos` | `registrar_pagamento(pessoa, valor, descricao, mes)` |

## Caixinhas

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/caixinhas` | `andamento_caixinhas()` + `caixinhas_tem_historico()` |
| GET | `/api/caixinhas/{id}` | `obter_caixinha(id)` |
| POST | `/api/caixinhas` | `definir_caixinha(dono, nome, valor)` |
| PUT | `/api/caixinhas/{id}` | `atualizar_caixinha(...)` |
| PATCH | `/api/caixinhas/{id}/meta` | `definir_meta_caixinha(id, meta, data_alvo)` |
| POST | `/api/caixinhas/{id}/guardar` | `guardar_na_caixinha(id, valor, descricao)` |
| POST | `/api/caixinhas/{id}/retirar` | `retirar_da_caixinha(id, valor, descricao)` |
| GET | `/api/caixinhas/{id}/historico` | `historico_caixinha(id)` |

## Importar extrato

| Método | Rota | Fachada |
|---|---|---|
| POST | `/api/extrato/ler` | `ler_extrato(nome, conteudo, mes)`; corpo `{nome, conteudo_base64, mes}`; devolve também `cartao_sugerido` |
| POST | `/api/extrato/importar` | `importar_extrato(itens, destino, mes)` |

## Cópias de segurança

| Método | Rota | Fachada |
|---|---|---|
| GET | `/api/backups` | `listar_backups()` (tabela `backups`, script `08_backups_web.sql`) |
| POST | `/api/backups/restaurar` | `restaurar_backup(id)` |
| POST | `/api/backups/exportar` | `gerar_backup(senha)`; responde o arquivo `.cfbak` para baixar |
