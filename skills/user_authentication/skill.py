"""
User Authentication Skill for Todo Chatbot

This skill provides capabilities for user authentication and authorization in the Todo Chatbot system.
"""

import asyncio
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
import jwt
from passlib.context import CryptContext

class AuthMethod(Enum):
    PASSWORD = "password"
    TOKEN = "token"
    OAUTH = "oauth"

class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"

class UserAuthenticationSkill:
    """
    Skill that provides capabilities for user authentication and authorization in the Todo Chatbot system.
    """

    def __init__(self, secret_key: str = "todo-chatbot-secret-key", algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.users: Dict[str, Dict[str, Any]] = {}
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.tokens: Dict[str, Dict[str, Any]] = {}
        self.dapr_integration = None

    def set_dapr_integration(self, dapr_integration):
        """
        Set the Dapr integration for this skill.
        """
        self.dapr_integration = dapr_integration

    def _hash_password(self, password: str) -> str:
        """
        Hash a password using bcrypt.
        """
        # Bcrypt has a 72-byte password limit, so truncate if necessary
        if len(password.encode('utf-8')) > 72:
            password = password[:72]
        return self.pwd_context.hash(password)

    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify a plain password against a hashed password.
        """
        # Bcrypt has a 72-byte password limit, so truncate if necessary
        if len(plain_password.encode('utf-8')) > 72:
            plain_password = plain_password[:72]
        return self.pwd_context.verify(plain_password, hashed_password)

    def _generate_token(self, user_id: str, expires_delta: Optional[timedelta] = None) -> str:
        """
        Generate a JWT token for a user.
        """
        if expires_delta:
            expire = datetime.now() + expires_delta
        else:
            expire = datetime.now() + timedelta(minutes=30)

        to_encode = {
            "sub": user_id,
            "exp": expire.timestamp(),
            "iat": datetime.now().timestamp()
        }

        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def _decode_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Decode a JWT token.
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.JWTError:
            return None

    async def register_user(self,
                           username: str,
                           email: str,
                           password: str,
                           role: UserRole = UserRole.USER,
                           metadata: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Register a new user with password strength validation.
        """
        # Validate inputs
        if not username or not email or not password:
            return None

        # Validate email format
        if "@" not in email or "." not in email:
            return None

        # Validate password strength
        password_errors = await self.validate_password_strength(password)
        if password_errors:
            return None

        # Check if user already exists
        if any(user["username"] == username for user in self.users.values()):
            return None

        if any(user["email"] == email for user in self.users.values()):
            return None

        user_id = f"user_{secrets.token_urlsafe(8)}"
        hashed_password = self._hash_password(password)

        user = {
            "id": user_id,
            "username": username,
            "email": email,
            "hashed_password": hashed_password,
            "role": role.value,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "is_active": True,
            "metadata": metadata or {}
        }

        self.users[user_id] = user

        # Save user to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"user-{user_id}", user)

        return user

    async def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """
        Authenticate a user with username and password.
        """
        # Find user by username
        user = None
        for u in self.users.values():
            if u["username"] == username:
                user = u
                break

        if not user or not user["is_active"]:
            return None

        if not self._verify_password(password, user["hashed_password"]):
            return None

        return user

    async def login_user(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """
        Login a user and return access and refresh tokens.
        """
        user = await self.authenticate_user(username, password)
        if not user:
            return None

        access_token = self._generate_token(user["id"])
        refresh_token = self._generate_token(user["id"], expires_delta=timedelta(days=7))

        # Create session
        session_id = f"session_{secrets.token_urlsafe(16)}"
        session = {
            "id": session_id,
            "user_id": user["id"],
            "created_at": datetime.now().isoformat(),
            "last_activity": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat()
        }

        self.sessions[session_id] = session

        # Save session to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"session-{session_id}", session)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "session_id": session_id
        }

    async def logout_user(self, session_id: str) -> bool:
        """
        Logout a user by invalidating their session.
        """
        if session_id in self.sessions:
            del self.sessions[session_id]

            # Delete session from Dapr state if available
            if self.dapr_integration:
                await self.dapr_integration.delete_state("statestore", f"session-{session_id}")

            return True
        return False

    async def refresh_token(self, refresh_token: str) -> Optional[Dict[str, str]]:
        """
        Refresh an access token using a refresh token.
        """
        payload = self._decode_token(refresh_token)
        if not payload:
            return None

        user_id = payload.get("sub")
        if not user_id or user_id not in self.users:
            return None

        # Generate new access token
        new_access_token = self._generate_token(user_id)
        new_refresh_token = self._generate_token(user_id, expires_delta=timedelta(days=7))

        return {
            "access_token": new_access_token,
            "refresh_token": new_refresh_token,
            "token_type": "bearer"
        }

    async def get_user_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """
        Get user information from a valid token.
        """
        payload = self._decode_token(token)
        if not payload:
            return None

        user_id = payload.get("sub")
        return self.users.get(user_id)

    async def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user information by user ID.
        """
        # Try to get from memory first
        user = self.users.get(user_id)
        if user:
            return user

        # If not in memory, try to get from Dapr state if available
        if self.dapr_integration:
            user = await self.dapr_integration.get_state("statestore", f"user-{user_id}")
            if user:
                # Cache it in memory
                self.users[user_id] = user
                return user

        return None

    async def update_user(self, user_id: str, **updates) -> Optional[Dict[str, Any]]:
        """
        Update user information.
        """
        if user_id not in self.users:
            return None

        user = self.users[user_id]

        # Update allowed fields
        allowed_fields = {"username", "email", "role", "is_active", "metadata", "updated_at"}
        for field, value in updates.items():
            if field in allowed_fields:
                if field == "password":
                    user["hashed_password"] = self._hash_password(value)
                else:
                    user[field] = value

        user["updated_at"] = datetime.now().isoformat()

        # Save updated user to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"user-{user_id}", user)

        return user

    async def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change a user's password.
        """
        user = self.users.get(user_id)
        if not user:
            return False

        if not self._verify_password(current_password, user["hashed_password"]):
            return False

        # Ensure new password is within bcrypt limits before hashing
        if len(new_password.encode('utf-8')) > 72:
            new_password = new_password[:72]

        user["hashed_password"] = self._hash_password(new_password)
        user["updated_at"] = datetime.now().isoformat()

        # Save updated user to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"user-{user_id}", user)

        return True

    async def validate_token(self, token: str) -> bool:
        """
        Validate a token without returning user information.
        """
        payload = self._decode_token(token)
        return payload is not None

    async def get_user_role(self, user_id: str) -> Optional[UserRole]:
        """
        Get the role of a user.
        """
        user = self.users.get(user_id)
        if not user:
            return None

        return UserRole(user["role"])

    async def has_permission(self, user_id: str, required_role: UserRole) -> bool:
        """
        Check if a user has the required role or higher permissions.
        """
        user = self.users.get(user_id)
        if not user:
            return False

        user_role = UserRole(user["role"])

        # Define role hierarchy: admin > user > guest
        role_hierarchy = {
            UserRole.ADMIN: 3,
            UserRole.USER: 2,
            UserRole.GUEST: 1
        }

        return role_hierarchy[user_role] >= role_hierarchy[required_role]

    async def deactivate_user(self, user_id: str) -> bool:
        """
        Deactivate a user account.
        """
        if user_id not in self.users:
            return False

        self.users[user_id]["is_active"] = False
        self.users[user_id]["updated_at"] = datetime.now().isoformat()

        # Save updated user to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"user-{user_id}", self.users[user_id])

        return True

    async def activate_user(self, user_id: str) -> bool:
        """
        Activate a user account.
        """
        if user_id not in self.users:
            return False

        self.users[user_id]["is_active"] = True
        self.users[user_id]["updated_at"] = datetime.now().isoformat()

        # Save updated user to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"user-{user_id}", self.users[user_id])

        return True

    async def get_user_statistics(self) -> Dict[str, int]:
        """
        Get statistics about users.
        """
        stats = {
            "total_users": len(self.users),
            "active_users": 0,
            "inactive_users": 0,
            "by_role": {}
        }

        for user in self.users.values():
            if user["is_active"]:
                stats["active_users"] += 1
            else:
                stats["inactive_users"] += 1

            role = user["role"]
            if role not in stats["by_role"]:
                stats["by_role"][role] = 0
            stats["by_role"][role] += 1

        return stats

    async def validate_password_strength(self, password: str) -> List[str]:
        """
        Validate password strength and return a list of validation errors.
        """
        errors = []

        if len(password) < 8:
            errors.append("Password must be at least 8 characters long")

        if not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")

        if not any(c.islower() for c in password):
            errors.append("Password must contain at least one lowercase letter")

        if not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one digit")

        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")

        return errors

    async def create_api_key(self, user_id: str, name: str, expires_in_days: Optional[int] = None) -> Optional[str]:
        """
        Create an API key for a user.
        """
        if user_id not in self.users:
            return None

        api_key = f"todo_{secrets.token_urlsafe(32)}"
        key_data = {
            "api_key": api_key,
            "user_id": user_id,
            "name": name,
            "created_at": datetime.now().isoformat(),
            "last_used": None
        }

        if expires_in_days:
            expiry_date = datetime.now() + timedelta(days=expires_in_days)
            key_data["expires_at"] = expiry_date.isoformat()

        self.tokens[api_key] = key_data

        # Save token to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"token-{api_key}", key_data)

        return api_key

    async def validate_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """
        Validate an API key and return associated user info.
        """
        if api_key not in self.tokens:
            return None

        key_data = self.tokens[api_key]

        # Check if token is expired
        if "expires_at" in key_data:
            expiry_date = datetime.fromisoformat(key_data["expires_at"])
            if datetime.now() > expiry_date:
                del self.tokens[api_key]  # Remove expired token
                # Delete from Dapr state if available
                if self.dapr_integration:
                    await self.dapr_integration.delete_state("statestore", f"token-{api_key}")
                return None

        # Update last used time
        key_data["last_used"] = datetime.now().isoformat()

        # Save updated token to Dapr state if available
        if self.dapr_integration:
            await self.dapr_integration.save_state("statestore", f"token-{api_key}", key_data)

        return key_data

    async def revoke_api_key(self, api_key: str) -> bool:
        """
        Revoke an API key.
        """
        if api_key in self.tokens:
            del self.tokens[api_key]

            # Delete from Dapr state if available
            if self.dapr_integration:
                await self.dapr_integration.delete_state("statestore", f"token-{api_key}")

            return True
        return False

    async def get_user_sessions(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all active sessions for a user.
        """
        user_sessions = []
        for session in self.sessions.values():
            if session["user_id"] == user_id:
                user_sessions.append(session)
        return user_sessions

    async def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions and return the count of removed sessions.
        """
        expired_sessions = []
        now = datetime.now()

        for session_id, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session["expires_at"])
            if now > expires_at:
                expired_sessions.append(session_id)

        for session_id in expired_sessions:
            del self.sessions[session_id]

            # Delete from Dapr state if available
            if self.dapr_integration:
                await self.dapr_integration.delete_state("statestore", f"session-{session_id}")

        return len(expired_sessions)

# Example usage
async def main():
    skill = UserAuthenticationSkill()

    # Register a new user
    user = await skill.register_user(
        username="johndoe",
        email="john@example.com",
        password="SecurePass123!",
        role=UserRole.USER
    )

    if user:
        print(f"User registered: {user['username']}")

        # Try to login
        tokens = await skill.login_user("johndoe", "SecurePass123!")
        if tokens:
            print(f"Login successful. Access token: {tokens['access_token'][:20]}...")

            # Get user by token
            authenticated_user = await skill.get_user_by_token(tokens['access_token'])
            if authenticated_user:
                print(f"Authenticated user: {authenticated_user['username']}")

            # Check permissions
            has_perm = await skill.has_permission(authenticated_user['id'], UserRole.USER)
            print(f"User has USER permission: {has_perm}")

            # Get user statistics
            stats = await skill.get_user_statistics()
            print(f"User statistics: {stats}")

            # Create an API key
            api_key = await skill.create_api_key(authenticated_user['id'], "my-app-key")
            if api_key:
                print(f"API key created: {api_key[:10]}...")

                # Validate the API key
                key_info = await skill.validate_api_key(api_key)
                print(f"API key validated: {key_info['name']}")

        else:
            print("Login failed")

    print("User Authentication Skill initialized and tested")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())