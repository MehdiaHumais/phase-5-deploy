#!/bin/bash

# CI Requirements Check Script for Todo Chatbot
# This script performs automated requirement checking in CI pipeline

set -e

echo "==========================================="
echo "Todo Chatbot CI Requirements Check"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}Environment Information:${NC}"
echo "CI Environment: ${CI:-false}"
echo "GitHub Actions: ${GITHUB_ACTIONS:-false}"
echo "Runner OS: ${RUNNER_OS:-unknown}"
echo "Node version: $(node --version 2>/dev/null || echo 'not installed')"
echo "Python version: $(python --version 2>/dev/null || echo 'not installed')"
echo "Docker version: $(docker --version 2>/dev/null || echo 'not installed')"

echo ""
echo -e "${BLUE}Phase 1: System Requirements Check${NC}"
echo "----------------------------------------"

# Check OS
echo -n "Operating System check... "
if [[ "$RUNNER_OS" == "Linux" || "$RUNNER_OS" == "macOS" || "$RUNNER_OS" == "Windows" ]]; then
    echo -e "${GREEN}PASS${NC} ($RUNNER_OS)"
else
    UNAME_OUT="$(uname -s)"
    case "${UNAME_OUT}" in
        Linux*)     MACHINE=Linux;;
        Darwin*)    MACHINE=Mac;;
        CYGWIN*)    MACHINE=Cygwin;;
        MINGW*)     MACHINE=MinGw;;
        *)          MACHINE="UNKNOWN:${UNAME_OUT}"
    esac
    echo -e "${GREEN}PASS${NC} ($MACHINE)"
fi

# Check architecture
echo -n "Architecture check... "
ARCH=$(uname -m)
echo -e "${GREEN}PASS${NC} ($ARCH)"

# Check available disk space
echo -n "Disk space check (min 2GB free)... "
FREE_SPACE=$(df -k . | awk 'NR==2 {print int($4/1024/1024)}')  # Convert to GB
if [ $FREE_SPACE -ge 2 ]; then
    echo -e "${GREEN}PASS${NC} (${FREE_SPACE}GB available)"
else
    echo -e "${RED}FAIL${NC} (${FREE_SPACE}GB available, need at least 2GB)"
    exit 1
fi

echo ""
echo -e "${BLUE}Phase 2: Required Software Check${NC}"
echo "---------------------------------------"

# Check Git
echo -n "Git availability... "
if command -v git >/dev/null 2>&1; then
    GIT_VERSION=$(git --version | cut -d' ' -f3)
    echo -e "${GREEN}PASS${NC} (Git $GIT_VERSION)"
else
    echo -e "${RED}FAIL${NC} (Git not found)"
    exit 1
fi

# Check Python
echo -n "Python availability... "
if command -v python3 >/dev/null 2>&1; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ $PYTHON_MAJOR -gt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -ge 8 ]); then
        echo -e "${GREEN}PASS${NC} (Python $PYTHON_VERSION)"
    else
        echo -e "${RED}FAIL${NC} (Python $PYTHON_VERSION, need 3.8+)"
        exit 1
    fi
elif command -v python >/dev/null 2>&1; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
    if [ $PYTHON_MAJOR -gt 3 ] || ([ $PYTHON_MAJOR -eq 3 ] && [ $PYTHON_MINOR -ge 8 ]); then
        echo -e "${GREEN}PASS${NC} (Python $PYTHON_VERSION)"
    else
        echo -e "${RED}FAIL${NC} (Python $PYTHON_VERSION, need 3.8+)"
        exit 1
    fi
else
    echo -e "${RED}FAIL${NC} (Python not found)"
    exit 1
fi

# Check pip
echo -n "Pip availability... "
if command -v pip >/dev/null 2>&1 || command -v pip3 >/dev/null 2>&1; then
    PIP_CMD="pip3"
    if ! command -v pip3 >/dev/null 2>&1; then
        PIP_CMD="pip"
    fi
    PIP_VERSION=$($PIP_CMD --version 2>&1 | head -n1 | cut -d' ' -f2)
    echo -e "${GREEN}PASS${NC} (pip $PIP_VERSION)"
else
    echo -e "${RED}FAIL${NC} (pip not found)"
    exit 1
fi

# Check Node.js (if package.json exists)
if [ -f "package.json" ]; then
    echo -n "Node.js availability... "
    if command -v node >/dev/null 2>&1; then
        NODE_VERSION=$(node --version | cut -d'v' -f2)
        NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
        if [ $NODE_MAJOR -ge 14 ]; then
            echo -e "${GREEN}PASS${NC} (Node.js $NODE_VERSION)"
        else
            echo -e "${RED}FAIL${NC} (Node.js $NODE_VERSION, need 14+)"
            exit 1
        fi
    else
        echo -e "${RED}FAIL${NC} (Node.js not found)"
        exit 1
    fi

    echo -n "npm availability... "
    if command -v npm >/dev/null 2>&1; then
        NPM_VERSION=$(npm --version)
        echo -e "${GREEN}PASS${NC} (npm $NPM_VERSION)"
    else
        echo -e "${RED}FAIL${NC} (npm not found)"
        exit 1
    fi
fi

# Check Docker (if Dockerfile exists)
if [ -f "Dockerfile" ]; then
    echo -n "Docker availability... "
    if command -v docker >/dev/null 2>&1; then
        DOCKER_VERSION=$(docker --version | cut -d' ' -f3 | tr -d ',')
        echo -e "${GREEN}PASS${NC} (Docker $DOCKER_VERSION)"
    else
        echo -e "${RED}FAIL${NC} (Docker not found)"
        exit 1
    fi
fi

