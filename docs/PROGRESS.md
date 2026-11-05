# Kitaab Bank – Project Progress & Phase Tracker

---

## 1. Project Health & Milestone Status

| Phase | Milestone Name | Status | Target Date | Completed Date | Notes |
|---|---|---|---|---|---|
| **Phase 0** | **Project Planning & Architecture** | **COMPLETED & VERIFIED** | Day 1 | 2026-11-04 | PRD, Architecture, Schema, Security, Roadmap & Progress finalized with all review improvements. |
| **Phase 1** | **Foundation, WAL Concurrency & Dual-Portal Themes** | **COMPLETED & VERIFIED** | Day 1 | 2026-11-04 | Flask factory, Waitress, SQLite WAL, Dual-Portal Theme system, 100% offline assets verified. |
| **Phase 2** | **Student Website & Book Discovery** | **COMPLETED & VERIFIED** | Day 2 | 2026-11-04 | Live stats, hero search, multi-faceted filtering, book detail view, 16 realistic textbooks (En/Ur/Sd) with local SVG covers. |
| **Phase 3** | **Book Donations, Pillow Pipeline & Review Queue** | **COMPLETED & VERIFIED** | Day 3 | 2026-11-04 | Student donation form, secure reference tokens (KB-DON-), local Pillow re-encoding, teacher review queue, atomic approval (KB-BK-000001) & rejection reason ledger. |
| **Phase 4** | **Book Requests, Secure Tokens & Reservation Lock** | **COMPLETED & VERIFIED** | Day 4 | 2026-11-04 | Student book request form, cryptographically secure tracking code (KB-REQ-), atomic reservation lock (BEGIN IMMEDIATE), private tracking desk (/track) with strict PII masking, teacher review queue. |
| **Phase 5** | **Physical Handover Ledger & Circulation Defense** | **COMPLETED & VERIFIED** | Day 5 | 2026-11-05 | Handover verification form, dual confirmation checkboxes, sequential KB-HO-000001 ledger, printable A4 receipt, student tracking timeline, reservation release/cancellation, and 55 unit tests + 4 browser tests passing. |
| **Phase 6** | **QR System, Label Printing & Android Tested Scanner** | **READY TO START** | Day 6 | — | Dependent on Phase 5 sign-off. |
| **Phase 7** | Teacher Dashboard, Analytics & Themed Admin Desk | PENDING | Day 7 | — | Dependent on Phase 6. |
| **Phase 8** | Multilingual RTL, Hot Backups & Exhibition Mode | PENDING | Day 8 | — | Dependent on Phase 7. |
| **Phase 9** | Comprehensive QA, Multi-Device Hardening & Release | PENDING | Day 9 | — | Final sign-off milestone. |

---

## 2. Phase 0 Review & Enhancements Summary

The following core improvements have been fully integrated into the architecture documentation:

### 1. SQLite WAL Concurrency Clarification
- **Corrected Understanding:** Clarified in `ARCHITECTURE.md` and `DATABASE_SCHEMA.md` that SQLite WAL allows concurrent readers and **exactly ONE active writer at a time**.
- **Implementation Rules:** All write transactions must be ultra-short, use `BEGIN IMMEDIATE` up front (eliminating read-to-write deadlock scenarios), configure `PRAGMA busy_timeout = 5000;`, and wrap write operations with exponential backoff retries (3 attempts) against transient `database is locked` states.

### 2. QR Scanner & Mobile Camera LAN Constraints
- **Secure Context Restriction:** Documented that modern mobile browsers (Android Chrome, iOS Safari) strictly block `navigator.mediaDevices.getUserMedia` over plain HTTP on LAN IPs (`http://192.168.x.x:5000`).
- **Dual-Mode Solution:** Made manual 6-digit Book Code entry (`KB-BK-000001`) a prominent, first-class feature on the scan screen rather than a hidden fallback.
- **Physical Device Testing:** Added explicit acceptance criteria requiring physical Android device testing under both plain HTTP (graceful fallback banner) and HTTPS via ngrok (active camera stream).
- **Stream Cleanup:** Adopted stream teardown patterns from `madrasah_library` (`track.stop()` on dialog close and page unload) to prevent camera indicator lights from staying active.

### 3. Database Hot Backup, Validation & Restoration
- **Live Snapshot Mechanics:** Configured Python SQLite’s built-in `connection.backup()` API as a consistent live snapshot, explicitly acknowledging brief shared read page locks rather than claiming completely lock-free operation.
- **Automated Validation:** Every backup is verified using `PRAGMA integrity_check;` and schema checks before being cataloged in `backup_records`.
- **Restoration Protocol:** Documented safe restore procedure with automated pre-restore rollback copies.

