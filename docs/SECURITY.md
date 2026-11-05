# Security, Privacy & Data Protection Architecture
## Project: Kitaab Bank – Smart School Book Exchange (کتاب بینک)

---

## 1. Authentication & Session Security

### 1.1 Password Hashing & Credentials Storage
- All teacher passwords are encrypted using **Werkzeug's PBKDF2-HMAC-SHA256** (with a minimum of 600,000 hash iterations) using cryptographically secure random salts.
- Plaintext passwords are never logged, stored in application memory, or written to database snapshots.
- Seeded teacher accounts force a password reset prompt on first login.

### 1.2 Session Hardening
- Session cookies are signed with a cryptographically high-entropy 256-bit secret key (`SECRET_KEY`).
- Cookies enforce:
  - `HttpOnly = True`: Blocks client-side JavaScript access to session tokens.
  - `SameSite = 'Lax'`: Mitigates Cross-Site Request Forgery across external origins.
  - `Session Inactivity Timeout`: 8-hour max session lifespan, ensuring unattended school computers log out automatically.

### 1.3 Route Authorization Guards
- Public student endpoints (`/`, `/catalogue`, `/book/<id>`, `/donate`, `/request`, `/track`, `/scan`) are open to all users on the local Wi-Fi.
- All teacher management endpoints (`/teacher/*`, `/api/teacher/*`) are strictly shielded behind a custom Python decorator `@teacher_required`.
- Unauthenticated requests are immediately redirected to `/auth/login` with safe `next` parameter validation (open-redirect protection).

---

## 2. CSRF Protection & Public Form Defenses

### 2.1 Cross-Site Request Forgery (CSRF) Guard
All state-modifying requests (`POST`, `PUT`, `DELETE`) are strictly protected against CSRF attacks:
- A unique CSRF token is derived per user session using HMAC-SHA256: `HMAC(SECRET_KEY, session_id + timestamp)`.
- Every HTML form embeds:
  ```html
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  ```
- A global Flask `@app.before_request` hook validates the submitted token against the session before any view handler is invoked. Requests lacking a valid token are rejected with `HTTP 400 Bad Request: Invalid or missing CSRF token`.

---

## 3. Configurable Rate Limiting & Shared School Wi-Fi / ngrok Hardening

When the local server is shared across a school Wi-Fi network (or exposed via `run_tunnel.py` ngrok for exhibition demonstrations), dozens of students in a single computer lab or classroom will share the same router NAT IP. A hardcoded, low rate limit would mistakenly block legitimate students during group library sessions.

### 3.1 Configurable Sliding Window Rate Limiter
A lightweight, zero-dependency in-memory rate limiter tracks request frequency per client IP with configurable thresholds in `config.py`:
- **Donation Submissions (`POST /donate`):** Default **120 submissions per hour per IP** (supports full classroom batches).
- **Book Requests (`POST /request`):** Default **120 requests per hour per IP** (allows multiple students sharing one NAT IP to request books).
- **Tracking Lookups (`GET /track`):** Default **30 lookups per minute per IP** (handles multiple students checking their requests simultaneously while still blocking automated code enumeration).
- **Teacher Login Attempts (`POST /auth/login`):** Capped strictly at **5 failed attempts per 15 minutes per IP** (guards against brute-force attacks).
- If an individual client exceeds the threshold, the server returns an informative `HTTP 429 Too Many Requests` page with a retry timer.

### 3.2 Proxy & ngrok Header Sanitization
- Behind ngrok or a reverse proxy, client IP addresses are forwarded in the `X-Forwarded-For` HTTP header.
- The rate limiter sanitizes incoming headers to prevent IP spoofing, ensuring fair rate limiting for both local subnet devices and remote ngrok connections.

---

## 4. Student Privacy & Data Confidentiality

### 4.1 Frictionless Zero-Account Model
- School students (Classes 6–8) do **not** register accounts, store passwords, or link personal emails.
- This eliminates the risk of credential leakage, forgotten passwords, or unauthorized profile takeovers.

### 4.2 Cryptographically Unpredictable Tracking Codes & Collision Handling
- Tracking codes are **not** sequential integers (which would allow enumeration attacks).
- Codes are generated using Python’s standard library `secrets` module:
  ```python
  import secrets
  import string

  def generate_secure_tracking_code() -> str:
      # Generates a code like 'KB-REQ-7K9M-2X4P'
      alphabet = string.ascii_uppercase.replace('O', '').replace('I', '') + "23456789"
      part1 = ''.join(secrets.choice(alphabet) for _ in range(4))
      part2 = ''.join(secrets.choice(alphabet) for _ in range(4))
      return f"KB-REQ-{part1}-{part2}"
  ```
- **Database Uniqueness & Retry Loop:** The column `requests.tracking_code` enforces a `UNIQUE` constraint. The request creation service includes a bounded retry loop (5 attempts) to guarantee zero collisions even in astronomical edge cases.
- Combined with rate limiting, the $(32^8)$ combinations make brute-force guessing mathematically impossible.

