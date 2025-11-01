# Shared Vocabulary Endpoint Guide

## Overview

The shared vocabulary endpoint allows **public access** to vocabulary items via a ShareLink token. This enables sharing vocabulary sets without requiring authentication.

## Endpoint

```
GET /api/shared/{token}
```

### Parameters

- **token** (path parameter, required): The ShareLink token (e.g., "finnish-basics-2025")

### Authentication

**None required** - This is a public endpoint for sharing vocabulary.

## Usage

### Basic Request

```bash
curl http://127.0.0.1:8000/api/shared/finnish-basics-2025
```

### Response Format

#### Success (200 OK)

```json
{
  "success": true,
  "token": "finnish-basics-2025",
  "label": "Finnish Basics - Family & Self Vocabulary",
  "total": 12,
  "items": [
    {
      "front": "olen",
      "back": "olla",
      "comment": "(ich) bin [olla] 1. Pers. Sg. von olla (sein)",
      "lesson": "Finnish Basics - Family & Self",
      "createdAt": "2025-11-01T00:24:48.231054Z",
      "entity_id": "840d06c8-465c-4772-87a8-8c29cd0ced76",
      "state": "initial_state"
    },
    // ... more items
  ],
  "share_info": {
    "created_at": "2025-11-01T00:35:31.62692Z",
    "visit_count": 0,
    "last_accessed": null
  }
}
```

#### Not Found (404)

```json
{
  "error": "ShareLink not found for token: invalid-token"
}
```

#### Revoked (403)

```json
{
  "error": "This share link has been revoked and is no longer accessible"
}
```

## Use Cases

### 1. Web Application Integration

```javascript
// Fetch shared vocabulary
async function loadSharedVocabulary(token) {
  const response = await fetch(`/api/shared/${token}`);
  const data = await response.json();
  
  if (data.success) {
    return data.items;
  } else {
    throw new Error(data.error);
  }
}

// Usage
const items = await loadSharedVocabulary('finnish-basics-2025');
console.log(`Loaded ${items.length} vocabulary items`);
```

### 2. Mobile App Integration

```swift
// Swift example
func fetchSharedVocabulary(token: String) async throws -> [VocabularyItem] {
    let url = URL(string: "https://api.example.com/api/shared/\(token)")!
    let (data, _) = try await URLSession.shared.data(from: url)
    let response = try JSONDecoder().decode(SharedVocabularyResponse.self, from: data)
    return response.items
}
```

### 3. Command Line Access

```bash
# Get all items
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | jq '.items'

# Get just front/back pairs
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | \
  jq '.items[] | "\(.front) → \(.back)"'

# Count items
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | jq '.total'

# Get share info
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | jq '.share_info'
```

### 4. Flashcard Application

```python
import requests

def create_flashcards(token):
    """Fetch and display flashcards from shared link"""
    response = requests.get(f"http://127.0.0.1:8000/api/shared/{token}")
    data = response.json()
    
    if not data.get('success'):
        print(f"Error: {data.get('error')}")
        return
    
    print(f"📚 {data['label']}")
    print(f"Total cards: {data['total']}\n")
    
    for item in data['items']:
        print(f"Front: {item['front']}")
        print(f"Back:  {item['back']}")
        if item.get('comment'):
            print(f"Note:  {item['comment']}")
        print("-" * 40)

# Use it
create_flashcards('finnish-basics-2025')
```

## Features

### Current Features

✅ **Public access** - No authentication required  
✅ **Token-based** - Access via unique token  
✅ **Revocation support** - Returns 403 if link is revoked  
✅ **Metadata included** - Returns share info with creation date and stats  
✅ **Full vocabulary data** - All fields included (front, back, comment, lesson)  

### Planned Enhancements

🔄 **Access tracking** - Increment visit count on each access  
🔄 **Lesson filtering** - Only return items from specific lesson  
🔄 **Pagination** - Support for large vocabulary sets  
🔄 **Rate limiting** - Prevent abuse  
🔄 **Analytics** - Track geographic data, devices, etc.  

## Response Fields

### Root Object

| Field | Type | Description |
|-------|------|-------------|
| `success` | boolean | Whether the request was successful |
| `token` | string | The ShareLink token used |
| `label` | string | Human-readable label for the share |
| `total` | integer | Total number of vocabulary items |
| `items` | array | Array of vocabulary items |
| `share_info` | object | ShareLink metadata |

