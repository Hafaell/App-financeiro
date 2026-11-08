"""Abre o Controle Financeiro sem a janela do CMD (clique duplo neste arquivo).

Se o app não conseguir abrir, mostra uma mensagem e grava o detalhe do erro em
%LOCALAPPDATA%\\ControleFinanceiro\\erro_inicializacao.txt.
"""
import os
import sys
import traceback

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(RAIZ, "src"))

try:
    from controle_financeiro.ui.app import main
    main()
except Exception:
    detalhe = traceback.format_exc()
    pasta_dados = os.path.join(os.environ.get("LOCALAPPDATA", RAIZ), "ControleFinanceiro")
    os.makedirs(pasta_dados, exist_ok=True)
    arquivo = os.path.join(pasta_dados, "erro_inicializacao.txt")
    with open(arquivo, "w", encoding="utf-8") as f:
        f.write(detalhe)
    try:
        from PySide6.QtWidgets import QApplication, QMessageBox
        QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(None, "Controle Financeiro",
                             "O app não conseguiu abrir.\n\nDetalhes em:\n" + arquivo)
    except Exception:
        pass
