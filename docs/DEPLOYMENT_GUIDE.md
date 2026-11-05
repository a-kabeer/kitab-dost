# Kitaab Bank — Local Deployment & Operations Guide

> **100% Offline, Self-Hosted School Book Exchange Platform**  
> *Flask · SQLite (WAL Mode) · Waitress Production WSGI · Multi-Device Wi-Fi LAN*

---

## 1. System Requirements & Architecture Overview

Kitaab Bank operates completely offline on local school hardware without any dependency on external cloud providers, CDNs, or external internet access.

| Component | Minimum Specification | Recommended Specification |
| :--- | :--- | :--- |
| **Host Computer** | Dual-core CPU, 4 GB RAM, Windows 10/11 or Ubuntu 20.04+ | Quad-core CPU, 8 GB RAM, SSD Storage |
| **Python Runtime** | Python 3.10, 3.11, or 3.12 | Python 3.11 or 3.12 64-bit |
| **Network** | School Wi-Fi Router or Ethernet Switch | Dedicated Wi-Fi Access Point in School Library |
| **Client Devices** | Smartphones (Android/iOS) or PCs with any modern browser | Chrome, Edge, Safari, Firefox |
| **Storage** | 500 MB free disk space (covers database and local backups) | 2 GB free disk space |

---

## 2. Installation & First-Time Setup

### Step 2.1 — Clone or Copy the Repository
Place the `Kitaab Bank` project folder on the host computer (e.g., `D:\Kitaab Bank` or `C:\Schools\Kitaab Bank`).

### Step 2.2 — Create Python Virtual Environment
Open PowerShell or Command Prompt in the project folder:
```powershell
python -m venv .venv
```

### Step 2.3 — Activate Virtual Environment & Install Dependencies
```powershell
.venv\Scripts\activate
pip install -r requirements.txt
```
*(In strictly air-gapped environments without initial internet access, pre-downloaded wheel files in a `wheels/` directory can be installed using `pip install --no-index --find-links=wheels -r requirements.txt`)*

### Step 2.4 — Database Initialization & First Teacher Account
The database initializes automatically in SQLite WAL mode on first application launch. If initializing explicitly or resetting:
```powershell
python -c "from app import create_app; from app.services.database import init_db; app = create_app(); init_db(app)"
```
Initial teacher administrator credentials:
- **Username:** `teacher`
- **Default Password:** `Teacher@123`  *(Rotate immediately via Teacher Settings > Account Security)*

---

## 3. Running in Production via Waitress

Kitaab Bank uses **Waitress**, a pure-Python production-quality multi-threaded WSGI server that handles concurrent connections robustly on Windows and Linux.

### Method A — Double-Click Batch Launcher (Recommended for Windows)
Simply double-click:
```
start_kitaab_bank.bat
```
This launcher:
1. Validates the Python environment.
2. Identifies your host machine's Wi-Fi / LAN IP address.
3. Automatically opens your default web browser to `http://127.0.0.1:5000`.
4. Starts Waitress on `0.0.0.0:5000` listening on all network interfaces.

### Method B — Command Line Execution
```powershell
.venv\Scripts\python.exe run_server.py
```

Console output displays:
```
================================================================
 KITAAB BANK - SMART SCHOOL BOOK EXCHANGE (کتاب بینک)
 Production Local Server (Waitress WSGI)
================================================================
 Local Machine:  http://127.0.0.1:5000
 School Wi-Fi:   http://192.168.100.14:5000  <-- Open this on mobile phones
----------------------------------------------------------------
 Operating Mode: 100% Offline (Zero external cloud/CDN dependencies)
 Database:       SQLite with Write-Ahead Logging (WAL)
================================================================
 Server is listening... Press Ctrl+C to stop.
```

---

## 4. School Network & Windows Firewall Configuration

To allow students and staff on the school Wi-Fi network to access Kitaab Bank from their mobile devices and library laptops, port 5000 must be allowed through the Windows Defender Firewall.

### Adding Windows Firewall Inbound Rule (Run PowerShell as Administrator)
```powershell
New-NetFirewallRule -DisplayName "Kitaab Bank Local Server (Port 5000)" `
    -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow `
    -Profile Domain,Private -Description "Allows students and teachers on school Wi-Fi to access Kitaab Bank."
```

### Determining Your Host Computer's Wi-Fi IP
If the router IP changes, run in PowerShell:
```powershell
(Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -notmatch 'Loopback|vEthernet|Virtual' -and $_.IPAddress -notlike '169.254*' } | Select-Object -First 1).IPAddress
```
Or check the startup console banner of `start_kitaab_bank.bat`.

---

## 5. Hot Database Backups & Data Protection

Kitaab Bank includes a built-in zero-downtime hot backup mechanism leveraging the **SQLite Online Backup API** (`sqlite3.Connection.backup()`).

### Method A — One-Click Hot Backup
Double-click:
```
backup_now.bat
```
Creates a snapshot, calculates a SHA-256 digest, validates SQLite integrity (`PRAGMA integrity_check`), and catalogs it in `backup_records`.

### Method B — Teacher Administrative Desk
Navigate to **Teacher Settings > Database Backup & Restore** tab (`/teacher/settings?tab=backup`) and click **Create Live Backup Now**.

### Method C — Automated Windows Task Scheduler (Daily at 4:00 PM)
Run in elevated PowerShell:
```powershell
$Action = New-ScheduledTaskAction -Execute "d:\My Folder\My Work\Kitab Dost\backup_now.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At "16:00"
Register-ScheduledTask -TaskName "KitaabBank_DailyBackup" -Action $Action -Trigger $Trigger -Description "Automated Daily Hot Backup for Kitaab Bank"
```

---

## 6. Disaster Recovery & Restoration Runbook

Restoring a database snapshot can be performed via the safe CLI recovery utility:

```powershell
# List available backups and restore the latest verified snapshot:
python scripts/restore_backup.py --latest

# Or restore a specific backup file:
python scripts/restore_backup.py --file kitab_bank_backup_20261105_120000.db
```

### Safety Features of the Restoration Tool:
1. **WAL Checkpointing:** Executes `PRAGMA wal_checkpoint(TRUNCATE);` to ensure no active write-ahead pages are orphaned.
2. **Pre-Restore Rollback Copy:** Creates an emergency snapshot `kitaab_bank.db.pre_restore_<timestamp>` before making changes.
3. **Target Integrity Check:** Runs `PRAGMA integrity_check;` and schema verification before restoring.
4. **Automated Rollback:** If post-restoration verification fails, immediately restores the pre-restore snapshot so live operations are never broken.

---

## 7. Exhibition Showcase Mode

For school science fairs, educational inspections, and demonstration events:
- Open **Teacher Settings > Exhibition Showcase Mode** (`/teacher/settings?tab=demo`).
- Confirm the safety checkbox and click **Seed Exhibition Demo Data**.
- An automated pre-demo backup (`*_pre_demo.db`) is captured immediately.
- 18 high-realism curriculum textbooks across Classes 6, 7, and 8 are loaded.
- A prominent orange banner indicates demo mode is active.
- To revert back to real school data: Click **Exit Demo & Restore Real Data**.
