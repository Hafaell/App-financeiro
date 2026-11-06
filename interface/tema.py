"""Paleta de cores e folha de estilo (TEMA) do aplicativo."""


AZUL = "#2359D7"


AZUL_TEXTO = "#1B3F9A"


BORDA = "#DCE5F7"


FUNDO = "#EFF3FC"


VERDE_TEXTO = "#1E7A4A"


VERMELHO_TEXTO = "#B5483A"


TEMA = f"""
QWidget {{ background: {FUNDO}; color: #1B2A4A; font-family: "Segoe UI"; font-size: 10pt; }}
QLabel {{ background: transparent; }}
QToolTip {{ background: #1B2A4A; color: #FFFFFF; border: none; padding: 6px 8px; border-radius: 6px; }}

/* lateral */
#lateral {{ background: {AZUL}; }}
#marca {{ color: #FFFFFF; font-size: 17pt; font-weight: 700; padding: 30px 26px 26px 26px;
          background: {AZUL}; }}
#menu {{ background: {AZUL}; border: none; outline: 0; padding: 6px 0; }}
#menu::item {{ color: #DCE6FF; padding: 12px 22px; margin: 2px 14px; border-radius: 10px; }}
#menu::item:hover {{ background: #3A6EE3; }}
#menu::item:selected {{ background: #FFFFFF; color: {AZUL}; font-weight: 600; }}
#conta {{ background: {AZUL}; }}
#contaRotulo {{ color: #BFD0F7; font-size: 9pt; background: transparent; }}
#contaNome {{ color: #FFFFFF; font-size: 12pt; font-weight: 700; background: transparent; }}
#contaBtn {{ background: transparent; color: #FFFFFF; border: 1px solid #8FB0F0;
            border-radius: 10px; padding: 9px 12px; font-weight: 500; }}
#contaBtn:hover {{ background: #3A6EE3; border-color: #FFFFFF; }}

/* textos */
#titulo {{ font-size: 22pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#secao {{ font-size: 13pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#rotulo {{ color: #6B7A99; font-size: 9pt; }}
#valor {{ font-size: 20pt; font-weight: 700; color: {AZUL_TEXTO}; }}
#descricao {{ color: #6B7A99; font-size: 8.5pt; }}
QDialog QLabel {{ color: #1B2A4A; }}

/* cards */
#kpi {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 14px; }}
#kpi_verde {{ background: #E9F9EF; border: 1px solid #A8D8B9; border-radius: 14px; }}
#kpi_verde QLabel#valor {{ color: {VERDE_TEXTO}; }}
#kpi_amarelo {{ background: #FFF9DF; border: 1px solid #E5D897; border-radius: 14px; }}
#kpi_amarelo QLabel#valor {{ color: #6B5B12; }}
#kpi_azul {{ background: #E3EEFF; border: 1px solid #B5C8F5; border-radius: 14px; }}

/* seletor de mês */
#seletor {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 14px; }}
#mesNome {{ font-size: 13pt; font-weight: 700; color: {AZUL_TEXTO}; min-width: 190px; }}
#setaMes {{ padding: 0; border-radius: 10px; }}

/* botões */
QPushButton {{ background: #FFFFFF; color: {AZUL}; border: 1px solid #C9D8F5; border-radius: 10px;
              padding: 9px 18px; font-weight: 600; }}
QPushButton:hover {{ background: #F3F7FF; border-color: {AZUL}; }}
QPushButton:pressed {{ background: #E3EEFF; }}
QPushButton:disabled {{ color: #A7B4CC; border-color: #E3EAF7; }}
QPushButton#primario {{ background: {AZUL}; color: #FFFFFF; border: none; }}
QPushButton#primario:hover {{ background: #1E4EB8; }}
QPushButton#primario:pressed {{ background: #1A43A6; }}

/* campos */
QLineEdit {{ background: #FFFFFF; border: 1px solid #C9D8F5; border-radius: 10px;
            padding: 9px 12px; color: #1B2A4A; selection-background-color: {AZUL}; }}
QLineEdit:hover {{ border-color: #9DB8F2; }}
QLineEdit:focus {{ border: 1px solid {AZUL}; }}
QComboBox {{ background: #FFFFFF; border: 1px solid #C9D8F5; border-radius: 10px;
            padding: 8px 12px; min-width: 150px; color: #1B2A4A; }}
QComboBox:hover {{ border-color: #9DB8F2; }}
QComboBox:focus {{ border: 1px solid {AZUL}; }}
QComboBox::drop-down {{ subcontrol-origin: padding; subcontrol-position: top right;
                       width: 34px; border: none; background: transparent; }}
QComboBox::down-arrow {{ width: 0; height: 0; border-left: 5px solid transparent;
                        border-right: 5px solid transparent; border-top: 6px solid {AZUL};
                        margin-right: 12px; }}
QComboBox QAbstractItemView {{ background: #FFFFFF; border: 1px solid {BORDA}; border-radius: 10px;
                              padding: 6px; selection-background-color: #E3EEFF;
                              selection-color: {AZUL_TEXTO}; outline: 0; }}
QCheckBox {{ spacing: 10px; background: transparent; }}
QCheckBox::indicator {{ width: 18px; height: 18px; border: 1px solid #9DB8F2; border-radius: 6px;
                       background: #FFFFFF; }}
QCheckBox::indicator:hover {{ border-color: {AZUL}; }}
QCheckBox::indicator:checked {{ background: {AZUL}; border-color: {AZUL}; }}

/* tabelas */
QTableWidget {{ background: #FFFFFF; alternate-background-color: #EAF2FF; border: 1px solid {BORDA};
               border-radius: 14px; gridline-color: transparent;
               selection-background-color: #DCE7FB; selection-color: {AZUL_TEXTO}; outline: 0;
               padding: 4px; }}
QHeaderView::section {{ background: #FFFFFF; color: #6B7A99; border: none;
                       border-bottom: 1px solid {BORDA}; padding: 10px 12px;
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
QStatusBar {{ color: #6B7A99; background: {FUNDO}; }}
"""
