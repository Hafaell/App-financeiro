"""Paleta de cores e folha de estilo (TEMA) do aplicativo."""


AZUL = "#2359D7"


AZUL_TEXTO = "#1B3F9A"


BORDA = "#DCE5F7"


FUNDO = "#EFF3FC"


TEXTO = "#1B2A4A"


TEXTO_SUAVE = "#6B7A99"


VERDE_TEXTO = "#1E7A4A"


AMARELO_TEXTO = "#B07A00"


VERMELHO_TEXTO = "#B5483A"


TEMA = f"""
QWidget {{ background: {FUNDO}; color: {TEXTO}; font-family: "Segoe UI"; font-size: 10pt; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {TEXTO}; color: #FFFFFF; border: none; padding: 6px 8px; border-radius: 6px; }}
#transparente {{ background: transparent; }}

/* lateral: marca, menu em seções e conta */
#lateral, #lateral QWidget {{ background: {AZUL}; }}
#lateral QLabel#marca {{ color: #FFFFFF; font-size: 16pt; font-weight: 700; padding: 26px 26px 12px 26px; }}
#lateral QLabel#menuSecao {{ color: #B4C8F8; font-size: 8.5pt; font-weight: 600;
                           padding: 14px 12px 4px 9px; }}
#lateral QPushButton#menuItem {{ background: transparent; color: #DCE6FF; border: none;
                                border-radius: 10px; padding: 9px 12px; text-align: left;
                                font-weight: 500; }}
#lateral QPushButton#menuItem:hover {{ background: #3A6EE3; }}
#lateral QPushButton#menuItem:focus {{ background: #3A6EE3; }}
#lateral QPushButton#menuItem:checked {{ background: #FFFFFF; color: {AZUL}; font-weight: 600; }}
#lateral QFrame#contaLinha {{ background: #4B79E6; border: none; }}
#lateral QLabel#contaRotulo {{ color: #BFD0F7; font-size: 9pt; }}
#lateral QLabel#contaNome {{ color: #FFFFFF; font-size: 12pt; font-weight: 700; }}
#lateral QPushButton#contaBtn {{ background: transparent; color: #FFFFFF; border: 1px solid #8FB0F0;
                                border-radius: 10px; padding: 8px 12px; font-weight: 500; }}
#lateral QPushButton#contaBtn:hover, #lateral QPushButton#contaBtn:focus {{
    background: #3A6EE3; border-color: #FFFFFF; }}
#lateral QPushButton#contaLink {{ background: transparent; color: #DCE6FF; border: none;
                                 padding: 4px 0; font-size: 9pt; font-weight: 500; }}
#lateral QPushButton#contaLink:hover, #lateral QPushButton#contaLink:focus {{
    color: #FFFFFF; text-decoration: underline; }}

/* textos */
#titulo {{ font-size: 22pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#secao {{ font-size: 13pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#rotulo {{ color: {TEXTO_SUAVE}; font-size: 9pt; }}
#valor {{ font-size: 20pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#descricao {{ color: {TEXTO_SUAVE}; font-size: 8.5pt; }}
#total {{ font-size: 10.5pt; font-weight: 600; color: {AZUL_TEXTO}; }}
#forte {{ font-weight: 600; }}
#alerta {{ background: #FFF9DF; border: 1px solid #E5D897; border-radius: 10px; padding: 10px 14px;
          color: #6B5B12; font-weight: 600; }}
QDialog QLabel {{ color: {TEXTO}; }}

/* cards */
#kpi {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 14px; }}
#kpi_verde {{ background: #E9F9EF; border: 1px solid #A8D8B9; border-radius: 14px; }}
#kpi_verde QLabel#valor {{ color: {VERDE_TEXTO}; }}
#kpi_amarelo {{ background: #FFF9DF; border: 1px solid #E5D897; border-radius: 14px; }}
#kpi_amarelo QLabel#valor {{ color: #6B5B12; }}
#kpi_azul {{ background: #E3EEFF; border: 1px solid #B5C8F5; border-radius: 14px; }}
#kpi[clicavel="true"]:hover, #kpi_verde[clicavel="true"]:hover,
#kpi_amarelo[clicavel="true"]:hover, #kpi_azul[clicavel="true"]:hover {{ border: 1px solid {AZUL}; }}

/* seletor de mês */
#seletor {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 14px; }}
#mesNome {{ font-size: 13pt; font-weight: 700; color: {AZUL_TEXTO}; min-width: 180px; }}
#setaMes {{ padding: 0; border-radius: 10px; }}

/* botões */
QPushButton {{ background: #FFFFFF; color: {AZUL}; border: 1px solid #C9D8F5; border-radius: 10px;
              padding: 9px 18px; font-weight: 600; }}
QPushButton:hover {{ background: #F3F7FF; border-color: {AZUL}; }}
QPushButton:focus {{ border-color: {AZUL}; }}
QPushButton:pressed {{ background: #E3EEFF; }}
QPushButton:disabled {{ color: #A7B4CC; border-color: #E3EAF7; }}
QPushButton#primario {{ background: {AZUL}; color: #FFFFFF; border: 1px solid {AZUL}; }}
QPushButton#primario:hover {{ background: #1E4EB8; border-color: #1E4EB8; }}
QPushButton#primario:focus {{ border-color: {AZUL_TEXTO}; }}
QPushButton#primario:pressed {{ background: #1A43A6; }}

/* campos */
QLineEdit {{ background: #FFFFFF; border: 1px solid #C9D8F5; border-radius: 10px;
            padding: 9px 12px; color: {TEXTO}; selection-background-color: {AZUL}; }}
QLineEdit:hover {{ border-color: #9DB8F2; }}
QLineEdit:focus {{ border: 1px solid {AZUL}; }}
QComboBox {{ background: #FFFFFF; border: 1px solid #C9D8F5; border-radius: 10px;
            padding: 8px 12px; min-width: 150px; color: {TEXTO}; }}
QComboBox:hover {{ border-color: #9DB8F2; }}
QComboBox:focus {{ border: 1px solid {AZUL}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
                       width: 34px; border: none; background: transparent; }}
QComboBox QAbstractItemView {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 10px;
                              padding: 6px; selection-background-color: #E3EEFF;
                              selection-color: {AZUL_TEXTO}; outline: 0; }}
QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid #9DB8F2; border-radius: 6px;
                       background: #FFFFFF; }}
QCheckBox::indicator:hover {{ border-color: {AZUL}; }}
QCheckBox::indicator:checked {{ background: {AZUL}; border-color: {AZUL}; }}

/* barras de uso (orçamento): azul no normal, amarelo perto do limite, vermelho quando passou */
QProgressBar {{ background: #E3EEFF; border: none; border-radius: 5px; min-height: 10px;
               max-height: 10px; }}
QProgressBar::chunk {{ background: {AZUL}; border-radius: 5px; }}
QProgressBar[nivel="alerta"]::chunk {{ background: {AMARELO_TEXTO}; }}
QProgressBar[nivel="passou"]::chunk {{ background: {VERMELHO_TEXTO}; }}

/* tabelas */
QTableWidget {{ background: #FFFFFF; alternate-background-color: #EAF2FF; border: 1px solid {BORDA};
               border-radius: 14px; gridline-color: transparent;
               selection-background-color: #DCE7FB; selection-color: {AZUL_TEXTO}; outline: 0;
               padding: 4px; }}
QTableWidget:focus {{ border-color: #9DB8F2; }}
QHeaderView {{ background: #FFFFFF; }}
QHeaderView::section {{ background: #FFFFFF; color: {TEXTO_SUAVE}; border: none;
                       border-bottom: 1px solid {BORDA}; padding: 10px 8px;
                       font-size: 9pt; font-weight: 600; }}
QTableCornerButton::section {{ background: #FFFFFF; border: none; }}

/* barras de rolagem: finas e discretas */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #C9D8F5; border-radius: 4px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {AZUL}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: #C9D8F5; border-radius: 4px; min-width: 40px; }}
QScrollBar::handle:horizontal:hover {{ background: {AZUL}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QScrollArea {{ background: transparent; border: none; }}

/* janelas */
QDialog, QMessageBox {{ background: #FFFFFF; }}
QStatusBar {{ color: {TEXTO_SUAVE}; background: {FUNDO}; }}
"""


