@echo off
REM Gera ControleFinanceiro.exe (janela sem terminal) e mcp_server.exe (servidor do Claude)
cd /d "%~dp0"
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto erro
python -m PyInstaller --noconsole --onefile --name ControleFinanceiro iniciar.pyw
if errorlevel 1 goto erro
python -m PyInstaller --onefile --name mcp_server mcp_server.py
if errorlevel 1 goto erro
echo.
echo Pronto. Os arquivos estao em dist\
pause
exit /b 0
:erro
echo.
echo ERRO ao gerar o executavel. Veja a mensagem acima.
pause
exit /b 1