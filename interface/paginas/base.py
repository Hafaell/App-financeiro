"""Base das páginas da interface."""
from PySide6.QtWidgets import QMessageBox, QWidget


class Pagina(QWidget):
    def __init__(self, janela):
        super().__init__()
        self.janela = janela

    def mes(self):
        return self.janela.mes_atual()

    def mudou(self):
        self.janela.atualizar_tudo()

    def erro(self, e):
        QMessageBox.warning(self, "Não consegui salvar", str(e))

    def atualizar(self):
        pass