### 4. Standardized Book Codes & Unpredictable Tracking Codes with Collision Handling
- **Standardized Book Code Format:** Standardized as `KB-BK-000001` (six numeric digits) for consistent printing and scanning.
- **High-Entropy Tokens:** Switched from predictable sequential IDs to cryptographically secure tokens generated via Python `secrets`: `KB-REQ-XXXX-XXXX` (over 1 trillion combinations).
- **Database Uniqueness & Collision Handling:** Enforced database `UNIQUE` constraint with retry-on-collision loop.
- **Anti-Enumeration Guard:** Applied a sliding-window rate limit on `/track` lookups with generic error responses to prevent brute-force guessing of other students' tracking codes.

### 5. Configurable Rate Limiting for Shared School Wi-Fi & ngrok Hardening
- **Shared NAT Tolerance:** Configurable rate limits in `config.py` (default 120/hr for requests & donations) to allow multiple students sharing the same school Wi-Fi or lab gateway IP to submit simultaneously without false rate-limit rejections.
- **CSRF Defense:** Added HMAC-SHA256 session-bound CSRF token validation across all state-modifying requests (`POST`, `PUT`, `DELETE`).
- **Tunnel Exposure:** Hardened against ngrok exposure by sanitizing `X-Forwarded-For` proxy headers.

### 6. Integration of Insights from `madrasah_library` Reference
- Inspected the actual repository `https://github.com/a-kabeer/madrasah_library`.
- Adopted printable label CSS techniques (`@media print`), camera scanner stream cleanup lifecycles, bilingual RTL typography preserving Latin digits in codes, and design token styling.
- Maintained strict architectural simplicity: Kitaab Bank remains a lightweight Flask + SQLite WAL application, completely independent of Django or PostgreSQL.

### 7. Full Theme System Across Both Portals
- Verified that **Light Mode, Dark Mode, and System Default** are implemented seamlessly across **both the Student Website and the Teacher Administrative Dashboard**.
- Documented the shared CSS token system and the `<head>` inline script preventing Flash of Unstyled Content (FOUC).

---

## 3. Known Limitations & Operating Boundaries

1. **Camera Scanning on Local Wi-Fi (HTTP):**
   - Due to browser hardware security policies, camera scanning on mobile phones requires a Secure Context (HTTPS). When accessing the server via plain HTTP LAN IP (`http://192.168.1.x:5000`), mobile cameras will be blocked by Android Chrome/Safari. Students and teachers must either:
     - Use the prominent manual 6-digit Book Code entry (`KB-BK-000001`) on the scan screen (fastest, 0 setup).
     - Or access via the optional ngrok HTTPS tunnel (`run_tunnel.py`).
     - Or enable `unsafely-treat-insecure-origin-as-secure` in `chrome://flags` on test devices.
2. **Single Writer Serialization:**
   - Under heavy concurrent write loads (e.g. 20 students pressing "Submit Donation" in the exact same millisecond), writes are serialized by SQLite. The 5,000ms busy timeout and immediate transactions prevent errors, but write latency will be slightly higher during simultaneous burst submissions.

---

## 4. Phase 0 Completion & Sign-off

- All Phase 0 review tasks and documentation updates are **100% COMPLETE & APPROVED**.
- Final corrections applied:
  1. Configurable public form rate limits suitable for shared school Wi-Fi / NAT.
  2. Standardized 6-digit book codes (`KB-BK-000001`) and secure tracking token generation with database uniqueness and collision handling.
  3. Realistic SQLite backup documentation described as a consistent live snapshot with shared page locks.

---

## 5. Phase 1 Implementation & Verification Results

**Implementation Status: COMPLETED & VERIFIED (2026-11-04)**

### Implemented Components
1. **Flask Application Factory (`app/__init__.py`):**
   - Configurable environment-driven setup (`config.py`).
   - SQLite connection teardown hooks and automated schema initialization.
   - Built-in session CSRF protection context processor (`csrf_token`).
   - Hardened security headers (`X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`).
   - Custom error handlers for `404`, `429`, and `500`.
2. **Production WSGI Server (`run_server.py`):**
   - Waitress serving on `0.0.0.0:5000` with 6 worker threads.
   - Automatic local LAN IP detection (`172.31.161.179`) and network banner for mobile access.
   - Windows UTF-8 stdout configuration preventing charmap encoding errors with Urdu strings.
3. **Database Architecture (`app/database.py` & `app/schema.sql`):**
   - SQLite initialized with `PRAGMA foreign_keys = ON;`, `PRAGMA journal_mode = WAL;`, `PRAGMA busy_timeout = 5000;`, `PRAGMA synchronous = NORMAL;`.
   - `db_transaction()` context manager implementing `BEGIN IMMEDIATE` and exponential backoff retry.
   - All 8 core tables created (`teachers`, `books`, `donations`, `requests`, `handovers`, `activity_logs`, `system_settings`, `backup_records`).
4. **Base Application Layout & Dual-Portal Shells:**
   - **Student Portal:** Responsive base layout (`base.html`), hero landing shell (`student/index.html`), and placeholders for future phases.
   - **Teacher Portal:** Administrative shell (`teacher/base_teacher.html`) with sidebar navigation, metric cards, and dashboard overview (`teacher/dashboard.html`).
