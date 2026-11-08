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

### Step 2.4 — Environment Configuration & Secrets Setup
Copy the template `.env.example` to `.env` in the project root:
```powershell
copy .env.example .env
```
Open `.env` in Notepad and configure your production secrets:
1. **`SECRET_KEY`**: Generate a cryptographically secure 64-character hex key:
   ```powershell
   python -c "import secrets; print(secrets.token_hex(32))"
   ```
   Paste the generated token as `SECRET_KEY=...`. A persistent secret key prevents session cookie invalidation when the server restarts.
2. **`INITIAL_TEACHER_PASSWORD`**: Set a strong initial password (at least 8 characters with upper, lower, digit, and special char).
3. **`SCHOOL_NAME`**: Set your school's official display name.
4. **`RATE_LIMIT_LOGIN_FAILURES`**: Defaults to 5 failed attempts per 15-minute window (`RATE_LIMIT_LOGIN_WINDOW_SECONDS=900`).

> [!CAUTION]
> The `.env` file contains sensitive security credentials and is strictly excluded by `.gitignore`. Never commit `.env` to Git or share it over insecure channels.

### Step 2.5 — Database Initialization & First Teacher Account
The database initializes automatically in SQLite WAL mode on first application launch. If initializing explicitly:
```powershell
python -c "from app import create_app; from app.database import init_db; app = create_app('production'); init_db(app)"
```
Initial teacher administrator credentials:
- **Username:** `teacher`
- **Initial Password:** Value configured in `INITIAL_TEACHER_PASSWORD` (or default `Teacher@123` if unset).
- **Mandatory Rotation:** On first login, the Teacher Desk forces a password rotation before permitting access to management pages (`/teacher/settings?tab=security`).

---

## 3. Running in Production via Waitress

Kitaab Bank uses **Waitress**, a pure-Python production-quality multi-threaded WSGI server that handles concurrent connections robustly on Windows and Linux.

### Method A — Double-Click Batch Launcher (Standard Desktop)
Simply double-click:
```
start_kitaab_bank.bat
```
This launcher:
1. Validates the Python environment.
2. Automatically loads `.env` configuration.
3. Identifies your host machine's Wi-Fi / LAN IP address.
4. Opens your default web browser to `http://127.0.0.1:5000`.
5. Starts Waitress on `0.0.0.0:5000` with 6 worker threads.

### Method B — Command Line Execution
```powershell
.venv\Scripts\python.exe run_server.py
```

Console banner displays:
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

## 4. Windows Startup, Auto-Start & Background Services

For unattended library or school laboratory operation where the server must start automatically when the computer boots:

### Option 1 — Windows Startup Folder (Per-User Auto-Start)
1. Press `Win + R`, type `shell:startup`, and press Enter.
2. Right-click inside the folder &rarr; **New > Shortcut**.
3. Target: `d:\My Folder\My Work\Kitab Dost\start_kitaab_bank.bat`.
4. Working directory: `d:\My Folder\My Work\Kitab Dost`.
5. When the user logs in, the server starts automatically and opens the browser.

### Option 2 — Windows Task Scheduler (Boot-Time Auto-Start without Login)
To run headless when Windows powers on before any user logs in:
1. Open PowerShell as Administrator:
```powershell
$Action = New-ScheduledTaskAction -Execute "d:\My Folder\My Work\Kitab Dost\.venv\Scripts\python.exe" `
    -Argument "run_server.py" `
    -WorkingDirectory "d:\My Folder\My Work\Kitab Dost"
$Trigger = New-ScheduledTaskTrigger -AtStartup
$Principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
Register-ScheduledTask -TaskName "KitaabBank_Server" -Action $Action -Trigger $Trigger -Principal $Principal -Description "Kitaab Bank Local Production Server"
```

### Option 3 — Windows Service via NSSM (Recommended for 24/7 Dedicated Server)
Using NSSM (Non-Sucking Service Manager):
1. Download `nssm.exe` and place it in system path.
2. Run in Administrator Command Prompt:
```cmd
nssm install KitaabBank "d:\My Folder\My Work\Kitab Dost\.venv\Scripts\python.exe" run_server.py
nssm set KitaabBank AppDirectory "d:\My Folder\My Work\Kitab Dost"
nssm set KitaabBank DisplayName "Kitaab Bank School Server"
nssm set KitaabBank Description "100% Offline School Book Exchange Web Service"
nssm set KitaabBank Start SERVICE_AUTO_START
nssm start KitaabBank
```

---

## 5. School Network & Windows Firewall Configuration

To allow students and staff on the school Wi-Fi network to access Kitaab Bank from their mobile devices and library laptops, port 5000 must be allowed through the Windows Defender Firewall.

### Adding Windows Firewall Inbound Rule (Run PowerShell as Administrator)
```powershell
New-NetFirewallRule -DisplayName "Kitaab Bank Local Server (Port 5000)" `
    -Direction Inbound -LocalPort 5000 -Protocol TCP -Action Allow `
    -Profile Domain,Private -Description "Allows students and teachers on school Wi-Fi to access Kitaab Bank."
```

