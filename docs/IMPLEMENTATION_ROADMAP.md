# Detailed Implementation Roadmap & Milestone Plan
## Project: Kitaab Bank – Smart School Book Exchange (کتاب بینک)

---

## Roadmap Overview

Development follows a strict, sequential 10-phase execution model (Phase 0 through Phase 9). Each phase represents an atomic, verifiable milestone with clear deliverables and non-negotiable acceptance criteria. No phase begins until the preceding phase has been reviewed, tested, and marked complete in `docs/PROGRESS.md`.

```mermaid
flowchart TD
    P0["Phase 0: Project Planning & Architecture (IN REVIEW / UPDATED)"] --> P1["Phase 1: Foundation, WAL Concurrency & Dual-Portal Themes"]
    P1 --> P2["Phase 2: Student Discovery & Public Catalogue"]
    P2 --> P3["Phase 3: Book Donations, Pillow Pipeline & Review Queue"]
    P3 --> P4["Phase 4: Book Requests, Secure Tokens & Reservation Lock"]
    P4 --> P5["Phase 5: Physical Handover Ledger & Circulation Defense"]
    P5 --> P6["Phase 6: QR System, Label Printing & Android Tested Scanner"]
    P6 --> P7["Phase 7: Teacher Dashboard, Analytics & Themed Admin Desk"]
    P7 --> P8["Phase 8: Multilingual RTL, Hot Backups & Exhibition Mode"]
    P8 --> P9["Phase 9: Comprehensive QA, Multi-Device Hardening & Release"]
```

---

## Phase-by-Phase Execution Plan

### Phase 0 – Project Planning & Architecture (Current Phase)
- **Goal:** Establish a complete architectural blueprint, data model, security boundaries, and progress tracking framework without writing application code.
- **Key Deliverables:**
  - `docs/PRD.md` (Product Requirements Document)
  - `docs/ARCHITECTURE.md` (System Architecture, WAL Mechanics, Secure Context Scanner Constraints)
  - `docs/DATABASE_SCHEMA.md` (ERD, DDL, WAL Pragmas, Immediate Write Transactions)
  - `docs/SECURITY.md` (CSRF, Rate Limiting, Unpredictable Tokens, PII Masking, Hot Backups)
  - `docs/IMPLEMENTATION_ROADMAP.md` (Phase Breakdown & Acceptance Criteria)
  - `docs/PROGRESS.md` (Active Progress Tracking Document)
- **Acceptance Criteria:**
  - All 6 architectural documents updated in `docs/` incorporating WAL single-writer reality, mobile camera HTTPS constraints, CSRF, rate-limiting, and `madrasah_library` insights.
  - Zero application code written until Phase 0 sign-off.

---

### Phase 1 – Foundation, WAL Concurrency & Dual-Portal Themes
- **Goal:** Set up the Python Flask environment, SQLite database manager with WAL mode and short immediate transactions, base templates, CSRF protection, and the zero-FOUC Light/Dark/System theme system across both student and teacher portals.
- **Key Deliverables:**
  - `requirements.txt` with pinned versions (`Flask`, `waitress`, `Pillow`, `qrcode`).
  - `app/__init__.py` (Application Factory) and `app/database.py`:
    - SQLite connection manager with `PRAGMA journal_mode = WAL;`, `PRAGMA busy_timeout = 5000;`.
    - Short transaction helpers (`BEGIN IMMEDIATE`) and deadlock retry logic.
  - `app/schema.sql` containing initial DDL tables (`teachers`, `books`, `donations`, `requests`, `handovers`, `activity_logs`, `system_settings`, `backup_records`).
  - Base CSRF middleware and token generator for all state-changing requests.
  - `app/static/css/` core design tokens (`main.css`, `components.css`).
  - `app/static/js/theme.js` implementing Light / Dark / System Default modes with zero visual flash (FOUC).
  - Templates: `app/templates/base.html` (Student Portal) and `app/templates/teacher/base_teacher.html` (Teacher Dashboard), both featuring responsive theme toggles.
  - Verification scripts: `run_dev.py` and `run_server.py` (Waitress bound to `0.0.0.0:5000`).
- **Acceptance Criteria:**
  - Server starts on `0.0.0.0:5000` via Waitress.
  - SQLite database initializes with WAL mode verified (`PRAGMA journal_mode` returns `wal`).
  - CSRF validation is active on all POST requests.
  - Theme toggles seamlessly between Light, Dark, and System modes on **both** student and teacher base layouts without visual flash on reload.

---

### Phase 2 – Student Website: Discovery & Book Catalogue
- **Goal:** Build the public student-facing homepage, searchable catalogue, filtering system, and book details view with demonstration data.
- **Key Deliverables:**
  - `app/blueprints/student/routes.py` (`/`, `/catalogue`, `/book/<book_code>`, `/about`).
  - `app/services/book_service.py` (Querying, full-text subject/title search, filtering by Class 6–8, language, and condition).
  - Seed dataset (`app/seed_data.py`) with 12+ realistic school textbooks across subjects (Math, Science, English, Urdu, Sindhi, Computer).
  - Template views: `index.html` (Hero banner, live statistics counter, recent books), `catalogue.html` (responsive card grid with badges), and `book_detail.html`.
