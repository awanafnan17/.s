@echo off
REM IICE CRM Upload Script for Windows Command Prompt
REM This script helps upload your project to the hosting server

echo IICE CRM Server Upload Script
echo ================================
echo.

REM Server details
set SERVER=da600.is.cc
set USERNAME=iqraacad
set REMOTE_PATH=/home/iqraacad/public_html/IICE-CRM/
set LOCAL_PATH=C:\Users\Afnan Awan\Downloads\CRM\IICE-CRM

echo Server: %SERVER%
echo Username: %USERNAME%
echo Remote Path: %REMOTE_PATH%
echo Local Path: %LOCAL_PATH%
echo.

REM Check if we're in the right directory
if not exist "%LOCAL_PATH%" (
    echo Error: Project directory not found at %LOCAL_PATH%
    echo Please make sure you're running this script from the correct location.
    pause
    exit /b 1
)

echo Choose upload method:
echo 1. SCP (Secure Copy) - Recommended
echo 2. Create ZIP file for manual upload
echo 3. Show manual FTP commands
echo 4. Exit
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" goto scp_upload
if "%choice%"=="2" goto create_zip
if "%choice%"=="3" goto show_ftp
if "%choice%"=="4" goto exit_script
goto invalid_choice

:scp_upload
echo Using SCP to upload files...
echo You will be prompted for the server password: YegDgCkeA6Jjw3VPcFeX
echo.

REM Change to parent directory to upload the entire IICE-CRM folder
cd /d "C:\Users\Afnan Awan\Downloads\CRM"

REM Execute SCP command
echo Executing: scp -r IICE-CRM %USERNAME%@%SERVER%:%REMOTE_PATH%
scp -r IICE-CRM %USERNAME%@%SERVER%:%REMOTE_PATH%

if %errorlevel% equ 0 (
    echo Upload completed successfully!
) else (
    echo SCP failed. Make sure you have SCP installed (Git Bash, WSL, or OpenSSH).
    echo Alternative: Use option 2 to create a ZIP file.
)
goto end_script

:create_zip
echo Creating ZIP file for manual upload...

set ZIP_PATH=C:\Users\Afnan Awan\Downloads\CRM\IICE-CRM.zip

REM Use PowerShell to create ZIP file
powershell -command "Compress-Archive -Path '%LOCAL_PATH%' -DestinationPath '%ZIP_PATH%' -Force"

if %errorlevel% equ 0 (
    echo ZIP file created: %ZIP_PATH%
    echo.
    echo Next steps:
    echo 1. Upload %ZIP_PATH% via File Manager
    echo 2. SSH to server and extract:
    echo    ssh %USERNAME%@%SERVER%
    echo    cd public_html
    echo    unzip IICE-CRM.zip
) else (
    echo Failed to create ZIP file.
)
goto end_script

:show_ftp
echo Manual FTP Commands:
echo ==================
echo.
echo 1. Open Command Prompt or PowerShell
echo 2. Run: ftp %SERVER%
echo 3. Login with:
echo    Username: %USERNAME%
echo    Password: YegDgCkeA6Jjw3VPcFeX
echo 4. Navigate: cd public_html
echo 5. Create directory: mkdir IICE-CRM
echo 6. Enter directory: cd IICE-CRM
echo 7. Upload files: put filename
echo.
echo Note: FTP requires uploading files one by one.
goto end_script

:invalid_choice
echo Invalid choice. Please run the script again.
goto end_script

:exit_script
echo Exiting...
exit /b 0

:end_script
echo.
echo Upload script completed.
pause