; Instalador do Locke. Compile com scripts\build.ps1 (precisa de dist\Locke.exe e dist\LockeService.exe).
#define AppName "Locke"
#define AppVersion "1.0.0"

[Setup]
AppId={{6F1C3C0E-7A52-4C5B-9B1E-4C0C1A0E10C4}
AppName={#AppName}
AppVersion={#AppVersion}
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
PrivilegesRequired=admin
OutputDir=..\dist
OutputBaseFilename=LockeSetup
SetupIconFile=..\icon.ico
UninstallDisplayIcon={app}\Locke.exe
WizardStyle=modern
Compression=lzma2
SolidCompression=yes
ArchitecturesInstallIn64BitMode=x64compatible
DisableProgramGroupPage=yes

[Languages]
Name: "ptbr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Tasks]
Name: "desktopicon"; Description: "Criar um atalho na área de trabalho"; Flags: unchecked

[Files]
Source: "..\dist\Locke.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\LockeService.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{autoprograms}\{#AppName}"; Filename: "{app}\Locke.exe"
Name: "{autodesktop}\{#AppName}"; Filename: "{app}\Locke.exe"; Tasks: desktopicon

[Run]
Filename: "{sys}\sc.exe"; Parameters: "create LockeService binPath= ""{app}\LockeService.exe"" start= auto DisplayName= ""Locke"""; Flags: runhidden; StatusMsg: "Instalando o serviço..."
Filename: "{sys}\sc.exe"; Parameters: "description LockeService ""Bloqueia sites e aplicativos durante as sessões de foco do Locke."""; Flags: runhidden
; Se o processo for encerrado (ex.: Gerenciador de Tarefas), o Windows o reinicia em 1 segundo.
Filename: "{sys}\sc.exe"; Parameters: "failure LockeService reset= 86400 actions= restart/1000/restart/1000/restart/1000/restart/1000"; Flags: runhidden
Filename: "{sys}\sc.exe"; Parameters: "failureflag LockeService 1"; Flags: runhidden
Filename: "{sys}\sc.exe"; Parameters: "start LockeService"; Flags: runhidden
Filename: "{app}\Locke.exe"; Description: "Abrir o Locke"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{sys}\sc.exe"; Parameters: "stop LockeService"; Flags: runhidden; RunOnceId: "StopSvc"
Filename: "{sys}\sc.exe"; Parameters: "delete LockeService"; Flags: runhidden; RunOnceId: "DelSvc"

[Code]
// Reinstalação/atualização: para e remove o serviço antigo antes de copiar os arquivos.
procedure CurStepChanged(CurStep: TSetupStep);
var
  Code: Integer;
begin
  if CurStep = ssInstall then
  begin
    Exec(ExpandConstant('{sys}\sc.exe'), 'stop LockeService', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Sleep(1500);
    Exec(ExpandConstant('{sys}\sc.exe'), 'delete LockeService', '', SW_HIDE, ewWaitUntilTerminated, Code);
    Sleep(500);
  end;
end;
