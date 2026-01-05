"""
Test script for Natural Language Processing Agent with full orchestrator
"""
import asyncio
from main_orchestrator import TodoChatbotOrchestrator

async def test_nlp_integration():
    print("Initializing Todo Chatbot Orchestrator...")
    orchestrator = TodoChatbotOrchestrator()

    try:
        await orchestrator.initialize()
        print("Orchestrator initialized successfully!")

        test_inputs = [
            "I have a meeting tomorrow",
            "I need to call John tomorrow",
            "Remind me to buy groceries",
            "I have a dentist appointment next week"
        ]

        print("\nTesting Natural Language Processing with Orchestrator:")
        print("=" * 60)

        for i, test_input in enumerate(test_inputs, 1):
            print(f"\nTest {i}: '{test_input}'")

            # Process with the orchestrator's NLP command
            result = await orchestrator.process_natural_language_command("test_user", test_input)

            if result and result.get("success"):
                print(f"  SUCCESS: {result.get('message', 'Task created')}")
                if result.get("task_id"):
                    print(f"  Task ID: {result['task_id']}")
            else:
                print(f"  FAILED: {result if result else 'No result returned'}")

        print("\n" + "=" * 60)
        print("Integration test completed.")

    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()

    finally:
        try:
            await orchestrator.shutdown()
            print("\nOrchestrator shutdown completed.")
        except Exception as e:
            print(f"Error during shutdown: {e}")

if __name__ == "__main__":
    asyncio.run(test_nlp_integration())