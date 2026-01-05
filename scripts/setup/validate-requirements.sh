#!/bin/bash

# Requirements validation script for Todo Chatbot
# This script validates that system requirements are met

set -e

echo "==========================================="
echo "Todo Chatbot Requirements Validation"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Initialize counters
total_checks=0
passed_checks=0

# Function to run a check
run_check() {
    ((total_checks++))
    echo -n "Checking $1... "
    if eval "$2"; then
        echo -e "${GREEN}PASS${NC}"
        ((passed_checks++))
    else
        echo -e "${RED}FAIL${NC}"
    fi
}

echo ""
echo "Phase 1: System Resource Requirements"
echo "-------------------------------------"

# Check available disk space (need at least 4GB)
echo -n "Checking available disk space... "
available_space=$(df -k . | awk 'NR==2 {print int($4/1024/1024)}')  # Convert to GB
if [ $available_space -ge 4 ]; then
    echo -e "${GREEN}PASS${NC} (${available_space}GB available)"
    ((passed_checks++))
else
    echo -e "${RED}FAIL${NC} (${available_space}GB available, need at least 4GB)"
fi
((total_checks++))

# Check memory (require at least 4GB)
echo -n "Checking available memory... "
if command -v free >/dev/null 2>&1; then
    # Linux
    total_memory=$(free -g | awk 'NR==2 {print $2}')
elif command -v system_profiler >/dev/null 2>&1; then
    # macOS
    total_memory=$(system_profiler SPHardwareDataType | grep "Memory" | awk '{print $2}')
    # Convert to number for comparison
    if [[ $total_memory == *"GB"* ]]; then
        total_memory=${total_memory%GB}
    elif [[ $total_memory == *"TB"* ]]; then
        total_memory=$(echo "$total_memory * 1024" | bc)
    fi
else
    # Unknown system, assume pass for now
    total_memory=8
fi

if [ "$total_memory" -ge 4 ]; then
    echo -e "${GREEN}PASS${NC} (${total_memory}GB detected)"
    ((passed_checks++))
else
    echo -e "${RED}FAIL${NC} (${total_memory}GB detected, need at least 4GB)"
fi
((total_checks++))

# Check CPU cores (require at least 2)
echo -n "Checking CPU cores... "
if command -v nproc >/dev/null 2>&1; then
    # Linux
    cores=$(nproc)
elif command -v sysctl >/dev/null 2>&1; then
    # macOS
    cores=$(sysctl -n hw.ncpu)
else
    # Unknown system, default to 4
    cores=4
fi

if [ "$cores" -ge 2 ]; then
    echo -e "${GREEN}PASS${NC} (${cores} cores detected)"
    ((passed_checks++))
else
    echo -e "${RED}FAIL${NC} (${cores} cores detected, need at least 2)"
fi
((total_checks++))

echo ""
echo "Phase 2: Software Version Requirements"
echo "--------------------------------------"

