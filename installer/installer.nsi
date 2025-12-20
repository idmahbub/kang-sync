OutFile "KangAi-Sync-Setup.exe"
InstallDir "$PROGRAMFILES\\KangAiSync"
RequestExecutionLevel admin

Page directory
Page instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "KangAi-Sync.exe"

  CreateDirectory "$INSTDIR\\rsync"
  SetOutPath "$INSTDIR\\rsync"
  File "rsync\\rsync.exe"
  File "rsync\\cygwin1.dll"

  ReadRegStr $0 HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path"
  StrCpy $1 "$0;$INSTDIR;$INSTDIR\\rsync"
  WriteRegExpandStr HKLM "SYSTEM\\CurrentControlSet\\Control\\Session Manager\\Environment" "Path" "$1"
SectionEnd
