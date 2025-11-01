# Service APIs Documentation

## Overview

This document maps the **two-tier architecture** of the vocabulary application:

1. **Internal API** - Server-to-Cyoda communication using M2M credentials
2. **External API** - Public REST endpoints for client applications

**Critical Security Principle**: M2M credentials used to access Cyoda **NEVER leave the server**. The external API acts as a secure proxy.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     CLIENT TIER                               │
│  (Web Apps, Mobile Apps, Browser - NO CREDENTIALS)           │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ HTTPS (Public REST API)
                         │ No authentication needed from clients
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   SECURITY BOUNDARY                           │
│                External API Endpoints                         │
│  application/routes/vocabulary_items.py                       │
│  application/routes/share_links.py                            │
│  application/routes/shared_vocabulary.py                      │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         │ Internal method calls
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                  APPLICATION TIER                             │
│                  (Server-Side Only)                           │
│                                                               │
│  ┌────────────────────────────────────────────────┐          │
│  │  Service Layer (common/service/)               │          │
│  │  • EntityServiceImpl                           │          │
│  │  • Business logic & validation                 │          │
│  └───────────────────┬────────────────────────────┘          │
│                      │                                        │
│                      ▼                                        │
│  ┌────────────────────────────────────────────────┐          │
│  │  Repository Layer (common/repository/cyoda/)   │          │
│  │  • CyodaRepository (CRUD operations)           │          │
│  │  • WorkflowRepository                          │          │
│  │  • EdgeMessageRepository                       │          │
│  └───────────────────┬────────────────────────────┘          │
│                      │                                        │
│                      │ Uses M2M credentials (SENSITIVE!)     │
│                      ▼                                        │
│  ┌────────────────────────────────────────────────┐          │
│  │  Authentication (common/auth/)                 │          │
│  │  • CyodaAuthService                            │          │
│  │  • OAuth2 Client Credentials Flow              │          │
│  │  • CYODA_CLIENT_ID (SECRET)                    │          │
│  │  • CYODA_CLIENT_SECRET (SECRET)                │          │
│  └───────────────────┬────────────────────────────┘          │
└────────────────────────┼─────────────────────────────────────┘
                         │
                         │ HTTPS + gRPC (Authenticated)
                         │ Bearer Token from M2M credentials
                         ▼
┌──────────────────────────────────────────────────────────────┐
│                   CYODA PLATFORM                              │
│  • REST API (Entity CRUD, Search, Workflows)                 │
│  • gRPC Service (Event Streaming, Processors)                │
│  • OAuth2 Token Endpoint                                     │
└──────────────────────────────────────────────────────────────┘
```

---

## 1. INTERNAL API - Cyoda Platform Communication

> **🔒 Security Notice**: This tier contains M2M credentials that must **NEVER** be exposed to clients.

### 1.1 Authentication Layer

#### Files
- `common/auth/cyoda_auth.py` - Main authentication service
- `common/auth/async_token_fetcher.py` - Token lifecycle management
- `common/auth/sync_token_fetcher.py` - Synchronous token operations

#### Configuration (Environment Variables)

```bash
# ⚠️ SENSITIVE - Keep server-side only!
CYODA_CLIENT_ID=your-m2m-client-id
CYODA_CLIENT_SECRET=your-m2m-client-secret
CYODA_TOKEN_URL=https://client-xxx.eu.cyoda.net/api/oauth/token
CYODA_HOST=client-xxx.eu.cyoda.net
```

#### OAuth2 Client Credentials Flow

```python
# Automatic token management
1. POST ${CYODA_TOKEN_URL}
   Headers: None
   Body: {
     "grant_type": "client_credentials",
     "client_id": "${CYODA_CLIENT_ID}",
     "client_secret": "${CYODA_CLIENT_SECRET}",
     "scope": "read write"
   }

2. Response: {
     "access_token": "eyJ...",
     "token_type": "Bearer",
     "expires_in": 300
   }

