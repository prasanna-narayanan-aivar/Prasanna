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

# Tier 1 — Nginx (Reverse Proxy)

## Purpose

Nginx listens on port 80 and forwards all incoming requests to the Flask app running on port 5000.

## Commands

```bash
# Install
sudo apt update
sudo apt install -y nginx

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Create config
sudo vim /etc/nginx/sites-available/webapp
```

## Config File

`/etc/nginx/sites-available/webapp`:

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Enable and Apply

```bash
# Symlink config into sites-enabled/
sudo ln -s /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/webapp

# Validate config syntax
sudo nginx -t

# Apply changes
sudo systemctl reload nginx
```

## Checkpoint

```bash
curl http://localhost/
```

Expect a `502 Bad Gateway` — this confirms Nginx is running and forwarding correctly, but nothing is listening on port 5000 yet.