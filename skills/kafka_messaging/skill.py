"""
Kafka Messaging Skill for Todo Chatbot

This skill provides capabilities for producing and consuming messages via Kafka in the Todo Chatbot system.
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

# Try to import aiokafka, but handle gracefully if not available
try:
    import aiokafka
    AIOKAFKA_AVAILABLE = True
except ImportError:
    AIOKAFKA_AVAILABLE = False
    print("Warning: aiokafka not available. Kafka messaging functionality will be disabled.")

class EventType(Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_COMPLETED = "task_completed"
    REMINDER_SCHEDULED = "reminder_scheduled"
    REMINDER_TRIGGERED = "reminder_triggered"
    NOTIFICATION_SENT = "notification_sent"

class KafkaMessagingSkill:
    """
    Skill that provides capabilities for producing and consuming messages via Kafka in the Todo Chatbot system.
    """

    def __init__(self,
                 bootstrap_servers: str = "localhost:9092",
                 task_events_topic: str = "task-events",
                 reminder_events_topic: str = "reminders",
                 task_updates_topic: str = "task-updates"):
        if not AIOKAFKA_AVAILABLE:
            print("KafkaMessagingSkill initialized in disabled mode due to missing aiokafka")

        self.bootstrap_servers = bootstrap_servers
        self.task_events_topic = task_events_topic
        self.reminder_events_topic = reminder_events_topic
        self.task_updates_topic = task_updates_topic
        self.producer = None
        self.consumer = None
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        self.running = False

    async def initialize(self):
        """
        Initialize the Kafka producer.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka Messaging Skill initialized in disabled mode (aiokafka not available)")
            return

        self.producer = aiokafka.AIOKafkaProducer(
            bootstrap_servers=self.bootstrap_servers,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
        await self.producer.start()
        print("Kafka Messaging Skill initialized")

    async def shutdown(self):
        """
        Shutdown the Kafka producer and consumer.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka Messaging Skill shutdown (was in disabled mode)")
            return

        self.running = False
        if self.producer:
            await self.producer.stop()
        if self.consumer:
            await self.consumer.stop()

    async def publish_event(self,
                           event_type: str,
                           task_id: str,
                           user_id: str,
                           data: Dict[str, Any],
                           topic: Optional[str] = None) -> bool:
        """
        Publish an event to Kafka.
        """
        if not AIOKAFKA_AVAILABLE:
            print(f"Kafka disabled: Would publish event {event_type} for task {task_id} to topic (but aiokafka not available)")
            return False

        if not self.producer:
            print("Kafka producer not initialized")
            return False

        event = {
            "event_type": event_type,
            "task_id": task_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Determine the appropriate topic based on event type if not specified
        if not topic:
            if event_type.startswith("reminder"):
                topic = self.reminder_events_topic
            elif event_type.startswith("notification"):
                topic = self.reminder_events_topic
            else:
                topic = self.task_events_topic

        try:
            await self.producer.send_and_wait(topic, event)
            print(f"Event published to {topic}: {event_type} for task {task_id}")
            return True
        except Exception as e:
            print(f"Error publishing event: {e}")
            return False

    async def publish_task_event(self, event_type: EventType, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task-related event to Kafka.
        """
        event_data = {
            "event_type": event_type.value,
            "task_id": task_data.get("id", ""),
            "user_id": task_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "task_data": task_data
        }

        return await self.publish_event(
            event_type=event_type.value,
            task_id=task_data.get("id", ""),
            user_id=task_data.get("user_id", ""),
            data=event_data,
            topic=self.task_events_topic
        )

    async def publish_reminder_event(self, event_type: EventType, reminder_data: Dict[str, Any]) -> bool:
        """
        Publish a reminder-related event to Kafka.
        """
        event_data = {
            "event_type": event_type.value,
            "task_id": reminder_data.get("task_id", ""),
            "user_id": reminder_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "reminder_data": reminder_data
        }

        return await self.publish_event(
            event_type=event_type.value,
            task_id=reminder_data.get("task_id", ""),
            user_id=reminder_data.get("user_id", ""),
            data=event_data,
            topic=self.reminder_events_topic
        )

    async def consume_events(self, topic: str, handler: Callable, group_id: str = "todo-chatbot-group"):
        """
        Start consuming events from a Kafka topic.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot consume events (aiokafka not available)")
            return

        self.consumer = aiokafka.AIOKafkaConsumer(
            topic,
            bootstrap_servers=self.bootstrap_servers,
            group_id=group_id,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        await self.consumer.start()
        self.running = True

        try:
            async for msg in self.consumer:
                event_data = msg.value
                await handler(event_data)
        except Exception as e:
            print(f"Error consuming events: {e}")
        finally:
            await self.consumer.stop()
            self.running = False

    async def consume_task_events(self, handler: Callable, group_id: str = "todo-chatbot-tasks"):
        """
        Start consuming task events from Kafka.
        """
        await self.consume_events(self.task_events_topic, handler, group_id)

    async def consume_reminder_events(self, handler: Callable, group_id: str = "todo-chatbot-reminders"):
        """
        Start consuming reminder events from Kafka.
        """
        await self.consume_events(self.reminder_events_topic, handler, group_id)

    async def consume_task_updates(self, handler: Callable, group_id: str = "todo-chatbot-updates"):
        """
        Start consuming task update events from Kafka.
        """
        await self.consume_events(self.task_updates_topic, handler, group_id)

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
    async def task_created(self, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task created event.
        """
        return await self.publish_task_event(EventType.TASK_CREATED, task_data)

    async def task_updated(self, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task updated event.
        """
        return await self.publish_task_event(EventType.TASK_UPDATED, task_data)

    async def task_deleted(self, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task deleted event.
        """
        return await self.publish_task_event(EventType.TASK_DELETED, task_data)

    async def task_completed(self, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task completed event.
        """
        return await self.publish_task_event(EventType.TASK_COMPLETED, task_data)

    async def reminder_scheduled(self, reminder_data: Dict[str, Any]) -> bool:
        """
        Publish a reminder scheduled event.
        """
        return await self.publish_reminder_event(EventType.REMINDER_SCHEDULED, reminder_data)

    async def reminder_triggered(self, reminder_data: Dict[str, Any]) -> bool:
        """
        Publish a reminder triggered event.
        """
        return await self.publish_reminder_event(EventType.REMINDER_TRIGGERED, reminder_data)

    async def notification_sent(self, notification_data: Dict[str, Any]) -> bool:
        """
        Publish a notification sent event.
        """
        event_data = {
            "event_type": EventType.NOTIFICATION_SENT.value,
            "task_id": notification_data.get("task_id", ""),
            "user_id": notification_data.get("user_id", ""),
            "timestamp": datetime.now().isoformat(),
            "notification_data": notification_data
        }

        return await self.publish_event(
            event_type=EventType.NOTIFICATION_SENT.value,
            task_id=notification_data.get("task_id", ""),
            user_id=notification_data.get("user_id", ""),
            data=event_data,
            topic=self.reminder_events_topic
        )

    async def get_topic_partitions(self, topic: str) -> Optional[int]:
        """
        Get the number of partitions for a topic.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot get topic partitions (aiokafka not available)")
            return None

        if not self.producer:
            return None

        try:
            metadata = await self.producer.client.fetch_metadata()
            for t in metadata.topics:
                if t.topic == topic:
                    return len(t.partitions)
        except Exception as e:
            print(f"Error getting topic partitions: {e}")

        return None

    async def create_topic(self,
                          topic: str,
                          num_partitions: int = 1,
                          replication_factor: int = 1) -> bool:
        """
        Create a new Kafka topic (requires admin client which is not implemented here).
        This is a placeholder method - actual topic creation would require admin client.
        """
        print(f"Topic creation for '{topic}' would require admin client access")
        return False

    async def get_event_stats(self) -> Dict[str, int]:
        """
        Get statistics about published events.
        """
        # This would typically connect to Kafka to get topic information
        # For now, we'll return a placeholder
        return {
            "task_events_published": 0,
            "reminder_events_published": 0,
            "total_events_published": 0
        }

    async def batch_publish_events(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Publish multiple events in a batch.
        """
        results = {
            "success": 0,
            "failed": 0
        }

        for event in events:
            success = await self.publish_event(
                event_type=event.get("event_type", ""),
                task_id=event.get("task_id", ""),
                user_id=event.get("user_id", ""),
                data=event.get("data", {}),
                topic=event.get("topic")
            )
            if success:
                results["success"] += 1
            else:
                results["failed"] += 1

        return results

    async def send_message_with_key(self,
                                   topic: str,
                                   key: str,
                                   value: Dict[str, Any]) -> bool:
        """
        Send a message with a specific key to ensure partitioning.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot send message with key (aiokafka not available)")
            return False

        if not self.producer:
            print("Kafka producer not initialized")
            return False

        try:
            await self.producer.send_and_wait(topic, value=value, key=key.encode('utf-8'))
            print(f"Message sent to {topic} with key {key}")
            return True
        except Exception as e:
            print(f"Error sending message with key: {e}")
            return False

    async def flush_messages(self):
        """
        Flush any pending messages in the producer.
        """
        if not AIOKAFKA_AVAILABLE:
            print("Kafka disabled: Cannot flush messages (aiokafka not available)")
            return

        if self.producer:
            await self.producer.flush()

# Example usage
async def example_event_handler(event_data: Dict[str, Any]):
    """
    Example event handler function.
    """
    print(f"Processing event: {event_data['event_type']} for task {event_data['task_id']}")

async def main():
    skill = KafkaMessagingSkill()

    try:
        # Initialize the skill
        await skill.initialize()

        # Register an example handler
        await skill.register_event_handler(EventType.TASK_CREATED, example_event_handler)

        # Simulate sending a task created event
        task_data = {
            "id": "task123",
            "title": "Sample Task",
            "user_id": "user123",
            "status": "pending",
            "priority": "medium"
        }

        success = await skill.task_created(task_data)
        print(f"Task created event sent successfully: {success}")

        # Simulate sending a reminder scheduled event
        reminder_data = {
            "id": "rem123",
            "task_id": "task123",
            "user_id": "user123",
            "reminder_time": (datetime.now() + timedelta(hours=1)).isoformat()
        }

        success = await skill.reminder_scheduled(reminder_data)
        print(f"Reminder scheduled event sent successfully: {success}")

        # Get topic partitions
        partitions = await skill.get_topic_partitions("task-events")
        print(f"Task events topic has {partitions} partitions")

        # Batch publish example
        events = [
            {
                "event_type": "task_updated",
                "task_id": "task123",
                "user_id": "user123",
                "data": {"status": "in_progress"}
            },
            {
                "event_type": "task_completed",
                "task_id": "task456",
                "user_id": "user123",
                "data": {"completed_at": datetime.now().isoformat()}
            }
        ]

        batch_results = await skill.batch_publish_events(events)
        print(f"Batch publish results: {batch_results}")

    except Exception as e:
        print(f"Error in Kafka skill: {e}")
    finally:
        # Shutdown the skill
        await skill.shutdown()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())