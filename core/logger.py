import sqlite3
from datetime import datetime, timezone
from core.config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL,
            total_tests INTEGER DEFAULT 0,
            passed INTEGER DEFAULT 0,
            failed INTEGER DEFAULT 0
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id INTEGER NOT NULL,
            attack_type TEXT NOT NULL,
            prompt TEXT NOT NULL,
            response TEXT NOT NULL,
            success INTEGER NOT NULL,
            severity TEXT NOT NULL,
            notes TEXT,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (run_id) REFERENCES runs(id)
        )
    """)

    conn.commit()
    conn.close()


def create_run(model):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "INSERT INTO runs (timestamp, model) VALUES (?, ?)",
        (datetime.now(timezone.utc).isoformat(), model)
    )

    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id


def log_result(run_id, attack_type, prompt, response, success, severity, notes=""):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO results (run_id, attack_type, prompt, response, success, severity, notes, timestamp)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        run_id,
        attack_type,
        prompt,
        response,
        1 if success else 0,
        severity,
        notes,
        datetime.now(timezone.utc).isoformat()
    ))

    conn.commit()
    conn.close()


def finalize_run(run_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*) as total,
            SUM(success) as passed,
            SUM(CASE WHEN success = 0 THEN 1 ELSE 0 END) as failed
        FROM results WHERE run_id = ?
    """, (run_id,))
    row = cursor.fetchone()
    cursor.execute("""
        UPDATE runs SET total_tests = ?, passed = ?, failed = ?
        WHERE id = ?
    """, (row["total"], row["passed"], row["failed"], run_id))

    conn.commit()
    conn.close()


def get_run_results(run_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM results WHERE run_id = ?", (run_id,))

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows