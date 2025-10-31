# Product Requirements Document — Vocabulary List Manager (Prototype)

## 1) Summary & Goals
**Goal:** A minimal web app that lets a learner import vocabulary (CSV), review & edit it in a table (filterable by lesson), export it back to CSV, and share a read‑only public view via revocable tokenized links.

**Primary KPI (prototype):**
- Import-to-first-successful-review under 2 minutes.
- ≥95% import success rate (well-formed CSV) in manual tests.
- Read-only link opens successfully on first try (≤1 error in 50).

## 2) Scope
**In scope (prototype):**
- Single user “workspace” (no multi-tenant account system yet).
- CSV import with upsert-by-id semantics.
- Editable tabular view (columns: front, back, comment, lesson).
- Filter by lesson (single or multi-select).
- CSV export (round‑trippable, includes id column).
- Generate multiple public read-only links, list & revoke them.

**Out of scope (for now):**
- Spaced repetition algorithms, progress tracking, mobile apps.
- User authentication & roles, multi-user editing.
- Media (audio/image) on cards.
- Per‑link scoping/filters and link expiration.
- API/SDK for third‑party integrations.

## 3) Personas
- **Learner (Owner):** Maintains the vocabulary list, imports/edits data, generates share links.
- **Viewer (Public):** Opens a share link to browse the list read-only, optionally filter by lesson.

## 4) Core User Stories
1. **Import:** As a learner, I can import a CSV of vocabulary to create/update entries.
2. **Review & Edit:** As a learner, I can view vocabulary in a table and edit front/back/comment/lesson inline.
3. **Filter:** As a learner/viewer, I can filter the table by lesson to focus on a subset.
4. **Export:** As a learner, I can export all vocabulary to CSV (including generated ids) for backup or editing.
5. **Share (Create):** As a learner, I can create one or more read‑only links with random tokens.
6. **Share (Manage):** As a learner, I can see all my links and revoke any of them.
7. **Share (Consume):** As a public viewer, I can open a link and see a read‑only table with filter by lesson.

## 5) Functional Requirements
### 5.1 Import (CSV)
- **FR-1:** Accept UTF‑8 CSV upload. Columns: `id?`, `lesson?`, `front`, `back`, `comment?`.
- **FR-2:** `front` and `back` are required per row; others optional.
- **FR-3 (Upsert rule):**
  - If `id` present and matches existing item → update `front/back/comment/lesson`.
  - If `id` present and not found → create new item using that `id`.
  - If `id` absent → create new item and generate a new opaque `id`.
- **FR-4:** Ignore unknown extra columns; preserve only known fields.
- **FR-5:** Multi-line values and commas inside quotes must be supported.
- **FR-6:** Import preview: show N sample rows, detected columns, and potential errors before commit.
- **FR-7:** On commit, show a summary: created count, updated count, skipped/error count (with downloadable error CSV of failed rows and reasons).

### 5.2 Tabular Review & Edit
- **FR-8:** Table shows columns: `front`, `back`, `comment`, `lesson` (all editable) and (non-editable) `id`.
- **FR-9:** Inline edit with Enter/Escape, client-side validation (non-empty `front/back`).
- **FR-10:** Sorting by any column; search (simple contains) across `front/back/comment`.
- **FR-11:** Filter by `lesson` with a dropdown (multi-select) based on distinct lessons present.
- **FR-12:** Pagination or virtualized scrolling; target >10k rows without freezing UI.

### 5.3 Export (CSV)
- **FR-13:** Export full dataset to CSV with header row. Default column order: `id,lesson,front,back,comment`.
- **FR-14:** UTF‑8 with BOM optional (toggle); CRLF line endings for compatibility; quoted fields when needed.

### 5.4 Shareable Public Links
- **FR-15:** Create share links with random tokens (≥128 bits entropy), e.g., 22–32 char URL-safe.
- **FR-16:** Each link provides read-only access to the table (same columns) with sort & filter by lesson.
- **FR-17:** Owner can see a **Share Links** page listing: token (copy button), created date, last accessed, total visits, status (active/revoked), optional label.
- **FR-18:** Owner can revoke a link; revoked links immediately become unusable (HTTP 410 or 404).
- **FR-19:** Robots noindex and noopen; do not expose tokens in referrers across domains.

