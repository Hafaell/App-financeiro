; Instalador do Controle Financeiro (Inno Setup 6). Gerado pelo build_exe.bat.
; Instala só para o usuário atual (sem pedir administrador) e cria os atalhos de forma nativa.
[Setup]
AppId={{6F1D0B52-3C1A-4E7B-9A55-B0C4D7E1A2F3}
AppName=Controle Financeiro
AppVersion=2.0.0
AppPublisher=Rafael
DefaultDirName={autopf}\ControleFinanceiro
DefaultGroupName=Controle Financeiro
PrivilegesRequired=lowest
OutputDir=dist
OutputBaseFilename=InstaladorControleFinanceiro
SetupIconFile=assets\icone.ico
UninstallDisplayIcon={app}\ControleFinanceiro.exe
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
DisableProgramGroupPage=yes

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "dist\ControleFinanceiro\*"; DestDir: "{app}"; Flags: recursesubdirs createallsubdirs ignoreversion

[Icons]
Name: "{autodesktop}\Controle Financeiro"; Filename: "{app}\ControleFinanceiro.exe"
Name: "{autoprograms}\Controle Financeiro"; Filename: "{app}\ControleFinanceiro.exe"

[Run]
Filename: "{app}\ControleFinanceiro.exe"; Description: "Abrir o Controle Financeiro"; Flags: nowait postinstall skipifsilent