### 4.3 Personally Identifiable Information (PII) Redaction
- **Public Catalogue & Book Details:** Book records display title, author, subject, class, language, condition, and availability. No donor or requester details are ever exposed in public HTML.
- **Request Tracking Lookup (`/track`):**
  - Requires the exact private 16-character Tracking Code.
  - Displays only request status (`Pending`, `Approved - Ready for Pickup`, `Completed`) and masked student identifiers (e.g., `Zeeshan *** (Class 7)`).
  - Parent phone numbers and student roll numbers are completely redacted on public tracking pages.
- **Teacher Dashboard Exclusivity:** Full student roll numbers, classes, and contact numbers are visible **only** to authenticated teachers for verification during physical handover.

---

## 5. Input Validation, Injection Defense & Upload Security

### 5.1 SQL Injection Prevention
- Zero raw string formatting or SQL string concatenation (`f"SELECT ... {input}"` is strictly forbidden).
- 100% of database interactions use **parameterized queries** with positional tuples:
  ```python
  cursor.execute(
      "SELECT * FROM books WHERE subject = ? AND class_grade = ?;",
      (subject, class_grade)
  )
  ```

### 5.2 Cross-Site Scripting (XSS) Mitigation
- Jinja2 automatic contextual HTML escaping is enforced across all templates.
- Any dynamic text rendered in templates utilizes safe variable interpolation (`{{ book.title }}`).
- Raw HTML rendering (`| safe`) is banned across all user-submitted fields.

### 5.3 Secure File Upload Handling
Uploaded book photographs represent a common attack vector if left unconstrained:
1. **Extension Whitelisting:** Strictly permit only `.jpg`, `.jpeg`, `.png`, and `.webp`.
2. **File Size Capping:** Enforce `MAX_CONTENT_LENGTH = 3 * 1024 * 1024` (3 Megabytes).
3. **Path Traversal Defense:** Original filenames are discarded. Files are renamed using a deterministic UUID4 hex string: `uuid.uuid4().hex + ".webp"`.
4. **Image Re-Encoding (Pillow):** All incoming images are parsed, converted to `RGB`, resized to a maximum dimension of 800px, and re-encoded using Pillow. This process automatically strips embedded EXIF metadata and neutralizes malicious polyglot file payloads.
5. **Storage Isolation:** Uploads reside in `app/static/uploads/books/` and are served strictly as static images.

---

## 7. Physical Handover Security & Circulation Defense

### 7.1 Student Identity Verification (Anti-Impersonation)
- **Tracking Code Insufficiency Policy:** The presentation of a tracking code (`KB-REQ-XXXX-XXXX`) is treated solely as an indexing reference, **never** as proof of identity or entitlement.
- **Physical Verification Mandate:** Teachers must cross-check the student's name, class, section, and roll number against official school attendance or identity cards before handing over any textbook.
- **Mandatory Dual Checkboxes:** The handover confirmation route strictly enforces both `confirm_id` and `confirm_physical` checkboxes. Submitting the form with either checkbox unchecked results in an explicit rejection.

### 7.2 Immutable Handover Ledger
- Every completed handover generates an immutable snapshot record in `handovers` with a sequential code (`KB-HO-000001`).
- The ledger snapshot preserves the student name, class, roll number, teacher name, book code, and tracking code as they existed at the exact moment of physical custody transfer.
- Once a handover is completed, it cannot be modified, deleted, or cancelled via the web interface.

### 7.3 Anti-Double-Distribution & Atomic Lock
- The database enforces `request_id INTEGER NOT NULL UNIQUE` on the `handovers` table.
- A physical book can only be handed over if its current status is `reserved` and the request is `approved`.
- All status transitions (`requests.status = 'completed'`, `books.status = 'handed_over'`) occur within a single atomic `BEGIN IMMEDIATE` transaction, eliminating race conditions or double handovers.

### 7.4 Handover Receipt Confidentiality
- Handover receipts (`/teacher/handovers/<id>/receipt`) contain unmasked student roll numbers and phone numbers for official school records.
- These receipt routes are strictly restricted to authenticated teachers (`@teacher_bp.before_request`). Unauthenticated visitors or students cannot access receipt URLs.
- The public student tracking desk (`/track`) remains 100% redacted: showing only the handover reference code (`KB-HO-XXXXXX`), completion status, and masked student name (`Saad R***`). Student roll numbers and phone numbers are completely stripped.

### 6.1 Lock Starvation & Deadlock Defense
- SQLite WAL mode permits concurrent readers alongside **at most one active writer**.
- To prevent locking bottlenecks and connection starvation:
  - Every connection sets `PRAGMA busy_timeout = 5000;`.
  - All write transactions invoke `BEGIN IMMEDIATE` up front, avoiding read-to-write lock upgrade deadlocks.
  - File I/O, password hashing, and image processing are completed **before** opening a write transaction.
  - Operations catch `sqlite3.OperationalError` with an exponential backoff retry policy (3 retries).