5. **Theme System (Light, Dark, System Default):**
   - 100% offline CSS custom properties in `static/css/main.css` and `static/css/components.css`.
   - Zero-FOUC blocking script in `<head>` eliminating light/dark flashing on page load.
   - Fully interactive dropdown selector with instant DOM update and `localStorage` persistence.
   - Shared consistently across both student and teacher portals.
6. **100% Offline Static Assets:**
   - Zero external CDN links (no Bootstrap, Tailwind, Google Fonts, or unpkg).

### Automated Test Verification Summary
| Test Suite | Scope | Result | Details |
|---|---|---|---|
| `test_phase1.py` [Test 1] | SQLite & WAL Mode | **PASS** | `journal_mode = wal`, 8 tables verified, 4 settings seeded |
| `test_phase1.py` [Test 2] | Student Portal Routes | **PASS** | `/`, `/catalogue`, `/donate`, `/track`, `/scan`, `/about` (HTTP 200) |
| `test_phase1.py` [Test 3] | Teacher Route Auth Protection | **PASS** | All `/teacher/*` routes blocked without login (HTTP 302 -> `/auth/login`); CSRF validated; login authenticated |
| `test_phase1.py` [Test 4] | Offline Static Assets | **PASS** | `main.css`, `components.css`, `student.css`, `teacher.css`, `theme.js` (HTTP 200, 0 CDNs) |
| `test_phase1.py` [Test 5] | Error Handlers | **PASS** | Custom 404 page renders cleanly |
| `test_phase1.py` [Test 6] | Immediate Transactions | **PASS** | `BEGIN IMMEDIATE` transaction committed successfully |
| `test_phase1.py` [Test 7] | App Restart Persistence | **PASS** | Data preserved across app context teardown and restart |
| `test_server_live.py` | Live Waitress Server | **PASS** | Localhost `127.0.0.1:5000` & Active LAN Wi-Fi `172.17.109.179:5000` (HTTP 200) |
| `test_concurrency.py` | Concurrency & Simultaneous Submissions | **PASS** | 15 concurrent threads submitted simultaneously; 100% success, 0 lock errors |
| `test_ui_audit.py` | UI, Assets & Responsiveness Audit | **PASS** | 100% internal links resolved, 0 external CDN links, responsive meta viewport verified |
| `test_browser_live_edge.py` | Real Chromium (Edge) Browser Audit | **PASS** | 0 console errors, 0 runtime JS errors, 390px mobile viewport, theme persistence verified |

---

## 6. Phase 1 Final Verification Audit & Defect Fixes

1. **Teacher Route Access Protection (Defect Resolved):**
   - *Defect Found:* Initial implementation allowed direct unauthenticated access to `/teacher/dashboard`.
   - *Fix Applied:* Built `app/blueprints/auth/` with secure password hashing (`check_password_hash`), seeded default teacher account (`teacher` / `Teacher@123`), and attached `@teacher_bp.before_request` hook redirecting all unauthenticated requests to `/auth/login`. Added CSRF token validation on login.
2. **Git Initialization & Exclusion Hardening (Completed):**
   - *Action:* Git repository initialized (`master` branch).
   - *Exclusions Verified:* Updated `.gitignore` to explicitly ignore `.env`, `*.db`, `backups/*.db`, and `app/static/uploads/books/*` while retaining directory structures with `.gitkeep`.
   - *Baseline Commits:*
     - `7611ea2` – `feat(phase-1): application foundation, dual-portal theme system and SQLite WAL setup`
     - `3b1686d` – `fix(phase-1): add local svg favicon, eliminate browser console 404, add Playwright Edge browser audit`
3. **Browser Console 404 Defect (Resolved):**
   - *Defect Found:* Browsers automatically request `/favicon.ico`, which returned a 404 in the console.
   - *Fix Applied:* Added local SVG book favicon (`app/static/img/favicon.svg`), wired into `<link rel="icon">`, and added `/favicon.ico` route in `app/__init__.py`. Result: **0 Console Errors / Warnings**.
4. **Real Browser Headless Audit (Completed via Playwright + Microsoft Edge):**
   - Verified on both Desktop (1280x800) and Mobile (390x844 with touch enabled and Android user agent).
   - Theme switching (Light, Dark, System Default) confirmed with persistence across reloads.
   - Mobile hamburger navigation toggle confirmed working cleanly on tap.
   - Student navigation flow (5 routes) confirmed loading HTTP 200.
   - Teacher authentication lifecycle (guard, invalid login rejection, valid login, theme toggle, sign out, re-locking) confirmed.
5. **LAN IP & Wi-Fi Access Testing:**
   - *Automated Server Test:* Verified Waitress binds to `0.0.0.0:5000` and serves on `http://172.17.109.179:5000` and `http://127.0.0.1:5000`.
   - *IP Update Note:* Active Wi-Fi DHCP lease updated the host IP to `172.17.109.179`.
   - *Physical Device Access:* Android phone connects via `http://172.17.109.179:5000/`. If Windows Firewall on Public network blocks incoming TCP traffic, profile must be set to Private network in Windows Wi-Fi settings.
