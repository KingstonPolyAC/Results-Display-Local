# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Set the GitHub repository URL
$repoUrl = "https://github.com/redbullsugar3/Athletics-Results-Display.git"

# Set the installation directory
$installDir = "$env:LOCALAPPDATA\GLINTegrate-Results-Display"

# Create the installation directory if it doesn't exist
New-Item -ItemType Directory -Force -Path $installDir

# Change to the installation directory
Set-Location $installDir

# Check if git is installed
if (-not (Test-Command git)) {
    Write-Host "Git is not installed. Please install Git and run this script again."
    exit
}

# Clone the repository
git clone $repoUrl .

# Check if Python is installed
if (-not (Test-Command python)) {
    Write-Host "Python is not installed. Downloading Python 3.11..."
    $pythonUrl = "https://www.python.org/ftp/python/3.11.0/python-3.11.0-amd64.exe"
    $pythonInstaller = "$env:TEMP\python-3.11.0-amd64.exe"
    Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller
    
    Write-Host "Installing Python 3.11..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=1 PrependPath=1" -Wait
    
    # Refresh environment variables
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
}

# Create and activate virtual environment
python -m venv venv
$venvPath = Join-Path $installDir "venv\Scripts\Activate.ps1"
& $venvPath

# Install requirements
if (Test-Path "requirements.txt") {
    Write-Host "Installing required packages..."
    & "$installDir\venv\Scripts\python.exe" -m pip install -r requirements.txt
}

# Create desktop shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:USERPROFILE\Desktop\Launch-GLINTegrate-Display.lnk")
$Shortcut.TargetPath = "$installDir\Launch Results Display.exe"
$Shortcut.Save()

Write-Host "Setup completed successfully!"