3. Cache token with TTL (expires - 60 seconds)
4. Auto-refresh on expiry or 401 response
```

#### CyodaAuthService API

```python
from services.services import get_auth_service

auth = get_auth_service()

# Get current valid token (auto-refreshes if needed)
token = await auth.get_access_token()
# Returns: "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."

# Force token refresh
new_token = await auth.refresh_token()
```

---

### 1.2 Repository Layer - Cyoda REST API

#### Files
- `common/repository/crud_repository.py` - Repository interface
- `common/repository/cyoda/cyoda_repository.py` - Main entity operations
- `common/repository/cyoda/workflow_repository.py` - Workflow management
- `common/repository/cyoda/edge_message_repository.py` - Messaging
- `common/repository/cyoda/deployment_repository.py` - Model deployment

#### Entity CRUD Operations

##### Create Entity
```python
# Cyoda API: POST /api/entity/JSON/{model}/{version}
# Headers: Authorization: Bearer {token}

await repository.save(
    entity={
        "front": "hello",
        "back": "hola",
        "lesson": "Spanish 101"
    },
    entity_model="VocabularyItem",
    entity_version=1,
    meta={}  # Optional metadata
)

# Returns: Entity with generated UUID
```

**Cyoda Endpoint**: `POST https://${CYODA_HOST}/api/entity/JSON/VocabularyItem/1`

##### Read Entity by ID
```python
# Cyoda API: GET /api/entity/{id}

await repository.find_by_id(
    entity_id="uuid-abc-123-def",
    entity_model="VocabularyItem",
    entity_version=1
)

# Returns: Entity data with metadata
```

**Cyoda Endpoint**: `GET https://${CYODA_HOST}/api/entity/uuid-abc-123-def`

##### List All Entities
```python
# Cyoda API: GET /api/entity/{model}/{version}

await repository.find_all(
    entity_model="VocabularyItem",
    entity_version=1,
    meta={}
)

# Returns: List of entities
```

**Cyoda Endpoint**: `GET https://${CYODA_HOST}/api/entity/VocabularyItem/1`

##### Update Entity
```python
# Cyoda API: PUT /api/entity/JSON/{id}/{transition}

await repository.update(
    entity_id="uuid-abc-123",
    entity={"front": "hello", "back": "hola updated"},
    entity_model="VocabularyItem",
    entity_version=1,
    transition="update",  # Optional workflow transition
    meta={}
)
```

**Cyoda Endpoint**: `PUT https://${CYODA_HOST}/api/entity/JSON/uuid-abc-123/update`

##### Delete Entity
```python
# Cyoda API: DELETE /api/entity/{id}

await repository.delete_by_id(
    entity_id="uuid-abc-123",
    entity_model="VocabularyItem",
    entity_version=1,
    meta={}
)
```

**Cyoda Endpoint**: `DELETE https://${CYODA_HOST}/api/entity/uuid-abc-123`

#### Search Operations

##### Simple Search by Criteria
```python
# Cyoda API: POST /api/search/{model}/{version}

await repository.find_all_by_criteria(
    entity_model="VocabularyItem",
    entity_version=1,
    criteria={
        "lesson": "Spanish 101",
        "state": "active"
    }
)
```

**Cyoda Endpoint**: `POST https://${CYODA_HOST}/api/search/VocabularyItem/1`

**Request Body** (auto-converted to Cyoda format):
```json
{
  "cyoda": {
    "type": "group",
    "operator": "AND",
    "conditions": [
      {
        "type": "simple",
        "jsonPath": "$.lesson",
        "operatorType": "EQUALS",
        "value": "Spanish 101"
      },
      {
        "type": "lifecycle",
        "field": "state",
        "operatorType": "EQUALS",
        "value": "active"
      }
    ]
  }
}
```

