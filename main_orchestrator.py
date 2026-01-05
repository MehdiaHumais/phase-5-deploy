"""
Main Orchestrator for Todo Chatbot System

This orchestrator connects all agents and skills together to form a cohesive system.
"""

import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

# Import all agents and skills
from agents.task_management.agent import TaskManagementAgent
from agents.notification_reminder.agent import NotificationReminderAgent
from agents.kafka_event_processing.agent import KafkaEventProcessingAgent
from agents.dapr_service_invocation.agent import DaprServiceInvocationAgent
from agents.user_interface.agent import UserInterfaceAgent
from agents.natural_language_agent.agent import NaturalLanguageAgent

from skills.task_creation_deletion.skill import TaskCreationDeletionSkill
from skills.reminder_scheduling.skill import ReminderSchedulingSkill
from skills.kafka_messaging.skill import KafkaMessagingSkill
from skills.dapr_integration.skill import DaprIntegrationSkill
from skills.user_authentication.skill import UserAuthenticationSkill

from event_publisher import EventPublisher, EventType

class TodoChatbotOrchestrator:
    """
    Main orchestrator that connects all agents and skills in the Todo Chatbot system.
    """

    def __init__(self):
        # Initialize the event publisher
        self.event_publisher = EventPublisher()

        # Initialize agents
        self.task_management_agent = TaskManagementAgent()
        self.notification_agent = NotificationReminderAgent(event_queue=self.task_management_agent.event_queue)
        self.kafka_agent = KafkaEventProcessingAgent()
        self.dapr_agent = DaprServiceInvocationAgent()
        self.ui_agent = UserInterfaceAgent()
        self.natural_language_agent = NaturalLanguageAgent()

        # Initialize skills
        self.task_skill = TaskCreationDeletionSkill()
        self.reminder_skill = ReminderSchedulingSkill()
        self.kafka_skill = KafkaMessagingSkill()
        self.dapr_skill = DaprIntegrationSkill()
        self.auth_skill = UserAuthenticationSkill()

        # Connect components
        self._connect_components()

    def _connect_components(self):
        """
        Connect agents and skills together.
        """
        # Connect event publisher to skills that need it
        self.task_skill.set_event_publisher(self.event_publisher)
        self.reminder_skill.set_event_publisher(self.event_publisher)

        # Connect UI agent to other agents
        self.ui_agent.set_task_management_agent(self.task_management_agent)
        self.ui_agent.set_notification_agent(self.notification_agent)

        # Connect Natural Language Agent to other components
        self.natural_language_agent.set_task_management_agent(self.task_management_agent)
        self.natural_language_agent.set_user_interface_agent(self.ui_agent)
        self.natural_language_agent.set_kafka_agent(self.kafka_agent)

        # Connect Dapr integration to authentication skill
        self.auth_skill.set_dapr_integration(self.dapr_skill)

        # Subscribe event handlers
        self.event_publisher.subscribe(EventType.TASK_CREATED, self._on_task_created)
        self.event_publisher.subscribe(EventType.TASK_COMPLETED, self._on_task_completed)
        self.event_publisher.subscribe(EventType.REMINDER_SCHEDULED, self._on_reminder_scheduled)

    async def _on_task_created(self, event: Dict[str, Any]):
        """
        Handle task created event.
        """
        print(f"Task created event received: {event['task_id']}")
        # Could trigger additional actions when a task is created
        task_data = event.get('data', {})
        if 'due_date' in task_data:
            # Create a reminder for tasks with due dates
            await self.reminder_skill.create_due_date_reminder(
                task_id=event['task_id'],
                user_id=event['user_id'],
                due_date=datetime.fromisoformat(task_data['due_date'].replace('Z', '+00:00'))
            )

    async def _on_task_completed(self, event: Dict[str, Any]):
        """
        Handle task completed event.
        """
        print(f"Task completed event received: {event['task_id']}")
        # Could trigger additional actions when a task is completed

    async def _on_reminder_scheduled(self, event: Dict[str, Any]):
        """
        Handle reminder scheduled event.
        """
        print(f"Reminder scheduled event received: {event['data']['id']}")
        # Could trigger additional actions when a reminder is scheduled

    async def initialize(self):
        """
        Initialize all components.
        """
        print("Initializing Todo Chatbot System...")

        # Initialize Kafka components
        await self.kafka_agent.start()
        await self.kafka_skill.initialize()

        # Start event processing
        self.event_processing_task = asyncio.create_task(self.event_publisher.start_processing())

        print("Todo Chatbot System initialized successfully")

    async def shutdown(self):
        """
        Shutdown all components.
        """
        print("Shutting down Todo Chatbot System...")

        # Stop event processing
        await self.event_publisher.stop_processing()

        # Shutdown Kafka components
        await self.kafka_agent.stop()
        await self.kafka_skill.shutdown()

        # Close Dapr clients
        await self.dapr_agent.close()
        await self.dapr_skill.close()

        print("Todo Chatbot System shutdown complete")

    # High-level methods that coordinate multiple components
    async def create_task_with_reminder(self,
                                       user_id: str,
                                       title: str,
                                       description: str = "",
                                       due_date: Optional[datetime] = None,
                                       priority: str = "medium",
                                       notification_type: str = "in_app") -> Optional[Dict[str, Any]]:
        """
        Create a task and optionally schedule a reminder for it.
        """
        # Use the task creation skill
        task = await self.task_skill.create_task(
            title=title,
            description=description,
            user_id=user_id
        )

        if not task:
            return None

        # If there's a due date, create a reminder
        if due_date:
            reminder = await self.reminder_skill.create_due_date_reminder(
                task_id=task['id'],
                user_id=user_id,
                due_date=due_date
            )

        return task

    async def get_user_tasks_with_reminders(self, user_id: str) -> Dict[str, Any]:
        """
        Get all tasks for a user along with their associated reminders.
        """
        # Get tasks using the task management agent
        agent_tasks = await self.task_management_agent.get_tasks_by_user(user_id)

        # Get tasks using the skill
        skill_tasks = await self.task_skill.get_tasks_by_user(user_id)

        # Get reminders for the user
        reminders = await self.reminder_skill.get_reminders_for_user(user_id)

        return {
            "tasks": skill_tasks,
            "reminders": reminders,
            "user_id": user_id
        }

    async def process_user_command(self, user_id: str, command: str) -> str:
        """
        Process a user command through the UI agent.
        """
        from agents.user_interface.agent import UserInput, InputChannel
        user_input = UserInput(
            channel=InputChannel.CLI,
            user_id=user_id,
            message=command,
            timestamp=datetime.now()
        )

        response = await self.ui_agent.process_input(user_input)
        return await self.ui_agent.format_response(response, InputChannel.CLI)

    async def process_natural_language_command(self, user_id: str, command: str) -> Dict[str, Any]:
        """
        Process a natural language command using the Natural Language Agent.
        """
        message = {
            "content": command,
            "user_id": user_id,
            "timestamp": datetime.now()
        }

        result = await self.natural_language_agent.process_message(message)
        return result

    async def authenticate_and_perform_action(self, username: str, password: str, action: str) -> Dict[str, Any]:
        """
        Authenticate a user and perform an action.
        """
        # Authenticate user
        tokens = await self.auth_skill.login_user(username, password)
        if not tokens:
            return {"success": False, "message": "Authentication failed"}

        # Perform the requested action
        if action == "get_profile":
            user = await self.auth_skill.get_user_by_token(tokens['access_token'])
            return {"success": True, "user": user}
        elif action.startswith("create_task:"):
            task_title = action.split(":", 1)[1]
            task = await self.create_task_with_reminder(
                user_id=tokens['sub'] if hasattr(tokens, 'sub') else user['id'],
                title=task_title
            )
            return {"success": True, "task": task}
        else:
            return {"success": False, "message": "Unknown action"}

    async def run_demo(self):
        """
        Run a demonstration of the integrated system.
        """
        print("\n" + "="*50)
        print("TODO CHATBOT SYSTEM DEMO")
        print("="*50)

        # Register a user
        user = await self.auth_skill.register_user(
            username="demo_user",
            email="demo@example.com",
            password="Demo123!"
        )
        print(f"Registered user: {user['username'] if user else 'Failed'}")

        # Login the user
        tokens = await self.auth_skill.login_user("demo_user", "Demo123!")
        print(f"Login successful: {'Yes' if tokens else 'No'}")

        if tokens:
            user_id = user['id']

            # Create a task with a reminder
            from datetime import timedelta
            task = await self.create_task_with_reminder(
                user_id=user_id,
                title="Complete project documentation",
                description="Write comprehensive documentation for the Todo Chatbot project",
                due_date=datetime.now().replace(hour=10, minute=0, second=0) + timedelta(days=1)  # Tomorrow at 10 AM
            )
            print(f"Created task: {task['title'] if task else 'Failed'}")

            # Process a user command
            command_response = await self.process_user_command(user_id, "list tasks")
            print(f"Command response: {command_response}")

            # Get user tasks with reminders
            user_data = await self.get_user_tasks_with_reminders(user_id)
            print(f"User has {len(user_data['tasks'])} tasks and {len(user_data['reminders'])} reminders")

        print("="*50)
        print("DEMO COMPLETE")
        print("="*50)

# Example usage
async def main():
    orchestrator = TodoChatbotOrchestrator()

    try:
        # Initialize the system
        await orchestrator.initialize()

        # Run a demonstration
        await orchestrator.run_demo()

    except Exception as e:
        print(f"Error in orchestrator: {e}")
    finally:
        # Shutdown the system
        await orchestrator.shutdown()

if __name__ == "__main__":
    asyncio.run(main())