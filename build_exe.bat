@echo off
REM Gera ControleFinanceiro.exe (janela sem terminal) e mcp_server.exe (servidor do Claude)
pip install -r requirements.txt pyinstaller
pyinstaller --noconsole --onefile --name ControleFinanceiro iniciar.pyw
pyinstaller --onefile --name mcp_server mcp_server.py
echo.
echo Pronto. Os arquivos estao em dist\
pause