##### Advanced Search (Direct Cyoda Format)
```python
await repository.find_all_by_criteria(
    entity_model="VocabularyItem",
    entity_version=1,
    criteria={
        "cyoda": {
            "type": "group",
            "operator": "AND",
            "conditions": [
                {
                    "type": "simple",
                    "jsonPath": "$.lesson",
                    "operatorType": "CONTAINS",
                    "value": "Spanish"
                },
                {
                    "type": "simple",
                    "jsonPath": "$.front",
                    "operatorType": "STARTS_WITH",
                    "value": "h"
                }
            ]
        }
    }
)
```

**Supported Operators**:
- `EQUALS`, `NOT_EQUALS`, `IEQUALS` (case-insensitive)
- `GREATER_THAN`, `LESS_THAN`, `GREATER_THAN_OR_EQUAL`, `LESS_THAN_OR_EQUAL`
- `CONTAINS`, `ICONTAINS`, `STARTS_WITH`, `ENDS_WITH`
- `IN`, `NOT_IN`
- `IS_NULL`, `NOT_NULL`

#### Temporal Operations

##### Get Entity at Point in Time
```python
# Cyoda API: GET /api/entity/{id}/at-time

await repository.find_by_id_at_time(
    entity_id="uuid-abc-123",
    point_in_time="2024-01-15T10:30:00Z",
    entity_model="VocabularyItem",
    entity_version=1
)
```

**Cyoda Endpoint**: `GET https://${CYODA_HOST}/api/entity/uuid-abc-123/at-time?pointInTime=2024-01-15T10:30:00Z`

##### Get Change History
```python
# Cyoda API: GET /api/entity/{id}/changes

await repository.get_entity_changes_metadata(
    entity_id="uuid-abc-123"
)

# Returns: List of all changes with timestamps
```

---

### 1.3 Workflow Repository

#### Files
- `common/repository/cyoda/workflow_repository.py`

#### Export Workflow
```python
# Cyoda API: GET /api/model/{name}/{version}/workflow/export

await workflow_repository.export_entity_workflows(
    entity_name="VocabularyItem",
    model_version="1"
)

# Returns: List of workflow definitions as JSON
```

**Cyoda Endpoint**: `GET https://${CYODA_HOST}/api/model/VocabularyItem/1/workflow/export`

#### Import Workflow
```python
# Cyoda API: POST /api/model/{name}/{version}/workflow/import

await workflow_repository.import_entity_workflows(
    entity_name="VocabularyItem",
    model_version="1",
    workflows=[{
        "name": "vocabulary_workflow",
        "initialState": "draft",
        "states": {...}
    }],
    import_mode="REPLACE"  # or "MERGE"
)
```

**Cyoda Endpoint**: `POST https://${CYODA_HOST}/api/model/VocabularyItem/1/workflow/import`

#### Copy Workflow Between Entities
```python
# Cyoda API: POST /api/model/{source}/workflow/copy

await workflow_repository.copy_workflow(
    source_entity_name="VocabularyItem",
    source_version="1",
    target_entity_name="FlashCard",
    target_version="1",
    workflow_name="vocabulary_workflow"
)
```

---

### 1.4 gRPC Bidirectional Streaming

#### Files
- `common/grpc_client/grpc_client.py`
- `common/proto/cyoda_cloud_api_pb2.py` - Protocol definitions
- `common/proto/cloudevents_pb2.py` - CloudEvents format

#### Connection Lifecycle

```python
# Automatically started in app.py
grpc_client = get_grpc_client()
asyncio.create_task(grpc_client.grpc_stream())

# Connection flow:
1. Establish gRPC stream to Cyoda
2. Send JOIN event with processor tags
3. Receive GREET acknowledgment
4. Listen for CALC_REQ (calculation requests)
5. Process via ProcessorManager
6. Send CALC_RESP (results)
7. Maintain with KEEP_ALIVE
```

#### Event Types

