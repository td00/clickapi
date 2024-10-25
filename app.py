import json
import sqlite3
import os
import logging
from flask import Flask, jsonify

logging.basicConfig(level=logging.WARNING)

DEFAULT_PORT = 3000

def create_directories():
    os.makedirs("./config", exist_ok=True)
    os.makedirs("./db", exist_ok=True)

def load_config():
    try:
        with open("./config/config.json") as config_file:
            config = json.load(config_file)
            return config.get("port")
    except FileNotFoundError:
        return None
def init_db():
    conn = sqlite3.connect("./db/counter.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS counters (
            project TEXT,
            endpoint TEXT,
            count INTEGER DEFAULT 0,
            PRIMARY KEY (project, endpoint)
        )
    """)
    conn.commit()
    conn.close()

def hit_counter(project, endpoint):
    conn = sqlite3.connect("./db/counter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM counters WHERE project = ? AND endpoint = ?", (project, endpoint))
    row = cursor.fetchone()

    if row is None:
        cursor.execute("INSERT INTO counters (project, endpoint, count) VALUES (?, ?, 1)", (project, endpoint))
        count = 1
    else:
        count = row[0] + 1
        cursor.execute("UPDATE counters SET count = ? WHERE project = ? AND endpoint = ?", (count, project, endpoint))

    conn.commit()
    conn.close()
    return count

def get_counter(project, endpoint):
    conn = sqlite3.connect("./db/counter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT count FROM counters WHERE project = ? AND endpoint = ?", (project, endpoint))
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else 0

app = Flask(__name__)
create_directories()

@app.route('/<path:subpath>/hit/<string:project>/<string:endpoint>', methods=['GET', 'POST'])
@app.route('/hit/<string:project>/<string:endpoint>', methods=['GET', 'POST'])
def hit(project, endpoint, subpath=""):
    count = hit_counter(project, endpoint)
    return jsonify({"count": count})

@app.route('/<path:subpath>/get/<string:project>/<string:endpoint>', methods=['GET'])
@app.route('/get/<string:project>/<string:endpoint>', methods=['GET'])
def get(project, endpoint, subpath=""):
    count = get_counter(project, endpoint)
    return jsonify({"count": count})

if __name__ == "__main__":
    port = int(os.getenv("APIPORT") or load_config() or DEFAULT_PORT)
    init_db()
    app.run(host="0.0.0.0", port=port, debug=False)  # Debug auf False setzen

