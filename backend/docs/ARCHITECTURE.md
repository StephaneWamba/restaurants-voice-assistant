# Architecture

System architecture and design patterns for the Restaurant Voice Assistant backend.

## Overview

The system provides a multi-tenant voice assistant backend where each restaurant has isolated data but shares a single Vapi assistant instance for cost efficiency. Phone numbers are mapped to restaurants for routing.

## System Architecture

```mermaid
graph TB
    Customer[Customer Calls Phone] --> Vapi[Vapi Voice Assistant<br/>Shared Instance]
    Admin[Admin Creates Restaurant] --> API[FastAPI Backend]
    API --> PhoneService[Phone Service]
    API --> VectorSearch[Vector Search Service]
    API --> EmbeddingService[Embedding Service]
    
    Vapi --> Backend[FastAPI Backend<br/>/api/vapi/*]
    Backend --> PhoneMapping[Phone Mapping Service]
    Backend --> VectorSearch
    Backend --> Cache[Cache Layer<br/>TTL: 60s]
    
    VectorSearch --> Supabase[(Supabase PostgreSQL<br/>+ pgvector)]
    EmbeddingService --> OpenAI[OpenAI Embeddings API]
    PhoneService --> Twilio[Twilio API]
    PhoneService --> VapiClient[Vapi API Client]
    
    Supabase --> Restaurants[restaurants table]
    Supabase --> Embeddings[document_embeddings<br/>with vector column]
    Supabase --> PhoneMappingTable[restaurant_phone_mappings]
    Supabase --> Menu[menu_items]
    Supabase --> Hours[operating_hours]
    Supabase --> Zones[delivery_zones]
```

## Multi-Tenant Routing

The system uses phone number mapping to route calls to the correct restaurant:

```mermaid
sequenceDiagram
    participant C as Customer
    participant V as Vapi Assistant
    participant B as Backend API
    participant P as Phone Mapping
    participant D as Database
    
    C->>V: Calls phone number
    V->>B: POST /api/vapi/assistant-request<br/>(phone number in metadata)
    B->>P: get_restaurant_id_from_phone()
    P->>D: Query restaurant_phone_mappings
    D-->>P: restaurant_id
    P-->>B: restaurant_id
    B-->>V: {metadata: {restaurant_id}}
    
    C->>V: "What's on your menu?"
    V->>B: POST /api/vapi/knowledge-base<br/>(with restaurant_id in metadata)
    B->>D: Vector search with restaurant_id filter
    D-->>B: Restaurant-specific results
    B-->>V: Tool result
    V-->>C: Voice response
```

## Voice Call Flow

Complete flow from customer call to voice response:

```mermaid
sequenceDiagram
    participant C as Customer
    participant V as Vapi
    participant A as Assistant Request
    participant KB as Knowledge Base
    participant VS as Vector Search
    participant S as Supabase
    participant O as OpenAI
    
    C->>V: Calls +1234567890
    V->>A: POST /api/vapi/assistant-request<br/>{phoneNumber: "+1234567890"}
    A->>S: Lookup phone → restaurant_id
    S-->>A: restaurant_id: "abc-123"
    A-->>V: {metadata: {restaurant_id: "abc-123"}}
    
    C->>V: "What are your hours?"
    V->>KB: POST /api/vapi/knowledge-base<br/>Tool: get_hours_info<br/>Query: "hours"<br/>Metadata: {restaurant_id: "abc-123"}
    
    KB->>KB: Extract restaurant_id from metadata
    KB->>VS: search_knowledge_base(query, restaurant_id, category="hours")
    VS->>O: Generate embedding for query
    O-->>VS: Query embedding vector
    VS->>S: Vector similarity search<br/>WHERE restaurant_id = "abc-123"<br/>AND category = "hours"
    S-->>VS: Matching documents
    VS-->>KB: Results with content
    KB->>KB: Format response
    KB-->>V: Tool result with hours data
    V->>C: "We're open Monday-Friday 9am-5pm..."
```

## Phone Assignment Flow

How phone numbers are assigned to restaurants:

```mermaid
flowchart TD
    Start[POST /api/restaurants<br/>assign_phone=true] --> Check{force_twilio?}
    
    Check -->|false| FindExisting[Find existing<br/>unassigned phones]
    FindExisting --> HasExisting{Phone found?}
    
    HasExisting -->|yes| AssignExisting[Assign existing phone<br/>Create mapping]
    HasExisting -->|no| CheckTwilio{Twilio<br/>configured?}
    
    Check -->|true| CheckTwilio
    
    CheckTwilio -->|yes| GetCredential[Get/Create Twilio<br/>credential in Vapi]
    GetCredential --> ListTwilio[List existing Twilio<br/>numbers]
    ListTwilio --> HasTwilioNumber{Number<br/>exists?}
    
    HasTwilioNumber -->|yes| UseExisting[Use existing Twilio number]
    HasTwilioNumber -->|no| SearchTwilio[Search available<br/>Twilio numbers]
    
    SearchTwilio --> Purchase[Purchase from Twilio API]
    Purchase --> AddToVapi[Add to Vapi with<br/>Twilio credentials]
    
    UseExisting --> AddToVapi
    AddToVapi --> AssignAssistant[Assign to shared assistant]
    AssignAssistant --> CreateMapping[Create phone mapping<br/>in database]
    
    AssignExisting --> Done[Return phone number]
    CreateMapping --> Done
    
    CheckTwilio -->|no| ReturnNone[Return None<br/>No phone assigned]
```

