# Prerequisites for Todo Chatbot Development

This document outlines all the prerequisites needed to set up and run the Todo Chatbot project with Kafka and Dapr.

## System Requirements

### Minimum Hardware Requirements
- **CPU**: 2 cores or more
- **RAM**: 4GB or more (8GB recommended)
- **Storage**: 4GB free disk space (10GB recommended)
- **OS**: Windows 10+, macOS 10.15+, or Linux (Ubuntu 20.04+)

### Network Requirements
- Stable internet connection for initial setup and dependency downloads
- Access to Docker Hub for pulling container images
- Access to package repositories (PyPI, npm)

## Software Dependencies

### Required Software
1. **Git** (2.30 or higher)
   - Version control system
   - Used for cloning the repository and managing code

2. **Python** (3.9 or higher, 3.11 recommended)
   - Backend runtime environment
   - Used for the main Todo Chatbot API

3. **Node.js** (18 or higher)
   - JavaScript runtime environment
   - Used for frontend development and tooling

4. **Docker** (20.10 or higher)
   - Containerization platform
   - Used for running Kafka, database, and other services

5. **Kubernetes CLI (kubectl)**
   - Command-line tool for Kubernetes
   - Used for managing deployments in Kubernetes

6. **Dapr CLI**
   - Command-line tool for Dapr
   - Used for initializing and managing Dapr sidecars

7. **Minikube** (for local development)
   - Local Kubernetes cluster
   - Used for testing Kubernetes deployments locally

### Optional Software (Recommended)
1. **Visual Studio Code** or **IntelliJ IDEA**
   - Code editor with extensions for Python and JavaScript

2. **Postman** or **Insomnia**
   - API testing tools

3. **Lens** or **K9s**
   - Kubernetes management tools

## Version Compatibility Requirements

### Python Dependencies
- **Python**: 3.11 (minimum 3.9)
- **FastAPI**: 0.104.1
- **Uvicorn**: 0.23.2
- **SQLModel**: 0.0.8
- **Aiokafka**: 0.8.0
- **Dapr SDK**: 0.8.0
- **Pydantic**: 2.4.2
- **Passlib**: 1.7.4
- **PyJWT**: 3.3.0

### Node.js Dependencies
- **Node.js**: 18.x or higher (LTS recommended)
- **Express**: 4.18.2
- **KafkaJS**: 2.2.4
- **Dapr Client**: 2.2.0
- **Axios**: 1.5.0
- **Joi**: 17.9.2

### Infrastructure Dependencies
- **Git**: 2.30 or higher
- **Docker**: 20.10.0 or higher
- **Docker Compose**: v2.20.0 or higher
- **Kubernetes CLI (kubectl)**: 1.24 or higher
- **Dapr CLI**: 1.10 or higher
- **Dapr Runtime**: 1.10 or higher
- **Minikube**: 1.28 or higher
- **PostgreSQL**: 14 or higher
- **Redis**: 7.0 or higher
- **Kafka/Redpanda**: Latest stable version

### OS-Specific Requirements
- **Windows**: Windows 10 version 2004 or higher (with WSL2 for Docker)
- **macOS**: 10.15 (Catalina) or higher
- **Linux**: Ubuntu 20.04+, CentOS 8+, or equivalent

### Version Compatibility Requirements by Component
- **API Server**: FastAPI 0.104.1 with Uvicorn 0.23.2
- **Database**: PostgreSQL 14+ with SQLAlchemy/SQLModel
- **Message Queue**: Kafka/Redpanda compatible with aiokafka 0.8.0
- **Caching**: Redis 7.0+ with python-redis client
- **Authentication**: JWT with python-jose and passlib
- **Dapr Runtime**: 1.10+ with Python SDK 0.8.0
- **Frontend (if applicable)**: Node.js 18+ with Express 4.18.2

## Environment Setup

### Environment Variables
The following environment variables should be configured:

```bash
# Database
DATABASE_URL=postgresql://todo_user:todo_pass@localhost:5432/todo_db

# Kafka
KAFKA_BROKERS=localhost:9092

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001

# Application
TODO_CHATBOT_ENV=development
TODO_CHATBOT_PORT=8000
```

### Configuration Files
- `requirements.txt` - Python dependencies
- `package.json` - Node.js dependencies
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Multi-container setup
- `dapr/components/` - Dapr component configurations

## Platform-Specific Notes

### Windows
- Enable WSL 2 or Hyper-V for Docker Desktop
- Use PowerShell as the primary terminal
- Consider using Windows Terminal for better experience

### macOS
- Xcode Command Line Tools are required
- Homebrew is recommended for package management
- Ensure Docker has sufficient resources allocated

### Linux
- Add user to docker group to run Docker without sudo
- Ensure proper file permissions for project directory
- Some distributions may require additional configuration

## Verification Steps

After installing all prerequisites, verify the installation by running:

```bash
# Verify Git
git --version

# Verify Python
python --version

# Verify Node.js
node --version
npm --version

# Verify Docker
docker --version
docker-compose --version

# Verify kubectl
kubectl version --client

# Verify Dapr
dapr --version

# Verify Minikube
minikube version
```

## Next Steps

Once all prerequisites are installed and verified:

1. Proceed with the platform-specific setup guide:
   - [Windows Setup](windows.md)
   - [macOS Setup](macos.md)
   - [Linux Setup](linux.md)

2. Review the [Architecture Overview](../architecture/overview.md)

3. Follow the [Quickstart Guide](../quickstart.md)