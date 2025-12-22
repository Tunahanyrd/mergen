; Mergen Download Manager - Inno Setup Script
; Creates Windows installer with FFmpeg auto-installation support

#define MyAppName "Mergen Download Manager"
#define MyAppVersion "0.8.0"
#define MyAppPublisher "Tunahanyrd"
#define MyAppURL "https://github.com/Tunahanyrd/mergen"
#define MyAppExeName "mergen.exe"

[Setup]
AppId={{{{8F9B5C3D-7E2A-4B1C-9D8E-1F2A3B4C5D6E}}}}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\Mergen
DefaultGroupName=Mergen
AllowNoIcons=yes
LicenseFile=..\..\LICENSE
OutputDir=Output
OutputBaseFilename=MergenSetup
Compression=lzma
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Components]
Name: "main"; Description: "Mergen Application"; Types: full compact custom; Flags: fixed
Name: "ffmpeg"; Description: "FFmpeg (Required for stream downloads HLS/DASH)"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "..\..\dist\mergen.exe"; DestDir: "{app}"; Flags: ignoreversion; Components: main
Source: "..\..\data\*"; DestDir: "{app}\data"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main
Source: "..\..\browser-extension\*"; DestDir: "{app}\browser-extension"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main
Source: "..\..\native-host\*"; DestDir: "{app}\native-host"; Flags: ignoreversion recursesubdirs createallsubdirs; Components: main

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent

[Registry]
Root: HKCU; Subkey: "Software\Mergen"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Mergen\Settings"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"

[Code]
var
  FFmpegInstallSuccess: Boolean;

function CheckWingetAvailable: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c winget --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function CheckChocoAvailable: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c choco --version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function CheckFFmpegInstalled: Boolean;
var
  ResultCode: Integer;
begin
  Result := Exec('cmd.exe', '/c ffmpeg -version', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
end;

function InstallFFmpegViaWinget: Boolean;
var
  ResultCode: Integer;
begin
  Log('Attempting FFmpeg install via winget...');
  Result := Exec('cmd.exe', '/c winget install --id Gyan.FFmpeg --silent --accept-source-agreements --accept-package-agreements', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if Result then
    Log('FFmpeg installed successfully via winget')
  else
    Log('FFmpeg install via winget failed with code: ' + IntToStr(ResultCode));
end;

function InstallFFmpegViaChoco: Boolean;
var
  ResultCode: Integer;
begin
  Log('Attempting FFmpeg install via chocolatey...');
  Result := Exec('cmd.exe', '/c choco install ffmpeg -y', '', SW_HIDE, ewWaitUntilTerminated, ResultCode) and (ResultCode = 0);
  if Result then
    Log('FFmpeg installed successfully via chocolatey')
  else
    Log('FFmpeg install via chocolatey failed with code: ' + IntToStr(ResultCode));
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  MessageText: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Only attempt FFmpeg installation if user selected the component
    if WizardIsComponentSelected('ffmpeg') then
    begin
      Log('FFmpeg component selected, checking installation...');
      
      // Check if FFmpeg already installed
      if CheckFFmpegInstalled then
      begin
        Log('FFmpeg already installed, skipping.');
        FFmpegInstallSuccess := True;
      end
      else
      begin
        FFmpegInstallSuccess := False;
        
        // Try winget first (modern, built-in to Windows 10+)
        if CheckWingetAvailable then
        begin
          Log('Winget available, attempting install...');
          if InstallFFmpegViaWinget then
          begin
            FFmpegInstallSuccess := True;
            MsgBox('FFmpeg installed successfully via winget!', mbInformation, MB_OK);
          end;
        end;
        
        // If winget failed, try chocolatey
        if not FFmpegInstallSuccess and CheckChocoAvailable then
        begin
          Log('Winget failed or unavailable, trying chocolatey...');
          if InstallFFmpegViaChoco then
          begin
            FFmpegInstallSuccess := True;
            MsgBox('FFmpeg installed successfully via Chocolatey!', mbInformation, MB_OK);
          end;
        end;
        
        // If both failed, show manual instructions
        if not FFmpegInstallSuccess then
        begin
          MessageText := 'FFmpeg could not be installed automatically.' + #13#10#13#10 +
                        'To enable stream downloads (HLS/DASH), please install FFmpeg manually:' + #13#10#13#10 +
                        '1. Open PowerShell as Administrator' + #13#10 +
                        '2. Run: winget install Gyan.FFmpeg' + #13#10#13#10 +
                        'Alternative:' + #13#10 +
                        '• Download from: https://www.gyan.dev/ffmpeg/builds/' + #13#10 +
                        '• Install Chocolatey first, then: choco install ffmpeg';
          
          MsgBox(MessageText, mbInformation, MB_OK);
          Log('FFmpeg auto-install failed, user notified for manual installation');
        end;
      end;
    end
    else
    begin
      Log('FFmpeg component not selected, skipping installation.');
    end;
  end;
end;
