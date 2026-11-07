# Kitaab Bank — Source Audit Report

**Audit date:** 7 November 2026  
**Repository:** `a-kabeer/kitab-dost`  
**Audited baseline:** `main` at `e5a7db7735e07aab5bc87e4531106b6b1a5af575`  
**Fix branch:** `audit/critical-security-integrity-fixes`

## 1. Scope and verification boundary

This was a static source-code audit of the GitHub repository: Flask application factory, authentication and teacher/student routes, SQLite schema and database helper, domain services, templates, backup/restore tools, tests, and project documentation.

The audit branch contains proposed fixes and regression tests. It has **not** been merged into `main`.

The project could not be executed on the developer's Windows computer from this audit environment. Runtime behavior on the school LAN, browser/device compatibility, camera permissions, Windows file locking, power-loss recovery, and visual UI acceptance therefore remain to be confirmed. The GitHub Actions regression workflow was added and triggered; its result must be read from the run linked below rather than inferred from the fact that it was queued.

## 2. Findings addressed on the audit branch

| Priority | Finding in the baseline | Change made |
|---|---|---|
| Critical | Activity-log details were rendered with Jinja `|safe`, while log details can contain book titles, donor names, teacher names, and other user-controlled text. | Escaped captured values in the English, Urdu, and Sindhi activity-log formatter; only application-owned translation markup is trusted. |
| High | `record_activity()` called `commit()` unconditionally, even when a business operation already owned a transaction. | The logger now commits only when it did not join an open caller transaction. |
| High | `db_transaction()` could retry the caller's transaction body after a lock error. | Retry is limited to acquiring `BEGIN IMMEDIATE`; the business operation is never replayed. |
| High | Student request creation checked book availability before entering the write transaction, leaving a race with teacher reservation. | Availability and approval are checked again while holding the SQLite write lock. |
| High | Maintenance drain held the shared state lock while waiting, preventing incoming requests from registering promptly. | The lock is held only while establishing the gate; new dynamic requests can now register and receive maintenance response. |
| High | Maintenance marker writes and reads failed open or swallowed file-system errors; simultaneous processes could race to establish the gate. | Gate acquisition uses exclusive file creation; marker writes are atomic; uncertain gate state fails closed. |
| High | Interrupted restore recovery was only checked on the new-database initialization path. | Recovery is checked before opening an existing or new live database; startup aborts if recovery cannot be verified. Successful recovery also clears a stale maintenance marker. |
| High | Restore accepted a caller-supplied filename/path without requiring the exact catalogued backup and did not consistently verify the catalogued checksum. | Restore requires a safe filename, a catalogue record, and the catalogue's recorded checksum. Path traversal and a caller-supplied checksum override are rejected. |
| High | Restore rollback could run after the maintenance context released its gate, and SQLite handles were not consistently closed on exception paths. | Restore is refactored so rollback and verification happen before releasing maintenance. If rollback fails, the restore marker is retained and the running process remains gated. SQLite handles are closed deterministically. |
| High | Backup integrity checks and hot-backup handles could be left open on early returns or exceptions. | Validation and hot-backup connections close deterministically; only verified snapshots are catalogued as `VALID`. Partial/untracked snapshots are cleaned up. |
| High | Login rate-limit setting existed in config/docs but was not enforced by the login route. | Failed login attempts are limited to 5 per 15-minute window by default. The limiter is thread-safe and only trusts forwarded IPs from configured proxy peers. |
| High | The public bootstrap password was not actually restricted to first-login password rotation. | Login with the configured initial password is limited to the Security tab and password-change route, including sessions that pre-date this patch. |
| Medium | Teacher inventory cover uploads trusted only an allowed extension, not the decoded image format. | Actual image format is checked and the image is verified/reopened before re-encoding. |
| High | A legacy `handovers` table without `handover_code` was dropped during startup. | The old table is renamed to a collision-safe `handovers_legacy*` table so history is preserved. It is not automatically mapped into the new schema. |
| Medium | Several test configurations used the development/default database path or created an app before redirecting it to a temporary path. | Added an explicit isolated `testing` config and changed selected suites to use it. |
| Medium | Security and deployment documentation described controls/routes that did not match the code, and the deployment guide referenced a nonexistent import path. | Corrected security claims, the database initialization import, backup/restore UI instructions, and added a root README. Rewrote architecture notes to reflect the current Flask blueprints/services. |

## 3. Regression coverage added

`tests/test_security_integrity_regressions.py` now covers:

1. Activity-log HTML escaping in English, Urdu, and Sindhi.
2. Activity logging preserving a caller-owned transaction and rolling back with it.
3. Transaction bodies not being replayed after an operational lock error.
4. Rechecking book availability inside the write transaction.
5. New requests registering and observing the maintenance gate while restore is active.
6. Recovery of an existing live database from an interrupted-restore marker.
7. Forced initial-password rotation before Teacher Desk access.
8. Failed-login throttling.
9. Rejection of non-image content uploaded with an allowed extension.
10. Rejection of path-traversal backup filenames.

The GitHub Actions workflow `.github/workflows/audit-regressions.yml` runs Python compilation and these targeted regressions on branch pushes and pull requests to `main`.

**Test status:** do not treat these tests as passed until the linked GitHub Actions run reports success. The full historical test suite, browser automation and live Windows/LAN tests have not yet been independently run.

## 4. Important remaining work / decisions

### A. Legacy handover migration

The branch preserves an incompatible legacy `handovers` table by renaming it to `handovers_legacy*`. This avoids data loss, but does not translate those historical rows into the current `handovers` model. Before removing any archived table, inspect its columns and data, define a mapping, and verify row counts and relationships.

### B. Versioned database migrations

The code still uses startup schema execution and a small set of ad-hoc column checks rather than a formal, versioned migration system. Existing database variants should be inventoried before a production schema upgrade is approved.

### C. Deployment secrets and first login

For a fresh deployment, set stable, random `SECRET_KEY` and strong `INITIAL_TEACHER_PASSWORD` environment variables before starting the app. Do not commit them to this public repository. The default value `Teacher@123` remains a documented bootstrap fallback, but sessions using it are now constrained to password rotation. Existing installations must confirm which password hash is already stored before changing the configured bootstrap password.

### D. Rate limiter scope

The limiter is process-local and resets when the server restarts. It is suitable for the current single-process Waitress setup, but it is not a shared store for a future multi-process or multi-host deployment. Configure `TRUSTED_PROXY_IPS` only when a known reverse proxy is used and its forwarding headers are controlled.

### E. Manual operational checks still required

- Start the app on Windows with the actual school database and verify no production data is reseeded or changed unexpectedly.
- Generate a backup, validate its checksum/catalogue entry, restore it to a disposable copy, and compare key table counts.
- Simulate a failed restore and confirm rollback plus marker cleanup.
- Test recovery from a deliberately interrupted restore using a disposable database, not the live school database.
- Test camera QR scanning on Android over HTTPS and confirm manual-entry fallback on plain HTTP LAN.
- Recheck responsive layouts, keyboard navigation, screen-reader semantics, and clickable catalogue-card behavior in real browsers.
- Confirm no actual credentials or tokens are embedded in text/code before continuing to keep the repository public.

## 5. Module boundary

This audit concerns the existing student book-exchange application only. The separately discussed bulk government textbook stock/distribution module is not implemented or included in this branch.

## 6. Branch and review

The audit branch is intentionally separate from `main`. Review the code and CI result before merging. Do not deploy the branch to the live school host until regression checks and the manual data-recovery tests above have passed.
