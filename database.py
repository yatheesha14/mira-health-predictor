"""
data base.py
Handles all SQLite database operations for the MIRA Health Predictor.
Every function here is a single, clear responsibility.
"""
import sqlite3
import os
DB_PATH = os.path.join(os.path.dirname(__file__), "mira health.db")

def get_connection():
    """Return an open SQLite connection. Rows come back as dlick-like objects."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Create the patients table if it does not already exit."""
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS patients (
                 id    INTEGER  PRIMARY KEY AUTOINCREMENT,
                 full_name    TEXT    NOT NULL,
            dob          TEXT    NOT NULL,
            email        TEXT    NOT NULL,
            glucose      REAL    NOT NULL,
            hemoglobin  REAL    NOT NULL,
            cholesterol  REAL    NOT NULL,
            remarks      TEXT    DEFAULT '',
            created_at   TEXT    DEFAULT (datetime('now','localtime'))
            """)
    conn.commit()
    conn.close()

#create
def add_patient(full_name, dob, email, glucose, hemoglobin, cholesterol, remarks):
    """
    Insert one patient record.
    Return the new row's id (integer).
    """
    conn = get_connection()
    cursor = conn.execute(
        """INSERT INTO patients
        (full_name, dob, email, glucose, hemoglobin, cholesterol, remarks)
        VALUES(?, ?, ?, ?, ?, ?, ?)""",
        (full_name, dob, email, float(glucose),
         float(hemoglobin), float(cholesterol), remarks)
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id

#READ
def get_all_patients():
    """Return a list of all patient row, newest first."""
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM patients ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return rows

# UPDATE
def update_patient(patient_id, full_name, dob, email,glucose, haemoglobin, cholesterol, remarks):
    """Update all fields for the given patient id."""
    conn = get_connection()
    conn.execute(
        """UPDATE patients
           SET full_name=?, dob=?, email=?,
               glucose=?, haemoglobin=?, cholesterol=?, remarks=?
           WHERE id=?""",
        (full_name, dob, email,
         float(glucose), float(haemoglobin), float(cholesterol),
         remarks, patient_id)
    )
    conn.commit()
    conn.close()

# DELETE
def delete_patient(patient_id):
    """Permanently remove a patient record."""
    conn = get_connection()
    conn.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
    conn.commit()
    conn.close()