6. **Zero External Dependencies Confirmed:**
   - Verified that all assets load 100% offline without active internet.

### Stopping Point
- **Phase 1 Final Verification Audit is 100% COMPLETE.**

---

## 7. Phase 2 Implementation & Verification Results

**Implementation Status: COMPLETED & VERIFIED (2026-11-04)**

### Implemented Components
1. **Homepage & Impact Metrics (`/`):**
   - Project introduction and mission for school students and teachers.
   - Quick hero search bar directing queries seamlessly to `/catalogue`.
   - Real-time impact metric counters queried directly from SQLite: `Total Books Donated`, `Currently Available`, `Successfully Reused`, `Student Beneficiaries`.
   - "Recently Added Educational Books" showcase grid with condition badges, class badges, and direct links to book details.
   - 4-step "How Kitaab Bank Works" visual workflow.
2. **Book Catalogue (`/catalogue`):**
   - Multi-faceted filter panel allowing simultaneous filtering by:
     - Free-text search query (`q`) matching title, author, subject, description, publisher, and standardized book code.
     - Class Level (`Class 6`, `Class 7`, `Class 8`).
     - Subject (`Mathematics`, `General Science`, `Urdu`, `Sindhi`, `Computer Science`, `Islamiat`, `Social Studies`).
     - Language (`English`, `Urdu`, `Sindhi`).
     - Condition State (`Like New`, `Good`, `Fair`).
     - Sorting: Title (A-Z), Newest First, Class Level.
   - Active filter pills display with one-click reset links.
   - Result count strip showing number of matching books.
   - User-friendly empty state with icon, helpful tips, and "Clear All Filters" button when no results match.
3. **Book Detail Page (`/book/<book_code>`):**
   - Full textbook view with large cover display and availability status.
   - Standardized reference code display (`KB-BK-000001` to `KB-BK-000016`).
   - Metadata grid: Class Grade, Subject, Language, Publisher/Board, Edition Year, Teacher Verified status.
   - Detailed syllabus coverage and textbook overview section.
   - Contextual related books section recommending other available books for the same class grade.
   - Return to catalogue breadcrumb and navigation.
4. **Sample Educational Dataset & 100% Offline Local Media:**
   - 16 realistic curriculum textbooks seeded into SQLite:
     - 8 English medium books
     - 5 Urdu medium books
     - 3 Sindhi medium books
     - Covering Classes 6, 7, and 8 across all core school subjects.
   - 17 local SVG textbook cover illustrations generated in `app/static/img/covers/` with zero CDN or external image dependencies.
5. **Domain Services Layer (`app/services/book_service.py`):**
   - Clean separation of concerns between HTTP routes and SQLite database queries.
   - Functions for filtered querying, detail lookup, dropdown options, featured books, and live metrics.

### Automated Test Verification Summary
| Test Suite | Scope | Result | Details |
|---|---|---|---|
| `tests/test_phase2.py` | Unit & Integration Tests | **PASS (12/12)** | Homepage, unfiltered catalogue (16 books), Class 6/7/8 filters, subject filters, English/Urdu/Sindhi filters, condition filters, keyword/code/Urdu/Sindhi search, empty search state, valid book detail, multilingual book detail, 404 on invalid code, 100% local cover assets verified |
| `test_phase1.py` | Phase 1 Foundation Regression | **PASS (7/7)** | Database, WAL mode, teacher auth guards, static assets, error handlers, and persistence verified |
| `test_concurrency.py` | Concurrency & WAL Performance | **PASS (15/15)** | 15 concurrent student write operations committed with 0 errors |
| `test_browser_phase2.py` | Real Headless Edge Browser Audit | **PASS** | Desktop (1280x800) and Mobile (390x844) viewports: search, filtering, card rendering, book details, and theme switching verified with **0 console errors and 0 page exceptions** |
| `test_browser_live_edge.py` | Real Browser Foundation Audit | **PASS** | Theme engine persistence and teacher authentication lifecycle verified with **0 console errors** |

### Network & LAN Access Note
- **Active LAN IP:** Host machine's Wi-Fi adapter IP renewed via DHCP to `10.0.0.35` (replacing the previous `172.31.161.179`).
- **Connection Refused Explanation:** Any browser attempting to connect to `172.31.161.179:5000` will fail with `ERR_CONNECTION_REFUSED` because that address is no longer assigned to the host computer.
- **Current Access URLs:**
  - Local PC: `http://127.0.0.1:5000` or `http://localhost:5000`
  - Mobile Phones / LAN devices: `http://10.0.0.35:5000` (on the same Wi-Fi)

### Stopping Point
- **Phase 2 – Student Website & Book Discovery is 100% COMPLETE & VERIFIED.**

---

## 8. Phase 3 Implementation & Verification Results

**Implementation Status: COMPLETED & VERIFIED (2026-11-04)**