## 6) Data Model (minimal)
### VocabularyItem
- `id: string` (opaque, unique)
- `front: string`
- `back: string`
- `comment?: string`
- `lesson?: string`
- `createdAt: datetime`
- `updatedAt: datetime`

### ShareLink
- `id: string`
- `token: string` (unique, URL-safe)
- `label?: string`
- `createdAt: datetime`
- `revokedAt?: datetime`
- `lastAccessedAt?: datetime`
- `visitCount: number`

## 7) API Endpoints (suggested for prototype)
- `POST /api/import` — multipart CSV upload → `{created, updated, errors[]}`; dryRun=true for preview.
- `GET /api/items` — list with query: `q`, `lesson[]`, `sort`, `page`, `pageSize`.
- `PATCH /api/items/:id` — partial updates to `front/back/comment/lesson`.
- `GET /api/export` — returns CSV stream.
- `POST /api/shares` — create link `{label?}` → `{token, url}`.
- `GET /api/shares` — list links.
- `DELETE /api/shares/:id` — revoke.
- `GET /s/:token` — public read-only view (server-rendered or SPA route) using token.

## 8) UX Flows (high level)
1. **Import Flow:** Click *Import* → upload CSV → preview parsed columns & N rows → show issues → *Import* → summary.
2. **Review/Edit Flow:** See table → filter by lesson → inline edit cells → autosave per cell (toast on success/error).
3. **Export Flow:** Click *Export CSV* → download starts.
4. **Share Flow:** *Create Share Link* → optional label → show URL & copy button → *Manage Links* list with revoke.
5. **Public View:** Open `/s/{token}` → read-only table with filter/search/sort.

## 9) Validation & Error Handling
- Required fields (`front/back`) enforced on import and inline edits.
- Import errors produce row-level messages (e.g., missing `back`, invalid CSV quoting). Provide downloadable error CSV.
- Unknown columns ignored with warning.
- Large file handling: stream parse; cap at, e.g., 10 MB for prototype with clear error.
- Public link invalid/revoked → friendly error page ("This list is no longer available").

## 10) Acceptance Criteria (per feature)
**Import**
- Upload of well-formed CSV with 3+ rows shows accurate preview; after import, created/updated counts match expectations.
- Upsert by `id` updates existing rows without creating duplicates.
- Unknown columns are ignored; required columns enforced.

**Table Edit & Filter**
- Inline edits persist after refresh; validation prevents empty `front/back`.
- Filter by one or more lessons reduces rows accordingly.
- Sorting by any column works and is stable.

**Export**
- Exported CSV re-imports without data change (id preserved), byte-for-byte equality for fields.

**Share Links**
- Creating a link yields a working public URL that is read-only.
- Revoking a link immediately disables access.
- Share links list shows all links with accurate last accessed and visit count.

## 11) Test Cases (sampling)
- Import CSV with: (a) missing header, (b) BOM, (c) quoted commas, (d) multi-line comment, (e) unknown columns, (f) duplicate ids, (g) non-UTF8 (should fail gracefully).
- Upsert: same `id`, modified `front` only → item updates.
- Inline edit: clear `comment` to empty → persists.
- Lesson filter: multiple selection shows union of lessons.
- Export→Re-import round trip yields identical row counts and ids.
- Public view: open revoked token returns 410/404 with friendly page.

## 12) Milestones
- **M0 (Skeleton):** Project scaffolding; health check; basic table with mock data.
- **M1 (Import):** CSV upload, preview, commit, summary.
- **M2 (Review/Edit/Filter):** Editable table; sort/search; lesson filter; persistence.
- **M3 (Export):** CSV export (round-trip tested).
- **M4 (Sharing):** Create/list/revoke tokens; public read-only route.
- **M5 (Polish):** Accessibility pass, empty states, copy-to-clipboard, error pages.

## 13) Future Considerations (post‑prototype)
- Spaced repetition (SM-2, FSRS), quiz modes, progress stats.
- Per-link filters, expiration, password protection.
- Multi-user accounts, collaboration, comments.
- Rich fields (examples, parts of speech), media attachments.
- Mobile-friendly layout and PWA/offline support.

