from flask import Flask, jsonify
import os
import psycopg2


DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "appdb")
DB_USER = os.environ.get("DB_USER", "appuser")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "")

app = Flask(__name__)

@app.route("/health")
def health():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
        )
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "ok", "db": "reachable"})
    except Exception as e:
        return jsonify({"status": "error", "db": "unreachable", "detail": str(e)}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)