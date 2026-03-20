"""Panneau éditeur de note (panneau droit)."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTextEdit, QTextBrowser, QScrollArea, QFrame, QStackedWidget,
    QProgressBar, QMessageBox, QFileDialog,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

from ui.widgets import TagChip, AudioPlayerWidget, ImageThumbnailWidget
from core.audio_recorder import AudioPlayer


class EditorPanel(QWidget):
    """Panneau de droite : éditeur de note complet."""

    # Émis quand la note change (pour mettre à jour la liste centrale)
    note_changed = pyqtSignal(int, str)    # note_id, new_title

    def __init__(self, db, file_manager, audio_recorder, parent=None):
        super().__init__(parent)
        self.db             = db
        self.file_manager   = file_manager
        self.audio_recorder = audio_recorder
        self.audio_player   = AudioPlayer()

        self.current_note_id = None
        self._is_modified    = False
        self._loading        = False

        self.setObjectName("editor_panel")

        # Timer d'auto-sauvegarde (3 s après la dernière frappe)
        self.save_timer = QTimer(singleShot=True)
        self.save_timer.setInterval(3000)
        self.save_timer.timeout.connect(self.save_note)

        self._build_ui()
        self._connect_signals()
        self.show_empty_state()

    # ──────────────────────────── Construction UI ─────────────────────

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ── État vide ──────────────────────────────────────────────────
        self.empty_widget = QWidget()
        ev = QVBoxLayout(self.empty_widget)
        ev.addStretch()
        lbl = QLabel("Sélectionnez ou créez une note")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("color:#9CA3AF; font-size:15px;")
        ev.addWidget(lbl)
        hint = QLabel("Ctrl+N  pour une nouvelle note")
        hint.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hint.setStyleSheet("color:#D1D5DB; font-size:11px; margin-top:6px;")
        ev.addWidget(hint)
        ev.addStretch()
        root.addWidget(self.empty_widget)

        # ── Conteneur éditeur ─────────────────────────────────────────
        self.editor_widget = QWidget()
        self.editor_widget.setVisible(False)
        el = QVBoxLayout(self.editor_widget)
        el.setContentsMargins(20, 16, 20, 12)
        el.setSpacing(10)

        # Titre + bouton sauvegarder
        title_row = QHBoxLayout()
        self.title_input = QLineEdit()
        self.title_input.setObjectName("note_title")
        self.title_input.setPlaceholderText("Titre de la note…")
        title_row.addWidget(self.title_input)
        self.save_btn = QPushButton("💾 Sauvegarder")
        self.save_btn.setObjectName("save_btn")
        self.save_btn.setEnabled(False)
        self.save_btn.setFixedWidth(140)
        title_row.addWidget(self.save_btn)
        el.addLayout(title_row)

        # Zone des tags
        tags_frame = QFrame()
        tags_frame.setObjectName("tags_frame")
        tags_frame.setFixedHeight(36)
        tfl = QHBoxLayout(tags_frame)
        tfl.setContentsMargins(8, 2, 8, 2)
        tfl.setSpacing(6)
        tfl.addWidget(QLabel("🏷"))

        self.tags_area = QScrollArea()
        self.tags_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.tags_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.tags_area.setWidgetResizable(True)
        self.tags_area.setFrameShape(QFrame.Shape.NoFrame)
        self.tags_area.setFixedHeight(30)

        self.tags_container = QWidget()
        self.tags_layout    = QHBoxLayout(self.tags_container)
        self.tags_layout.setContentsMargins(0, 0, 0, 0)
        self.tags_layout.setSpacing(4)
        self.tags_layout.addStretch()
        self.tags_area.setWidget(self.tags_container)
        tfl.addWidget(self.tags_area, 1)

        self.tag_input = QLineEdit()
        self.tag_input.setObjectName("tag_input")
        self.tag_input.setPlaceholderText("+ Ajouter un tag…")
        self.tag_input.setFixedWidth(140)
        tfl.addWidget(self.tag_input)
        el.addWidget(tags_frame)

        # Barre Markdown + aperçu
        md_bar = QHBoxLayout()
        md_bar.setSpacing(3)
        for label, slot in [
            ("**B**",  self._insert_bold),
            ("*I*",    self._insert_italic),
            ("`Code`", self._insert_code),
            ("—  Liste",    self._insert_list),
            ("1. Liste",    self._insert_olist),
            ("# Titre",     self._insert_heading),
        ]:
            b = QPushButton(label)
            b.setObjectName("md_btn")
            b.setFixedHeight(26)
            b.clicked.connect(slot)
            md_bar.addWidget(b)
        md_bar.addStretch()
        self.preview_btn = QPushButton("Aperçu")
        self.preview_btn.setObjectName("preview_btn")
        self.preview_btn.setCheckable(True)
        self.preview_btn.setFixedHeight(26)
        self.preview_btn.clicked.connect(self._toggle_preview)
        md_bar.addWidget(self.preview_btn)
        el.addLayout(md_bar)

        # Zone édition / prévisualisation
        self.content_stack = QStackedWidget()

        self.text_editor = QTextEdit()
        self.text_editor.setObjectName("text_editor")
        self.text_editor.setAcceptRichText(False)
        self.text_editor.setPlaceholderText(
            "Commencez à écrire votre note ici…\n\n"
            "Markdown supporté :\n**gras**  *italique*  `code`  # Titre\n"
            "- liste  ```bloc de code```"
        )
        self.content_stack.addWidget(self.text_editor)

        self.preview_browser = QTextBrowser()
        self.preview_browser.setObjectName("preview_browser")
        self.content_stack.addWidget(self.preview_browser)

        el.addWidget(self.content_stack, 1)

        # ── En-tête pièces jointes ────────────────────────────────────
        attach_header = QHBoxLayout()
        sec_lbl = QLabel("Pièces jointes")
        sec_lbl.setObjectName("section_label")
        attach_header.addWidget(sec_lbl)
        attach_header.addStretch()

        self.record_btn = QPushButton("🎤 Enregistrer")
        self.record_btn.setObjectName("record_btn")
        self.record_btn.setCheckable(True)
        attach_header.addWidget(self.record_btn)

        self.screenshot_btn = QPushButton("📷 Capture")
        self.screenshot_btn.setObjectName("action_btn")
        attach_header.addWidget(self.screenshot_btn)

        self.import_btn = QPushButton("📁 Importer")
        self.import_btn.setObjectName("action_btn")
        attach_header.addWidget(self.import_btn)

        el.addLayout(attach_header)

        # Indicateur enregistrement
        self.rec_indicator = QWidget()
        ri = QHBoxLayout(self.rec_indicator)
        ri.setContentsMargins(0, 0, 0, 0)
        ri.setSpacing(8)
        ri.addWidget(QLabel("🔴 Enregistrement en cours…"))
        self.level_bar = QProgressBar()
        self.level_bar.setObjectName("level_bar")
        self.level_bar.setRange(0, 100)
        self.level_bar.setTextVisible(False)
        self.level_bar.setFixedHeight(8)
        ri.addWidget(self.level_bar, 1)
        self.rec_indicator.setVisible(False)
        el.addWidget(self.rec_indicator)

        # Zone de défilement des pièces jointes
        self.attach_scroll = QScrollArea()
        self.attach_scroll.setObjectName("attachments_scroll")
        self.attach_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.attach_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.attach_scroll.setFixedHeight(100)
        self.attach_scroll.setWidgetResizable(True)

        self.attach_container = QWidget()
        self.attach_layout    = QHBoxLayout(self.attach_container)
        self.attach_layout.setContentsMargins(6, 6, 6, 6)
        self.attach_layout.setSpacing(8)
        self.attach_layout.addStretch()
        self.attach_scroll.setWidget(self.attach_container)
        el.addWidget(self.attach_scroll)

        root.addWidget(self.editor_widget)

    def _connect_signals(self):
        self.title_input.textChanged.connect(self._on_modified)
        self.text_editor.textChanged.connect(self._on_modified)
        self.tag_input.returnPressed.connect(self._add_tag)
        self.save_btn.clicked.connect(self.save_note)

        self.record_btn.clicked.connect(self._toggle_recording)
        self.screenshot_btn.clicked.connect(self._take_screenshot)
        self.import_btn.clicked.connect(self._import_image)

        self.audio_recorder.recording_started.connect(self._on_rec_started)
        self.audio_recorder.recording_stopped.connect(self._on_rec_stopped)
        self.audio_recorder.recording_error.connect(self._on_rec_error)
        self.audio_recorder.level_updated.connect(
            lambda v: self.level_bar.setValue(int(v * 100))
        )

    # ──────────────────────────── API publique ─────────────────────────

    def show_empty_state(self):
        if self._is_modified and self.current_note_id:
            self.save_note()
        self.current_note_id = None
        self.empty_widget.setVisible(True)
        self.editor_widget.setVisible(False)

    def load_note(self, note_id: int):
        if self._is_modified and self.current_note_id:
            self.save_note()

        self.current_note_id = note_id
        self._loading = True

        note = self.db.get_note(note_id)
        if not note:
            return

        self.title_input.setText(note["title"])
        self.text_editor.setPlainText(note["content"] or "")

        # Repasser en mode édition si on était en prévisualisation
        if self.preview_btn.isChecked():
            self.preview_btn.setChecked(False)
            self._toggle_preview(False)

        self._refresh_tags()
        self._refresh_attachments()

        self.empty_widget.setVisible(False)
        self.editor_widget.setVisible(True)

        self._loading = False
        self._is_modified = False
        self.save_btn.setEnabled(False)

        # Active/désactive les boutons médias
        self.record_btn.setEnabled(True)
        self.screenshot_btn.setEnabled(True)
        self.import_btn.setEnabled(True)

    def save_note(self):
        if not self.current_note_id:
            return
        title   = self.title_input.text().strip() or "Sans titre"
        content = self.text_editor.toPlainText()
        self.db.update_note(self.current_note_id, title=title, content=content)
        self._is_modified = False
        self.save_btn.setEnabled(False)
        self.save_timer.stop()
        self.note_changed.emit(self.current_note_id, title)

    # ──────────────────────────── Tags ────────────────────────────────

    def _refresh_tags(self):
        # Vider l'ancien contenu (sauf le stretch en fin)
        while self.tags_layout.count() > 1:
            item = self.tags_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if self.current_note_id:
            for tag in self.db.get_note_tags(self.current_note_id):
                chip = TagChip(tag["id"], tag["name"], tag["color"], removable=True)
                chip.remove_requested.connect(self._remove_tag)
                self.tags_layout.insertWidget(self.tags_layout.count() - 1, chip)

    def _add_tag(self):
        name = self.tag_input.text().strip()
        if not name or not self.current_note_id:
            return
        tag_id = self.db.create_tag(name)
        if tag_id:
            self.db.add_tag_to_note(self.current_note_id, tag_id)
        self.tag_input.clear()
        self._refresh_tags()

    def _remove_tag(self, tag_id: int):
        if self.current_note_id:
            self.db.remove_tag_from_note(self.current_note_id, tag_id)
            self._refresh_tags()

    # ──────────────────────────── Pièces jointes ──────────────────────

    def _refresh_attachments(self):
        while self.attach_layout.count() > 1:
            item = self.attach_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        if self.current_note_id:
            for att in self.db.get_attachments(self.current_note_id):
                if att["type"] == "image":
                    w = ImageThumbnailWidget(att)
                else:
                    w = AudioPlayerWidget(att, self.audio_player)
                w.delete_requested.connect(self._delete_attachment)
                self.attach_layout.insertWidget(self.attach_layout.count() - 1, w)

    def _delete_attachment(self, attachment_id: int):
        att = self.db.delete_attachment(attachment_id)
        if att:
            self.file_manager.delete_file(att["filepath"])
            if att["thumbnail_path"]:
                self.file_manager.delete_file(att["thumbnail_path"])
        self._refresh_attachments()
        if self.current_note_id:
            self.note_changed.emit(self.current_note_id, self.title_input.text())

    # ──────────────────────────── Markdown ────────────────────────────

    def _toggle_preview(self, checked: bool):
        if checked:
            md_text = self.text_editor.toPlainText()
            try:
                import markdown
                html = markdown.markdown(
                    md_text,
                    extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
                )
            except ImportError:
                html = md_text.replace("\n", "<br>")
            self.preview_browser.setHtml(
                f"<style>body{{font-family:sans-serif;line-height:1.6;padding:4px}}"
                f"code{{background:#F3F4F6;padding:2px 4px;border-radius:3px}}"
                f"pre{{background:#F3F4F6;padding:8px;border-radius:6px}}</style>{html}"
            )
            self.content_stack.setCurrentIndex(1)
            self.preview_btn.setText("✏ Modifier")
        else:
            self.content_stack.setCurrentIndex(0)
            self.preview_btn.setText("Aperçu")

    def _insert_bold(self):   self._wrap("**", "**")
    def _insert_italic(self): self._wrap("*", "*")
    def _insert_code(self):   self._wrap("`", "`")

    def _insert_list(self):
        self.text_editor.textCursor().insertText("\n- ")

    def _insert_olist(self):
        self.text_editor.textCursor().insertText("\n1. ")

    def _insert_heading(self):
        self.text_editor.textCursor().insertText("\n## ")

    def _wrap(self, prefix: str, suffix: str):
        cursor = self.text_editor.textCursor()
        if cursor.hasSelection():
            cursor.insertText(f"{prefix}{cursor.selectedText()}{suffix}")
        else:
            cursor.insertText(f"{prefix}{suffix}")
            pos = cursor.position()
            cursor.setPosition(pos - len(suffix))
            self.text_editor.setTextCursor(cursor)

    # ──────────────────────────── Médias ──────────────────────────────

    def _toggle_recording(self, checked: bool):
        if not self.current_note_id:
            self.record_btn.setChecked(False)
            QMessageBox.information(self, "Noteor", "Veuillez d'abord créer ou sélectionner une note.")
            return
        if checked:
            self.audio_recorder.start()
        else:
            self.audio_recorder.stop()

    def _on_rec_started(self):
        self.rec_indicator.setVisible(True)
        self.record_btn.setText("⏹ Arrêter")

    def _on_rec_stopped(self, filepath: str, duration: float):
        self.rec_indicator.setVisible(False)
        self.record_btn.setText("🎤 Enregistrer")
        self.record_btn.setChecked(False)
        self.level_bar.setValue(0)

        if self.current_note_id:
            filename = Path(filepath).name
            self.db.add_attachment(
                self.current_note_id, "audio", filename, filepath, duration=duration
            )
            self._refresh_attachments()
            self.note_changed.emit(self.current_note_id, self.title_input.text())

    def _on_rec_error(self, msg: str):
        self.rec_indicator.setVisible(False)
        self.record_btn.setText("🎤 Enregistrer")
        self.record_btn.setChecked(False)
        QMessageBox.warning(self, "Erreur d'enregistrement", msg)

    def _take_screenshot(self):
        if not self.current_note_id:
            return
        window = self.window()
        window.showMinimized()
        QTimer.singleShot(600, self._do_screenshot)

    def _do_screenshot(self):
        result = self.file_manager.take_screenshot()
        self.window().showNormal()
        if result and self.current_note_id:
            filepath, thumb = result
            self.db.add_attachment(
                self.current_note_id, "image",
                Path(filepath).name, filepath, thumbnail_path=thumb
            )
            self._refresh_attachments()
            self.note_changed.emit(self.current_note_id, self.title_input.text())

    def _import_image(self):
        if not self.current_note_id:
            return
        path, _ = QFileDialog.getOpenFileName(
            self, "Importer une image", str(Path.home()),
            "Images (*.png *.jpg *.jpeg *.gif *.bmp *.webp *.tiff)"
        )
        if path:
            filepath, thumb = self.file_manager.import_image(path)
            self.db.add_attachment(
                self.current_note_id, "image",
                Path(filepath).name, filepath, thumbnail_path=thumb
            )
            self._refresh_attachments()
            self.note_changed.emit(self.current_note_id, self.title_input.text())

    # ──────────────────────────── Interne ─────────────────────────────

    def _on_modified(self):
        if not self._loading:
            self._is_modified = True
            self.save_btn.setEnabled(True)
            self.save_timer.start()
