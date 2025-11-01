# API Reference

Complete API endpoint documentation for the Restaurant Voice Assistant backend.

## Authentication

All endpoints require authentication via `X-Vapi-Secret` header:

```http
X-Vapi-Secret: your_vapi_secret_key
```

## Base URL

- Local: `http://localhost:8000`
- Production: Your deployed URL

## Endpoints

### Health Check

#### `GET /api/health`

Enhanced health check endpoint with service connectivity checks.

**Features:**

- Checks connectivity to all external services (Supabase, OpenAI, Vapi)
- Returns detailed status for each service
- Measures latency for performance monitoring
- Excluded from rate limiting

**Response (All Healthy):**

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "restaurant-voice-assistant",
  "checks": {
    "supabase": {
      "status": "healthy",
      "latency_ms": 12.5
    },
    "openai": {
      "status": "healthy",
      "latency_ms": 145.3
    },
    "vapi": {
      "status": "healthy",
      "latency_ms": 89.2,
      "assistants": 1
    }
  }
}
```

**Response (Degraded - 503):**

If any critical service (Supabase or OpenAI) is unhealthy, returns HTTP 503:

```json
{
  "status": "degraded",
  "timestamp": "2025-01-01T12:00:00Z",
  "service": "restaurant-voice-assistant",
  "checks": {
    "supabase": {
      "status": "healthy",
      "latency_ms": 12.5
    },
    "openai": {
      "status": "unhealthy",
      "error": "Connection timeout"
    },
    "vapi": {
      "status": "not_configured"
    }
  }
}
```

**Status Codes:**

- `200`: All critical services healthy
- `503`: One or more critical services unhealthy

---

### Restaurants

#### `POST /api/restaurants`

Create a new restaurant with optional automatic phone assignment.

**Headers:**

- `X-Vapi-Secret` (required)

**Request Body:**

```json
{
  "name": "Le Bistro Français",
  "api_key": "optional_custom_api_key",
  "assign_phone": true,
  "force_twilio": false
}
```

**Parameters:**

- `name` (required): Restaurant name
- `api_key` (optional): Custom API key (auto-generated if not provided)
- `assign_phone` (optional, default: `true`): Automatically assign phone number
- `force_twilio` (optional, default: `false`): Skip existing phones, force Twilio creation

**Response:**

```json
{
  "id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
  "name": "Le Bistro Français",
  "api_key": "api_key_abc123",
  "phone_number": "+19014994418",
  "created_at": "2025-01-01T12:00:00Z"
}
```

**Phone Assignment Behavior:**

- If `assign_phone=true` and `force_twilio=false`: Tries existing unassigned phones first, then Twilio if available
- If `assign_phone=true` and `force_twilio=true`: Skips existing phones, directly creates Twilio number
- Returns `phone_number: null` if assignment fails

---

### Vapi Webhooks

#### `POST /api/vapi/assistant-request`

Vapi Assistant Server URL endpoint. Extracts `restaurant_id` from phone number and returns it in metadata for subsequent tool calls.

**Request Body:**

```json
{
  "message": {
    "phoneNumber": "+19014994418",
    "call": {
      "phoneNumber": "+19014994418"
    }
  }
}
```

**Response:**

```json
{
  "metadata": {
    "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
    "phoneNumber": "+19014994418"
  }
}
```

**Returns:** `{}` if phone number not found in mappings.

#### `POST /api/vapi/knowledge-base`

Main Vapi webhook endpoint for Function Tool calls. Performs vector similarity search and returns results.

**Headers:**

- `X-Vapi-Secret` (required)
- `X-Restaurant-Id` (optional, can be in metadata instead)

**Request Body:**

```json
{
  "message": {
    "toolCalls": [
      {
        "id": "call_abc123",
        "function": {
          "name": "get_menu_info",
          "arguments": {
            "query": "What's on your menu?"
          }
        }
      }
    ]
  },
  "metadata": {
    "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d"
  }
}
```

**Tool Names:**

- `get_menu_info` → category: `menu`
- `get_modifiers_info` → category: `modifiers`
- `get_hours_info` → category: `hours`
- `get_zones_info` → category: `zones`

**Restaurant ID Resolution:**

1. `X-Restaurant-Id` header
2. Query parameter `restaurant_id`
3. Request metadata `restaurant_id`
4. Extract from phone number in request body

**Response:**

```json
{
  "results": [
    {
      "toolCallId": "call_abc123",
      "result": "Croissant - Buttery French pastry - $3.50\n\nBaguette - Fresh bread - $2.00",
      "metadata": {
        "items": [
          {
            "type": "menu_item",
            "name": "Croissant",
            "price": 3.5,
            "description": "Buttery French pastry",
            "score": 0.95
          }
        ]
      }
    }
  ]
}
```

**Error Responses:**

- `401`: Invalid `X-Vapi-Secret`
- `422`: Missing `restaurant_id` or invalid request format

---

### Embeddings

#### `POST /api/embeddings/generate`

Generate embeddings for restaurant data (menu, modifiers, hours, zones).

**Headers:**

- `X-Vapi-Secret` (required)

**Request Body:**

```json
{
  "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
  "category": "menu"
}
```

**Parameters:**

- `restaurant_id` (required): Restaurant UUID
- `category` (optional): Specific category to generate (`menu`, `modifiers`, `hours`, `zones`). If omitted, generates for all categories.

**Response:**

```json
{
  "status": "success",
  "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
  "embeddings_generated": 23
}
```

#### `POST /api/embeddings/cache/invalidate`

Force invalidate cache for a restaurant/category.

**Headers:**

- `X-Vapi-Secret` (required)

**Request Body:**

```json
{
  "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
  "category": "menu"
}
```

**Parameters:**

- `restaurant_id` (required): Restaurant UUID
- `category` (optional): Specific category to invalidate. If omitted, invalidates all categories.

**Response:**

```json
{
  "status": "success",
  "message": "Cache cleared for restaurant 04529052-b3dd-43c1-a534-c18d8c0f4c6d"
}
```

---

### Call History

#### `GET /api/calls`

List call history for a restaurant.

**Headers:**

- `X-Restaurant-Id` (optional)

**Query Parameters:**

- `restaurant_id` (optional): Restaurant UUID (if not in header)
- `limit` (optional, default: 50, max: 200): Maximum number of results

**Example:**

```bash
GET /api/calls?restaurant_id=04529052-b3dd-43c1-a534-c18d8c0f4c6d&limit=10
```

**Response:**

```json
{
  "data": [
    {
      "id": "call_abc123",
      "started_at": "2025-01-01T12:00:00Z",
      "ended_at": "2025-01-01T12:05:00Z",
      "duration_seconds": 300,
      "caller": "+1234567890",
      "outcome": "completed",
      "messages": [
        {
          "role": "user",
          "content": "What's on your menu?",
          "timestamp": "2025-01-01T12:00:30Z"
        },
        {
          "role": "assistant",
          "content": "We have croissants, baguettes...",
          "timestamp": "2025-01-01T12:00:35Z"
        }
      ]
    }
  ]
}
```

#### `POST /api/calls`

Create a call history record.

**Headers:**

- `X-Restaurant-Id` (optional)

**Request Body:**

```json
{
  "restaurant_id": "04529052-b3dd-43c1-a534-c18d8c0f4c6d",
  "started_at": "2025-01-01T12:00:00Z",
  "ended_at": "2025-01-01T12:05:00Z",
  "duration_seconds": 300,
  "caller": "+1234567890",
  "outcome": "completed",
  "messages": [
    {
      "role": "user",
      "content": "What's on your menu?",
      "timestamp": "2025-01-01T12:00:30Z"
    }
  ]
}
```

**Restaurant ID Priority:**

1. `X-Restaurant-Id` header
2. `restaurant_id` in request body

**Response:**

```json
{
  "success": true,
  "id": "call_abc123"
}
```

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "detail": "Error message"
}
```

