# Environment Variables

Complete reference for all environment variables used by the Restaurant Voice Assistant backend.

## Quick Reference

| Variable                    | Required | Description                               |
| --------------------------- | -------- | ----------------------------------------- |
| `SUPABASE_URL`              | Yes      | Supabase project URL                      |
| `SUPABASE_ANON_KEY`         | Yes      | Supabase anonymous key                    |
| `SUPABASE_SERVICE_ROLE_KEY` | Yes      | Supabase service role key                 |
| `OPENAI_API_KEY`            | Yes      | OpenAI API key                            |
| `VAPI_API_KEY`              | Yes      | Vapi API key                              |
| `VAPI_SECRET_KEY`           | Yes      | Vapi webhook secret                       |
| `PUBLIC_BACKEND_URL`        | Yes      | Public URL of backend API                 |
| `TWILIO_ACCOUNT_SID`        | No       | Twilio Account SID (for phone automation) |
| `TWILIO_AUTH_TOKEN`         | No       | Twilio Auth Token (for phone automation)  |
| `ENVIRONMENT`               | No       | Environment type (default: `development`) |

## Detailed Documentation

### SUPABASE_URL

**Required**: Yes  
**Format**: `https://your-project-ref.supabase.co`

Your Supabase project URL. Found in Supabase Dashboard → Settings → API → Project URL.

**Example:**

```bash
SUPABASE_URL=https://coeetmhcivmcxgrhsoty.supabase.co
```

**Used by:**

- `src/services/supabase_client.py` - Database connection

---

### SUPABASE_ANON_KEY

**Required**: Yes  
**Format**: JWT token string

Supabase anonymous key for read operations. Subject to Row Level Security (RLS) policies.

**Location**: Supabase Dashboard → Settings → API → `anon` `public` key

**Security**: Safe to use in client-side code, but has RLS restrictions.

**Used by:**

- `src/services/supabase_client.py` - `get_supabase_client()` function
- Also used as fallback if `SUPABASE_SERVICE_ROLE_KEY` is not set

---

### SUPABASE_SERVICE_ROLE_KEY

**Required**: Yes  
**Format**: JWT token string

Supabase service role key that bypasses RLS. Used for admin operations and writes.

**Location**: Supabase Dashboard → Settings → API → `service_role` `secret` key

**Security**: **Keep this secret!** Never expose in client-side code. Bypasses all RLS policies.

**Used by:**

- `src/services/supabase_client.py` - `get_supabase_service_client()` function
- All write operations (inserts, updates, deletes)

---

### OPENAI_API_KEY

**Required**: Yes  
**Format**: `sk-proj-...` string

OpenAI API key for generating embeddings. Requires billing-enabled account.

**Location**: https://platform.openai.com/api-keys

**Model Used**: `text-embedding-3-small` (1536 dimensions)

**Used by:**

- `src/services/embedding_service.py` - Embedding generation

---

### VAPI_API_KEY

**Required**: Yes  
**Format**: UUID or token string

Vapi API key for programmatic access to Vapi resources (assistants, tools, phone numbers).

**Location**: Vapi Dashboard → API Keys

**Used by:**

- `vapi/client.py` - Vapi API client
- `src/services/phone_service.py` - Phone assignment
- `scripts/setup_vapi.py` - Assistant/tool creation

---

### VAPI_SECRET_KEY

**Required**: Yes  
**Format**: UUID or token string

Vapi webhook secret for authenticating webhook requests from Vapi.

**Location**: Vapi Dashboard → Webhooks → Secret

**Security**: Used to verify requests are actually from Vapi (HMAC verification).

**Used by:**

- `src/services/auth.py` - `verify_vapi_secret()` function
- All `/api/vapi/*` endpoints

---

### PUBLIC_BACKEND_URL

**Required**: Yes  
**Format**: `https://your-url.com` or `http://localhost:8000` (for local testing)

Public URL where your backend API is accessible. This is used by Vapi to make webhook calls to your backend.

**Local Development Options:**

- **Cloudflare Tunnel**: `https://xxxxx.trycloudflare.com`
- **ngrok**: `https://xxxxx.ngrok.io`

