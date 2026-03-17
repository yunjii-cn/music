[Version]
Class=IEXPRESS
SEDVersion=3.00
[Options]
PackagePurpose=InstallApp
ShowInstallProgramWindow=1
HideExtractAnimation=0
UseLongFileName=1
InsideCompressed=0
CAB_FixedSize=0
CAB_ResvCodeSigning=0
RebootMode=N
InstallPrompt=%InstallPrompt%
DisplayLicense=%DisplayLicense%
FinishMessage=%FinishMessage%
TargetName=%TargetName%
FriendlyName=%FriendlyName%
AppLaunched=%AppLaunched%
PostInstallCmd=%PostInstallCmd%
AdminQuietInstCmd=%AdminQuietInstCmd%
UserQuietInstCmd=%UserQuietInstCmd%
SourceFiles=SourceFiles
[Strings]
InstallPrompt=ACE-Step UI 启动器
DisplayLicense=
FinishMessage=ACE-Step UI 启动器已启动！
TargetName=E:\AI应用\qinglong-music-trainer-2.8.3\ACE-Step-UI-启动器.exe
FriendlyName=ACE-Step UI 启动器
AppLaunched=powershell.exe -ExecutionPolicy Bypass -File "start-ace-step-ui.ps1"
PostInstallCmd=
AdminQuietInstCmd=
UserQuietInstCmd=
[SourceFiles]
SourceFiles0=E:\AI应用\qinglong-music-trainer-2.8.3\
[SourceFiles0]
start-ace-step-ui.ps1
1、install-uv-qinglong.ps1
2、run_gradio.ps1
3、run_server.ps1
4、run_npmgui.ps1
