"""
User Interface Agent for Todo Chatbot

This agent handles all user interface operations including:
- Processing user commands and queries
- Generating appropriate responses
- Managing conversation state
- Handling different input/output channels (CLI, web, mobile)
"""

import asyncio
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import re

class InputChannel(Enum):
    CLI = "cli"
    WEB = "web"
    MOBILE = "mobile"
    CHAT = "chat"
    VOICE = "voice"

class OutputFormat(Enum):
    TEXT = "text"
    MARKDOWN = "markdown"
    JSON = "json"
    HTML = "html"

@dataclass
class UserInput:
    channel: InputChannel
    user_id: str
    message: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AgentResponse:
    response: str
    output_format: OutputFormat
    metadata: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None

class UserInterfaceAgent:
    """
    Agent responsible for managing user interactions in the Todo Chatbot system.
    """

    def __init__(self):
        self.conversation_state: Dict[str, Any] = {}
        self.command_patterns = {
            "create_task": [
                r"create task (.+)",
                r"add task (.+)",
                r"new task (.+)",
                r"create (.+)"
            ],
            "list_tasks": [
                r"list tasks",
                r"show tasks",
                r"what are my tasks",
                r"my tasks"
            ],
            "complete_task": [
                r"complete task (\d+)",
                r"finish task (\d+)",
                r"done task (\d+)",
                r"mark task (\d+) as complete"
            ],
            "delete_task": [
                r"delete task (\d+)",
                r"remove task (\d+)",
                r"cancel task (\d+)"
            ],
            "help": [
                r"help",
                r"what can you do",
                r"commands",
                r"options"
            ],
            "search_tasks": [
                r"search (.+)",
                r"find (.+)",
                r"look for (.+)"
            ]
        }
        self.task_management_agent = None
        self.notification_agent = None

    def set_task_management_agent(self, agent):
        """
        Set the task management agent for this UI agent.
        """
        self.task_management_agent = agent

    def set_notification_agent(self, agent):
        """
        Set the notification agent for this UI agent.
        """
        self.notification_agent = agent

    async def process_input(self, user_input: UserInput) -> AgentResponse:
        """
        Process user input and generate an appropriate response.
        """
        # Update conversation state
        await self._update_conversation_state(user_input)

        # Parse the command
        command = await self._parse_command(user_input.message)

        # Execute the command
        response = await self._execute_command(command, user_input)

        # Generate response
        return response

    async def _update_conversation_state(self, user_input: UserInput):
        """
        Update the conversation state with the user's input.
        """
        if user_input.user_id not in self.conversation_state:
            self.conversation_state[user_input.user_id] = {
                "last_input": user_input.message,
                "last_timestamp": user_input.timestamp,
                "context": {}
            }

        self.conversation_state[user_input.user_id].update({
            "last_input": user_input.message,
            "last_timestamp": user_input.timestamp
        })

    async def _parse_command(self, message: str) -> Dict[str, Any]:
        """
        Parse the user's message to determine the command and parameters.
        """
        message_lower = message.lower().strip()

        for command_type, patterns in self.command_patterns.items():
            for pattern in patterns:
                match = re.search(pattern, message_lower)
                if match:
                    return {
                        "type": command_type,
                        "params": match.groups() if match.groups() else [],
                        "original_message": message
                    }

        # If no specific command matched, treat as a general query
        return {
            "type": "general_query",
            "params": [message],
            "original_message": message
        }

    async def _execute_command(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Execute the parsed command and return a response.
        """
        command_type = command["type"]

        if command_type == "create_task":
            return await self._handle_create_task(command, user_input)
        elif command_type == "list_tasks":
            return await self._handle_list_tasks(command, user_input)
        elif command_type == "complete_task":
            return await self._handle_complete_task(command, user_input)
        elif command_type == "delete_task":
            return await self._handle_delete_task(command, user_input)
        elif command_type == "help":
            return await self._handle_help(command, user_input)
        elif command_type == "search_tasks":
            return await self._handle_search_tasks(command, user_input)
        elif command_type == "general_query":
            return await self._handle_general_query(command, user_input)
        else:
            return AgentResponse(
                response=f"Sorry, I don't understand the command: {command_type}",
                output_format=OutputFormat.TEXT,
                suggestions=["Try 'help' to see available commands"]
            )

    async def _handle_create_task(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the create task command.
        """
        if not self.task_management_agent:
            return AgentResponse(
                response="Task management agent not available",
                output_format=OutputFormat.TEXT
            )

        task_title = command["params"][0] if command["params"] else "Untitled Task"

        # For now, create a simple task without additional details
        task = await self.task_management_agent.create_task(
            title=task_title,
            user_id=user_input.user_id
        )

        response_text = f"Task '{task.title}' created successfully with ID: {task.id}"
        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["list tasks", "create another task", "help"]
        )

    async def _handle_list_tasks(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the list tasks command.
        """
        if not self.task_management_agent:
            return AgentResponse(
                response="Task management agent not available",
                output_format=OutputFormat.TEXT
            )

        tasks = await self.task_management_agent.get_tasks_by_user(user_input.user_id)

        if not tasks:
            response_text = "You have no tasks. Create a task to get started!"
        else:
            response_text = f"You have {len(tasks)} task(s):\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = "✅" if task.status.value == "completed" else "📝"
                response_text += f"{i}. {status_emoji} {task.title} - {task.status.value}\n"

        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["create task <title>", "complete task <number>", "help"]
        )

    async def _handle_complete_task(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the complete task command.
        """
        if not self.task_management_agent:
            return AgentResponse(
                response="Task management agent not available",
                output_format=OutputFormat.TEXT
            )

        try:
            task_number = int(command["params"][0]) if command["params"] else 0
            tasks = await self.task_management_agent.get_tasks_by_user(user_input.user_id)

            if 1 <= task_number <= len(tasks):
                task = tasks[task_number - 1]
                await self.task_management_agent.complete_task(task.id)
                response_text = f"Task '{task.title}' marked as completed!"
            else:
                response_text = f"Invalid task number. Please specify a number between 1 and {len(tasks)}."
        except ValueError:
            response_text = "Please specify a valid task number."
        except Exception as e:
            response_text = f"Error completing task: {str(e)}"

        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["list tasks", "create task", "help"]
        )

    async def _handle_delete_task(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the delete task command.
        """
        if not self.task_management_agent:
            return AgentResponse(
                response="Task management agent not available",
                output_format=OutputFormat.TEXT
            )

        try:
            task_number = int(command["params"][0]) if command["params"] else 0
            tasks = await self.task_management_agent.get_tasks_by_user(user_input.user_id)

            if 1 <= task_number <= len(tasks):
                task = tasks[task_number - 1]
                success = await self.task_management_agent.delete_task(task.id)
                if success:
                    response_text = f"Task '{task.title}' deleted successfully!"
                else:
                    response_text = f"Failed to delete task '{task.title}'."
            else:
                response_text = f"Invalid task number. Please specify a number between 1 and {len(tasks)}."
        except ValueError:
            response_text = "Please specify a valid task number."
        except Exception as e:
            response_text = f"Error deleting task: {str(e)}"

        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["list tasks", "create task", "help"]
        )

    async def _handle_help(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the help command.
        """
        help_text = """
Available commands:
• create task <title> - Create a new task
• list tasks - Show all your tasks
• complete task <number> - Mark a task as completed
• delete task <number> - Delete a task
• search <query> - Search for tasks
• help - Show this help message

Examples:
• "create task Buy groceries"
• "list tasks"
• "complete task 1"
        """

        return AgentResponse(
            response=help_text.strip(),
            output_format=OutputFormat.TEXT,
            suggestions=["create task <title>", "list tasks", "help"]
        )

    async def _handle_search_tasks(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle the search tasks command.
        """
        if not self.task_management_agent:
            return AgentResponse(
                response="Task management agent not available",
                output_format=OutputFormat.TEXT
            )

        query = command["params"][0] if command["params"] else ""

        tasks = await self.task_management_agent.search_tasks(query)

        if not tasks:
            response_text = f"No tasks found matching '{query}'."
        else:
            response_text = f"Found {len(tasks)} task(s) matching '{query}':\n"
            for i, task in enumerate(tasks, 1):
                status_emoji = "✅" if task.status.value == "completed" else "📝"
                response_text += f"{i}. {status_emoji} {task.title} - {task.status.value}\n"

        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["list tasks", "create task", "help"]
        )

    async def _handle_general_query(self, command: Dict[str, Any], user_input: UserInput) -> AgentResponse:
        """
        Handle general queries that don't match specific commands.
        """
        message = command["params"][0] if command["params"] else ""

        # Simple NLP-like responses for common queries
        if any(word in message.lower() for word in ["hello", "hi", "hey", "greetings"]):
            response_text = "Hello! I'm your Todo Chatbot assistant. How can I help you today?"
        elif any(word in message.lower() for word in ["thank", "thanks", "thank you"]):
            response_text = "You're welcome! Is there anything else I can help you with?"
        elif any(word in message.lower() for word in ["bye", "goodbye", "see you"]):
            response_text = "Goodbye! Feel free to come back when you need to manage your tasks."
        else:
            response_text = f"I'm not sure how to handle '{message}'. Try asking for 'help' to see available commands."

        return AgentResponse(
            response=response_text,
            output_format=OutputFormat.TEXT,
            suggestions=["help", "create task <title>", "list tasks"]
        )

    async def format_response(self, response: AgentResponse, channel: InputChannel) -> str:
        """
        Format the response based on the output format and channel.
        """
        if response.output_format == OutputFormat.JSON:
            import json
            return json.dumps({
                "response": response.response,
                "metadata": response.metadata,
                "suggestions": response.suggestions
            })
        elif response.output_format == OutputFormat.MARKDOWN:
            formatted = f"## {response.response}\n\n"
            if response.suggestions:
                formatted += "**Suggestions:**\n"
                for suggestion in response.suggestions:
                    formatted += f"- {suggestion}\n"
            return formatted
        else:  # Default to text
            result = response.response
            if response.suggestions:
                result += f"\n\nSuggestions: {', '.join(response.suggestions)}"
            return result

    async def process_cli_input(self, user_id: str, message: str) -> str:
        """
        Process input specifically from CLI channel.
        """
        user_input = UserInput(
            channel=InputChannel.CLI,
            user_id=user_id,
            message=message,
            timestamp=datetime.now()
        )

        agent_response = await self.process_input(user_input)
        return await self.format_response(agent_response, InputChannel.CLI)

    async def process_web_input(self, user_id: str, message: str) -> Dict[str, Any]:
        """
        Process input specifically from web channel and return structured response.
        """
        user_input = UserInput(
            channel=InputChannel.WEB,
            user_id=user_id,
            message=message,
            timestamp=datetime.now()
        )

        agent_response = await self.process_input(user_input)

        return {
            "response": agent_response.response,
            "format": agent_response.output_format.value,
            "suggestions": agent_response.suggestions or [],
            "timestamp": datetime.now().isoformat()
        }

    async def get_conversation_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get the current conversation context for a user.
        """
        return self.conversation_state.get(user_id, {})

    async def clear_conversation_context(self, user_id: str):
        """
        Clear the conversation context for a user.
        """
        if user_id in self.conversation_state:
            del self.conversation_state[user_id]

# Example usage
async def main():
    agent = UserInterfaceAgent()

    # Simulate some user interactions
    print("User Interface Agent initialized")

    # Example CLI interaction
    response = await agent.process_cli_input("user123", "create task Buy groceries")
    print(f"Response: {response}")

    response = await agent.process_cli_input("user123", "list tasks")
    print(f"Response: {response}")

    response = await agent.process_cli_input("user123", "help")
    print(f"Response: {response}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())