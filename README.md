# Kitaab Bank

**Kitaab Bank** is an offline-first school textbook exchange web application. Students can browse approved books, submit donations and requests, and track requests without creating accounts. Teachers review donations and requests, manage the individual-book catalogue, record physical handovers, print QR labels, and run reports.

## Technology

- Python, Flask, Jinja templates
- SQLite with Write-Ahead Logging (WAL)
- Waitress for the multi-device school LAN server
- Local Bootstrap and Font Awesome assets; no runtime CDN dependency
- Vanilla JavaScript for theme, tables, and QR scanning
- English, Urdu, and Sindhi UI support

## Run on Windows

Open PowerShell in the repository folder:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run_server.py
```

Or start the bundled Windows launcher:

```text
start_kitaab_bank.bat
```

Open `http://127.0.0.1:5000` on the host computer. Other devices on the same school Wi-Fi can use the LAN address displayed in the server console.

## First teacher login

- Username: `teacher`
- Initial password: the `INITIAL_TEACHER_PASSWORD` environment variable, or `Teacher@123` when not configured.
- A session that authenticates with the initial password is restricted to the Security settings until a different password is saved.

For a real deployment, set a strong `INITIAL_TEACHER_PASSWORD` and a stable, random `SECRET_KEY` in the host environment before first launch. Do not store either value in source control.

Optional reverse-proxy client IP forwarding is disabled by default. Only set `TRUSTED_PROXY_IPS` for known proxy peer addresses whose `X-Forwarded-For` header is configured safely.

## Data and backups

- The live SQLite database is stored at the configured `DATABASE_PATH` (default: `kitaab_bank.db` in the project root).
- Uploaded book photos and generated QR assets are stored locally under `app/static/uploads/`.
- Backups are stored in the configured `BACKUP_FOLDER` (default: `backups/`).
- Create a hot backup from **Teacher Desk → Settings → Live Backups**, or use `backup_now.bat`.
- Restore a backup using the CLI runbook in [docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md). The current Teacher Settings screen does not provide a general-purpose restore button.

## Developer references

- [Current architecture](docs/ARCHITECTURE.md)
- [Product requirements](docs/PRD.md)
- [Database schema](docs/DATABASE_SCHEMA.md)
- [Deployment and recovery guide](docs/DEPLOYMENT_GUIDE.md)
- [Security notes](docs/SECURITY.md)
- [Progress history](docs/PROGRESS.md)

## Tests

The repository contains Python unit/integration tests in `tests/` and root-level test scripts. Use the isolated `testing` app configuration for tests; it allocates a temporary database and upload/backup directories per application instance.

```powershell
python -m unittest discover -s tests
```

Browser-based tests may require additional tooling beyond `requirements.txt`; see their imports and setup before running them.
