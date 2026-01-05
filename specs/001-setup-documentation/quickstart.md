# Quickstart Guide: Todo Chatbot Development Setup

## Overview
This guide will help you set up your development environment for the Todo Chatbot project with Kafka and Dapr in under 30 minutes.

## Prerequisites
- Git installed (2.30 or higher)
- At least 4GB of free disk space
- Administrator/root access for installing software
- Internet connection for downloading dependencies

## Platform-Specific Setup

### Windows
1. Install Chocolatey package manager (if not already installed):
   ```powershell
   Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
   ```

2. Install required dependencies:
   ```powershell
   choco install docker-desktop kubernetes-cli dapr-cli python nodejs
   ```

3. Restart your terminal to ensure PATH updates take effect.

### macOS
1. Install Homebrew (if not already installed):
   ```bash
   /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
   ```

2. Install required dependencies:
   ```bash
   brew install docker kubernetes-cli
   brew tap dapr/tap
   brew install dapr/tap/dapr-cli
   brew install python@3.9
   brew install node
   ```

### Linux (Ubuntu/Debian)
1. Install required dependencies:
   ```bash
   sudo apt update
   sudo apt install -y git docker.io kubectl python3 nodejs npm
   ```

2. Install Dapr CLI:
   ```bash
   wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
   ```

## Initialize Dapr
After installing the Dapr CLI, initialize it in standalone mode:

```bash
dapr init
```

## Validate Your Setup
Run the following validation script to ensure all dependencies are properly installed:

```bash
# Clone the repository
git clone https://github.com/your-org/todo-chatbot.git
cd todo-chatbot

# Run validation
./scripts/setup/validate-setup.sh
```

## Next Steps
1. Follow the architecture documentation in `docs/architecture/overview.md`
2. Review the API contracts in `specs/001-setup-documentation/contracts/`
3. Start development with the tasks defined in `specs/001-setup-documentation/tasks.md`

## Troubleshooting
If you encounter issues during setup:

1. Check that all dependencies are properly installed:
   ```bash
   git --version
   docker --version
   kubectl version --client
   dapr --version
   python --version
   node --version
   ```

2. Ensure Docker is running and accessible without sudo (Linux):
   ```bash
   sudo usermod -aG docker $USER
   # Log out and log back in for changes to take effect
   ```

3. If Dapr fails to initialize, try:
   ```bash
   dapr uninstall --all
   dapr init
   ```

## Support
For additional help, refer to the troubleshooting documentation in `docs/setup/troubleshooting.md` or reach out to the development team.