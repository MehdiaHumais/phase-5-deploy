#!/bin/bash

# Installation script for Todo Chatbot dependencies on Linux/macOS
# This script installs all required dependencies for the Todo Chatbot development environment

set -e  # Exit immediately if a command exits with a non-zero status

echo "==========================================="
echo "Todo Chatbot Dependencies Installation Script"
echo "==========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Detect OS
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
else
    echo -e "${RED}Unsupported OS: $OSTYPE${NC}"
    exit 1
fi

echo "Detected OS: $OS"
echo ""

# Function to print status
print_status() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Function to print warning
print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

echo "Phase 1: Installing Package Managers (if needed)"
echo "------------------------------------------------"

# Install Homebrew on macOS if not present
if [ "$OS" = "macos" ] && ! command_exists "brew"; then
    echo "Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

    # Add Homebrew to PATH
    if [[ ":$PATH:" != *":/opt/homebrew/bin:"* ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    print_status "Homebrew installed"
fi

# On Linux, ensure package manager is available
if [ "$OS" = "linux" ]; then
    if command_exists "apt"; then
        PACKAGE_MANAGER="apt"
    elif command_exists "dnf"; then
        PACKAGE_MANAGER="dnf"
    elif command_exists "yum"; then
        PACKAGE_MANAGER="yum"
    else
        print_error "No supported package manager found (apt, dnf, yum)"
        exit 1
    fi
    print_status "Package manager detected: $PACKAGE_MANAGER"
fi

echo ""
echo "Phase 2: Installing Git"
echo "------------------------"

if command_exists "git"; then
    print_status "Git is already installed: $(git --version)"
else
    if [ "$OS" = "macos" ]; then
        brew install git
    else
        if [ "$PACKAGE_MANAGER" = "apt" ]; then
            sudo apt update
            sudo apt install -y git
        elif [ "$PACKAGE_MANAGER" = "dnf" ]; then
            sudo dnf install -y git
        elif [ "$PACKAGE_MANAGER" = "yum" ]; then
            sudo yum install -y git
        fi
    fi
    print_status "Git installed: $(git --version)"
fi

echo ""
echo "Phase 3: Installing Python 3.11"
echo "--------------------------------"

if command_exists "python3.11"; then
    print_status "Python 3.11 is already installed: $(python3.11 --version)"
elif command_exists "python3" && python3 --version 2>&1 | grep -q "3\.11"; then
    print_status "Python 3.11 is already installed: $(python3 --version)"
else
    if [ "$OS" = "macos" ]; then
        brew install python@3.11
    else
        if [ "$PACKAGE_MANAGER" = "apt" ]; then
            sudo apt update
            sudo apt install -y software-properties-common
            sudo add-apt-repository -y ppa:deadsnakes/ppa
            sudo apt update
            sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
        elif [ "$PACKAGE_MANAGER" = "dnf" ]; then
            sudo dnf install -y python3.11 python3.11-pip python3.11-devel
        elif [ "$PACKAGE_MANAGER" = "yum" ]; then
            sudo yum install -y python3.11 python3.11-pip python3.11-devel
        fi
    fi

    # Create python3.11 alias if needed
    if command_exists "python3.11"; then
        print_status "Python 3.11 installed: $(python3.11 --version)"
    elif command_exists "python3"; then
        print_status "Python 3 installed: $(python3 --version)"
    fi
fi

echo ""
echo "Phase 4: Installing Node.js and npm"
echo "------------------------------------"

if command_exists "node" && command_exists "npm"; then
    NODE_VERSION=$(node --version)
    NPM_VERSION=$(npm --version)
    print_status "Node.js is already installed: $NODE_VERSION"
    print_status "npm is already installed: $NPM_VERSION"
else
    if [ "$OS" = "macos" ]; then
        brew install node
    else
        if [ "$PACKAGE_MANAGER" = "apt" ]; then
            curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
            sudo apt-get install -y nodejs
        elif [ "$PACKAGE_MANAGER" = "dnf" ]; then
            sudo dnf module enable -y nodejs:lts
            sudo dnf install -y nodejs
        elif [ "$PACKAGE_MANAGER" = "yum" ]; then
            curl -sL https://rpm.nodesource.com/setup_lts.x | sudo bash -
            sudo yum install -y nodejs
        fi
    fi
    print_status "Node.js installed: $(node --version)"
    print_status "npm installed: $(npm --version)"
fi

echo ""
echo "Phase 5: Installing Docker"
echo "---------------------------"

if command_exists "docker"; then
    DOCKER_VERSION=$(docker --version)
    print_status "Docker is already installed: $DOCKER_VERSION"
else
    print_warning "Docker installation requires manual steps:"
    if [ "$OS" = "macos" ]; then
        echo "  1. Download Docker Desktop from https://www.docker.com/products/docker-desktop"
        echo "  2. Install and start Docker Desktop application"
    else
        echo "  1. For Ubuntu: Follow the official Docker installation guide for Ubuntu"
        echo "  2. For other distributions: Install using your distribution's package manager"
        echo "  3. Start Docker service and add your user to the docker group"
    fi
    echo "  After installation, please restart your terminal and run this script again."
    exit 1
fi

# Check if Docker daemon is running
if docker info >/dev/null 2>&1; then
    print_status "Docker daemon is running"
else
    print_warning "Docker daemon is not running. Please start Docker Desktop/Docker service."
    exit 1
fi

echo ""
echo "Phase 6: Installing Kubernetes CLI (kubectl)"
echo "---------------------------------------------"

if command_exists "kubectl"; then
    KUBECTL_VERSION=$(kubectl version --client --short)
    print_status "kubectl is already installed: $KUBECTL_VERSION"
else
    if [ "$OS" = "macos" ]; then
        brew install kubectl
    else
        if [ "$PACKAGE_MANAGER" = "apt" ]; then
            curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
            sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
        elif [ "$PACKAGE_MANAGER" = "dnf" ]; then
            sudo dnf install -y kubectl
        elif [ "$PACKAGE_MANAGER" = "yum" ]; then
            sudo yum install -y kubectl
        fi
    fi
    print_status "kubectl installed: $(kubectl version --client --short)"
fi

echo ""
echo "Phase 7: Installing Dapr CLI"
echo "-----------------------------"

if command_exists "dapr"; then
    DAPR_VERSION=$(dapr --version)
    print_status "Dapr CLI is already installed: $DAPR_VERSION"
else
    if [ "$OS" = "macos" ]; then
        brew tap dapr/tap
        brew install dapr/tap/dapr-cli
    else
        wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
    fi
    print_status "Dapr CLI installed: $(dapr --version)"
fi

echo ""
echo "Phase 8: Installing Minikube"
echo "-----------------------------"

if command_exists "minikube"; then
    MINIKUBE_VERSION=$(minikube version)
    print_status "Minikube is already installed: $MINIKUBE_VERSION"
else
    if [ "$OS" = "macos" ]; then
        brew install minikube
    else
        if [ "$OS" = "linux" ]; then
            curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
            sudo install minikube-linux-amd64 /usr/local/bin/minikube
        fi
    fi
    print_status "Minikube installed: $(minikube version)"
fi

echo ""
echo "Phase 9: Installing Python Dependencies"
echo "----------------------------------------"

if [ -f "requirements.txt" ]; then
    echo "Installing Python dependencies from requirements.txt..."

    # Check if virtual environment is active
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "Creating and activating virtual environment..."
        python3 -m venv venv
        source venv/bin/activate
        print_status "Virtual environment created and activated"
    fi

    pip install --upgrade pip
    pip install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_warning "requirements.txt not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

echo ""
echo "Phase 10: Installing Node.js Dependencies"
echo "------------------------------------------"

if [ -f "package.json" ]; then
    echo "Installing Node.js dependencies from package.json..."
    npm install
    print_status "Node.js dependencies installed"
else
    print_warning "package.json not found in current directory"
fi

echo ""
echo "Phase 11: Initializing Dapr"
echo "-----------------------------"

echo "Initializing Dapr runtime..."
dapr init
print_status "Dapr initialized"

echo ""
echo "Phase 13: Adding Dapr initialization to setup process"
echo "-----------------------------------------------------"

# Create Dapr components directory
if [ ! -d "./dapr/components" ]; then
    mkdir -p ./dapr/components
    print_status "Dapr components directory created"
else
    print_status "Dapr components directory already exists"
fi

# Create basic Dapr configuration files
cat > ./dapr/components/statestore.yaml << 'EOF'
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
EOF

cat > ./dapr/components/pubsub.yaml << 'EOF'
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
EOF

print_status "Basic Dapr components configured"

echo ""
echo "Phase 14: Adding Kubernetes tools to setup process"
echo "---------------------------------------------------"

# On Linux/macOS, kubectl was already installed in Phase 6
# For Minikube, ensure it's properly configured
if command_exists "minikube"; then
    echo "Starting Minikube (this may take a few minutes)..."
    # Only start Minikube if it's not already running
    if ! minikube status >/dev/null 2>&1; then
        minikube start --driver=docker
        print_status "Minikube started with Docker driver"
    else
        minikube_status=$(minikube status --format='{{.APIServer}}')
        if [ "$minikube_status" = "Running" ]; then
            print_status "Minikube is already running"
        else
            minikube start --driver=docker
            print_status "Minikube started with Docker driver"
        fi
    fi

    # Install Dapr to Minikube
    echo "Installing Dapr to Minikube..."
    dapr init -k
    print_status "Dapr installed to Minikube"
else
    print_warning "Minikube not found - skipping Minikube setup"
fi

echo ""
echo "Phase 15: Verifying Installation"
echo "---------------------------------"

# Run the validation script
if [ -f "scripts/setup/validate-setup.sh" ]; then
    echo "Running validation script..."
    chmod +x scripts/setup/validate-setup.sh
    ./scripts/setup/validate-setup.sh
else
    print_warning "Validation script not found"
fi

echo ""
echo "==========================================="
echo "INSTALLATION COMPLETE"
echo "==========================================="
echo ""
echo "All required dependencies for Todo Chatbot development have been installed!"
echo ""
echo "Next steps:"
echo "1. Ensure Docker Desktop is running"
echo "2. Start Minikube: minikube start"
echo "3. Verify setup: ./scripts/setup/validate-setup.sh"
echo "4. Follow the quickstart guide in docs/quickstart.md"
echo ""
echo "For local development, you can now run:"
echo "- Start services: docker-compose up -d"
echo "- Run the Todo Chatbot API: dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload"
echo ""

# Create a quick start script
cat > start-dev-environment.sh << 'EOF'
#!/bin/bash
# Quick start script for Todo Chatbot development

echo "Starting Todo Chatbot development environment..."

# Start Docker services
echo "Starting Docker services..."
docker-compose up -d

# Start the Todo Chatbot API with Dapr
echo "Starting Todo Chatbot API with Dapr..."
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

echo "Development environment started!"
EOF

chmod +x start-dev-environment.sh
print_status "Quick start script created: start-dev-environment.sh"

echo -e "${GREEN}🎉 Todo Chatbot development environment is ready!${NC}"