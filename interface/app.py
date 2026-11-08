"""Ponto de entrada da interface."""
import sys

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtWidgets import QMessageBox

from financas.contexto import auth
from financas.nuvem import ErroConexao
from financas.config import CONEXAO_PATH, TIPO_BANCO
from .dialogos import ConfigurarConexao, Login
from .janela import Janela
from .tema import TEMA


def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TEMA)
    if TIPO_BANCO == "postgres" and not CONEXAO_PATH.exists():
        if ConfigurarConexao().exec() != QDialog.Accepted:
            sys.exit(0)
    try:
        if not auth().usuario_logado():
            login = Login("")
            if login.exec() != QDialog.Accepted:
                sys.exit(0)
    except ErroConexao as e:
        QMessageBox.critical(None, "Controle Financeiro", str(e))
        sys.exit(1)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())
