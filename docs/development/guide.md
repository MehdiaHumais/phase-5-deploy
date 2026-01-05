# Development Guide for Todo Chatbot

This guide provides instructions for developers contributing to the Todo Chatbot project.

## Prerequisites

Before starting development, ensure you have:

### Required Software
- Git 2.30+
- Python 3.11 (with venv support)
- Node.js 18+ (for frontend, if applicable)
- Docker and Docker Compose
- Dapr CLI and Runtime
- kubectl (for Kubernetes operations)

### Recommended Tools
- Visual Studio Code or IntelliJ IDEA
- Docker Desktop with Kubernetes enabled
- Postman or Insomnia for API testing

## Getting Started

### 1. Fork and Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/todo-chatbot.git
cd todo-chatbot
```

### 2. Set Up Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
Create a `.env` file in the project root:

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

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Dapr
DAPR_HTTP_PORT=3500
DAPR_GRPC_PORT=50001
```

## Development Environment Setup

### Option 1: Local Development with Dapr
```bash
# Start Dapr sidecar for the API
dapr run --app-id todo-api --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 -- uvicorn main:app --reload

# In another terminal, run the service directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Option 2: Docker-based Development
```bash
# Build and start all services
docker-compose up --build

# Start specific services
docker-compose up db kafka redis
```

## Project Structure

```
todo-chatbot/
├── main.py                 # Main application entry point
├── requirements.txt        # Python dependencies
├── package.json            # Node.js dependencies (if applicable)
├── Dockerfile             # Container definition
├── docker-compose.yml     # Multi-container setup
├── dapr/                  # Dapr component configurations
│   └── components/
│       ├── statestore.yaml
│       └── pubsub.yaml
├── scripts/               # Setup and utility scripts
│   └── setup/
├── docs/                  # Documentation
├── tests/                 # Test files
├── src/                   # Source code (if using this structure)
└── README.md
```

## Coding Standards

### Python
- Follow PEP 8 style guide
- Use type hints for all function parameters and return values
- Write docstrings for all public classes, methods, and functions
- Use meaningful variable and function names

### Example:
```python
from typing import List, Optional
from datetime import datetime

def get_user_tasks(user_id: str, status: Optional[str] = None) -> List[dict]:
    """
    Retrieve tasks for a specific user, optionally filtered by status.

    Args:
        user_id: The ID of the user whose tasks to retrieve
        status: Optional status filter (e.g., 'completed', 'pending')

    Returns:
        List of task dictionaries
    """
    # Implementation here
    pass
```

### API Endpoints
- Use RESTful URL patterns
- Implement proper HTTP status codes
- Include comprehensive error handling
- Document all endpoints with OpenAPI/Swagger

## Testing

### Running Tests
```bash
# Run all tests
python -m pytest

# Run tests with coverage
python -m pytest --cov=.

# Run specific test file
python -m pytest tests/test_tasks.py

