"""Widgets réutilisables : délégué de liste, TagChip, AudioPlayer, ImageThumbnail."""

from pathlib import Path

from PyQt6.QtWidgets import (
    QStyledItemDelegate, QStyle, QWidget, QLabel, QPushButton,
    QHBoxLayout, QVBoxLayout, QFrame, QSizePolicy, QApplication,
)
from PyQt6.QtCore import Qt, QRect, QSize, pyqtSignal, QTimer
from PyQt6.QtGui import QPainter, QColor, QFont, QPixmap, QPen


# ─────────────────────────────────────────────────────────────────────────────
# Délégué personnalisé pour la liste des notes
# ─────────────────────────────────────────────────────────────────────────────

class NoteItemDelegate(QStyledItemDelegate):
    """Dessine chaque note dans la liste centrale."""

    ITEM_HEIGHT = 64

    def paint(self, painter: QPainter, option, index):
        painter.save()
        rect = option.rect

        is_selected = bool(option.state & QStyle.StateFlag.State_Selected)

        # Fond
        bg = QColor("#EEF2FF") if is_selected else QColor("#FFFFFF")
        painter.fillRect(rect, bg)

        # Bande colorée à gauche (couleur catégorie)
        cat_color = index.data(Qt.ItemDataRole.UserRole + 2)
        if cat_color:
            strip = QRect(rect.left(), rect.top(), 4, rect.height())
            painter.fillRect(strip, QColor(cat_color))

        # Zone de texte (indentée pour éviter la bande)
        tx = rect.left() + 12
        ty = rect.top()
        tw = rect.width() - 20
        th = rect.height()

        # Titre
        title_font = QFont()
        title_font.setPointSize(10)
        title_font.setBold(True)
        painter.setFont(title_font)
        title_color = QColor("#4F46E5") if is_selected else QColor("#111827")
        painter.setPen(title_color)
        title = index.data(Qt.ItemDataRole.DisplayRole) or "Sans titre"
        title_rect = QRect(tx, ty + 8, tw, 20)
        painter.drawText(title_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         title)

        # Métadonnées (date + icônes)
        meta_font = QFont()
        meta_font.setPointSize(8)
        painter.setFont(meta_font)
        painter.setPen(QColor("#9CA3AF"))

        date_str  = index.data(Qt.ItemDataRole.UserRole + 1)  or ""
        has_audio = index.data(Qt.ItemDataRole.UserRole + 3)
        has_image = index.data(Qt.ItemDataRole.UserRole + 4)
        has_video = index.data(Qt.ItemDataRole.UserRole + 5)
        icons     = ("🎤 " if has_audio else "") + ("🖼 " if has_image else "") + ("🎬 " if has_video else "")
        meta_rect = QRect(tx, ty + 32, tw, 16)
        painter.drawText(meta_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
                         f"{date_str}  {icons}")

        # Séparateur bas
        painter.setPen(QPen(QColor("#F3F4F6")))
        painter.drawLine(rect.left(), rect.bottom(), rect.right(), rect.bottom())

        # Bordure gauche si sélectionné
        if is_selected:
            painter.setPen(QPen(QColor("#4F46E5"), 3))
            painter.drawLine(rect.left(), rect.top(), rect.left(), rect.bottom())

        painter.restore()

    def sizeHint(self, option, index):
        return QSize(option.rect.width(), self.ITEM_HEIGHT)


# ─────────────────────────────────────────────────────────────────────────────
# Tag Chip
# ─────────────────────────────────────────────────────────────────────────────

