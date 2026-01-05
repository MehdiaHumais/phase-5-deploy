from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import uvicorn
import asyncio
from datetime import datetime
import json
from passlib.context import CryptContext
import jwt
from datetime import datetime, timedelta
import os

# JWT Configuration
SECRET_KEY = "todo-chatbot-secret-key"  # In production, use a secure random key
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    email: Optional[str] = None
    disabled: Optional[bool] = None

class UserInDB(User):
    hashed_password: str

class UserRegistration(BaseModel):
    username: str
    email: str
    password: str

class UserLogin(BaseModel):
    username: str
    password: str

def verify_password(plain_password, hashed_password):
    # Bcrypt has a 72-byte password limit, so truncate if necessary
    if len(plain_password.encode('utf-8')) > 72:
        plain_password = plain_password[:72]
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Bcrypt has a 72-byte password limit, so truncate if necessary
    if len(password.encode('utf-8')) > 72:
        password = password[:72]
    return pwd_context.hash(password)

def authenticate_user(users_db: Dict, username: str, password: str):
    user = None
    for u in users_db.values():
        if u["username"] == username:
            user = u
            break

    if not user or not verify_password(password, user["hashed_password"]):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now() + expires_delta
    else:
        expire = datetime.now() + timedelta(minutes=15)
    to_encode.update({"exp": expire.timestamp()})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# OAuth2 scheme for token authentication
from fastapi.security import OAuth2PasswordBearer
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# In-memory storage for development
users_db = {}
tasks_db = {}
reminders_db = {}

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.JWTError:
        raise credentials_exception

    user = None
    for u in users_db.values():
        if u["username"] == token_data.username:
            user = u
            break

    if user is None:
        raise credentials_exception
    return user

app = FastAPI(
    title="Todo Chatbot API",
    description="API for managing todos with chatbot integration",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, change this to your specific domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the static files directory
app.mount("/static", StaticFiles(directory="web"), name="static")

# In-memory storage for development
users_db = {}
tasks_db = {}
reminders_db = {}

@app.get("/")
async def root():
    return {
        "message": "Welcome to the Todo Chatbot API",
        "environment": os.getenv("TODO_CHATBOT_ENV", "unknown"),
        "status": "running",
        "endpoints": {
            "web_ui": "/ui",
            "health": "/health",
            "todos": "/todos",
            "tasks": "/tasks",
            "users": "/users"
        }
    }

@app.get("/ui", response_class=HTMLResponse)
async def get_web_ui():
    """Serve the web UI"""
    with open("web/index.html", "r", encoding="utf-8") as file:
        content = file.read()
    return HTMLResponse(content=content)

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "todo-chatbot-api",
        "timestamp": datetime.now().isoformat()
    }

# Authentication endpoints
@app.post("/auth/register", response_model=Token)
async def register(user_data: UserRegistration):
    # Check if user already exists
    for user in users_db.values():
        if user["username"] == user_data.username:
            raise HTTPException(status_code=400, detail="Username already registered")
        if user["email"] == user_data.email:
            raise HTTPException(status_code=400, detail="Email already registered")

    user_id = f"user_{len(users_db) + 1}"
    hashed_password = get_password_hash(user_data.password)

    user = {
        "id": user_id,
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "created_at": datetime.now().isoformat(),
        "tasks": []
    }
    users_db[user_id] = user

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/auth/login", response_model=Token)
async def login(credentials: UserLogin):
    user = authenticate_user(users_db, credentials.username, credentials.password)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user["username"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}

# User endpoints
@app.post("/users/register")
async def register_user(user_data: Dict):
    user_id = f"user_{len(users_db) + 1}"
    user = {
        "id": user_id,
        "username": user_data.get("username"),
        "email": user_data.get("email"),
        "created_at": datetime.now().isoformat(),
        "tasks": []
    }
    users_db[user_id] = user
    return user

@app.post("/users/login")
async def login_user(credentials: Dict):
    username = credentials.get("username")
    # Simple validation - in real app, use proper auth
    for user in users_db.values():
        if user["username"] == username:
            return {
                "user_id": user["id"],
                "username": user["username"],
                "access_token": f"token_{user['id']}",
                "status": "success"
            }
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Task endpoints
@app.get("/tasks")
async def get_tasks():
    """Get all tasks"""
    all_tasks = []
    for task_list in tasks_db.values():
        all_tasks.extend(task_list)
    return {"tasks": all_tasks}

