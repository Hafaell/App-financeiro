"""Ponto de entrada da interface."""
import subprocess
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
from controle_financeiro.ui.tema import TEMA


def criar_atalhos():
    """Primeira abertura do .exe neste computador: cria atalho na área de trabalho e no menu Iniciar.
    Não faz nada quando o app roda pelo Python (só no .exe)."""
    if not getattr(sys, "frozen", False):
        return
    marcador = PASTA / "atalhos_criados"
    if marcador.exists():
        return
    exe = str(Path(sys.executable).resolve()).replace("'", "''")
    pasta = str(Path(sys.executable).resolve().parent).replace("'", "''")
    script = (
        "$ws = New-Object -ComObject WScript.Shell; "
        "foreach ($pasta in @([Environment]::GetFolderPath('Desktop'), "
        "[Environment]::GetFolderPath('Programs'))) { "
        "$lnk = Join-Path $pasta 'Controle Financeiro.lnk'; "
        f"$s = $ws.CreateShortcut($lnk); $s.TargetPath = '{exe}'; "
        f"$s.WorkingDirectory = '{pasta}'; $s.IconLocation = '{exe},0'; $s.Save() }}"
    )
    try:
        subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
                       creationflags=0x08000000, timeout=30, check=False)  # 0x08000000: sem janela
        marcador.parent.mkdir(parents=True, exist_ok=True)
        marcador.write_text("ok", encoding="utf-8")
    except (OSError, subprocess.SubprocessError):
        pass  # se não der para criar o atalho, o app abre do mesmo jeito


def caminho_icone():
    """Acha o icone.png: dentro do app empacotado (PyInstaller) ou na pasta assets do projeto."""
    candidatos = []
    if getattr(sys, "frozen", False):
        candidatos.append(Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent)) / "assets" / "icone.png")
    candidatos.append(Path(__file__).resolve().parents[3] / "assets" / "icone.png")
    return next((c for c in candidatos if c.exists()), None)


def main():
    criar_atalhos()
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
    app.setStyleSheet(TEMA)
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
