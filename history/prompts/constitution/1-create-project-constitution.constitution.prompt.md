---
id: 1
title: Create-Project-Constitution
stage: constitution
date: 2025-12-19
surface: agent
model: claude-sonnet-4-5-20250929
feature: none
branch: master
user: unknown
command: /sp.constitution
labels: ["constitution", "project-setup", "todo-chatbot", "kafka", "dapr"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files:
 - .specify/memory/constitution.md
tests:
 - none
---

## Prompt

Make the project using this "Objective: Implement advanced features and deploy first on Minikube locally and then to
production-grade Kubernetes on DigitalOcean and Kafka on Redpanda Cloud.
Part A: Advanced Features
• Implement all Advanced Level features (Recurring Tasks, Due Dates & Reminders)
• Implement Intermediate Level features (Priorities, Tags, Search, Filter, Sort)
• Add event-driven architecture with Kafka
• Implement Dapr for distributed application runtime
Part B: Local Deployment
• Deploy to Minikube
• Deploy Dapr on Minikube use Full Dapr: Pub/Sub, State, Bindings (cron), Secrets,
Service Invocation
Part C: Cloud Deployment
• Deploy to DigitalOcean Kubernetes (DOKS)
• Deploy Dapr on DOKS use Full Dapr: Pub/Sub, State, Bindings (cron), Secrets,
Service Invocation
• Use Kafka on Redpanda Cloud
• Set up CI/CD pipeline using Github Actions
• Configure monitoring and logging
DigitalOcean Setup
New DigitalOcean accounts receive $200 credit for 60 days:
1. Sign up at digitalocean.com
2. Create a Kubernetes cluster (DOKS)
3. Configure kubectl to connect to DOKS
4. Deploy using Helm charts from Phase IV
Kafka Use Cases in Phase
Event-Driven Architecture for Todo Chatbot
1. Reminder/Notification System
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
┌─────────────────┐
│ │ │ │ │ │ │
│
│ Todo Service │────▶│ Kafka Topic │────▶│ Notification │────▶│ User
Device │
│ (Producer) │ │ "reminders" │ │ Service │ │
(Push/Email) │
│ │ │ │ │ (Consumer) │ │
│
└─────────────────┘ └─────────────────┘ └─────────────────┘
└─────────────────┘
Page 24 of 37
Hackathon II: Spec-Driven Development
When a task with a due date is created, publish a reminder event. A separate notification
service consumes and sends reminders at the right time.
2. Recurring Task Engine
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ │ │ │ │ │
│ Task Completed │────▶│ Kafka Topic │────▶│ Recurring Task  ▼
│
│ ┌─────────────┐ ┌─────────────────┐ ┌─────────────────┐
│
│ │ Neon DB │ │ Recurring Task │ │ Notification │
│
│ │ (External) │ │ Service │ │ Service │
│
│ └─────────────┘ └─────────────────┘ └─────────────────┘
│
└───────────────────────────────────────────────────────────────────────────────
───────┘
Kafka Topics
Topic Producer Consumer Purpose
task-events Chat API (MCP Tools) Recurring Task
Service, Audit Service
All task CRUD
operations
reminders Chat API (when due
date set)
Notificatiere
services communicate through events rather than direct API calls. This is essential for the
advanced features (recurring tasks, reminders) and scales better in production.
Key Takeaway:
Kafka enables decoupled, scalable microservices architecture where the Chat API publishes
events and specialized services (Notification, Recurring Task, Audit) consume and process
them independently.
Kafka Service Recommendations
For Cloud Deployment
Service Free Tier Pros Cons
Redpanda Cloud
⭐
Free Serverless tier Kafka-compatible, no
Zookeeper, fast, easy
on Service Scheduled reminder
triggers
task-updates Chat API WebSocket Service Real-time client sync
Event Schema Examples
Task Event
Field Type Description
event_type string "created", "updated", "completed", "deleted"
task_id integer The task ID
task_data object Full task object
user_id string User who performed action
timestamp datetime When event occurred
Reminder Event
Field Type Description
task_id integer The task ID
title string Task title for notification
due_at datetime When task is due
remind_at datetime When to send reminder
user_id string User to notify
Why Kafka for Todo App?
Without Kafka With Kafka
Reminder logic coupled with main app Decoupled notification service
Recurring tasks processed synchronously Async processing, no blocking
No activity history Complete audit trail
Single client updates Real-time multi-client sync
Tight coupling between services Loose coupling, scalable
Page 26 of 37
Hackathon II: Spec-Driven Development
Bottom Line
Kafka turns the Todo app from a simple CRUD app intosetup
Newer ecosystem
Confluent Cloud $400 credit for 30
days
Industry standard,
Schema Registry, great
docs
Credit expires
CloudKarafka "Developer Duck"
free plan
Simple, 5 topics free Limited throughput
Aiven $300 credit trial Fully managed,
multi-cloud
Trial expires
Self-hosted
(Strimzi)
Free (just compute
cost)
Full control, learning
experience
More complex setup
For Local Development (Minikube)
Option Complexity Description
Redpanda (Docker) ⭐ Easy Single binary, no Zookeeper,
Kafka-compatible
Bitnami Kafka Helm Medium Kubernetes-native, Helm chart
Strimzi Operator Medium-Hard Production-grade K8s operator
Primary Recommendation: Redpanda Cloud (Serverless)
Best for hackathon because:
● Free serverless tier (no credit card for basic usage)
● Kafka-compatible - same APIs, clients work unchanged
● No Zookeeper - simpler architecture
● Fast setup - under 5 minutes
● REST API + Native protocols
Sign up: https://redpanda.com/cloud
For Local/Minikube: Redpanda Docker
Page 27 of 37
Hackathon II: Spec-Driven Development
Single container, Kafka-compatible:
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
Alternative: Self-Hosted on Kubernetes (Strimzi)
Good learning experience for students:
# Install Strimzi operator
kubectl create namespace kafka
kubectl apply -f https://strimzi.io/install/latest?namespace=kafka
# Create Kafka cluster
kubectl apply -f kafka-cluster.yaml
Redpanda Cloud Quick Setup
Step Action
1 Sign up at redpanda.com/cloud
2 Create a Serverless cluster (free tier)
3 Create topics: task-events, reminders, task-updates
4 Copy bootstrap server URL and credentials
5 Use standard Kafka clients (kafka-python, aiokafka)
Python Client Example
Standard kafka-python works with Redpanda:
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
Summary for Hackathon
Type Recommendation
Local: Minikube Redpanda Docker container
Page 28 of 37
Hackathon II: Spec-Driven Development
Type Recommendation
Cloud Redpanda Cloud Serverless (free) or Strimzi
self-hosted
Dapr Integration Guide
What is Dapr?
Dapr (Distributed Application Runtime) is a portable, event-driven runtime that simplifies
building microservices. It runs as a sidecar next to your application and provides building
blocks via HTTP/gRPC APIs.
Dapr Building Blocks for Todo App
Building Block Use Case in Todo App
Pub/Sub Kafka abstraction – publish/subscribe without Kafka client
code
State Management Conversation state storage (alternative to direct DB calls)
Service Invocation Frontend → Backend communication with built-in retries
Bindings Cron triggers for scheduled reminders
Secrets Management Store API keys, DB credentials securely
Architecture: Without Dapr vs With Dapr
Without Dapr (Direct Dependencies)
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│ Frontend │────▶│ Backend │────▶│ Kafka │
│ │ │ (FastAPI) │────▶│ Neon DB │
└─────────────┘ └─────────────┘ └─────────────┘
 │
 Tight coupling:
- kafka-python library
 - psycopg2/sqlmodel
- Direct connection strings
With Dapr (Abstracted Dependencies)
┌─────────────┐ ┌─────────────────────────────────┐ ┌─────────────┐
│ Frontend │ │ Backend Pod │ │ │
│ + Dapr │────▶│ ┌─────────┐ ┌───────────┐ │ │ Dapr │
│ Sidecar │ │ │ FastAPI │◀──▶│ Dapr │──┼────▶│ Components │
└─────────────┘ │ │ App │ │ Sidecar │ │ │ - Kafka │
 │ └─────────┘ └───────────┘ │ │ - Neon DB │
 └─────────────────────────────────┘ │ - Secrets │
 └─────────────┘
 Loose coupling:
- App talks to Dapr via HTTP
 - Dapr handles Kafka, DB, etc.
 - Swap components without code changes
Page 29 of 37
Hackathon II: Spec-Driven Development
Use Case 1: Pub/Sub (Kafka Abstraction)
Instead of using kafka-python directly, publish events via Dapr:
Without Dapr:
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers="kafka:9092", ...)
producer.send("task-events", value=event)
With Dapr:
import httpx
# Publish via Dapr sidecar (no Kafka library needed!)
await httpx.post(
 "http://localhost:3500/v1.0/publish/kafka-pubsub/task-events",
 json={"event_type": "created", "task_id": 1}
)
Dapr Component Configuration:
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
Use Case 2: State Management (Conversation State)
Store conversation history without direct DB code:
Without Dapr:
from sqlmodel import Session
session.add(Message(...))
session.commit()
With Dapr:
import httpx
# Save state via Dapr
await httpx.post(
 "http://localhost:3500/v1.0/state/statestore",
 json=[{
 "key": f"conversation-{conv_id}",
 "value": {"messages": messages}
 }]
)
# Get state
response = await httpx.get(
 f"http://localhost:3500/v1.0/state/statestore/conversation-{conv_id}"
)
Dapr Component Configuration:
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
 name: statestore