### Vocabulary Item Object

| Field | Type | Description |
|-------|------|-------------|
| `front` | string | Front side of flashcard |
| `back` | string | Back side of flashcard |
| `comment` | string? | Optional comment/notes |
| `lesson` | string? | Optional lesson name |
| `entity_id` | string | Unique entity ID |
| `createdAt` | string | ISO timestamp |
| `state` | string | Workflow state |

### Share Info Object

| Field | Type | Description |
|-------|------|-------------|
| `created_at` | string | When ShareLink was created |
| `visit_count` | integer | Number of times accessed |
| `last_accessed` | string? | Last access timestamp |

## Testing

### Test Script

Run the included test script:

```bash
python test_shared_endpoint.py
```

### Manual Tests

```bash
# Test valid token
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | jq '.success'
# Expected: true

# Test invalid token
curl -s http://127.0.0.1:8000/api/shared/invalid-xyz | jq '.error'
# Expected: "ShareLink not found for token: invalid-xyz"

# Test with pretty output
curl -s http://127.0.0.1:8000/api/shared/finnish-basics-2025 | jq '.'
```

## Security Considerations

### Current Implementation

- ✅ Token-based access (not easily guessable)
- ✅ Revocation support
- ⚠️ No rate limiting (could be abused)
- ⚠️ No expiration dates
- ⚠️ No password protection
- ⚠️ Returns ALL vocabulary items (should filter by lesson/collection)

### Recommended Security Enhancements

1. **Rate Limiting**: Limit requests per IP/token
2. **Expiration**: Add expiry dates to ShareLinks
3. **Password Protection**: Optional password for sensitive shares
4. **IP Whitelisting**: Restrict access to specific IPs
5. **Access Logs**: Track who accesses what and when
6. **CORS Configuration**: Restrict which domains can embed
7. **Lesson Filtering**: Only return vocabulary associated with the ShareLink

## Integration Examples

### React Component

```jsx
import { useState, useEffect } from 'react';

function SharedVocabulary({ token }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetch(`/api/shared/${token}`)
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setData(data);
        } else {
          setError(data.error);
        }
      })
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [token]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h1>{data.label}</h1>
      <p>{data.total} items</p>
      
      <div className="flashcards">
        {data.items.map(item => (
          <div key={item.entity_id} className="flashcard">
            <div className="front">{item.front}</div>
            <div className="back">{item.back}</div>
            {item.comment && <div className="comment">{item.comment}</div>}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### Embeddable Widget

```html
<!-- Embed in any webpage -->
<iframe 
  src="https://your-app.com/embed/finnish-basics-2025"
  width="100%" 
  height="600"
  frameborder="0">
</iframe>

<script>
// Or load dynamically
(function() {
  const token = 'finnish-basics-2025';
  fetch(`https://your-app.com/api/shared/${token}`)
    .then(r => r.json())
    .then(data => {
      // Render flashcards in current page
      renderFlashcards(data.items);
    });
})();
</script>
```

## Error Handling

```javascript
async function fetchShared(token) {
  try {
    const response = await fetch(`/api/shared/${token}`);
    const data = await response.json();
    
    if (response.status === 404) {
      console.error('ShareLink not found');
      return null;
    }
    
    if (response.status === 403) {
      console.error('ShareLink has been revoked');
      return null;
    }
    
    if (!data.success) {
      console.error('Failed to fetch vocabulary:', data.error);
      return null;
    }
    
    return data;
  } catch (error) {
    console.error('Network error:', error);
    return null;
  }
}
```

## Next Steps

1. **Restart the application** to load the new endpoint
2. **Test with**: `python test_shared_endpoint.py`
3. **Verify**: `curl http://127.0.0.1:8000/api/shared/finnish-basics-2025`
4. **Build a frontend** that consumes this endpoint
5. **Add filtering** to return only relevant vocabulary items
6. **Implement access tracking** to update visit count

## Summary

The `/api/shared/{token}` endpoint enables:

✅ **Public vocabulary sharing** without authentication  
✅ **Token-based access control**  
✅ **Full vocabulary data** with all metadata  
✅ **Share link management** (creation, revocation)  
✅ **Easy integration** with web/mobile apps  

This completes the ShareLink functionality - you can now create ShareLinks AND retrieve the vocabulary data they reference!
