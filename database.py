import sqlite3

DATABASE_NAME = "resume.db"


def create_database():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        ats_score INTEGER,
        job_match_score INTEGER,
        rating TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_resume(name, email, phone, ats_score, job_match_score, rating):
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO resumes
    (name, email, phone, ats_score, job_match_score, rating)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        name,
        email,
        phone,
        ats_score,
        job_match_score,
        rating
    ))

    conn.commit()
    conn.close()
def get_all_resumes():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name, email, ats_score,
               job_match_score, rating, created_at
        FROM resumes
        ORDER BY id DESC
    """)

    data = cursor.fetchall()

    conn.close()

    return data
def get_dashboard_data():
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            COUNT(*),
            AVG(ats_score),
            MAX(ats_score),
            AVG(job_match_score)
        FROM resumes
    """)

    data = cursor.fetchone()

    conn.close()

    return data