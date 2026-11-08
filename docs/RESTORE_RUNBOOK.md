# Kitaab Bank — Disaster Recovery & Database Restoration Runbook

> **Target Audience:** School System Administrators, IT Coordinators, and Teacher In-Charge  
> **Platform:** Windows 10/11 (PowerShell / Command Prompt)  
> **Scope:** Safe point-in-time database restoration, crash recovery, and stale lock remediation  

---

## 1. Quick Emergency Reference

In the event of accidental data corruption, failed migration, or hardware disruption:

| Situation | Recommended Action |
|---|---|
| **Restore from latest verified backup** | Stop server (Ctrl+C) &rarr; Run `python scripts/restore_backup.py --latest` &rarr; Restart server. |
| **Restore from specific snapshot file** | Stop server (Ctrl+C) &rarr; Run `python scripts/restore_backup.py --file <filename>` &rarr; Restart server. |
| **App crashed mid-restore (power cut)** | Simply restart the application. Built-in ownership-aware recovery automatically restores the pre-restore rollback snapshot. |
| **App stuck in 503 Maintenance Mode** | Ensure no active restore is running &rarr; Restart server. Startup checks process liveness and cleans stale locks automatically. |
| **Exiting Exhibition Showcase Mode** | Use the Web UI: Go to **Teacher Settings > Exhibition Showcase Mode** &rarr; Click **Exit Demo & Restore Real Data**. |

---

## 2. Standard CLI Restoration Procedure

Kitaab Bank includes a built-in cross-process safety guard that prevents running CLI restore while the Waitress web server is actively handling requests.

### Step 1: Gracefully Stop the Web Server
On the host computer:
1. Locate the running server console window (titled `Kitaab Bank - Smart School Book Exchange`).
2. Press `Ctrl + C` to stop Waitress.
3. Verify the console has stopped.

### Step 2: List Available Verified Backups
Open PowerShell or Command Prompt in the project directory:
```powershell
.venv\Scripts\activate
python scripts/restore_backup.py --list
```
Sample output:
```text
======================================================================
AVAILABLE KITAAB BANK BACKUPS
======================================================================
[1] kitab_bank_backup_20261108_120000.db  (516.0 KB) - 2026-11-08 12:00:00
[2] kitab_bank_backup_20261107_160000.db  (512.0 KB) - 2026-11-07 16:00:00
[3] kitab_bank_backup_20261106_160000.db  (508.0 KB) - 2026-11-06 16:00:00
======================================================================
```

### Step 3: Execute Restoration
To restore the most recent verified backup:
```powershell
python scripts/restore_backup.py --latest
```

Or to restore a specific historical snapshot:
```powershell
python scripts/restore_backup.py --file kitab_bank_backup_20261107_160000.db
```

### Step 4: Verification Performed by the Tool
The restore tool executes the following automated safety pipeline:
1. **Target Integrity Check:** Validates SQLite structure (`PRAGMA integrity_check`) and verifies all essential schema tables exist (`books`, `students`, `inventory`, `book_requests`, `users`, `backup_records`).
2. **Maintenance Gate Acquisition:** Writes `.maintenance_lock` with the active PID.
3. **Emergency Pre-Restore Snapshot:** Captures `backups/pre_restore_<timestamp>.db` from the current live database.
4. **Crash Resilience Marker:** Writes `.restore_in_progress` containing metadata and the rollback snapshot path.
5. **Page Copy & WAL Truncation:** Transfers database pages and flushes WAL (`PRAGMA wal_checkpoint(TRUNCATE);`).
6. **Backup Catalog Merge:** Automatically merges recent backup records into the restored database so newer snapshots remain discoverable.
7. **Post-Restore Integrity Validation:** Runs `PRAGMA integrity_check` on the newly written live database.
8. **Marker Clearance:** Deletes `.restore_in_progress` and releases `.maintenance_lock`.

