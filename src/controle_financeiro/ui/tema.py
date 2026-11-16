"""Paleta de cores, fonte e folha de estilo (TEMA) do aplicativo.

Direção visual: lateral e painel de saldo em verde petróleo escuro (tinta), fundo claro
levemente esverdeado, ação principal em petróleo e números na fonte Manrope CF, com
algarismos de largura fixa para os valores alinharem nas colunas.
"""

# Fonte da interface (assets/fontes). Sem ela, o Windows usa a Segoe UI.
FONTE = "Manrope CF"

# Base
TINTA = "#123B3A"          # lateral, painel de saldo e títulos
TINTA_CLARA = "#1C4F4D"    # passar o mouse na lateral
MENTA = "#8BE0C9"          # destaque sobre a tinta
FUNDO = "#F2F5F3"
SUPERFICIE = "#FFFFFF"
BORDA = "#DEE6E2"
LINHA = "#EDF2EF"          # separador entre linhas das tabelas
TEXTO = "#15272A"
TEXTO_SUAVE = "#5F706D"

# Ação principal
PRIMARIA = "#0E6B66"
PRIMARIA_ESCURA = "#0A5551"
PRIMARIA_CLARA = "#E2F1EE"

# Significado dos números
VERDE_TEXTO = "#17803D"
AMARELO_TEXTO = "#A35A06"
VERMELHO_TEXTO = "#B42318"
DESPESA = "#E3A13B"        # barras de despesa no comparativo e no painel de saldo

# Nomes antigos, usados em telas que ainda não foram renomeadas
AZUL = PRIMARIA
AZUL_TEXTO = TINTA


