# Linux Setup Guide for Todo Chatbot

This guide will help you set up the development environment for the Todo Chatbot project on Linux.

## Prerequisites

Before you begin, ensure your system meets the following requirements:

- Ubuntu 20.04, 22.04 or equivalent distribution
- At least 4GB of free disk space
- Sudo access for installing software
- Terminal access
- Internet connection for downloading dependencies

## Install Git

For Ubuntu/Debian-based systems:

```bash
sudo apt update
sudo apt install -y git
```

For CentOS/RHEL/Fedora:

```bash
sudo dnf install -y git
```

## Install Python 3.9+

For Ubuntu/Debian-based systems:

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip
```

For CentOS/RHEL/Fedora:

```bash
sudo dnf install -y python3 python3-pip python3-devel
```

## Install Node.js

For Ubuntu/Debian-based systems:

```bash
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs
```

For CentOS/RHEL/Fedora:

```bash
sudo dnf module enable nodejs:lts
sudo dnf install -y nodejs
```

## Install Docker

For Ubuntu/Debian-based systems:

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release

sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

For CentOS/RHEL/Fedora:

```bash
sudo dnf -y install dnf-plugins-core
sudo dnf config-manager --add-repo https://download.docker.com/linux/fedora/docker-ce.repo
sudo dnf install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

Start and enable Docker:

```bash
sudo systemctl start docker
sudo systemctl enable docker

# Add your user to the docker group to run Docker without sudo
sudo usermod -aG docker $USER
```

**Note**: Log out and log back in for the group changes to take effect.

## Install Kubernetes CLI (kubectl)

```bash
curl -LO "https://dl.k8s.io/release/$(curl -L -s https://dl.k8s.io/release/stable.txt)/bin/linux/amd64/kubectl"
sudo install -o root -g root -m 0755 kubectl /usr/local/bin/kubectl
```

## Install Dapr CLI

```bash
wget -q https://raw.githubusercontent.com/dapr/cli/master/install/install.sh -O - | /bin/bash
```

## Install Minikube

```bash
curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
sudo install minikube-linux-amd64 /usr/local/bin/minikube
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

- **Docker permission denied**: Make sure to add your user to the docker group and log out/in
- **Python version**: Ensure you have Python 3.9+ installed (check with `python3 --version`)
- **Package manager**: Adjust commands based on your specific Linux distribution

### Getting Help

If you encounter issues not covered here, please check the [Troubleshooting Guide](troubleshooting.md) or reach out to the development team.