### Implemented Components
1. **Student Donation Workflow (`/donate`):**
   - Clean, mobile-friendly submission form styled with Kitaab Bank design tokens.
   - Comprehensive input validation:
     - Textbook metadata: Title, Author, Class Level (`Class 6`, `Class 7`, `Class 8`), Subject, Language (`Urdu`, `English`, `Sindhi`), Condition (`Like New`, `Good`, `Fair`), and Description/Syllabus remarks.
     - Student donor information: Full Name, Class & Section (e.g. `8-A`), Roll Number, and optional Contact phone.
   - Preserves user input values on validation errors without data loss.
   - Hidden CSRF token verification across all form submissions.
   - Rate limiting via sliding-window tracker (`RATE_LIMIT_DONATE_PER_HOUR = 120`).
2. **Cryptographically Secure Reference Codes:**
   - Every submitted donation receives an unpredictable code: `KB-DON-XXXX-XXXX` (e.g. `KB-DON-ZRKC-6EHG`) generated using Python's `secrets` module with ambiguity-free characters.
   - Database uniqueness enforced with a collision-retry loop.
3. **Local Pillow Media & Image Security Pipeline:**
   - Optional book photograph upload supporting `.jpg`, `.jpeg`, `.png`, and `.webp`.
   - Content verification via `PIL.Image.open()` (inspecting actual binary data, not just file extensions).
   - Re-encoding to `RGB` mode and stripping all EXIF metadata and polyglot payloads.
   - Proportional resizing (maximum dimension 1000px) maintaining crisp aspect ratios.
   - Safe deterministic UUID4 filenames (`uuid.uuid4().hex + ".webp"`) stored in `app/static/uploads/books/`.
   - Fallback to matching local SVG covers if no photo is attached.
4. **Donation Confirmation Screen (`/donate/success/<donation_code>`):**
   - Highlighting the unique donation reference code with one-click clipboard copy.
   - Summarizing submitted textbook metadata and donor details.
   - Visual status badge: `⏳ Awaiting Teacher Approval`.
   - Explanatory copy reassuring students that teacher verification ensures school syllabus matching before catalogue publication.
5. **Teacher Administrative Donation Review Queue (`/teacher/donations`):**
   - Filter tabs with live badge counters: `Pending Review`, `Approved`, `Rejected`, and `All Records`.
   - Dynamic search by book title, author, donor name, roll number, or reference code.
   - Dropdown filter by class grade and subject.
   - Horizontally scrollable responsive table displaying thumbnails, metadata, and donor info.
6. **Atomic Approval Workflow (`/teacher/donations/<id>/approve`):**
   - Verification that donation status is currently `pending` (prevents double-approval).
   - Sequential unique book code generation in standard `KB-BK-000001` format (e.g. `KB-BK-000017`).
   - Atomic creation of public `books` record marked `available` and linked to original donation.
   - Updating donation status to `approved`, linking `book_id`, and recording reviewing teacher ID and timestamp.
   - Instant publication in the public catalogue (`/catalogue`) and book detail page.
7. **Rejection & History Ledger (`/teacher/donations/<id>/reject`):**
   - Interactive rejection modal with pre-configured reasons or custom reason input.
   - Updates donation status to `rejected`, records reason and teacher reviewer timestamp.
   - Preserves complete audit history without generating a public book listing.
8. **Student Privacy Protection:**
   - Student donor names, roll numbers, and contact numbers are strictly confined to teacher views.
   - Zero donor PII is exposed in the public catalogue, book cards, or book detail views.

### Automated Test Verification Summary
| Test Suite | Scope | Result | Details |
|---|---|---|---|
| `tests/test_phase3.py` | Unit & Integration Suite | **PASS (12/12)** | Form rendering, valid submission, validation errors, Pillow image pipeline & webp re-encoding, fake image rejection, teacher auth guards, review queue search/filters, atomic approval & book creation, donor privacy verification, duplicate approval prevention, rejection workflow, identical title handling |
| `tests/test_phase2.py` | Student Discovery Suite | **PASS (12/12)** | Homepage, catalogue, multi-faceted filtering, and book detail views |
| Full Test Suite (`tests/`) | Combined Suite | **PASS (24/24)** | 100% of unit and integration tests passing |
| `test_phase1.py` | Foundation & Security Regression | **PASS (7/7)** | SQLite WAL mode, dual portals, 100% offline static assets, error handlers, and persistence |
| `test_concurrency.py` | Concurrency & WAL Performance | **PASS (15/15)** | 15 concurrent student write operations committed without lock errors |
| `test_browser_phase3.py` | Playwright Edge Browser Audit | **PASS** | Complete end-to-end user journey (student submit -> teacher approve -> public catalogue -> privacy check) verified on Desktop (1280x800) and Mobile (390x844) viewports with **0 console errors and 0 page exceptions** |

### Stopping Point
- **Phase 3 – Book Donation System is 100% COMPLETE & VERIFIED.**

---

## 9. Phase 4 Implementation & Verification Results

