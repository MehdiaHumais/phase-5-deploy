"""
Natural Language Processing Agent for Todo Chatbot

This agent processes natural language input and automatically creates tasks based on the input.
"""

import re
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import asyncio

from openai import OpenAI

class TaskPriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

class TaskType(Enum):
    MEETING = "meeting"
    APPOINTMENT = "appointment"
    REMINDER = "reminder"
    GENERAL = "general"

class NaturalLanguageAgent:
    """
    Agent that processes natural language input and automatically creates tasks.
    """

    def __init__(self):
        self.task_management_agent = None
        self.user_interface_agent = None
        self.kafka_agent = None

        # Initialize OpenAI client
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
            self.use_openai = True
        else:
            print("Warning: OPENAI_API_KEY not found in environment. Using fallback regex patterns.")
            self.use_openai = False

        # Keywords for different task types
        self.meeting_keywords = [
            "meeting", "meet", "appointment", "call", "conference", "discussion", "talk", "session"
        ]

        self.time_keywords = [
            "today", "tomorrow", "tonight", "now", "morning", "afternoon", "evening",
            "yesterday", "week", "month", "year", "next", "last", "this"
        ]

        # Date patterns
        self.date_patterns = [
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",  # MM/DD/YYYY or MM-DD-YYYY
            r"(\d{4}[/-]\d{1,2}[/-]\d{1,2})",  # YYYY/MM/DD or YYYY-MM-DD
            r"(today|tomorrow|tonight|yesterday)",  # Relative dates
            r"(next\s+(week|month|year))",  # Next week/month/year
        ]

        # Time patterns
        self.time_patterns = [
            r"(\d{1,2}:\d{2}\s*(am|pm)?)",  # HH:MM AM/PM
            r"(\d{1,2}\s*(am|pm))",  # HH AM/PM
        ]

    def set_task_management_agent(self, agent):
        """Set the task management agent for creating tasks."""
        self.task_management_agent = agent

    def set_user_interface_agent(self, agent):
        """Set the user interface agent for responses."""
        self.user_interface_agent = agent

    def set_kafka_agent(self, agent):
        """Set the Kafka agent for event processing."""
        self.kafka_agent = agent

    def extract_date_time(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract date and time information from natural language text.
        """
        text_lower = text.lower()
        result = {}

        # Check for relative dates
        if "tomorrow" in text_lower:
            result["due_date"] = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        elif "today" in text_lower:
            result["due_date"] = datetime.now().strftime("%Y-%m-%d")
        elif "tonight" in text_lower:
            result["due_date"] = datetime.now().strftime("%Y-%m-%d")
            if "time" not in result:
                result["due_time"] = "19:00"  # Default to 7 PM for tonight
        elif "yesterday" in text_lower:
            result["due_date"] = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

        # Check for specific dates using regex
        for pattern in self.date_patterns:
            match = re.search(pattern, text_lower)
            if match:
                date_str = match.group(1)
                if date_str in ["today", "tomorrow", "tonight", "yesterday"]:
                    continue  # Already handled above
                result["due_date"] = self._parse_date(date_str)
                break

        # Check for times
        for pattern in self.time_patterns:
            match = re.search(pattern, text_lower)
            if match:
                time_str = match.group(1)
                result["due_time"] = self._parse_time(time_str)
                break

        return result if result else None

    def _parse_date(self, date_str: str) -> Optional[str]:
        """
        Parse a date string into YYYY-MM-DD format.
        """
        try:
            # Handle MM/DD/YYYY or MM-DD-YYYY
            if "/" in date_str or "-" in date_str:
                parts = re.split(r"[/\-]", date_str)
                if len(parts) == 3:
                    month, day, year = parts
                    # Handle 2-digit years
                    if len(year) == 2:
                        year = "20" + year
                    return f"{year.zfill(4)}-{month.zfill(2)}-{day.zfill(2)}"
            return date_str
        except:
            return None

    def _parse_time(self, time_str: str) -> Optional[str]:
        """
        Parse a time string into HH:MM format.
        """
        try:
            time_str = time_str.strip()
            if "am" in time_str or "pm" in time_str:
                # Handle 12-hour format
                time_part = time_str.replace("am", "").replace("pm", "").strip()
                hour, minute = time_part.split(":") if ":" in time_str else (time_str.replace("am", "").replace("pm", "").strip(), "00")
                hour = int(hour)

                if "pm" in time_str.lower() and hour != 12:
                    hour += 12
                elif "am" in time_str.lower() and hour == 12:
                    hour = 0

                return f"{hour:02d}:{minute.zfill(2)}"
            else:
                # Handle 24-hour format
                if ":" in time_str:
                    hour, minute = time_str.split(":")
                    return f"{hour.zfill(2)}:{minute.zfill(2)}"
                else:
                    return f"{time_str.zfill(2)}:00"
        except:
            return None

    def classify_task_type(self, text: str) -> TaskType:
        """
        Classify the type of task based on keywords in the text.
        """
        text_lower = text.lower()

        for keyword in self.meeting_keywords:
            if keyword in text_lower:
                return TaskType.MEETING

        # Check for appointment-related keywords
        appointment_keywords = ["appointment", "doctor", "dentist", "meeting", "call", "interview"]
        for keyword in appointment_keywords:
            if keyword in text_lower:
                return TaskType.APPOINTMENT

        # Check for reminder-related keywords
        reminder_keywords = ["remind", "remember", "reminder", "don't forget"]
        for keyword in reminder_keywords:
            if keyword in text_lower:
                return TaskType.REMINDER

        return TaskType.GENERAL

    def _extract_title_and_description_with_openai(self, text: str) -> tuple[str, str, str, str]:
        """
        Use OpenAI API to extract task details from natural language text.
        Returns: (title, description, priority, task_type)
        """
        if not self.use_openai:
            # Fallback to regex if OpenAI is not available
            title, description = self._extract_title_and_description_fallback(text)
            return title, description, "medium", "general"

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": """You are a task extraction assistant. Extract the following from the user's input:
                        1. Task title (the main task to be done)
                        2. Task description (additional details about the task)
                        3. Task priority (low, medium, or high)
                        4. Task type (meeting, appointment, reminder, general)

                        Respond in the format: TITLE|DESCRIPTION|PRIORITY|TYPE
                        If you cannot extract certain information, use 'N/A' for title/description or 'medium' for priority or 'general' for type."""
                    },
                    {
                        "role": "user",
                        "content": text
                    }
                ],
                max_tokens=200,
                temperature=0.1
            )

            result = response.choices[0].message.content.strip()

            # Parse the result
            parts = result.split('|')
            if len(parts) >= 4:
                title = parts[0].strip()
                description = parts[1].strip()
                priority = parts[2].strip().lower()
                task_type = parts[3].strip().lower()

                # Validate values
                if priority not in ["low", "medium", "high"]:
                    priority = "medium"
                if task_type not in ["meeting", "appointment", "reminder", "general"]:
                    task_type = "general"

                # If title is N/A, use the original text
                if title == "N/A":
                    title, description = self._extract_title_and_description_fallback(text)
                    return title, description, priority, task_type

                return title, f"Automatically created from: {text}", priority, task_type
            else:
                # If parsing fails, fallback to regex
                title, description = self._extract_title_and_description_fallback(text)
                return title, description, "medium", "general"

        except Exception as e:
            print(f"Error calling OpenAI API: {str(e)}")
            # Fallback to regex if API call fails
            title, description = self._extract_title_and_description_fallback(text)
            return title, description, "medium", "general"

    def _extract_title_and_description_fallback(self, text: str) -> tuple[str, str]:
        """
        Enhanced method to extract title and description from various input formats using regex.
        This is the fallback when OpenAI is not available.
        """
        text = text.strip()

        # Check for structured input like "Title: X Description: Y" or "Title 'X' Description: 'Y'"
        structured_patterns = [
            r"(?:title|task)\s*[:=]?\s*\"([^\"]+)\".*?(?:description|desc)\s*[:=]?\s*\"([^\"]+)\"",
            r"(?:title|task)\s*[:=]?\s*'([^']+)'[^.]*?(?:description|desc)\s*[:=]?\s*'([^']+)'",
            r"(?:title|task)\s*[:=]?\s*([^:.]+)[^.]*?(?:description|desc)\s*[:=]?\s*(.+)",
            r"Title\s*\"([^\"]+)\"\s*description\s*:\s*\"([^\"]+)\"",
        ]

        for pattern in structured_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                title = match.group(1).strip()
                description = match.group(2).strip()
                return title, f"Automatically created from: {text}"

        # Handle "I have X to do" pattern (with optional time reference at the end)
        # Capture the full phrase including articles - also handle common typos like "tommorow"/"tmmorow"
        have_todo_pattern = r"i\s+have\s+(.+?)\s+to\s+do\s+(?:tomorrow|today|tonight|later|now|this\s+\w+|next\s+\w+|yesterday|tommorow|tommorw|tmmorow|tmrw|tonight|in\s+\w+|at\s+\w+|by\s+\w+)"
        match = re.search(have_todo_pattern, text, re.IGNORECASE)
        if match:
            task_detail = match.group(1).strip()
            return task_detail, f"Automatically created from: {text}"

        # Handle "I have X to do named Y" pattern
        have_todo_named_pattern = r"i\s+have\s+(?:a\s+|an\s+|the\s+)?(.+?)\s+to\s+do\s+(?:named|called)\s+(.+)"
        match = re.search(have_todo_named_pattern, text, re.IGNORECASE)
        if match:
            task_detail = match.group(2).strip()
            return task_detail, f"Automatically created from: {text}"

        # Handle "I have X project(s) to do" pattern
        project_pattern = r"i\s+have\s+(\d*)\s*([a-zA-Z\s]+?)\s+project(?:s)?\s+to\s+do.*?(?:named|called)?\s*(.+)?"
        match = re.search(project_pattern, text, re.IGNORECASE)
        if match:
            number = match.group(1).strip() if match.group(1).strip() else "1"
            project_type = match.group(2).strip()
            project_name = match.group(3).strip() if match.group(3) and match.group(3).strip() else f"{project_type} project"
            if project_name and project_name.lower() != project_type.lower():
                return project_name, f"Automatically created from: {text}"
            else:
                task_title = f"{number} {project_type} project(s)" if number != "1" else f"{project_type} project"
                return task_title, f"Automatically created from: {text}"

        # Handle general "I have X" pattern for tasks like "I have a meeting"
        have_pattern = r"i\s+have\s+(.+?)(?:\s+(?:tomorrow|today|tonight|later|now|this\s+\w+|next\s+\w+|yesterday)|\s*$|[.!?])"
        match = re.search(have_pattern, text, re.IGNORECASE)
        if match:
            task_detail = match.group(1).strip()
            return task_detail, f"Automatically created from: {text}"

        # Handle simple "I need to X" or "I have to X" patterns
        need_to_pattern = r"i\s+(?:need|have|want)\s+to\s+(.+?)(?:\s+(?:tomorrow|today|tonight|later|now|this\s+\w+|next\s+\w+|yesterday)|\s*$|[.!?])"
        match = re.search(need_to_pattern, text, re.IGNORECASE)
        if match:
            action = match.group(1).strip()
            return action.capitalize(), f"Automatically created from: {text}"

        # Handle "create a task named X" pattern - fix to capture full name, also handle typos like "taks"
        create_task_pattern = r"(?:create|make|add|new)\s+(?:a\s+)?(?:task|taks)\s+(?:named|called|titled)\s+(.+)"
        match = re.search(create_task_pattern, text, re.IGNORECASE)
        if match:
            task_name = match.group(1).strip()
            # Remove common trailing words that aren't part of the task name
            task_name = re.sub(r'\s+(?:named|called|titled)\s*$', '', task_name, flags=re.IGNORECASE)
            return task_name, f"Automatically created from: {text}"

        # Handle "do X" pattern
        do_pattern = r"(?:do|complete|finish|start|begin)\s+(.+?)(?:\s+(?:tomorrow|today|tonight|later|now|this\s+\w+|next\s+\w+|yesterday)|\s*$|[.!?])"
        match = re.search(do_pattern, text, re.IGNORECASE)
        if match:
            action = match.group(1).strip()
            return action.capitalize(), f"Automatically created from: {text}"

        # If no specific pattern matched, try to extract meaningful content
        # Remove common phrases and extract the core task
        cleaned_text = re.sub(r"i\s+(?:need|have|want)\s+(?:to|got|a)\s*", "", text, flags=re.IGNORECASE)
        cleaned_text = re.sub(r"please\s+|kindly\s+", "", cleaned_text, flags=re.IGNORECASE)

        # Remove time references from the cleaned text
        for pattern in self.time_patterns + self.date_patterns:
            cleaned_text = re.sub(pattern, "", cleaned_text, flags=re.IGNORECASE)

        # Clean up extra whitespace
        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()

        # Use the cleaned text as the title if it's meaningful
        if len(cleaned_text) > 3:  # Meaningful title should be longer than 3 chars
            return cleaned_text, f"Automatically created from: {text}"
        else:
            # Fallback: use original text as title
            return text, f"Automatically created from: {text}"

    def extract_task_details(self, text: str) -> Dict[str, Any]:
        """
        Extract task details from natural language text using OpenAI API if available,
        otherwise fall back to regex patterns.
        """
        # Use OpenAI to extract task details if available
        title, description, priority_str, task_type_str = self._extract_title_and_description_with_openai(text)

        # Determine task type (prioritize OpenAI result, but fallback to keyword classification)
        task_type = TaskType.GENERAL
        if task_type_str == "meeting":
            task_type = TaskType.MEETING
        elif task_type_str == "appointment":
            task_type = TaskType.APPOINTMENT
        elif task_type_str == "reminder":
            task_type = TaskType.REMINDER
        else:
            # If OpenAI didn't classify or used fallback, use keyword classification
            task_type = self.classify_task_type(text)

        # Convert priority string to enum
        priority = TaskPriority.MEDIUM
        if priority_str == "high":
            priority = TaskPriority.HIGH
        elif priority_str == "low":
            priority = TaskPriority.LOW

        # Extract date/time
        date_time_info = self.extract_date_time(text)

        result = {
            "title": title,
            "description": description,
            "priority": priority.value,
            "task_type": task_type.value
        }

        if date_time_info:
            result.update(date_time_info)

        return result

    def needs_additional_info(self, text: str) -> Dict[str, bool]:
        """
        Determine what additional information might be needed for the task.
        """
        text_lower = text.lower()

        # Check if description is likely missing
        has_description = len(text.split()) > 6  # If the input is quite short, likely missing description

        # Check if due date is mentioned
        date_mentioned = any(keyword in text_lower for keyword in [
            "today", "tomorrow", "tonight", "yesterday",
            "monday", "tuesday", "wednesday", "thursday", "friday",
            "saturday", "sunday", "week", "month", "year",
            "morning", "afternoon", "evening", "night",
            "at", "on", "by", "before", "after", "in", "next"
        ])

        # Check if reminder might be relevant
        reminder_indicators = ["remind", "remember", "don't forget", "alert", "notification"]
        needs_reminder = any(indicator in text_lower for indicator in reminder_indicators)

        return {
            "description": not has_description,
            "due_date": not date_mentioned,
            "reminder": needs_reminder
        }

    async def process_natural_language(self, user_input: str, user_id: str = None, tasks_db: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Process natural language input and create appropriate tasks.
        """
        if not user_input or len(user_input.strip()) < 3:
            return None

        # Extract task details from natural language
        task_details = self.extract_task_details(user_input)

        # Determine if additional information is needed
        additional_info_needed = self.needs_additional_info(user_input)

        # If we have enough information to create a task
        if task_details and task_details.get("title"):
            # Create the task using the task management agent if available
            if self.task_management_agent:
                # Prepare task data
                task_data = {
                    "title": task_details["title"],
                    "description": task_details["description"],
                    "status": "pending",
                    "priority": task_details["priority"],
                    "due_date": task_details.get("due_date"),
                    "due_time": task_details.get("due_time"),
                    "user_id": user_id,
                    "recurring": False,
                    "recurring_pattern": None
                }

                # Create the task using the correct method signature
                created_task = await self.task_management_agent.create_task(
                    title=task_data.get("title", ""),
                    description=task_data.get("description", ""),
                    priority=task_data.get("priority", "medium"),
                    due_date=task_data.get("due_date"),
                    user_id=task_data.get("user_id", ""),
                    recurrence_pattern=task_data.get("recurring_pattern")
                )

                if created_task:
                    # Send event via Kafka if available
                    if self.kafka_agent and hasattr(self.kafka_agent, 'task_created'):
                        # Convert the task to a dictionary for the Kafka event
                        from dataclasses import asdict
                        task_dict = asdict(created_task)
                        await self.kafka_agent.task_created(task_dict)

                    # Prepare response with potential follow-up questions
                    response_message = f"Task '{task_details['title']}' has been created"

                    # Add follow-up suggestions if additional info might be needed
                    follow_up_questions = []
                    if additional_info_needed.get("description", False):
                        follow_up_questions.append("Would you like to add a detailed description?")
                    if additional_info_needed.get("due_date", False):
                        follow_up_questions.append("Would you like to set a due date?")
                    if additional_info_needed.get("reminder", False):
                        follow_up_questions.append("Would you like to set a reminder?")

                    if follow_up_questions:
                        response_message += f". You can enhance this task by: {' '.join(follow_up_questions)}"

                    # Return success response
                    from dataclasses import asdict
                    response = {
                        "success": True,
                        "task_id": created_task.id,
                        "message": response_message,
                        "task_details": asdict(created_task),
                        "needs_additional_info": additional_info_needed
                    }

                    return response
            else:
                # If no task management agent is available, create the task in the provided database
                task_id = f"task_{len(tasks_db) + sum(len(tasks) for tasks_list in tasks_db.values()) + 1}" if tasks_db else f"task_{int(datetime.now().timestamp())}_{len(str(task_details.get('title', '')))}"

                # Create task data similar to main.py
                task_data = {
                    "id": task_id,
                    "title": task_details["title"],
                    "description": task_details["description"],
                    "status": "pending",
                    "priority": task_details.get("priority", "medium"),
                    "due_date": task_details.get("due_date"),
                    "due_time": task_details.get("due_time"),
                    "user_id": user_id or "default_user"
                }

                # Actually save the task to the database if provided
                if tasks_db is not None:
                    user_id_to_use = user_id or "default_user"
                    if user_id_to_use not in tasks_db:
                        tasks_db[user_id_to_use] = []
                    tasks_db[user_id_to_use].append(task_data)

                # Prepare response with potential follow-up questions
                response_message = f"Task '{task_details['title']}' has been created"

                # Add follow-up suggestions if additional info might be needed
                follow_up_questions = []
                if additional_info_needed.get("description", False):
                    follow_up_questions.append("Would you like to add a detailed description?")
                if additional_info_needed.get("due_date", False):
                    follow_up_questions.append("Would you like to set a due date?")
                if additional_info_needed.get("reminder", False):
                    follow_up_questions.append("Would you like to set a reminder?")

                if follow_up_questions:
                    response_message += f". You can enhance this task by: {' '.join(follow_up_questions)}"

                return {
                    "success": True,
                    "task_id": task_id,
                    "message": response_message,
                    "task_details": task_data,
                    "needs_additional_info": additional_info_needed
                }

        # If no task could be created, return None
        return None

    async def process_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process a message through the natural language agent.
        """
        user_input = message.get("content", "")
        user_id = message.get("user_id")

        # Process the natural language input
        result = await self.process_natural_language(user_input, user_id)

        if result:
            # Send response through user interface agent if available
            # Note: The UserInterfaceAgent doesn't have a send_response method
            # This is handled by other parts of the system
            pass

        return result

# Example usage and testing
async def main():
    agent = NaturalLanguageAgent()

    # Test cases
    test_inputs = [
        "I have a meeting tomorrow at 3 PM",
        "I need to call the doctor next week",
        "Don't forget to buy groceries today",
        "I have a dentist appointment on 12/25/2025",
        "Meeting with John tomorrow morning",
        "I have a meeting tommorw",
        "Set a reminder for my birthday next month"
    ]

    print("Testing Natural Language Processing Agent:")
    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: '{test_input}'")
        result = await agent.extract_task_details(test_input)
        print(f"  Extracted: {result}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())