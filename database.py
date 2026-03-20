import sqlite3
from pathlib import Path
import config


class Database:
    def __init__(self):
        self.db_path = config.DB_PATH
        self._create_schema()

    def get_connection(self):
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def _create_schema(self):
        with self.get_connection() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS categories (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    name  TEXT NOT NULL,
                    parent_id INTEGER REFERENCES categories(id) ON DELETE CASCADE,
                    color TEXT DEFAULT '#4F46E5',
                    sort_order INTEGER DEFAULT 0
                );

                CREATE TABLE IF NOT EXISTS notes (
                    id          INTEGER PRIMARY KEY AUTOINCREMENT,
                    title       TEXT NOT NULL DEFAULT 'Sans titre',
                    content     TEXT DEFAULT '',
                    category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
                    created_at  TEXT DEFAULT (datetime('now','localtime')),
                    updated_at  TEXT DEFAULT (datetime('now','localtime')),
                    is_deleted  INTEGER DEFAULT 0,
                    deleted_at  TEXT
                );

                CREATE TABLE IF NOT EXISTS tags (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    name  TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    color TEXT DEFAULT '#10B981'
                );

                CREATE TABLE IF NOT EXISTS note_tags (
                    note_id INTEGER REFERENCES notes(id) ON DELETE CASCADE,
                    tag_id  INTEGER REFERENCES tags(id)  ON DELETE CASCADE,
                    PRIMARY KEY (note_id, tag_id)
                );

                CREATE TABLE IF NOT EXISTS attachments (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    note_id         INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
                    type            TEXT NOT NULL CHECK(type IN ('image','audio')),
                    filename        TEXT NOT NULL,
                    filepath        TEXT NOT NULL,
                    thumbnail_path  TEXT,
                    duration        REAL,
                    transcription   TEXT,
                    created_at      TEXT DEFAULT (datetime('now','localtime'))
                );

                CREATE INDEX IF NOT EXISTS idx_notes_category ON notes(category_id);
                CREATE INDEX IF NOT EXISTS idx_notes_deleted  ON notes(is_deleted);
                CREATE INDEX IF NOT EXISTS idx_attach_note    ON attachments(note_id);
            """)

    # ──────────────────────────── Notes ────────────────────────────

    def create_note(self, title="Sans titre", content="", category_id=None):
        with self.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO notes (title, content, category_id) VALUES (?,?,?)",
                (title, content, category_id),
            )
            return cur.lastrowid

    def get_note(self, note_id):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM notes WHERE id = ?", (note_id,)
            ).fetchone()

    def update_note(self, note_id, title=None, content=None, category_id=None):
        fields, values = ["updated_at = datetime('now','localtime')"], []
        if title is not None:
            fields.append("title = ?"); values.append(title)
        if content is not None:
            fields.append("content = ?"); values.append(content)
        if category_id is not None:
            fields.append("category_id = ?"); values.append(category_id)
        values.append(note_id)
        with self.get_connection() as conn:
            conn.execute(f"UPDATE notes SET {', '.join(fields)} WHERE id = ?", values)

    def soft_delete_note(self, note_id):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE notes SET is_deleted=1, deleted_at=datetime('now','localtime') WHERE id=?",
                (note_id,),
            )

    def restore_note(self, note_id):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE notes SET is_deleted=0, deleted_at=NULL WHERE id=?", (note_id,)
            )

    def delete_note_permanently(self, note_id):
        attachments = self.get_attachments(note_id)
        with self.get_connection() as conn:
            conn.execute("DELETE FROM notes WHERE id=?", (note_id,))
        return attachments

    def get_notes(
        self,
        category_id=None,
        deleted=False,
        tag_id=None,
        search=None,
        type_filter=None,
    ):
        query = """
            SELECT DISTINCT n.*,
                c.color AS category_color,
                (SELECT COUNT(*) FROM attachments a WHERE a.note_id=n.id AND a.type='image') AS image_count,
                (SELECT COUNT(*) FROM attachments a WHERE a.note_id=n.id AND a.type='audio') AS audio_count
            FROM notes n
            LEFT JOIN categories c ON c.id = n.category_id
        """
        conditions = ["n.is_deleted = ?"]
        params = [1 if deleted else 0]

        if tag_id is not None:
            query += " JOIN note_tags nt ON nt.note_id = n.id"
            conditions.append("nt.tag_id = ?")
            params.append(tag_id)

        if category_id is not None:
            conditions.append("n.category_id = ?")
            params.append(category_id)

        if search:
            conditions.append("(n.title LIKE ? OR n.content LIKE ?)")
            params += [f"%{search}%", f"%{search}%"]

        if type_filter == "image":
            conditions.append(
                "(SELECT COUNT(*) FROM attachments a WHERE a.note_id=n.id AND a.type='image') > 0"
            )
        elif type_filter == "audio":
            conditions.append(
                "(SELECT COUNT(*) FROM attachments a WHERE a.note_id=n.id AND a.type='audio') > 0"
            )

        query += " WHERE " + " AND ".join(conditions)
        query += " ORDER BY n.updated_at DESC"

        with self.get_connection() as conn:
            return conn.execute(query, params).fetchall()

    # ──────────────────────────── Categories ─────────────────────────

    def create_category(self, name, parent_id=None, color="#4F46E5"):
        with self.get_connection() as conn:
            cur = conn.execute(
                "INSERT INTO categories (name, parent_id, color) VALUES (?,?,?)",
                (name, parent_id, color),
            )
            return cur.lastrowid

    def get_categories(self):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM categories ORDER BY parent_id NULLS FIRST, name"
            ).fetchall()

    def update_category(self, category_id, name=None, color=None):
        if name:
            with self.get_connection() as conn:
                conn.execute("UPDATE categories SET name=? WHERE id=?", (name, category_id))
        if color:
            with self.get_connection() as conn:
                conn.execute("UPDATE categories SET color=? WHERE id=?", (color, category_id))

    def delete_category(self, category_id):
        with self.get_connection() as conn:
            conn.execute("UPDATE notes SET category_id=NULL WHERE category_id=?", (category_id,))
            conn.execute("DELETE FROM categories WHERE id=?", (category_id,))

    # ──────────────────────────── Tags ───────────────────────────────

    def create_tag(self, name, color="#10B981"):
        with self.get_connection() as conn:
            try:
                cur = conn.execute(
                    "INSERT INTO tags (name, color) VALUES (?,?)", (name, color)
                )
                return cur.lastrowid
            except sqlite3.IntegrityError:
                row = conn.execute("SELECT id FROM tags WHERE name=?", (name,)).fetchone()
                return row["id"] if row else None

    def get_tags(self):
        with self.get_connection() as conn:
            return conn.execute("SELECT * FROM tags ORDER BY name").fetchall()

    def get_note_tags(self, note_id):
        with self.get_connection() as conn:
            return conn.execute(
                """SELECT t.* FROM tags t
                   JOIN note_tags nt ON nt.tag_id = t.id
                   WHERE nt.note_id = ? ORDER BY t.name""",
                (note_id,),
            ).fetchall()

    def add_tag_to_note(self, note_id, tag_id):
        with self.get_connection() as conn:
            try:
                conn.execute(
                    "INSERT INTO note_tags (note_id, tag_id) VALUES (?,?)", (note_id, tag_id)
                )
            except sqlite3.IntegrityError:
                pass

    def remove_tag_from_note(self, note_id, tag_id):
        with self.get_connection() as conn:
            conn.execute(
                "DELETE FROM note_tags WHERE note_id=? AND tag_id=?", (note_id, tag_id)
            )

    def delete_tag(self, tag_id):
        with self.get_connection() as conn:
            conn.execute("DELETE FROM tags WHERE id=?", (tag_id,))

    # ──────────────────────────── Attachments ────────────────────────

    def add_attachment(
        self, note_id, type_, filename, filepath,
        thumbnail_path=None, duration=None, transcription=None
    ):
        with self.get_connection() as conn:
            cur = conn.execute(
                """INSERT INTO attachments
                   (note_id, type, filename, filepath, thumbnail_path, duration, transcription)
                   VALUES (?,?,?,?,?,?,?)""",
                (note_id, type_, filename, filepath, thumbnail_path, duration, transcription),
            )
            return cur.lastrowid

    def get_attachments(self, note_id):
        with self.get_connection() as conn:
            return conn.execute(
                "SELECT * FROM attachments WHERE note_id=? ORDER BY created_at", (note_id,)
            ).fetchall()

    def delete_attachment(self, attachment_id):
        with self.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM attachments WHERE id=?", (attachment_id,)
            ).fetchone()
            if row:
                conn.execute("DELETE FROM attachments WHERE id=?", (attachment_id,))
            return row

    def update_attachment_transcription(self, attachment_id, transcription):
        with self.get_connection() as conn:
            conn.execute(
                "UPDATE attachments SET transcription=? WHERE id=?",
                (transcription, attachment_id),
            )
