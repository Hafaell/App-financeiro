"""Ponto de entrada da interface."""
import sys

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtWidgets import QMessageBox

from financas.contexto import auth
from financas.usuarios_nuvem import ErroConexaoNuvem
from .dialogos import Login
from .janela import Janela
from .tema import TEMA


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TEMA)
    try:
        if not auth().usuario_logado():
            login = Login("")
            if login.exec() != QDialog.Accepted:
                sys.exit(0)
            auth().definir_sessao(login.usuario_conectado)
    except ErroConexaoNuvem as e:
        QMessageBox.critical(None, "Controle Financeiro", str(e))
        sys.exit(1)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())