class TagChip(QWidget):
    """Pastille de tag avec bouton de suppression optionnel."""

    remove_requested = pyqtSignal(int)   # tag_id

    def __init__(self, tag_id: int, name: str, color: str, removable=False, parent=None):
        super().__init__(parent)
        self.tag_id = tag_id
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setStyleSheet(
            f"background-color:{color}; border-radius:9px;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(7, 2, 7, 2)
        layout.setSpacing(3)

        lbl = QLabel(name)
        lbl.setStyleSheet("color:white; font-size:10px; font-weight:bold; background:transparent;")
        layout.addWidget(lbl)

        if removable:
            btn = QPushButton("×")
            btn.setFixedSize(14, 14)
            btn.setStyleSheet(
                "QPushButton{background:transparent;color:white;border:none;font-size:13px;padding:0;}"
                "QPushButton:hover{color:#FFD0D0;}"
            )
            btn.clicked.connect(lambda: self.remove_requested.emit(self.tag_id))
            layout.addWidget(btn)

        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


# ─────────────────────────────────────────────────────────────────────────────
# Miniature image
# ─────────────────────────────────────────────────────────────────────────────

class ImageThumbnailWidget(QFrame):
    """Miniature d'une pièce jointe image avec boutons ouvrir/supprimer."""

    delete_requested = pyqtSignal(int)   # attachment_id

    def __init__(self, attachment, parent=None):
        super().__init__(parent)
        self.att_id   = attachment["id"]
        self.filepath = attachment["filepath"]
        self.setObjectName("attach_widget")
        self.setFixedSize(140, 120)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 4)
        layout.setSpacing(4)

        # Miniature
        thumb_path = attachment["thumbnail_path"] or attachment["filepath"]
        pix = QPixmap(thumb_path)
        lbl = QLabel()
        if pix.isNull():
            lbl.setText("🖼")
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        else:
            lbl.setPixmap(
                pix.scaled(128, 80,
                           Qt.AspectRatioMode.KeepAspectRatio,
                           Qt.TransformationMode.SmoothTransformation)
            )
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setCursor(Qt.CursorShape.PointingHandCursor)
        lbl.mousePressEvent = lambda _: self._open_full()
        layout.addWidget(lbl)

        # Boutons
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)
        filename = Path(self.filepath).name
        name_lbl = QLabel(filename[:16] + "…" if len(filename) > 16 else filename)
        name_lbl.setStyleSheet("font-size:9px; color:#6B7280;")
        name_lbl.setToolTip(filename)
        btn_row.addWidget(name_lbl, 1)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("attach_del_btn")
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("Supprimer")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.att_id))
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    def _open_full(self):
        """Ouvre l'image dans le visualiseur par défaut du système."""
        import subprocess, shutil
        for viewer in ("eog", "shotwell", "feh", "display", "xdg-open"):
            if shutil.which(viewer):
                subprocess.Popen([viewer, self.filepath])
                return
        subprocess.Popen(["xdg-open", self.filepath])


# ─────────────────────────────────────────────────────────────────────────────
# Lecteur audio
# ─────────────────────────────────────────────────────────────────────────────