def montar_tema(pasta):
    """Folha de estilo completa. Além do TEMA, desenha a seta das listas (QComboBox) em
    `pasta`, porque a folha de estilo do Qt só aceita seta vinda de um arquivo de imagem.
    Precisa de um QApplication já criado. Se não der para gravar, as listas ficam sem seta."""
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtGui import QColor, QPainter, QPen, QPixmap

    try:
        pasta.mkdir(parents=True, exist_ok=True)
        for sufixo, escala in (("", 1), ("@2x", 2)):  # @2x: telas com escala acima de 100%
            lado = 12 * escala
            imagem = QPixmap(lado, lado)
            imagem.fill(Qt.GlobalColor.transparent)
            p = QPainter(imagem)
            p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setPen(QPen(QColor(AZUL), 1.8 * escala, Qt.PenStyle.SolidLine,
                          Qt.PenCapStyle.RoundCap, Qt.PenJoinStyle.RoundJoin))
            p.drawPolyline([QPointF(2.5 * escala, 4.5 * escala), QPointF(6 * escala, 8 * escala),
                            QPointF(9.5 * escala, 4.5 * escala)])
            p.end()
            if not imagem.save(str(pasta / f"seta_lista{sufixo}.png")):
                return TEMA
    except OSError:
        return TEMA
    caminho = (pasta / "seta_lista.png").as_posix()
    return TEMA + (f'QComboBox::down-arrow {{ image: url("{caminho}"); width: 12px; height: 12px; '
                   "margin-right: 12px; }\n")
