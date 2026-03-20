import shutil
from pathlib import Path
from datetime import datetime

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

import config

try:
    from PIL import Image as PILImage
    PILLOW_AVAILABLE = True
except ImportError:
    PILLOW_AVAILABLE = False


class FileManager:

    # ──────────────── Images ─────────────────────────────────────────

    def import_image(self, source_path: str) -> tuple[str, str]:
        """Copie l'image dans le dossier media et génère une miniature.
        Retourne (filepath, thumbnail_path)."""
        source    = Path(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"img_{timestamp}{source.suffix.lower()}"
        dest      = config.IMAGE_DIR / filename

        shutil.copy2(source, dest)
        thumb_path = self._create_thumbnail(dest)
        return str(dest), thumb_path

    def take_screenshot(self) -> tuple[str, str] | None:
        """Capture l'écran principal. Retourne (filepath, thumbnail_path) ou None."""
        screen = QApplication.primaryScreen()
        if not screen:
            return None

        pixmap    = screen.grabWindow(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"screenshot_{timestamp}.png"
        filepath  = config.IMAGE_DIR / filename

        pixmap.save(str(filepath), "PNG")
        thumb_path = self._create_thumbnail(filepath)
        return str(filepath), thumb_path

    def _create_thumbnail(self, image_path: Path) -> str:
        """Crée une miniature avec Pillow ou via Qt si Pillow absent."""
        thumb_name = f"thumb_{image_path.name}"
        thumb_path = config.THUMB_DIR / thumb_name

        if PILLOW_AVAILABLE:
            try:
                with PILImage.open(image_path) as img:
                    img.thumbnail(config.THUMBNAIL_SIZE, PILImage.Resampling.LANCZOS)
                    # Convert RGBA → RGB for JPEG compatibility
                    if img.mode in ("RGBA", "P"):
                        img = img.convert("RGB")
                    img.save(str(thumb_path))
                return str(thumb_path)
            except Exception:
                pass

        # Fallback : Qt redimensionnement
        try:
            from PyQt6.QtGui import QPixmap
            pix = QPixmap(str(image_path))
            if not pix.isNull():
                scaled = pix.scaled(
                    config.THUMBNAIL_SIZE[0],
                    config.THUMBNAIL_SIZE[1],
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                scaled.save(str(thumb_path))
                return str(thumb_path)
        except Exception:
            pass

        return str(image_path)

    # ──────────────── Fichiers texte / Markdown ───────────────────────

    def import_text_folder(self, folder_path: str, db) -> int:
        """Importe les fichiers .txt et .md d'un dossier comme notes.
        Retourne le nombre de notes créées."""
        folder = Path(folder_path)
        count  = 0

        for ext in ("*.txt", "*.md"):
            for file_path in sorted(folder.rglob(ext)):
                try:
                    content = file_path.read_text(encoding="utf-8", errors="replace")
                    title   = (
                        file_path.stem
                        .replace("_", " ")
                        .replace("-", " ")
                        .strip()
                        .title()
                    ) or "Sans titre"
                    db.create_note(title=title, content=content)
                    count += 1
                except Exception:
                    pass

        return count

    # ──────────────── Utilitaires ─────────────────────────────────────

    def delete_file(self, filepath: str):
        path = Path(filepath)
        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass
