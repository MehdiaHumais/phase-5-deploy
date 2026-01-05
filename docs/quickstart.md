# Quickstart Guide: Todo Chatbot with Kafka and Dapr

Get up and running with the Todo Chatbot project in minutes.

## Prerequisites

Before starting, ensure you have:
- Git installed
- Docker and Docker Compose
- Python 3.9+ (Python 3.11 recommended)
- Node.js 18+
- Dapr CLI installed and initialized
- At least 4GB of RAM and 4GB of free disk space

## Option 1: Quick Setup with Scripts

### For Linux/macOS:
```bash
# Clone the repository
git clone https://github.com/your-org/todo-chatbot.git
cd todo-chatbot

# Run the installation script
chmod +x scripts/setup/install-dependencies.sh
./scripts/setup/install-dependencies.sh

# Validate your setup
./scripts/setup/validate-setup.sh
```

### For Windows:
```powershell
# Clone the repository
git clone https://github.com/your-org/todo-chatbot.git
cd todo-chatbot

# Run the installation script (in PowerShell as Administrator)
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\setup\install-dependencies.ps1

# Validate your setup
.\scripts\setup\validate-setup.ps1
```

## Option 2: Manual Setup

### 1. Clone the Repository
```bash
git clone https://github.com/your-org/todo-chatbot.git
cd todo-chatbot
```

### 2. Install Python Dependencies
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Install Node.js Dependencies
```bash
npm install
```

### 4. Initialize Dapr
```bash
dapr init
```

### 5. Start Services with Docker Compose
```bash
docker-compose up -d
```

### 6. Run the Todo Chatbot API
```bash
# With Dapr
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

# Or without Dapr (for development)
uvicorn main:app --reload
```

## Running the Application

### Using Docker Compose (Recommended)
```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f api

# Stop services
docker-compose down
```

### Using Dapr CLI
```bash
# Run with Dapr sidecar
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

# Run with Dapr and specific configurations
dapr run --app-id todo-api --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 -- uvicorn main:app --reload
```

## API Endpoints

Once running, the Todo Chatbot API will be available at:
- **Base URL**: `http://localhost:8000`
- **Health Check**: `GET /health`
- **API Documentation**: `GET /docs` (Swagger UI)
- **API Documentation**: `GET /redoc` (ReDoc)

## Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# Database
DATABASE_URL=postgresql://todo_user:todo_pass@localhost:5432/todo_db

# Kafka
KAFKA_BROKERS=localhost:9092

# Redis
REDIS_URL=redis://localhost:6379

# Application
TODO_CHATBOT_ENV=development
TODO_CHATBOT_PORT=8000

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
```

## Dapr Configuration

The project includes Dapr configuration in the `dapr/` directory:

- `dapr/components/` - Dapr component definitions
  - `statestore.yaml` - State management configuration
  - `pubsub.yaml` - Pub/Sub messaging configuration

## Development

### Running in Development Mode
```bash
# Install in development mode
pip install -e .

# Run with auto-reload
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Running Tests
```bash
# Run Python tests
python -m pytest

# Run with coverage
python -m pytest --cov=.
```

### Database Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head
```

## Troubleshooting

### Common Issues

1. **Port already in use**: Check if services are already running
   ```bash
   # Kill processes using port 8000
   lsof -ti:8000 | xargs kill -9  # Linux/macOS
   netstat -ano | findstr :8000   # Windows
   ```

2. **Docker memory issues**: Increase Docker's memory allocation in settings

3. **Dapr not connecting**: Ensure Dapr placement service is running
   ```bash
   dapr status -k  # For Kubernetes
   dapr list       # For local services
   ```

### Validation Scripts
Run the validation scripts to check your setup:
```bash
# Linux/macOS
./scripts/setup/validate-setup.sh

# Windows
.\scripts\setup\validate-setup.ps1

# Requirements validation
./scripts/setup/validate-requirements.sh  # Linux/macOS
.\scripts\setup\validate-requirements.ps1  # Windows
```

## Next Steps

1. **Architecture Overview**: Read `docs/architecture/overview.md` to understand the system design
2. **API Documentation**: Explore the interactive API docs at `http://localhost:8000/docs`
3. **Advanced Features**: Check out how to implement recurring tasks, due dates, and reminders
4. **Kafka Integration**: Learn how events are processed in `docs/architecture/kafka.md`
5. **Dapr Usage**: Understand Dapr building blocks in `docs/architecture/dapr.md`
6. **API Reference**: Detailed API endpoints in `docs/api/rest.md`
7. **Development Guide**: Contribute to the project with `docs/development/guide.md`

## Getting Help

- Check the [Troubleshooting Guide](setup/troubleshooting.md)
- Review the [Architecture Overview](architecture/overview.md)
- File an issue in the repository if you encounter problems