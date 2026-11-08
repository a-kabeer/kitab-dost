# Kitaab Bank — Production Release & Deployment Checklist

> **Purpose:** Pre-flight technical verification, security sign-off, and operational handoff checklist before putting Kitaab Bank into live school use.

---

## 1. Environment & Configuration Security Checklist

- [ ] **`.env` Configuration File:**
  - [ ] `.env` created from `.env.example` in the project root.
  - [ ] `.env` is confirmed in `.gitignore` and **not** tracked by Git (`git status` shows clean).
- [ ] **Secret Key (`SECRET_KEY`):**
  - [ ] Generated using `python -c "import secrets; print(secrets.token_hex(32))"`.
  - [ ] Stable 64-character hex key saved in `.env` (prevents cookie invalidation on server restart).
- [ ] **Initial Teacher Password (`INITIAL_TEACHER_PASSWORD`):**
  - [ ] Customized in `.env` or set in host environment (not default `Teacher@123`).
  - [ ] Enforces minimum 8 characters, uppercase, lowercase, number, and special character.
  - [ ] Mandatory password rotation on initial login verified (`/teacher/settings?tab=security`).
- [ ] **Rate Limiting Policies:**
  - [ ] `RATE_LIMIT_LOGIN_FAILURES` set to `5` per 15-minute window (`RATE_LIMIT_LOGIN_WINDOW_SECONDS=900`).
  - [ ] Donation and Request rate limits configured to accommodate school classroom sizes (`120/hr`).
- [ ] **School Branding:**
  - [ ] `SCHOOL_NAME` set correctly in `.env` and confirmed on the student portal header.

---

## 2. Infrastructure & Network Checklist

- [ ] **Python Runtime & Virtual Environment:**
  - [ ] Python 3.10+ installed and 64-bit architecture verified.
  - [ ] Virtual environment `.venv` active with all dependencies from `requirements.txt` installed.
- [ ] **Host IP & School Wi-Fi:**
  - [ ] Host computer assigned a static IP or DHCP router reservation (e.g. `192.168.100.14`).
  - [ ] Wi-Fi router / Access Point operational and covers the library/classrooms.
- [ ] **Windows Defender Firewall Rule:**
  - [ ] Inbound TCP rule for Port 5000 enabled for Private/Domain profiles.
  - [ ] Client smartphones and student laptops can browse `http://<HOST_IP>:5000/catalogue`.
- [ ] **Zero-Cloud Air-Gap Verification:**
  - [ ] Disconnected host from external internet and verified that Bootstrap CSS, FontAwesome icons, Urdu fonts, and book covers load 100% locally with zero CDN errors.

---

## 3. Database & Data Integrity Checklist

- [ ] **SQLite WAL Mode:**
  - [ ] Database initialized at `kitaab_bank.db` with `PRAGMA journal_mode=wal;`.
  - [ ] Foreign keys enabled (`PRAGMA foreign_keys=ON;`).
- [ ] **Schema & Seeds:**
  - [ ] All tables created (`books`, `students`, `inventory`, `book_requests`, `users`, `backup_records`, `activity_logs`, `settings`).
  - [ ] Curriculum textbooks seeded or verified in catalogue.
- [ ] **Stored XSS Elimination:**
  - [ ] Verified that book titles and student names with `<script>` or HTML tags are strictly escaped in activity logs.
- [ ] **Atomic Book Reservation:**
  - [ ] Verified that simultaneous requests for the last remaining available copy cannot double-allocate.

---

## 4. Backup & Disaster Recovery Checklist

- [ ] **Live Backup Verification:**
  - [ ] Executed `backup_now.bat`; verified snapshot appears in `backups/`.
  - [ ] Tested Teacher Desk backup creation (`/teacher/settings?tab=backup`).
  - [ ] SHA-256 checksum and `PRAGMA integrity_check` verified as `VALID`.
- [ ] **Automated Daily Backup Schedule:**
  - [ ] Windows Task Scheduler job `KitaabBank_DailyBackup` configured to run daily at 4:00 PM.
  - [ ] Task Scheduler history confirms successful unattended execution.
- [ ] **Offsite / USB Backup Routine:**
  - [ ] Designated school USB flash drive identified for weekly offline snapshots.
- [ ] **Restoration Runbook Drill:**
  - [ ] Stopped Waitress; verified `scripts/restore_backup.py --list` displays snapshots.
  - [ ] Restored a test backup using `scripts/restore_backup.py --latest` and confirmed data integrity.
  - [ ] Restarted Waitress; verified catalogue loads correctly.

---

## 5. Startup & High-Availability Checklist

- [ ] **Host Startup Automation (Choose One):**
  - [ ] **Option A (Desktop):** Shortcut to `start_kitaab_bank.bat` on the Teacher/Librarian desktop.
  - [ ] **Option B (Windows Startup):** Batch shortcut placed in `shell:startup`.
  - [ ] **Option C (Task Scheduler):** Task created to run `run_server.py` at system boot.
  - [ ] **Option D (Windows Service):** Service installed using NSSM (`nssm install KitaabBank`).
- [ ] **Crash Resilience & Ownership Recovery:**
  - [ ] Confirmed that startup safely clears stale maintenance locks if previous process died.
  - [ ] Confirmed that startup automatically recovers from rollback snapshot if interrupted mid-restore.

---

## 6. Staff Training & Operational Handoff

- [ ] **Teacher Administrator Login:**
  - [ ] Teacher logged in, successfully changed initial password, and noted recovery procedures.
- [ ] **QR Code Verification:**
  - [ ] Printed QR codes tested with smartphone cameras; opens `http://<HOST_IP>:5000/catalogue` directly.
- [ ] **Exhibition Showcase Mode Demonstrated:**
  - [ ] Demonstrated entering Demo Mode for school fairs and safely exiting back to real school data.
- [ ] **Documentation Delivered:**
  - [ ] `docs/DEPLOYMENT_GUIDE.md` and `docs/RESTORE_RUNBOOK.md` printed or saved on the desktop.

---

### Sign-Off & Approval

| Role | Name | Signature | Date |
|---|---|---|---|
| **Deploying Engineer / IT Lead** | ________________________ | ____________________ | ____________ |
| **Teacher In-Charge / Librarian** | ________________________ | ____________________ | ____________ |
| **School Headmaster / Principal** | ________________________ | ____________________ | ____________ |
