"""Ponto de entrada da interface."""
import sys

from PySide6.QtWidgets import QApplication, QDialog
from financas.contexto import auth
from .dialogos import Login
from .janela import Janela
from .tema import TEMA


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TEMA)
    if not auth().usuario_logado():
        login = Login("")
        if login.exec() != QDialog.Accepted:
            sys.exit(0)
        auth().definir_sessao(login.usuario_conectado)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())