class AudioPlayerWidget(QFrame):
    """Widget compact pour lire un enregistrement audio."""

    delete_requested = pyqtSignal(int)   # attachment_id

    def __init__(self, attachment, audio_player, parent=None):
        super().__init__(parent)
        self.att_id       = attachment["id"]
        self.filepath     = attachment["filepath"]
        self.audio_player = audio_player
        self.setObjectName("attach_widget")
        self.setFixedSize(160, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        # Icône + durée
        dur = attachment["duration"] or 0
        mins, secs = divmod(int(dur), 60)
        dur_str = f"{mins:02d}:{secs:02d}"

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("🎤")
        icon_lbl.setStyleSheet("font-size:20px;")
        top_row.addWidget(icon_lbl)
        top_row.addStretch()
        dur_lbl = QLabel(dur_str)
        dur_lbl.setStyleSheet("color:#4F46E5; font-weight:bold; font-size:12px;")
        top_row.addWidget(dur_lbl)
        layout.addLayout(top_row)

        # Transcription (si disponible)
        trans = attachment["transcription"] or ""
        if trans:
            t_lbl = QLabel(trans[:40] + ("…" if len(trans) > 40 else ""))
            t_lbl.setStyleSheet("font-size:9px; color:#6B7280;")
            t_lbl.setToolTip(trans)
            layout.addWidget(t_lbl)
        else:
            layout.addStretch()

        # Boutons lecture / supprimer
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        self.play_btn = QPushButton("▶ Lire")
        self.play_btn.setObjectName("attach_play_btn")
        self.play_btn.setCheckable(True)
        self.play_btn.setFixedHeight(22)
        self.play_btn.clicked.connect(self._toggle_play)
        btn_row.addWidget(self.play_btn, 1)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("attach_del_btn")
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("Supprimer")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.att_id))
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

        # Connexions lecteur
        self.audio_player.playback_stopped.connect(self._on_stopped)

    def _toggle_play(self, checked):
        if checked:
            self.play_btn.setText("⏹ Stop")
            self.audio_player.play(self.filepath)
        else:
            self.audio_player.stop()
            self.play_btn.setText("▶ Lire")

    def _on_stopped(self):
        self.play_btn.setChecked(False)
        self.play_btn.setText("▶ Lire")


# ─────────────────────────────────────────────────────────────────────────────
# Lecteur vidéo
# ─────────────────────────────────────────────────────────────────────────────

class VideoPlayerWidget(QFrame):
    """Widget compact pour afficher et ouvrir une pièce jointe vidéo."""

    delete_requested = pyqtSignal(int)   # attachment_id

    def __init__(self, attachment, parent=None):
        super().__init__(parent)
        self.att_id   = attachment["id"]
        self.filepath = attachment["filepath"]
        self.setObjectName("attach_widget")
        self.setFixedSize(160, 80)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 6)
        layout.setSpacing(4)

        # Icône + durée
        dur = attachment["duration"] or 0
        mins, secs = divmod(int(dur), 60)
        dur_str = f"{mins:02d}:{secs:02d}" if dur else "--:--"

        top_row = QHBoxLayout()
        top_row.setContentsMargins(0, 0, 0, 0)
        icon_lbl = QLabel("🎬")
        icon_lbl.setStyleSheet("font-size:20px;")
        top_row.addWidget(icon_lbl)
        top_row.addStretch()
        dur_lbl = QLabel(dur_str)
        dur_lbl.setStyleSheet("color:#7C3AED; font-weight:bold; font-size:12px;")
        top_row.addWidget(dur_lbl)
        layout.addLayout(top_row)

        # Nom du fichier
        filename = Path(self.filepath).name
        name_lbl = QLabel(filename[:20] + "…" if len(filename) > 20 else filename)
        name_lbl.setStyleSheet("font-size:9px; color:#6B7280;")
        name_lbl.setToolTip(filename)
        layout.addWidget(name_lbl)

        # Boutons ouvrir / supprimer
        btn_row = QHBoxLayout()
        btn_row.setContentsMargins(0, 0, 0, 0)

        open_btn = QPushButton("▶ Ouvrir")
        open_btn.setObjectName("attach_play_btn")
        open_btn.setFixedHeight(22)
        open_btn.clicked.connect(self._open_video)
        btn_row.addWidget(open_btn, 1)

        del_btn = QPushButton("🗑")
        del_btn.setObjectName("attach_del_btn")
        del_btn.setFixedSize(22, 22)
        del_btn.setToolTip("Supprimer")
        del_btn.clicked.connect(lambda: self.delete_requested.emit(self.att_id))
        btn_row.addWidget(del_btn)
        layout.addLayout(btn_row)

    def _open_video(self):
        """Ouvre la vidéo dans le lecteur système."""
        import subprocess, shutil
        for player in ("mpv", "vlc", "totem", "xdg-open"):
            if shutil.which(player):
                subprocess.Popen([player, self.filepath])
                return
        subprocess.Popen(["xdg-open", self.filepath])
