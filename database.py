
"""
Angren Quiz - SQLite database
Foydalanuvchilar tarixi va viktorina javoblarini saqlash.
"""

import os
import sqlite3
from pathlib import Path
from contextlib import contextmanager

BASE_DIR = Path(__file__).resolve().parent

# DB_PATH muhit o'zgaruvchisi orqali ham belgilanadi.
DB_PATH = Path(
    os.environ.get(
        "DB_PATH",
        str(BASE_DIR / "data" / "quiz.db")
    )
)


SCHEMA = """
CREATE TABLE IF NOT EXISTS attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    token TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    phone TEXT NOT NULL,
    school TEXT NOT NULL,
    mfy TEXT NOT NULL,
    lang TEXT,
    created INTEGER NOT NULL,
    finished INTEGER,
    score INTEGER,
    total INTEGER
);

CREATE TABLE IF NOT EXISTS answers (
    attempt_id INTEGER NOT NULL,
    qi INTEGER NOT NULL,
    choice INTEGER NOT NULL,
    qtext TEXT,
    chosen TEXT,
    correct_text TEXT,
    is_correct INTEGER,
    ts INTEGER,

    PRIMARY KEY (attempt_id, qi),

    FOREIGN KEY (attempt_id)
        REFERENCES attempts(id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS ix_phone
ON attempts(phone);

CREATE INDEX IF NOT EXISTS ix_attempt_finished
ON attempts(finished);

CREATE INDEX IF NOT EXISTS ix_answer_attempt
ON answers(attempt_id);
"""


def connect_db():
    """SQLite bazasiga ulanish."""

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    connection.execute("PRAGMA foreign_keys=ON")
    connection.execute("PRAGMA busy_timeout=30000")

    return connection


def init_db():
    """Bazani yaratish va eski bazani yangilash."""

    DB_PATH.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    connection = sqlite3.connect(
        str(DB_PATH),
        timeout=30
    )

    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.execute("PRAGMA foreign_keys=ON")

        connection.executescript(SCHEMA)

        # Eski bazalar bilan moslik.
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(answers)"
            )
        }

        migrations = {
            "qtext": "TEXT",
            "chosen": "TEXT",
            "correct_text": "TEXT",
            "is_correct": "INTEGER",
            "ts": "INTEGER"
        }

        for name, data_type in migrations.items():
            if name not in columns:
                connection.execute(
                    f"ALTER TABLE answers ADD COLUMN {name} {data_type}"
                )

        connection.commit()

    finally:
        connection.close()


@contextmanager
def get_connection():
    """Xavfsiz ulanish va tranzaksiya."""

    connection = connect_db()

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def save_attempt(
    token,
    name,
    phone,
    school,
    mfy,
    lang,
    created,
    total
):
    """Yangi foydalanuvchi testini saqlash."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO attempts (
                token, name, phone, school,
                mfy, lang, created, total
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                token,
                name,
                phone,
                school,
                mfy,
                lang,
                created,
                total
            )
        )

        return cursor.lastrowid


def save_answer(
    attempt_id,
    qi,
    choice,
    qtext,
    chosen,
    correct_text,
    is_correct,
    ts
):
    """Foydalanuvchining javobini saqlash."""

    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT OR IGNORE INTO answers (
                attempt_id, qi, choice,
                qtext, chosen, correct_text,
                is_correct, ts
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                attempt_id,
                qi,
                choice,
                qtext,
                chosen,
                correct_text,
                is_correct,
                ts
            )
        )

        return cursor.rowcount == 1


def finish_attempt(attempt_id, score, total, finished):
    """Test yakunini saqlash."""

    with get_connection() as connection:
        connection.execute(
            """
            UPDATE attempts
            SET score=?, total=?, finished=?
            WHERE id=? AND finished IS NULL
            """,
            (
                score,
                total,
                finished,
                attempt_id
            )
        )


def get_all_attempts():
    """Administrator uchun barcha urinishlar."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM attempts
            ORDER BY created DESC
            """
        ).fetchall()


def get_attempt_answers(attempt_id):
    """Administrator uchun foydalanuvchi javoblari."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT *
            FROM answers
            WHERE attempt_id=?
            ORDER BY qi
            """,
            (attempt_id,)
        ).fetchall()


def get_statistics():
    """Umumiy statistika."""

    with get_connection() as connection:
        return connection.execute(
            """
            SELECT
                COUNT(*) AS total_attempts,
                SUM(
                    CASE WHEN finished IS NOT NULL
                    THEN 1 ELSE 0 END
                ) AS completed,
                AVG(
                    CASE WHEN finished IS NOT NULL
                    THEN score * 100.0 / NULLIF(total, 0)
                    END
                ) AS average_percent
            FROM attempts
            """
        ).fetchone()


def backup_database(destination):
    """Bazani xavfsiz zaxiralash."""

    destination = Path(destination)
    destination.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    source = connect_db()
    target = sqlite3.connect(str(destination))

    try:
        source.backup(target)
    finally:
        target.close()
        source.close()


# Ilova ishga tushganda bazani tayyorlash.
init_db()

