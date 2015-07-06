@echo off
d:

set /p init_time="Initial Time:"%=%
set /p end_time="End Time:"%=%

cd D:\image_software\SoftwareC\build\nucleiChSvWshedPBC\Release\

ProcessStackBatchMulticore.exe D:\image_software\own\image_extraction\TGMM_configFile.txt %init_time% %end_time%

cd D:\image_software\own\image_extraction

pause