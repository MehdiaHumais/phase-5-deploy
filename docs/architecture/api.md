# Todo Chatbot API Design and Endpoints

This document details the API design and endpoints for the Todo Chatbot system.

## API Design Principles

1. **RESTful Design**: Follow REST conventions for resource-based endpoints
2. **Consistent Naming**: Use plural nouns for collections, consistent verb patterns
3. **Versioning**: API versioning through URL path (e.g., `/api/v1/tasks`)
4. **HTTP Status Codes**: Use standard HTTP status codes appropriately
5. **Error Handling**: Consistent error response format
6. **Authentication**: JWT-based authentication for all endpoints
7. **Rate Limiting**: Implement rate limiting to prevent abuse
8. **Documentation**: Self-documenting API with OpenAPI/Swagger

## API Versioning

The API uses URL-based versioning:
- Base path: `/api/v1/`
- All endpoints are versioned (current version: v1)
- Breaking changes will result in new version (v2, v3, etc.)
- Non-breaking changes are added to existing version

## Authentication

All API endpoints (except health checks) require JWT authentication:

```
Authorization: Bearer {access_token}
```

### Token Lifecycle
1. **Login**: `POST /auth/login` → Returns access and refresh tokens
2. **Use Access Token**: Include in Authorization header for API calls
3. **Token Expiry**: Access tokens expire after 30 minutes
4. **Refresh**: Use refresh token to get new access token: `POST /auth/refresh`

## Rate Limiting

- **Per IP**: 100 requests/minute, 1000 requests/hour
- **Per User**: 200 requests/minute, 2000 requests/hour
- **Response Headers**:
  - `X-RateLimit-Limit`: Max requests allowed
  - `X-RateLimit-Remaining`: Requests remaining
  - `X-RateLimit-Reset`: Time when counter resets

## Response Format

### Success Responses
```json
{
  "data": { ... },  // Response data
  "message": "Success message"  // Optional message
}
```

For collections:
```json
{
  "data": [...],  // Array of items
  "pagination": {
    "total": 100,
    "offset": 0,
    "limit": 20,
    "has_more": true
  }
}
```

### Error Responses
```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {  // Optional detailed error info
      "field": "error details"
    }
  }
}
```

## Core Endpoints

### Authentication
- `POST /auth/register` - User registration
- `POST /auth/login` - User login
- `POST /auth/refresh` - Token refresh
- `POST /auth/logout` - User logout
- `GET /auth/me` - Get current user info

### Tasks
- `GET /api/v1/tasks` - Get all tasks with filters
- `POST /api/v1/tasks` - Create a new task
- `GET /api/v1/tasks/{id}` - Get specific task
- `PUT /api/v1/tasks/{id}` - Update task
- `DELETE /api/v1/tasks/{id}` - Delete task
- `POST /api/v1/tasks/{id}/complete` - Mark task as completed
- `POST /api/v1/tasks/{id}/incomplete` - Mark task as incomplete

### Task Management Features
- `GET /api/v1/tasks/search?q={query}` - Search tasks
- `GET /api/v1/tasks?status={status}` - Filter by status
- `GET /api/v1/tasks?priority={priority}` - Filter by priority
- `GET /api/v1/tasks?due_after={date}&due_before={date}` - Filter by due date
- `GET /api/v1/tasks?tags={tag1,tag2}` - Filter by tags

### Users
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update current user profile
- `GET /api/v1/users/me/tasks` - Get current user's tasks
- `GET /api/v1/users/me/settings` - Get user settings
- `PUT /api/v1/users/me/settings` - Update user settings

### Reminders
- `POST /api/v1/reminders` - Create a reminder
- `GET /api/v1/reminders` - Get user's reminders
- `GET /api/v1/reminders/{id}` - Get specific reminder
- `PUT /api/v1/reminders/{id}` - Update reminder
- `DELETE /api/v1/reminders/{id}` - Delete reminder

### Notifications
- `GET /api/v1/notifications` - Get user's notifications
- `GET /api/v1/notifications/unread` - Get unread notifications
- `POST /api/v1/notifications/{id}/read` - Mark notification as read
- `DELETE /api/v1/notifications/{id}` - Delete notification

### Recurring Tasks
- `POST /api/v1/recurring-tasks` - Create recurring task pattern
- `GET /api/v1/recurring-tasks` - Get recurring task patterns
- `GET /api/v1/recurring-tasks/{id}` - Get specific pattern
- `PUT /api/v1/recurring-tasks/{id}` - Update pattern
- `DELETE /api/v1/recurring-tasks/{id}` - Delete pattern

