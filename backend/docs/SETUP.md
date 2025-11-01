# Setup Guide

Complete setup instructions for the Restaurant Voice Assistant backend.

## Prerequisites

- Docker and Docker Compose
- Supabase account
- OpenAI API account with billing enabled
- Vapi.ai account
- Twilio account (optional, for automatic phone provisioning)

## Step 1: Environment Variables

Copy `.env.example` to `.env` and fill in all required variables.

```bash
cp .env.example .env
```

See [Environment Variables](ENVIRONMENT_VARIABLES.md) for detailed documentation on each variable.

### Required Variables

- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Supabase anonymous key
- `SUPABASE_SERVICE_ROLE_KEY` - Supabase service role key
- `OPENAI_API_KEY` - OpenAI API key
- `VAPI_API_KEY` - Vapi API key
- `VAPI_SECRET_KEY` - Vapi webhook secret
- `PUBLIC_BACKEND_URL` - Public URL of your backend (Cloudflare Tunnel, ngrok, or production URL)

### Optional Variables

- `TWILIO_ACCOUNT_SID` - Twilio Account SID (for automatic phone provisioning)
- `TWILIO_AUTH_TOKEN` - Twilio Auth Token
- `ENVIRONMENT` - Set to `development` or `production` (default: `development`)

## Step 2: Supabase Database Setup

### 2.1 Create Supabase Project

1. Go to [Supabase](https://supabase.com/) and create a new project
2. Wait for the project to be fully provisioned

### 2.2 Enable pgvector Extension

1. Navigate to **Database** → **Extensions** in Supabase Dashboard
2. Search for `pgvector`
3. Click **Enable** next to the `vector` extension

### 2.3 Run Migrations

Run the SQL migrations in order using Supabase SQL Editor:

1. **Open SQL Editor** in Supabase Dashboard
2. Run migrations in this order:
   - `supabase/migrations/000_clean_schema.sql`
   - `supabase/migrations/015_fix_service_role_policies.sql`
   - `supabase/migrations/016_add_phone_mapping_table.sql`

**Note**: Use `999_drop_all_tables.sql` only if you need to reset the entire database.

### 2.4 Get API Keys

1. Go to **Settings** → **API**
2. Copy:
   - **Project URL** → `SUPABASE_URL`
   - **anon public** key → `SUPABASE_ANON_KEY`
   - **service_role** key → `SUPABASE_SERVICE_ROLE_KEY` (keep this secret!)

## Step 3: OpenAI Setup

1. Go to [OpenAI Platform](https://platform.openai.com/)
2. Navigate to **API Keys**
3. Create a new API key
4. Ensure billing is set up (required for embeddings API)
5. Add the key to `.env` as `OPENAI_API_KEY`

## Step 4: Vapi.ai Setup

1. Sign up at [Vapi.ai](https://vapi.ai/)
2. Get your **API Key** from dashboard → `VAPI_API_KEY`
3. Generate a **Webhook Secret** → `VAPI_SECRET_KEY`
4. Add both to `.env`

## Step 5: Public Backend URL

For local development, you need to expose your backend publicly:

### Option A: Cloudflare Tunnel (Recommended)

1. Install `cloudflared`: https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/
2. Run: `cloudflared tunnel --url http://localhost:8000`
3. Copy the generated URL → `PUBLIC_BACKEND_URL`

### Option B: ngrok

1. Install ngrok: https://ngrok.com/
2. Run: `ngrok http 8000`
3. Copy the HTTPS URL → `PUBLIC_BACKEND_URL`

**Note**: Update `PUBLIC_BACKEND_URL` whenever you restart the tunnel.

## Step 6: Twilio Setup (Optional)

Only required if you want automatic phone number provisioning:

1. Sign up at [Twilio](https://www.twilio.com/)
2. Get **Account SID** and **Auth Token** from Console
3. Add to `.env`:
   - `TWILIO_ACCOUNT_SID`
   - `TWILIO_AUTH_TOKEN`

**Note**: Twilio trial accounts are limited to one phone number.

## Step 7: Run Backend

### Start Docker Container

```bash
docker-compose up -d
```

### Verify Backend is Running

```bash
curl http://localhost:8000/api/health
```

Expected response:

```json
{
  "status": "healthy",
  "timestamp": "2025-01-01T12:00:00",
  "service": "restaurant-voice-assistant"
}
```

## Step 8: Configure Vapi Assistant

Create the shared Vapi assistant and tools:

```bash
docker-compose exec api python -m scripts.setup_vapi
```

This script:

- Loads tool configurations from `vapi/config/tools.yaml`
- Creates function tools in Vapi
- Creates or reuses a shared assistant named "Restaurant Voice Assistant"
- Links tools to the assistant

**Important**: Ensure `PUBLIC_BACKEND_URL` is set correctly before running this script.

## Step 9: Seed Database (Testing)

Create a test restaurant with sample data:

```bash
docker-compose exec api python -m scripts.seed_database \
  --restaurant-name "Le Bistro Français" \
  --generate-embeddings
```

This creates:

- A restaurant record
- Menu items, modifiers, operating hours, delivery zones
- Vector embeddings for all data

## Step 10: Assign Phone Number

### Automatic Assignment (Recommended)

Phone numbers are automatically assigned when creating restaurants via API:

```bash
curl -X POST http://localhost:8000/api/restaurants \
  -H "Content-Type: application/json" \
  -H "X-Vapi-Secret: your_secret" \
  -d '{
    "name": "My Restaurant",
    "assign_phone": true
  }'
```

### Manual Assignment

For batch operations, use:

```bash
docker-compose exec api python -m scripts.create_twilio_phone_numbers
```

See [Phone Number Automation](PHONE_NUMBER_AUTOMATION.md) for details.

## Step 11: Test Voice Call

1. Go to Vapi Dashboard → Your Assistant
2. Click **Test Call**
3. Ask: "What's on your menu?"
4. Check backend logs: `docker-compose logs -f api`

## Troubleshooting

### Backend Not Accessible

- Verify Docker container is running: `docker-compose ps`
- Check logs: `docker-compose logs api`
- Verify `PUBLIC_BACKEND_URL` is correct and accessible

### Vapi Tool Calls Failing

- Verify `PUBLIC_BACKEND_URL` is correct
- Check webhook secret matches `VAPI_SECRET_KEY`
- Ensure assistant is configured with correct server URL
- Check backend logs for errors

### No Results from Voice Calls

- Verify restaurant has data: Check Supabase tables
- Generate embeddings: `POST /api/embeddings/generate`
- Ensure phone number is mapped to restaurant in `restaurant_phone_mappings` table

### Database Errors

- Verify all migrations are run
- Check Supabase connection: Test `SUPABASE_URL` and keys
- Ensure pgvector extension is enabled

## Next Steps

- Read [Architecture](ARCHITECTURE.md) to understand the system design
- Review [API Reference](API.md) for endpoint documentation
- Check [Phone Number Automation](PHONE_NUMBER_AUTOMATION.md) for phone provisioning details
