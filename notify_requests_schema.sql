
-- جدول درخواست نوتیفیکیشن بازی
CREATE TABLE IF NOT EXISTS notify_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watcher_telegram_id TEXT,
    target_username TEXT,
    game_name TEXT,
    scope TEXT CHECK(scope IN ('private', 'group')),
    group_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
