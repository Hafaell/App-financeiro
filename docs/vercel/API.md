# API da versão web (rascunho)

Todas as rotas ficam em `/api/...`, exigem `Authorization: Bearer <JWT do Supabase>` (menos
`/api/saude`) e chamam **um método da fachada `Financas`** (`nucleo/servico.py`), sem regra de
negócio própria. Parâmetro `mes` vazio = mês atual (o mais recente aberto), igual às ferramentas
da Ayla.

Erros (formato `{"erro": "mensagem em português"}`):

| Exceção no Python | HTTP |
|---|---|
| `ValueError` (regra de negócio) | 400 |
| `SessaoExpirada` | 401 |
| item não encontrado | 404 |
| `ErroBanco` | 422 |
| `ErroConexao` | 503 |

Fase indica quando a rota entra (veja `PLANO.md`).

## Sistema

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/saude` | (nenhuma; responde `{"ok": true}`) | 0 |
| GET | `/api/versao` | `versao()` (o front usa para saber se precisa recarregar) | 2 |

## Meses e resumo

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/meses` | `sessoes()`, `mes_ativo()` | 1 |
| POST | `/api/meses/virar` | `virar_mes()` (com cópia antes, ver PLANO §2.4) | 2 |
| DELETE | `/api/meses/{mes}` | `apagar_mes(mes)` | 2 |
| GET | `/api/resumo?mes=` | `resumo_mes(mes)` | 1 |
| GET | `/api/previsao?mes=` | `previsao_proximo_mes(mes)` | 2 |
| GET | `/api/parcelas-futuras?mes=&quantos=6` | `parcelas_futuras(mes, quantos)` | 2 |
| GET | `/api/assinaturas?mes=` | `assinaturas(mes)` | 2 |
| GET | `/api/comparativo?quantos=6` | `comparar_meses(quantos)` | 2 |
| GET | `/api/buscar?texto=` | `buscar(texto)` | 2 |
| GET | `/api/alertas-faturas` | `alertas_faturas()` | 2 |

## Cartões e compras

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/cartoes` | `listar_cartoes()` | 2 |
| POST | `/api/cartoes` | `adicionar_cartao(nome, cor)` | 2 |
| PATCH | `/api/cartoes/{id}/datas` | `definir_datas_cartao(id, fechamento, vencimento)` | 2 |
| GET | `/api/compras?mes=&cartao=` | `listar_compras(cartao, mes)` | 2 |
| GET | `/api/compras/{id}` | `obter_compra(id)` | 2 |
| POST | `/api/compras` | `lancar_compra(...)` | 2 |
| PATCH | `/api/compras/{id}` | `editar_compra(id, **campos)` (só os campos enviados) | 2 |
| DELETE | `/api/compras/{id}` | `apagar_compra(id)` | 2 |

## Receitas e despesas (`tabela` = `receitas` ou `despesas`)

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/{tabela}?mes=` | `listar_lancamentos(tabela, mes)` | 2 |
| GET | `/api/{tabela}/{id}` | `obter_lancamento(tabela, id)` | 2 |
| POST | `/api/{tabela}` | `adicionar_lancamento(...)` | 2 |
| PATCH | `/api/{tabela}/{id}` | `editar_lancamento(tabela, id, **campos)` | 2 |
| DELETE | `/api/{tabela}/{id}` | `apagar_lancamento(tabela, id)` | 2 |
| POST | `/api/recolocar` | `recolocar(tabela, linha)` (desfazer exclusão) | 2 |

## Categorias e renda

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/categorias` | `listar_categorias()` | 2 |
| POST | `/api/categorias` | `adicionar_categoria(nome, cor, orcamento)` | 2 |
| PUT | `/api/categorias/{id}` | `atualizar_categoria(id, nome, cor, orcamento)` | 2 |
| DELETE | `/api/categorias/{id}` | `apagar_categoria(id)` | 2 |
| PATCH | `/api/{tabela}/{id}/categoria` | `classificar(tabela, id, categoria_id)` | 2 |
| GET | `/api/gasto-por-categoria?mes=` | `gasto_por_categoria(mes)` | 2 |
| GET | `/api/renda?mes=` | `obter_renda(mes)` | 2 |
| PUT | `/api/renda` | `definir_renda(valor, mes)` | 2 |

## Empréstimos

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/emprestimos?mes=` | `quanto_me_devem(mes)` | 2 |
| GET | `/api/pessoas` | `pessoas()` | 2 |
| GET | `/api/emprestimos/{pessoa}?mes=` | `emprestimos_de(pessoa, mes)` | 2 |
| POST | `/api/pagamentos` | `registrar_pagamento(pessoa, valor, descricao, mes)` | 2 |

## Caixinhas

| Método | Rota | Fachada | Fase |
|---|---|---|---|
| GET | `/api/caixinhas` | `listar_caixinhas()`, `andamento_caixinhas()` | 2 |
| GET | `/api/caixinhas/{id}` | `obter_caixinha(id)` | 2 |
| POST | `/api/caixinhas` | `definir_caixinha(dono, nome, valor)` | 2 |
| PUT | `/api/caixinhas/{id}` | `atualizar_caixinha(...)` | 2 |
| PATCH | `/api/caixinhas/{id}/meta` | `definir_meta_caixinha(id, meta, data_alvo)` | 2 |
| POST | `/api/caixinhas/{id}/guardar` | `guardar_na_caixinha(id, valor, descricao)` | 2 |
| POST | `/api/caixinhas/{id}/retirar` | `retirar_da_caixinha(id, valor, descricao)` | 2 |
| GET | `/api/caixinhas/{id}/historico` | `historico_caixinha(id)` (vazio se `caixinhas_tem_historico()` for falso) | 2 |

## Só depois de decidir (PLANO §5)

| Método | Rota | Fachada | Observação |
|---|---|---|---|
| POST | `/api/extrato/ler` | `ler_extrato(nome, conteudo, mes)` | upload multipart |
| POST | `/api/extrato/importar` | `importar_extrato(itens, destino, mes)` | |
| GET | `/api/backups` | `listar_backups()` | depende do destino das cópias |
| POST | `/api/backups/restaurar` | `restaurar_backup(...)` | idem |
| POST | `/api/backups/exportar` | `exportar_backup(...)` | devolve o arquivo para download em vez de gravar em disco |
