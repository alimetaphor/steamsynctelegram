import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name="steamsync_users.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._create_tables()
    
    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            telegram_id TEXT PRIMARY KEY,
            username TEXT,
            steam_id TEXT UNIQUE,
            display_name TEXT,
            last_seen TIMESTAMP,
            last_fetched_data TEXT
        )
        """)
        self.conn.commit()

    def save_user_data(self, telegram_id, username, steam_id, display_name, last_data):
        cursor = self.conn.cursor()
        cursor.execute("""
        INSERT INTO users VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(telegram_id) DO UPDATE SET
            steam_id=excluded.steam_id,
            display_name=excluded.display_name,
            last_seen=excluded.last_seen,
            last_fetched_data=excluded.last_fetched_data
        """, (telegram_id, username, steam_id, display_name, datetime.utcnow(), json.dumps(last_data)))
        self.conn.commit()

    def get_recent_users(self, limit=5):
        cursor = self.conn.cursor()
        cursor.execute("SELECT username, steam_id, last_seen FROM users ORDER BY last_seen DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def get_total_users(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        return cursor.fetchone()[0]
