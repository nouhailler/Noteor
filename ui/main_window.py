"""Fenêtre principale de Noteor avec les 3 panneaux."""

from pathlib import Path

from datetime import date, timedelta

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QSplitter, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTreeWidget, QTreeWidgetItem,
    QListWidget, QListWidgetItem, QComboBox, QStatusBar,
    QMenu, QMessageBox, QInputDialog, QFileDialog, QColorDialog,
    QAbstractItemView, QDateEdit, QTabWidget, QDialog, QDialogButtonBox,
)
from PyQt6.QtCore import Qt, QTimer, QDate, QMimeData, QMarginsF, pyqtSignal
from PyQt6.QtGui import QAction, QColor, QIcon, QKeySequence, QDrag, QPixmap, QPainter, QFont, QPageLayout, QPageSize
from PyQt6.QtPrintSupport import QPrinter

import config
from database import Database
from core.audio_recorder import AudioRecorder
from core.file_manager import FileManager
from core.webcam_recorder import WebcamRecorder
from ui.editor import EditorPanel
from ui.widgets import NoteItemDelegate
from ui.help_window import HelpWindow


# Rôles personnalisés dans QListWidgetItem
ROLE_NOTE_ID   = Qt.ItemDataRole.UserRole
ROLE_DATE      = Qt.ItemDataRole.UserRole + 1
ROLE_CAT_COLOR = Qt.ItemDataRole.UserRole + 2
ROLE_AUDIO     = Qt.ItemDataRole.UserRole + 3
ROLE_IMAGE     = Qt.ItemDataRole.UserRole + 4
ROLE_VIDEO     = Qt.ItemDataRole.UserRole + 5

_MIME_NOTE_ID = "application/x-noteor-note-id"