### Static IP / DHCP Reservation Recommendation
To ensure the Wi-Fi address does not change each morning:
1. Access the school Wi-Fi router admin page (e.g. `192.168.1.1` or `192.168.100.1`).
2. Locate **DHCP Reservation** or **Static Lease**.
3. Bind the host computer's MAC address to a fixed IP (e.g. `192.168.100.14`).
4. Generate QR codes pointing to `http://192.168.100.14:5000/catalogue` and post them in the library and classrooms.

---

## 6. Hot Database Backup Policy & Data Protection

Kitaab Bank includes a built-in zero-downtime hot backup mechanism leveraging the **SQLite Online Backup API** (`sqlite3.Connection.backup()`).

### Backup Targets & Objectives
- **RPO (Recovery Point Objective):** Maximum 24 hours of exchange transactions lost in disaster scenarios.
- **RTO (Recovery Time Objective):** Under 2 minutes to restore full operational service from a verified snapshot.

### Method A — One-Click Instant Hot Backup
Double-click:
```
backup_now.bat
```
Creates a snapshot, calculates a SHA-256 digest, validates SQLite integrity (`PRAGMA integrity_check`), and catalogs it in `backup_records`.

### Method B — Teacher Administrative Desk
Navigate to **Teacher Settings > Live Backups** tab (`/teacher/settings?tab=backup`) and click **Create Live Backup Now**. Teachers can download snapshots directly to their computer or delete obsolete backups.

### Method C — Automated Windows Task Scheduler (Daily at 4:00 PM)
Run in elevated PowerShell to automate daily backups when school closes:
```powershell
$Action = New-ScheduledTaskAction -Execute "d:\My Folder\My Work\Kitab Dost\backup_now.bat"
$Trigger = New-ScheduledTaskTrigger -Daily -At "16:00"
Register-ScheduledTask -TaskName "KitaabBank_DailyBackup" -Action $Action -Trigger $Trigger -Description "Automated Daily Hot Backup for Kitaab Bank"
```

### 3-2-1 Offline Storage Rule for Schools
1. **3 Copies:** Live database (`kitaab_bank.db`), local backups folder (`backups/`), and an offline USB drive.
2. **2 Media:** Host SSD and external USB flash drive.
3. **1 Air-Gapped Offsite Copy:** The Teacher In-Charge copies the `backups/` folder to a designated USB drive every Friday afternoon.

---

## 7. Disaster Recovery & Startup Crash Recovery

Detailed operational runbook: See [**`docs/RESTORE_RUNBOOK.md`**](file:///d:/My%20Folder/My%20Work/Kitab%20Dost/docs/RESTORE_RUNBOOK.md).

### Quick CLI Restore Command
```powershell
# 1. Stop Waitress server (Ctrl+C on server console)
# 2. Restore latest verified backup:
python scripts/restore_backup.py --latest

# 3. Restart server:
start_kitaab_bank.bat
```

### Built-in Crash Resilience Architecture
1. **Cross-Process Maintenance Gating:** Restore operations acquire `.maintenance_lock` with the active PID. Incoming web requests receive HTTP 503 Service Unavailable (`503_maintenance.html`) while active connections drain deterministically.
2. **Crash Resilience Marker:** Before pages are mutated, `.restore_in_progress` records the pre-restore rollback snapshot path and target backup metadata.
3. **Ownership-Aware Startup Recovery:**
   - On reboot or startup, `check_and_recover_interrupted_restore(app)` runs before opening the live database.
   - On Windows: Native Win32 APIs (`OpenProcess`, `GetExitCodeProcess`) verify whether the recorded owner PID has exited.
   - If the previous process crashed: The system automatically restores the live database from `emergency_pre_restore_snapshot.db`, validates `PRAGMA integrity_check;`, and clears all markers.
   - If the recorded owner is still alive: The system **fails closed** (`RuntimeError`) to prevent dual-writer corruption.
   - Stale maintenance gates without page mutation are safely cleared on boot.

---

## 8. Exhibition Showcase Mode

For school science fairs, educational inspections, and demonstration events:
- Open **Teacher Settings > Exhibition Showcase Mode** (`/teacher/settings?tab=demo`).
- Confirm the safety checkbox and click **Seed Exhibition Demo Data**.
- An automated pre-demo backup (`*_pre_demo.db`) is captured immediately.
- 18 high-realism curriculum textbooks across Classes 6, 7, and 8 are loaded.
- A prominent orange banner indicates demo mode is active.
- To revert back to real school data: Click **Exit Demo & Restore Real Data** (reverts seamlessly from the pre-demo backup).

---

## 9. Production Release Sign-Off

Before handing the system over to school staff, complete the [**`docs/RELEASE_CHECKLIST.md`**](file:///d:/My%20Folder/My%20Work/Kitab%20Dost/docs/RELEASE_CHECKLIST.md) sign-off procedure:
1. Verify 182/182 test suite passes: `python -m unittest discover -s tests -p "test_*.py"`.
2. Verify secrets and initial password rotation policy.
3. Verify firewall rule and test student mobile connectivity.
4. Verify scheduled daily backup and execute one drill restore.
