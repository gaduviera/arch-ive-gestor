; Arch-Ive Inno Setup 6 installer script
; Build steps:
;   1. Run: pyinstaller ArchIve.spec --noconfirm
;   2. Compile this file with Inno Setup 6 (ISCC.exe)

#define MyAppName "Arch-Ive"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Gabriel Duarte Viera"
#define MyAppURL "https://github.com/gaduviera/arch-ive-gestor"
#define MyAppExeName "ArchIve.exe"

[Setup]
AppId={{1F6DAA2B-6BE7-47A8-A5EA-09E55E56F2E1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Arch-Ive
DefaultGroupName=Arch-Ive
OutputBaseFilename=arch-ive-setup-v1.0.0
OutputDir=output
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\{#MyAppExeName}
; Include the project license when it exists at the repository root.
#ifexist "..\LICENSE"
LicenseFile=..\LICENSE
#endif
MinVersion=10.0

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Additional icons:"; Flags: unchecked

[Files]
Source: "..\dist\ArchIve\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Arch-Ive"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\Arch-Ive"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "Launch Arch-Ive"; Flags: nowait postinstall skipifsilent