**Implementation Status: COMPLETED & VERIFIED (2026-11-04)**

### Implemented Components
1. **Student Book Request Workflow (`/request` & `/request/<code_or_id>`):**
   - Clean, accessible request form pre-populating selected book details (title, code, class, subject, cover thumbnail).
   - Validation for student identifiers: Full Name, Class & Section (e.g. `Class 7-B`), Roll Number, and Contact phone.
   - Availability check preventing request submissions for non-existent or already-reserved/borrowed books.
   - Form rate limiting via sliding-window tracker (`RATE_LIMIT_REQUEST_PER_HOUR = 120`) suited for shared school Wi-Fi.
   - Session CSRF token validation on every submission.

2. **Cryptographically Secure Tracking Codes (`KB-REQ-XXXX-XXXX`):**
   - Every submitted request generates an unpredictable, high-entropy token (e.g. `KB-REQ-6248-3RWG`) via `secrets.choice()` using ambiguity-free alphanumeric characters (`2-9`, `A-Z` minus `0/O/1/I`).
   - SQLite `UNIQUE` constraint with collision retry loop guarantees zero duplicate tokens.

3. **Request Confirmation Screen (`/request/success/<tracking_code>`):**
   - Visual status badge: `⏳ Status: Awaiting Teacher Approval`.
   - Prominent tracking code display with one-click clipboard copy.
   - Summary of requested book and student details.
   - Guidance explaining the teacher review and reservation process.

4. **Public Request Tracking Desk (`/track`) & Strict PII Redaction:**
   - Real-time status lookup by tracking code (`KB-REQ-XXXX-XXXX`).
   - Visual progress timeline (`Request Submitted` → `Teacher Review` → `Approved & Book Reserved` → `Handed Over`).
   - **Strict Privacy & Anti-Harassment Redaction:**
     - Student full name is masked (`mask_student_name`, e.g., `Saad Rehman` → `Saad R***`).
     - Student roll number and phone number are **100% EXCLUDED** from the public response HTML.
     - Rate-limited lookup (`RATE_LIMIT_TRACK_PER_MINUTE = 30`) preventing token enumeration.

5. **Teacher Administrative Request Queue (`/teacher/requests`):**
   - Live badge counters and filter tabs: `Pending Review`, `Approved (Reserved)`, `Rejected`, `Handed Over`, and `All Records`.
   - Dynamic search by student name, roll number, tracking code, or book code/title.
   - Class grade dropdown filter (`Class 6`, `Class 7`, `Class 8`).
   - Detailed inspection page (`/teacher/requests/<id>`) displaying unmasked student information for verified handovers.

6. **Atomic Reservation Locking & Competing Request Policy:**
   - Implemented in `request_service.approve_request()`.
   - Runs in a single SQLite transaction with an immediate write lock (`BEGIN IMMEDIATE`).
   - Validates that request is still `pending` and book is still `available`.
   - Atomically transitions book status from `available` to `reserved` (`UPDATE books SET status = 'reserved'`).
   - Marks request as `approved`, recording reviewer ID, reviewer name, and review timestamp.
   - **Competing Request Auto-Resolution Policy:** When multiple students request the same physical textbook, approving one immediately closes all other pending requests for that book with `status = 'rejected'`, records a clear reason ("This copy was allocated to another student who requested earlier or was prioritized by teacher review. Please browse the school catalogue for other available copies."), and logs the closure. **Zero orphaned pending requests remain.**
   - **Race Condition & Double-Booking Defense:** Simultaneous approval attempts on the same book fail atomically because the book status is locked as `reserved` and competing requests are already transitioned out of `pending`.

7. **Duplicate Request Prevention by Same Student:**
   - When a student attempts to submit a second request for the same physical book (matched by class and roll number), the system blocks it with: `"You already have an active request (KB-REQ-...) for this textbook."`
   - Prevents accidental double submissions and student request spamming while allowing requests for different books.

8. **Strict Defense-in-Depth PII Redaction:**
   - On the student tracking desk (`/track`), the dictionary is actively sanitized before template rendering: `requester_roll_no`, `requester_contact`, `requester_name`, and `notes` are removed completely.
   - Only `masked_name` (e.g. `Saad R***`) is passed.

9. **Teacher Rejection Workflow (`/teacher/requests/<id>/reject`):**
   - Modal dialog with preset reasons ("Allocated to higher priority student", "Textbook quota exceeded", etc.) and custom reason input.
   - Marks request as `rejected`, records reason and teacher reviewer timestamp.
   - **Book remains `available`** for other students.
   - Rejection reason is safely displayed to the student on `/track`.

10. **Dynamic UI Synchronization:**
   - Teacher navigation bar badge dynamically reflects live pending request count via context processor.
   - Book detail page dynamically swaps CTA: displays active "Request This Book" button for available books, and a disabled "Currently Reserved" badge when reserved.
   - Direct `GET /request?book=...` for an unavailable book redirects to book detail with an explanatory flash message.