```python
# Sent by Application
JOIN_EVENT_TYPE = "cloud.cyoda.join.v1"
CALC_RESP_EVENT_TYPE = "cloud.cyoda.calc.resp.v1"
KEEP_ALIVE_EVENT_TYPE = "cloud.cyoda.keepalive.v1"
EVENT_ACK_TYPE = "cloud.cyoda.event.ack.v1"

# Received from Cyoda
GREET_EVENT_TYPE = "cloud.cyoda.greet.v1"
CALC_REQ_EVENT_TYPE = "cloud.cyoda.calc.req.v1"
ERROR_EVENT_TYPE = "cloud.cyoda.error.v1"
```

#### Processor Execution

When Cyoda sends a CALC_REQ event:

```python
# Event contains:
# - entity: The entity data
# - processor_name: Which processor to run
# - transition: Optional workflow transition

# Application routes to processor:
from application.processor.vocabulary_processor import process_vocabulary

result = await process_vocabulary(entity)

# Returns result via CALC_RESP event
```

---

### 1.5 Service Layer API

#### Files
- `common/service/entity_service.py` - Interface
- `common/service/service.py` - Implementation

#### EntityServiceImpl Methods

```python
from services.services import get_entity_service

service = get_entity_service()

# Create
response = await service.save(
    entity={"front": "hello", "back": "hola"},
    entity_class="VocabularyItem",
    entity_version="1"
)

# Read by ID (FASTEST)
response = await service.get_by_id(
    entity_id="uuid-abc-123",
    entity_class="VocabularyItem",
    entity_version="1"
)

# Read by business ID (MEDIUM - uses search)
response = await service.get_by_business_id(
    business_id="hello",
    business_id_field="front",
    entity_class="VocabularyItem",
    entity_version="1"
)

# Search (SLOWEST - complex query)
responses = await service.search(
    condition={"lesson": "Spanish 101"},
    entity_class="VocabularyItem",
    entity_version="1"
)

# List all (SLOW - returns everything)
responses = await service.find_all(
    entity_class="VocabularyItem",
    entity_version="1"
)

# Update with optional workflow transition
response = await service.update(
    entity_id="uuid-abc-123",
    entity={"front": "hello", "back": "hola updated"},
    entity_class="VocabularyItem",
    entity_version="1",
    transition="update"  # Optional
)

# Delete
await service.delete_by_id(
    entity_id="uuid-abc-123",
    entity_class="VocabularyItem",
    entity_version="1"
)

# Execute workflow transition only
await service.execute_transition(
    entity_id="uuid-abc-123",
    transition_name="publish",
    entity_class="VocabularyItem",
    entity_version="1"
)

# Get available transitions
transitions = await service.get_transitions(
    entity_id="uuid-abc-123",
    entity_class="VocabularyItem",
    entity_version="1"
)
```

#### Response Format

```python
@dataclass
class EntityResponse:
    data: CyodaEntity  # The entity data (Pydantic model or dict)
    metadata: EntityMetadata  # Entity metadata

@dataclass
class EntityMetadata:
    id: str  # Technical UUID
    state: Optional[str]  # Current workflow state
    creation_date: Optional[datetime]
    last_update_time: Optional[datetime]
    version: Optional[int]
```

---

## 2. EXTERNAL API - Client-Facing REST Endpoints

> **✅ Safe for Public Access**: These endpoints can be consumed by client applications.

### 2.1 VocabularyItem Endpoints

#### Base Path: `/api/vocabulary-items`

#### Create Vocabulary Item

```http
POST /api/vocabulary-items
Content-Type: application/json

{
  "front": "hello",
  "back": "hola",
  "comment": "Basic greeting",
  "lesson": "Spanish 101"
}
```

