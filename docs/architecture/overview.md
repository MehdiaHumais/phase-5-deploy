# Architecture Overview of Todo Chatbot

This document provides an overview of the Todo Chatbot system architecture, which implements advanced features using Kafka for event streaming and Dapr for distributed application runtime.

## System Architecture

The Todo Chatbot system follows a microservices architecture with event-driven communication patterns:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Todo API      │    │  Notification   │
│   (Next.js)     │◄──►│   (FastAPI)     │◄──►│   Service       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │    Kafka        │
                       │  (Redpanda)     │
                       └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌─────────────────┐   ┌─────────────────┐   ┌─────────────────┐
│  Reminder       │   │  Audit Service  │   │  Websocket      │
│  Service        │   │                 │   │  Service        │
└─────────────────┘   └─────────────────┘   └─────────────────┘
```

## Core Components

### 1. Todo API Service
- **Technology**: FastAPI, Python
- **Responsibilities**:
  - Handle all task operations (CRUD)
  - Process user commands and queries
  - Publish events to Kafka
  - Integrate with Dapr building blocks

### 2. Notification Service
- **Technology**: FastAPI, Python
- **Responsibilities**:
  - Send notifications to users
  - Handle multiple notification channels (email, SMS, push)
  - Process notification events from Kafka

### 3. Reminder Service
- **Technology**: FastAPI, Python
- **Responsibilities**:
  - Schedule and trigger reminders
  - Process recurring task logic
  - Publish reminder events to Kafka

### 4. Audit Service
- **Technology**: FastAPI, Python
- **Responsibilities**:
  - Maintain audit trail of all operations
  - Process audit events from Kafka
  - Store audit logs

### 5. Websocket Service
- **Technology**: FastAPI, Python
- **Responsibilities**:
  - Handle real-time client synchronization
  - Broadcast updates to connected clients
  - Process real-time events from Kafka

## API Documentation

For detailed API documentation, see:
- [REST API Documentation](api.md)
- [Dapr Integration Guide](dapr.md)
- [Kafka Integration Guide](kafka.md)

## Event-Driven Architecture

### Kafka Topics
1. **task-events**: All task CRUD operations
2. **reminders**: Reminder scheduling and triggering events
3. **task-updates**: Real-time task updates for WebSocket service

### Event Schema
#### Task Event
```json
{
  "event_type": "task_created|task_updated|task_deleted|task_completed",
  "task_id": "string",
  "user_id": "string",
  "timestamp": "datetime",
  "task_data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": "datetime",
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
}
```

#### Reminder Event
```json
{
  "event_type": "reminder_scheduled|reminder_triggered",
  "task_id": "string",
  "user_id": "string",
  "timestamp": "datetime",
  "title": "string",
  "due_at": "datetime",
  "remind_at": "datetime",
  "notification_type": "email|sms|push|in_app"
}
```

## Dapr Integration

### Building Blocks Used
1. **Service Invocation**: Inter-service communication with built-in retries
2. **State Management**: Store conversation state and task cache
3. **Pub/Sub**: Event streaming through Kafka via Dapr
4. **Bindings**: Cron triggers for scheduled reminders
5. **Secrets**: Secure storage of API keys and credentials

### Dapr Components Configuration
```yaml
# Kafka Pub/Sub Component
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

# PostgreSQL State Store Component
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

# Cron Binding Component
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

## Advanced Features Implementation

### 1. Recurring Tasks
- Implemented in the Reminder Service
- Task completion triggers creation of next instance based on recurrence pattern
- Events published to Kafka for audit trail

### 2. Due Dates & Reminders
- Tasks with due dates automatically create reminder events
- Multiple notification channels supported
- Configurable reminder timing (1 hour before, 1 day before, etc.)

### 3. Priorities, Tags, Search, Filter, Sort
- Implemented in the Todo API Service
- Full-text search capability
- Multiple filter and sort options
- Tag-based organization

### 4. Event-Driven Architecture
- All operations publish events to Kafka
- Services consume relevant events asynchronously
- Loose coupling between services
- Scalable and resilient design

## Deployment Architecture

### Local Development (Minikube)
- Minikube cluster with Dapr enabled
- All services deployed as Kubernetes deployments
- Kafka (Redpanda) deployed in-cluster
- Dapr components configured for local development

### Cloud Deployment (DigitalOcean Kubernetes)
- Production-grade DOKS cluster
- Dapr installed with full capabilities
- Redpanda Cloud for Kafka
- CI/CD pipeline with GitHub Actions
- Monitoring and logging configured

## Security Considerations

1. **Authentication & Authorization**: JWT-based authentication
2. **Secrets Management**: Dapr secret store integration
3. **Network Security**: Service mesh with mTLS
4. **Data Encryption**: At-rest and in-transit encryption
5. **API Security**: Rate limiting and input validation

## Monitoring and Observability

1. **Logging**: Structured logging with correlation IDs
2. **Metrics**: Prometheus integration for performance metrics
3. **Tracing**: Distributed tracing with OpenTelemetry
4. **Alerting**: Configured alerts for critical metrics

## Data Management

### Source of Truth
- PostgreSQL database for persistent storage
- Kafka for event sourcing and audit trail
- Redis for caching and session storage

### Schema Evolution
- Database migrations using Alembic
- Backward-compatible event schemas
- Versioned API endpoints

## Scalability Considerations

1. **Horizontal Scaling**: Services can be scaled independently
2. **Load Distribution**: Kafka partitions for parallel processing
3. **Caching Strategy**: Redis for frequently accessed data
4. **Database Optimization**: Connection pooling and indexing

## Technology Stack

### Backend
- **Runtime**: Python 3.11, FastAPI
- **Database**: PostgreSQL
- **Caching**: Redis
- **Message Queue**: Kafka (Redpanda)
- **Orchestration**: Kubernetes
- **Service Mesh**: Dapr

### Frontend
- **Framework**: Next.js
- **Runtime**: Node.js
- **API Communication**: REST/GraphQL

### Infrastructure
- **Containerization**: Docker
- **Orchestration**: Kubernetes (Minikube/DOKS)
- **Service Mesh**: Dapr
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana, ELK Stack

## Development Workflow

1. **Local Development**: Minikube with Dapr
2. **Testing**: Unit, integration, and end-to-end tests
3. **CI/CD**: Automated testing and deployment
4. **Monitoring**: Real-time application monitoring
5. **Logging**: Centralized log management

This architecture enables the Todo Chatbot to handle advanced features while maintaining scalability, resilience, and maintainability.