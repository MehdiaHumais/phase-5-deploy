"""
Test script for Natural Language Processing Agent
"""
import asyncio
from agents.natural_language_agent.agent import NaturalLanguageAgent

async def test_nlp_agent():
    agent = NaturalLanguageAgent()

    test_inputs = [
        "I have a meeting tomorrow",
        "I need to call John tomorrow",
        "Remind me to buy groceries",
        "I have a dentist appointment next week",
        "Meeting with the team today",
        "I have a meeting tommorw",  # Test typo handling
        "Nothing special today"
    ]

    print("Testing Natural Language Processing Agent:")
    print("=" * 50)

    for i, test_input in enumerate(test_inputs, 1):
        print(f"\nTest {i}: '{test_input}'")

        # Create a mock message
        message = {
            "content": test_input,
            "user_id": "test_user",
            "timestamp": "2025-12-23T10:00:00"
        }

        # Process the message
        result = await agent.process_message(message)

        if result:
            print(f"  Result: {result}")
        else:
            print(f"  Result: No task created from this input")

    print("\n" + "=" * 50)
    print("Test completed.")

if __name__ == "__main__":
    asyncio.run(test_nlp_agent())