**Response** (201 Created):
```json
{
  "entity_id": "840d06c8-465c-4772-87a8-8c29cd0ced76",
  "technical_id": "b76e46dc-bb1f-11b2-97af-e6a591cf140b",
  "front": "hello",
  "back": "hola",
  "comment": "Basic greeting",
  "lesson": "Spanish 101",
  "createdAt": "2025-11-01T00:24:48.231054Z",
  "updatedAt": null,
  "state": "initial_state",
  "version": "1.0"
}
```

#### List All Vocabulary Items

```http
GET /api/vocabulary-items
```

**Response** (200 OK):
```json
{
  "entities": [
    {
      "data": {
        "entity_id": "840d06c8-465c-4772-87a8-8c29cd0ced76",
        "front": "hello",
        "back": "hola",
        "comment": "Basic greeting",
        "lesson": "Spanish 101",
        "createdAt": "2025-11-01T00:24:48.231054Z",
        "state": "initial_state"
      },
      "meta": {
        "id": "b76e46dc-bb1f-11b2-97af-e6a591cf140b",
        "state": "completed",
        "creationDate": "2025-11-01T00:00:08.855Z"
      }
    }
  ],
  "total": 12
}
```

#### Get Vocabulary Item by ID

```http
GET /api/vocabulary-items/{id}
```

**Response** (200 OK):
```json
{
  "entity_id": "840d06c8-465c-4772-87a8-8c29cd0ced76",
  "technical_id": "b76e46dc-bb1f-11b2-97af-e6a591cf140b",
  "front": "hello",
  "back": "hola",
  "comment": "Basic greeting",
  "lesson": "Spanish 101",
  "current_state": "completed",
  "createdAt": "2025-11-01T00:24:48.231054Z"
}
```

#### Update Vocabulary Item

```http
PUT /api/vocabulary-items/{id}
Content-Type: application/json

{
  "front": "hello",
  "back": "hola (updated)",
  "comment": "Updated comment",
  "lesson": "Spanish 101"
}
```

**Response** (200 OK): Updated entity

⚠️ **Known Issue**: Currently returns error "Update operation returned no entity ID"

#### Delete Vocabulary Item

```http
DELETE /api/vocabulary-items/{id}
```

**Response** (200 OK):
```json
{
  "success": true,
  "message": "VocabularyItem deleted"
}
```

---

### 2.2 ShareLink Endpoints

#### Base Path: `/api/share-links`

#### Create ShareLink

```http
POST /api/share-links
Content-Type: application/json

{
  "token": "my-vocab-2025",
  "label": "My Vocabulary Collection"
}
```

**Response** (201 Created):
```json
{
  "entity_id": "76471ac0-06f7-4547-a48d-d3b1e4bc8a9c",
  "technical_id": "a9107524-bb24-11b2-b117-760185de7300",
  "token": "my-vocab-2025",
  "label": "My Vocabulary Collection",
  "createdAt": "2025-11-01T00:35:31.626920Z",
  "revokedAt": null,
  "lastAccessedAt": null,
  "visitCount": 0,
  "state": "initial_state"
}
```

#### List All ShareLinks

```http
GET /api/share-links
```

**Response** (200 OK): List of ShareLinks

#### Get ShareLink by ID

```http
GET /api/share-links/{id}
```

**Response** (200 OK): ShareLink details

#### Revoke ShareLink

```http
DELETE /api/share-links/{id}
```

**Response** (200 OK): Revoked ShareLink

⚠️ **Known Issue**: Entity casting error - needs fix

---

### 2.3 Public Shared Vocabulary Endpoint

#### Base Path: `/api/shared`

**🌐 PUBLIC ACCESS** - No authentication required!

#### Get Shared Vocabulary by Token

```http
GET /api/shared/{token}
```

**Example**:
```http
GET /api/shared/finnish-basics-2025
```

