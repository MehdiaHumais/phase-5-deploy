# PowerShell Installation Script for Todo Chatbot Dependencies
# This script installs all required dependencies for the Todo Chatbot development environment on Windows

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Todo Chatbot Dependencies Installation Script" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Function to check if a command exists
function Test-CommandExists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

# Function to print status
function Write-Status {
    param($message)
    Write-Host "✓ $message" -ForegroundColor Green
}

# Function to print error
function Write-ErrorStatus {
    param($message)
    Write-Host "✗ $message" -ForegroundColor Red
}

# Function to print warning
function Write-WarningStatus {
    param($message)
    Write-Host "⚠ $message" -ForegroundColor Yellow
}

# Function to print info
function Write-Info {
    param($message)
    Write-Host "→ $message" -ForegroundColor White
}

Write-Host "Phase 1: Checking PowerShell Version" -ForegroundColor Yellow
$psVersion = $PSVersionTable.PSVersion
Write-Info "PowerShell Version: $psVersion"

if ($psVersion.Major -lt 5) {
    Write-ErrorStatus "PowerShell 5.1 or higher is required"
    exit 1
} else {
    Write-Status "PowerShell version is sufficient"
}

Write-Host ""
Write-Host "Phase 2: Installing Package Managers (if needed)" -ForegroundColor Yellow

# Check if Chocolatey is installed
if (Test-CommandExists "choco") {
    Write-Status "Chocolatey is already installed"
    $chocoVersion = choco --version
    Write-Info "Chocolatey Version: $chocoVersion"
} else {
    Write-Info "Installing Chocolatey..."
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

    # Add Chocolatey to current session
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

    if (Test-CommandExists "choco") {
        Write-Status "Chocolatey installed successfully"
    } else {
        Write-ErrorStatus "Failed to install Chocolatey"
        exit 1
    }
}

Write-Host ""
Write-Host "Phase 3: Installing Git" -ForegroundColor Yellow

if (Test-CommandExists "git") {
    $gitVersion = git --version
    Write-Status "Git is already installed: $gitVersion"
} else {
    Write-Info "Installing Git..."
    choco install git -y
    Write-Status "Git installed"

    # Add Git to PATH for current session
    $gitPath = "${env:ProgramFiles}\Git\cmd"
    $env:Path += ";$gitPath"
}

Write-Host ""
Write-Host "Phase 4: Installing Python 3.11" -ForegroundColor Yellow

if (Test-CommandExists "python") {
    $pythonVersion = python --version
    Write-Info "Python is already installed: $pythonVersion"

    # Check if version is 3.11.x
    if ($pythonVersion -match "3\.11\.\d+") {
        Write-Status "Python 3.11 is already installed"
    } else {
        Write-WarningStatus "Python version is not 3.11.x. This script will install Python 3.11 alongside existing version."
        Write-Info "Installing Python 3.11..."
        choco install python311 -y
        Write-Status "Python 3.11 installed"
    }
} else {
    Write-Info "Installing Python 3.11..."
    choco install python311 -y
    Write-Status "Python 3.11 installed"
}

# Refresh PATH to include Python
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

Write-Host ""
Write-Host "Phase 5: Installing Node.js and npm" -ForegroundColor Yellow

if (Test-CommandExists "node" -and Test-CommandExists "npm") {
    $nodeVersion = node --version
    $npmVersion = npm --version
    Write-Status "Node.js is already installed: $nodeVersion"
    Write-Status "npm is already installed: $npmVersion"
} else {
    Write-Info "Installing Node.js LTS..."
    choco install nodejs -y
    Write-Status "Node.js installed"
}

Write-Host ""
Write-Host "Phase 6: Installing Docker Desktop" -ForegroundColor Yellow

if (Test-CommandExists "docker") {
    $dockerVersion = docker --version
    Write-Status "Docker is already installed: $dockerVersion"
} else {
    Write-WarningStatus "Docker Desktop requires manual installation:"
    Write-Host "  1. Download Docker Desktop from https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    Write-Host "  2. Install and start Docker Desktop application" -ForegroundColor Yellow
    Write-Host "  3. After installation, please run this script again" -ForegroundColor Yellow
    exit 1
}

# Check if Docker daemon is running
try {
    $dockerInfo = docker info 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Status "Docker daemon is running"
    } else {
        Write-WarningStatus "Docker daemon is not running. Please start Docker Desktop."
        exit 1
    }
} catch {
    Write-WarningStatus "Docker daemon is not running. Please start Docker Desktop."
    exit 1
}

Write-Host ""
Write-Host "Phase 7: Installing Kubernetes CLI (kubectl)" -ForegroundColor Yellow

if (Test-CommandExists "kubectl") {
    $kubectlVersion = kubectl version --client --short
    Write-Status "kubectl is already installed: $kubectlVersion"
} else {
    Write-Info "Installing kubectl..."
    choco install kubernetes-cli -y
    Write-Status "kubectl installed"
}

Write-Host ""
Write-Host "Phase 8: Installing Dapr CLI" -ForegroundColor Yellow

if (Test-CommandExists "dapr") {
    $daprVersion = dapr --version
    Write-Status "Dapr CLI is already installed: $daprVersion"
} else {
    Write-Info "Installing Dapr CLI..."
    # Download and install Dapr CLI
    $daprTempFile = Join-Path $env:TEMP "install-dapr.ps1"
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1" -OutFile $daprTempFile
    & $daprTempFile -DownloadLatest
    Remove-Item $daprTempFile
    Write-Status "Dapr CLI installed"
}

Write-Host ""
Write-Host "Phase 9: Installing Minikube" -ForegroundColor Yellow

