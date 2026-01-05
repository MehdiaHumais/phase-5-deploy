# Testing Guide for Todo Chatbot

This document provides guidelines for testing the Todo Chatbot application with Kafka and Dapr integration.

## Testing Philosophy

The Todo Chatbot follows a comprehensive testing approach:
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test interactions between components
- **End-to-End Tests**: Test complete user workflows
- **Contract Tests**: Test API contracts and event schemas
- **Performance Tests**: Test system performance under load

## Testing Frameworks

### Primary Frameworks
- **pytest**: Python test framework with rich plugin ecosystem
- **pytest-asyncio**: For testing async/await functions
- **httpx**: For testing HTTP clients and servers
- **pytest-cov**: For code coverage measurement

### Testing Tools
- **Docker**: For isolated test environments
- **Testcontainers**: For integration tests with real services
- **Factory Boy**: For generating test data
- **Mock**: For mocking external dependencies

## Test Structure

```
tests/
├── unit/                    # Unit tests
│   ├── test_models.py       # Model tests
│   ├── test_services.py     # Service layer tests
│   ├── test_utils.py        # Utility function tests
│   └── test_validators.py   # Validation logic tests
├── integration/             # Integration tests
│   ├── test_api.py          # API integration tests
│   ├── test_kafka.py        # Kafka integration tests
│   ├── test_dapr.py         # Dapr integration tests
│   └── test_database.py     # Database integration tests
├── e2e/                     # End-to-end tests
│   ├── test_user_workflows.py
│   ├── test_reminder_flows.py
│   └── test_recurring_tasks.py
├── contract/                # Contract tests
│   ├── test_api_contracts.py
│   └── test_event_schemas.py
└── conftest.py              # Test configuration and fixtures
```

## Unit Testing

### Best Practices
1. **Fast Execution**: Unit tests should run quickly (milliseconds)
2. **Isolation**: Each test should be independent
3. **Coverage**: Aim for 80%+ coverage of business logic
4. **Clarity**: Test names should clearly describe what is being tested

### Example Unit Test
```python
import pytest
from src.models.task import Task
from src.services.task_service import TaskService

def test_create_task_with_valid_data():
    """Test creating a task with valid data."""
    task_data = {
        "title": "Test Task",
        "description": "Test Description",
        "priority": "medium"
    }

    task = Task(**task_data)

    assert task.title == "Test Task"
    assert task.description == "Test Description"
    assert task.priority == "medium"
    assert task.status == "pending"

async def test_update_task_priority():
    """Test updating task priority."""
    task_service = TaskService()
    task = await task_service.create_task(title="Test", priority="low")

    updated_task = await task_service.update_task_priority(task.id, "high")

    assert updated_task.priority == "high"
```

### Mocking External Dependencies
```python
import pytest
from unittest.mock import AsyncMock, patch

async def test_task_creation_with_notification():
    """Test task creation triggers notification."""
    with patch('src.services.notification_service.NotificationService.send_notification', new_callable=AsyncMock) as mock_send:
        task_service = TaskService()
        await task_service.create_task(title="Test Task", notify=True)

        mock_send.assert_called_once()
```

## Integration Testing

### Kafka Integration Tests
```python
import pytest
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import asyncio

@pytest.mark.asyncio
async def test_task_event_published_to_kafka(kafka_producer, kafka_consumer):
    """Test that task events are properly published to Kafka."""
    # Publish task created event
    event_data = {
        "event_type": "task_created",
        "task_id": "test-123",
        "user_id": "user-456",
        "timestamp": "2025-12-20T10:00:00Z"
    }

    await kafka_producer.send_and_wait("task-events", event_data)

    # Consume and verify event
    msg = await asyncio.wait_for(kafka_consumer.getone(), timeout=5.0)
    assert msg.value == event_data
```

