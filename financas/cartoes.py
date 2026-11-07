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

    @staticmethod
    def _dia(valor, nome):
        if valor in (None, ""):
            return None
        d = int(valor)
        if not 1 <= d <= 31:
            raise ValueError(f"O dia de {nome} precisa estar entre 1 e 31.")
        return d

    def definir_datas(self, id_, fechamento=None, vencimento=None) -> bool:
        """Dia do fechamento e do vencimento da fatura (opcionais)."""
        f = self._dia(fechamento, "fechamento")
        v = self._dia(vencimento, "vencimento")
        _, n = self.banco.gravar("UPDATE cartoes SET dia_fechamento = ?, dia_vencimento = ? WHERE id = ?",
                                 (f, v, int(id_)))
        if n == 0:
            raise ValueError("Cartão não encontrado.")
        return True

    def alertas(self, hoje, dias=5) -> list:
        """Faturas que fecham ou vencem nos próximos 'dias' dias (a partir de 'hoje', um date)."""
        from datetime import timedelta
        import calendar
        saida = []
        for cartao in self.listar():
            for tipo, chave in (("fecha", "dia_fechamento"), ("vence", "dia_vencimento")):
                dia = cartao[chave]
                if not dia:
                    continue
                ultimo = calendar.monthrange(hoje.year, hoje.month)[1]
                alvo = hoje.replace(day=min(dia, ultimo))
                if alvo < hoje:
                    proximo = (hoje.replace(day=1) + timedelta(days=32)).replace(day=1)
                    ultimo2 = calendar.monthrange(proximo.year, proximo.month)[1]
                    alvo = proximo.replace(day=min(dia, ultimo2))
                faltam = (alvo - hoje).days
                if faltam <= dias:
                    saida.append({"cartao": cartao["nome"], "tipo": tipo, "faltam": faltam,
                                  "data": alvo.strftime("%d/%m/%Y")})
        return sorted(saida, key=lambda x: x["faltam"])

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