@app.post("/tasks")
async def create_task(task_data: Dict):
    """Create a new task"""
    task_id = f"task_{len(tasks_db) + sum(len(tasks) for tasks in tasks_db.values()) + 1}"
    task = {
        "id": task_id,
        "title": task_data.get("title"),
        "description": task_data.get("description", ""),
        "priority": task_data.get("priority", "medium"),
        "status": "pending",
        "due_date": task_data.get("due_date"),
        "created_at": datetime.now().isoformat(),
        "user_id": task_data.get("user_id", "default_user")
    }

    user_id = task["user_id"]
    if user_id not in tasks_db:
        tasks_db[user_id] = []
    tasks_db[user_id].append(task)

    # If the task has a due date, create a reminder for it
    due_date_str = task_data.get("due_date")
    if due_date_str:
        from datetime import datetime as dt_datetime
        try:
            # Parse the due date
            due_date = dt_datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            if due_date.tzinfo is not None:
                due_date = due_date.replace(tzinfo=None)

            # Import and use the reminder skill to create due date reminders
            from skills.reminder_scheduling.skill import ReminderSchedulingSkill, NotificationType
            reminder_skill = ReminderSchedulingSkill()

            # Create both pre-due and overdue reminders
            await reminder_skill.create_due_date_reminder(
                task_id=task_id,
                user_id=user_id,
                due_date=due_date,
                notification_type=NotificationType.IN_APP
            )
        except ValueError:
            # If date parsing fails, just continue without creating a reminder
            pass

    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: str, task_data: Dict):
    """Update a task"""
    for user_tasks in tasks_db.values():
        for i, task in enumerate(user_tasks):
            if task["id"] == task_id:
                user_tasks[i].update(task_data)
                user_tasks[i]["updated_at"] = datetime.now().isoformat()
                return user_tasks[i]

    raise HTTPException(status_code=404, detail="Task not found")

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    """Delete a task"""
    for user_id, user_tasks in tasks_db.items():
        for i, task in enumerate(user_tasks):
            if task["id"] == task_id:
                deleted_task = user_tasks.pop(i)
                return {"message": "Task deleted", "task": deleted_task}

    raise HTTPException(status_code=404, detail="Task not found")

# Reminder endpoints
@app.post("/reminders")
async def create_reminder(reminder_data: Dict):
    """Create a new reminder"""
    # Import the reminder skill
    from skills.reminder_scheduling.skill import ReminderSchedulingSkill, NotificationType
    from datetime import datetime

    # Create a temporary reminder skill instance
    # In a real application, this would be a shared instance
    reminder_skill = ReminderSchedulingSkill()

    task_id = reminder_data.get("task_id")
    user_id = reminder_data.get("user_id", "default_user")
    notification_type = reminder_data.get("notification_type", "in_app")
    reminder_time_str = reminder_data.get("reminder_time")
    message = reminder_data.get("message", "Task reminder")
    title = reminder_data.get("title", f"Reminder for task {task_id}")

    if not task_id or not reminder_time_str:
        raise HTTPException(status_code=400, detail="task_id and reminder_time are required")

    try:
        # Handle timezone-aware datetime
        reminder_time = datetime.fromisoformat(reminder_time_str.replace('Z', '+00:00'))
        # If it's timezone-aware, convert to naive for comparison with datetime.now()
        if reminder_time.tzinfo is not None:
            reminder_time = reminder_time.replace(tzinfo=None)
        notification_enum = NotificationType(notification_type)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid reminder_time format or notification_type")

    # Create the reminder
    reminder = await reminder_skill.create_reminder(
        task_id=task_id,
        user_id=user_id,
        notification_type=notification_enum,
        reminder_time=reminder_time,
        message=message,
        title=title
    )

    return reminder

@app.get("/reminders/{user_id}")
async def get_reminders(user_id: str):
    """Get all reminders for a user"""
    # Import the reminder skill
    from skills.reminder_scheduling.skill import ReminderSchedulingSkill

    # Create a temporary reminder skill instance
    reminder_skill = ReminderSchedulingSkill()

    # Get reminders for the user
    reminders = await reminder_skill.get_reminders_for_user(user_id)

    return {"reminders": reminders}

