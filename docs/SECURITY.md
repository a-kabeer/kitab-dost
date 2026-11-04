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

## 6. SQLite Concurrency, Lock Mitigation & Hot Backups

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
