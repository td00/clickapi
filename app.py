import json
import sqlite3
import os
import logging
from flask import Flask, jsonify, Response

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

def get_all_counters(project):
    conn = sqlite3.connect("./db/counter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT endpoint, count FROM counters WHERE project = ?", (project,))
    counters = cursor.fetchall()
    conn.close()
    return {endpoint: count for endpoint, count in counters}

def get_all_projects_counters():
    conn = sqlite3.connect("./db/counter.db")
    cursor = conn.cursor()
    cursor.execute("SELECT project, endpoint, count FROM counters")
    counters = cursor.fetchall()
    conn.close()
    return {(project, endpoint): count for project, endpoint, count in counters}

app = Flask(__name__)
create_directories()

@app.route('/hit/<string:project>/<string:endpoint>', methods=['GET', 'POST'])
def hit(project, endpoint):
    count = hit_counter(project, endpoint)
    return str(count)

@app.route('/hit/<string:project>/<string:endpoint>/json', methods=['GET', 'POST'])
def hit_json(project, endpoint):
    count = hit_counter(project, endpoint)
    return jsonify({"count": count})

@app.route('/get/<string:project>/<string:endpoint>', methods=['GET'])
def get(project, endpoint):
    count = get_counter(project, endpoint)
    return str(count)

@app.route('/get/<string:project>/<string:endpoint>/json', methods=['GET'])
def get_json(project, endpoint):
    count = get_counter(project, endpoint)
    return jsonify({"count": count})

@app.route('/get/<string:project>/<string:endpoint>/metrics', methods=['GET'])
def get_metrics(project, endpoint):
    count = get_counter(project, endpoint)
    metrics = (f"{project}_{endpoint}_count {count}")
    return Response(f"# TYPE counter gauge\n{metrics}\n", mimetype='text/plain')


@app.route('/get/<string:project>/metrics', methods=['GET'])
def get_project_metrics(project):
    counters = get_all_counters(project)
    metrics = "\n".join(f"{project}_{endpoint}_count {count}" for endpoint, count in counters.items())
    return Response(f"# TYPE counter gauge\n{metrics}\n", mimetype='text/plain')

@app.route('/get/metrics', methods=['GET'])
def get_all_metrics():
    counters = get_all_projects_counters()
    metrics = "\n".join(f"{project}_{endpoint}_count {count}" for (project, endpoint), count in counters.items())
    return Response(f"# TYPE counter gauge\n{metrics}\n", mimetype='text/plain')

if __name__ == "__main__":
    port = int(os.getenv("APIPORT") or load_config() or DEFAULT_PORT)
    init_db()
    app.run(host="0.0.0.0", port=port, debug=False)
