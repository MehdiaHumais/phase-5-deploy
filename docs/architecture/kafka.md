# Kafka Integration in Todo Chatbot

This document explains how Apache Kafka (using Redpanda) is integrated into the Todo Chatbot system for event-driven architecture.

## Overview

Kafka enables a decoupled, scalable microservices architecture where the Todo Chatbot API publishes events and specialized services (Notification, Recurring Task, Audit) consume and process them independently. This is essential for the advanced features (recurring tasks, reminders) and scales better in production.

## Kafka Topics

### task-events
- **Producer**: Todo Chatbot API (MCP Tools)
- **Consumers**: Recurring Task Service, Audit Service
- **Purpose**: All task CRUD operations
- **Event Schema**:
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

### reminders
- **Producer**: Todo Chatbot API (when due date set)
- **Consumers**: Notification Service
- **Purpose**: Reminder scheduling and triggering
- **Event Schema**:
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

### task-updates
- **Producer**: Todo Chatbot API WebSocket Service
- **Consumers**: WebSocket Service
- **Purpose**: Real-time client synchronization
- **Event Schema**:
  ```json
  {
    "event_type": "task_updated|task_assigned|task_shared",
    "task_id": "string",
    "user_id": "string",
    "timestamp": "datetime",
    "update_data": {}
  }
  ```

## Use Cases

### 1. Reminder/Notification System
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Todo Service  │───▶│ Kafka Topic     │───▶│ Notification    │
│ (Producer)      │    │ "reminders"     │    │ Service         │
│                 │    │                 │    │ (Consumer)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

When a task with a due date is created, publish a reminder event. A separate notification service consumes and sends reminders at the right time.

### 2. Recurring Task Engine
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Task Completed  │───▶│ Kafka Topic     │───▶│ Recurring Task  │
│ Event           │    │ "task-events"   │    │ Service         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

When a recurring task is completed, the Recurring Task Service receives the event and creates the next instance of the task based on the recurrence pattern.

## Event Schema Examples

### Task Event
| Field | Type | Description |
|-------|------|-------------|
| event_type | string | "created", "updated", "completed", "deleted" |
| task_id | integer | The task ID |
| task_data | object | Full task object |
| user_id | string | User who performed action |
| timestamp | datetime | When event occurred |

### Reminder Event
| Field | Type | Description |
|-------|------|-------------|
| task_id | integer | The task ID |
| title | string | Task title for notification |
| due_at | datetime | When task is due |
| remind_at | datetime | When to send reminder |
| user_id | string | User to notify |

## Implementation with Dapr

Instead of using Kafka client libraries directly, the Todo Chatbot uses Dapr's pub/sub building block:

### Publishing Events (Python)
```python
import httpx

# Publish via Dapr sidecar (no Kafka library needed!)
async def publish_task_event(task_data):
    async with httpx.AsyncClient() as client:
        await client.post(
            "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
            json={"event_type": "created", "task_id": task_data["id"]}
        )
```

### Dapr Kafka Component Configuration
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

## Local vs Cloud Kafka Setup

### For Local Development (Minikube)
**Recommendation**: Redpanda Docker container
```yaml
# docker-compose.redpanda.yml
services:
  redpanda:
    image: redpandadata/redpanda:latest
    command:
      - redpanda start
      - --smp 1
      - --memory 512M
      - --overprovisioned
      - --kafka-addr PLAINTEXT://0.0.0.0:9092
      - --advertise-kafka-addr PLAINTEXT://localhost:9092
    ports:
      - "9092:9092"
      - "8081:8081" # Schema Registry
      - "8082:8082" # REST Proxy
```

### For Cloud Deployment
**Recommendation**: Redpanda Cloud Serverless or Strimzi self-hosted

## Why Kafka for Todo App?

### Without Kafka
- Reminder logic coupled with main app
- Recurring tasks processed synchronously
- No activity history
- Single client updates
- Tight coupling between services

### With Kafka
- Decoupled notification service
- Async processing, no blocking
- Complete audit trail
- Real-time multi-client sync
- Loose coupling, scalable

## Kafka Service Recommendations

### For Cloud Deployment

| Service | Free Tier | Pros | Cons |
|---------|-----------|------|------|
| Redpanda Cloud | ⭐ | Free Serverless tier, no Zookeeper, fast, easy | Scheduled reminder triggers |
| Confluent Cloud | $400 credit for 30 days | Industry standard, Schema Registry, great docs | Credit expires |
| CloudKarafka | "Developer Duck" free plan | Simple, 5 topics free | Limited throughput |
| Aiven | $300 credit trial | Fully managed, multi-cloud | Trial expires |
| Self-hosted (Strimzi) | Free (just compute cost) | Full control, learning experience | More complex setup |

### For Local Development (Minikube)
| Option | Complexity | Description |
|--------|------------|-------------|
| Redpanda (Docker) | ⭐ | Single binary, no Zookeeper, Kafka-compatible |
| Bitnami Kafka Helm | Medium | Kubernetes-native, Helm chart |
| Strimzi Operator | Medium-Hard | Production-grade K8s operator |

## Python Client Example (Direct - Not Used in Our Implementation)

Standard `kafka-python` works with Redpanda, but we use Dapr instead:

```python
from kafka import KafkaProducer
import json

producer = KafkaProducer(
    bootstrap_servers="YOUR-CLUSTER.cloud.redpanda.com:9092",
    security_protocol="SASL_SSL",
    sasl_mechanism="SCRAM-SHA-256",
    sasl_plain_username="YOUR-USERNAME",
    sasl_plain_password="YOUR-PASSWORD",
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Publish event
producer.send("task-events", {"event_type": "created", "task_id": 1})
```

## Summary for Hackathon

| Type | Recommendation |
|------|----------------|
| Local: Minikube | Redpanda Docker container |
| Cloud | Redpanda Cloud Serverless (free) or Strimzi self-hosted |

## Event Processing Guarantees

- **At-least-once delivery**: Ensures no events are lost
- **Ordered processing per partition**: Events for the same task are processed in order
- **Partitioning strategy**: Tasks are partitioned by user_id to ensure ordering while allowing parallel processing

## Monitoring and Observability

- Kafka metrics are collected via Dapr
- Consumer lag monitoring for each topic
- Event processing time tracking
- Dead letter queue for failed events