- **Acceptance Criteria:**
  - Homepage displays live counters pulled directly from SQLite.
  - Catalogue displays only approved books (`is_approved = 1` and `status = 'available'`).
  - Search and dropdown filters (Class, Subject, Language, Condition) work instantly.
  - Book detail view renders high-resolution cover photo and clear metadata.

---

### Phase 3 – Book Donations, Pillow Pipeline & Review Queue
- **Goal:** Enable students to submit unused books with configurable rate limiting and CSRF protection, and provide teachers with a dedicated queue to review, approve, or reject submissions.
- **Key Deliverables:**
  - Student donation form (`/donate`) with CSRF token and configurable IP rate limiting (default 120/hour for shared school Wi-Fi).
  - Image upload handler (`app/services/image_service.py`) with 800px resizing, WebP re-encoding, and EXIF stripping.
  - Unique donation reference generator (`KB-DON-XXXX-XXXX`).
  - Teacher authentication portal (`/auth/login`, `/auth/logout`) with PBKDF2 hashing and rate limiting (max 5 failed attempts/15min).
  - Teacher donation desk (`/teacher/donations`) with side-by-side inspection, approval (promotes to `books` catalogue with standardized six-digit code `KB-BK-000001`), and rejection with reason.
- **Acceptance Criteria:**
  - Submitting a donation generates a valid reference code and stores sanitized images.
  - Rate limiting supports simultaneous classroom submissions from shared school Wi-Fi NAT.
  - Unapproved donations **never** appear in the public catalogue.
  - Approving a donation creates a corresponding `books` record with format `KB-BK-000001`.

---

### Phase 4 – Book Requests, Secure Tokens & Reservation Lock
- **Goal:** Allow students to request available books, generate cryptographically secure unpredictable tracking tokens with database uniqueness and collision handling, and enable teachers to approve and reserve books without race conditions.
- **Key Deliverables:**
  - Book request form (`/request?book=<id>`) with CSRF token and configurable rate limiting (default 120/hour for shared school Wi-Fi).
  - Secure tracking code generator using Python `secrets` (`KB-REQ-XXXX-XXXX`) with database uniqueness constraint and retry-on-collision loop.
  - Student tracking page (`/track`) with configurable rate limiting (default 30/min) and PII redaction (masked student name, zero phone/roll number exposure).
  - Teacher request management queue (`/teacher/requests`).
  - Atomic reservation lock (`BEGIN IMMEDIATE` with `status = 'available'` check) preventing concurrent claiming of the same book.
- **Acceptance Criteria:**
  - A student can request an available book and receive an unpredictable tracking token.
  - Database collision handling verified: guarantees uniqueness even across thousands of submissions.
  - Simultaneous requests from multiple devices sharing one school Wi-Fi NAT succeed without false rate-limit rejections.
  - Atomic reservation prevents double-booking if multiple devices submit requests simultaneously.
  - Tracking lookup is rate-limited to prevent code enumeration.
  - Student phone numbers and roll numbers are completely redacted on `/track`.

---

### Phase 5 – Physical Handover Ledger & Circulation Defense (COMPLETED & VERIFIED)
- **Goal:** Provide teachers with a physical collection verification desk to record handovers and log completed reuse events.
- **Key Deliverables:**
  - Teacher handover interface (`/teacher/handovers`).
  - Verification modal & dedicated handover confirmation form (`/teacher/requests/<id>/handover`).
  - Mandatory dual-verification checkboxes (`confirm_id`, `confirm_physical`). Presentation of tracking code alone is strictly rejected.
  - Atomic handover transaction (`BEGIN IMMEDIATE`): Inserts immutable snapshot record into `handovers` with sequential code `KB-HO-000001`, updates request to `completed`, updates book to `handed_over`, and creates structured audit activity log.
  - Historical handover ledger with multi-field search, class filter, and date filtering.
  - Printable distribution receipt (`/teacher/handovers/<id>/receipt`) formatted for A4 printing (`@media print`) with dual signature lines.
  - Reservation release action (`/teacher/requests/<id>/cancel-reservation`) returning uncollected book to `available` in catalogue, blocked after handover.
  - Public student tracking desk (`/track`) updated with completed timeline status, handover reference, date, and zero PII leakage.
- **Acceptance Criteria (VERIFIED):**
  - Unique constraint on `handovers.request_id` and atomic check strictly prevent double handover.
  - Completed exchange updates public reuse metrics in real-time.
  - Handover log captures timestamp, teacher ID, recipient details, and activity log.
  - 17 unit/integration tests (`tests/test_phase5.py`) and full browser audit (`test_browser_phase5.py`) passing with 0 console errors and 0 page exceptions.

---

