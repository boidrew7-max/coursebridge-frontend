"""
User database — SQLite with werkzeug password hashing.
Handles users, profiles, chat sessions/messages, password reset, and feedback.
"""
import sqlite3, os, random, secrets
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash, check_password_hash

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'users.db')

_ADJS  = ['Swift','Bright','Bold','Calm','Sharp','Ready','Keen','Smart','Sage','Brisk']
_NOUNS = ['Hawk','Scout','Spark','Path','Aim','Trek','Plan','Rise','Step','Goal']


def _connect():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def _row(r):
    return dict(r) if r else None


def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with _connect() as conn:
        conn.execute('PRAGMA foreign_keys = ON')

        conn.execute('''CREATE TABLE IF NOT EXISTS users (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            email         TEXT    UNIQUE NOT NULL,
            password_hash TEXT    NOT NULL,
            username      TEXT    NOT NULL,
            created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        # Idempotent profile columns on existing table
        for col, typedef in [
            ('college',        'TEXT NOT NULL DEFAULT ""'),
            ('major',          'TEXT NOT NULL DEFAULT ""'),
            ('target_schools', 'TEXT NOT NULL DEFAULT ""'),
            ('onboarded',      'INTEGER NOT NULL DEFAULT 0'),
        ]:
            try:
                conn.execute(f'ALTER TABLE users ADD COLUMN {col} {typedef}')
            except sqlite3.OperationalError:
                pass  # column already exists

        conn.execute('''CREATE TABLE IF NOT EXISTS chat_sessions (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            title      TEXT    NOT NULL DEFAULT "New chat",
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS chat_messages (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL,
            role       TEXT    NOT NULL,
            content    TEXT    NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS reset_tokens (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER NOT NULL,
            token      TEXT    NOT NULL UNIQUE,
            expires_at TEXT    NOT NULL,
            used       INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.execute('''CREATE TABLE IF NOT EXISTS message_feedback (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id    INTEGER,
            session_id INTEGER,
            rating     INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )''')

        conn.commit()


def _gen_username():
    return random.choice(_ADJS) + random.choice(_NOUNS) + str(random.randint(10, 999))


# ── Users ─────────────────────────────────────────────────────────

def create_user(email, password, username=None):
    username = (username or '').strip() or _gen_username()
    with _connect() as conn:
        conn.execute(
            'INSERT INTO users (email, password_hash, username) VALUES (?,?,?)',
            (email.lower().strip(), generate_password_hash(password), username)
        )
        conn.commit()
    return get_user_by_email(email)


def get_user_by_email(email):
    with _connect() as conn:
        row = conn.execute(
            'SELECT id,email,password_hash,username,college,major,target_schools,onboarded FROM users WHERE email=?',
            (email.lower().strip(),)
        ).fetchone()
    return _row(row)


def get_user_by_id(uid):
    with _connect() as conn:
        row = conn.execute(
            'SELECT id,email,username,college,major,target_schools,onboarded FROM users WHERE id=?',
            (uid,)
        ).fetchone()
    return _row(row)


def verify_password(user, password):
    return check_password_hash(user['password_hash'], password)


def email_exists(email):
    return get_user_by_email(email) is not None


def update_profile(uid, **fields):
    """Update any subset of: username, college, major, target_schools, onboarded."""
    allowed = {'username', 'college', 'major', 'target_schools', 'onboarded'}
    updates = {k: v for k, v in fields.items() if k in allowed}
    if not updates:
        return
    cols = ', '.join(f'{k}=?' for k in updates)
    vals = list(updates.values()) + [uid]
    with _connect() as conn:
        conn.execute(f'UPDATE users SET {cols} WHERE id=?', vals)
        conn.commit()


def update_password(uid, new_password):
    with _connect() as conn:
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',
                     (generate_password_hash(new_password), uid))
        conn.commit()


# ── Password reset ────────────────────────────────────────────────

def create_reset_token(email):
    """Returns (token, user) or (None, None) if email not found."""
    user = get_user_by_email(email)
    if not user:
        return None, None
    token = secrets.token_urlsafe(32)
    expires = (datetime.utcnow() + timedelta(hours=1)).isoformat()
    with _connect() as conn:
        conn.execute('UPDATE reset_tokens SET used=1 WHERE user_id=?', (user['id'],))
        conn.execute('INSERT INTO reset_tokens (user_id, token, expires_at) VALUES (?,?,?)',
                     (user['id'], token, expires))
        conn.commit()
    return token, user


def redeem_reset_token(token, new_password):
    """Returns True on success, False if invalid/expired/used."""
    with _connect() as conn:
        row = conn.execute(
            'SELECT user_id, expires_at, used FROM reset_tokens WHERE token=?', (token,)
        ).fetchone()
        if not row or row['used']:
            return False
        if datetime.utcnow().isoformat() > row['expires_at']:
            return False
        conn.execute('UPDATE reset_tokens SET used=1 WHERE token=?', (token,))
        conn.execute('UPDATE users SET password_hash=? WHERE id=?',
                     (generate_password_hash(new_password), row['user_id']))
        conn.commit()
    return True


# ── Chat sessions ─────────────────────────────────────────────────

def create_session(uid, title='New chat'):
    with _connect() as conn:
        cur = conn.execute('INSERT INTO chat_sessions (user_id,title) VALUES (?,?)', (uid, title))
        sid = cur.lastrowid
        conn.commit()
    return get_session(sid, uid)


def get_session(sid, uid):
    with _connect() as conn:
        row = conn.execute(
            'SELECT id,title,created_at,updated_at FROM chat_sessions WHERE id=? AND user_id=?',
            (sid, uid)
        ).fetchone()
    return _row(row)


def get_user_sessions(uid):
    with _connect() as conn:
        rows = conn.execute(
            'SELECT id,title,created_at,updated_at FROM chat_sessions WHERE user_id=? ORDER BY updated_at DESC',
            (uid,)
        ).fetchall()
    return [dict(r) for r in rows]


def update_session_title(sid, uid, title):
    with _connect() as conn:
        conn.execute(
            'UPDATE chat_sessions SET title=?, updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?',
            (title, sid, uid)
        )
        conn.commit()


def delete_session(sid, uid):
    with _connect() as conn:
        conn.execute('DELETE FROM chat_sessions WHERE id=? AND user_id=?', (sid, uid))
        conn.commit()


# ── Chat messages ─────────────────────────────────────────────────

def add_messages(sid, uid, message_list):
    """message_list: [{role, content}, ...]. Also touches session updated_at."""
    with _connect() as conn:
        owns = conn.execute(
            'SELECT 1 FROM chat_sessions WHERE id=? AND user_id=?', (sid, uid)
        ).fetchone()
        if not owns:
            return False
        for m in message_list:
            conn.execute(
                'INSERT INTO chat_messages (session_id,role,content) VALUES (?,?,?)',
                (sid, m['role'], m['content'])
            )
        conn.execute(
            'UPDATE chat_sessions SET updated_at=CURRENT_TIMESTAMP WHERE id=? AND user_id=?',
            (sid, uid)
        )
        conn.commit()
    return True


def get_session_messages(sid, uid):
    """Returns list of {role, content} or None if session not owned by uid."""
    with _connect() as conn:
        owns = conn.execute(
            'SELECT 1 FROM chat_sessions WHERE id=? AND user_id=?', (sid, uid)
        ).fetchone()
        if not owns:
            return None
        rows = conn.execute(
            'SELECT role, content FROM chat_messages WHERE session_id=? ORDER BY id ASC',
            (sid,)
        ).fetchall()
    return [dict(r) for r in rows]


# ── Feedback ──────────────────────────────────────────────────────

def save_feedback(uid, session_id, rating):
    with _connect() as conn:
        conn.execute(
            'INSERT INTO message_feedback (user_id,session_id,rating) VALUES (?,?,?)',
            (uid, session_id, rating)
        )
        conn.commit()
