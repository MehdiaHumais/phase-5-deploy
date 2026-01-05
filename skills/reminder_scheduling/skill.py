"""
Reminder Scheduling Skill for Todo Chatbot

This skill provides capabilities for scheduling and managing reminders in the Todo Chatbot system.
"""

import asyncio
import uuid
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from enum import Enum

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

class ReminderSchedulingSkill:
    """
    Skill that provides capabilities for scheduling and managing reminders in the Todo Chatbot system.
    """

    def __init__(self):
        self.reminders: Dict[str, Dict[str, Any]] = {}
        self.active_reminders: Dict[str, asyncio.Task] = {}
        self.event_publisher = None

    def set_event_publisher(self, event_publisher):
        """
        Set the event publisher for this skill.
        """
        self.event_publisher = event_publisher

    async def create_reminder(self,
                             task_id: str,
                             user_id: str,
                             notification_type: NotificationType,
                             reminder_time: datetime,
                             message: str,
                             frequency: ReminderFrequency = ReminderFrequency.ONCE,
                             title: str = "") -> Dict[str, Any]:
        """
        Create a new reminder for a task.
        """
        reminder_id = str(uuid.uuid4())

        reminder = {
            "id": reminder_id,
            "task_id": task_id,
            "user_id": user_id,
            "notification_type": notification_type.value,
            "reminder_time": reminder_time.isoformat(),
            "message": message,
            "title": title or f"Reminder for task {task_id}",
            "frequency": frequency.value,
            "is_active": True,
            "created_at": datetime.now().isoformat(),
            "last_triggered": None,
            "next_scheduled": reminder_time.isoformat()
        }

        self.reminders[reminder_id] = reminder

        # Schedule the reminder
        await self._schedule_reminder(reminder_id, reminder_time)

        # Publish reminder scheduled event if event publisher is available
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="reminder_scheduled",
                task_id=task_id,
                user_id=user_id,
                data=reminder
            )

        return reminder

    async def _schedule_reminder(self, reminder_id: str, reminder_time: datetime):
        """
        Schedule a reminder to be triggered at the specified time.
        """
        delay = (reminder_time - datetime.now()).total_seconds()

        if delay > 0:
            # Cancel any existing scheduled task for this reminder
            if reminder_id in self.active_reminders:
                self.active_reminders[reminder_id].cancel()

            # Create a new scheduled task
            task = asyncio.create_task(self._wait_and_trigger(reminder_id, delay))
            self.active_reminders[reminder_id] = task

    async def _wait_and_trigger(self, reminder_id: str, delay: float):
        """
        Wait for the specified delay and then trigger the reminder.
        """
        await asyncio.sleep(delay)
        await self._trigger_reminder(reminder_id)

    async def _trigger_reminder(self, reminder_id: str):
        """
        Trigger a reminder by publishing a notification event.
        """
        if reminder_id not in self.reminders:
            return

        reminder = self.reminders[reminder_id]

        if not reminder["is_active"]:
            return

        # Update the last triggered time
        self.reminders[reminder_id]["last_triggered"] = datetime.now().isoformat()

        # Handle recurring reminders
        if reminder["frequency"] != ReminderFrequency.ONCE.value:
            await self._reschedule_reminder(reminder_id)

        # Publish reminder triggered event
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="reminder_triggered",
                task_id=reminder["task_id"],
                user_id=reminder["user_id"],
                data=reminder
            )

    async def _reschedule_reminder(self, reminder_id: str):
        """
        Reschedule a recurring reminder.
        """
        if reminder_id not in self.reminders:
            return

        reminder = self.reminders[reminder_id]
        current_time = datetime.fromisoformat(reminder["reminder_time"])
        new_reminder_time = None

        if reminder["frequency"] == ReminderFrequency.DAILY.value:
            new_reminder_time = current_time + timedelta(days=1)
        elif reminder["frequency"] == ReminderFrequency.WEEKLY.value:
            new_reminder_time = current_time + timedelta(weeks=1)
        elif reminder["frequency"] == ReminderFrequency.MONTHLY.value:
            # Simple monthly rescheduling (same day next month)
            from datetime import date
            current_date = current_time.date()
            next_month = current_date.month % 12 + 1
            next_year = current_date.year + (1 if next_month == 1 else 0)
            try:
                new_reminder_date = date(next_year, next_month, current_date.day)
            except ValueError:
                # Handle months with fewer days (e.g., Feb 30th)
                import calendar
                max_day = calendar.monthrange(next_year, next_month)[1]
                new_reminder_date = date(next_year, next_month, max_day)
            new_reminder_time = datetime.combine(new_reminder_date, current_time.time())
        else:
            # For custom frequency, we'd need more complex logic
            return

        if new_reminder_time:
            # Update the reminder's next scheduled time
            self.reminders[reminder_id]["next_scheduled"] = new_reminder_time.isoformat()
            self.reminders[reminder_id]["reminder_time"] = new_reminder_time.isoformat()

            # Reschedule the reminder
            await self._schedule_reminder(reminder_id, new_reminder_time)

    async def get_reminder(self, reminder_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a reminder by its ID.
        """
        return self.reminders.get(reminder_id)

    async def get_reminders_for_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        Get all reminders for a specific task.
        """
        return [
            reminder for reminder in self.reminders.values()
            if reminder["task_id"] == task_id
        ]

    async def get_reminders_for_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all reminders for a specific user.
        """
        return [
            reminder for reminder in self.reminders.values()
            if reminder["user_id"] == user_id
        ]

    async def cancel_reminder(self, reminder_id: str, user_id: str = None) -> bool:
        """
        Cancel a reminder by its ID.
        """
        if reminder_id not in self.reminders:
            return False

        reminder = self.reminders[reminder_id]

        # Check if user has permission to cancel this reminder
        if user_id and reminder["user_id"] != user_id:
            return False

        # Mark as inactive
        self.reminders[reminder_id]["is_active"] = False

        # Cancel the scheduled task if it exists
        if reminder_id in self.active_reminders:
            self.active_reminders[reminder_id].cancel()
            del self.active_reminders[reminder_id]

        # Publish reminder cancelled event if event publisher is available
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="reminder_cancelled",
                task_id=reminder["task_id"],
                user_id=reminder["user_id"],
                data={"id": reminder_id}
            )

        return True

    async def cancel_reminders_for_task(self, task_id: str, user_id: str = None) -> int:
        """
        Cancel all reminders for a specific task.
        """
        reminder_ids = [
            rid for rid, reminder in self.reminders.items()
            if reminder["task_id"] == task_id and (not user_id or reminder["user_id"] == user_id)
        ]

        cancelled_count = 0
        for reminder_id in reminder_ids:
            if await self.cancel_reminder(reminder_id, user_id):
                cancelled_count += 1

        return cancelled_count

    async def update_reminder(self, reminder_id: str, **updates) -> Optional[Dict[str, Any]]:
        """
        Update a reminder with the provided fields.
        """
        if reminder_id not in self.reminders:
            return None

        reminder = self.reminders[reminder_id]

        # Check if this is the reminder owner
        # (In a real system, you'd have proper authentication here)

        # Update reminder fields
        for field, value in updates.items():
            if field in reminder:
                reminder[field] = value

        # If reminder time was updated, reschedule it
        if "reminder_time" in updates:
            new_time = datetime.fromisoformat(updates["reminder_time"])
            await self._schedule_reminder(reminder_id, new_time)

        return reminder

    async def create_due_date_reminder(self,
                                      task_id: str,
                                      user_id: str,
                                      due_date: datetime,
                                      notification_type: NotificationType = NotificationType.IN_APP,
                                      reminder_offset: timedelta = timedelta(hours=1),
                                      custom_message: str = None) -> Optional[Dict[str, Any]]:
        """
        Create a reminder based on a task's due date.
        """
        reminder_time = due_date - reminder_offset

        # Only create reminder if it's in the future
        if reminder_time <= datetime.now():
            return None

        message = custom_message or f"Task '{task_id}' is due soon!"
        title = f"Due Date Reminder: {task_id}"

        reminder = await self.create_reminder(
            task_id=task_id,
            user_id=user_id,
            notification_type=notification_type,
            reminder_time=reminder_time,
            message=message,
            title=title
        )

        # Create an additional overdue reminder to check if task is completed after due date
        overdue_reminder_time = due_date + timedelta(minutes=5)  # Check 5 minutes after due date
        if overdue_reminder_time > datetime.now():
            overdue_message = f"Task '{task_id}' was due at {due_date.strftime('%H:%M')} and may be overdue!"
            overdue_title = f"Overdue Task Check: {task_id}"

            await self.create_reminder(
                task_id=task_id,
                user_id=user_id,
                notification_type=notification_type,
                reminder_time=overdue_reminder_time,
                message=overdue_message,
                title=overdue_title
            )

        return reminder

    async def create_recurring_reminder(self,
                                       task_id: str,
                                       user_id: str,
                                       start_time: datetime,
                                       frequency: ReminderFrequency,
                                       message: str,
                                       notification_type: NotificationType = NotificationType.IN_APP,
                                       title: str = "") -> Dict[str, Any]:
        """
        Create a recurring reminder for a task.
        """
        return await self.create_reminder(
            task_id=task_id,
            user_id=user_id,
            notification_type=notification_type,
            reminder_time=start_time,
            message=message,
            frequency=frequency,
            title=title
        )

    async def get_upcoming_reminders(self,
                                    user_id: str = None,
                                    within_minutes: int = 60) -> List[Dict[str, Any]]:
        """
        Get reminders that are scheduled to trigger within the specified time window.
        """
        now = datetime.now()
        future_time = now + timedelta(minutes=within_minutes)

        upcoming = []
        for reminder in self.reminders.values():
            reminder_time = datetime.fromisoformat(reminder["reminder_time"])
            if (now < reminder_time <= future_time and
                reminder["is_active"] and
                (not user_id or reminder["user_id"] == user_id)):
                upcoming.append(reminder)

        return upcoming

    async def get_reminder_statistics(self, user_id: str = None) -> Dict[str, int]:
        """
        Get statistics about reminders.
        """
        all_reminders = list(self.reminders.values())
        if user_id:
            all_reminders = [r for r in all_reminders if r["user_id"] == user_id]

        stats = {
            "total": len(all_reminders),
            "active": 0,
            "inactive": 0,
            "by_frequency": {}
        }

        for reminder in all_reminders:
            if reminder["is_active"]:
                stats["active"] += 1
            else:
                stats["inactive"] += 1

            freq = reminder["frequency"]
            if freq not in stats["by_frequency"]:
                stats["by_frequency"][freq] = 0
            stats["by_frequency"][freq] += 1

        return stats

    async def validate_reminder_data(self, reminder_data: Dict[str, Any]) -> List[str]:
        """
        Validate reminder data and return a list of validation errors.
        """
        errors = []

        required_fields = ["task_id", "user_id", "notification_type", "reminder_time", "message"]
        for field in required_fields:
            if not reminder_data.get(field):
                errors.append(f"{field} is required")

        notification_type = reminder_data.get("notification_type")
        if notification_type and notification_type not in [nt.value for nt in NotificationType]:
            errors.append(f"Invalid notification_type. Must be one of: {', '.join([nt.value for nt in NotificationType])}")

        frequency = reminder_data.get("frequency")
        if frequency and frequency not in [rf.value for rf in ReminderFrequency]:
            errors.append(f"Invalid frequency. Must be one of: {', '.join([rf.value for rf in ReminderFrequency])}")

        reminder_time_str = reminder_data.get("reminder_time")
        if reminder_time_str:
            try:
                datetime.fromisoformat(reminder_time_str.replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid reminder time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        return errors

    async def bulk_create_reminders(self, reminders_data: List[Dict[str, Any]], validate: bool = True) -> Dict[str, Any]:
        """
        Create multiple reminders with validation and return results.
        """
        results = {
            "created": [],
            "failed": [],
            "errors": []
        }

        for i, reminder_data in enumerate(reminders_data):
            if validate:
                errors = await self.validate_reminder_data(reminder_data)
                if errors:
                    results["failed"].append(i)
                    results["errors"].extend([f"Reminder {i}: {error}" for error in errors])
                    continue

            try:
                # Convert string values back to enums for creation
                notification_type = NotificationType(reminder_data.get("notification_type", "in_app"))
                frequency = ReminderFrequency(reminder_data.get("frequency", "once"))
                reminder_time = datetime.fromisoformat(reminder_data["reminder_time"])

                reminder = await self.create_reminder(
                    task_id=reminder_data["task_id"],
                    user_id=reminder_data["user_id"],
                    notification_type=notification_type,
                    reminder_time=reminder_time,
                    message=reminder_data["message"],
                    frequency=frequency,
                    title=reminder_data.get("title", "")
                )
                results["created"].append(reminder)
            except Exception as e:
                results["failed"].append(i)
                results["errors"].append(f"Reminder {i}: {str(e)}")

        return results

    async def cleanup(self):
        """
        Clean up any active reminder tasks.
        """
        for task in self.active_reminders.values():
            task.cancel()

        # Wait for tasks to finish cancellation
        if self.active_reminders:
            await asyncio.gather(*self.active_reminders.values(), return_exceptions=True)

        self.active_reminders.clear()

# Example usage
async def main():
    skill = ReminderSchedulingSkill()

    # Create a sample reminder
    reminder = await skill.create_reminder(
        task_id="task123",
        user_id="user123",
        notification_type=NotificationType.IN_APP,
        reminder_time=datetime.now() + timedelta(seconds=10),  # 10 seconds from now
        message="Time to review your task!",
        title="Task Review Reminder"
    )

    print(f"Created reminder: {reminder['title']}")

    # Get the reminder
    retrieved_reminder = await skill.get_reminder(reminder['id'])
    print(f"Retrieved reminder: {retrieved_reminder['title']}")

    # Get reminders for user
    user_reminders = await skill.get_reminders_for_user("user123")
    print(f"User has {len(user_reminders)} reminders")

    # Get upcoming reminders (within 60 minutes)
    upcoming = await skill.get_upcoming_reminders(user_id="user123", within_minutes=60)
    print(f"User has {len(upcoming)} upcoming reminders")

    # Get statistics
    stats = await skill.get_reminder_statistics("user123")
    print(f"Reminder statistics: {stats}")

    print("Reminder Scheduling Skill initialized and tested")

    # Clean up
    await skill.cleanup()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())