#define MyAppName "GEBKIM SDS AI Platform"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "GEBKIM"
#define MyAppExeName "GEBKIM_SDS_AI.exe"

[Setup]
AppId={{1E7EBB41-7A96-4C97-8C80-61B80CE1A8C1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}

DefaultDirName={autopf}\GEBKIM SDS AI
DefaultGroupName=GEBKIM SDS AI

OutputDir=output
OutputBaseFilename=GEBKIM_SDS_AI_Setup

Compression=lzma2
SolidCompression=yes

PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

WizardStyle=modern

UninstallDisplayName={#MyAppName}

[Files]
Source: "..\backend\dist\GEBKIM_SDS_AI\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\GEBKIM SDS AI"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\GEBKIM SDS AI"; Filename: "{app}\{#MyAppExeName}"

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "GEBKIM SDS AI Platform'u Aç"; Flags: nowait postinstall skipifsilent