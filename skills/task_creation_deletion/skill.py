"""
Task Creation/Deletion Skill for Todo Chatbot

This skill provides capabilities for creating and deleting tasks in the Todo Chatbot system.
"""

import asyncio
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import uuid
from enum import Enum

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskCreationDeletionSkill:
    """
    Skill that provides capabilities for creating and deleting tasks in the Todo Chatbot system.
    """

    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}
        self.event_publisher = None

    def set_event_publisher(self, event_publisher):
        """
        Set the event publisher for this skill.
        """
        self.event_publisher = event_publisher

    async def create_task(self,
                         title: str,
                         description: str = "",
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         due_date: Optional[datetime] = None,
                         tags: List[str] = None,
                         user_id: str = "",
                         recurrence_pattern: Optional[str] = None) -> Dict[str, Any]:
        """
        Create a new task with the given parameters.
        """
        task_id = str(uuid.uuid4())

        task = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": TaskStatus.PENDING.value,
            "priority": priority.value,
            "due_date": due_date.isoformat() if due_date else None,
            "created_at": datetime.now().isoformat(),
            "completed_at": None,
            "tags": tags or [],
            "user_id": user_id,
            "recurrence_pattern": recurrence_pattern
        }

        self.tasks[task_id] = task

        # Publish task created event if event publisher is available
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="task_created",
                task_id=task_id,
                user_id=user_id,
                data=task
            )

        return task

    async def create_tasks_batch(self, tasks_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Create multiple tasks in a batch operation.
        """
        created_tasks = []
        for task_data in tasks_data:
            task = await self.create_task(**task_data)
            created_tasks.append(task)
        return created_tasks

    async def delete_task(self, task_id: str, user_id: str = None) -> bool:
        """
        Delete a task by its ID.
        """
        if task_id not in self.tasks:
            return False

        task = self.tasks[task_id]

        # Check if user has permission to delete this task
        if user_id and task["user_id"] != user_id:
            return False

        # Remove the task
        del self.tasks[task_id]

        # Publish task deleted event if event publisher is available
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="task_deleted",
                task_id=task_id,
                user_id=task["user_id"],
                data={"id": task_id}
            )

        return True

    async def delete_tasks_by_user(self, user_id: str) -> int:
        """
        Delete all tasks for a specific user.
        """
        user_task_ids = [
            task_id for task_id, task in self.tasks.items()
            if task["user_id"] == user_id
        ]

        deleted_count = 0
        for task_id in user_task_ids:
            if await self.delete_task(task_id, user_id):
                deleted_count += 1

        return deleted_count

    async def delete_tasks_by_status(self, status: TaskStatus, user_id: str = None) -> int:
        """
        Delete tasks with a specific status.
        """
        task_ids_to_delete = [
            task_id for task_id, task in self.tasks.items()
            if task["status"] == status.value and (not user_id or task["user_id"] == user_id)
        ]

        deleted_count = 0
        for task_id in task_ids_to_delete:
            if await self.delete_task(task_id, user_id):
                deleted_count += 1

        return deleted_count

    async def delete_tasks_by_tag(self, tag: str, user_id: str = None) -> int:
        """
        Delete tasks that have a specific tag.
        """
        task_ids_to_delete = [
            task_id for task_id, task in self.tasks.items()
            if tag in task["tags"] and (not user_id or task["user_id"] == user_id)
        ]

        deleted_count = 0
        for task_id in task_ids_to_delete:
            if await self.delete_task(task_id, user_id):
                deleted_count += 1

        return deleted_count

    async def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a task by its ID.
        """
        return self.tasks.get(task_id)

    async def get_tasks_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all tasks for a specific user.
        """
        return [
            task for task in self.tasks.values()
            if task["user_id"] == user_id
        ]

    async def get_tasks_by_status(self, status: TaskStatus, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Get all tasks with a specific status.
        """
        return [
            task for task in self.tasks.values()
            if task["status"] == status.value and (not user_id or task["user_id"] == user_id)
        ]

    async def update_task(self, task_id: str, **updates) -> Optional[Dict[str, Any]]:
        """
        Update a task with the provided fields.
        """
        if task_id not in self.tasks:
            return None

        task = self.tasks[task_id]

        # Update task fields
        for field, value in updates.items():
            if field in task:
                if field == 'status' and value == TaskStatus.COMPLETED.value:
                    task['completed_at'] = datetime.now().isoformat()
                task[field] = value

        # Publish task updated event if event publisher is available
        if self.event_publisher:
            await self.event_publisher.publish_event(
                event_type="task_updated",
                task_id=task_id,
                user_id=task["user_id"],
                data=task
            )

        return task

    async def search_tasks(self, query: str, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Search tasks by title or description.
        """
        query_lower = query.lower()
        results = []

        for task in self.tasks.values():
            matches_query = (
                query_lower in task["title"].lower() or
                query_lower in task["description"].lower()
            )

            if matches_query and (not user_id or task["user_id"] == user_id):
                results.append(task)

        return results

    async def validate_task_data(self, task_data: Dict[str, Any]) -> List[str]:
        """
        Validate task data and return a list of validation errors.
        """
        errors = []

        if not task_data.get("title"):
            errors.append("Title is required")

        priority = task_data.get("priority")
        if priority and priority not in [p.value for p in TaskPriority]:
            errors.append(f"Invalid priority. Must be one of: {', '.join([p.value for p in TaskPriority])}")

        status = task_data.get("status")
        if status and status not in [s.value for s in TaskStatus]:
            errors.append(f"Invalid status. Must be one of: {', '.join([s.value for s in TaskStatus])}")

        due_date_str = task_data.get("due_date")
        if due_date_str:
            try:
                datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except ValueError:
                errors.append("Invalid due date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)")

        return errors

    async def get_task_statistics(self, user_id: str = None) -> Dict[str, int]:
        """
        Get statistics about tasks.
        """
        all_tasks = list(self.tasks.values())
        if user_id:
            all_tasks = [task for task in all_tasks if task["user_id"] == user_id]

        stats = {
            "total": len(all_tasks),
            "pending": 0,
            "in_progress": 0,
            "completed": 0,
            "cancelled": 0
        }

        for task in all_tasks:
            status = task["status"]
            if status in stats:
                stats[status] += 1

        return stats

    async def create_recurring_task(self,
                                   title: str,
                                   description: str = "",
                                   priority: TaskPriority = TaskPriority.MEDIUM,
                                   due_date: Optional[datetime] = None,
                                   tags: List[str] = None,
                                   user_id: str = "",
                                   recurrence_pattern: str = "daily") -> Dict[str, Any]:
        """
        Create a recurring task that generates new tasks based on a pattern.
        """
        # Create the initial task
        task = await self.create_task(
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags,
            user_id=user_id,
            recurrence_pattern=recurrence_pattern
        )

        # For now, we'll just mark it as recurring - the actual recurrence logic
        # would be handled by a separate service
        task["is_recurring"] = True

        return task

    async def bulk_create_tasks(self, tasks_data: List[Dict[str, Any]], validate: bool = True) -> Dict[str, Any]:
        """
        Create multiple tasks with validation and return results.
        """
        results = {
            "created": [],
            "failed": [],
            "errors": []
        }

        for i, task_data in enumerate(tasks_data):
            if validate:
                errors = await self.validate_task_data(task_data)
                if errors:
                    results["failed"].append(i)
                    results["errors"].extend([f"Task {i}: {error}" for error in errors])
                    continue

            try:
                task = await self.create_task(**task_data)
                results["created"].append(task)
            except Exception as e:
                results["failed"].append(i)
                results["errors"].append(f"Task {i}: {str(e)}")

        return results

# Example usage
async def main():
    skill = TaskCreationDeletionSkill()

    # Create a sample task
    task = await skill.create_task(
        title="Complete project documentation",
        description="Write comprehensive documentation for the Todo Chatbot project",
        priority=TaskPriority.HIGH,
        due_date=datetime.now() + timedelta(days=3),
        tags=["documentation", "urgent"],
        user_id="user123"
    )

    print(f"Created task: {task['title']}")

    # Get the task
    retrieved_task = await skill.get_task(task['id'])
    print(f"Retrieved task: {retrieved_task['title']}")

    # Update the task
    await skill.update_task(task['id'], status=TaskStatus.IN_PROGRESS.value)
    updated_task = await skill.get_task(task['id'])
    print(f"Updated task status to: {updated_task['status']}")

    # Get tasks by user
    user_tasks = await skill.get_tasks_by_user("user123")
    print(f"User has {len(user_tasks)} tasks")

    # Search tasks
    search_results = await skill.search_tasks("documentation")
    print(f"Found {len(search_results)} tasks matching 'documentation'")

    # Get statistics
    stats = await skill.get_task_statistics("user123")
    print(f"Task statistics: {stats}")

    print("Task Creation/Deletion Skill initialized and tested")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())