**Common Status Codes:**

- `401`: Authentication failed (invalid `X-Vapi-Secret`)
- `422`: Validation error (missing required field, invalid format)
- `500`: Internal server error

## Rate Limiting

Rate limiting is enabled by default to protect the API from abuse.

**Configuration:**

- Default: 60 requests per minute per IP address
- Configurable via `RATE_LIMIT_ENABLED` and `RATE_LIMIT_PER_MINUTE` environment variables
- Can be disabled by setting `RATE_LIMIT_ENABLED=false`

**Behavior:**

- Applied to all endpoints except:
  - `/api/health` (health checks)
  - `/docs` and `/openapi.json` (API documentation)
  - `/` (root endpoint)

**Response:**
When rate limit is exceeded:

- Status Code: `429 Too Many Requests`
- Response includes:
  - Error message with limit details
  - `X-Request-ID` header for tracking

**Example:**

```json
{
  "detail": "Rate limit exceeded: 60 requests per minute",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

## Request ID Tracking

All API responses include an `X-Request-ID` header for request tracking and debugging.

**Header:**

```http
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

**Usage:**

- Automatically generated for each request
- Included in all error responses
- Used in server logs for correlation
- Can be provided by client (for request tracing)

**Example:**

```bash
curl -H "X-Request-ID: my-custom-id" http://localhost:8000/api/health
```

## Response Formatting

- All timestamps are in ISO 8601 format (UTC)
- All UUIDs are lowercase with hyphens
- Phone numbers are in E.164 format (e.g., `+19014994418`)

## Interactive API Documentation

FastAPI provides interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

These are available in development mode and show all endpoints, request/response schemas, and allow testing directly from the browser.
