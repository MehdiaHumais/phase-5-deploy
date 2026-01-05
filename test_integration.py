"""
Test script to verify the integrated Todo Chatbot system.
"""

import asyncio
from main_orchestrator import TodoChatbotOrchestrator

async def test_integration():
    """
    Test the integration between agents and skills.
    """
    print("Testing Todo Chatbot System Integration...")

    orchestrator = TodoChatbotOrchestrator()

    try:
        # Initialize the system
        await orchestrator.initialize()
        print("✓ System initialized successfully")

        # Test user registration
        user = await orchestrator.auth_skill.register_user(
            username="test_user",
            email="test@example.com",
            password="TestPass123!"
        )

        if user:
            print(f"✓ User registered: {user['username']}")
            user_id = user['id']

            # Test task creation with reminder
            task = await orchestrator.create_task_with_reminder(
                user_id=user_id,
                title="Test Integration Task",
                description="This is a test task for integration verification",
                due_date=None  # No due date for this test
            )

            if task:
                print(f"✓ Task created: {task['title']}")

                # Test getting user tasks
                user_data = await orchestrator.get_user_tasks_with_reminders(user_id)
                print(f"✓ Retrieved user data: {len(user_data['tasks'])} tasks, {len(user_data['reminders'])} reminders")

                # Test command processing
                command_response = await orchestrator.process_user_command(user_id, "list tasks")
                print(f"✓ Command processed: {len(command_response)} characters in response")

                # Test authentication and action
                auth_result = await orchestrator.authenticate_and_perform_action(
                    "test_user",
                    "TestPass123!",
                    "get_profile"
                )
                print(f"✓ Authentication test: {auth_result['success']}")

            else:
                print("✗ Failed to create task")
        else:
            print("✗ Failed to register user")

    except Exception as e:
        print(f"✗ Error during integration test: {e}")

    finally:
        # Shutdown the system
        await orchestrator.shutdown()
        print("✓ System shutdown complete")

    print("\nIntegration test completed!")

if __name__ == "__main__":
    asyncio.run(test_integration())