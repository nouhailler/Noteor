"""Fenêtre principale de Noteor avec les 3 panneaux."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QComboBox, QStatusBar,
    QMenu, QMessageBox, QInputDialog, QFileDialog, QColorDialog,
    QAbstractItemView,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence

import config
from database import Database
from core.audio_recorder import AudioRecorder
from core.file_manager import FileManager
from ui.editor import EditorPanel
from ui.widgets import NoteItemDelegate


# Rôles personnalisés dans QListWidgetItem
ROLE_NOTE_ID   = Qt.ItemDataRole.UserRole
ROLE_DATE      = Qt.ItemDataRole.UserRole + 1
ROLE_CAT_COLOR = Qt.ItemDataRole.UserRole + 2
ROLE_AUDIO     = Qt.ItemDataRole.UserRole + 3
ROLE_IMAGE     = Qt.ItemDataRole.UserRole + 4


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── Noyau ────────────────────────────────────────────────────
        self.db             = Database()
        self.file_manager   = FileManager()
        self.audio_recorder = AudioRecorder()

        # ── État des filtres ─────────────────────────────────────────
        self._current_category_id = None   # None = toutes les notes
        self._current_tag_id      = None
        self._show_deleted        = False
        self._type_filter         = None   # 'image' | 'audio' | None
        self._search_text         = ""

        self._building_tree   = False
        self._building_notes  = False

        self.setWindowTitle(config.WINDOW_TITLE)
        self.setMinimumSize(980, 640)
        self.resize(1200, 760)

        self._build_ui()
        self._build_menu()
        self._refresh_categories()
        self._refresh_tags_list()
        self._refresh_notes_list()

        self.statusBar().showMessage("Prêt")

    # ──────────────────────────── Construction ────────────────────────

    def _build_ui(self):
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.setCentralWidget(splitter)

        splitter.addWidget(self._build_left_panel())
        splitter.addWidget(self._build_center_panel())

        self.editor = EditorPanel(self.db, self.file_manager, self.audio_recorder)
        self.editor.note_changed.connect(self._on_note_changed)
        splitter.addWidget(self.editor)

        splitter.setSizes([240, 300, 660])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 0)
        splitter.setStretchFactor(2, 1)
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

    # ── Panneau gauche ────────────────────────────────────────────────

    def _build_left_panel(self) -> QWidget:
        panel = QWidget()
        panel.setObjectName("left_panel")
        panel.setMinimumWidth(config.LEFT_PANEL_MIN_WIDTH)
        panel.setMaximumWidth(config.LEFT_PANEL_MAX_WIDTH)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 12, 10, 10)
        layout.setSpacing(6)

        # Barre de recherche
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setPlaceholderText("🔍 Rechercher…")
        self.search_bar.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)

        # Bouton nouvelle note
        new_btn = QPushButton("+ Nouvelle note")
        new_btn.setObjectName("new_note_btn")
        new_btn.clicked.connect(self.create_note)
        layout.addWidget(new_btn)

        # ── Catégories ────────────────────────────────────────────────
        cat_lbl = QLabel("CATÉGORIES")
        cat_lbl.setObjectName("section_header")
        layout.addWidget(cat_lbl)

        self.cat_tree = QTreeWidget()
        self.cat_tree.setHeaderHidden(True)
        self.cat_tree.setRootIsDecorated(True)
        self.cat_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cat_tree.customContextMenuRequested.connect(self._cat_context_menu)
        self.cat_tree.itemClicked.connect(self._on_category_clicked)
        self.cat_tree.setMaximumHeight(200)
        layout.addWidget(self.cat_tree)

        # ── Tags ──────────────────────────────────────────────────────
        tag_lbl = QLabel("TAGS")
        tag_lbl.setObjectName("section_header")
        layout.addWidget(tag_lbl)

        self.tags_list = QListWidget()
        self.tags_list.setObjectName("tags_list")
        self.tags_list.itemClicked.connect(self._on_tag_clicked)
        self.tags_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tags_list.customContextMenuRequested.connect(self._tag_context_menu)
        layout.addWidget(self.tags_list, 1)

        # Filtre type
        type_lbl = QLabel("FILTRER PAR TYPE")
        type_lbl.setObjectName("section_header")
        layout.addWidget(type_lbl)

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("filter_combo")
        self.type_combo.addItems(["Toutes les notes", "Avec audio 🎤", "Avec images 🖼"])
        self.type_combo.currentIndexChanged.connect(self._on_type_filter_changed)
        layout.addWidget(self.type_combo)

        # Corbeille
        self.trash_btn = QPushButton("🗑  Corbeille")
        self.trash_btn.setObjectName("trash_btn")
        self.trash_btn.setCheckable(True)
        self.trash_btn.clicked.connect(self._on_trash_clicked)
        layout.addWidget(self.trash_btn)

        return panel

    # ── Panneau central ───────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(config.CENTER_PANEL_MIN_WIDTH)
        panel.setMaximumWidth(config.CENTER_PANEL_MAX_WIDTH)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.notes_list = QListWidget()
        self.notes_list.setObjectName("notes_list")
        self.notes_list.setItemDelegate(NoteItemDelegate(self.notes_list))
        self.notes_list.itemClicked.connect(self._on_note_clicked)
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self._note_context_menu)
        layout.addWidget(self.notes_list)
        return panel

    # ──────────────────────────── Menu ────────────────────────────────

    def _build_menu(self):
        mb = self.menuBar()

        # Fichier
        file_menu = mb.addMenu("Fichier")
        self._add_action(file_menu, "Nouvelle note",          self.create_note,    "Ctrl+N")
        self._add_action(file_menu, "Sauvegarder",            self.save_current,   "Ctrl+S")
        file_menu.addSeparator()
        self._add_action(file_menu, "Importer des fichiers texte…", self.import_text_files)
        file_menu.addSeparator()
        self._add_action(file_menu, "Quitter",                self.close,          "Ctrl+Q")

        # Affichage
        view_menu = mb.addMenu("Affichage")
        self._add_action(view_menu, "Toutes les notes",       self._show_all_notes)
        self._add_action(view_menu, "Actualiser",             self._full_refresh,  "F5")

        # Aide
        help_menu = mb.addMenu("Aide")
        self._add_action(help_menu, "À propos",               self._about)

    @staticmethod
    def _add_action(menu, label, slot, shortcut=None):
        act = QAction(label, menu.parent())
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        menu.addAction(act)

    # ──────────────────────────── Remplissage données ─────────────────

    def _refresh_categories(self):
        self._building_tree = True
        self.cat_tree.clear()

        all_item = QTreeWidgetItem(["📋  Toutes les notes"])
        all_item.setData(0, Qt.ItemDataRole.UserRole, None)
        all_item.setForeground(0, QColor("#4F46E5"))
        self.cat_tree.addTopLevelItem(all_item)

        cats = self.db.get_categories()
        by_id = {}
        for cat in cats:
            item = QTreeWidgetItem([f"📁  {cat['name']}"])
            item.setData(0, Qt.ItemDataRole.UserRole, cat["id"])
            item.setData(0, Qt.ItemDataRole.UserRole + 1, cat["color"])
            item.setForeground(0, QColor(cat["color"] or "#374151"))
            by_id[cat["id"]] = item

        for cat in cats:
            item = by_id[cat["id"]]
            if cat["parent_id"] and cat["parent_id"] in by_id:
                by_id[cat["parent_id"]].addChild(item)
            else:
                self.cat_tree.addTopLevelItem(item)

        self.cat_tree.expandAll()

        # Re-sélectionner l'item courant
        if self._current_category_id is None:
            self.cat_tree.setCurrentItem(all_item)

        self._building_tree = False

    def _refresh_tags_list(self):
        self.tags_list.clear()
        for tag in self.db.get_tags():
            item = QListWidgetItem(f"● {tag['name']}")
            item.setData(Qt.ItemDataRole.UserRole, tag["id"])
            item.setForeground(QColor(tag["color"] or "#10B981"))
            self.tags_list.addItem(item)

    def _refresh_notes_list(self):
        self._building_notes = True
        prev_id = None
        if self.notes_list.currentItem():
            prev_id = self.notes_list.currentItem().data(ROLE_NOTE_ID)

        self.notes_list.clear()
        notes = self.db.get_notes(
            category_id=self._current_category_id,
            deleted=self._show_deleted,
            tag_id=self._current_tag_id,
            search=self._search_text or None,
            type_filter=self._type_filter,
        )

        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, note["title"])
            item.setData(ROLE_NOTE_ID,   note["id"])
            item.setData(ROLE_DATE,      note["updated_at"][:16] if note["updated_at"] else "")
            item.setData(ROLE_CAT_COLOR, note["category_color"])
            item.setData(ROLE_AUDIO,     bool(note["audio_count"]))
            item.setData(ROLE_IMAGE,     bool(note["image_count"]))
            self.notes_list.addItem(item)
            if note["id"] == prev_id:
                self.notes_list.setCurrentItem(item)

        count = self.notes_list.count()
        noun  = "note" if count <= 1 else "notes"
        self.statusBar().showMessage(f"{count} {noun}")
        self._building_notes = False

    # ──────────────────────────── Événements UI ───────────────────────

    def _on_category_clicked(self, item: QTreeWidgetItem, column: int):
        if self._building_tree:
            return
        self._current_category_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._current_tag_id      = None
        self._show_deleted        = False
        self.trash_btn.setChecked(False)
        self.tags_list.clearSelection()
        self._refresh_notes_list()

    def _on_tag_clicked(self, item: QListWidgetItem):
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        if self._current_tag_id == tag_id:
            # Désélection
            self._current_tag_id = None
            self.tags_list.clearSelection()
        else:
            self._current_tag_id = tag_id
        self._refresh_notes_list()

    def _on_trash_clicked(self, checked: bool):
        self._show_deleted        = checked
        self._current_category_id = None
        self._current_tag_id      = None
        self.cat_tree.clearSelection()
        self.tags_list.clearSelection()
        self._refresh_notes_list()

    def _on_search_changed(self, text: str):
        self._search_text = text
        self._refresh_notes_list()

    def _on_type_filter_changed(self, index: int):
        self._type_filter = [None, "audio", "image"][index]
        self._refresh_notes_list()

    def _on_note_clicked(self, item: QListWidgetItem):
        if self._building_notes:
            return
        note_id = item.data(ROLE_NOTE_ID)
        self.editor.load_note(note_id)

    def _on_note_changed(self, note_id: int, title: str):
        """Mise à jour de l'item dans la liste après modification."""
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(ROLE_NOTE_ID) == note_id:
                item.setData(Qt.ItemDataRole.DisplayRole, title)
                # Récupère les nouvelles métadonnées depuis la DB
                note = self.db.get_note(note_id)
                if note:
                    item.setData(ROLE_DATE, (note["updated_at"] or "")[:16])
                # Met à jour les compteurs d'attachements
                notes = self.db.get_notes()
                for n in notes:
                    if n["id"] == note_id:
                        item.setData(ROLE_AUDIO, bool(n["audio_count"]))
                        item.setData(ROLE_IMAGE, bool(n["image_count"]))
                        break
                self.notes_list.viewport().update()
                break
        self.statusBar().showMessage("Note sauvegardée", 3000)

    # ──────────────────────────── Menus contextuels ───────────────────

    def _cat_context_menu(self, pos):
        item  = self.cat_tree.itemAt(pos)
        menu  = QMenu(self)
        menu.addAction("Nouvelle catégorie",     self._add_category)
        if item and item.data(0, Qt.ItemDataRole.UserRole) is not None:
            menu.addAction("Renommer",           lambda: self._rename_category(item))
            menu.addAction("Changer la couleur", lambda: self._change_cat_color(item))
            menu.addSeparator()
            menu.addAction("Supprimer",          lambda: self._delete_category(item))
        menu.exec(self.cat_tree.mapToGlobal(pos))

    def _note_context_menu(self, pos):
        item = self.notes_list.itemAt(pos)
        if not item:
            return
        note_id = item.data(ROLE_NOTE_ID)
        menu = QMenu(self)
        if self._show_deleted:
            menu.addAction("Restaurer",               lambda: self._restore_note(note_id))
            menu.addAction("Supprimer définitivement",lambda: self._delete_note_permanent(note_id))
        else:
            menu.addAction("Mettre à la corbeille",   lambda: self._move_to_trash(note_id))
        menu.exec(self.notes_list.mapToGlobal(pos))

    def _tag_context_menu(self, pos):
        item = self.tags_list.itemAt(pos)
        if not item:
            return
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        menu = QMenu(self)
        menu.addAction("Supprimer le tag", lambda: self._delete_tag(tag_id))
        menu.exec(self.tags_list.mapToGlobal(pos))

    # ──────────────────────────── Actions notes ───────────────────────

    def create_note(self):
        note_id = self.db.create_note(
            title="Sans titre",
            category_id=self._current_category_id,
        )
        self._refresh_notes_list()
        # Sélectionner la nouvelle note
        for i in range(self.notes_list.count()):
            item = self.notes_list.item(i)
            if item.data(ROLE_NOTE_ID) == note_id:
                self.notes_list.setCurrentItem(item)
                break
        self.editor.load_note(note_id)
        self.editor.title_input.setFocus()
        self.editor.title_input.selectAll()

    def save_current(self):
        self.editor.save_note()

    def _move_to_trash(self, note_id: int):
        self.db.soft_delete_note(note_id)
        if self.editor.current_note_id == note_id:
            self.editor.show_empty_state()
        self._refresh_notes_list()

    def _restore_note(self, note_id: int):
        self.db.restore_note(note_id)
        self._refresh_notes_list()

    def _delete_note_permanent(self, note_id: int):
        reply = QMessageBox.question(
            self, "Suppression définitive",
            "Cette note et ses pièces jointes seront supprimées définitivement.\nContinuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            attachments = self.db.delete_note_permanently(note_id)
            for att in attachments:
                self.file_manager.delete_file(att["filepath"])
                if att["thumbnail_path"]:
                    self.file_manager.delete_file(att["thumbnail_path"])
            if self.editor.current_note_id == note_id:
                self.editor.show_empty_state()
            self._refresh_notes_list()

    # ──────────────────────────── Actions catégories ─────────────────

    def _add_category(self):
        name, ok = QInputDialog.getText(self, "Nouvelle catégorie", "Nom :")
        if ok and name.strip():
            self.db.create_category(name.strip())
            self._refresh_categories()

    def _rename_category(self, item: QTreeWidgetItem):
        cat_id   = item.data(0, Qt.ItemDataRole.UserRole)
        old_name = item.text(0).replace("📁  ", "")
        name, ok = QInputDialog.getText(self, "Renommer", "Nouveau nom :", text=old_name)
        if ok and name.strip():
            self.db.update_category(cat_id, name=name.strip())
            self._refresh_categories()

    def _change_cat_color(self, item: QTreeWidgetItem):
        cat_id    = item.data(0, Qt.ItemDataRole.UserRole)
        old_color = item.data(0, Qt.ItemDataRole.UserRole + 1) or "#4F46E5"
        color     = QColorDialog.getColor(QColor(old_color), self, "Couleur de la catégorie")
        if color.isValid():
            self.db.update_category(cat_id, color=color.name())
            self._refresh_categories()
            self._refresh_notes_list()

    def _delete_category(self, item: QTreeWidgetItem):
        cat_id = item.data(0, Qt.ItemDataRole.UserRole)
        reply  = QMessageBox.question(
            self, "Supprimer la catégorie",
            "Les notes de cette catégorie seront décatégorisées.\nContinuer ?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_category(cat_id)
            if self._current_category_id == cat_id:
                self._current_category_id = None
            self._refresh_categories()
            self._refresh_notes_list()

    # ──────────────────────────── Actions tags ────────────────────────

    def _delete_tag(self, tag_id: int):
        self.db.delete_tag(tag_id)
        if self._current_tag_id == tag_id:
            self._current_tag_id = None
        self._refresh_tags_list()
        self._refresh_notes_list()

    # ──────────────────────────── Import ──────────────────────────────

    def import_text_files(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Sélectionner le dossier à importer", str(Path.home())
        )
        if folder:
            count = self.file_manager.import_text_folder(folder, self.db)
            QMessageBox.information(
                self, "Import terminé",
                f"{count} fichier(s) importé(s) avec succès."
            )
            self._refresh_notes_list()

    # ──────────────────────────── Utilitaires ─────────────────────────

    def _show_all_notes(self):
        self._current_category_id = None
        self._current_tag_id      = None
        self._show_deleted        = False
        self.trash_btn.setChecked(False)
        self.search_bar.clear()
        self.type_combo.setCurrentIndex(0)
        self._refresh_notes_list()
        self.cat_tree.clearSelection()

    def _full_refresh(self):
        self._refresh_categories()
        self._refresh_tags_list()
        self._refresh_notes_list()

    def _about(self):
        QMessageBox.about(
            self, f"À propos de {config.APP_NAME}",
            f"<b>{config.APP_NAME}</b> v{config.VERSION}<br><br>"
            "Gestionnaire de notes avec support audio et images.<br>"
            "Base de données SQLite locale.<br><br>"
            "Données stockées dans :<br>"
            f"<code>{config.DATA_DIR}</code>",
        )

    def closeEvent(self, event):
        if self.editor._is_modified and self.editor.current_note_id:
            self.editor.save_note()
        if self.audio_recorder.is_recording:
            self.audio_recorder.stop()
        event.accept()
