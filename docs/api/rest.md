# Todo Chatbot REST API Documentation

This document provides detailed information about the Todo Chatbot REST API endpoints.

## Base URL

All API endpoints are relative to:
```
http://localhost:8000
```

When deployed, replace `localhost:8000` with your actual deployment URL.

## Authentication

The API uses JWT-based authentication. Include the access token in the Authorization header:

```
Authorization: Bearer {access_token}
```

## Common Headers

- `Content-Type: application/json`
- `Accept: application/json`

## Error Responses

All error responses follow this format:

```json
{
  "detail": "Error message describing what went wrong"
}
```

## API Endpoints

### Tasks

#### Get All Tasks
- **Endpoint**: `GET /api/tasks`
- **Description**: Retrieve all tasks for the authenticated user
- **Authentication**: Required
- **Parameters**:
  - `status` (optional): Filter by task status (pending, in_progress, completed, cancelled)
  - `priority` (optional): Filter by task priority (low, medium, high, urgent)
  - `limit` (optional): Number of tasks to return (default: 20, max: 100)
  - `offset` (optional): Number of tasks to skip (default: 0)
- **Response**: 200 OK
  ```json
  {
    "tasks": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "status": "string",
        "priority": "string",
        "due_date": "datetime",
        "created_at": "datetime",
        "completed_at": "datetime",
        "tags": ["string"],
        "user_id": "string",
        "recurrence_pattern": "string"
      }
    ],
    "total": 0,
    "offset": 0,
    "limit": 20
  }
  ```

#### Create Task
- **Endpoint**: `POST /api/tasks`
- **Description**: Create a new task
- **Authentication**: Required
- **Request Body**:
  ```json
  {
    "title": "string",
    "description": "string",
    "priority": "medium",
    "due_date": "datetime",
    "tags": ["string"],
    "recurrence_pattern": "string"
  }
  ```
- **Response**: 201 Created
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "pending",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": null,
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
  ```

#### Get Task by ID
- **Endpoint**: `GET /api/tasks/{task_id}`
- **Description**: Retrieve a specific task by its ID
- **Authentication**: Required
- **Parameters**:
  - `task_id`: The ID of the task to retrieve
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": "datetime",
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
  ```

#### Update Task
- **Endpoint**: `PUT /api/tasks/{task_id}`
- **Description**: Update an existing task
- **Authentication**: Required
- **Parameters**:
  - `task_id`: The ID of the task to update
- **Request Body** (all fields optional):
  ```json
  {
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "due_date": "datetime",
    "tags": ["string"],
    "recurrence_pattern": "string"
  }
  ```
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": "datetime",
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
  ```

#### Delete Task
- **Endpoint**: `DELETE /api/tasks/{task_id}`
- **Description**: Delete a task by its ID
- **Authentication**: Required
- **Parameters**:
  - `task_id`: The ID of the task to delete
- **Response**: 204 No Content

#### Complete Task
- **Endpoint**: `POST /api/tasks/{task_id}/complete`
- **Description**: Mark a task as completed
- **Authentication**: Required
- **Parameters**:
  - `task_id`: The ID of the task to complete
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "completed",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": "datetime",
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
  ```

### Users

#### Get Current User Profile
- **Endpoint**: `GET /api/users/me`
- **Description**: Retrieve the profile of the currently authenticated user
- **Authentication**: Required
- **Response**: 200 OK
  ```json
  {
    "id": "string",
    "username": "string",
    "email": "string",
    "role": "string",
    "created_at": "datetime",
    "updated_at": "datetime"
  }
  ```

### Search

#### Search Tasks
- **Endpoint**: `GET /api/search/tasks`
- **Description**: Search tasks by title, description, or tags
- **Authentication**: Required
- **Parameters**:
  - `q`: Search query string
  - `limit` (optional): Number of results to return (default: 20, max: 100)
- **Response**: 200 OK
  ```json
  {
    "tasks": [
      {
        "id": "string",
        "title": "string",
        "description": "string",
        "status": "string",
        "priority": "string",
        "due_date": "datetime",
        "created_at": "datetime",
        "completed_at": "datetime",
        "tags": ["string"],
        "user_id": "string",
        "recurrence_pattern": "string"
      }
    ],
    "total": 0,
    "query": "string"
  }
  ```

## Event Schema

The API publishes events to Kafka. Here are the event schemas:

### Task Event
```json
{
  "event_type": "task_created|task_updated|task_deleted|task_completed",
  "task_id": "string",
  "user_id": "string",
  "timestamp": "datetime",
  "task_data": {
    "id": "string",
    "title": "string",
    "description": "string",
    "status": "string",
    "priority": "string",
    "due_date": "datetime",
    "created_at": "datetime",
    "completed_at": "datetime",
    "tags": ["string"],
    "user_id": "string",
    "recurrence_pattern": "string"
  }
}
```

### Reminder Event
```json
{
  "event_type": "reminder_scheduled|reminder_triggered",
  "task_id": "string",
  "user_id": "string",
  "timestamp": "datetime",
  "title": "string",
  "due_at": "datetime",
  "remind_at": "datetime",
  "notification_type": "email|sms|push|in_app"
}
```

## Status Codes

- `200`: Success
- `201`: Created
- `204`: No Content
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `422`: Validation Error
- `500`: Internal Server Error

## Rate Limiting

The API implements rate limiting to prevent abuse. The default limits are:
- 100 requests per minute per IP
- 1000 requests per hour per IP

When rate limited, the API returns a 429 status code with the following response:
```json
{
  "detail": "Rate limit exceeded"
}
```

## CORS

The API supports Cross-Origin Resource Sharing (CORS). By default, it allows requests from any origin during development. In production, configure allowed origins appropriately.