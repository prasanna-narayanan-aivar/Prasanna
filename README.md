3-Tier Web App on Ubuntu (Nginx + Flask/Gunicorn + PostgreSQL)

A minimal 3-tier deployment built from scratch on Ubuntu 24.04, no containers:

Tier 1 (web/proxy): Nginx on port 80, reverse-proxying to the app
Tier 2 (app): Flask app served by Gunicorn on port 5000
Tier 3 (data): PostgreSQL on port 5432, dedicated non-superuser role

End state: curl http://localhost/health returns

{"status": "ok", "db": "reachable"}