**Response** (200 OK):
```json
{
  "success": true,
  "token": "finnish-basics-2025",
  "label": "Finnish Basics - Family & Self Vocabulary",
  "total": 12,
  "items": [
    {
      "entity_id": "840d06c8-465c-4772-87a8-8c29cd0ced76",
      "front": "olen",
      "back": "olla",
      "comment": "(ich) bin [olla] 1. Pers. Sg. von olla (sein)",
      "lesson": "Finnish Basics - Family & Self",
      "createdAt": "2025-11-01T00:24:48.231054Z",
      "state": "initial_state"
    }
    // ... 11 more items
  ],
  "share_info": {
    "created_at": "2025-11-01T00:35:31.62692Z",
    "visit_count": 0,
    "last_accessed": null
  }
}
```

**Error Responses**:

Not Found (404):
```json
{
  "error": "ShareLink not found for token: invalid-token"
}
```

Revoked (403):
```json
{
  "error": "This share link has been revoked and is no longer accessible"
}
```

---

### 2.4 API Documentation

#### OpenAPI/Swagger Docs

When the application is running:

```
http://127.0.0.1:8000/docs
```

Interactive API documentation with:
- All endpoints listed
- Request/response schemas
- Try-it-out functionality
- Authentication requirements

---

## 3. Security Architecture

### 3.1 Credential Flow

```
┌─────────────────────────────────────────────────────┐
│  NEVER EXPOSED TO CLIENTS                           │
│                                                      │
│  Environment Variables (.env):                      │
│  • CYODA_CLIENT_ID=xxx                              │
│  • CYODA_CLIENT_SECRET=yyy  ← SENSITIVE!            │
│  • CYODA_TOKEN_URL=https://...                      │
│  • CYODA_HOST=client-xxx.eu.cyoda.net               │
│                                                      │
│  Loaded by: services/config.py                      │
│  Used by: common/auth/cyoda_auth.py                 │
└─────────────────────────────────────────────────────┘
                         │
                         │ Server-side only
                         ▼
┌─────────────────────────────────────────────────────┐
│  CyodaAuthService                                    │
│  • Fetches OAuth2 token using M2M credentials       │
│  • Caches token (expires - 60 seconds)              │
│  • Auto-refreshes on expiry or 401                  │
└─────────────────────────────────────────────────────┘
                         │
                         │ Provides token
                         ▼
┌─────────────────────────────────────────────────────┐
│  CyodaRepository & GrpcClient                        │
│  • Use token for all Cyoda API calls                │
│  • Authorization: Bearer {token}                    │
└─────────────────────────────────────────────────────┘
                         │
                         │ Authenticated requests
                         ▼
┌─────────────────────────────────────────────────────┐
│  Cyoda Platform                                      │
│  • Validates token                                   │
│  • Processes request                                 │
│  • Returns data                                      │
└─────────────────────────────────────────────────────┘
                         │
                         │ Data returned
                         ▼
┌─────────────────────────────────────────────────────┐
│  REST API Endpoints                                  │
│  • Receive data from service layer                  │
│  • Format for client consumption                    │
│  • Return to client (NO CREDENTIALS)                │
└─────────────────────────────────────────────────────┘
                         │
                         │ Safe data only
                         ▼
┌─────────────────────────────────────────────────────┐
│  CLIENT APPLICATION                                  │
│  • Receives vocabulary data                         │
│  • Never sees M2M credentials                       │
│  • No need for Cyoda access                         │
└─────────────────────────────────────────────────────┘
```

### 3.2 What to NEVER Expose

**🔒 Server-Side Only**:
1. M2M credentials (`CYODA_CLIENT_ID`, `CYODA_CLIENT_SECRET`)
2. OAuth2 access tokens
3. Direct Cyoda API endpoints
4. Repository implementation details
5. Service configuration
6. gRPC connection details

### 3.3 What is Safe to Expose

**✅ Client-Safe**:
1. REST API endpoints (`/api/vocabulary-items`, etc.)
2. Entity data (vocabulary items, ShareLinks)
3. Business operations (CRUD via REST)
4. Workflow state names
5. Search results
6. Public shared vocabulary endpoint