## Database Schema

Key tables and relationships:

```mermaid
erDiagram
    restaurants ||--o{ menu_items : has
    restaurants ||--o{ modifiers : has
    restaurants ||--o{ operating_hours : has
    restaurants ||--o{ delivery_zones : has
    restaurants ||--o{ document_embeddings : has
    restaurants ||--o{ restaurant_phone_mappings : has
    restaurants ||--o{ call_history : has
    
    restaurants {
        uuid id PK
        string name
        string api_key
        timestamp created_at
    }
    
    restaurant_phone_mappings {
        string phone_number PK
        uuid restaurant_id FK
        timestamp created_at
    }
    
    document_embeddings {
        uuid id PK
        uuid restaurant_id FK
        text content
        vector embedding
        string category
        jsonb metadata
    }
    
    menu_items {
        uuid id PK
        uuid restaurant_id FK
        string name
        text description
        decimal price
    }
    
    operating_hours {
        uuid id PK
        uuid restaurant_id FK
        string day_of_week
        time open_time
        time close_time
        boolean is_closed
    }
```

## Component Responsibilities

### FastAPI Backend (`src/main.py`)

- Main application entry point
- CORS middleware configuration
- Global exception handling
- Route registration

### API Endpoints (`src/api/`)

- **restaurants.py**: Restaurant CRUD, phone assignment
- **vapi.py**: Vapi webhooks (assistant-request, knowledge-base)
- **embeddings.py**: Embedding generation, cache invalidation
- **calls.py**: Call history management
- **health.py**: Health check endpoint

### Services (`src/services/`)

- **phone_service.py**: Phone assignment orchestration
- **phone_mapping.py**: Phone → restaurant_id mapping
- **twilio_service.py**: Twilio API integration
- **vector_search.py**: Vector similarity search
- **embedding_service.py**: OpenAI embeddings generation
- **cache.py**: In-memory caching (TTL: 60s)
- **vapi_response.py**: Vapi response formatting

### Vapi Integration (`vapi/`)

- **client.py**: Vapi API client wrapper
- **manager.py**: Resource manager (tools, assistants)
- **config_loader.py**: YAML configuration loader
- **config/**: Tool and assistant YAML configurations

## Data Flow Patterns

### Query Processing

1. **Extract** restaurant_id from phone number or metadata
2. **Generate** embedding for user query (OpenAI)
3. **Search** vector database with restaurant_id filter (Supabase pgvector)
4. **Cache** results for 60 seconds
5. **Format** response for Vapi tool result

### Phone Assignment

1. **Check** for existing unassigned phones (unless `force_twilio=True`)
2. **Create** Twilio credential in Vapi (if needed)
3. **Purchase** phone from Twilio API (if needed)
4. **Register** phone in Vapi with credentials
5. **Assign** phone to shared assistant
6. **Create** phone mapping in database

### Multi-Tenancy Isolation

- All queries filtered by `restaurant_id`
- Row Level Security (RLS) policies in Supabase
- Service role key used for writes (bypasses RLS)
- Anon key used for reads (respects RLS)

## Caching Strategy

- **Cache Key**: `{restaurant_id}:{category}:{query}`
- **TTL**: 60 seconds (configurable via `CACHE_TTL_SECONDS`)
- **Invalidation**: Manual via `/api/embeddings/cache/invalidate`
- **Storage**: In-memory (TTLCache from cachetools)

## Security

- **Vapi Webhooks**: HMAC verification via `X-Vapi-Secret` header
- **API Endpoints**: Protected by `VAPI_SECRET_KEY`
- **Database**: RLS policies for multi-tenant isolation
- **Service Role**: Only used for admin operations (writes)

## Cost Optimization

- **Single Vapi Assistant**: Shared across all restaurants
- **Phone Reuse**: Assigns existing phones before creating new ones
- **Caching**: Reduces OpenAI embedding API calls
- **Vector Search**: Efficient pgvector indexing

## Scalability Considerations

- **Horizontal Scaling**: Stateless FastAPI app, can run multiple instances
- **Database**: Supabase scales PostgreSQL automatically
- **Caching**: Consider Redis for multi-instance deployments
- **Phone Limits**: Twilio account quotas apply per restaurant