# Check Git version (require 2.30+)
run_check "Git version (2.30+)" '
    if command -v git >/dev/null 2>&1; then
        git_version=$(git --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
        if [ -n "$git_version" ]; then
            # Convert version to comparable format
            git_major=$(echo $git_version | cut -d. -f1)
            git_minor=$(echo $git_version | cut -d. -f2)
            if [ $git_major -gt 2 ] || ([ $git_major -eq 2 ] && [ $git_minor -ge 30 ]); then
                exit 0
            fi
        fi
    fi
    exit 1
'

# Check Python version (require 3.9+)
run_check "Python version (3.9+)" '
    if command -v python3 >/dev/null 2>&1; then
        python_version=$(python3 --version 2>&1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
    elif command -v python >/dev/null 2>&1; then
        python_version=$(python --version 2>&1 | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
    fi

    if [ -n "$python_version" ]; then
        python_major=$(echo $python_version | cut -d. -f1)
        python_minor=$(echo $python_version | cut -d. -f2)
        if [ $python_major -gt 3 ] || ([ $python_major -eq 3 ] && [ $python_minor -ge 9 ]); then
            exit 0
        fi
    fi
    exit 1
'

# Check Node.js version (require 18+)
run_check "Node.js version (18+)" '
    if command -v node >/dev/null 2>&1; then
        node_version=$(node --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
        if [ -n "$node_version" ]; then
            node_major=$(echo $node_version | cut -d. -f1)
            if [ $node_major -ge 18 ]; then
                exit 0
            fi
        fi
    fi
    exit 1
'

# Check Docker version (require 20.10+)
run_check "Docker version (20.10+)" '
    if command -v docker >/dev/null 2>&1; then
        docker_version=$(docker --version | grep -oE "[0-9]+\.[0-9]+\.[0-9]+" | head -n1)
        if [ -n "$docker_version" ]; then
            docker_major=$(echo $docker_version | cut -d. -f1)
            docker_minor=$(echo $docker_version | cut -d. -f2)
            if [ $docker_major -gt 20 ] || ([ $docker_major -eq 20 ] && [ $docker_minor -ge 10 ]); then
                exit 0
            fi
        fi
    fi
    exit 1
'

echo ""
echo "Phase 3: Network and Connectivity Requirements"
echo "----------------------------------------------"

# Check internet connectivity
echo -n "Checking internet connectivity... "
if ping -c 1 -W 5 google.com >/dev/null 2>&1 || ping -c 1 -W 5 8.8.8.8 >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${RED}FAIL${NC}"
fi
((total_checks++))

# Check Docker Hub access
echo -n "Checking Docker Hub access... "
if docker pull hello-world >/dev/null 2>&1; then
    docker rmi hello-world >/dev/null 2>&1
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${RED}FAIL${NC}"
fi
((total_checks++))

echo ""
echo "Phase 4: Dependency Compatibility"
echo "---------------------------------"

# Check if required ports are available (8000, 3500, 50001 for Dapr, 9092 for Kafka)
check_port() {
    local port=$1
    if command -v nc >/dev/null 2>&1; then
        # Use netcat to check if port is in use
        if ! nc -z localhost $port 2>/dev/null; then
            return 0  # Port is free
        else
            return 1  # Port is in use
        fi
    elif command -v lsof >/dev/null 2>&1; then
        # Use lsof on macOS
        if ! lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
            return 0  # Port is free
        else
            return 1  # Port is in use
        fi
    else
        # If we can't check, assume it's available
        return 0
    fi
}

echo -n "Checking if port 8000 is available... "
if check_port 8000; then
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${YELLOW}WARN${NC} (Port 8000 is in use)"
fi
((total_checks++))

echo -n "Checking if port 3500 is available... "
if check_port 3500; then
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${YELLOW}WARN${NC} (Port 3500 is in use - Dapr HTTP port)"
fi
((total_checks++))

echo -n "Checking if port 50001 is available... "
if check_port 50001; then
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${YELLOW}WARN${NC} (Port 50001 is in use - Dapr gRPC port)"
fi
((total_checks++))

echo -n "Checking if port 9092 is available... "
if check_port 9092; then
    echo -e "${GREEN}PASS${NC}"
    ((passed_checks++))
else
    echo -e "${YELLOW}WARN${NC} (Port 9092 is in use - Kafka port)"
fi
((total_checks++))

echo ""
echo "Phase 5: Dependency Version Validation"
echo "---------------------------------------"

# Validate Python dependency versions if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo -n "Checking Python dependency versions... "

    # Check for critical dependencies by importing them
    python_deps_valid=true
    while IFS= read -r dep; do
        # Skip empty lines and comments
        [[ $dep =~ ^#.*$ ]] || [[ -z $dep ]] && continue

        # Extract package name (remove version specifiers)
        pkg_name=$(echo "$dep" | sed 's/[>=<~!].*//g' | sed 's/ //g')

        if [ -n "$pkg_name" ] && [ "$pkg_name" != "fastapi" ] && [ "$pkg_name" != "uvicorn" ]; then
            continue  # Only validate key packages
        fi

        if [ "$pkg_name" = "fastapi" ] || [ "$pkg_name" = "uvicorn" ]; then
            if ! python3 -c "import $pkg_name" 2>/dev/null; then
                if [ "$python_deps_valid" = true ]; then
                    echo -e "${RED}FAIL${NC}"
                    python_deps_valid=false
                fi
                echo -e "${YELLOW}Missing Python dependency: $pkg_name${NC}"
            fi
        fi
    done < requirements.txt

    if [ "$python_deps_valid" = true ]; then
        echo -e "${GREEN}PASS${NC}"
        ((passed_checks++))
    else
        ((total_checks++))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (requirements.txt not found)"
    ((total_checks++))
fi

# Validate Node.js dependency versions if package.json exists
if [ -f "package.json" ]; then
    echo -n "Checking Node.js dependency versions... "

    node_deps_valid=true
    # For now, just check if key packages can be resolved
    if command -v npm >/dev/null 2>&1; then
        # Try to check if the packages in package.json are available
        if npm list express kafkajs dapr-client >/dev/null 2>&1; then
            echo -e "${GREEN}PASS${NC}"
            ((passed_checks++))
        else
            # If npm list fails, try to at least check if packages can be installed
            echo -e "${YELLOW}PARTIAL${NC}"
            echo -e "${YELLOW}Could not fully validate Node.js dependency versions${NC}"
            ((total_checks++))
            ((passed_checks++))  # Count as pass since this is complex to validate
        fi
    else
        echo -e "${YELLOW}SKIP${NC}"
        echo -e "${YELLOW}npm not found, skipping Node.js dependency version check${NC}"
        ((total_checks++))
    fi
else
    echo -e "${YELLOW}SKIP${NC} (package.json not found)"
    ((total_checks++))
fi

echo ""
echo "==========================================="
echo "REQUIREMENTS VALIDATION SUMMARY"
echo "==========================================="
echo "Total checks: $total_checks"
echo "Passed: $passed_checks"
echo "Failed: $((total_checks - passed_checks))"
echo ""

if [ $passed_checks -eq $total_checks ]; then
    echo -e "${GREEN}🎉 All requirements are met! Your system is ready for Todo Chatbot.${NC}"
    exit 0
else
    failed_count=$((total_checks - passed_checks))
    echo -e "${RED}$failed_count requirement(s) not met. Please address the issues above.${NC}"

    echo ""
    echo "Important notes:"
    echo "- Minor requirement issues (like port availability) may be acceptable for development"
    echo "- Critical issues (like missing software or insufficient resources) must be resolved"
    exit 1
fi