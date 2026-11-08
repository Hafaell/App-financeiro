"""Ponto de entrada da interface."""
import subprocess
import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QDialog
from PySide6.QtWidgets import QMessageBox

from financas.contexto import auth
from financas.nuvem import ErroConexao
from financas.config import PASTA, TIPO_BANCO
from financas.conexao import conexao_configurada
from .dialogos import ConectarSupabase, Login
from .janela import Janela
from .tema import TEMA


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


def main():
    criar_atalhos()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(TEMA)
    if TIPO_BANCO == "postgres" and not conexao_configurada():
        if ConectarSupabase("inicio").exec() != QDialog.Accepted:
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
