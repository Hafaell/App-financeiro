"""Abre o Controle Financeiro sem a janela do CMD.

Se o app não conseguir abrir, mostra uma mensagem e grava o detalhe do erro em
%LOCALAPPDATA%\\ControleFinanceiro\\erro_inicializacao.txt.
"""
import os
import sys
import traceback

PASTA = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PASTA)

try:
    from interface.app import main
    main()
except Exception:
    detalhe = traceback.format_exc()
    pasta_dados = os.path.join(os.environ.get("LOCALAPPDATA", PASTA), "ControleFinanceiro")
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
