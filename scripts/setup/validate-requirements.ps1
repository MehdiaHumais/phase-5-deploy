# PowerShell Requirements Validation Script for Todo Chatbot
# This script validates that system requirements are met

Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Todo Chatbot Requirements Validation" -ForegroundColor Cyan
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

    $global:totalChecks++
    Write-Host "Checking $CheckName... " -NoNewline

    try {
        $result = & $CheckScript
        if ($result) {
            Write-Host "PASS" -ForegroundColor Green
            $global:passedChecks++
        } else {
            Write-Host "FAIL" -ForegroundColor Red
        }
    } catch {
        Write-Host "FAIL" -ForegroundColor Red
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Phase 1: System Resource Requirements" -ForegroundColor Yellow
Write-Host "-------------------------------------" -ForegroundColor Yellow

# Check available disk space (need at least 4GB)
Write-Host "Checking available disk space... " -NoNewline
$drive = Get-PSDrive -Name ([System.IO.Path]::GetPathRoot($PWD)) -PSProvider FileSystem
$freeSpaceGB = [math]::Round($drive.Free / 1GB, 2)
if ($freeSpaceGB -ge 4) {
    Write-Host "PASS" -ForegroundColor Green
    Write-Host "  ($freeSpaceGB GB available)" -ForegroundColor Green
    $passedChecks++
} else {
    Write-Host "FAIL" -ForegroundColor Red
    Write-Host "  ($freeSpaceGB GB available, need at least 4GB)" -ForegroundColor Red
}
$totalChecks++

# Check memory (require at least 4GB)
Write-Host "Checking available memory... " -NoNewline
try {
    $memory = Get-WmiObject -Class Win32_PhysicalMemory | Measure-Object -Property Capacity -Sum
    $totalMemoryGB = [math]::Round($memory.Sum / 1GB, 2)
    if ($totalMemoryGB -ge 4) {
        Write-Host "PASS" -ForegroundColor Green
        Write-Host "  ($totalMemoryGB GB detected)" -ForegroundColor Green
        $passedChecks++
    } else {
        Write-Host "FAIL" -ForegroundColor Red
        Write-Host "  ($totalMemoryGB GB detected, need at least 4GB)" -ForegroundColor Red
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
    Write-Host "  (Could not determine memory: $($_.Exception.Message))" -ForegroundColor Red
}
$totalChecks++

# Check CPU cores (require at least 2)
Write-Host "Checking CPU cores... " -NoNewline
try {
    $cpuCores = (Get-WmiObject -Class Win32_Processor).NumberOfCores | Measure-Object -Sum
    $totalCores = $cpuCores.Sum
    if ($totalCores -ge 2) {
        Write-Host "PASS" -ForegroundColor Green
        Write-Host "  ($totalCores cores detected)" -ForegroundColor Green
        $passedChecks++
    } else {
        Write-Host "FAIL" -ForegroundColor Red
        Write-Host "  ($totalCores cores detected, need at least 2)" -ForegroundColor Red
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
    Write-Host "  (Could not determine CPU cores: $($_.Exception.Message))" -ForegroundColor Red
}
$totalChecks++

Write-Host ""
Write-Host "Phase 2: Software Version Requirements" -ForegroundColor Yellow
Write-Host "--------------------------------------" -ForegroundColor Yellow

# Check Git version (require 2.30+)
Run-Check "Git version (2.30+)" {
    if (Get-Command git -ErrorAction SilentlyContinue) {
        $gitVersion = git --version
        if ($gitVersion -match "git version (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            $patch = [int]$matches[3]
            if ($major -gt 2 -or ($major -eq 2 -and $minor -ge 30)) {
                return $true
            }
        }
    }
    return $false
}

# Check Python version (require 3.9+)
Run-Check "Python version (3.9+)" {
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $pythonVersion = python --version
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                return $true
            }
        }
    }
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonVersion = python3 --version
        if ($pythonVersion -match "Python (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 9)) {
                return $true
            }
        }
    }
    return $false
}

# Check Node.js version (require 18+)
Run-Check "Node.js version (18+)" {
    if (Get-Command node -ErrorAction SilentlyContinue) {
        $nodeVersion = node --version
        if ($nodeVersion -match "v(\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            if ($major -ge 18) {
                return $true
            }
        }
    }
    return $false
}

# Check Docker version (require 20.10+)
Run-Check "Docker version (20.10+)" {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        $dockerVersion = docker --version
        if ($dockerVersion -match "Docker version (\d+)\.(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -gt 20 -or ($major -eq 20 -and $minor -ge 10)) {
                return $true
            }
        }
    }
    return $false
}

