# IICE CRM Upload Script for Windows PowerShell
# This script helps upload your project to the hosting server

Write-Host "IICE CRM Server Upload Script" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Green

# Server details
$SERVER = "da600.is.cc"
$USERNAME = "iqraacad"
$REMOTE_PATH = "/home/iqraacad/public_html/IICE-CRM/"
$LOCAL_PATH = "C:\Users\Afnan Awan\Downloads\CRM\IICE-CRM"

Write-Host "Server: $SERVER" -ForegroundColor Yellow
Write-Host "Username: $USERNAME" -ForegroundColor Yellow
Write-Host "Remote Path: $REMOTE_PATH" -ForegroundColor Yellow
Write-Host "Local Path: $LOCAL_PATH" -ForegroundColor Yellow
Write-Host ""

# Check if we're in the right directory
if (-not (Test-Path $LOCAL_PATH)) {
    Write-Host "Error: Project directory not found at $LOCAL_PATH" -ForegroundColor Red
    Write-Host "Please make sure you're running this script from the correct location." -ForegroundColor Red
    exit 1
}

Write-Host "Choose upload method:" -ForegroundColor Cyan
Write-Host "1. SCP (Secure Copy) - Recommended" -ForegroundColor White
Write-Host "2. Create ZIP file for manual upload" -ForegroundColor White
Write-Host "3. Show manual FTP commands" -ForegroundColor White
Write-Host "4. Exit" -ForegroundColor White
Write-Host ""

$choice = Read-Host "Enter your choice (1-4)"

switch ($choice) {
    "1" {
        Write-Host "Using SCP to upload files..." -ForegroundColor Green
        Write-Host "You will be prompted for the server password: YegDgCkeA6Jjw3VPcFeX" -ForegroundColor Yellow
        Write-Host ""
        
        # Change to parent directory to upload the entire IICE-CRM folder
        Set-Location "C:\Users\Afnan Awan\Downloads\CRM"
        
        # Execute SCP command
        $scpCommand = "scp -r IICE-CRM $USERNAME@${SERVER}:$REMOTE_PATH"
        Write-Host "Executing: $scpCommand" -ForegroundColor Cyan
        
        try {
            Invoke-Expression $scpCommand
            Write-Host "Upload completed successfully!" -ForegroundColor Green
        } catch {
            Write-Host "SCP failed. Make sure you have SCP installed (Git Bash, WSL, or OpenSSH)." -ForegroundColor Red
            Write-Host "Alternative: Use option 2 to create a ZIP file." -ForegroundColor Yellow
        }
    }
    
    "2" {
        Write-Host "Creating ZIP file for manual upload..." -ForegroundColor Green
        
        $zipPath = "C:\Users\Afnan Awan\Downloads\CRM\IICE-CRM.zip"
        
        try {
            # Create ZIP file using PowerShell
            Compress-Archive -Path $LOCAL_PATH -DestinationPath $zipPath -Force
            Write-Host "ZIP file created: $zipPath" -ForegroundColor Green
            Write-Host ""
            Write-Host "Next steps:" -ForegroundColor Cyan
            Write-Host "1. Upload $zipPath via File Manager" -ForegroundColor White
            Write-Host "2. SSH to server and extract:" -ForegroundColor White
            Write-Host "   ssh $USERNAME@$SERVER" -ForegroundColor Gray
            Write-Host "   cd public_html" -ForegroundColor Gray
            Write-Host "   unzip IICE-CRM.zip" -ForegroundColor Gray
        } catch {
            Write-Host "Failed to create ZIP file: $_" -ForegroundColor Red
        }
    }
    
    "3" {
        Write-Host "Manual FTP Commands:" -ForegroundColor Green
        Write-Host "==================" -ForegroundColor Green
        Write-Host ""
        Write-Host "1. Open Command Prompt or PowerShell" -ForegroundColor White
        Write-Host "2. Run: ftp $SERVER" -ForegroundColor Gray
        Write-Host "3. Login with:" -ForegroundColor White
        Write-Host "   Username: $USERNAME" -ForegroundColor Gray
        Write-Host "   Password: YegDgCkeA6Jjw3VPcFeX" -ForegroundColor Gray
        Write-Host "4. Navigate: cd public_html" -ForegroundColor Gray
        Write-Host "5. Create directory: mkdir IICE-CRM" -ForegroundColor Gray
        Write-Host "6. Enter directory: cd IICE-CRM" -ForegroundColor Gray
        Write-Host "7. Upload files: put filename" -ForegroundColor Gray
        Write-Host ""
        Write-Host "Note: FTP requires uploading files one by one." -ForegroundColor Yellow
    }
    
    "4" {
        Write-Host "Exiting..." -ForegroundColor Yellow
        exit 0
    }
    
    default {
        Write-Host "Invalid choice. Please run the script again." -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Upload script completed." -ForegroundColor Green
Write-Host "Press any key to continue..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")