if (Test-CommandExists "minikube") {
    $minikubeVersion = minikube version
    Write-Status "Minikube is already installed: $minikubeVersion"
} else {
    Write-Info "Installing Minikube..."
    choco install minikube -y
    Write-Status "Minikube installed"
}

Write-Host ""
Write-Host "Phase 10: Installing Python Dependencies" -ForegroundColor Yellow

$requirementsFile = Join-Path $PWD "requirements.txt"
if (Test-Path $requirementsFile) {
    Write-Info "Installing Python dependencies from requirements.txt..."

    # Check if virtual environment exists
    $venvPath = Join-Path $PWD "venv"
    if (-not (Test-Path $venvPath)) {
        Write-Info "Creating virtual environment..."
        python -m venv venv
        Write-Status "Virtual environment created"
    }

    # Activate virtual environment
    $activateScript = Join-Path $venvPath "Scripts\Activate.ps1"
    if (Test-Path $activateScript) {
        & $activateScript
        Write-Status "Virtual environment activated"
    }

    # Upgrade pip
    python -m pip install --upgrade pip

    # Install requirements
    python -m pip install -r $requirementsFile
    Write-Status "Python dependencies installed"
} else {
    Write-WarningStatus "requirements.txt not found in current directory"
    Write-Host "Please run this script from the project root directory" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Phase 11: Installing Node.js Dependencies" -ForegroundColor Yellow

$packageJsonFile = Join-Path $PWD "package.json"
if (Test-Path $packageJsonFile) {
    Write-Info "Installing Node.js dependencies from package.json..."
    npm install
    Write-Status "Node.js dependencies installed"
} else {
    Write-WarningStatus "package.json not found in current directory"
}

Write-Host ""
Write-Host "Phase 12: Initializing Dapr" -ForegroundColor Yellow

Write-Info "Initializing Dapr runtime..."
dapr init
Write-Status "Dapr initialized"

Write-Host ""
Write-Host "Phase 13: Adding Dapr initialization to setup process" -ForegroundColor Yellow

# Create Dapr components directory
$daprComponentsPath = Join-Path $PWD "dapr\components"
if (-not (Test-Path $daprComponentsPath)) {
    New-Item -ItemType Directory -Path $daprComponentsPath -Force | Out-Null
    Write-Status "Dapr components directory created"
} else {
    Write-Status "Dapr components directory already exists"
}

# Create basic Dapr configuration files
$statestoreContent = @"
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.redis
  version: v1
  metadata:
  - name: redisHost
    value: localhost:6379
  - name: redisPassword
    value: ""
"@

$pubsubContent = @"
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "localhost:9092"
  - name: consumerGroup
    value: "todo-chatbot"
  - name: disableTls
    value: "true"
"@

$statestorePath = Join-Path $daprComponentsPath "statestore.yaml"
$pubsubPath = Join-Path $daprComponentsPath "pubsub.yaml"

Set-Content -Path $statestorePath -Value $statestoreContent
Set-Content -Path $pubsubPath -Value $pubsubContent

Write-Status "Basic Dapr components configured"

Write-Host ""
Write-Host "Phase 14: Adding Kubernetes tools to setup process" -ForegroundColor Yellow

# For Minikube, ensure it's properly configured
if (Test-CommandExists "minikube") {
    Write-Info "Starting Minikube (this may take a few minutes)..."
    # Only start Minikube if it's not already running
    $minikubeStatus = minikube status --format='{{.APIServer}}' 2>$null
    if ($LASTEXITCODE -ne 0 -or $minikubeStatus -ne "Running") {
        minikube start --driver=docker
        Write-Status "Minikube started with Docker driver"
    } else {
        Write-Status "Minikube is already running"
    }

    # Install Dapr to Minikube
    Write-Info "Installing Dapr to Minikube..."
    dapr init -k
    Write-Status "Dapr installed to Minikube"
} else {
    Write-WarningStatus "Minikube not found - skipping Minikube setup"
}

Write-Host ""
Write-Host "Phase 15: Verifying Installation" -ForegroundColor Yellow

$validationScript = Join-Path $PWD "scripts\setup\validate-setup.sh"
if (Test-Path $validationScript) {
    Write-Info "Validation script found. For full validation, run it from Git Bash or WSL."
} else {
    Write-WarningStatus "Validation script not found"
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "INSTALLATION COMPLETE" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "All required dependencies for Todo Chatbot development have been installed!" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Ensure Docker Desktop is running" -ForegroundColor White
Write-Host "2. Start Minikube: minikube start" -ForegroundColor White
Write-Host "3. Follow the quickstart guide in docs/quickstart.md" -ForegroundColor White
Write-Host ""

Write-Host "For local development, you can now run:" -ForegroundColor Yellow
Write-Host "- Start services: docker-compose up -d" -ForegroundColor White
Write-Host "- Run the Todo Chatbot API: dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload" -ForegroundColor White
Write-Host ""

# Create a Windows batch file for quick start
$quickStartScript = @"
@echo off
echo Starting Todo Chatbot development environment...
echo.

echo Starting Docker services...
docker-compose up -d
if errorlevel 1 echo Warning: Docker services failed to start

echo.
echo Starting Todo Chatbot API with Dapr...
start "Todo Chatbot API" cmd /k "dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload"

echo.
echo Development environment started!
echo Open your browser to http://localhost:8000 to access the API
"@

$quickStartPath = Join-Path $PWD "start-dev-environment.bat"
$quickStartScript | Out-File -FilePath $quickStartPath -Encoding ASCII
Write-Status "Quick start batch file created: start-dev-environment.bat"

Write-Host ""
Write-Host "🎉 Todo Chatbot development environment is ready!" -ForegroundColor Green