### Automated & Browser Test Verification Summary
| Test Suite | Scope | Result | Details |
|---|---|---|---|
| `tests/test_phase4.py` | Unit & Integration Suite | **PASS (14/14)** | Request form rendering, token generation, field validation, unavailable book guard, tracking lookup & PII masking, teacher auth guards on all endpoints, review queue & filtering, atomic approval & reservation locking, competing request auto-closure (0 orphaned requests), race-condition double-booking defense, teacher rejection workflow, duplicate approval guard, duplicate student request guard, rate limiting defense |
| `tests/test_phase3.py` | Phase 3 Unit Regression | **PASS (12/12)** | Book donation lifecycle and Pillow image processing |
| `tests/test_phase2.py` | Phase 2 Unit Regression | **PASS (12/12)** | Student catalogue discovery, search, and multi-faceted filtering |
| Full Test Suite (`tests/`) | Combined Test Suite | **PASS (38/38)** | 100% of unit and integration tests passing across all completed phases |
| `test_phase1.py` | Foundation & Security Regression | **PASS (7/7)** | SQLite WAL mode, dual portals, 100% offline static assets, error handlers, and persistence |
| `test_concurrency.py` | Concurrency & WAL Performance | **PASS (15/15)** | 15 concurrent student write operations committed without lock errors |
| `test_browser_phase2.py` | Phase 2 Playwright Audit | **PASS** | Desktop & Mobile viewports, multi-filter & search with **0 console errors and 0 page exceptions** |
| `test_browser_phase3.py` | Phase 3 Playwright Audit | **PASS** | Complete donation lifecycle, inspection & approval with **0 console errors and 0 page exceptions** |
| `test_browser_phase4.py` | Phase 4 Playwright Audit | **PASS** | Multi-student competing request submission, teacher review, atomic approval, auto-closure of competing request (0 orphaned requests), tracking desk privacy, and mobile viewport (390x844) with **0 console errors and 0 page exceptions** |

### Network & Wi-Fi LAN Access Note
- **Active Server Status:** Running via Waitress WSGI on `0.0.0.0:5000` with 6 worker threads.
- **Current Machine Wi-Fi IP:** `10.0.0.36` (DHCP lease renewed at 10:35 AM today on network `bbrouter`).
- **Connection Diagnostics:**
  - `Test-NetConnection -ComputerName 10.0.0.36 -Port 5000`: **TcpTestSucceeded = True** (Verified live).
  - `http://10.0.0.36:5000`: **HTTP 200 OK** (Verified responsive).
- **Current Active URLs:**
  - Local Host Computer: `http://127.0.0.1:5000` or `http://localhost:5000`
  - Mobile Phones & Other Devices on Same Wi-Fi: **`http://10.0.0.36:5000`**

### Stopping Point
- **Phase 4 – Book Request System & Atomic Reservation Lock is 100% COMPLETE & VERIFIED.**

---

## 7. Phase 5 Implementation & Verification Details

### Features Implemented
1. **Teacher Handover Confirmation Form (`/teacher/requests/<id>/handover`):**
   - Renders complete student verification profile (Student Name, Class & Section, Roll Number, Contact Number, Notes).
   - Displays textbook metadata snapshot (Title, Author, Code, Class, Condition).
   - **Mandatory Dual Verification Checkboxes:**
     - `confirm_id`: Certifies teacher verified student identity against school records / ID card.
     - `confirm_physical`: Certifies teacher physically inspected textbook and transferred custody.
     - Presentation of tracking code alone is strictly rejected.
   - Handover remarks / condition notes field.
   - Warning banner: Irreversible transaction note.

2. **Sequential Handover Ledger Reference Generation (`KB-HO-000001`):**
   - Implemented in `handover_service.generate_next_handover_code()`.
   - Format: `KB-HO-000001` to `KB-HO-999999` using six numeric digits.
   - Verified sequential generation and uniqueness.

3. **Atomic Handover Distribution Protection (`BEGIN IMMEDIATE`):**
   - Implemented in `handover_service.confirm_physical_handover()`.
   - Validates request is currently `approved` and book is currently `reserved`.
   - Inserts permanent snapshot record in `handovers` table (`handover_code`, `request_id`, `tracking_code`, `book_id`, `book_code`, `recipient_name`, `recipient_class`, `recipient_roll_no`, `recipient_contact`, `handed_over_by`, `teacher_name`, `remarks`, `status`).
   - Updates request `status = 'completed'`.
   - Updates book `status = 'handed_over'`.
   - Writes detailed transaction entry in `activity_logs`.
   - Strict race-condition and double-handover prevention via `request_id UNIQUE` constraint and transaction locking.

4. **Printable Distribution Receipt (`/teacher/handovers/<id>/receipt`):**
   - Formatted for official A4 printing with dedicated `@media print` CSS rules.
   - Includes School Name, Official Handover Code (`KB-HO-XXXXXX`), Request Tracking Code, Timestamp, Verifying Teacher Name.
   - Textbook metadata: Title, Book Code, Class, Condition.
   - Student recipient details: Name, Class, Roll Number, Contact.
   - Formal handover acknowledgment statement.
   - Dual signature boxes: Authorized Teacher & Student / Parent Recipient.
   - Access restricted to authenticated teachers (`@teacher_bp.before_request`).

