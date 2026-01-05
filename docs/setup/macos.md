# macOS Setup Guide for Todo Chatbot

This guide will help you set up the development environment for the Todo Chatbot project on macOS.

## Prerequisites

Before you begin, ensure your system meets the following requirements:

- macOS 10.15 (Catalina) or later
- At least 4GB of free disk space
- Administrator access for installing software
- Terminal access
- Internet connection for downloading dependencies

## Install Homebrew

Homebrew is a package manager for macOS that will help you install the required dependencies:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Install Git

If Git is not already installed:

```bash
brew install git
```

## Install Python 3.9+

Install Python 3.11 using Homebrew:

```bash
brew install python@3.11
```

## Install Node.js

Install Node.js LTS using Homebrew:

```bash
brew install node
```

## Install Docker Desktop

1. Download Docker Desktop for Mac from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. Start Docker Desktop application
4. Wait for it to finish starting up (indicated by the Docker whale in the menu bar)

## Install Kubernetes CLI (kubectl)

```bash
brew install kubectl
```

## Install Dapr CLI

```bash
brew tap dapr/tap
brew install dapr/tap/dapr-cli
```

## Install Minikube

```bash
brew install minikube
```

## Clone the Repository

```bash
git clone https://github.com/your-org/todo-chatbot.git
cd todo-chatbot
```

## Initialize Dapr

```bash
dapr init
```

## Install Python Dependencies

```bash
pip3 install -r requirements.txt
```

## Verify Setup

Run the validation script to ensure everything is properly configured:

```bash
# Make sure you're in the project root directory
cd todo-chatbot

# Make the validation script executable and run it
chmod +x scripts/setup/validate-setup.sh
./scripts/setup/validate-setup.sh
```

## Next Steps

1. Follow the [Architecture Overview](../architecture/overview.md) to understand the system
2. Review the [Quickstart Guide](../quickstart.md) to begin development
3. Check out the [API Documentation](../api.md) for detailed endpoints

## Troubleshooting

### Common Issues

- **Xcode Command Line Tools**: If you encounter issues with Homebrew, install Xcode Command Line Tools first:
  ```bash
  xcode-select --install
  ```
- **Permission errors**: Make sure you have proper permissions for the directories you're working in
- **PATH issues**: Add the Python and Node.js paths to your shell profile (`.zshrc` or `.bash_profile`)

### Getting Help

If you encounter issues not covered here, please check the [Troubleshooting Guide](troubleshooting.md) or reach out to the development team.