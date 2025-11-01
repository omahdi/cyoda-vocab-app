# UI Implementation Plan - Vocabulary App

## Overview

This document outlines the plan for adding a simple web UI to the vocabulary application using **FastHTML + HTMX**, integrated into the existing Quart app.

---

## Recommended Approach: FastHTML + HTMX (Integrated)

### Why This Approach?

✅ **Python-native** - Works seamlessly with existing Quart app  
✅ **Simple** - No build tooling, no separate dev server  
✅ **Same port (8000)** - No CORS/proxy complications  
✅ **Fast to implement** - 2-5 hours total effort  
✅ **HTMX** - Modern interactive UX without heavy JavaScript  
✅ **Component-based** - FastHTML provides Pythonic HTML components  

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│  Browser (http://localhost:8000)                        │
└────────────────┬────────────────────────────────────────┘
                 │
                 ├─ /ui (Admin Interface - HTML Pages)
                 │   └─ FastHTML + HTMX fragments
                 │
                 ├─ /s/{token} (Public Viewer - HTML)
                 │   └─ Server-rendered read-only page
                 │
                 └─ /api/* (JSON REST API)
                     └─ Existing endpoints (unchanged)
                     
┌─────────────────────────────────────────────────────────┐
│  Quart App (Port 8000)                                  │
│                                                          │
│  ┌────────────────┐  ┌──────────────────┐              │
│  │ UI Blueprint   │  │ API Blueprints   │              │
│  │ /ui/*          │  │ /api/*           │              │
│  │ /s/{token}     │  │                  │              │
│  └────────┬───────┘  └──────────────────┘              │
│           │                                             │
│           └──── httpx ────> /api/* (internal calls)    │
│                                                          │
│  Both use same EntityService (no duplication)           │
└─────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Preparation (30 min)

#### 1.1 Install Dependencies

```bash
pip install fasthtml httpx
```

Update `pyproject.toml`:
```toml
dependencies = [
    # ... existing deps ...
    "fasthtml>=2.12.0",
    "httpx>=0.28.1",  # Already included
]
```

#### 1.2 Create UI Directory Structure

```bash
mkdir -p application/ui
touch application/ui/__init__.py
touch application/ui/ui.py
touch application/ui/components.py
```

#### 1.3 Fix Minor API Issues (Optional but Recommended)

**File**: `application/app.py`

Change:
```python
response.headers["Access-Control-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
```

To:
```python
response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
```

**File**: `application/routes/vocabulary_items.py`

Ensure responses include `id` field:
```python
# In create_vocabulary_item
return {
    **_to_entity_dict(response.data),
    "id": response.metadata.id  # Add this
}, 201

# In get_vocabulary_item
return {
    **_to_entity_dict(response.data),
    "id": entity_id  # Add this
}, 200

# In list_vocabulary_items (already returns full structure)
entity_list = [
    {**_to_entity_dict(r.data), "id": r.metadata.id}
    for r in entities
]
```

---

### Phase 2: UI Blueprint Implementation (2-3 hours)

#### 2.1 Create UI Components (`application/ui/components.py`)

```python
from fasthtml.common import *

def base_layout(title: str, *content):
    """Base HTML layout with HTMX and Pico CSS"""
    return Html(
        Head(
            Title(title),
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            # Pico CSS for quick styling
            Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            # HTMX for interactivity
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            Nav(
                Ul(
                    Li(Strong("Vocabulary App"))
                ),
                Ul(
                    Li(A("Admin", href="/ui")),
                    Li(A("API Docs", href="/docs"))
                )
            ),
            Main(
                *content,
                cls="container"
            )
        )
    )

def vocabulary_form():
    """Form for creating vocabulary items"""
    return Article(
        H2("Create Vocabulary Item"),
        Form(
            Input(
                type="text",
                name="front",
                placeholder="Front (e.g., hello)",
                required=True
            ),
            Input(
                type="text",
                name="back",
                placeholder="Back (e.g., hola)",
                required=True
            ),
            Input(
                type="text",
                name="comment",
                placeholder="Comment (optional)"
            ),
            Input(
                type="text",
                name="lesson",
                placeholder="Lesson (optional)"
            ),
            Button("Create", type="submit"),
            hx_post="/ui/items",
            hx_target="#items-tbody",
            hx_swap="afterbegin"  # Add new item to top of list
        )
    )

def vocabulary_table_shell():
    """Empty table structure that HTMX will populate"""
    return Article(
        H2("Vocabulary Items"),
        Table(
            Thead(
                Tr(
                    Th("Front"),
                    Th("Back"),
                    Th("Comment"),
                    Th("Lesson"),
                    Th("Actions")
                )
            ),
            Tbody(
                id="items-tbody",
                hx_get="/ui/items",
                hx_trigger="load",
                hx_swap="innerHTML"
            )
        )
    )

def vocabulary_row(item: dict):
    """Single vocabulary item row"""
    return Tr(
        Td(item.get("front", "")),
        Td(item.get("back", "")),
        Td(item.get("comment", "—")),
        Td(item.get("lesson", "—")),
        Td(
            Button(
                "Delete",
                hx_delete=f"/ui/items/{item.get('id')}",
                hx_target="closest tr",
                hx_swap="outerHTML swap:1s",
                hx_confirm="Delete this item?"
            )
        )
    )

def share_form():
    """Form for creating share links"""
    return Article(
        H2("Create Share Link"),
        Form(
            Input(
                type="text",
                name="token",
                placeholder="Token (e.g., my-vocab-2025)",
                required=True
            ),
            Input(
                type="text",
                name="label",
                placeholder="Label (e.g., Spanish Vocabulary)"
            ),
            Button("Create Share Link", type="submit"),
            hx_post="/ui/share",
            hx_target="#share-result",
            hx_swap="innerHTML"
        ),
        Div(id="share-result")
    )

def share_result(token: str, full_url: str, label: str):
    """Display created share link"""
    return Article(
        H3("✅ Share Link Created!"),
        P(Strong("Token: "), Code(token)),
        P(Strong("Label: "), label),
        P(Strong("Public URL: ")),
        Input(
            type="text",
            value=full_url,
            readonly=True,
            onclick="this.select()"
        ),
        A("Open Public Viewer", href=f"/s/{token}", target="_blank")
    )

def public_viewer_page(token: str, data: dict):
    """Public vocabulary viewer page"""
    items = data.get("items", [])
    
    return base_layout(
        f"Shared Vocabulary - {data.get('label', token)}",
        Article(
            H1(data.get("label", "Shared Vocabulary")),
            P(f"Total items: {data.get('total', 0)}"),
            Ul(
                *[
                    Li(
                        Strong(item.get("front", "")),
                        " → ",
                        item.get("back", ""),
                        (P(Em(item.get("comment")), style="margin-left: 2rem; color: #666;") 
                         if item.get("comment") else None)
                    )
                    for item in items
                ]
            ),
            Footer(
                P(
                    Small(
                        f"Shared via token: {token} | ",
                        f"Visit count: {data.get('share_info', {}).get('visit_count', 0)}"
                    )
                )
            )
        )
    )
```

#### 2.2 Create UI Routes (`application/ui/ui.py`)

```python
import httpx
from quart import Blueprint, request, Response
from application.ui.components import *

ui_bp = Blueprint("ui", __name__, url_prefix="")

# Internal API base URL
API_BASE = "http://127.0.0.1:8000/api"

async def call_api(method: str, endpoint: str, **kwargs) -> dict:
    """Helper to call internal API"""
    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{API_BASE}{endpoint}", **kwargs)
        response.raise_for_status()
        return response.json()


@ui_bp.route("/ui", methods=["GET"])
async def admin_page():
    """Main admin interface"""
    page = base_layout(
        "Vocabulary Admin",
        H1("Vocabulary Administration"),
        vocabulary_form(),
        vocabulary_table_shell(),
        share_form()
    )
    return str(page)


@ui_bp.route("/ui/items", methods=["GET"])
async def list_items_html():
    """Return HTML fragment with vocabulary items"""
    try:
        data = await call_api("GET", "/vocabulary-items")
        
        # Extract items from response structure
        entities = data.get("entities", [])
        
        # Generate rows
        rows = []
        for entity in entities:
            # Handle nested structure: entities[].data
            if isinstance(entity, dict) and "data" in entity:
                item_data = entity["data"]
                item_data["id"] = entity.get("meta", {}).get("id")
            else:
                item_data = entity
            
            rows.append(vocabulary_row(item_data))
        
        # Return rows as HTML string
        return "".join(str(row) for row in rows)
    
    except Exception as e:
        return f"<tr><td colspan='5'>Error loading items: {str(e)}</td></tr>"


@ui_bp.route("/ui/items", methods=["POST"])
async def create_item_html():
    """Create vocabulary item and return new row HTML"""
    try:
        form = await request.form
        
        # Create item via API
        result = await call_api(
            "POST",
            "/vocabulary-items",
            json={
                "front": form.get("front"),
                "back": form.get("back"),
                "comment": form.get("comment") or None,
                "lesson": form.get("lesson") or None
            }
        )
        
        # Return new row
        return str(vocabulary_row(result))
    
    except Exception as e:
        return f"<tr><td colspan='5'>Error creating item: {str(e)}</td></tr>"


@ui_bp.route("/ui/items/<item_id>", methods=["DELETE"])
async def delete_item_html(item_id: str):
    """Delete vocabulary item and return empty (HTMX will remove the row)"""
    try:
        await call_api("DELETE", f"/vocabulary-items/{item_id}")
        return ""  # Empty response = HTMX removes the element
    
    except Exception as e:
        return f"<tr><td colspan='5'>Error deleting item: {str(e)}</td></tr>"


@ui_bp.route("/ui/share", methods=["POST"])
async def create_share_html():
    """Create share link and return result HTML"""
    try:
        form = await request.form
        
        # Create share link via API
        result = await call_api(
            "POST",
            "/share-links",
            json={
                "token": form.get("token"),
                "label": form.get("label") or f"Shared Vocabulary - {form.get('token')}"
            }
        )
        
        # Get the token from result
        token = result.get("token")
        full_url = f"http://localhost:8000/s/{token}"
        
        return str(share_result(token, full_url, result.get("label", "")))
    
    except Exception as e:
        return f"<div>Error creating share link: {str(e)}</div>"


@ui_bp.route("/s/<token>", methods=["GET"])
async def public_viewer(token: str):
    """Public viewer for shared vocabulary"""
    try:
        # Fetch shared vocabulary
        data = await call_api("GET", f"/shared/{token}")
        
        # Render page
        page = public_viewer_page(token, data)
        return str(page)
    
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            return str(base_layout(
                "Share Not Found",
                Article(
                    H1("Share Link Not Found"),
                    P(f"No shared vocabulary found for token: {token}"),
                    A("Go to Admin", href="/ui")
                )
            )), 404
        raise
    except Exception as e:
        return str(base_layout(
            "Error",
            Article(
                H1("Error Loading Shared Vocabulary"),
                P(str(e)),
                A("Go to Admin", href="/ui")
            )
        )), 500
```

#### 2.3 Register UI Blueprint (`application/app.py`)

```python
from application.routes.shared_vocabulary import shared_vocabulary_bp
from application.ui.ui import ui_bp  # Add this import

# ... existing code ...

# Register blueprints
app.register_blueprint(vocabulary_items_bp)
app.register_blueprint(share_links_bp)
app.register_blueprint(shared_vocabulary_bp)
app.register_blueprint(ui_bp)  # Add this line
```

---

### Phase 3: Testing (30 min)

#### Test Checklist

1. **Admin Interface** (`http://localhost:8000/ui`)
   - [ ] Page loads with form and empty table
   - [ ] Create vocabulary item via form
   - [ ] Table auto-updates with new item
   - [ ] Delete button removes item
   - [ ] Create share link generates URL

2. **Public Viewer** (`http://localhost:8000/s/{token}`)
   - [ ] Page loads with vocabulary list
   - [ ] Shows all items for the token
   - [ ] Read-only (no edit/delete buttons)
   - [ ] 404 for invalid tokens

3. **API Still Works** (`http://localhost:8000/api/vocabulary-items`)
   - [ ] JSON endpoints unchanged
   - [ ] Can still use curl/Postman

---

## Alternative Approaches Considered

### Option 2: Quart + Jinja2 + HTMX

**Pros**:
- Standard templating with excellent documentation
- Trivial Quart integration
- More familiar to most developers

**Cons**:
- More HTML string manipulation vs FastHTML's Python components
- Less component-oriented

**When to use**: If FastHTML feels too novel or you want Jinja's ecosystem

---

### Option 3: Alpine.js + Tailwind (Static HTML + Fetch)

**Pros**:
- Minimal JavaScript
- No build tooling if using CDN
- Very lightweight and fast
- Great for simple interactivity

**Cons**:
- Client-side JSON → DOM mapping
- Slightly more client-side code than HTMX
- Need to handle CORS if served separately

**Example**:
```html
<div x-data="{ items: [] }" x-init="fetch('/api/vocabulary-items').then(r => r.json()).then(d => items = d.entities)">
  <template x-for="item in items">
    <div x-text="item.data.front + ' → ' + item.data.back"></div>
  </template>
</div>
```

**When to use**: If you prefer declarative client-side JavaScript

---

### Option 4: Svelte (Full SPA)

**Pros**:
- Rich interactivity and smooth UX
- Component-based with great DX
- Scalable frontend architecture
- TypeScript support

**Cons**:
- Requires Node.js, Vite, build toolchain
- Separate dev server (port 5173)
- More complex setup
- Overkill for simple CRUD

**When to use**: Complex UI requirements, team separation, or multi-page app with routing

---

## Comparison Table

| Approach | Setup Time | Complexity | Build Tools | Port | Best For |
|----------|-----------|------------|-------------|------|----------|
| **FastHTML + HTMX** | 2-3h | Low | None | 8000 | Simple CRUD, Python devs |
| Jinja2 + HTMX | 2-3h | Low | None | 8000 | Template-familiar teams |
| Alpine.js | 2-4h | Low-Med | None (CDN) | 8000 | Client-side preference |
| Svelte SPA | 4-8h | Medium | Vite, Node | 5173+8000 | Complex UI, FE team |

---

## Recommended: FastHTML + HTMX

### Why?

1. **Fastest path** to working UI
2. **Python-native** - matches your stack
3. **No build complexity** - just add files and restart
4. **Same port** - no CORS/proxy issues
5. **Modern UX** - HTMX provides SPA-like experience
6. **Low maintenance** - fewer moving parts

### When to Reconsider?

- You need complex client-side state management
- Team prefers React/Vue/Svelte ecosystem
- Offline-first or PWA requirements
- Heavy client-side routing needs

---

## Implementation Timeline

### Quick Win (2 hours)
- [ ] Install FastHTML + httpx
- [ ] Create basic components
- [ ] Create UI blueprint with admin page
- [ ] Wire up to app.py
- [ ] Test create/list/delete

### Full Implementation (4-5 hours)
- [ ] Above + styling with Pico CSS
- [ ] Share link creation UI
- [ ] Public viewer page
- [ ] Error handling
- [ ] Responsive design tweaks

### Polish (optional, +2 hours)
- [ ] Inline edit functionality
- [ ] Search/filter
- [ ] Pagination
- [ ] Better animations
- [ ] Export functionality

---

## File Structure After Implementation

```
application/
├── ui/
│   ├── __init__.py
│   ├── ui.py          # UI routes and HTMX endpoints
│   └── components.py  # FastHTML components
├── routes/
│   ├── vocabulary_items.py  # JSON API (unchanged)
│   ├── share_links.py       # JSON API (unchanged)
│   └── shared_vocabulary.py # JSON API (unchanged)
└── app.py             # Register UI blueprint
```

---

## Next Steps

1. **Install dependencies**: `pip install fasthtml httpx`
2. **Create UI directory**: `mkdir -p application/ui`
3. **Copy component code** from Phase 2.1
4. **Copy route code** from Phase 2.2
5. **Register blueprint** in app.py
6. **Restart app**: `hypercorn application.app:app --reload --bind 0.0.0.0:8000`
7. **Open browser**: `http://localhost:8000/ui`

---

## Resources

- **FastHTML Docs**: https://docs.fastht.ml
- **HTMX Docs**: https://htmx.org/docs/
- **Pico CSS**: https://picocss.com/docs
- **FastHTML Examples**: https://github.com/AnswerDotAI/fasthtml/tree/main/examples

---

## Success Criteria

✅ Admin interface loads at `/ui`  
✅ Can create vocabulary items via form  
✅ Items appear in table without page reload  
✅ Can delete items with confirmation  
✅ Can create share links  
✅ Public viewer works at `/s/{token}`  
✅ No impact on existing JSON API  
✅ All on same port (8000)  