---

## 4. Request/Response Flow Example

### Complete Flow: Create Vocabulary Item

```
1. CLIENT sends HTTP POST
   ↓
   POST http://app.example.com/api/vocabulary-items
   Content-Type: application/json
   Body: {"front": "hello", "back": "hola"}

2. APPLICATION receives request
   ↓
   File: application/routes/vocabulary_items.py
   Function: create_vocabulary_item(data: VocabularyItem)
   
3. VALIDATES with Pydantic
   ↓
   Checks: front and back are non-empty strings
   
4. CALLS service layer
   ↓
   service = get_entity_service()
   response = await service.save(
       entity=data.model_dump(by_alias=True),
       entity_class="VocabularyItem",
       entity_version="1"
   )
   
5. SERVICE calls repository
   ↓
   File: common/service/service.py
   → repository.save(entity, "VocabularyItem", 1)
   
6. REPOSITORY gets auth token
   ↓
   File: common/repository/cyoda/cyoda_repository.py
   token = await self._cyoda_auth_service.get_access_token()
   
7. AUTH SERVICE fetches/caches token
   ↓
   File: common/auth/async_token_fetcher.py
   If cached and valid: return cached token
   Else: POST to CYODA_TOKEN_URL with M2M credentials
   
8. REPOSITORY calls Cyoda API
   ↓
   POST https://client-xxx.eu.cyoda.net/api/entity/JSON/VocabularyItem/1
   Headers: {
       "Authorization": "Bearer eyJ...",
       "Content-Type": "application/json"
   }
   Body: {"front": "hello", "back": "hola", ...}
   
9. CYODA processes request
   ↓
   • Validates token
   • Creates entity with UUID
   • Triggers workflow (initial_state)
   • Stores in database
   • Returns entity data
   
10. REPOSITORY receives response
    ↓
    Returns EntityResponse with data and metadata
    
11. SERVICE returns to route
    ↓
    EntityResponse → dict conversion
    
12. ROUTE returns to client
    ↓
    HTTP 201 Created
    Body: {
        "entity_id": "uuid-abc-123",
        "front": "hello",
        "back": "hola",
        "createdAt": "2025-11-01...",
        ...
    }
    
13. CLIENT receives response
    ↓
    SUCCESS - No knowledge of M2M credentials or Cyoda API
```

---

## 5. Performance Considerations

### Internal API (Cyoda Communication)

**Token Caching**:
- Tokens cached for (expires_in - 60) seconds
- Reduces auth overhead to ~1 request per 4 minutes
- Automatic refresh prevents 401 errors

**Repository Operations**:
- **Fastest**: `find_by_id(uuid)` - Direct UUID lookup
- **Medium**: `find_by_business_id()` - Uses search internally
- **Slow**: `find_all()` - Returns all entities
- **Slowest**: `find_all_by_criteria()` - Complex queries

**Recommendations**:
1. Prefer UUID lookups when possible
2. Cache frequently accessed entities
3. Use specific criteria to limit search results
4. Paginate large result sets

### External API

**Response Times**:
- Simple CRUD: 200-500ms
- Search operations: 500-2000ms
- Shared vocabulary: 300-800ms

**Bottlenecks**:
1. Network latency to Cyoda (external API calls)
2. Token refresh (occasional 500ms delay)
3. Large result sets (no pagination yet)

---

## 6. File Reference

### Internal API Implementation

| File | Purpose |
|------|---------|
| `services/config.py` | M2M credential configuration |
| `services/services.py` | Dependency injection container |
| `common/auth/cyoda_auth.py` | OAuth2 authentication |
| `common/auth/async_token_fetcher.py` | Token lifecycle |
| `common/repository/crud_repository.py` | Repository interface |
| `common/repository/cyoda/cyoda_repository.py` | Main Cyoda operations |
| `common/repository/cyoda/workflow_repository.py` | Workflow management |
| `common/repository/cyoda/edge_message_repository.py` | Messaging |
| `common/service/entity_service.py` | Service interface |
| `common/service/service.py` | Service implementation |
| `common/grpc_client/grpc_client.py` | gRPC streaming |
| `common/utils/utils.py` | HTTP request helpers |

