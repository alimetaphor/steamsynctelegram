import sqlite3

conn = sqlite3.connect("steamsync_users.db")
cursor = conn.cursor()

cursor.execute("""CREATE TABLE IF NOT EXISTS users (
    telegram_id TEXT PRIMARY KEY,
    username TEXT,
    steam_id TEXT UNIQUE,
    display_name TEXT,
    last_seen TIMESTAMP,
    last_fetched_data TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS notify_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watcher_telegram_id TEXT,
    target_username TEXT,
    game_name TEXT,
    scope TEXT,
    group_id TEXT
)""")

cursor.execute("""CREATE TABLE IF NOT EXISTS auto_post_targets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    group_id TEXT,
    topic_id TEXT,
    purpose TEXT
)""")

conn.commit()
conn.close()