### Dapr Integration Tests
```python
import pytest
import httpx

@pytest.mark.asyncio
async def test_dapr_state_management():
    """Test Dapr state management functionality."""
    async with httpx.AsyncClient(base_url="http://localhost:3500") as client:
        # Save state
        await client.post(
            "/v1.0/state/statestore",
            json=[{
                "key": "test-key",
                "value": {"data": "test-value"}
            }]
        )

        # Get state
        response = await client.get("/v1.0/state/statestore/test-key")
        assert response.json()["data"] == "test-value"
```

### Database Integration Tests
```python
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

@pytest.mark.asyncio
async def test_create_task_in_database(async_session):
    """Test creating a task in the database."""
    task_service = TaskService(db_session=async_session)
    task = await task_service.create_task(title="Test Task")

    # Verify task exists in database
    retrieved_task = await async_session.get(Task, task.id)
    assert retrieved_task.title == "Test Task"
```

## End-to-End Testing

### API End-to-End Tests
```python
import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_full_task_workflow(client, auth_headers):
    """Test complete task workflow from creation to completion."""
    # Create task
    response = client.post(
        "/api/v1/tasks",
        json={
            "title": "E2E Test Task",
            "description": "Task for end-to-end testing",
            "priority": "medium"
        },
        headers=auth_headers
    )
    assert response.status_code == 201
    task_data = response.json()

    # Get task
    response = client.get(f"/api/v1/tasks/{task_data['id']}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["title"] == "E2E Test Task"

    # Complete task
    response = client.post(f"/api/v1/tasks/{task_data['id']}/complete", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["status"] == "completed"
```

### Event-Driven Flow Tests
```python
import pytest
import asyncio
from unittest.mock import patch

@pytest.mark.asyncio
async def test_reminder_triggers_notification():
    """Test that creating a task with due date triggers reminder and notification."""
    with patch('src.services.notification_service.NotificationService.send_notification') as mock_notify:
        # Create task with due date
        task_service = TaskService()
        task = await task_service.create_task(
            title="Test Task",
            due_date=datetime.now() + timedelta(minutes=1)
        )

        # Verify reminder was scheduled
        assert mock_notify.called
        assert "due date" in mock_notify.call_args[0][0]  # Check notification content
```

## Contract Testing

### API Contract Tests
```python
import pytest
from openapi_spec_validator import validate_spec
import yaml

def test_openapi_spec_is_valid():
    """Test that the OpenAPI specification is valid."""
    with open("openapi.json") as f:
        spec = yaml.safe_load(f)

    validate_spec(spec)

def test_api_response_schema():
    """Test that API responses match expected schemas."""
    client = TestClient(app)
    response = client.get("/api/v1/tasks")

    # Validate response structure
    assert "tasks" in response.json()
    assert "total" in response.json()
    assert "offset" in response.json()
    assert "limit" in response.json()
```

### Event Schema Tests
```python
from pydantic import ValidationError
from src.schemas.events import TaskEvent, ReminderEvent

def test_task_event_schema():
    """Test that task events conform to expected schema."""
    event_data = {
        "event_type": "task_created",
        "task_id": "test-123",
        "user_id": "user-456",
        "timestamp": "2025-12-20T10:00:00Z",
        "task_data": {
            "id": "test-123",
            "title": "Test Task",
            "status": "pending"
        }
    }

    event = TaskEvent(**event_data)
    assert event.event_type == "task_created"
    assert event.task_id == "test-123"

def test_invalid_task_event_fails_validation():
    """Test that invalid task events fail validation."""
    invalid_data = {
        "event_type": "invalid_type",
        "task_id": "test-123"
        # Missing required fields
    }

    with pytest.raises(ValidationError):
        TaskEvent(**invalid_data)
```

## Test Configuration

### conftest.py
```python
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
from main import app
from src.config import settings

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
async def async_session():
    """Create a test database session."""
    engine = create_async_engine(settings.test_database_url)
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)

@pytest.fixture
def kafka_producer():
    """Create a Kafka producer for testing."""
    # Use testcontainers to create a real Kafka instance for integration tests
    pass

@pytest.fixture
def kafka_consumer():
    """Create a Kafka consumer for testing."""
    # Use testcontainers to create a real Kafka instance for integration tests
    pass
```

