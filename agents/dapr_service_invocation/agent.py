"""
Dapr Service Invocation Agent for Todo Chatbot

This agent handles all Dapr-related operations including:
- Service-to-service invocation using Dapr
- State management with Dapr state store
- Pub/Sub messaging through Dapr
- Secret management with Dapr secret store
- Input/output bindings with Dapr
"""

import asyncio
import httpx
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import json

class DaprServiceInvocationAgent:
    """
    Agent responsible for interacting with Dapr building blocks in the Todo Chatbot system.
    """

    def __init__(self, dapr_http_port: int = 3500, dapr_grpc_port: int = 50001):
        self.dapr_http_port = dapr_http_port
        self.dapr_grpc_port = dapr_grpc_port
        self.base_url = f"http://localhost:{dapr_http_port}"
        self.client = httpx.AsyncClient(timeout=30.0)
        self.app_id = "todo-chatbot-agent"

    async def invoke_service(self, target_app_id: str, method: str, data: Optional[Dict] = None) -> Any:
        """
        Invoke a method on another service using Dapr service invocation.
        """
        url = f"{self.base_url}/v1.0/invoke/{target_app_id}/method/{method}"

        try:
            if data:
                response = await self.client.post(url, json=data)
            else:
                response = await self.client.get(url)

            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during service invocation: {e}")
            raise
        except Exception as e:
            print(f"Error during service invocation: {e}")
            raise

    async def save_state(self, store_name: str, key: str, value: Any,
                         etag: Optional[str] = None,
                         options: Optional[Dict] = None) -> bool:
        """
        Save state to a Dapr state store.
        """
        url = f"{self.base_url}/v1.0/state/{store_name}"

        state_item = {
            "key": key,
            "value": value
        }

        if etag:
            state_item["etag"] = etag
        if options:
            state_item["options"] = options

        try:
            response = await self.client.post(url, json=[state_item])
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during state save: {e}")
            return False
        except Exception as e:
            print(f"Error during state save: {e}")
            return False

    async def get_state(self, store_name: str, key: str,
                       consistency: str = "eventual") -> Any:
        """
        Get state from a Dapr state store.
        """
        url = f"{self.base_url}/v1.0/state/{store_name}/{key}"
        params = {"consistency": consistency}

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None  # Key not found
            print(f"HTTP error during state get: {e}")
            raise
        except Exception as e:
            print(f"Error during state get: {e}")
            raise

    async def delete_state(self, store_name: str, key: str,
                          etag: Optional[str] = None,
                          options: Optional[Dict] = None) -> bool:
        """
        Delete state from a Dapr state store.
        """
        url = f"{self.base_url}/v1.0/state/{store_name}/{key}"

        params = {}
        if etag:
            params["etag"] = etag
        if options:
            # Options would be passed in headers for delete
            pass

        try:
            response = await self.client.delete(url, params=params)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during state delete: {e}")
            return False
        except Exception as e:
            print(f"Error during state delete: {e}")
            return False

    async def publish_event(self, pubsub_name: str, topic_name: str, data: Any) -> bool:
        """
        Publish an event to a Dapr pub/sub broker.
        """
        url = f"{self.base_url}/v1.0/publish/{pubsub_name}/{topic_name}"

        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return True
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during event publish: {e}")
            return False
        except Exception as e:
            print(f"Error during event publish: {e}")
            return False

    async def get_secret(self, store_name: str, key: str,
                        metadata: Optional[Dict] = None) -> Optional[str]:
        """
        Retrieve a secret from a Dapr secret store.
        """
        url = f"{self.base_url}/v1.0/secrets/{store_name}/{key}"

        if metadata:
            params = {"metadata": json.dumps(metadata)}
            response = await self.client.get(url, params=params)
        else:
            response = await self.client.get(url)

        try:
            response.raise_for_status()
            secret_data = response.json()
            return secret_data.get(key)  # Return the actual secret value
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return None  # Secret not found
            print(f"HTTP error during secret get: {e}")
            raise
        except Exception as e:
            print(f"Error during secret get: {e}")
            raise

    async def get_secrets(self, store_name: str,
                         keys: Optional[List[str]] = None,
                         metadata: Optional[Dict] = None) -> Dict[str, str]:
        """
        Retrieve multiple secrets from a Dapr secret store.
        """
        url = f"{self.base_url}/v1.0/secrets/{store_name}/bulk"

        params = {}
        if keys:
            params["keys"] = ",".join(keys)
        if metadata:
            params["metadata"] = json.dumps(metadata)

        try:
            response = await self.client.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during secrets get: {e}")
            raise
        except Exception as e:
            print(f"Error during secrets get: {e}")
            raise

    async def create_binding(self, binding_name: str, operation: str, data: Any,
                            metadata: Optional[Dict] = None) -> Any:
        """
        Invoke an output binding using Dapr.
        """
        url = f"{self.base_url}/v1.0/bindings/{binding_name}"

        payload = {
            "operation": operation,
            "data": data
        }

        if metadata:
            payload["metadata"] = metadata

        try:
            response = await self.client.post(url, json=payload)
            response.raise_for_status()
            return response.json() if response.content else None
        except httpx.HTTPStatusError as e:
            print(f"HTTP error during binding invocation: {e}")
            raise
        except Exception as e:
            print(f"Error during binding invocation: {e}")
            raise

    # Specific methods for Todo Chatbot functionality
    async def save_task_state(self, task_id: str, task_data: Dict[str, Any]) -> bool:
        """
        Save task state using Dapr state management.
        """
        return await self.save_state("statestore", f"task-{task_id}", task_data)

    async def get_task_state(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get task state from Dapr state management.
        """
        return await self.get_state("statestore", f"task-{task_id}")

    async def save_user_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Save user session state using Dapr state management.
        """
        return await self.save_state("statestore", f"session-{user_id}", session_data)

    async def get_user_session(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session state from Dapr state management.
        """
        return await self.get_state("statestore", f"session-{user_id}")

    async def publish_task_event(self, event_type: str, task_data: Dict[str, Any]) -> bool:
        """
        Publish a task-related event using Dapr pub/sub.
        """
        event = {
            "event_type": event_type,
            "task_id": task_data.get("id"),
            "user_id": task_data.get("user_id"),
            "timestamp": datetime.now().isoformat(),
            "data": task_data
        }

        # Use the appropriate topic based on event type
        if event_type.startswith("reminder"):
            topic = "reminders"
        else:
            topic = "task-events"

        return await self.publish_event("kafka-pubsub", topic, event)

    async def publish_reminder_event(self, event_type: str, reminder_data: Dict[str, Any]) -> bool:
        """
        Publish a reminder-related event using Dapr pub/sub.
        """
        event = {
            "event_type": event_type,
            "task_id": reminder_data.get("task_id"),
            "user_id": reminder_data.get("user_id"),
            "timestamp": datetime.now().isoformat(),
            "data": reminder_data
        }

        return await self.publish_event("kafka-pubsub", "reminders", event)

    async def get_api_key(self) -> Optional[str]:
        """
        Get the API key from Dapr secret store.
        """
        return await self.get_secret("kubernetes-secrets", "openai-api-key")

    async def get_database_connection_string(self) -> Optional[str]:
        """
        Get the database connection string from Dapr secret store.
        """
        return await self.get_secret("kubernetes-secrets", "database-connection-string")

    async def trigger_cron_binding(self, cron_data: Dict[str, Any]) -> Any:
        """
        Trigger a cron-based binding using Dapr.
        """
        return await self.create_binding("reminder-cron", "create", cron_data)

    async def get_app_config(self) -> Dict[str, Any]:
        """
        Get application configuration from Dapr secret store.
        """
        try:
            secrets = await self.get_secrets("kubernetes-secrets",
                                           keys=["app-config", "database-url", "api-keys"])
            return secrets
        except Exception as e:
            print(f"Error getting app config: {e}")
            return {}

    async def health_check(self) -> bool:
        """
        Perform a health check on the Dapr sidecar.
        """
        url = f"{self.base_url}/v1.0/healthz"

        try:
            response = await self.client.get(url)
            return response.status_code == 200
        except Exception:
            return False

    async def close(self):
        """
        Close the HTTP client.
        """
        await self.client.aclose()

# Example usage
async def main():
    agent = DaprServiceInvocationAgent()

    try:
        # Check if Dapr is running
        if await agent.health_check():
            print("Dapr sidecar is running")
        else:
            print("Dapr sidecar is not running - this is expected in development without Dapr")
            return  # Skip further tests if Dapr is not available

        # Test state management
        test_data = {"message": "Hello from Dapr agent", "timestamp": datetime.now().isoformat()}
        success = await agent.save_state("statestore", "test-key", test_data)
        print(f"State save successful: {success}")

        retrieved_data = await agent.get_state("statestore", "test-key")
        print(f"Retrieved state: {retrieved_data}")

        # Test secret retrieval (would work in a real Dapr environment)
        try:
            api_key = await agent.get_api_key()
            print(f"API key retrieved: {'Yes' if api_key else 'No'}")
        except Exception as e:
            print(f"Could not retrieve API key (expected in dev environment): {e}")

        print("Dapr Service Invocation Agent initialized and tested")

    except Exception as e:
        print(f"Error in Dapr agent: {e}")
    finally:
        await agent.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())