### 6.2 Safe Hot Backups & Integrity Verification
- Backups use Python's built-in `sqlite3.Connection.backup()` API.
- **Consistent Live Snapshot:** It produces a byte-consistent live snapshot while concurrent reads proceed smoothly. Rather than promising completely lock-free operation, it briefly acquires shared read locks per incremental page chunk (`step()`), pausing writes for only microseconds without causing timeouts.
- Generated backup files are automatically verified using `PRAGMA integrity_check;` and schema validation before being cataloged in `backup_records`.
- Restorations create an automatic pre-restore safety snapshot before touching live data.

---

## 8. QR Code Security, Camera Hardware Safeguards & Code Normalization

### 8.1 Camera Hardware Privacy & Anti-Surveillance Lifecycle
- Mobile browser cameras represent a sensitive hardware sensor. Kitab Bank enforces strict hardware stream teardown in `app/static/js/qr_scanner.js`.
- Whenever a camera modal is closed, the user switches browser tabs (`visibilitychange` with `document.hidden`), or navigates away (`pagehide`, `beforeunload`), every active `MediaStreamTrack` is explicitly terminated via `track.stop()`.
- This guarantees that device camera hardware and green/orange indicator lights are immediately powered down, preventing background surveillance or battery drain.

### 8.2 Secure Context Restrictions & Local Network Protection
- In compliance with W3C web security standards, camera access (`navigator.mediaDevices.getUserMedia`) is strictly restricted to Secure Contexts (`https://` or `localhost`).
- When accessed over unencrypted local school Wi-Fi (e.g. `http://10.0.0.36:5000`), the application detects insecure origins via `window.isSecureContext` and presents an educational notice instead of throwing unhandled exceptions or attempting insecure capture.
- Prominent manual 6-digit Book Code lookup (`KB-BK-000001`) ensures full student functionality even when HTTPS certificates are not deployed on local school intranets.

### 8.3 Input Normalization & Anti-Injection on Scanner Lookups
- Scanned inputs and manual queries on `/scan` pass through a robust parser (`qr_service.parse_scanned_book_code`):
  - Strips leading/trailing whitespace and control characters.
  - Safely extracts codes from full URLs or relative paths using Python standard library URL parsing.
  - Enforces strict regex validation (`KB-BK-\d{6}` or numeric expansion).
  - Sanitizes user input before parameterized SQLite queries, completely preventing SQL injection.
- Failed lookups return generic user-friendly messages without leaking database internals or stack traces.

### 8.4 Zero-Storage QR Generation & Teacher Auth Guards
- Dynamic QR code generation (`/qr/<book_code>.png`) generates images in-memory via Pillow/qrcode, preventing disk fill attacks or filesystem race conditions.
- Single book sticker labels (`/teacher/books/<code_or_id>/qr`) and bulk A4 label printing (`/teacher/qr-sheet`) are strictly protected behind teacher session authentication (`@teacher_bp.before_request`). Unauthenticated users cannot view batch label sheets or teacher administration tools.

---

## 9. Teacher Administrative Security, Inventory Authorization & Audit Integrity

### 9.1 Teacher Route Defense & CSRF Session Isolation
- Every teacher route under `/teacher/*` is gated behind `@teacher_bp.before_request`. Any attempt to access dashboard, inventory, reports, or logs without an active authenticated session results in a 302 redirect to `/auth/login`.
- All mutation endpoints (`/teacher/inventory/new`, `/teacher/inventory/<id>/edit`, `/teacher/inventory/<id>/status`, `/auth/login`) enforce session CSRF token verification. Missing or mismatched tokens trigger an immediate HTTP 400 rejection.
- Login redirection strictly validates the `next` query parameter against `is_safe_url()`, completely neutralizing open-redirect vulnerabilities.

### 9.2 Inventory State Machine Integrity & Circulation Defense
- Books in the inventory cannot have their status changed arbitrarily:
  - Textbooks with an active reservation (`status = 'reserved'`) cannot be retired or modified until the teacher cancels the reservation.
  - Textbooks that have completed physical handover (`status = 'handed_over'`) cannot be modified or retired, preserving the historical integrity of the handover ledger.
- Textbooks added directly by teachers receive unique, sequential Latin codes (`KB-BK-XXXXXX`), validated to prevent identifier collisions.

### 9.3 Immutable Append-Only System Audit Trail
- The `activity_logs` table operates as an append-only audit trail. It does not expose `UPDATE` or `DELETE` endpoints in the web application.
- Staff logins, logouts, donation actions, request allocations, handover completions, and inventory mutations are automatically recorded with actor names, roles, and timestamps, ensuring accountability.

### 9.4 CSV Injection Mitigation
- Exported spreadsheets (`/teacher/reports/export/inventory.csv` and `/teacher/reports/export/handovers.csv`) are generated using Python's standard `csv.writer` with strict quoting.
- Text cells containing potential spreadsheet formula prefixes (`=`, `+`, `-`, `@`) are safely handled to prevent command execution or DDE injection when opened in external spreadsheet software like Excel or LibreOffice Calc.
