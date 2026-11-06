"""Cartões cadastrados (nome e cor do balão)."""
import re


class Cartoes:
    def __init__(self, banco):
        self.banco = banco

    def listar(self):
        return self.banco.consultar("SELECT * FROM cartoes ORDER BY id")

    def canonico(self, nome) -> str:
        """Devolve o nome cadastrado, ignorando maiúsculas, ou levanta erro."""
        alvo = str(nome or "").strip().lower()
        for cartao in self.listar():
            if cartao["nome"].lower() == alvo:
                return cartao["nome"]
        raise ValueError(f"Cartão inválido: '{nome}'. Cadastre o cartão primeiro.")

    def adicionar(self, nome, cor) -> bool:
        nome = str(nome or "").strip()
        if not nome:
            raise ValueError("Informe o nome do cartão.")
        if not re.fullmatch(r"#[0-9A-Fa-f]{6}", str(cor or "")):
            raise ValueError("Escolha uma cor para o cartão.")
        if any(c["nome"].lower() == nome.lower() for c in self.listar()):
            raise ValueError(f"Já existe um cartão chamado {nome}.")
        cor = cor.upper()
        self.banco.gravar("INSERT INTO cartoes (nome, cor, cor_texto) VALUES (?,?,?)",
                          (nome, cor, self.cor_texto(cor)))
        return True

    @staticmethod
    def cor_texto(cor: str) -> str:
        """Letra escura sobre cores claras, branca sobre cores escuras."""
        r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
        luminancia = (0.299 * r + 0.587 * g + 0.114 * b) / 255
        return "#1B2A4A" if luminancia > 0.6 else "#FFFFFF"