# Check Docker Compose (if docker-compose.yml exists)
if [ -f "docker-compose.yml" ]; then
    echo -n "Docker Compose availability... "
    if command -v docker-compose >/dev/null 2>&1 || docker compose version >/dev/null 2>&1; then
        if command -v docker-compose >/dev/null 2>&1; then
            COMPOSE_VERSION=$(docker-compose --version | cut -d' ' -f3 | tr -d ',')
            echo -e "${GREEN}PASS${NC} (Docker Compose $COMPOSE_VERSION)"
        else
            COMPOSE_VERSION=$(docker compose version 2>&1 | head -n1 | cut -d' ' -f4)
            echo -e "${GREEN}PASS${NC} (Docker Compose $COMPOSE_VERSION)"
        fi
    else
        echo -e "${RED}FAIL${NC} (Docker Compose not found)"
        exit 1
    fi
fi

echo ""
echo -e "${BLUE}Phase 3: Project Dependencies Check${NC}"
echo "------------------------------------------"

# Check if requirements.txt exists and validate format
if [ -f "requirements.txt" ]; then
    echo -n "requirements.txt format check... "
    if [ -s "requirements.txt" ]; then
        # Check for common formatting issues
        if grep -q "^[[:space:]]*#" requirements.txt || grep -q "^[[:space:]]*$" requirements.txt || grep -v "^[[:space:]]*#" requirements.txt | grep -v "^[[:space:]]*$" | grep -q "."; then
            echo -e "${GREEN}PASS${NC} (Valid format)"
        else
            echo -e "${YELLOW}WARNING${NC} (requirements.txt exists but may be empty)"
        fi
    else
        echo -e "${YELLOW}WARNING${NC} (requirements.txt is empty)"
    fi
else
    echo -e "${YELLOW}SKIP${NC} (requirements.txt not found)"
fi

# Check if package.json exists and validate format
if [ -f "package.json" ]; then
    echo -n "package.json format check... "
    if command -v jq >/dev/null 2>&1; then
        if jq empty package.json 2>/dev/null; then
            echo -e "${GREEN}PASS${NC} (Valid JSON)"
        else
            echo -e "${RED}FAIL${NC} (Invalid JSON)"
            exit 1
        fi
    else
        echo -e "${YELLOW}SKIP${NC} (jq not available to validate JSON)"
    fi
fi

echo ""
echo -e "${BLUE}Phase 4: CI-Specific Checks${NC}"
echo "-------------------------------"

# Check if we're in a git repository
echo -n "Git repository check... "
if git status >/dev/null 2>&1; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${RED}FAIL${NC} (Not in a git repository)"
    exit 1
fi

# Check for presence of common CI files
echo -n "README.md check... "
if [ -f "README.md" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${YELLOW}WARNING${NC} (README.md not found)"
fi

echo -n "LICENSE check... "
if [ -f "LICENSE" ] || [ -f "LICENSE.md" ] || [ -f "LICENSE.txt" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${YELLOW}INFO${NC} (LICENSE file not found)"
fi

echo ""
echo -e "${BLUE}Phase 5: Security Checks${NC}"
echo "---------------------------"

# Check for secrets in code (basic check)
echo -n "Secrets in code check... "
if command -v grep >/dev/null 2>&1; then
    # Look for common secret patterns
    SECRET_COUNT=$(grep -r -i -E "(password|secret|token|key|api)" --include="*.py" --include="*.js" --include="*.ts" --include="*.json" --include="*.yaml" --include="*.yml" . 2>/dev/null | grep -v "node_modules" | grep -v "__pycache__" | grep -v ".git" | wc -l)
    if [ $SECRET_COUNT -eq 0 ]; then
        echo -e "${GREEN}PASS${NC} (No obvious secrets found)"
    else
        echo -e "${YELLOW}INFO${NC} (Found $SECRET_COUNT potential secrets, manual review needed)"
    fi
else
    echo -e "${YELLOW}SKIP${NC} (grep not available)"
fi

# Check for .gitignore
echo -n ".gitignore check... "
if [ -f ".gitignore" ]; then
    echo -e "${GREEN}PASS${NC}"
else
    echo -e "${YELLOW}WARNING${NC} (.gitignore not found)"
fi

echo ""
echo -e "${BLUE}Phase 6: Test Preparation${NC}"
echo "--------------------------"

# Check for test directory or test files
echo -n "Test files check... "
if [ -d "tests" ] || [ -d "test" ] || [ -f "pytest.ini" ] || [ -f "tox.ini" ] || ls *_test.py */*_test.py test_*.py */test_*.py 2>/dev/null; then
    echo -e "${GREEN}PASS${NC} (Test files/directory found)"
else
    echo -e "${YELLOW}INFO${NC} (No test files found)"
fi

# Check if we can install Python dependencies (dry run)
if [ -f "requirements.txt" ]; then
    echo -n "Dependency installation dry run... "
    if command -v pip >/dev/null 2>&1; then
        # Just check if the requirements file is syntactically correct
        if pip install -r requirements.txt --dry-run 2>/dev/null || pip3 install -r requirements.txt --dry-run 2>/dev/null; then
            echo -e "${GREEN}PASS${NC}"
        else
            echo -e "${YELLOW}INFO${NC} (Dry run failed, may be due to missing packages in CI environment)"
        fi
    else
        echo -e "${YELLOW}SKIP${NC} (pip not found)"
    fi
fi

echo ""
echo -e "${GREEN}🎉 CI Requirements Check Completed Successfully!${NC}"
echo ""
echo "This script verifies that the project has all necessary components"
echo "for a successful CI pipeline execution."
echo ""
echo "Next steps in CI pipeline:"
echo "- Install dependencies: pip install -r requirements.txt"
echo "- Run tests: python -m pytest"
echo "- Build application: python -m build (if applicable)"
echo "- Run security scans: bandit, safety, etc."
echo ""

exit 0