TEMA = f"""
QWidget {{ background: {FUNDO}; color: {TEXTO}; font-family: "{FONTE}", "Segoe UI"; font-size: 10pt; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: {TINTA}; color: #FFFFFF; border: none; padding: 6px 9px; border-radius: 6px; }}
#transparente {{ background: transparent; }}

/* ---------- lateral: marca, menu em seções e conta ---------- */
#lateral, #lateral QWidget {{ background: {TINTA}; }}
#lateral QLabel#marcaSelo {{ background: {MENTA}; color: {TINTA}; border-radius: 10px;
                            font-size: 11pt; font-weight: 800; }}
#lateral QLabel#marca {{ color: #FFFFFF; font-size: 12.5pt; font-weight: 800; }}
#lateral QLabel#marcaSub {{ color: #9DBDB6; font-size: 8.5pt; font-weight: 500; }}
#lateral QLabel#menuSecao {{ color: #7FA39C; font-size: 8.5pt; font-weight: 700;
                           padding: 16px 12px 6px 12px; }}
#lateral QPushButton#menuItem {{ background: transparent; color: #C5DAD5; border: none;
                                border-left: 3px solid transparent; border-radius: 8px;
                                padding: 9px 12px; text-align: left; font-weight: 600; }}
#lateral QPushButton#menuItem:hover, #lateral QPushButton#menuItem:focus {{
    background: {TINTA_CLARA}; color: #FFFFFF; }}
#lateral QPushButton#menuItem:checked {{ background: #22605C; color: #FFFFFF;
                                        border-left: 3px solid {MENTA}; }}
#lateral QFrame#contaLinha {{ background: #2A5B58; border: none; }}
#lateral QLabel#contaRotulo {{ color: #8FB2AB; font-size: 8.5pt; }}
#lateral QLabel#contaNome {{ color: #FFFFFF; font-size: 11.5pt; font-weight: 700; }}
#lateral QPushButton#contaBtn {{ background: transparent; color: #FFFFFF; border: 1px solid #3F7570;
                                border-radius: 8px; padding: 8px 12px; font-weight: 600; }}
#lateral QPushButton#contaBtn:hover, #lateral QPushButton#contaBtn:focus {{
    background: {TINTA_CLARA}; border-color: {MENTA}; }}
#lateral QPushButton#contaLink {{ background: transparent; color: #9DBDB6; border: none;
                                 padding: 4px 0; font-size: 9pt; font-weight: 600; }}
#lateral QPushButton#contaLink:hover, #lateral QPushButton#contaLink:focus {{ color: #FFFFFF; }}

/* ---------- textos ---------- */
#titulo {{ font-size: 23pt; font-weight: 800; color: {TINTA}; }}
#secao {{ font-size: 13pt; font-weight: 800; color: {TINTA}; }}
#rotulo {{ color: {TEXTO_SUAVE}; font-size: 9pt; }}
#descricao {{ color: {TEXTO_SUAVE}; font-size: 8.5pt; }}
#total {{ font-size: 10.5pt; font-weight: 700; color: {TINTA}; }}
#forte {{ font-weight: 700; }}
#excedido {{ color: {VERMELHO_TEXTO}; font-size: 9pt; font-weight: 700; }}
#alerta {{ background: #FDF3E1; border: 1px solid #EED7A8; border-radius: 12px; padding: 11px 15px;
          color: #6E4306; font-weight: 600; }}
#tecla {{ background: {FUNDO}; border: 1px solid {BORDA}; border-bottom: 2px solid #CBD6D1;
         border-radius: 6px; padding: 2px 8px; font-size: 9pt; font-weight: 700; color: {TINTA}; }}
QDialog QLabel {{ color: {TEXTO}; }}

/* ---------- painel de saldo (Visão geral): o destaque do app ---------- */
#saldo {{ background: {TINTA}; border-radius: 20px; }}
#saldo QLabel {{ color: #FFFFFF; }}
#saldo QLabel#saldoRotulo {{ color: {MENTA}; font-size: 10pt; font-weight: 700; }}
#saldo QLabel#saldoValor {{ font-size: 34pt; font-weight: 800; }}
#saldo QLabel#saldoValor[negativo="true"] {{ color: #FFB4A8; }}
#saldo QLabel#saldoFrase {{ color: #C5DAD5; font-size: 10pt; }}
#saldo QLabel#fluxoRotulo {{ color: #9DBDB6; font-size: 9pt; font-weight: 600; }}
#saldo QLabel#fluxoValor {{ font-size: 16pt; font-weight: 800; }}
#saldo QFrame#saldoDivisor {{ background: #2A5B58; }}
#saldo #fluxo {{ background: transparent; border-radius: 12px; }}
#saldo #fluxo:hover {{ background: {TINTA_CLARA}; }}

/* ---------- faixa de números: vários valores num painel só ---------- */
#faixa, #painel {{ background: {SUPERFICIE}; border: 1px solid {BORDA}; border-radius: 16px; }}
#faixa QFrame#divisor {{ background: {BORDA}; }}
#metrica {{ background: transparent; border-radius: 12px; }}
#metrica[clicavel="true"]:hover {{ background: #F3F8F6; }}
#metrica QLabel#metricaRotulo {{ color: {TEXTO_SUAVE}; font-size: 9pt; font-weight: 600; }}
#metrica QLabel#metricaValor {{ font-size: 19pt; font-weight: 800; color: {TINTA}; }}
#metrica QLabel#metricaValor[tom="positivo"] {{ color: {VERDE_TEXTO}; }}
#metrica QLabel#metricaValor[tom="aviso"] {{ color: {AMARELO_TEXTO}; }}
#metrica QLabel#metricaValor[tom="negativo"] {{ color: {VERMELHO_TEXTO}; }}
#metrica QLabel#metricaPonto {{ border-radius: 4px; }}
#metrica QLabel#metricaPonto[tom="positivo"] {{ background: {VERDE_TEXTO}; }}
#metrica QLabel#metricaPonto[tom="aviso"] {{ background: {DESPESA}; }}
#metrica QLabel#metricaPonto[tom="negativo"] {{ background: {VERMELHO_TEXTO}; }}
#metrica QLabel#metricaPonto[tom="normal"] {{ background: {PRIMARIA}; }}

/* cards soltos (Ferramentas) */
#kpi {{ background: {SUPERFICIE}; border: 1px solid {BORDA}; border-radius: 16px; }}

/* ---------- seletor de mês ---------- */
#seletor {{ background: {SUPERFICIE}; border: 1px solid {BORDA}; border-radius: 16px; }}
#mesNome {{ font-size: 13pt; font-weight: 800; color: {TINTA}; min-width: 180px; }}
#setaMes {{ padding: 0; border-radius: 10px; }}
QPushButton#voltar {{ border: none; background: transparent; color: {PRIMARIA}; padding: 8px 10px; }}
QPushButton#voltar:hover {{ background: {PRIMARIA_CLARA}; }}
QPushButton#voltar:disabled {{ color: #B3C1BD; background: transparent; }}

/* ---------- botões ---------- */
QPushButton {{ background: {SUPERFICIE}; color: {TINTA}; border: 1px solid #CFDAD6; border-radius: 10px;
              padding: 9px 18px; font-weight: 700; }}
QPushButton:hover {{ background: #F5F9F7; border-color: {PRIMARIA}; color: {PRIMARIA}; }}
QPushButton:focus {{ border-color: {PRIMARIA}; }}
QPushButton:pressed {{ background: {PRIMARIA_CLARA}; }}
QPushButton:disabled {{ color: #A9B7B3; border-color: #E4EBE8; }}
QPushButton#primario {{ background: {PRIMARIA}; color: #FFFFFF; border: 1px solid {PRIMARIA}; }}
QPushButton#primario:hover {{ background: {PRIMARIA_ESCURA}; border-color: {PRIMARIA_ESCURA}; color: #FFFFFF; }}
QPushButton#primario:focus {{ border-color: {TINTA}; }}
QPushButton#primario:pressed {{ background: {TINTA}; }}
QPushButton#perigo {{ color: {VERMELHO_TEXTO}; }}
QPushButton#desfazer {{ background: transparent; border: none; color: {PRIMARIA}; padding: 2px 6px;
                       text-decoration: underline; }}
QPushButton#desfazer:hover {{ background: {PRIMARIA_CLARA}; }}
QPushButton#perigo:hover {{ background: #FDF0EE; border-color: {VERMELHO_TEXTO}; color: {VERMELHO_TEXTO}; }}

/* ---------- campos ---------- */
QLineEdit {{ background: {SUPERFICIE}; border: 1px solid #CFDAD6; border-radius: 10px;
            padding: 9px 12px; color: {TEXTO}; selection-background-color: {PRIMARIA}; }}
QLineEdit:hover {{ border-color: #A7BDB7; }}
QLineEdit:focus {{ border: 1px solid {PRIMARIA}; }}
QComboBox {{ background: {SUPERFICIE}; border: 1px solid #CFDAD6; border-radius: 10px;
            padding: 8px 12px; min-width: 150px; color: {TEXTO}; }}
QComboBox:hover {{ border-color: #A7BDB7; }}
QComboBox:focus {{ border: 1px solid {PRIMARIA}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
                       width: 34px; border: none; background: transparent; }}
QComboBox QAbstractItemView {{ background: {SUPERFICIE}; border: 1px solid {BORDA}; border-radius: 10px;
                              padding: 6px; selection-background-color: {PRIMARIA_CLARA};
                              selection-color: {TINTA}; outline: 0; }}
QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid #A7BDB7; border-radius: 6px;
                       background: {SUPERFICIE}; }}
QCheckBox::indicator:hover {{ border-color: {PRIMARIA}; }}
QCheckBox::indicator:checked {{ background: {PRIMARIA}; border-color: {PRIMARIA}; }}

/* barras de uso (orçamento): petróleo no normal, âmbar perto do limite, vermelho quando passou */
QProgressBar {{ background: #E5ECE9; border: none; border-radius: 4px; min-height: 8px; max-height: 8px; }}
QProgressBar::chunk {{ background: {PRIMARIA}; border-radius: 4px; }}
QProgressBar[nivel="alerta"]::chunk {{ background: {DESPESA}; }}
QProgressBar[nivel="passou"]::chunk {{ background: {VERMELHO_TEXTO}; }}

/* ---------- tabelas: sem listras, com uma linha fina entre os itens ---------- */
QTableWidget {{ background: {SUPERFICIE}; border: 1px solid {BORDA}; border-radius: 16px;
               gridline-color: transparent; selection-background-color: {PRIMARIA_CLARA};
               selection-color: {TINTA}; outline: 0; padding: 4px 6px; }}
QTableWidget:focus {{ border-color: #A7BDB7; }}
QTableWidget::item {{ border-bottom: 1px solid {LINHA}; padding: 0 6px; }}
QTableWidget::item:selected {{ background: {PRIMARIA_CLARA}; color: {TINTA}; }}
QHeaderView {{ background: {SUPERFICIE}; }}
QHeaderView::section {{ background: {SUPERFICIE}; color: {TEXTO_SUAVE}; border: none;
                       border-bottom: 1px solid {BORDA}; padding: 11px 6px;
                       font-size: 9pt; font-weight: 700; }}
QTableCornerButton::section {{ background: {SUPERFICIE}; border: none; }}

/* área de arrastar o extrato */
#zonaArrastar {{ border: 2px dashed #A7BDB7; border-radius: 16px; background: {SUPERFICIE};
                color: {TEXTO_SUAVE}; font-size: 11pt; font-weight: 600; }}
#zonaArrastar:hover {{ border-color: {PRIMARIA}; color: {PRIMARIA}; background: #F7FBFA; }}

/* ---------- barras de rolagem: finas e discretas ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 4px 2px; }}
QScrollBar::handle:vertical {{ background: #C9D6D1; border-radius: 4px; min-height: 40px; }}
QScrollBar::handle:vertical:hover {{ background: {PRIMARIA}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px 4px; }}
QScrollBar::handle:horizontal {{ background: #C9D6D1; border-radius: 4px; min-width: 40px; }}
QScrollBar::handle:horizontal:hover {{ background: {PRIMARIA}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; border: none; background: none; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QScrollArea {{ background: transparent; border: none; }}
#lateral QScrollBar::handle:vertical {{ background: #2F6460; }}

/* ---------- janelas ---------- */
QDialog, QMessageBox {{ background: {SUPERFICIE}; }}
QStatusBar {{ color: {TEXTO_SUAVE}; background: {FUNDO}; }}
"""


def carregar_fontes(pasta):
    """Registra as fontes de `pasta` (arquivos .ttf). Devolve True se a Manrope CF entrou.
    Precisa de um QApplication já criado."""
    from PySide6.QtGui import QFontDatabase

    familias = set()
    for arquivo in sorted(pasta.glob("*.ttf")) if pasta and pasta.exists() else []:
        indice = QFontDatabase.addApplicationFont(str(arquivo))
        if indice >= 0:
            familias.update(QFontDatabase.applicationFontFamilies(indice))
    return FONTE in familias


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
            p.setPen(QPen(QColor(PRIMARIA), 1.8 * escala, Qt.PenStyle.SolidLine,
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