**Production**: Your deployed URL (e.g., Render, Railway, etc.)

**Important**:

- Must be HTTPS (Vapi requires secure webhooks)
- Update whenever tunnel URL changes
- Must be accessible from the internet (not `localhost`)

**Used by:**

- `vapi/manager.py` - Tool server URL configuration
- `src/services/phone_service.py` - Phone service initialization
- `scripts/setup_vapi.py` - Vapi setup

---

### TWILIO_ACCOUNT_SID

**Required**: No (optional)  
**Format**: `AC...` string

Twilio Account SID for automatic phone number provisioning.

**Location**: Twilio Console → Account Info

**Used by:**

- `src/services/twilio_service.py` - Twilio API calls
- `scripts/create_twilio_phone_numbers.py` - Batch phone creation

**Note**: Only required if you want automatic Twilio phone number creation. Without this, the system will only use existing unassigned phones or Vapi free numbers.

---

### TWILIO_AUTH_TOKEN

**Required**: No (optional)  
**Format**: Token string

Twilio Auth Token for authenticating Twilio API requests.

**Location**: Twilio Console → Account Info

**Security**: Keep this secret. Used to authenticate Twilio API calls.

**Used by:**

- `src/services/twilio_service.py` - Twilio API calls
- `scripts/create_twilio_phone_numbers.py` - Batch phone creation

**Note**: Required together with `TWILIO_ACCOUNT_SID` for automatic phone provisioning.

---

### ENVIRONMENT

**Required**: No (optional)  
**Default**: `development`  
**Values**: `development` | `production`

Environment type used for:

- Logging level (DEBUG in development, INFO in production)
- Error message detail (full errors in development, generic in production)

**Used by:**

- `src/main.py` - Logging configuration and error handling

**Example:**

```bash
ENVIRONMENT=production
```

---

### RATE_LIMIT_ENABLED

**Required**: No (optional)  
**Default**: `true`  
**Values**: `true` | `false`

Enable or disable rate limiting on API endpoints.

**Behavior:**

- When `true`: Rate limiting is applied to all endpoints (except health checks and docs)
- When `false`: Rate limiting is completely disabled

**Used by:**

- `src/main.py` - Rate limiting middleware

**Example:**

```bash
RATE_LIMIT_ENABLED=true
```

---

### RATE_LIMIT_PER_MINUTE

**Required**: No (optional)  
**Default**: `60`  
**Values**: Positive integer

Maximum number of requests allowed per minute per IP address.

**Behavior:**

- Applies per IP address (based on `X-Forwarded-For` or direct connection)
- Excluded endpoints: `/api/health`, `/docs`, `/openapi.json`, `/`
- Returns HTTP 429 when limit exceeded

**Used by:**

- `src/main.py` - Rate limiting middleware

**Example:**

```bash
RATE_LIMIT_PER_MINUTE=60
```

**Note**: Adjust based on your expected traffic and server capacity.

---

## Environment File Setup

### Development

Create `.env` file in `backend/` directory:

```bash
cp .env.example .env
```

Fill in all required variables.

### Production

Set environment variables in your deployment platform (Render, Railway, etc.). Do not commit `.env` file to version control.

---

## Variable Priority

1. Environment variables set in Docker Compose (for local development)
2. `.env` file (for local development)
3. System environment variables (for production)

**Note**: Docker Compose reads from `.env` file and passes variables to containers.

---

## Validation

The application validates required variables on startup:

- Missing required variables will cause startup failures
- Optional variables (Twilio) are checked only when needed

## Security Best Practices

1. **Never commit** `.env` file to version control
2. **Use** `.env.example` as template
3. **Rotate** keys regularly
4. **Restrict** access to production environment variables
5. **Use** different keys for development and production

## Troubleshooting

### Variables Not Loading

- Verify `.env` file is in `backend/` directory
- Check Docker Compose `environment` section
- Restart Docker container after changes

### Missing Variables

- Check error logs for specific missing variable
- Verify variable name spelling (case-sensitive)
- Ensure no trailing spaces in `.env` file
