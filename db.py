import sqlite3
import json
from datetime import datetime

class Database:
    def __init__(self, db_name="steamsync_users.db"):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self._create_tables()

    def _create_tables(self):
        cursor = self.conn.cursor()
        cursor.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id TEXT PRIMARY KEY,
                username TEXT,
                steam_id TEXT UNIQUE,
                display_name TEXT,
                last_seen TIMESTAMP,
                last_fetched_data TEXT
            );

            CREATE TABLE IF NOT EXISTS user_groups (
                telegram_id TEXT,
                group_id TEXT,
                username TEXT,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (telegram_id, group_id)
            );

            CREATE TABLE IF NOT EXISTS auto_post_targets (
                group_id TEXT,
                topic_id TEXT,
                purpose TEXT,
                PRIMARY KEY (group_id, purpose)
            );

            CREATE TABLE IF NOT EXISTS command_logs (
                telegram_id TEXT,
                command TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS notify_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                watcher_telegram_id TEXT,
                target_username TEXT,
                game_name TEXT,
                scope TEXT CHECK(scope IN ('private', 'group')),
                group_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
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

    def get_user_by_username(self, username):
        cursor = self.conn.cursor()
        cursor.execute("SELECT steam_id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_users_in_group(self, group_id):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT u.username, u.steam_id
            FROM user_groups g
            JOIN users u ON g.telegram_id = u.telegram_id
            WHERE g.group_id = ?
        """, (group_id,))
        return cursor.fetchall()

    def link_user_to_group(self, telegram_id, group_id, username):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO user_groups (telegram_id, group_id, username)
            VALUES (?, ?, ?)
            ON CONFLICT(telegram_id, group_id) DO UPDATE SET last_active=CURRENT_TIMESTAMP
        """, (telegram_id, group_id, username))
        self.conn.commit()

    def set_auto_post_target(self, group_id, topic_id, purpose):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO auto_post_targets VALUES (?, ?, ?)
            ON CONFLICT(group_id, purpose) DO UPDATE SET topic_id=excluded.topic_id
        """, (group_id, topic_id, purpose))
        self.conn.commit()

    def get_post_targets_by_purpose(self, purpose):
        cursor = self.conn.cursor()
        cursor.execute("SELECT group_id, topic_id FROM auto_post_targets WHERE purpose = ?", (purpose,))
        return cursor.fetchall()

    # ---- قابلیت‌های نوتیف ----

    def add_notify_request(self, watcher_telegram_id, target_username, game_name, scope, group_id=None):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO notify_requests (watcher_telegram_id, target_username, game_name, scope, group_id)
            VALUES (?, ?, ?, ?, ?)
        """, (watcher_telegram_id, target_username, game_name, scope, group_id))
        self.conn.commit()
        return cursor.lastrowid

    def get_all_notify_requests(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, watcher_telegram_id, target_username, game_name, scope, group_id FROM notify_requests")
        return cursor.fetchall()

    def remove_notify_request(self, request_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM notify_requests WHERE id = ?", (request_id,))
        self.conn.commit()

    def get_requests_for_target(self, target_username):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, watcher_telegram_id, game_name, scope, group_id
            FROM notify_requests
            WHERE target_username = ?
        """, (target_username,))
        return cursor.fetchall()