### External API Implementation

| File | Purpose |
|------|---------|
| `application/app.py` | Quart application setup |
| `application/routes/vocabulary_items.py` | Vocabulary endpoints |
| `application/routes/share_links.py` | ShareLink endpoints |
| `application/routes/shared_vocabulary.py` | Public sharing endpoint |
| `application/entity/vocabulary_item/version_1/vocabulary_item.py` | VocabularyItem model |
| `application/entity/share_link/version_1/share_link.py` | ShareLink model |

---

## 7. Summary Tables

### Internal API - Cyoda Operations

| Operation | Cyoda Endpoint | Auth Required | Purpose |
|-----------|---------------|---------------|---------|
| Create Entity | `POST /api/entity/JSON/{model}/{version}` | Yes (Bearer) | Create new entity |
| Read Entity | `GET /api/entity/{id}` | Yes | Get entity by UUID |
| List Entities | `GET /api/entity/{model}/{version}` | Yes | Get all entities |
| Update Entity | `PUT /api/entity/JSON/{id}/{transition}` | Yes | Update entity |
| Delete Entity | `DELETE /api/entity/{id}` | Yes | Delete entity |
| Search | `POST /api/search/{model}/{version}` | Yes | Complex queries |
| Export Workflow | `GET /api/model/{name}/{version}/workflow/export` | Yes | Get workflow JSON |
| Import Workflow | `POST /api/model/{name}/{version}/workflow/import` | Yes | Deploy workflow |
| Get Token | `POST /api/oauth/token` | M2M Credentials | OAuth2 auth |

### External API - Client Endpoints

| Endpoint | Method | Auth Required | Purpose |
|----------|--------|---------------|---------|
| `/api/vocabulary-items` | POST | No | Create item |
| `/api/vocabulary-items` | GET | No | List all items |
| `/api/vocabulary-items/{id}` | GET | No | Get item |
| `/api/vocabulary-items/{id}` | PUT | No | Update item |
| `/api/vocabulary-items/{id}` | DELETE | No | Delete item |
| `/api/share-links` | POST | No | Create ShareLink |
| `/api/share-links` | GET | No | List ShareLinks |
| `/api/share-links/{id}` | GET | No | Get ShareLink |
| `/api/share-links/{id}` | DELETE | No | Revoke link |
| `/api/shared/{token}` | GET | **No (Public!)** | Get shared vocab |

---

## 8. Deployment Notes

### Environment Setup

```bash
# Required environment variables
export CYODA_CLIENT_ID="your-m2m-client-id"
export CYODA_CLIENT_SECRET="your-m2m-secret"  # KEEP SECRET!
export CYODA_HOST="client-xxx.eu.cyoda.net"
export CYODA_TOKEN_URL="https://client-xxx.eu.cyoda.net/api/oauth/token"

# Optional
export APP_HOST="0.0.0.0"
export APP_PORT="8000"
export APP_DEBUG="false"
```

### Security Checklist

- [x] M2M credentials in environment variables (not code)
- [x] Credentials never logged or exposed in responses
- [x] Token caching to reduce auth overhead
- [x] HTTPS in production
- [ ] Rate limiting on public endpoints
- [ ] CORS configuration
- [ ] User authentication (optional - add if needed)
- [ ] Input validation and sanitization

---

## Conclusion

This architecture provides a **secure separation** between:

1. **Internal API** - Server-to-Cyoda communication using M2M credentials that never leave the server
2. **External API** - Public REST endpoints that clients can safely consume

The application acts as a **secure proxy**, leveraging M2M credentials internally while exposing safe, high-level operations to clients.
