; Mergen Download Manager - Modern Inno Setup Script v0.9.5
; Features: FFmpeg auto-install, Browser extension auto-config, Native messaging setup

#define MyAppName "Mergen Download Manager"
#define MyAppVersion "0.9.5"
#define MyAppPublisher "Tunahanyrd"
#define MyAppURL "https://github.com/Tunahanyrd/mergen"
#define MyAppExeName "mergen.exe"
#define ExtensionID "jahgeondjmbcjleahkcmegfenejicoeb"

[Setup]
AppId={{8F9B5C3D-7E2A-4B1C-9D8E-1F2A3B4C5D6E}}
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
OutputBaseFilename=Mergen-{#MyAppVersion}-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
UninstallDisplayIcon={app}\{#MyAppExeName}
UninstallDisplayName={#MyAppName}
VersionInfoVersion={#MyAppVersion}
VersionInfoCompany={#MyAppPublisher}
VersionInfoDescription={#MyAppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Components]
Name: "main"; Description: "Mergen Application"; Types: full compact custom; Flags: fixed
Name: "ffmpeg"; Description: "FFmpeg (Required for HLS/DASH stream downloads)"; Types: full
Name: "browser"; Description: "Browser Extension Auto-Configuration"; Types: full

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1
Name: "autostart"; Description: "Start Mergen on system startup"; GroupDescription: "Startup options:"; Flags: unchecked
Name: "setupchrome"; Description: "Configure Chrome extension"; GroupDescription: "Browser Integration:"; Components: browser
Name: "setupedge"; Description: "Configure Edge extension"; GroupDescription: "Browser Integration:"; Components: browser
Name: "setupbrave"; Description: "Configure Brave extension"; GroupDescription: "Browser Integration:"; Components: browser
Name: "setupfirefox"; Description: "Configure Firefox extension"; GroupDescription: "Browser Integration:"; Components: browser

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
; App settings
Root: HKCU; Subkey: "Software\Mergen"; Flags: uninsdeletekeyifempty
Root: HKCU; Subkey: "Software\Mergen\Settings"; ValueType: string; ValueName: "InstallPath"; ValueData: "{app}"
Root: HKCU; Subkey: "Software\Mergen\Settings"; ValueType: string; ValueName: "Version"; ValueData: "{#MyAppVersion}"

; Auto-startup
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "Mergen"; ValueData: """{app}\{#MyAppExeName}"""; Tasks: autostart; Flags: uninsdeletevalue

; Chrome Native Messaging
Root: HKCU; Subkey: "Software\Google\Chrome\NativeMessagingHosts\com.mergen.native"; ValueType: string; ValueData: "{app}\native-host\com.mergen.native.json"; Tasks: setupchrome; Flags: uninsdeletekey

; Edge Native Messaging
Root: HKCU; Subkey: "Software\Microsoft\Edge\NativeMessagingHosts\com.mergen.native"; ValueType: string; ValueData: "{app}\native-host\com.mergen.native.json"; Tasks: setupedge; Flags: uninsdeletekey

; Brave Native Messaging (uses Chrome registry)
Root: HKCU; Subkey: "Software\Google\Chrome\NativeMessagingHosts\com.mergen.native"; ValueType: string; ValueData: "{app}\native-host\com.mergen.native.json"; Tasks: setupbrave; Flags: uninsdeletekey

; Firefox Native Messaging
Root: HKCU; Subkey: "Software\Mozilla\NativeMessagingHosts\com.mergen.native"; ValueType: string; ValueData: "{app}\native-host\com.mergen.native.json"; Tasks: setupfirefox; Flags: uninsdeletekey

[Code]
var
  FFmpegInstallSuccess: Boolean;
  BrowserConfigPage: TOutputMsgWizardPage;

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

procedure UpdateNativeMessagingManifest;
var
  ManifestPath: String;
  ManifestContent: String;
  AppPath: String;
begin
  ManifestPath := ExpandConstant('{app}\native-host\com.mergen.native.json');
  AppPath := ExpandConstant('{app}\{#MyAppExeName}');
  
  // Escape backslashes for JSON
  StringChangeEx(AppPath, '\', '\\', True);
  
  ManifestContent := '{' + #13#10 +
    '  "name": "com.mergen.native",' + #13#10 +
    '  "description": "Mergen Download Manager Native Messaging Host",' + #13#10 +
    '  "path": "' + AppPath + '",' + #13#10 +
    '  "type": "stdio",' + #13#10 +
    '  "allowed_origins": [' + #13#10 +
    '    "chrome-extension://{#ExtensionID}/"' + #13#10 +
    '  ]' + #13#10 +
    '}';
  
  SaveStringToFile(ManifestPath, ManifestContent, False);
  Log('Native messaging manifest updated: ' + ManifestPath);
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  MessageText: String;
  BrowserMsg: String;
begin
  if CurStep = ssPostInstall then
  begin
    // Update native messaging manifest with actual install path
    if WizardIsComponentSelected('browser') then
    begin
      UpdateNativeMessagingManifest;
      Log('Browser integration configured');
    end;
    
    // FFmpeg installation
    if WizardIsComponentSelected('ffmpeg') then
    begin
      Log('FFmpeg component selected, checking installation...');
      
      if CheckFFmpegInstalled then
      begin
        Log('FFmpeg already installed, skipping.');
        FFmpegInstallSuccess := True;
      end
      else
      begin
        FFmpegInstallSuccess := False;
        
        // Try winget first
        if CheckWingetAvailable then
        begin
          Log('Winget available, attempting install...');
          if InstallFFmpegViaWinget then
          begin
            FFmpegInstallSuccess := True;
            MsgBox('FFmpeg installed successfully!', mbInformation, MB_OK);
          end;
        end;
        
        // Fallback to chocolatey
        if not FFmpegInstallSuccess and CheckChocoAvailable then
        begin
          Log('Trying chocolatey...');
          if InstallFFmpegViaChoco then
          begin
            FFmpegInstallSuccess := True;
            MsgBox('FFmpeg installed successfully via Chocolatey!', mbInformation, MB_OK);
          end;
        end;
        
        // Manual instructions
        if not FFmpegInstallSuccess then
        begin
          MessageText := 'FFmpeg could not be installed automatically.' + #13#10#13#10 +
                        'To enable stream downloads (HLS/DASH), install FFmpeg manually:' + #13#10#13#10 +
                        '1. Open PowerShell as Administrator' + #13#10 +
                        '2. Run: winget install Gyan.FFmpeg' + #13#10#13#10 +
                        'Alternative: Download from https://www.gyan.dev/ffmpeg/builds/';
          
          MsgBox(MessageText, mbInformation, MB_OK);
          Log('FFmpeg auto-install failed, user notified');
        end;
      end;
    end;
  end;
end;

procedure InitializeWizard;
begin
  BrowserConfigPage := CreateOutputMsgPage(wpSelectTasks,
    'Browser Extension Setup', 
    'How to install the browser extension',
    'After installation, follow these steps to install the browser extension:' + #13#10#13#10 +
    '1. Open your browser (Chrome, Edge, Brave, or Firefox)' + #13#10 +
    '2. Navigate to Extensions page:' + #13#10 +
    '   - Chrome: chrome://extensions' + #13#10 +
    '   - Edge: edge://extensions' + #13#10 +
    '   - Brave: brave://extensions' + #13#10 +
    '   - Firefox: about:addons' + #13#10 +
    '3. Enable "Developer mode" (top right)' + #13#10 +
    '4. Click "Load unpacked" (Chrome/Edge/Brave) or "Load Temporary Add-on" (Firefox)' + #13#10 +
    '5. Select folder: ' + ExpandConstant('{app}\browser-extension') + #13#10#13#10 +
    'Native messaging has been configured automatically!');
end;
