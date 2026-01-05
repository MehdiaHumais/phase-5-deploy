"""
Kafka Event Processing Agent for Todo Chatbot

This agent handles all Kafka-related operations including:
- Producing events to Kafka topics
- Consuming events from Kafka topics
- Processing task events (created, updated, deleted)
- Processing reminder events
- Managing event schemas and validation
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum

# Try to import aiokafka, but handle gracefully if not available
try:
    import aiokafka
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    print("Warning: aiokafka not available. Kafka functionality will be disabled.")

class EventType(Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_COMPLETED = "task_completed"
    REMINDER_SCHEDULED = "reminder_scheduled"
    REMINDER_TRIGGERED = "reminder_triggered"
    NOTIFICATION_SENT = "notification_sent"

@dataclass
class Event:
    event_type: str
    task_id: str
    user_id: str
    timestamp: datetime
    data: Dict[str, Any]

class KafkaEventProcessingAgent:
    """
    Agent responsible for processing events through Kafka in the Todo Chatbot system.
    """

    def __init__(self,
                 bootstrap_servers: str = "localhost:9092",
                 task_events_topic: str = "task-events",
                 reminder_events_topic: str = "reminders",
                 task_updates_topic: str = "task-updates"):
        if not AIOKAFKA_AVAILABLE:
            print("KafkaEventProcessingAgent initialized in disabled mode due to missing aiokafka")

        self.bootstrap_servers = bootstrap_servers
        self.task_events_topic = task_events_topic
        self.reminder_events_topic = reminder_events_topic
        self.task_updates_topic = task_updates_topic
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.producer = None
        self.consumer = None
        self.running = False

    async def start(self):
        """
        Start the Kafka event processing agent.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka Event Processing Agent started in disabled mode (aiokafka not available)")
            return

        # Initialize Kafka producer
        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()

        print("Kafka Event Processing Agent started")

    async def stop(self):
        """
        Stop the Kafka event processing agent.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka Event Processing Agent stopped (was in disabled mode)")
            return

        self.running = False
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()

        print("Kafka Event Processing Agent stopped")

    async def send_event(self, event_type: str, task_id: str, user_id: str, data: Dict[str, Any]):
        """
        Send an event to the appropriate Kafka topic.
        """
        if not AIOKAFKA_AVAILABLE:
            print(f"Kafka disabled: Would send event {event_type} for task {task_id} to topic (but aiokafka not available)")
            return

        event = {
            "event_type": event_type,
            "task_id": task_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Determine the appropriate topic based on event type
        if event_type.startswith("reminder"):
            topic = self.reminder_events_topic
        elif event_type.startswith("notification"):
            topic = self.reminder_events_topic
        else:
            topic = self.task_events_topic

        try:
            await self.producer.send_and_wait(topic, event)
            print(f"Event sent to {topic}: {event_type} for task {task_id}")
        except Exception as e:
            print(f"Error sending event: {e}")
            raise

    async def send_task_event(self, event_type: EventType, task_data: Dict[str, Any]):
        """
        Send a task-related event to Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print(f"Kafka disabled: Would send task event {event_type.value} for task {task_data.get('id')} (but aiokafka not available)")
            return

        event_data = {
            "event_type": event_type.value,
            "task_id": task_data.get("id", ""),
            "user_id": task_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "task_data": task_data
        }

        await self.producer.send_and_wait(self.task_events_topic, event_data)
        print(f"Task event sent: {event_type.value} for task {task_data.get('id')}")

    async def send_reminder_event(self, event_type: EventType, reminder_data: Dict[str, Any]):
        """
        Send a reminder-related event to Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print(f"Kafka disabled: Would send reminder event {event_type.value} for task {reminder_data.get('task_id')} (but aiokafka not available)")
            return

        event_data = {
            "event_type": event_type.value,
            "task_id": reminder_data.get("task_id", ""),
            "user_id": reminder_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "reminder_data": reminder_data
        }

        await self.producer.send_and_wait(self.reminder_events_topic, event_data)
        print(f"Reminder event sent: {event_type.value} for task {reminder_data.get('task_id')}")

    async def consume_task_events(self, handler: Callable):
        """
        Start consuming task events from Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot consume task events (aiokafka not available)")
            return

        self.consumer = aiokafka.AIOKafkaConsumer(
            self.task_events_topic,
            bootstrap_servers=self.bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        await self.consumer.start()

        try:
            async for msg in self.consumer:
                event_data = msg.value
                await handler(event_data)
        except Exception as e:
            print(f"Error consuming task events: {e}")
        finally:
            await self.consumer.stop()

    async def consume_reminder_events(self, handler: Callable):
        """
        Start consuming reminder events from Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot consume reminder events (aiokafka not available)")
            return

        if not self.consumer:
            self.consumer = aiokafka.AIOKafkaConsumer(
                self.reminder_events_topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()

        try:
            async for msg in self.consumer:
                event_data = msg.value
                await handler(event_data)
        except Exception as e:
            print(f"Error consuming reminder events: {e}")

    async def consume_task_updates(self, handler: Callable):
        """
        Start consuming task update events from Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot consume task updates (aiokafka not available)")
            return

        if not self.consumer:
            self.consumer = aiokafka.AIOKafkaConsumer(
                self.task_updates_topic,
                bootstrap_servers=self.bootstrap_servers,
                value_deserializer=lambda v: json.loads(v.decode('utf-8'))
            )
            await self.consumer.start()

        try:
            async for msg in self.consumer:
                event_data = msg.value
                await handler(event_data)
        except Exception as e:
            print(f"Error consuming task updates: {e}")

    async def register_event_handler(self, event_type: EventType, handler: Callable):
        """
        Register a handler for a specific event type.
        """
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)

    async def process_event(self, event_data: Dict[str, Any]):
        """
        Process an incoming event based on its type.
        """
        event_type_str = event_data.get("event_type")

        try:
            event_type = EventType(event_type_str)
        except ValueError:
            print(f"Unknown event type: {event_type_str}")
            return

        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event_data)
            except Exception as e:
                print(f"Error processing event with handler: {e}")

    async def validate_event_schema(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate that the event conforms to the expected schema.
        """
        required_fields = ["event_type", "task_id", "user_id", "timestamp", "data"]
        for field in required_fields:
            if field not in event_data:
                print(f"Missing required field in event: {field}")
                return False
        return True

    # Specific event publishing methods
    async def task_created(self, task_data: Dict[str, Any]):
        """
        Publish a task created event.
        """
        await self.send_task_event(EventType.TASK_CREATED, task_data)

    async def task_updated(self, task_data: Dict[str, Any]):
        """
        Publish a task updated event.
        """
        await self.send_task_event(EventType.TASK_UPDATED, task_data)

    async def task_deleted(self, task_data: Dict[str, Any]):
        """
        Publish a task deleted event.
        """
        await self.send_task_event(EventType.TASK_DELETED, task_data)

    async def task_completed(self, task_data: Dict[str, Any]):
        """
        Publish a task completed event.
        """
        await self.send_task_event(EventType.TASK_COMPLETED, task_data)

    async def reminder_scheduled(self, reminder_data: Dict[str, Any]):
        """
        Publish a reminder scheduled event.
        """
        await self.send_reminder_event(EventType.REMINDER_SCHEDULED, reminder_data)

    async def reminder_triggered(self, reminder_data: Dict[str, Any]):
        """
        Publish a reminder triggered event.
        """
        await self.send_reminder_event(EventType.REMINDER_TRIGGERED, reminder_data)

    async def notification_sent(self, notification_data: Dict[str, Any]):
        """
        Publish a notification sent event.
        """
        if not AIOKAFKA_AVAILABLE:
            print(f"Kafka disabled: Would publish notification sent event for user {notification_data.get('user_id')} (but aiokafka not available)")
            return

        event_data = {
            "event_type": EventType.NOTIFICATION_SENT.value,
            "task_id": notification_data.get("task_id", ""),
            "user_id": notification_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "notification_data": notification_data
        }

        await self.producer.send_and_wait(self.reminder_events_topic, event_data)
        print(f"Notification sent event published for user {notification_data.get('user_id')}")

    async def get_event_stats(self) -> Dict[str, int]:
        """
        Get statistics about processed events.
        """
        # This would typically connect to Kafka to get topic information
        # For now, we'll return a placeholder
        return {
            "task_events_processed": 0,
            "reminder_events_processed": 0,
            "total_events_processed": 0
        }

# Example usage and testing
async def example_event_handler(event_data: Dict[str, Any]):
    """
    Example event handler function.
    """
    print(f"Processing event: {event_data['event_type']} for task {event_data['task_id']}")

async def main():
    # Create the Kafka event processing agent
    agent = KafkaEventProcessingAgent()

    try:
        # Start the agent
        await agent.start()

        # Register an example handler
        await agent.register_event_handler(EventType.TASK_CREATED, example_event_handler)

        # Simulate sending a task created event
        task_data = {
            "id": "task123",
            "title": "Sample Task",
            "user_id": "user123",
            "status": "pending",
            "priority": "medium"
        }

        await agent.task_created(task_data)
        print("Task created event sent successfully")

        # Simulate sending a reminder scheduled event
        reminder_data = {
            "id": "rem123",
            "task_id": "task123",
            "user_id": "user123",
            "reminder_time": (datetime.now() +  timedelta(hours=1)).isoformat()
        }

        await agent.reminder_scheduled(reminder_data)
        print("Reminder scheduled event sent successfully")

    except Exception as e:
        print(f"Error in Kafka agent: {e}")
    finally:
        # Stop the agent
        await agent.stop()

if __name__ == "__main__":
    asyncio.run(main())