### Phase 6 – QR System, Label Printing & Android Tested Scanner (COMPLETED & VERIFIED)
- **Goal:** Enable offline QR code generation for physical book labeling, printable sticker sheets, and an in-browser scanner with graceful Secure Context fallback.
- **Key Deliverables:**
  - Local QR generator (`app/services/qr_service.py`) generating PNG matrix / data URI encoding relative book URL (`/book/<book_code>`).
  - Printable sticker template (`/teacher/books/<code_or_id>/qr` and bulk print `/teacher/qr-sheet`) styled with `@media print` adapted from `madrasah_library` label standards with zero margin printing.
  - Scanner page (`/scan`) featuring:
    - Prominent manual 6-digit Book Code entry (`KB-BK-000001`) with quick-select sample chips and autofocus.
    - Secure Context detection (`window.isSecureContext || localhost || 127.0.0.1`).
    - Camera scanner using HTML5 video with `playsinline`, `muted`, BarcodeDetector API with local `jsQR` canvas fallback, and hardware stream teardown (`track.stop()`) on modal close, pagehide, and visibilitychange.
    - Educational notification banner explaining camera security policies over plain HTTP Wi-Fi, seamlessly steering students to manual 6-digit lookup.
- **Acceptance Criteria (VERIFIED):**
  - Printable sheet formats cleanly to paper/PDF with sharp QR codes and standardized 6-digit Latin book codes (`KB-BK-000001`).
  - Scanning tested and verified on actual physical Android devices:
    - Under plain HTTP LAN: Gracefully detects insecure context and falls back to manual entry.
    - Under HTTPS: Activates camera, decodes QR, and redirects to book page.
  - Manual code input immediately normalizes codes and navigates to the corresponding book or tracking desk.
  - 14 unit/integration tests (`tests/test_phase6.py`) and full browser audit (`test_browser_phase6.py`) passing with 0 console errors and 0 page exceptions.

---

### Phase 7 – Teacher Dashboard, Analytics & Themed Admin Desk (READY TO START)
- **Goal:** Build a complete teacher administrative dashboard with live analytics, full book inventory CRUD, and audit activity logging.
- **Key Deliverables:**
  - Dashboard overview (`/teacher/dashboard`) with dynamic cards (Total Donated, Available, Reserved, Reused, Pending Actions).
  - Breakdown charts/tables: Most requested subjects, class-wise distribution (Grades 6, 7, 8), monthly trends.
  - Inventory manager (`/teacher/inventory`) to directly add school books, edit details, or retire damaged books.
  - System activity log (`/teacher/logs`) recording teacher actions.
  - Full theme compliance: Verifying Light, Dark, and System Default themes across all admin screens, modals, and data tables.
- **Acceptance Criteria:**
  - All dashboard metrics calculate from real SQLite records with zero fabricated data.
  - Teachers can edit book details or retire books with proper status updates.
  - Audit log captures donations, approvals, requests, and handovers.
  - Theme switching works flawlessly in the teacher portal.

---

### Phase 8 – Multilingual RTL, Live Snapshot Backups & Exhibition Mode
- **Goal:** Implement full bilingual / trilingual localization (English, Urdu اردو, Sindhi سنڌي) with RTL support, Python SQLite consistent live snapshot backup and restoration verification tools, and exhibition showcase mode.
- **Key Deliverables:**
  - JSON translation dictionaries (`en.json`, `ur.json`, `sd.json`) and template translation helper `_t('key')` preserving Latin digits in codes.
  - RTL stylesheet (`rtl.css`) dynamically applied when Urdu or Sindhi is selected.
  - Language switcher in student and teacher navbars.
  - Built-in SQLite Hot Backup Engine (Consistent Live Snapshot) using `sqlite3.Connection.backup()`:
    - Dedicated backup route (`/teacher/settings/backup`).
    - Automated backup validation check (`PRAGMA integrity_check;` and schema verification).
    - Safe restoration script (`scripts/restore_backup.py`) with pre-restore rollback snapshot and verification test.
  - Exhibition Demo Seeder: One-click script to reset and seed clean exhibition demo data in < 2 seconds.
- **Acceptance Criteria:**
  - UI language switches instantly without losing theme preference.
  - Right-to-Left (RTL) typography renders correctly for Urdu and Sindhi text.
  - Hot database backup produces a verified, consistent live snapshot `.db` file in `/backups/`.
  - Restore procedure successfully restores data with verified integrity after test simulation.

---

### Phase 9 – Comprehensive QA, Multi-Device Hardening & Release
- **Goal:** Rigorous end-to-end testing across multiple physical devices on local Wi-Fi, ngrok verification, performance audits, and release packaging.
- **Key Deliverables:**
  - Multi-device verification (Host PC + Android phone + iPhone connected to local Wi-Fi).
  - ngrok tunnel validation (`run_tunnel.py`) with `X-Forwarded-For` header check.
  - Automated test suite covering auth, CSRF, rate limits, donation approval, atomic reservation lock, and double-handover defense.
  - User documentation and teacher quick-start guide (`docs/TEACHER_GUIDE.md`).
- **Acceptance Criteria:**
  - Zero external CDN dependencies (browser network tab verifies 0 external network requests).
  - Multi-device concurrent operations execute cleanly without SQLite locking errors.
  - Camera scanning verified on physical Android device via HTTPS tunnel; manual code fallback verified via HTTP LAN.
  - All tests pass; all acceptance criteria across all phases verified.
