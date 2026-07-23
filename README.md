# 3-Tier Web App on Ubuntu (No Docker) — Hardened Edition

## What this is

A 3-tier web application deployed from scratch on an Ubuntu VM, without containers,
with Tier 1 upgraded from a plain forwarder into an actual reverse proxy: load
balancing across multiple Gunicorn instances, rate limiting, and proper header
forwarding.

- **Tier 1 — Nginx (port 80):** reverse proxy — load balances across 2 Gunicorn
  instances, rate-limits abusive clients
- **Tier 2 — Flask app via Gunicorn (ports 8000–8001):** application logic, `/health`
  endpoint. Port 8000 runs as a proper systemd service; port 8001 is run manually
  with the `gunicorn` command, purely to have a second live backend to prove load
  balancing works
- **Tier 3 — PostgreSQL (port 5432, localhost-only):** database, accessed via a
  dedicated non-superuser role

## Goal

```bash
curl http://localhost
```

returns:

```json
{"status": "ok", "db": "reachable"}
```

and does so even if either Gunicorn instance is stopped or restarting.

## Architecture

```
Client → Nginx :80 (rate limit + load balance)
              → Gunicorn :8000 (systemd service)   ─┐
              → Gunicorn :8001 (manual, for testing)─┼─→ Flask app → Postgres :5432 (localhost only)
```

---

## Tier 3 — PostgreSQL

### Setup

```bash
sudo apt update
sudo apt install -y postgresql
sudo -u postgres psql
```

```sql
CREATE USER appuser WITH PASSWORD 'choose_a_strong_password';
CREATE DATABASE appdb OWNER appuser;
GRANT ALL PRIVILEGES ON DATABASE appdb TO appuser;
\q
```

`appuser` owns `appdb` directly, so it already has full rights on that one database —
no `postgres` superuser is used by the app, and `appuser` has no rights outside `appdb`.

### Verify it's not reachable from outside the VM

```bash
# 1. Check what interface Postgres is actually listening on
sudo ss -tlnp | grep 5432
# want: 127.0.0.1:5432   — not 0.0.0.0:5432 or *:5432

```bash
# Restart Postgres after any config changes
sudo systemctl restart postgresql
sudo systemctl status postgresql
```

---

## Tier 2 — Flask + Gunicorn (1 systemd service + 1 manual instance)

Only one Gunicorn instance is a proper systemd-managed service (port 8000). A second
instance on port 8001 is started manually with the `gunicorn` command directly — it
exists only to give nginx a second live backend so load balancing can actually be
observed, not as a production-grade setup.

### App code (`/opt/Prasanna/app.py`)

Connects to Postgres using `flaskapp`user, exposes `/health` returning
`{"status": "ok", "db": "reachable"}` — unchanged from earlier

### systemd service — `/etc/systemd/system/flaskapp.service`

```ini
[Unit]
Description=Gunicorn for serving Flask app
After=network.target postgresql.service
Wants=postgresql.service

[Service]
User=flaskapp
Group=flaskapp
WorkingDirectory=/opt/Prasanna
EnvironmentFile=/opt/Prasanna/.env
ExecStart=/opt/Prasanna/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:8000 app:app
Restart=on-failure
RestartSec=5
Type=simple


[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable flaskapp
sudo systemctl status flaskapp
```

### Second instance — run manually (port 8001), for load-balancing testing only

```bash
cd /opt/myapp
source venv/bin/activate
export $(cat /opt/myapp/.env | xargs)

gunicorn --bind 127.0.0.1:8001 app:app
```

This one isn't managed by systemd — if the VM reboots or the process is killed, it
won't come back on its own. That's fine for proving the load-balancing concept, but
it's the reason this isn't described as a production HA setup.

---

## Tier 1 — Nginx (reverse proxy: load balancing + rate limiting)

### Install and clean default config

```bash
sudo apt install -y nginx
sudo rm /etc/nginx/sites-enabled/default
```

### Global settings — `/etc/nginx/nginx.conf` (inside the `http {}` block)

# Upstream pool — the 2 Gunicorn instances
upstream flaskbackend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
}
```

### Site config — `/etc/nginx/sites-available/webapp`

```nginx

limit_req_zone $binary_remote_addr zone=app_limit:10m rate=2r/s;

server {
    listen 80;
    server_name _;

    location / {
        # Rate limiting — allow short bursts, reject the rest with 429
        limit_req zone=app_limit burst=5 nodelay;
        limit_req_status 429;

        proxy_pass http://flaskbackend/health;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

    }
}
```

### Enable and apply

```bash
sudo ln -s /etc/nginx/sites-available/webapp /etc/nginx/sites-enabled/webapp

# Always validate syntax before reloading — catches typos before they take the site down
sudo nginx -t

sudo systemctl reload nginx
sudo systemctl status nginx
```

---

## End-to-end verification

### 1. Basic checkpoint

```bash
curl http://localhost
# expect: {"status": "ok", "db": "reachable"}
```

### 2. Prove rate limiting is real

```bash
for i in {1..10}; do curl -i -s http://192.168.64.2 | grep "HTTP/"; done
```

Expected
HTTP/1.1 200 OK
HTTP/1.1 200 OK
HTTP/1.1 200 OK
HTTP/1.1 200 OK
HTTP/1.1 200 OK
HTTP/1.1 200 OK
HTTP/1.1 429 Too Many Requests
HTTP/1.1 429 Too Many Requests
HTTP/1.1 429 Too Many Requests
HTTP/1.1 429 Too Many Requests
### 3. Prove Tier 3 isolation

```bash
psql -h <VM_PUBLIC_IP> -U appuser -d appdb   # from your Mac — should fail/refuse
```
