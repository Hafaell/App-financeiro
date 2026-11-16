"""Formulário de compra no cartão (novo e edição). Pessoa preenchida = empréstimo."""
from PySide6.QtWidgets import QCheckBox, QDialog, QMessageBox

from controle_financeiro.dados.contexto import fin
from controle_financeiro.ui.componentes import ComboPessoa, Formulario, combo, texto
from controle_financeiro.ui.formatacao import (SEM_CATEGORIA, _parcela_exibida, _pessoa_exibida, brl,
                                               categorias_opcoes, id_categoria, nome_categoria, nomes_cartoes)


def campos_compra(c=None):
    """Campos do formulário de compra. Pessoa preenchida = empréstimo."""
    def valor(chave, padrao=""):
        return c[chave] if c is not None else padrao
    recorrente = QCheckBox("Recorrente: permanece no próximo mês")
    recorrente.setChecked(bool(valor("recorrente", 0)))
    return [
        ("cartao", "Cartão", combo(nomes_cartoes(), valor("cartao", None))),
        ("item", "Descrição", texto(valor("item"), "Ex.: Mercado")),
        ("categoria", "Categoria", combo(categorias_opcoes(),
                                         nome_categoria(c["categoria_id"]) if c else SEM_CATEGORIA)),
        ("parcelas", "Parcelas", texto(_parcela_exibida(c) if c else "", "Ex.: 3/12 (vazio = à vista)")),
        ("valor_parcela", "Valor da parcela",
         texto(brl(c["valor_parcela"]) if c else "", "R$ 0,00")),
        ("pessoa", "Pessoa (só se for empréstimo)",
         ComboPessoa(_pessoa_exibida(c) if c else "")),
        ("recorrente", "", recorrente),
    ]


def dialogo_compra(pai, c):
    """Abre a janela de edição de uma compra. Só altera o registro existente."""
    dlg = Formulario(pai, "Editar compra", campos_compra(c))
    if dlg.exec() != QDialog.Accepted:
        return False
    v = dlg.valores()
    try:
        fin().atualizar_compra(c["id"], v["cartao"], v["item"], v["parcelas"],
                              v["valor_parcela"], pessoa=v["pessoa"],
                              recorrente=v["recorrente"], categoria_id=id_categoria(v["categoria"]))
    except ValueError as e:
        QMessageBox.warning(pai, "Não consegui salvar", str(e))
        return False
    return True
