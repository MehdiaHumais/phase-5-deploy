# Windows Setup Guide for Todo Chatbot

This guide will help you set up the development environment for the Todo Chatbot project on Windows.

## Prerequisites

Before you begin, ensure your system meets the following requirements:

- Windows 10 or later (64-bit)
- At least 4GB of free disk space
- Administrator access for installing software
- PowerShell 5.1 or later
- Internet connection for downloading dependencies

## Install Git

1. Download Git for Windows from [https://git-scm.com/download/win](https://git-scm.com/download/win)
2. Run the installer with default settings
3. Restart your terminal to ensure Git is in your PATH

## Install Python 3.9+

1. Download Python 3.11 from [https://www.python.org/downloads/](https://www.python.org/downloads/)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation
4. Verify installation: `python --version`

## Install Node.js

1. Download Node.js LTS from [https://nodejs.org/](https://nodejs.org/)
2. Run the installer with default settings
3. Verify installation: `node --version` and `npm --version`

## Install Docker Desktop

1. Download Docker Desktop for Windows from [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Run the installer
3. Follow the setup wizard (ensure WSL 2 is enabled if on Windows 10)
4. Restart your computer if prompted
5. Start Docker Desktop application

## Install Kubernetes CLI (kubectl)

1. Download kubectl from [https://kubernetes.io/docs/tasks/tools/](https://kubernetes.io/docs/tasks/tools/)
2. Place the executable in your PATH or in a directory that's in your PATH
3. Verify installation: `kubectl version --client`

## Install Dapr CLI

1. Open PowerShell as Administrator
2. Run the following command:
   ```powershell
   wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.ps1 -O install.ps1
   .\install.ps1 -DownloadLatest
   ```
3. Verify installation: `dapr --version`

## Install Minikube

1. Download Minikube installer for Windows from [https://minikube.sigs.k8s.io/docs/start/](https://minikube.sigs.k8s.io/docs/start/)
2. Run the installer
3. Verify installation: `minikube version`

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
pip install -r requirements.txt
```

## Verify Setup

Run the validation script to ensure everything is properly configured:

```bash
# Make sure you're in the project root directory
cd todo-chatbot

# Run the validation script
powershell -File "scripts/setup/validate-setup.ps1"
# Or if using Git Bash:
bash scripts/setup/validate-setup.sh
```

## Next Steps

1. Follow the [Architecture Overview](../architecture/overview.md) to understand the system
2. Review the [Quickstart Guide](../quickstart.md) to begin development
3. Check out the [API Documentation](../api.md) for detailed endpoints

## Troubleshooting

### Common Issues

- **Permission errors**: Ensure you're running PowerShell as Administrator when installing global packages
- **PATH issues**: Restart your terminal after installing new tools to refresh PATH
- **Docker issues**: Ensure Windows features like Hyper-V or WSL 2 are enabled
- **Python version**: Make sure you have Python 3.9+ installed (check with `python --version`)

### Getting Help

If you encounter issues not covered here, please check the [Troubleshooting Guide](troubleshooting.md) or reach out to the development team.