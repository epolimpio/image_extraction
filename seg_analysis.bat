@echo off

set /p frame="Frame:"%=%
set init_folder=%CD%

set c_folder=D:\image_software\SoftwareC
set config_path=D:\image_software\own\image_extraction\TGMM_configFile.txt

%c_folder:~0,2%

cd %c_folder%\build\nucleiChSvWshedPBC\Release\

ProcessStack.exe %config_path% %frame%

cd %init_folder%

pause