spec:
 type: state.postgresql
Page 30 of 37
Hackathon II: Spec-Driven Development
 version: v1
 metadata:
 - name: connectionString
 value: "host=neon.db user=... password=... dbname=todo"
Page 31 of 37
Hackathon II: Spec-Driven Development
Use Case 3: Service Invocation (Frontend → Backend)
Built-in service discovery, retries, and mTLS:
Without Dapr:
// Frontend must know backend URL
fetch("http://backend-service:8000/api/chat", {...})
With Dapr:
// Frontend calls via Dapr sidecar – automatic discovery
fetch("http://localhost:3500/v1.0/invoke/backend-service/method/api/chat",
{...})
Use Case 4: Input Bindings (Scheduled Reminders)
Trigger reminder checks on a schedule:
Dapr Cron Binding:
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
Backend Handler:
@app.post("/reminder-cron")
async def check_reminders():
 # Dapr calls this every 5 minutes
 # Check for due tasks and send notifications
 pass
Use Case 5: Secrets Management
Securely store and access credentials:
Dapr Component (Kubernetes Secrets):
apiVersion: dapr.io/v1alpha1
kind: Component
metadata:
 name: kubernetes-secrets
spec:
 type: secretstores.kubernetes
 version: v1
Access in App:
import httpx
response = await httpx.get(
 "http://localhost:3500/v1.0/secrets/kubernetes-secrets/openai-api-key"
)
api_key = response.json()["openai-api-key"]
Page 32 of 37
Hackathon II: Spec-Driven Development
Complete Dapr Architecture
┌───────────────────────────────────────────────────────────────────────────────
───────┐
│ KUBERNETES CLUSTER
│
│
│
│ ┌─────────────────────┐ ┌─────────────────────┐ ┌─────────────────────┐
│
│ │ Frontend Pod │ │ Backend Pod │ │ Notification Pod │
│
│ │ ┌───────┐ ┌───────┐ │ │ ┌───────┐ ┌───────┐ │ │ ┌───────┐ ┌───────┐ │
│
│ │ │ Next │ │ Dapr │ │ │ │FastAPI│ │ Dapr │ │ │ │Notif │ │ Dapr │ │
│
│ │ │ App │◀┼▶Sidecar│ │ │ │+ MCP │◀┼▶Sidecar│ │ │ │Service│◀┼▶Sidecar│ │
│
│ │ └───────┘ └───────┘ │ │ └───────┘ └───────┘ │ │ └───────┘ └───────┘ │
│
│ └──────────┬──────────┘ └──────────┬──────────┘ └──────────┬──────────┘
│
│ │ │ │
│
│ └─────────────────────────┼─────────────────────────┘
│
│ │
│
│ ┌────────────▼────────────┐
│
│ │ DAPR COMPONENTS │
│
│ │ ┌──────────────────┐ │
│
│ │ │ pubsub.kafka │───┼────▶ Redpanda/Kafka
│
│ │ ├──────────────────┤ │
│ │ │ state.postgresql │───┼────▶ Neon DB
│
│ │ ├──────────────────┤ │
│ │ │ bindings.cron │ │ (Scheduled triggers)
│
│ │ ├──────────────────┤ │
│ │ │ secretstores.k8s │ │ (API keys, credentials)
│
│ │ └──────────────────┘ │
│
│ └─────────────────────────┘
│
└───────────────────────────────────────────────────────────────────────────────
───────┘
Dapr Components Summary
Component Type Purpose
kafka-pubsub pubsub.kafka Event streaming (task-events,
reminders)
statestore state.postgresql Conversation state, task cache
reminder-cron bindings.cron Trigger reminder checks
kubernetes-secrets secretstores.kubernetes API keys, DB credentials
Page 33 of 37
Hackathon II: Spec-Driven Development
Why Use Dapr?
Without Dapr With Dapr
Import Kafka, Redis, Postgres libraries Single HTTP API for all
Connection strings in code Dapr components (YAML config)
Manual retry logic Built-in retries, circuit breakers
Service URLs hardcoded Automatic service discovery
Secrets in env vars Secure secret store integration
Vendor lock-in Swap Kafka for RabbitMQ with config change
Local vs Cloud Dapr Usage
Phase Dapr Usage
Local (Minikube) Install Dapr, use Pub/Sub for Kafka, basic state management
Cloud (DigitalOcean) Full Dapr: Pub/Sub, State, Bindings (cron), Secrets, Service
Invocation
Getting Started with Dapr
# Install Dapr CLI
curl -fsSL https://raw.githubusercontent.com/dapr/cli/master/install/install.sh
| bash
# Initialize Dapr on Kubernetes
dapr init -k
# Deploy components
kubectl apply -f dapr-components/
# Run app with Dapr sidecar
dapr run --app-id backend --app-port 8000 -- uvicorn main:app
Bottom Line
Dapr abstracts infrastructure (Kafka, DB, Secrets) behind simple HTTP APIs. Your app code
stays clean, and you can swap backends (e.g., Kafka → RabbitMQ) by changing YAML
config, not code" for more infomation read this pdf "Hackathon II - Todo Spec-Driven Development"

