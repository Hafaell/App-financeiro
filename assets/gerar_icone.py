"""Desenha o ícone do app (assets/icone.png). Rode: python assets/gerar_icone.py"""
import sys
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt
from PySide6.QtGui import (QBrush, QColor, QGuiApplication, QImage, QLinearGradient, QPainter, QPainterPath,
                           QPen, QPolygonF)

T = 1024


def desenhar(saida):
    img = QImage(T, T, QImage.Format_ARGB32)
    img.fill(Qt.transparent)
    p = QPainter(img)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

    # fundo: quadrado arredondado com degradê azul
    grad = QLinearGradient(0, 0, T, T)
    grad.setColorAt(0, QColor("#3F7BF5"))
    grad.setColorAt(1, QColor("#1B3F9A"))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawRoundedRect(QRectF(32, 32, T - 64, T - 64), 220, 220)

    # três barras brancas crescentes
    p.setBrush(QColor("#FFFFFF"))
    base = 800
    for x, alt in ((210, 210), (430, 340), (650, 470)):
        p.drawRoundedRect(QRectF(x, base - alt, 170, alt), 40, 40)

    # seta verde subindo
    verde = QColor("#34D07F")
    pen = QPen(verde, 56, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin)
    p.setPen(pen)
    p.drawPolyline(QPolygonF([QPointF(220, 470), QPointF(450, 330), QPointF(590, 420), QPointF(780, 235)]))
    # ponta da seta, alinhada com o último trecho da linha
    import math
    ponta = QPointF(850, 165)
    ang = math.atan2(-205, 210)
    def ponto(dist, desvio):
        return QPointF(ponta.x() - dist * math.cos(ang) - desvio * -math.sin(ang),
                       ponta.y() - dist * math.sin(ang) - desvio * math.cos(ang))
    p.setBrush(verde)
    p.setPen(Qt.NoPen)
    p.drawPolygon(QPolygonF([ponta, ponto(150, 85), ponto(150, -85)]))
    p.end()
    img.save(str(saida))




def gerar_ico(png, ico):
    """Monta o icone.ico (PNG embutido em vários tamanhos) a partir do icone.png."""
    import struct
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice
    base = QImage(str(png))
    tamanhos = (16, 24, 32, 48, 64, 128, 256)
    dados = []
    for t in tamanhos:
        dados_buf = QByteArray()
        buf = QBuffer(dados_buf)
        buf.open(QIODevice.WriteOnly)
        base.scaled(t, t, Qt.IgnoreAspectRatio, Qt.SmoothTransformation).save(buf, "PNG")
        buf.close()
        dados.append(bytes(dados_buf))
    cab = struct.pack("<HHH", 0, 1, len(tamanhos))
    pos = 6 + 16 * len(tamanhos)
    entradas = b""
    for t, d in zip(tamanhos, dados):
        entradas += struct.pack("<BBBBHHII", t % 256, t % 256, 0, 0, 1, 32, len(d), pos)
        pos += len(d)
    Path(ico).write_bytes(cab + entradas + b"".join(dados))


if __name__ == "__main__":
    app = QGuiApplication(sys.argv)
    pasta = Path(__file__).parent
    desenhar(pasta / "icone.png")
    gerar_ico(pasta / "icone.png", pasta / "icone.ico")
    print("icone.png e icone.ico gerados em", pasta)

