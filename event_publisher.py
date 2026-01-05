"""
Event Publisher for Todo Chatbot System

This component facilitates communication between agents and skills through event publishing.
"""

import asyncio
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

class EventType(Enum):
    TASK_CREATED = "task_created"
    TASK_UPDATED = "task_updated"
    TASK_DELETED = "task_deleted"
    TASK_COMPLETED = "task_completed"
    REMINDER_SCHEDULED = "reminder_scheduled"
    REMINDER_TRIGGERED = "reminder_triggered"
    NOTIFICATION_SENT = "notification_sent"
    USER_REGISTERED = "user_registered"
    USER_LOGGED_IN = "user_logged_in"
    USER_LOGGED_OUT = "user_logged_out"

class EventPublisher:
    """
    Event publisher that allows agents and skills to communicate through events.
    """

    def __init__(self):
        self.handlers: Dict[EventType, List[Callable]] = {}
        self.event_queue = asyncio.Queue()
        self.running = False

    def subscribe(self, event_type: EventType, handler: Callable):
        """
        Subscribe a handler to an event type.
        """
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)

    def unsubscribe(self, event_type: EventType, handler: Callable):
        """
        Unsubscribe a handler from an event type.
        """
        if event_type in self.handlers and handler in self.handlers[event_type]:
            self.handlers[event_type].remove(handler)

    async def publish_event(self, event_type: EventType, task_id: str, user_id: str, data: Dict[str, Any]):
        """
        Publish an event to all subscribed handlers.
        """
        event = {
            "event_type": event_type.value,
            "task_id": task_id,
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }

        # Add to queue for async processing
        await self.event_queue.put(event)

        # Process immediately as well
        await self._process_event(event)

    async def _process_event(self, event: Dict[str, Any]):
        """
        Process an event by calling all subscribed handlers.
        """
        event_type_str = event.get("event_type")
        try:
            event_type = EventType(event_type_str)
        except ValueError:
            print(f"Unknown event type: {event_type_str}")
            return

        handlers = self.handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                print(f"Error in event handler: {e}")

    async def start_processing(self):
        """
        Start processing events from the queue.
        """
        self.running = True
        while self.running:
            try:
                event = await self.event_queue.get()
                await self._process_event(event)
                self.event_queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing event: {e}")

    async def stop_processing(self):
        """
        Stop processing events.
        """
        self.running = False