## Response snapshot

Created a comprehensive project constitution for the Todo Chatbot with Kafka and Dapr, incorporating all the required principles and constraints from the user's requirements.

## Outcome

Successfully created a project constitution that defines the core principles for the Todo Chatbot project, including event-driven architecture, Dapr-centric infrastructure, spec-driven development, Kubernetes-native deployment, advanced feature completeness, and security-first approach.

## Tests

none

## Files modified

- .specify/memory/constitution.md

## Next prompts

Consider creating the initial feature specification for the Todo Chatbot project to define the specific user stories and requirements.

## Reflection note

The constitution successfully captures all the key architectural requirements including Kafka for event streaming, Dapr for infrastructure abstraction, and the deployment strategy across Minikube and DigitalOcean Kubernetes.

## Outcome

✅ Impact: Created comprehensive project constitution with 6 core principles
✅ Tests: No tests involved in constitution creation
✅ Files: Updated .specify/memory/constitution.md
✅ Next: Ready to create feature specifications based on this constitution

## Evaluation notes (flywheel)

- Failure modes observed: None; the constitution template was properly filled with all required principles
- Graders run and results (PASS/FAIL): PASS - All required principles and constraints were incorporated
- Prompt variant (if applicable): Standard constitution creation prompt
- Next experiment (smallest change to try): Create the initial feature specification based on these principles