class _DraggableNotesList(QListWidget):
    """QListWidget avec drag activé — encode le note_id dans le MIME data."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setDragDropMode(QAbstractItemView.DragDropMode.DragOnly)

    def startDrag(self, supported_actions):
        item = self.currentItem()
        if not item:
            return
        note_id = item.data(ROLE_NOTE_ID)
        if note_id is None:
            return

        mime = QMimeData()
        mime.setData(_MIME_NOTE_ID, str(note_id).encode())

        # Pixmap de drag : miniature du titre de la note
        title = item.data(Qt.ItemDataRole.DisplayRole) or "Note"
        pix = QPixmap(200, 28)
        pix.fill(QColor("#EEF2FF"))
        painter = QPainter(pix)
        painter.setFont(QFont("sans-serif", 10))
        painter.setPen(QColor("#4F46E5"))
        painter.drawText(8, 20, title[:35] + ("…" if len(title) > 35 else ""))
        painter.end()

        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.setPixmap(pix)
        drag.setHotSpot(pix.rect().center())
        drag.exec(Qt.DropAction.MoveAction)


class _FolderDropTree(QTreeWidget):
    """QTreeWidget qui accepte les drops de notes et émet note_dropped(note_id, folder_id)."""

    note_dropped = pyqtSignal(int, object)   # note_id, folder_id (int ou None)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._highlighted_item = None

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat(_MIME_NOTE_ID):
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event):
        if event.mimeData().hasFormat(_MIME_NOTE_ID):
            item = self.itemAt(event.position().toPoint())
            # Met en évidence le dossier survolé
            if item is not self._highlighted_item:
                if self._highlighted_item:
                    self._highlighted_item.setBackground(0, QColor("transparent"))
                self._highlighted_item = item
                if item:
                    item.setBackground(0, QColor("#C7D2FE"))
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dragLeaveEvent(self, event):
        self._clear_highlight()
        super().dragLeaveEvent(event)

    def dropEvent(self, event):
        self._clear_highlight()
        if event.mimeData().hasFormat(_MIME_NOTE_ID):
            raw = event.mimeData().data(_MIME_NOTE_ID)
            note_id = int(bytes(raw).decode())
            item = self.itemAt(event.position().toPoint())
            folder_id = item.data(0, Qt.ItemDataRole.UserRole) if item else None
            self.note_dropped.emit(note_id, folder_id)
            event.acceptProposedAction()
        else:
            super().dropEvent(event)

    def _clear_highlight(self):
        if self._highlighted_item:
            self._highlighted_item.setBackground(0, QColor("transparent"))
            self._highlighted_item = None


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # ── Noyau ────────────────────────────────────────────────────
        self.db              = Database()
        self.file_manager    = FileManager()
        self.audio_recorder  = AudioRecorder()
        self.webcam_recorder = WebcamRecorder()

        # ── État des filtres ─────────────────────────────────────────
        self._current_category_id = None   # None = toutes les notes
        self._current_folder_id   = None   # None = tous les dossiers
        self._current_tag_id      = None
        self._show_deleted        = False
        self._type_filter         = None   # 'image' | 'audio' | 'video' | None
        self._search_text         = ""
        self._date_from           = None   # str "YYYY-MM-DD" ou None
        self._date_to             = None   # str "YYYY-MM-DD" ou None

        self._building_tree   = False
        self._building_notes  = False
        self._help_window     = None

        self.setWindowTitle(config.WINDOW_TITLE)
        self.setMinimumSize(980, 640)
        self.resize(1200, 760)

        self._build_ui()
        self._build_menu()
        self._refresh_folders()
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

        self.editor = EditorPanel(self.db, self.file_manager, self.audio_recorder, self.webcam_recorder)
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

        # Barre de recherche (toujours visible)
        self.search_bar = QLineEdit()
        self.search_bar.setObjectName("search_bar")
        self.search_bar.setPlaceholderText("🔍 Rechercher…")
        self.search_bar.textChanged.connect(self._on_search_changed)
        layout.addWidget(self.search_bar)

        # Bouton nouvelle note (toujours visible)
        new_btn = QPushButton("+ Nouvelle note")
        new_btn.setObjectName("new_note_btn")
        new_btn.clicked.connect(self.create_note)
        layout.addWidget(new_btn)

        # Onglets Dossiers / Organisation
        self.left_tabs = QTabWidget()
        self.left_tabs.setObjectName("left_tabs")
        self.left_tabs.addTab(self._build_folder_tab(),       "📂 Dossiers")
        self.left_tabs.addTab(self._build_organisation_tab(), "🏷 Organisation")
        layout.addWidget(self.left_tabs, 1)

        return panel

    def _build_folder_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(4)

        # En-tête + bouton nouveau dossier
        hdr = QHBoxLayout()
        hdr.addStretch()
        add_folder_btn = QPushButton("+ Dossier")
        add_folder_btn.setObjectName("action_btn")
        add_folder_btn.setFixedHeight(24)
        add_folder_btn.clicked.connect(self._add_folder)
        hdr.addWidget(add_folder_btn)
        lay.addLayout(hdr)

        self.folder_tree = _FolderDropTree()
        self.folder_tree.setHeaderHidden(True)
        self.folder_tree.setRootIsDecorated(True)
        self.folder_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.folder_tree.customContextMenuRequested.connect(self._folder_context_menu)
        self.folder_tree.itemClicked.connect(self._on_folder_clicked)
        self.folder_tree.note_dropped.connect(self._on_note_dropped_to_folder)
        lay.addWidget(self.folder_tree, 1)

        return w

    def _build_organisation_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(0, 6, 0, 0)
        lay.setSpacing(6)

        # Catégories
        cat_lbl = QLabel("CATÉGORIES")
        cat_lbl.setObjectName("section_header")
        lay.addWidget(cat_lbl)

        self.cat_tree = QTreeWidget()
        self.cat_tree.setHeaderHidden(True)
        self.cat_tree.setRootIsDecorated(True)
        self.cat_tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.cat_tree.customContextMenuRequested.connect(self._cat_context_menu)
        self.cat_tree.itemClicked.connect(self._on_category_clicked)
        self.cat_tree.setMaximumHeight(180)
        lay.addWidget(self.cat_tree)

        # Tags
        tag_lbl = QLabel("TAGS")
        tag_lbl.setObjectName("section_header")
        lay.addWidget(tag_lbl)

        self.tags_list = QListWidget()
        self.tags_list.setObjectName("tags_list")
        self.tags_list.itemClicked.connect(self._on_tag_clicked)
        self.tags_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tags_list.customContextMenuRequested.connect(self._tag_context_menu)
        lay.addWidget(self.tags_list, 1)

        # Filtre type
        type_lbl = QLabel("FILTRER PAR TYPE")
        type_lbl.setObjectName("section_header")
        lay.addWidget(type_lbl)

        self.type_combo = QComboBox()
        self.type_combo.setObjectName("filter_combo")
        self.type_combo.addItems(["Toutes les notes", "Avec audio 🎤", "Avec images 🖼", "Avec vidéos 🎬"])
        self.type_combo.currentIndexChanged.connect(self._on_type_filter_changed)
        lay.addWidget(self.type_combo)

        # Filtre date
        date_lbl = QLabel("FILTRER PAR DATE")
        date_lbl.setObjectName("section_header")
        lay.addWidget(date_lbl)

        self.date_combo = QComboBox()
        self.date_combo.setObjectName("filter_combo")
        self.date_combo.addItems([
            "Toutes les dates", "Aujourd'hui", "7 derniers jours",
            "30 derniers jours", "Cette année", "Période…",
        ])
        self.date_combo.currentIndexChanged.connect(self._on_date_preset_changed)
        lay.addWidget(self.date_combo)

        self.date_range_widget = QWidget()
        dr = QHBoxLayout(self.date_range_widget)
        dr.setContentsMargins(0, 2, 0, 2)
        dr.setSpacing(4)
        self.date_from_edit = QDateEdit()
        self.date_from_edit.setCalendarPopup(True)
        self.date_from_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_from_edit.setDate(QDate.currentDate().addMonths(-1))
        self.date_from_edit.dateChanged.connect(self._on_date_range_changed)
        dr.addWidget(self.date_from_edit)
        dr.addWidget(QLabel("→"))
        self.date_to_edit = QDateEdit()
        self.date_to_edit.setCalendarPopup(True)
        self.date_to_edit.setDisplayFormat("dd/MM/yyyy")
        self.date_to_edit.setDate(QDate.currentDate())
        self.date_to_edit.dateChanged.connect(self._on_date_range_changed)
        dr.addWidget(self.date_to_edit)
        self.date_range_widget.setVisible(False)
        lay.addWidget(self.date_range_widget)

        # Corbeille
        self.trash_btn = QPushButton("🗑  Corbeille")
        self.trash_btn.setObjectName("trash_btn")
        self.trash_btn.setCheckable(True)
        self.trash_btn.clicked.connect(self._on_trash_clicked)
        lay.addWidget(self.trash_btn)

        return w

    # ── Panneau central ───────────────────────────────────────────────

    def _build_center_panel(self) -> QWidget:
        panel = QWidget()
        panel.setMinimumWidth(config.CENTER_PANEL_MIN_WIDTH)
        panel.setMaximumWidth(config.CENTER_PANEL_MAX_WIDTH)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.notes_list = _DraggableNotesList()
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
        self._add_action(file_menu, "Exporter en PDF…",       self._export_current_note_pdf, "Ctrl+E")
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
        self._add_action(help_menu, "Aide complète",          self._show_help,   "F1")
        help_menu.addSeparator()
        self._add_action(help_menu, "À propos",               self._about)

    @staticmethod
    def _add_action(menu, label, slot, shortcut=None):
        act = QAction(label, menu.parent())
        if shortcut:
            act.setShortcut(QKeySequence(shortcut))
        act.triggered.connect(slot)
        menu.addAction(act)

    # ──────────────────────────── Remplissage données ─────────────────

    def _refresh_folders(self):
        self.folder_tree.clear()

        all_item = QTreeWidgetItem(["📂  Tous les dossiers"])
        all_item.setData(0, Qt.ItemDataRole.UserRole, None)
        all_item.setForeground(0, QColor("#6366F1"))
        self.folder_tree.addTopLevelItem(all_item)

        folders = self.db.get_all_folders()
        by_id = {}
        for f in folders:
            count = f["note_count"]
            label = f"📁  {f['name']}"
            if count:
                label += f"  ({count})"
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, f["id"])
            item.setToolTip(0, f"{count} note(s)")
            by_id[f["id"]] = item

        for f in folders:
            item = by_id[f["id"]]
            if f["parent_id"] and f["parent_id"] in by_id:
                by_id[f["parent_id"]].addChild(item)
            else:
                self.folder_tree.addTopLevelItem(item)

        self.folder_tree.expandAll()

        if self._current_folder_id is None:
            self.folder_tree.setCurrentItem(all_item)

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
            folder_id=self._current_folder_id,
            deleted=self._show_deleted,
            tag_id=self._current_tag_id,
            search=self._search_text or None,
            type_filter=self._type_filter,
            date_from=self._date_from,
            date_to=self._date_to,
        )

        item_to_select = None
        for note in notes:
            item = QListWidgetItem()
            item.setData(Qt.ItemDataRole.DisplayRole, note["title"])
            item.setData(ROLE_NOTE_ID,   note["id"])
            item.setData(ROLE_DATE,      note["updated_at"][:16] if note["updated_at"] else "")
            item.setData(ROLE_CAT_COLOR, note["category_color"])
            item.setData(ROLE_AUDIO,     bool(note["audio_count"]))
            item.setData(ROLE_IMAGE,     bool(note["image_count"]))
            item.setData(ROLE_VIDEO,     bool(note["video_count"]))
            self.notes_list.addItem(item)
            if note["id"] == prev_id:
                item_to_select = item

        # Restaurer la sélection une fois la liste entièrement construite
        if item_to_select is not None:
            self.notes_list.setCurrentItem(item_to_select)
            self.notes_list.scrollToItem(item_to_select)

        count = self.notes_list.count()
        noun  = "note" if count <= 1 else "notes"
        self.statusBar().showMessage(f"{count} {noun}")
        self._building_notes = False

    # ──────────────────────────── Événements UI ───────────────────────

    def _on_folder_clicked(self, item: QTreeWidgetItem, column: int):
        self._current_folder_id   = item.data(0, Qt.ItemDataRole.UserRole)
        self._current_category_id = None
        self._current_tag_id      = None
        self._show_deleted        = False
        self.trash_btn.setChecked(False)
        self.cat_tree.clearSelection()
        self.tags_list.clearSelection()
        self._refresh_notes_list()

    def _on_category_clicked(self, item: QTreeWidgetItem, column: int):
        if self._building_tree:
            return
        self._current_category_id = item.data(0, Qt.ItemDataRole.UserRole)
        self._current_folder_id   = None
        self._current_tag_id      = None
        self._show_deleted        = False
        self.trash_btn.setChecked(False)
        self.tags_list.clearSelection()
        self._refresh_notes_list()

    def _on_tag_clicked(self, item: QListWidgetItem):
        tag_id = item.data(Qt.ItemDataRole.UserRole)
        if self._current_tag_id == tag_id:
            self._current_tag_id = None
            self.tags_list.clearSelection()
        else:
            self._current_tag_id  = tag_id
            self._current_folder_id = None
        self._refresh_notes_list()

    def _on_trash_clicked(self, checked: bool):
        self._show_deleted        = checked
        self._current_category_id = None
        self._current_folder_id   = None
        self._current_tag_id      = None
        self.cat_tree.clearSelection()
        self.tags_list.clearSelection()
        self.folder_tree.clearSelection()
        self._refresh_notes_list()

    def _on_search_changed(self, text: str):
        self._search_text = text
        self._refresh_notes_list()

    def _on_type_filter_changed(self, index: int):
        self._type_filter = [None, "audio", "image", "video"][index]
        self._refresh_notes_list()

    def _on_date_preset_changed(self, index: int):
        today = date.today()
        presets = {
            0: (None, None),                                          # Toutes les dates
            1: (today.isoformat(), today.isoformat()),               # Aujourd'hui
            2: ((today - timedelta(days=6)).isoformat(), today.isoformat()),  # 7 jours
            3: ((today - timedelta(days=29)).isoformat(), today.isoformat()), # 30 jours
            4: (date(today.year, 1, 1).isoformat(), today.isoformat()),       # Cette année
        }
        is_custom = (index == 5)
        self.date_range_widget.setVisible(is_custom)
        if is_custom:
            self._on_date_range_changed()
        else:
            self._date_from, self._date_to = presets.get(index, (None, None))
            self._refresh_notes_list()

    def _on_date_range_changed(self):
        self._date_from = self.date_from_edit.date().toString("yyyy-MM-dd")
        self._date_to   = self.date_to_edit.date().toString("yyyy-MM-dd")
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
                        item.setData(ROLE_VIDEO, bool(n["video_count"]))
                        break
                self.notes_list.viewport().update()
                break
        self.statusBar().showMessage("Note sauvegardée", 3000)

    # ──────────────────────────── Menus contextuels ───────────────────

    def _folder_context_menu(self, pos):
        item  = self.folder_tree.itemAt(pos)
        menu  = QMenu(self)
        menu.addAction("Nouveau dossier", self._add_folder)
        if item and item.data(0, Qt.ItemDataRole.UserRole) is not None:
            folder_id = item.data(0, Qt.ItemDataRole.UserRole)
            menu.addAction("Nouveau sous-dossier", lambda: self._add_subfolder(folder_id))
            menu.addAction("Renommer",             lambda: self._rename_folder(item))
            menu.addSeparator()
            menu.addAction("Supprimer",            lambda: self._delete_folder(item))
        menu.exec(self.folder_tree.mapToGlobal(pos))

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
            menu.addAction("Exporter en PDF…",           lambda: self._export_note_pdf(note_id))
            menu.addAction("Déplacer vers un dossier…",  lambda: self._move_note_to_folder_dialog(note_id))
            menu.addSeparator()
            menu.addAction("Mettre à la corbeille",      lambda: self._move_to_trash(note_id))
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
            folder_id=self._current_folder_id,
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

    # ──────────────────────────── Actions dossiers ───────────────────

    def _add_folder(self):
        name, ok = QInputDialog.getText(self, "Nouveau dossier", "Nom :")
        if ok and name.strip():
            self.db.create_folder(name.strip())
            self._refresh_folders()

    def _add_subfolder(self, parent_id: int):
        name, ok = QInputDialog.getText(self, "Nouveau sous-dossier", "Nom :")
        if ok and name.strip():
            self.db.create_folder(name.strip(), parent_id=parent_id)
            self._refresh_folders()

    def _rename_folder(self, item: QTreeWidgetItem):
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        old_name  = item.text(0).split("  (")[0].replace("📁  ", "")
        name, ok  = QInputDialog.getText(self, "Renommer", "Nouveau nom :", text=old_name)
        if ok and name.strip():
            self.db.rename_folder(folder_id, name.strip())
            self._refresh_folders()

    def _delete_folder(self, item: QTreeWidgetItem):
        folder_id = item.data(0, Qt.ItemDataRole.UserRole)
        folder_name = item.text(0).split("  (")[0].replace("📁  ", "")
        reply = QMessageBox.question(
            self, "Supprimer le dossier",
            f"Supprimer « {folder_name} » et ses sous-dossiers ?\n"
            "Les notes qu'il contient ne seront pas supprimées.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self.db.delete_folder(folder_id)
            if self._current_folder_id == folder_id:
                self._current_folder_id = None
            self._refresh_folders()
            self._refresh_notes_list()

    def _on_note_dropped_to_folder(self, note_id: int, folder_id):
        self.db.move_note_to_folder(note_id, folder_id)
        self._refresh_folders()
        self._refresh_notes_list()
        label = "retiré de tout dossier" if folder_id is None else "déplacé dans le dossier"
        self.statusBar().showMessage(f"Note {label}", 3000)

    def _move_note_to_folder_dialog(self, note_id: int):
        folders = self.db.get_all_folders()
        dlg = _FolderPickerDialog(folders, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            target = dlg.selected_folder_id   # None = retirer du dossier
            self.db.move_note_to_folder(note_id, target)
            self._refresh_folders()
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

    # ──────────────────────────── Export PDF ──────────────────────────

    def _export_current_note_pdf(self):
        note_id = self.editor.current_note_id
        if not note_id:
            QMessageBox.information(self, "Export PDF",
                                    "Aucune note sélectionnée.\n"
                                    "Cliquez sur une note puis réessayez.")
            return
        self._export_note_pdf(note_id)

    def _export_note_pdf(self, note_id: int):
        note = self.db.get_note(note_id)
        if not note:
            return

        # ── Dialogue de sauvegarde ────────────────────────────────────
        safe_title = "".join(c for c in note["title"] if c not in r'\/:*?"<>|').strip() or "note"
        default_path = Path.home() / f"{safe_title}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Exporter en PDF", str(default_path), "PDF (*.pdf)"
        )
        if not path:
            return

        # ── Markdown → HTML ───────────────────────────────────────────
        content = note["content"] or ""
        try:
            import markdown as _md
            body_html = _md.markdown(
                content,
                extensions=["fenced_code", "tables", "nl2br", "sane_lists"],
            )
        except ImportError:
            body_html = content.replace("&", "&amp;").replace("<", "&lt;").replace("\n", "<br>")

        created = (note["created_at"] or "")[:16]
        updated = (note["updated_at"] or "")[:16]

        # Récupère les tags et les images attachées
        tags = self.db.get_note_tags(note_id)
        tag_str = ",  ".join(t["name"] for t in tags) if tags else ""

        attachments = self.db.get_attachments(note_id)
        images = [a for a in attachments
                  if a["type"] == "image" and Path(a["filepath"]).exists()]

        # ── Section images ────────────────────────────────────────────
        images_html = ""
        if images:
            images_html = (
                "<hr style='margin:28px 0 20px; border:none;"
                " border-top:1px solid #e5e7eb;'>"
                "<h2 style='margin-bottom:16px;'>Captures et images</h2>"
            )
            for img in images:
                data_uri = self._image_to_base64_uri(img["filepath"])
                if data_uri:
                    images_html += (
                        f"<div style='margin:16px 0; text-align:center;'>"
                        f"<img src='{data_uri}'><br>"
                        f"<span style='color:#6b7280; font-size:9pt;'>"
                        f"{img['filename']}</span></div>"
                    )

        html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body      {{ font-family: Georgia, 'Times New Roman', serif;
               font-size: 11pt; line-height: 1.7; color: #1f2937;
               margin: 0; padding: 0; }}
  .header   {{ border-bottom: 2px solid #4F46E5; padding-bottom: 10px; margin-bottom: 18px; }}
  h1        {{ font-size: 20pt; color: #111827; margin: 0 0 4px 0; }}
  .meta     {{ color: #6b7280; font-size: 9pt; }}
  .tags     {{ color: #4F46E5; font-size: 9pt; margin-top: 2px; }}
  h2        {{ font-size: 14pt; color: #374151; margin-top: 22px; }}
  h3        {{ font-size: 12pt; color: #374151; }}
  code      {{ font-family: 'Courier New', monospace; font-size: 9.5pt;
               background: #f3f4f6; padding: 1px 4px; border-radius: 3px; }}
  pre       {{ background: #f3f4f6; padding: 10px 14px; border-radius: 5px;
               border-left: 3px solid #4F46E5; overflow-wrap: break-word; }}
  pre code  {{ background: none; padding: 0; }}
  blockquote{{ border-left: 3px solid #d1d5db; margin-left: 0;
               padding-left: 14px; color: #6b7280; font-style: italic; }}
  table     {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}
  th, td    {{ border: 1px solid #e5e7eb; padding: 6px 10px; text-align: left; }}
  th        {{ background: #f9fafb; font-weight: bold; }}
  a         {{ color: #4F46E5; }}
</style>
</head><body>
<div class="header">
  <h1>{note["title"]}</h1>
  <div class="meta">Créé le {created} &nbsp;·&nbsp; Modifié le {updated}</div>
  {"<div class='tags'>🏷 " + tag_str + "</div>" if tag_str else ""}
</div>
{body_html}
{images_html}
</body></html>"""

        # ── Impression vers PDF ───────────────────────────────────────
        from PyQt6.QtGui import QTextDocument
        printer = QPrinter(QPrinter.PrinterMode.HighResolution)
        printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat)
        printer.setOutputFileName(path)
        printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
        printer.setPageMargins(
            QMarginsF(18, 18, 18, 18), QPageLayout.Unit.Millimeter
        )

        doc = QTextDocument()
        doc.setHtml(html)
        doc.setPageSize(printer.pageRect(QPrinter.Unit.Point).size())
        doc.print(printer)

        self.statusBar().showMessage(f"PDF exporté : {path}", 5000)

    @staticmethod
    def _image_to_base64_uri(filepath: str, max_px: int = 2000) -> str:
        """Charge une image, la redimensionne et retourne un data URI base64 PNG.
        max_px = 2000 : suffit pour A4 300 DPI (~2050 px de large imprimable)."""
        import base64
        from PyQt6.QtCore import QBuffer, QIODevice
        pix = QPixmap(filepath)
        if pix.isNull():
            return ""
        if pix.width() > max_px:
            pix = pix.scaledToWidth(max_px, Qt.TransformationMode.SmoothTransformation)
        buf = QBuffer()
        buf.open(QIODevice.OpenModeFlag.WriteOnly)
        pix.save(buf, "PNG")
        data = base64.b64encode(bytes(buf.data())).decode()
        return f"data:image/png;base64,{data}"

    # ──────────────────────────── Utilitaires ─────────────────────────

    def _show_all_notes(self):
        self._current_category_id = None
        self._current_folder_id   = None
        self._current_tag_id      = None
        self._show_deleted        = False
        self._date_from           = None
        self._date_to             = None
        self.trash_btn.setChecked(False)
        self.search_bar.clear()
        self.type_combo.setCurrentIndex(0)
        self.date_combo.setCurrentIndex(0)
        self._refresh_notes_list()
        self.cat_tree.clearSelection()
        self.folder_tree.clearSelection()

    def _full_refresh(self):
        self._refresh_folders()
        self._refresh_categories()
        self._refresh_tags_list()
        self._refresh_notes_list()

    def _show_help(self):
        if self._help_window is None:
            self._help_window = HelpWindow(self)
        self._help_window.show()
        self._help_window.raise_()
        self._help_window.activateWindow()

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


