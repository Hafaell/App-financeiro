@echo off
REM Gera o app em modo "pasta" (onedir), que o Windows Defender/SmartScreen barra bem menos
REM do que um .exe unico (onefile), e cria o instalador pronto para enviar.
REM Resultado: dist\ControleFinanceiro\ControleFinanceiro.exe
REM            dist\ControleFinanceiro\servidor_claude\mcp_server.exe  (servidor do Claude)
REM            dist\InstaladorControleFinanceiro.exe  (o que voce abre/envia)
cd /d "%~dp0"
set PYTHONPATH=%CD%\src

REM PyInstaller atualizado: versoes antigas caem mais em listas de bloqueio dos antivirus.
python -m pip install -r requirements.txt
if errorlevel 1 goto erro
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto erro

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM --onedir: nada se auto-extrai em pasta temporaria ao abrir (comportamento que acende alerta).
REM --noupx: nao compacta com UPX (compactadores sao tratados como suspeitos).
python -m PyInstaller --noconfirm --clean --noupx --onedir --noconsole --name ControleFinanceiro --icon assets\icone.ico --version-file assets\versao.txt --add-data "assets\icone.png;assets" --paths src iniciar.pyw
if errorlevel 1 goto erro
python -m PyInstaller --noconfirm --clean --noupx --onedir --icon assets\icone.ico --version-file assets\versao.txt --name mcp_server --paths src src\controle_financeiro\servidor_claude\__main__.py
if errorlevel 1 goto erro

REM O servidor do Claude vai para dentro da pasta do app, para entregar uma pasta so.
move "dist\mcp_server" "dist\ControleFinanceiro\servidor_claude" >nul
if errorlevel 1 goto erro

REM Instalador de um arquivo so (Inno Setup): copia o app, cria atalhos nativos e nao precisa destravar zip.
REM Instale o Inno Setup 6 uma vez: winget install JRSoftware.InnoSetup
set ISCC=
if exist "%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe" set "ISCC=%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
if "%ISCC%"=="" (
    echo Inno Setup nao encontrado. Rode: winget install JRSoftware.InnoSetup
    goto erro
)
"%ISCC%" instalador.iss
if errorlevel 1 goto erro

echo.
echo Pronto. Envie/abra o arquivo dist\InstaladorControleFinanceiro.exe
echo Ele instala o app, cria o atalho na area de trabalho e no menu Iniciar.
echo Se aparecer a tela azul do SmartScreen: "Mais informacoes" ^> "Executar assim mesmo".
echo.
echo Para reduzir ainda mais, envie o .exe como falso positivo em
echo https://www.microsoft.com/wdsi/filesubmission
pause
exit /b 0
:erro
echo.
echo ERRO ao gerar o executavel. Veja a mensagem acima.
pause
exit /b 1