@app.get("/reminders/task/{task_id}")
async def get_reminders_for_task(task_id: str):
    """Get all reminders for a specific task"""
    # Import the reminder skill
    from skills.reminder_scheduling.skill import ReminderSchedulingSkill

    # Create a temporary reminder skill instance
    reminder_skill = ReminderSchedulingSkill()

    # Get reminders for the task
    reminders = await reminder_skill.get_reminders_for_task(task_id)

    return {"reminders": reminders}

# Natural language processing endpoint
@app.post("/natural_language")
async def process_natural_language(message_data: Dict):
    """Process natural language input and create tasks automatically"""
    user_message = message_data.get("message", "")
    user_id = message_data.get("user_id", "default_user")

    # Use the enhanced natural language agent
    from agents.natural_language_agent.agent import NaturalLanguageAgent
    nlp_agent = NaturalLanguageAgent()

    # Process the natural language using the agent's method
    # Pass the database reference to the agent for task persistence
    result = await nlp_agent.process_natural_language(user_message, user_id, tasks_db)

    if result and result.get("success"):
        # If the agent created a task, return the agent's response
        response_data = {
            "success": True,
            "message": result.get("message", f"Task created successfully"),
            "task_id": result.get("task_id"),
            "timestamp": datetime.now().isoformat()
        }

        # Include additional info if available
        if "needs_additional_info" in result:
            response_data["needs_additional_info"] = result["needs_additional_info"]

        return response_data
    else:
        # Fallback to basic task creation if agent processing fails
        task_details = nlp_agent.extract_task_details(user_message)

        # Create a task using the same format as the UI form
        task_data = {
            "title": task_details.get("title", user_message),
            "description": f"Created from natural language input: '{user_message}'",
            "priority": task_details.get("priority", "medium"),
            "status": "pending",
            "due_date": task_details.get("due_date"),
            "due_time": task_details.get("due_time"),
            "user_id": user_id
        }

        # Create the task using the same method as the /tasks endpoint
        task_id = f"task_{len(tasks_db) + sum(len(tasks) for tasks_list in tasks_db.values()) + 1}"
        task_data["id"] = task_id

        # Add to user's task list
        if user_id not in tasks_db:
            tasks_db[user_id] = []
        tasks_db[user_id].append(task_data)

        # Return success response
        return {
            "success": True,
            "message": f"Task '{task_data['title']}' has been created",
            "task_id": task_id,
            "timestamp": datetime.now().isoformat()
        }

# Simple chat endpoint
@app.post("/chat")
async def chat_with_bot(message_data: Dict):
    """Chat with the todo bot"""
    message = message_data.get("message", "").lower()
    user_id = message_data.get("user_id", "default_user")

    # Note: Natural language processing for task creation is handled by the /natural_language endpoint
    # The chat endpoint should only handle conversational responses

    # Regular chat responses
    if "hello" in message or "hi" in message:
        response = "Hello! I'm your Todo Chatbot. How can I help you with your tasks today?"
    elif "task" in message or "todo" in message:
        if "create" in message or "add" in message:
            response = "To add a new task, use the task creation form. Just enter the task title and description!"
        elif "list" in message or "show" in message:
            total_tasks = sum(len(tasks) for tasks in tasks_db.values())
            response = f"You have {total_tasks} tasks in your list. You can see them in the tasks section!"
        else:
            response = "I can help you manage your tasks. Try asking me to create a task, list your tasks, or set reminders."
    elif "reminder" in message or "due" in message:
        response = "You can set reminders for your tasks using the reminder functionality."
    elif "help" in message:
        response = "Here's how I can help you:\n• Add tasks using the form\n• List your current tasks\n• Set reminders\n• Mark tasks as completed\n• Ask about specific tasks"
    else:
        response = f"I understand you mentioned: '{message_data.get('message')}'. I can help you manage your tasks. Try asking me to create a task, list your tasks, or set reminders. Or just tell me what you need to do, like 'I have a meeting tomorrow'!"

    return {
        "response": response,
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)