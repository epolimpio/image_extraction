@echo off

set /p init_time="Initial Time:"%=%
set /p end_time="End Time:"%=%
set init_folder=%CD%

set c_folder=D:\image_software\SoftwareC
set config_path=D:\image_software\own\image_extraction\TGMM_configFile.txt

%c_folder:~0,2%

cd %c_folder%\build\nucleiChSvWshedPBC\Release\

ProcessStackBatchMulticore.exe %config_path% %init_time% %end_time%

cd %init_folder%

pause