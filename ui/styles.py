STYLESHEET = """
/* ── Global ──────────────────────────────────────────────────────── */
QMainWindow, QDialog {
    background-color: #F9FAFB;
    color: #111827;
    font-family: 'Ubuntu', 'Segoe UI', 'Noto Sans', sans-serif;
    font-size: 13px;
}

QSplitter::handle {
    background-color: #E5E7EB;
    width: 1px;
}

/* ── Left panel ──────────────────────────────────────────────────── */
#left_panel {
    background-color: #F3F4F6;
    border-right: 1px solid #E5E7EB;
}

#section_header {
    color: #6B7280;
    font-size: 10px;
    font-weight: bold;
    letter-spacing: 1px;
    padding: 4px 8px 2px 8px;
}

/* ── Search ──────────────────────────────────────────────────────── */
QLineEdit#search_bar {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
QLineEdit#search_bar:focus {
    border-color: #4F46E5;
}

/* ── Buttons ─────────────────────────────────────────────────────── */
QPushButton#new_note_btn {
    background-color: #4F46E5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-weight: bold;
    font-size: 13px;
}
QPushButton#new_note_btn:hover   { background-color: #4338CA; }
QPushButton#new_note_btn:pressed { background-color: #3730A3; }

QPushButton#trash_btn {
    background-color: transparent;
    color: #6B7280;
    border: none;
    border-radius: 6px;
    padding: 6px 10px;
    text-align: left;
    font-size: 12px;
}
QPushButton#trash_btn:hover   { background-color: #FEE2E2; color: #EF4444; }
QPushButton#trash_btn:checked { background-color: #FEE2E2; color: #EF4444; font-weight: bold; }

/* ── Category Tree ───────────────────────────────────────────────── */
QTreeWidget {
    background-color: transparent;
    border: none;
    outline: none;
    font-size: 13px;
}
QTreeWidget::item {
    padding: 5px 4px;
    border-radius: 4px;
}
QTreeWidget::item:selected {
    background-color: #EEF2FF;
    color: #4F46E5;
}
QTreeWidget::item:hover:!selected {
    background-color: #E5E7EB;
}
QTreeWidget::branch { background: transparent; }

/* ── Tags List ───────────────────────────────────────────────────── */
QListWidget#tags_list {
    background-color: transparent;
    border: none;
    outline: none;
    font-size: 12px;
}
QListWidget#tags_list::item {
    padding: 4px 8px;
    border-radius: 4px;
}
QListWidget#tags_list::item:selected {
    background-color: #D1FAE5;
    color: #065F46;
}
QListWidget#tags_list::item:hover:!selected {
    background-color: #E5E7EB;
}

/* ── Notes List ──────────────────────────────────────────────────── */
QListWidget#notes_list {
    background-color: #FFFFFF;
    border: none;
    border-right: 1px solid #E5E7EB;
    outline: none;
}
QListWidget#notes_list::item {
    border-bottom: 1px solid #F3F4F6;
    padding: 0;
}
QListWidget#notes_list::item:selected { background: transparent; }

/* ── Filter Combo ────────────────────────────────────────────────── */
QComboBox#filter_combo {
    background-color: #FFFFFF;
    border: 1px solid #D1D5DB;
    border-radius: 4px;
    padding: 4px 8px;
    font-size: 11px;
}
QComboBox#filter_combo::drop-down { border: none; }

/* ── Editor ──────────────────────────────────────────────────────── */
#editor_panel {
    background-color: #FFFFFF;
}

QLineEdit#note_title {
    font-size: 18px;
    font-weight: bold;
    border: none;
    border-bottom: 2px solid #E5E7EB;
    padding: 6px 2px;
    background: transparent;
    color: #111827;
}
QLineEdit#note_title:focus {
    border-bottom-color: #4F46E5;
}

QFrame#tags_frame {
    background-color: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
}

QLineEdit#tag_input {
    background-color: transparent;
    border: none;
    font-size: 11px;
    color: #6B7280;
    padding: 2px 4px;
    min-width: 120px;
}
QLineEdit#tag_input:focus { color: #111827; }

QTextEdit#text_editor {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 12px;
    font-family: 'JetBrains Mono', 'Fira Code', 'Ubuntu Mono', monospace;
    font-size: 13px;
    line-height: 1.6;
    color: #1F2937;
}
QTextEdit#text_editor:focus { border-color: #4F46E5; }

QTextBrowser#preview_browser {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
    padding: 12px;
    font-size: 13px;
    color: #1F2937;
}

/* ── Toolbar buttons (markdown) ──────────────────────────────────── */
QPushButton#md_btn {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 4px;
    padding: 3px 8px;
    font-size: 11px;
    color: #374151;
}
QPushButton#md_btn:hover { background-color: #E5E7EB; }

QPushButton#preview_btn {
    background-color: #F3F4F6;
    border: 1px solid #E5E7EB;
    border-radius: 4px;
    padding: 3px 10px;
    font-size: 11px;
    color: #374151;
}
QPushButton#preview_btn:checked {
    background-color: #EEF2FF;
    border-color: #4F46E5;
    color: #4F46E5;
}

/* ── Save button ─────────────────────────────────────────────────── */
QPushButton#save_btn {
    background-color: #10B981;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 7px 14px;
    font-weight: bold;
    font-size: 12px;
}
QPushButton#save_btn:hover   { background-color: #059669; }
QPushButton#save_btn:disabled {
    background-color: #D1D5DB;
    color: #9CA3AF;
}

/* ── Action buttons (record / screenshot / import) ───────────────── */
QPushButton#record_btn {
    background-color: #FEF2F2;
    color: #EF4444;
    border: 1px solid #FECACA;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 11px;
    font-weight: bold;
}
QPushButton#record_btn:hover   { background-color: #FEE2E2; }
QPushButton#record_btn:checked {
    background-color: #EF4444;
    color: white;
    border-color: #DC2626;
}

QPushButton#action_btn {
    background-color: #F3F4F6;
    color: #374151;
    border: 1px solid #D1D5DB;
    border-radius: 5px;
    padding: 5px 10px;
    font-size: 11px;
}
QPushButton#action_btn:hover { background-color: #E5E7EB; }
QPushButton#action_btn:disabled { color: #9CA3AF; }

/* ── Attachments scroll ──────────────────────────────────────────── */
QScrollArea#attachments_scroll {
    background-color: #F9FAFB;
    border: 1px solid #E5E7EB;
    border-radius: 6px;
}

/* ── Section label ───────────────────────────────────────────────── */
QLabel#section_label {
    font-weight: bold;
    font-size: 12px;
    color: #374151;
}

/* ── Audio level bar ─────────────────────────────────────────────── */
QProgressBar#level_bar {
    background-color: #E5E7EB;
    border: none;
    border-radius: 4px;
}
QProgressBar#level_bar::chunk {
    background-color: #EF4444;
    border-radius: 4px;
}

/* ── Attachment widgets ──────────────────────────────────────────── */
#attach_widget {
    background-color: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 8px;
}
#attach_widget:hover { border-color: #4F46E5; }

QPushButton#attach_play_btn {
    background-color: #4F46E5;
    color: white;
    border: none;
    border-radius: 12px;
    font-size: 10px;
    padding: 2px 6px;
}
QPushButton#attach_play_btn:hover { background-color: #4338CA; }
QPushButton#attach_play_btn:checked {
    background-color: #7C3AED;
}

QPushButton#attach_del_btn {
    background-color: transparent;
    color: #9CA3AF;
    border: none;
    font-size: 14px;
    padding: 0 4px;
}
QPushButton#attach_del_btn:hover { color: #EF4444; }

/* ── Status bar ──────────────────────────────────────────────────── */
QStatusBar {
    background-color: #F3F4F6;
    color: #6B7280;
    font-size: 11px;
    border-top: 1px solid #E5E7EB;
}
"""
