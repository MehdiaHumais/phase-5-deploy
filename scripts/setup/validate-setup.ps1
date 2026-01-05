# PowerShell Validation Script for Todo Chatbot Development Environment
# This script checks if all required dependencies are properly installed and configured

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Todo Chatbot Development Environment Setup Validation" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan

# Initialize counters
$totalChecks = 0
$passedChecks = 0

# Function to run a check
function Run-Check {
    param(
        [string]$CheckName,
        [ScriptBlock]$CheckScript
    )

    $totalChecks++
    Write-Host "Checking $CheckName... " -NoNewline

    try {
        $result = & $CheckScript
        if ($result) {
            Write-Host "PASS" -ForegroundColor Green
            $passedChecks++
        } else {
            Write-Host "FAIL" -ForegroundColor Red
        }
    } catch {
        Write-Host "FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Function to check if command exists
function Test-CommandExists {
    param($command)
    $exists = $null -ne (Get-Command $command -ErrorAction SilentlyContinue)
    return $exists
}

Write-Host ""
Write-Host "Phase 1: Basic System Checks" -ForegroundColor Yellow
Write-Host "-----------------------------" -ForegroundColor Yellow

# Check Git
Run-Check "Git installation" {
    if (Test-CommandExists "git") {
        $gitVersion = git --version
        Write-Host "  Git version: $gitVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

# Check Python
Run-Check "Python 3.9+ installation" {
    if (Test-CommandExists "python") {
        $pythonVersion = python --version
        Write-Host "  Python version: $pythonVersion" -ForegroundColor Green
        # Check if version is 3.9 or higher
        if ($pythonVersion -match "Python (\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                return $true
            } else {
                Write-Host "  Warning: Python version is less than 3.9" -ForegroundColor Yellow
                return $false
            }
        }
        return $true
    }
    return $false
}

# Check Node.js
Run-Check "Node.js installation" {
    if (Test-CommandExists "node") {
        $nodeVersion = node --version
        Write-Host "  Node.js version: $nodeVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

# Check npm
Run-Check "npm installation" {
    if (Test-CommandExists "npm") {
        $npmVersion = npm --version
        Write-Host "  npm version: $npmVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

Write-Host ""
Write-Host "Phase 2: Docker and Containerization" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Yellow

# Check Docker
Run-Check "Docker installation" {
    if (Test-CommandExists "docker") {
        $dockerVersion = docker --version
        Write-Host "  Docker version: $dockerVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

# Check if Docker daemon is running
Run-Check "Docker daemon running" {
    try {
        $dockerInfo = docker info 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            return $false
        }
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "Phase 3: Kubernetes and Dapr" -ForegroundColor Yellow
Write-Host "-----------------------------" -ForegroundColor Yellow

# Check kubectl
Run-Check "kubectl installation" {
    if (Test-CommandExists "kubectl") {
        $kubectlVersion = kubectl version --client --short
        Write-Host "  kubectl version: $kubectlVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

# Check Dapr CLI
Run-Check "Dapr CLI installation" {
    if (Test-CommandExists "dapr") {
        $daprVersion = dapr --version
        Write-Host "  Dapr version: $daprVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

# Check Minikube
Run-Check "Minikube installation" {
    if (Test-CommandExists "minikube") {
        $minikubeVersion = minikube version
        Write-Host "  Minikube version: $minikubeVersion" -ForegroundColor Green
        return $true
    }
    return $false
}

Write-Host ""
Write-Host "Phase 4: Development Environment" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor Yellow

# Check if we're in the project directory
if (Test-Path "requirements.txt") {
    Write-Host "requirements.txt found" -ForegroundColor Green
    $totalChecks++
    $passedChecks++
} else {
    Write-Host "requirements.txt not found in current directory" -ForegroundColor Yellow
    $totalChecks++
}

if (Test-Path "package.json") {
    Write-Host "package.json found" -ForegroundColor Green
    $totalChecks++
    $passedChecks++
} else {
    Write-Host "package.json not found in current directory" -ForegroundColor Yellow
    $totalChecks++
}

if (Test-Path "Dockerfile") {
    Write-Host "Dockerfile found" -ForegroundColor Green
    $totalChecks++
    $passedChecks++
} else {
    Write-Host "Dockerfile not found in current directory" -ForegroundColor Yellow
    $totalChecks++
}

if (Test-Path "docker-compose.yml") {
    Write-Host "docker-compose.yml found" -ForegroundColor Green
    $totalChecks++
    $passedChecks++
} else {
    Write-Host "docker-compose.yml not found in current directory" -ForegroundColor Yellow
    $totalChecks++
}

Write-Host ""
Write-Host "Phase 5: Python Dependencies" -ForegroundColor Yellow
Write-Host "-----------------------------" -ForegroundColor Yellow

# Check if virtual environment is activated
if ($env:VIRTUAL_ENV) {
    Write-Host "Python virtual environment is activated" -ForegroundColor Green
    $totalChecks++
    $passedChecks++
} else {
    Write-Host "Python virtual environment is not activated" -ForegroundColor Yellow
    Write-Host "Consider activating a virtual environment before installing Python dependencies" -ForegroundColor Yellow
    $totalChecks++
}

# Check if requirements.txt exists and validate some key dependencies
if (Test-Path "requirements.txt") {
    Run-Check "Key Python dependencies" {
        $depsToCheck = @("fastapi", "uvicorn", "sqlmodel", "aiokafka")
        $allPresent = $true

        foreach ($dep in $depsToCheck) {
            try {
                # Try to import the module
                $result = python -c "import $dep" 2>$null
                if ($LASTEXITCODE -ne 0) {
                    Write-Host "  Missing dependency: $dep" -ForegroundColor Red
                    $allPresent = $false
                }
            } catch {
                Write-Host "  Error checking dependency: $dep" -ForegroundColor Red
                $allPresent = $false
            }
        }

        return $allPresent
    }
} else {
    Write-Host "requirements.txt not found, skipping Python dependencies check" -ForegroundColor Yellow
    $totalChecks++
}

Write-Host ""
Write-Host "Phase 6: Service Readiness Checks" -ForegroundColor Yellow
Write-Host "----------------------------------" -ForegroundColor Yellow

# Check if Docker services can be started
if (Test-Path "docker-compose.yml") {
    Run-Check "docker-compose file validity" {
        try {
            $result = docker-compose config 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $true
            } else {
                # Try alternative command format
                $result = docker compose config 2>$null
                if ($LASTEXITCODE -eq 0) {
                    return $true
                } else {
                    return $false
                }
            }
        } catch {
            return $false
        }
    }
} else {
    Write-Host "docker-compose.yml not found, skipping service check" -ForegroundColor Yellow
    $totalChecks++
}

Write-Host ""
Write-Host "Phase 7: Dapr Readiness" -ForegroundColor Yellow
Write-Host "------------------------" -ForegroundColor Yellow

# Check if Dapr is initialized
Run-Check "Dapr initialization" {
    try {
        $result = dapr status -k 2>$null
        if ($LASTEXITCODE -eq 0) {
            return $true
        } else {
            # Try to check if Dapr is running locally
            $result = dapr list 2>$null
            if ($LASTEXITCODE -eq 0) {
                return $true
            } else {
                return $false
            }
        }
    } catch {
        return $false
    }
}

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Total checks: $totalChecks" -ForegroundColor White
Write-Host "Passed: $passedChecks" -ForegroundColor White
Write-Host "Failed: $($totalChecks - $passedChecks)" -ForegroundColor White
Write-Host ""

if ($passedChecks -eq $totalChecks) {
    Write-Host "🎉 All checks passed! Your development environment is ready." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Yellow
    Write-Host "1. Run 'dapr init' if you haven't already" -ForegroundColor White
    Write-Host "2. Start services with 'docker-compose up -d'" -ForegroundColor White
    Write-Host "3. Follow the quickstart guide in docs/quickstart.md" -ForegroundColor White
    exit 0
} else {
    $failedCount = $totalChecks - $passedChecks
    Write-Host "$failedCount check(s) failed. Please review the output above and fix the issues." -ForegroundColor Red
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "- Install missing software using the setup guides" -ForegroundColor White
    Write-Host "- Restart Docker Desktop if Docker checks failed" -ForegroundColor White
    Write-Host "- Run 'dapr init' to initialize Dapr" -ForegroundColor White
    Write-Host "- Ensure you're in the correct project directory" -ForegroundColor White
    exit 1
}