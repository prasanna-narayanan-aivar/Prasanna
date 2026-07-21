# 3-Tier Web App on Ubuntu (No Docker)

## What this is

A 3-tier web application deployed from scratch on an Ubuntu VM, without containers:

- **Tier 1 — Nginx** (port 80): reverse proxy, forwards requests to the app
- **Tier 2 — Flask app via Gunicorn** (port 5000): application logic, has a `/health` endpoint
- **Tier 3 — PostgreSQL** (port 5432): database, accessed via a dedicated non-superuser role

## Goal

`curl http://localhost/health` should return:

```json
{"status": "ok", "db": "reachable"}
```

## Key requirements to keep in mind

- Use a dedicated Postgres user (`appuser`) and database (`appdb`) — do **not** use the `postgres` superuser for the app.
- Test the Flask app directly on port 5000 (via Gunicorn) before wiring up Nginx.
- Run the app as a proper **systemd service**, not a manually-run process.
- Nginx should proxy port 80 → port 5000, and the default Nginx site should be removed.
- Document any errors hit along the way and how they were fixed.

## Status

🚧 In progress — commands, config files, and the errors/fixes log will be added as each step is completed.ß