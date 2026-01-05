# Todo Chatbot with Kafka and Dapr

This project implements a Todo Chatbot system with advanced features using Kafka for event streaming and Dapr for distributed application runtime.

## Architecture Overview

The system is built using a modular architecture with agents and skills that work together through event-driven communication:

### Agents
- **Task Management Agent**: Handles all task-related operations (create, update, delete, search)
- **Notification/Reminder Agent**: Manages scheduling and delivery of reminders
- **Kafka Event Processing Agent**: Handles event production and consumption via Kafka
- **Dapr Service Invocation Agent**: Provides integration with Dapr building blocks
- **User Interface Agent**: Processes user commands and generates responses

### Skills
- **Task Creation/Deletion Skill**: Provides core task management capabilities
- **Reminder Scheduling Skill**: Handles reminder creation and management
- **Kafka Messaging Skill**: Provides Kafka publishing/subscribing capabilities
- **Dapr Integration Skill**: Integrates with Dapr state, pub/sub, and secrets
- **User Authentication Skill**: Handles user registration, login, and permissions

## System Integration

All components are connected through the `TodoChatbotOrchestrator` which:

1. Initializes all agents and skills
2. Connects them using the `EventPublisher` for communication
3. Provides high-level methods that coordinate multiple components
4. Handles authentication and authorization flows

## Event-Driven Architecture

The system uses an event-driven approach where:
- Tasks, reminders, and notifications are published as events to Kafka
- Components subscribe to relevant events and react accordingly
- State changes trigger appropriate actions across the system

## Dapr Integration

All infrastructure dependencies are abstracted through Dapr:
- State management through Dapr state stores
- Service invocation through Dapr service discovery
- Secret management through Dapr secret stores
- Pub/Sub messaging through Dapr pub/sub components

## Advanced Features

The system implements all the advanced features specified in the project requirements:

### Recurring Tasks
- Tasks can be configured to recur on daily, weekly, or monthly basis
- Implemented through the Reminder Scheduling Skill

### Due Dates & Reminders
- Tasks can have due dates with configurable reminder timing
- Multiple notification channels (email, SMS, push, in-app)
- Implemented through the Reminder Scheduling Skill and Notification Agent

### Priorities, Tags, Search, Filter, Sort
- Tasks can be assigned priorities (low, medium, high, urgent)
- Tasks can be tagged and searched by tags
- Advanced filtering and sorting capabilities
- Implemented through the Task Management Agent and Skill

### Event-Driven Architecture
- All operations publish events to Kafka
- Components react to events asynchronously
- Implemented through Kafka agents and skills

## Deployment

The system is designed for Kubernetes deployment with:
- Dapr sidecars for each service
- Kafka for event streaming
- State stores for persistence
- Service discovery and invocation through Dapr

## Getting Started

### Quick Setup

For a quick setup, run the installation script appropriate for your platform:

**Linux/macOS:**
```bash
chmod +x scripts/setup/install-dependencies.sh
./scripts/setup/install-dependencies.sh
```

**Windows (PowerShell as Administrator):**
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
.\scripts\setup\install-dependencies.ps1
```

Then validate your setup:
```bash
# Linux/macOS
./scripts/setup/validate-setup.sh

# Windows
.\scripts\setup\validate-setup.ps1
```

### Manual Setup

1. Install Dapr on your Kubernetes cluster
2. Set up Kafka (Redpanda Cloud recommended)
3. Deploy the services with Dapr sidecars
4. Configure Dapr components for state, pub/sub, and secrets
5. Scale services independently based on load

### Running the Application

For development, you can run the application using Docker Compose:

```bash
docker-compose up -d
```

Or run directly with Dapr:
```bash
dapr run --app-id todo-api --app-port 8000 -- uvicorn main:app --reload
```

For more detailed instructions, see the [Quickstart Guide](docs/quickstart.md).

## Files Structure

```
agents/                    # Individual agents
├── task-management/       # Task management agent
├── notification-reminder/ # Notification and reminder agent
├── kafka-event-processing/ # Kafka event processing agent
├── dapr-service-invocation/ # Dapr service invocation agent
└── user-interface/       # User interface agent

skills/                   # Individual skills
├── task-creation-deletion/ # Task creation/deletion skill
├── reminder-scheduling/  # Reminder scheduling skill
├── kafka-messaging/      # Kafka messaging skill
├── dapr-integration/     # Dapr integration skill
└── user-authentication/  # User authentication skill

event_publisher.py        # Event publishing and subscription
main_orchestrator.py      # Main orchestrator connecting all components
test_integration.py       # Integration test script
README.md                 # This file
```

## Key Components Connection

The main orchestrator connects all components as follows:

1. **Event Publisher** connects all agents and skills through event subscription
2. **UI Agent** connects to Task Management Agent for command processing
3. **Task Skill** connects to Event Publisher to publish task events
4. **Reminder Skill** connects to Event Publisher to publish reminder events
5. **Authentication Skill** connects to Dapr Integration Skill for state management
6. **Kafka components** handle event streaming between services
7. **Dapr components** provide infrastructure abstraction

This architecture ensures loose coupling between components while maintaining high cohesion within each agent and skill.