Write-Host ""
Write-Host "Phase 3: Network and Connectivity Requirements" -ForegroundColor Yellow
Write-Host "----------------------------------------------" -ForegroundColor Yellow

# Check internet connectivity
Write-Host "Checking internet connectivity... " -NoNewline
try {
    $ping = Test-Connection -ComputerName "8.8.8.8" -Count 1 -Quiet
    if ($ping) {
        Write-Host "PASS" -ForegroundColor Green
        $passedChecks++
    } else {
        Write-Host "FAIL" -ForegroundColor Red
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
}
$totalChecks++

# Check Docker Hub access (requires Docker to be running)
Write-Host "Checking Docker Hub access... " -NoNewline
try {
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        # Test if we can pull a small image
        $result = docker pull hello-world 2>$null
        if ($LASTEXITCODE -eq 0) {
            # Clean up
            docker rmi hello-world 2>$null
            Write-Host "PASS" -ForegroundColor Green
            $passedChecks++
        } else {
            Write-Host "FAIL" -ForegroundColor Red
        }
    } else {
        Write-Host "SKIP" -ForegroundColor Yellow
        Write-Host "  (Docker not found)" -ForegroundColor Yellow
        $passedChecks++  # Count as pass since Docker isn't required at this stage
    }
} catch {
    Write-Host "FAIL" -ForegroundColor Red
}
$totalChecks++

Write-Host ""
Write-Host "Phase 4: Dependency Compatibility" -ForegroundColor Yellow
Write-Host "---------------------------------" -ForegroundColor Yellow

# Function to check if a port is available
function Test-PortAvailability {
    param([int]$Port)

    $tcpConnection = New-Object System.Net.Sockets.TcpClient
    try {
        $tcpConnection.Connect("localhost", $Port)
        $tcpConnection.Close()
        return $false  # Port is in use
    } catch {
        return $true   # Port is available
    }
}

Write-Host "Checking if port 8000 is available... " -NoNewline
if (Test-PortAvailability -Port 8000) {
    Write-Host "PASS" -ForegroundColor Green
    $passedChecks++
} else {
    Write-Host "WARN" -ForegroundColor Yellow
    Write-Host "  (Port 8000 is in use)" -ForegroundColor Yellow
    $passedChecks++  # Count as pass since this is just a warning
}
$totalChecks++

Write-Host "Checking if port 3500 is available... " -NoNewline
if (Test-PortAvailability -Port 3500) {
    Write-Host "PASS" -ForegroundColor Green
    $passedChecks++
} else {
    Write-Host "WARN" -ForegroundColor Yellow
    Write-Host "  (Port 3500 is in use - Dapr HTTP port)" -ForegroundColor Yellow
    $passedChecks++  # Count as pass since this is just a warning
}
$totalChecks++

Write-Host "Checking if port 50001 is available... " -NoNewline
if (Test-PortAvailability -Port 50001) {
    Write-Host "PASS" -ForegroundColor Green
    $passedChecks++
} else {
    Write-Host "WARN" -ForegroundColor Yellow
    Write-Host "  (Port 50001 is in use - Dapr gRPC port)" -ForegroundColor Yellow
    $passedChecks++  # Count as pass since this is just a warning
}
$totalChecks++

Write-Host "Checking if port 9092 is available... " -NoNewline
if (Test-PortAvailability -Port 9092) {
    Write-Host "PASS" -ForegroundColor Green
    $passedChecks++
} else {
    Write-Host "WARN" -ForegroundColor Yellow
    Write-Host "  (Port 9092 is in use - Kafka port)" -ForegroundColor Yellow
    $passedChecks++  # Count as pass since this is just a warning
}
$totalChecks++

Write-Host ""
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "REQUIREMENTS VALIDATION SUMMARY" -ForegroundColor Cyan
Write-Host "===========================================" -ForegroundColor Cyan
Write-Host "Total checks: $totalChecks" -ForegroundColor White
Write-Host "Passed: $passedChecks" -ForegroundColor White
Write-Host "Failed: $($totalChecks - $passedChecks)" -ForegroundColor White
Write-Host ""

if ($passedChecks -eq $totalChecks) {
    Write-Host "🎉 All requirements are met! Your system is ready for Todo Chatbot." -ForegroundColor Green
    exit 0
} else {
    $failedCount = $totalChecks - $passedChecks
    Write-Host "$failedCount requirement(s) not met. Please address the issues above." -ForegroundColor Red

    Write-Host ""
    Write-Host "Important notes:" -ForegroundColor Yellow
    Write-Host "- Minor requirement issues (like port availability) may be acceptable for development" -ForegroundColor White
    Write-Host "- Critical issues (like missing software or insufficient resources) must be resolved" -ForegroundColor White
    exit 1
}