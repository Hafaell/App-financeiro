"""Ponto de entrada da interface."""
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtWidgets import QMessageBox

from controle_financeiro.dados.contexto import auth
from controle_financeiro.dados.nuvem import ErroConexao
from controle_financeiro.config import PASTA, TIPO_BANCO
from controle_financeiro.dados.conexao import conexao_configurada
from controle_financeiro.ui.dialogos import ConectarSupabase, Login
from controle_financeiro.ui.janela import Janela
from controle_financeiro.ui.tema import FONTE, carregar_fontes, montar_tema


def caminho_asset(*partes):
    """Acha um arquivo ou pasta de assets: dentro do app empacotado (PyInstaller) ou no projeto."""
    candidatos = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets")
    candidatos.append(Path(__file__).resolve().parents[3] / "assets")
    return next((c.joinpath(*partes) for c in candidatos if c.joinpath(*partes).exists()), None)


def caminho_icone():
    return caminho_asset("icone.png")


def main():
    if sys.platform == "win32":
        try:  # faz a barra de tarefas usar o icone do app (e não o do Python)
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ControleFinanceiro.App")
        except (AttributeError, OSError):
            pass
    app = QApplication(sys.argv)
    icone = caminho_icone()
    if icone:
        app.setWindowIcon(QIcon(str(icone)))  # janela, barra de tarefas e dialogos
    app.setStyle("Fusion")
    if carregar_fontes(caminho_asset("fontes")):  # sem a pasta, fica a Segoe UI do Windows
        fonte = app.font()
        fonte.setFamily(FONTE)
        app.setFont(fonte)
    app.setStyleSheet(montar_tema(PASTA / "tema"))
    if TIPO_BANCO == "postgres" and not conexao_configurada():
        if ConectarSupabase("inicio").exec() != QDialog.Accepted:
            sys.exit(0)
    try:
        # Reabre já logado usando a sessão guardada (refresh token criptografado, sem senha).
        # Só pede e-mail e senha se não houver sessão, ela expirou ou o usuário saiu da conta.
        if not auth().usuario_logado() and not auth().usuario_servico():
            login = Login("")
            if login.exec() != QDialog.Accepted:
                sys.exit(0)
    except ErroConexao as e:
        QMessageBox.critical(None, "Controle Financeiro", str(e))
        sys.exit(1)
    janela = Janela()
    janela.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
