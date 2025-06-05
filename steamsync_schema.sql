
-- جدول کاربران تلگرام
CREATE TABLE IF NOT EXISTS users (
    telegram_id TEXT PRIMARY KEY,
    username TEXT,
    steam_id TEXT UNIQUE,
    display_name TEXT,
    last_seen TIMESTAMP,
    last_fetched_data TEXT
);

-- نگه‌داری اینکه هر کاربر در کدوم گروه‌ها عضوه
CREATE TABLE IF NOT EXISTS user_groups (
    telegram_id TEXT,
    group_id TEXT,
    username TEXT,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (telegram_id, group_id)
);

-- نگه‌داری مقصد ارسال پیام‌های خودکار (مثل تخفیف)
CREATE TABLE IF NOT EXISTS auto_post_targets (
    group_id TEXT,
    topic_id TEXT,
    purpose TEXT, -- مثلاً "deals"
    PRIMARY KEY (group_id, purpose)
);

-- لاگ‌گیری دستورات استفاده شده (برای آنالیز یا محدودسازی در آینده)
CREATE TABLE IF NOT EXISTS command_logs (
    telegram_id TEXT,
    command TEXT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