## Request/Response Examples

### Create Task Request
```json
{
  "title": "Buy groceries",
  "description": "Milk, bread, eggs",
  "priority": "medium",
  "due_date": "2025-12-25T10:00:00Z",
  "tags": ["shopping", "urgent"],
  "recurrence_pattern": "none"
}
```

### Create Task Response (201 Created)
```json
{
  "id": "task-123",
  "title": "Buy groceries",
  "description": "Milk, bread, eggs",
  "status": "pending",
  "priority": "medium",
  "due_date": "2025-12-25T10:00:00Z",
  "created_at": "2025-12-20T10:00:00Z",
  "completed_at": null,
  "tags": ["shopping", "urgent"],
  "user_id": "user-456",
  "recurrence_pattern": "none"
}
```

### Error Response (400 Bad Request)
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request validation failed",
    "details": {
      "title": "Field is required",
      "priority": "Must be one of: low, medium, high, urgent"
    }
  }
}
```

## Filtering and Querying

### Query Parameters
- `limit` (integer, default: 20, max: 100) - Number of items to return
- `offset` (integer, default: 0) - Number of items to skip
- `sort` (string, default: "created_at") - Field to sort by
- `order` ("asc" or "desc", default: "desc") - Sort order

### Filtering Examples
```
GET /api/v1/tasks?status=completed&priority=high&limit=10
GET /api/v1/tasks?due_after=2025-12-01&due_before=2025-12-31
GET /api/v1/tasks?tags=work,urgent
GET /api/v1/tasks?search=grocery
```

## WebSockets for Real-time Updates

### Connection
```
ws://localhost:8000/ws?token={jwt_token}
```

### Message Format
```json
{
  "type": "task_updated|task_created|task_deleted|notification",
  "data": { ... },
  "timestamp": "2025-12-20T10:00:00Z"
}
```

## API Security

### Authentication
- JWT tokens with 30-minute expiration
- Refresh tokens with 7-day expiration
- Secure token storage in HTTP-only cookies or secure local storage

### Authorization
- Role-based access control (user, admin)
- Resource ownership (users can only access their own data)
- Permission checks on each endpoint

### Input Validation
- All inputs are validated on the server side
- SQL injection protection through parameterized queries
- XSS prevention through proper output encoding

### Rate Limiting
- Per-user and per-IP rate limiting
- Adaptive rate limiting based on usage patterns
- Rate limit headers in all responses

## Monitoring and Logging

### API Monitoring
- Response time tracking
- Error rate monitoring
- Request volume metrics
- User engagement metrics

### Logging
- Structured logging with correlation IDs
- Request/response logging for debugging
- Security event logging (failed logins, etc.)
- Audit logging for data changes

## API Performance

### Caching Strategy
- Redis-based caching for frequently accessed data
- Cache invalidation on data changes
- Cache headers for HTTP caching

### Database Optimization
- Proper indexing on query fields
- Connection pooling
- Query optimization

### Pagination
- Default page size: 20 items
- Maximum page size: 100 items
- Cursor-based pagination for large datasets

## API Testing

### Test Coverage
- Unit tests for all endpoints
- Integration tests for business logic
- End-to-end tests for user flows
- Performance tests for load scenarios

### Test Data
- Seeded test data for consistent testing
- Mock services for external dependencies
- Test-specific configuration

## API Documentation

### Auto-generated Documentation
- Swagger UI at `/docs`
- ReDoc at `/redoc`
- OpenAPI 3.0 specification at `/openapi.json`

### Manual Documentation
- This document for detailed API design
- Architecture documentation for system design
- Endpoint-specific examples and use cases

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Request validation failed |
| AUTHENTICATION_ERROR | 401 | Authentication required or failed |
| AUTHORIZATION_ERROR | 403 | User not authorized for this action |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict (e.g., duplicate) |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |
| SERVICE_UNAVAILABLE | 503 | Service temporarily unavailable |

## Client Libraries

The API is designed to be easily consumable by various clients:

### JavaScript/TypeScript
```javascript
// Using fetch API
const response = await fetch('/api/v1/tasks', {
  method: 'GET',
  headers: {
    'Authorization': `Bearer ${token}`,
    'Content-Type': 'application/json'
  }
});
```

### Python
```python
import requests

response = requests.get('/api/v1/tasks', headers={
    'Authorization': f'Bearer {token}',
    'Content-Type': 'application/json'
})
```

## Migration Strategy

### From v1 to Future Versions
- Maintain backward compatibility for 6 months
- Announce breaking changes 3 months in advance
- Provide migration guides
- Support parallel versions during transition