# Run tests with verbose output
python -m pytest -v
```

### Test Structure
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- End-to-end tests in `tests/e2e/`

### Writing Tests
```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_create_task(client):
    response = client.post("/api/v1/tasks", json={
        "title": "Test Task",
        "description": "Test Description"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
```

## Database Migrations

### Creating Migrations
```bash
# Create a new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Downgrade to previous version
alembic downgrade -1

# Check current version
alembic current
```

## Dapr Development

### Local Dapr Setup
```bash
# Initialize Dapr (first time only)
dapr init

# Run with Dapr sidecar
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

# Check Dapr status
dapr status -k  # For Kubernetes
dapr list       # For local running services
```

### Dapr Component Development
When developing with Dapr components:

1. Define components in `dapr/components/`
2. Test locally with `dapr run`
3. Deploy to Kubernetes with Dapr annotations

## Kafka Event Development

### Producing Events
```python
import httpx

async def publish_task_event(task_data: dict):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
            json={
                "event_type": "task_created",
                "task_id": task_data["id"],
                "user_id": task_data["user_id"],
                "timestamp": datetime.now().isoformat(),
                "task_data": task_data
            }
        )
```

### Consuming Events
Events are consumed by separate services that subscribe to Kafka topics.

## Git Workflow

### Branch Naming Convention
- Feature branches: `feature/issue-number-description`
- Bug fixes: `bugfix/issue-number-description`
- Hotfixes: `hotfix/issue-number-description`

### Example:
```bash
# Create a feature branch
git checkout -b feature/123-add-task-search

# Make changes and commit
git add .
git commit -m "feat: add task search functionality"

# Push and create PR
git push origin feature/123-add-task-search
```

### Commit Message Format
Use conventional commits:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `test:` for test updates
- `refactor:` for code restructuring
- `chore:` for maintenance tasks

## Local Development Commands

### Running the Application
```bash
# Run with auto-reload
uvicorn main:app --reload

# Run with Dapr
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

# Run with specific host/port
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Development Scripts
```bash
# Install dependencies
pip install -r requirements.txt

# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/

# Run all checks
make check  # If Makefile exists
```

## Debugging

### Local Debugging
1. Set breakpoints in your IDE
2. Run the application with the debugger attached
3. Use Dapr's debug mode if needed

### Dapr Debugging
```bash
# Check Dapr logs
dapr logs todo-api

# Check service status
dapr status

# List running services
dapr list
```

### Docker Debugging
```bash
# View container logs
docker logs todo-chatbot-api

# Execute commands in container
docker exec -it todo-chatbot-api /bin/bash
```

## Performance Optimization

### Caching
- Use Redis for caching frequently accessed data
- Implement cache invalidation strategies
- Monitor cache hit/miss ratios

### Database Optimization
- Use proper indexing
- Optimize queries with EXPLAIN
- Implement connection pooling
- Use async database operations

### API Optimization
- Implement pagination for large datasets
- Use field selection where appropriate
- Implement rate limiting
- Use compression for large responses

## Security Best Practices

### Input Validation
- Validate all inputs on the server side
- Use Pydantic models for request validation
- Sanitize user inputs to prevent injection attacks

### Authentication & Authorization
- Use JWT tokens for authentication
- Implement proper role-based access control
- Store secrets securely using Dapr secret store

### API Security
- Implement rate limiting
- Use HTTPS in production
- Validate CORS settings
- Sanitize error messages

## Documentation

### Code Documentation
- Document all public interfaces
- Use type hints for clarity
- Write meaningful docstrings
- Keep documentation up-to-date

### API Documentation
- Use FastAPI's automatic documentation
- Include example requests/responses
- Document error conditions
- Provide usage examples

## Deployment

### Local Deployment
```bash
# Using Docker Compose
docker-compose up -d

# Using Dapr CLI
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app
```

### Kubernetes Deployment
See deployment documentation in `docs/deployment/`.

## Troubleshooting

### Common Issues

#### Dapr Issues
- Ensure Dapr placement service is running
- Check component configurations
- Verify service names match app-id

#### Kafka Issues
- Verify Kafka broker is accessible
- Check topic configurations
- Ensure proper authentication

#### Database Issues
- Verify connection strings
- Check migration status
- Ensure database is running

### Getting Help
- Check the [Troubleshooting Guide](../setup/troubleshooting.md)
- Look at existing issues in the repository
- Contact maintainers through appropriate channels

## Contributing

### Pull Request Process
1. Create an issue for the feature/bug
2. Fork the repository
3. Create a feature branch
4. Make changes following coding standards
5. Write/update tests
6. Update documentation
7. Submit a pull request

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included/updated
- [ ] Documentation is updated
- [ ] Security considerations are addressed
- [ ] Performance implications are considered
- [ ] Commits are atomic and well-described

## Continuous Integration

The project uses GitHub Actions for CI/CD:

### CI Pipeline Includes:
- Code formatting checks
- Linting
- Unit and integration tests
- Security scanning
- Code coverage verification
- Docker image building

### Local CI Verification
```bash
# Run all CI checks locally
make ci-check  # If Makefile exists
# Or run individual checks
python -m pytest
flake8 src/
black --check src/
```

## Performance Monitoring

### Local Monitoring
- Use FastAPI's built-in performance metrics
- Monitor response times
- Track error rates
- Monitor resource usage

### Production Monitoring
- Set up logging and monitoring
- Configure alerting for critical issues
- Monitor user activity and engagement
- Track API usage patterns

This guide should help you get started with development on the Todo Chatbot project. For additional information, refer to other documentation files in the `docs/` directory.