### Step 5: Restart the Server
Once the tool reports:
```text
[SUCCESS] Live database successfully restored and verified.
```
Restart the server using:
```powershell
start_kitaab_bank.bat
```
Open `http://127.0.0.1:5000` in the browser and confirm the catalogue and inventory display the expected data.

---

## 3. Ownership-Aware Crash Recovery (Power Cut Mid-Restore)

If power is suddenly lost or the host machine reboots during a restoration:
- The live database file (`kitaab_bank.db`) may have partial or corrupted pages.
- The `.restore_in_progress` marker file and `backups/pre_restore_*.db` snapshot remain on disk.

### Automated Recovery Mechanism
1. On next launch, `create_app()` runs `check_and_recover_interrupted_restore(app)` **before** opening the database or binding network ports.
2. The system checks the process ID (PID) recorded in `.restore_in_progress`:
   - On Windows: Uses native Win32 APIs (`OpenProcess`, `GetExitCodeProcess`) to verify process liveness.
   - On POSIX: Uses `os.kill(pid, 0)`.
3. If the recorded owner PID has exited (process is dead):
   - Validates the integrity of the rollback snapshot.
   - Restores `kitaab_bank.db` from the pre-restore rollback snapshot.
   - Truncates the WAL.
   - Validates `PRAGMA integrity_check;`.
   - Clears `.restore_in_progress` and `.maintenance_lock`.
   - Logs: `[INFO] Interrupted restore recovery completed successfully.`
4. If the recorded owner PID is still active:
   - **Fails Closed:** The new process aborts startup (`RuntimeError`) rather than touching or overwriting a database that an active process is currently writing.

---

## 4. Stale Maintenance Lock Remediation

If a restore process crashed **after** acquiring `.maintenance_lock` but **before** modifying database pages:
- `.maintenance_lock` remains on disk.
- `.restore_in_progress` does **not** exist (no pages were altered).

### How the System Resolves This
On application startup, `check_and_recover_interrupted_restore(app)`:
1. Detects `.maintenance_lock` without `.restore_in_progress`.
2. Inspects the owner PID recorded in the lock file payload (`MAINTENANCE_ACTIVE:<timestamp>:PID:<pid>`).
3. Verifies that the recorded owner process has exited.
4. Safely removes the stale `.maintenance_lock` file.
5. Logs: `[WARNING] Removed stale maintenance gate left before restore mutation.`
6. The application boots normally and does **not** remain trapped in HTTP 503 maintenance mode.

---

## 5. Manual Emergency Recovery (Cold Standby Fallback)

In extreme edge cases where the automated script cannot execute (e.g., Python runtime damaged):

1. **Locate the Backups Directory:** Open `D:\My Folder\My Work\Kitab Dost\backups\`.
2. **Identify the Best Snapshot:** Look for the latest verified snapshot, e.g. `kitab_bank_backup_YYYYMMDD_HHMMSS.db` or `emergency_pre_restore_snapshot.db`.
3. **Verify File Size:** Confirm the snapshot file is non-empty (typically 500 KB+).
4. **Backup Existing Damaged File:** Rename `kitaab_bank.db` to `kitaab_bank_damaged_<timestamp>.db`.
5. **Remove Stale Markers:** Delete `.maintenance_lock` and `.restore_in_progress` if present.
6. **Copy Snapshot to Live DB:** Copy your chosen snapshot file and rename the copy to `kitaab_bank.db`.
7. **Clean Stale WAL Files:** Delete `kitaab_bank.db-wal` and `kitaab_bank.db-shm` if they exist.
8. **Test with SQLite CLI or Python:**
   ```powershell
   python -c "import sqlite3; c=sqlite3.connect('kitaab_bank.db'); print(c.execute('PRAGMA integrity_check;').fetchone()[0])"
   ```
   Must output: `ok`.
9. **Start Server:** Launch `start_kitaab_bank.bat`.