# ─────────────────────────────────────────────────────────────────────────────

class _FolderPickerDialog(QDialog):
    """Dialog de sélection d'un dossier (ou 'Aucun dossier')."""

    def __init__(self, folders, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Déplacer vers un dossier")
        self.setMinimumWidth(280)
        self._selected_folder_id = ...   # sentinel = pas encore cliqué

        layout = QVBoxLayout(self)

        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)

        none_item = QTreeWidgetItem(["(Aucun dossier)"])
        none_item.setData(0, Qt.ItemDataRole.UserRole, None)
        self.tree.addTopLevelItem(none_item)

        by_id = {}
        for f in folders:
            count = f["note_count"]
            label = f"📁  {f['name']}"
            if count:
                label += f"  ({count})"
            item = QTreeWidgetItem([label])
            item.setData(0, Qt.ItemDataRole.UserRole, f["id"])
            by_id[f["id"]] = item

        for f in folders:
            item = by_id[f["id"]]
            if f["parent_id"] and f["parent_id"] in by_id:
                by_id[f["parent_id"]].addChild(item)
            else:
                self.tree.addTopLevelItem(item)

        self.tree.expandAll()
        self.tree.itemClicked.connect(
            lambda it, _: setattr(self, "_selected_folder_id",
                                  it.data(0, Qt.ItemDataRole.UserRole))
        )
        layout.addWidget(self.tree)

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self.accept)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    @property
    def selected_folder_id(self):
        """Retourne l'id du dossier sélectionné, None = aucun dossier."""
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.ItemDataRole.UserRole)
        return self._selected_folder_id if self._selected_folder_id is not ... else None
