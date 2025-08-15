; Inno Setup 安装脚本
; 用于创建COMTRADE波形分析器安装程序

[Setup]
AppName=COMTRADE波形分析器
AppVersion=2.0.0
AppPublisher=电力系统分析工具
AppPublisherURL=http://www.example.com
DefaultDirName={pf}\COMTRADE波形分析器
DefaultGroupName=COMTRADE波形分析器
OutputBaseFilename=COMTRADE波形分析器_Setup_v2.0.0
Compression=lzma2/max
SolidCompression=yes
SetupIconFile=assets\icons\app.ico
UninstallDisplayIcon={app}\COMTRADE波形分析器.exe
VersionInfoVersion=2.0.0
VersionInfoDescription=COMTRADE波形分析器安装程序
ArchitecturesInstallIn64BitMode=x64
DisableProgramGroupPage=yes
LicenseFile=LICENSE.txt

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "quicklaunchicon"; Description: "{cm:CreateQuickLaunchIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked; OnlyBelowVersion: 6.1; Check: not IsAdminInstallMode

[Files]
Source: "dist\COMTRADE波形分析器.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "README.md"; DestDir: "{app}"; Flags: ignoreversion
; 如果有其他文件，添加在这里

[Icons]
Name: "{group}\COMTRADE波形分析器"; Filename: "{app}\COMTRADE波形分析器.exe"
Name: "{group}\卸载 COMTRADE波形分析器"; Filename: "{uninstallexe}"
Name: "{commondesktop}\COMTRADE波形分析器"; Filename: "{app}\COMTRADE波形分析器.exe"; Tasks: desktopicon
Name: "{userappdata}\Microsoft\Internet Explorer\Quick Launch\COMTRADE波形分析器"; Filename: "{app}\COMTRADE波形分析器.exe"; Tasks: quicklaunchicon

[Run]
Filename: "{app}\COMTRADE波形分析器.exe"; Description: "{cm:LaunchProgram,COMTRADE波形分析器}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;