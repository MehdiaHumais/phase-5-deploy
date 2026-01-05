"""
Notification/Reminder Agent for Todo Chatbot

This agent handles all notification and reminder operations including:
- Scheduling reminders for tasks with due dates
- Sending notifications to users
- Managing recurring task reminders
- Processing reminder events from the event queue
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class NotificationType(Enum):
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    IN_APP = "in_app"

class ReminderFrequency(Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

@dataclass
class Reminder:
    id: str
    task_id: str
    user_id: str
    notification_type: NotificationType
    reminder_time: datetime
    message: str
    frequency: ReminderFrequency = ReminderFrequency.ONCE
    is_active: bool = True
    created_at: datetime = None

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class Notification:
    id: str
    user_id: str
    notification_type: NotificationType
    title: str
    message: str
    sent_at: datetime = None
    is_delivered: bool = False

class NotificationReminderAgent:
    """
    Agent responsible for managing notifications and reminders in the Todo Chatbot system.
    """

    def __init__(self, event_queue: asyncio.Queue = None):
        self.reminders: Dict[str, Reminder] = {}
        self.notifications: Dict[str, Notification] = {}
        self.event_queue = event_queue or asyncio.Queue()
        self.active_reminders = set()
        self.notification_handlers = {
            NotificationType.EMAIL: self._send_email,
            NotificationType.SMS: self._send_sms,
            NotificationType.PUSH: self._send_push,
            NotificationType.IN_APP: self._send_in_app
        }

    async def create_reminder(self,
                             task_id: str,
                             user_id: str,
                             notification_type: NotificationType,
                             reminder_time: datetime,
                             message: str,
                             frequency: ReminderFrequency = ReminderFrequency.ONCE) -> Reminder:
        """
        Create a new reminder for a task.
        """
        import uuid
        reminder_id = str(uuid.uuid4())

        reminder = Reminder(
            id=reminder_id,
            task_id=task_id,
            user_id=user_id,
            notification_type=notification_type,
            reminder_time=reminder_time,
            message=message,
            frequency=frequency
        )

        self.reminders[reminder_id] = reminder

        # Schedule the reminder
        await self._schedule_reminder(reminder)

        return reminder

    async def _schedule_reminder(self, reminder: Reminder):
        """
        Schedule a reminder to be triggered at the specified time.
        """
        delay = (reminder.reminder_time - datetime.now()).total_seconds()

        if delay > 0:
            self.active_reminders.add(reminder.id)
            await asyncio.sleep(delay)
            await self._trigger_reminder(reminder)

    async def _trigger_reminder(self, reminder: Reminder):
        """
        Trigger a reminder by sending the notification.
        """
        if not reminder.is_active or reminder.id not in self.active_reminders:
            return

        # Send notification
        await self._send_notification(
            user_id=reminder.user_id,
            notification_type=reminder.notification_type,
            title=f"Task Reminder: {reminder.task_id}",
            message=reminder.message
        )

        # Handle recurring reminders
        if reminder.frequency != ReminderFrequency.ONCE:
            await self._reschedule_reminder(reminder)

        # Remove from active reminders
        self.active_reminders.discard(reminder.id)

    async def _reschedule_reminder(self, reminder: Reminder):
        """
        Reschedule a recurring reminder.
        """
        import uuid
        new_reminder_time = None

        if reminder.frequency == ReminderFrequency.DAILY:
            new_reminder_time = reminder.reminder_time + timedelta(days=1)
        elif reminder.frequency == ReminderFrequency.WEEKLY:
            new_reminder_time = reminder.reminder_time + timedelta(weeks=1)
        elif reminder.frequency == ReminderFrequency.MONTHLY:
            # Simple monthly rescheduling (same day next month)
            from datetime import date
            current_date = reminder.reminder_time.date()
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (1 if next_month == 1 else 0)
            try:
                new_reminder_date = date(next_year, next_month, current_date.day)
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30th)
                import calendar
                max_day = calendar.monthrange(next_year, next_month)[1]
                new_reminder_date = date(next_year, next_month, max_day)
            new_reminder_time = datetime.combine(new_reminder_date, reminder.reminder_time.time())
        else:
            # For custom frequency, we'd need more complex logic
            return

        if new_reminder_time:
            new_reminder = Reminder(
                id=str(uuid.uuid4()),
                task_id=reminder.task_id,
                user_id=reminder.user_id,
                notification_type=reminder.notification_type,
                reminder_time=new_reminder_time,
                message=reminder.message,
                frequency=reminder.frequency,
                is_active=True
            )
            self.reminders[new_reminder.id] = new_reminder
            await self._schedule_reminder(new_reminder)

    async def _send_notification(self,
                                user_id: str,
                                notification_type: NotificationType,
                                title: str,
                                message: str) -> bool:
        """
        Send a notification using the appropriate handler.
        """
        try:
            handler = self.notification_handlers.get(notification_type)
            if handler:
                await handler(user_id, title, message)

                # Record the notification
                import uuid
                notification_id = str(uuid.uuid4())
                notification = Notification(
                    id=notification_id,
                    user_id=user_id,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    sent_at=datetime.now(),
                    is_delivered=True
                )
                self.notifications[notification_id] = notification

                # Publish notification sent event
                await self._publish_event("notification_sent", {
                    "notification_id": notification_id,
                    "user_id": user_id,
                    "notification_type": notification_type.value,
                    "title": title
                })

                return True
            else:
                print(f"No handler found for notification type: {notification_type}")
                return False
        except Exception as e:
            print(f"Error sending notification: {e}")
            return False

    async def _send_email(self, user_id: str, title: str, message: str):
        """
        Send an email notification (placeholder implementation).
        """
        print(f"Sending email to user {user_id}: {title} - {message}")
        # In a real implementation, you would use aiosmtplib to send emails
        # This is a placeholder that just prints the action

    async def _send_sms(self, user_id: str, title: str, message: str):
        """
        Send an SMS notification (placeholder implementation).
        """
        print(f"Sending SMS to user {user_id}: {title} - {message}")
        # In a real implementation, you would use a service like Twilio
        # This is a placeholder that just prints the action

    async def _send_push(self, user_id: str, title: str, message: str):
        """
        Send a push notification (placeholder implementation).
        """
        print(f"Sending push notification to user {user_id}: {title} - {message}")
        # In a real implementation, you would use a service like Firebase Cloud Messaging
        # This is a placeholder that just prints the action

    async def _send_in_app(self, user_id: str, title: str, message: str):
        """
        Send an in-app notification (placeholder implementation).
        """
        print(f"Sending in-app notification to user {user_id}: {title} - {message}")
        # In a real implementation, you would store the notification in a database
        # and the frontend would fetch and display it
        # This is a placeholder that just prints the action

    async def get_reminders_for_user(self, user_id: str) -> List[Reminder]:
        """
        Get all reminders for a specific user.
        """
        return [reminder for reminder in self.reminders.values() if reminder.user_id == user_id]

    async def cancel_reminder(self, reminder_id: str) -> bool:
        """
        Cancel a reminder by its ID.
        """
        if reminder_id in self.reminders:
            reminder = self.reminders[reminder_id]
            reminder.is_active = False
            self.active_reminders.discard(reminder_id)

            # Publish reminder cancelled event
            await self._publish_event("reminder_cancelled", {
                "reminder_id": reminder_id,
                "task_id": reminder.task_id,
                "user_id": reminder.user_id
            })

            return True
        return False

    async def process_task_events(self):
        """
        Process task events from the event queue to create appropriate reminders.
        """
        while True:
            try:
                event = await self.event_queue.get()
                await self._handle_task_event(event)
                self.event_queue.task_done()
            except Exception as e:
                print(f"Error processing task event: {e}")
                continue

    async def _handle_task_event(self, event: Dict[str, Any]):
        """
        Handle task events to create or update reminders.
        """
        event_type = event.get("event_type")
        data = event.get("data", {})

        if event_type == "task_created":
            await self._handle_task_created(data)
        elif event_type == "task_updated":
            await self._handle_task_updated(data)
        elif event_type == "task_deleted":
            await self._handle_task_deleted(data)

    async def _handle_task_created(self, data: Dict[str, Any]):
        """
        Handle task created event to set up reminders if needed.
        """
        task_data = data.get("task_data", {})
        due_date = task_data.get("due_date")

        if due_date:
            # Parse the due date string if it's a string
            if isinstance(due_date, str):
                due_date = datetime.fromisoformat(due_date.replace('Z', '+00:00'))

            # Create a reminder 1 hour before due date
            reminder_time = due_date - timedelta(hours=1)

            # Only create reminder if it's in the future
            if reminder_time > datetime.now():
                await self.create_reminder(
                    task_id=data["task_id"],
                    user_id=data["user_id"],
                    notification_type=NotificationType.IN_APP,  # Default to in-app
                    reminder_time=reminder_time,
                    message=f"Task '{task_data.get('title', 'Untitled')}' is due soon!"
                )

    async def _handle_task_updated(self, data: Dict[str, Any]):
        """
        Handle task updated event to update reminders if needed.
        """
        # For now, just log the event
        print(f"Task updated event received: {data['task_id']}")

    async def _handle_task_deleted(self, data: Dict[str, Any]):
        """
        Handle task deleted event to cancel associated reminders.
        """
        # Cancel all reminders for this task
        for reminder_id, reminder in list(self.reminders.items()):
            if reminder.task_id == data["task_id"]:
                await self.cancel_reminder(reminder_id)

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to the event queue.
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        # Note: We don't put this back on the same queue to avoid circular processing
        print(f"Event published: {event_type} - {data}")

    async def start_processing(self):
        """
        Start processing events in the background.
        """
        print("Notification/Reminder agent started")
        await self.process_task_events()

# Example usage
async def main():
    # Create a shared event queue
    event_queue = asyncio.Queue()

    # Create the notification/reminder agent
    agent = NotificationReminderAgent(event_queue=event_queue)

    # Simulate a task created event
    task_created_event = {
        "event_type": "task_created",
        "timestamp": datetime.now().isoformat(),
        "data": {
            "task_id": "task123",
            "user_id": "user123",
            "task_data": {
                "title": "Complete project",
                "due_date": (datetime.now() + timedelta(minutes=1)).isoformat()
            }
        }
    }

    # Put the event in the queue
    await event_queue.put(task_created_event)

    # Process the event
    await agent._handle_task_event(task_created_event["data"])

    print("Notification/Reminder agent created and configured")

if __name__ == "__main__":
    asyncio.run(main())