5. **Historical Handover Ledger View (`/teacher/handovers`):**
   - Live metrics summary cards: Total Handovers Completed, Active Reservations Awaiting Pickup, Reused Books Counter.
   - Multi-field search filter (Handover Code, Student Name, Roll Number, Tracking Code, Book Code, Title).
   - Class level filter (`Class 6`, `Class 7`, `Class 8`).
   - Date range filters (`date_from`, `date_to`).
   - Direct link to detail view and printable receipts.

6. **Handover Audit Detail View (`/teacher/handovers/<id>`):**
   - Two-column layout with book cover, identifiers, and complete student recipient audit information.
   - Direct "Print Receipt" action.

7. **Reservation Cancellation / Release Control (`/teacher/requests/<id>/cancel-reservation`):**
   - Allows teachers to release an uncollected reservation back to circulation.
   - Transitions book `status = 'available'` in catalogue.
   - Transitions request `status = 'cancelled'` with teacher-entered reason.
   - Strictly blocked if physical handover has already been completed.

8. **Public Student Tracking Desk Synchronization (`/track`):**
   - Displays completed timeline step with green "Book Handed Over" badge.
   - Shows Handover Reference Code (`KB-HO-XXXXXX`) and Handover Date.
   - Zero PII Leakage: Student name masked (`Saad R***`), roll number and phone number completely stripped.
   - Reflects cancellation reasons if reservation is released.

### Automated & Browser Test Verification Summary
| Test Suite | Scope | Result | Details |
|---|---|---|---|
| `tests/test_phase5.py` | Unit & Integration Suite | **PASS (17/17)** | Handover workflow, unique code generation (KB-HO-000001), status guards, duplicate handover guard, double-distribution block, simultaneous handover race defense, identity checkbox mandate, physical handover checkbox mandate, student privacy on /track, teacher auth guards on all handover routes, receipt access protection, reservation cancellation & book availability restoration, post-handover cancellation block, transaction rollback |
| `tests/test_phase4.py` | Phase 4 Unit Regression | **PASS (14/14)** | Book request workflow, competing request resolution, reservation locking |
| `tests/test_phase3.py` | Phase 3 Unit Regression | **PASS (12/12)** | Book donation lifecycle and Pillow image processing |
| `tests/test_phase2.py` | Phase 2 Unit Regression | **PASS (12/12)** | Student catalogue discovery, search, and multi-faceted filtering |
| Full Test Suite (`tests/`) | Combined Test Suite | **PASS (55/55)** | 100% of unit and integration tests passing across all completed phases |
| `test_phase1.py` | Foundation & Security Regression | **PASS (7/7)** | SQLite WAL mode, dual portals, 100% offline static assets, error handlers, and persistence |
| `test_concurrency.py` | Concurrency & WAL Performance | **PASS (15/15)** | 15 concurrent student write operations committed without lock errors |
| `test_browser_phase5.py` | Phase 5 Playwright Audit | **PASS** | Desktop & Mobile viewports: Request -> Approval -> Physical Verification -> Handover Confirmation -> Ledger Audit -> Printable Receipt -> Public Tracking & Reservation Cancellation with **0 console errors and 0 page exceptions** |
| `test_browser_phase4.py` | Phase 4 Playwright Audit | **PASS** | Competing request submission & auto-closure with **0 console errors and 0 page exceptions** |
| `test_browser_phase3.py` | Phase 3 Playwright Audit | **PASS** | Complete donation lifecycle with **0 console errors and 0 page exceptions** |
| `test_browser_phase2.py` | Phase 2 Playwright Audit | **PASS** | Catalogue search & multi-filtering with **0 console errors and 0 page exceptions** |

### Network & Wi-Fi LAN Access Note
- **Active Server Status:** Running via Waitress WSGI on `0.0.0.0:5000` with 6 worker threads.
- **Current Machine Wi-Fi IP:** `10.0.0.36` (DHCP lease renewed at 10:35 AM today on network `bbrouter`).
- **Connection Diagnostics:**
  - `Test-NetConnection -ComputerName 10.0.0.36 -Port 5000`: **TcpTestSucceeded = True** (Verified live).
  - `http://10.0.0.36:5000`: **HTTP 200 OK** (Verified responsive).
- **Current Active URLs:**
  - Local Host Computer: `http://127.0.0.1:5000` or `http://localhost:5000`
  - Mobile Phones & Other Devices on Same Wi-Fi: **`http://10.0.0.36:5000`**

### Stopping Point
- **Phase 5 – Physical Handover Ledger & Circulation Defense is 100% COMPLETE & VERIFIED.**
- **Phase 6 (QR System, Label Printing & Android Tested Scanner) has NOT been started.** Awaiting instructions to proceed to Phase 6.
