# Dapr Integration in Todo Chatbot

This document explains how Dapr (Distributed Application Runtime) is integrated into the Todo Chatbot system.

## Overview

Dapr provides a set of building blocks that enable the Todo Chatbot to be built as a distributed system without tight coupling to specific infrastructure implementations. All infrastructure dependencies are accessed through Dapr's HTTP/gRPC APIs instead of direct client libraries.

## Dapr Building Blocks Used

### 1. Service Invocation
- **Purpose**: Enable communication between services with built-in retries and mTLS
- **Implementation**: Services call each other through Dapr's service invocation API
- **Example Usage**:
  ```bash
  curl -X POST http://localhost:3500/v1.0/invoke/notification-service/method/api/notifications
  ```

### 2. State Management
- **Purpose**: Store conversation state and task cache without direct database calls
- **Implementation**: Using PostgreSQL state store component
- **Example Usage**:
  ```bash
  # Save state
  curl -X POST http://localhost:3500/v1.0/state/statestore \
    -H "Content-Type: application/json" \
    -d '[{ "key": "user-123", "value": {"current_task": "abc"} }]'

  # Get state
  curl http://localhost:3500/v1.0/state/statestore/user-123
  ```

### 3. Pub/Sub (Publish/Subscribe)
- **Purpose**: Enable event-driven communication between services
- **Implementation**: Using Kafka as the pub/sub component
- **Example Usage**:
  ```bash
  curl -X POST http://localhost:3500/v1.0/publish/kafka-pubsub/task-events \
    -H "Content-Type: application/json" \
    -d '{"event_type": "task_created", "task_id": "123"}'
  ```

### 4. Input Bindings
- **Purpose**: Trigger services based on external events or schedules
- **Implementation**: Using cron bindings for scheduled reminders
- **Example Usage**: See cron binding configuration

### 5. Secrets Management
- **Purpose**: Securely store and access credentials
- **Implementation**: Using Kubernetes secrets store
- **Example Usage**:
  ```bash
  curl http://localhost:3500/v1.0/secrets/kubernetes-secrets/openai-api-key
  ```

## Dapr Component Configuration

### Kafka Pub/Sub Component
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kafka-pubsub
spec:
  type: pubsub.kafka
  version: v1
  metadata:
  - name: brokers
    value: "kafka:9092"
  - name: consumerGroup
    value: "todo-service"
  - name: authRequired
    value: "false"
```

### PostgreSQL State Store Component
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: statestore
spec:
  type: state.postgresql
  version: v1
  metadata:
  - name: connectionString
    value: "host=postgres user=todo password=todo123 port=5432 database=todo_db"
  - name: actorStateStore
    value: "true"
```

### Cron Binding Component for Reminders
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: reminder-cron
spec:
  type: bindings.cron
  version: v1
  metadata:
  - name: schedule
    value: "*/5 * * * *" # Every 5 minutes
```

### Kubernetes Secrets Component
```yaml
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
  name: kubernetes-secrets
spec:
  type: secretstores.kubernetes
  version: v1
```

## Service Implementation with Dapr

### Without Dapr (Tightly Coupled)
```python
from kafka import KafkaProducer
import psycopg2

# Direct dependencies with specific client libraries
producer = KafkaProducer(bootstrap_servers="kafka:9092", ...)
db_connection = psycopg2.connect(...)

# Publish event directly to Kafka
producer.send("task-events", value=event)

# Store state directly in PostgreSQL
cursor = db_connection.cursor()
cursor.execute("INSERT INTO tasks ...")
```

### With Dapr (Decoupled)
```python
import httpx

# No direct client libraries needed - use Dapr HTTP API
async def publish_task_event(task_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
            json={"event_type": "created", "task_id": task_data["id"]}
        )

async def save_task_state(task_id, task_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3500/v1.0/state/statestore",
            json=[{"key": f"task-{task_id}", "value": task_data}]
        )
```

## Running with Dapr

### Local Development
```bash
# Run service with Dapr sidecar
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload

# Run with specific Dapr ports
dapr run --app-id todo-api --app-port 8000 --dapr-http-port 3500 --dapr-grpc-port 50001 -- uvicorn main:app --reload
```

### With Docker Compose
```yaml
services:
  api:
    # ... other config
    command: >
      sh -c "
        dapr run --app-id todo-api --app-port 8000 --dapr-grpc-port 50001 -- uvicorn main:app --host 0.0.0.0 --port 8000
      "
```

## Benefits of Dapr Integration

1. **Infrastructure Abstraction**: Swap Kafka for RabbitMQ by changing YAML config, not code
2. **Reduced Boilerplate**: No need to implement retry logic, circuit breakers, etc.
3. **Security**: Built-in mTLS for service-to-service communication
4. **Observability**: Distributed tracing and metrics out of the box
5. **Portability**: Same code runs on local, Kubernetes, or other hosting platforms

## Local vs Cloud Dapr Usage

### Local Development
- Use Dapr CLI for pub/sub and basic state management
- Suitable for development and testing

### Cloud (DigitalOcean Kubernetes)
- Full Dapr: Pub/Sub, State, Bindings (cron), Secrets, Service Invocation
- Production-ready configuration with proper security

## Troubleshooting

### Common Issues

1. **Dapr Sidecar Not Starting**
   - Ensure Dapr CLI is installed: `dapr --version`
   - Initialize Dapr: `dapr init`
   - Check if placement service is running

2. **Service Invocation Failing**
   - Verify app IDs match between caller and callee
   - Check if both services have Dapr sidecars

3. **State Store Connection Issues**
   - Verify connection string in component configuration
   - Ensure the underlying database is accessible

4. **Pub/Sub Not Working**
   - Verify broker addresses in component configuration
   - Check if the message broker (Kafka) is running