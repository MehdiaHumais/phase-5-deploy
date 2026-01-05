"""
Task Management Agent for Todo Chatbot

This agent handles all task-related operations including:
- Creating, updating, deleting tasks
- Managing task states (pending, completed, etc.)
- Handling task priorities, due dates, and recurring tasks
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum

class TaskStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

@dataclass
class Task:
    id: str
    title: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    priority: TaskPriority = TaskPriority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = None
    completed_at: Optional[datetime] = None
    tags: List[str] = None
    user_id: str = ""
    recurrence_pattern: Optional[str] = None  # e.g., "daily", "weekly", "monthly"

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.tags is None:
            self.tags = []

class TaskManagementAgent:
    """
    Agent responsible for managing tasks in the Todo Chatbot system.
    """

    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.event_queue = asyncio.Queue()

    async def create_task(self, title: str, description: str = "",
                         priority: TaskPriority = TaskPriority.MEDIUM,
                         due_date: Optional[datetime] = None,
                         tags: List[str] = None,
                         user_id: str = "",
                         recurrence_pattern: Optional[str] = None) -> Task:
        """
        Create a new task with the given parameters.
        """
        import uuid
        task_id = str(uuid.uuid4())

        task = Task(
            id=task_id,
            title=title,
            description=description,
            priority=priority,
            due_date=due_date,
            tags=tags or [],
            user_id=user_id,
            recurrence_pattern=recurrence_pattern
        )

        self.tasks[task_id] = task

        # Publish task created event
        await self._publish_event("task_created", {
            "task_id": task_id,
            "user_id": user_id,
            "task_data": asdict(task)
        })

        return task

    async def get_task(self, task_id: str) -> Optional[Task]:
        """
        Retrieve a task by its ID.
        """
        return self.tasks.get(task_id)

    async def update_task(self, task_id: str, **updates) -> Optional[Task]:
        """
        Update a task with the provided fields.
        """
        task = self.tasks.get(task_id)
        if not task:
            return None

        # Update task fields
        for field, value in updates.items():
            if hasattr(task, field):
                if field == 'status' and value == 'completed':
                    task.completed_at = datetime.now()
                setattr(task, field, value)

        # Publish task updated event
        await self._publish_event("task_updated", {
            "task_id": task_id,
            "task_data": asdict(task)
        })

        return task

    async def delete_task(self, task_id: str) -> bool:
        """
        Delete a task by its ID.
        """
        if task_id in self.tasks:
            task = self.tasks[task_id]
            del self.tasks[task_id]

            # Publish task deleted event
            await self._publish_event("task_deleted", {
                "task_id": task_id,
                "user_id": task.user_id
            })

            return True
        return False

    async def complete_task(self, task_id: str) -> Optional[Task]:
        """
        Mark a task as completed.
        """
        return await self.update_task(task_id, status=TaskStatus.COMPLETED)

    async def get_tasks_by_user(self, user_id: str) -> List[Task]:
        """
        Get all tasks for a specific user.
        """
        return [task for task in self.tasks.values() if task.user_id == user_id]

    async def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """
        Get all tasks with a specific status.
        """
        return [task for task in self.tasks.values() if task.status == status]

    async def get_overdue_tasks(self) -> List[Task]:
        """
        Get all tasks that are overdue.
        """
        now = datetime.now()
        return [
            task for task in self.tasks.values()
            if task.due_date and task.due_date < now and task.status != TaskStatus.COMPLETED
        ]

    async def search_tasks(self, query: str) -> List[Task]:
        """
        Search tasks by title or description.
        """
        query_lower = query.lower()
        return [
            task for task in self.tasks.values()
            if query_lower in task.title.lower() or query_lower in task.description.lower()
        ]

    async def filter_tasks(self,
                          status: Optional[TaskStatus] = None,
                          priority: Optional[TaskPriority] = None,
                          tag: Optional[str] = None) -> List[Task]:
        """
        Filter tasks by various criteria.
        """
        filtered_tasks = list(self.tasks.values())

        if status:
            filtered_tasks = [task for task in filtered_tasks if task.status == status]

        if priority:
            filtered_tasks = [task for task in filtered_tasks if task.priority == priority]

        if tag:
            filtered_tasks = [task for task in filtered_tasks if tag in task.tags]

        return filtered_tasks

    async def sort_tasks(self,
                        tasks: List[Task],
                        sort_by: str = "due_date",
                        ascending: bool = True) -> List[Task]:
        """
        Sort tasks by a specified field.
        """
        if sort_by == "due_date":
            key_func = lambda task: task.due_date or datetime.max
        elif sort_by == "priority":
            key_func = lambda task: task.priority.value
        elif sort_by == "created_at":
            key_func = lambda task: task.created_at
        else:
            key_func = lambda task: getattr(task, sort_by, "")

        return sorted(tasks, key=key_func, reverse=not ascending)

    async def _publish_event(self, event_type: str, data: Dict[str, Any]):
        """
        Publish an event to the event queue (to be consumed by other agents).
        """
        event = {
            "event_type": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }
        await self.event_queue.put(event)
        print(f"Event published: {event_type} - {data}")

    async def get_next_event(self) -> Optional[Dict[str, Any]]:
        """
        Get the next event from the queue.
        """
        try:
            return self.event_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

# Example usage
async def main():
    agent = TaskManagementAgent()

    # Create a sample task
    task = await agent.create_task(
        title="Complete project documentation",
        description="Write comprehensive documentation for the Todo Chatbot project",
        priority=TaskPriority.HIGH,
        due_date=datetime.now() + timedelta(days=3),
        tags=["documentation", "urgent"],
        user_id="user123"
    )

    print(f"Created task: {task.title}")

    # Get the task
    retrieved_task = await agent.get_task(task.id)
    print(f"Retrieved task: {retrieved_task.title}")

    # Update the task
    await agent.update_task(task.id, status=TaskStatus.IN_PROGRESS)
    print(f"Updated task status to: {retrieved_task.status}")

    # Get tasks by user
    user_tasks = await agent.get_tasks_by_user("user123")
    print(f"User has {len(user_tasks)} tasks")

    # Search tasks
    search_results = await agent.search_tasks("documentation")
    print(f"Found {len(search_results)} tasks matching 'documentation'")

if __name__ == "__main__":
    asyncio.run(main())