## Running Tests

### Local Development
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/test_models.py

# Run tests with specific marker
pytest -m "integration"

# Run tests in parallel (faster execution)
pytest -n auto

# Run tests with verbose output
pytest -v
```

### CI/CD Pipeline
```bash
# Install dependencies
pip install -r requirements-test.txt

# Run tests with coverage
pytest --cov=src --cov-report=xml --cov-fail-under=80

# Run security tests
bandit -r src/
safety check

# Run linting
flake8 src/
black --check src/
```

## Test Markers

Use pytest markers to categorize tests:

```python
import pytest

@pytest.mark.unit
def test_basic_functionality():
    """Unit test for basic functionality."""

@pytest.mark.integration
@pytest.mark.asyncio
async def test_database_integration():
    """Integration test with database."""

@pytest.mark.e2e
@pytest.mark.slow
def test_complete_workflow():
    """End-to-end test for complete workflow."""

@pytest.mark.kafka
@pytest.mark.integration
@pytest.mark.asyncio
async def test_kafka_integration():
    """Test Kafka integration."""
```

## Performance Testing

### Load Testing
```python
import pytest
import asyncio
import time
from locust import HttpUser, task, constant_pacing

class TaskUser(HttpUser):
    wait_time = constant_pacing(1)

    @task
    def create_task(self):
        self.client.post("/api/v1/tasks", json={
            "title": f"Load Test Task {int(time.time())}",
            "priority": "medium"
        })
```

### Benchmark Testing
```python
import pytest
import time
from pytest_benchmark.fixture import benchmark

def test_task_creation_performance(benchmark):
    """Benchmark task creation performance."""
    def create_many_tasks():
        task_service = TaskService()
        tasks = []
        for i in range(100):
            task = task_service.create_task(title=f"Task {i}")
            tasks.append(task)
        return tasks

    result = benchmark(create_many_tasks)
    assert len(result) == 100
```

## Security Testing

### Dependency Scanning
```bash
# Check for vulnerable dependencies
safety check
pip-audit

# Check for security issues in code
bandit -r src/
```

### Authentication Testing
```python
def test_unauthorized_access():
    """Test that unauthorized access is prevented."""
    client = TestClient(app)
    response = client.get("/api/v1/tasks")
    assert response.status_code == 401

def test_invalid_token():
    """Test that invalid tokens are rejected."""
    client = TestClient(app)
    response = client.get("/api/v1/tasks", headers={"Authorization": "Bearer invalid-token"})
    assert response.status_code == 401
```

## Testing Best Practices

### 1. Test Data Management
- Use factories to generate consistent test data
- Clean up test data after tests
- Use separate test databases
- Mock external services in unit tests

### 2. Test Organization
- Group related tests together
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Keep tests focused and single-purpose

### 3. Test Coverage
- Aim for 80%+ code coverage on business logic
- Focus on testing critical paths
- Test edge cases and error conditions
- Include negative test cases

### 4. Continuous Testing
- Run unit tests on every commit
- Run integration tests on every pull request
- Run E2E tests before production deployment
- Monitor test performance and flakiness

## Troubleshooting Tests

### Common Issues
1. **Flaky Tests**: Use retries or fix race conditions
2. **Slow Tests**: Optimize database operations, use mocks
3. **Fragile Tests**: Reduce external dependencies, use stable test data
4. **Hard-to-Debug Tests**: Add logging, use descriptive assertions

### Debugging Tips
```python
# Add debugging to failing tests
import logging
logging.basicConfig(level=logging.DEBUG)

# Use pytest's debugging features
# Run with -s to see print statements
# Use --pdb to drop into debugger on failure
# Use --lf to run only last failed tests
```

This testing guide provides a comprehensive approach to ensuring the quality and reliability of the Todo Chatbot system with Kafka and Dapr integration.