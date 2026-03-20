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
        """Capture l'écran via le portail XDG (Wayland) ou Qt (X11).
        Retourne (filepath, thumbnail_path) ou None."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"screenshot_{timestamp}.png"
        filepath  = config.IMAGE_DIR / filename

        # ── Portail XDG (fonctionne sur Wayland et X11) ──────────────────
        result = self._screenshot_via_portal(filepath)
        if result:
            return result

        # ── Fallback : Qt grabWindow (X11 uniquement) ─────────────────────
        try:
            screen = QApplication.primaryScreen()
            if screen:
                pixmap = screen.grabWindow(0)
                if not pixmap.isNull() and pixmap.width() > 0:
                    pixmap.save(str(filepath), "PNG")
                    thumb_path = self._create_thumbnail(filepath)
                    return str(filepath), thumb_path
        except Exception:
            pass

        return None

    def _screenshot_via_portal(self, dest: Path) -> tuple[str, str] | None:
        """Utilise le portail XDG via D-Bus pour capturer l'écran."""
        import subprocess, sys, json
        from urllib.parse import urlparse

        # Script exécuté dans un sous-processus pour éviter le conflit
        # entre la boucle GLib et la boucle Qt.
        script = r"""
import sys, json
import dbus, dbus.mainloop.glib
from gi.repository import GLib
import threading

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SessionBus()
loop = GLib.MainLoop()
result = {}

def on_response(response, results):
    result['response'] = int(response)
    if int(response) == 0:
        result['uri'] = str(results.get('uri', ''))
    loop.quit()

obj = bus.get_object('org.freedesktop.portal.Desktop', '/org/freedesktop/portal/desktop')
iface = dbus.Interface(obj, 'org.freedesktop.portal.Screenshot')
req_path = iface.Screenshot('', {
    'interactive': dbus.Boolean(False),
    'handle_token': dbus.String('noteor_cap'),
})
req_obj = bus.get_object('org.freedesktop.portal.Desktop', req_path)
req_obj.connect_to_signal('Response', on_response)

threading.Timer(10, loop.quit).start()
loop.run()
print(json.dumps(result))
"""
        try:
            r = subprocess.run(
                [sys.executable, "-c", script],
                capture_output=True, text=True, timeout=12,
            )
            data = json.loads(r.stdout.strip())
            if data.get("response") == 0 and data.get("uri"):
                source = Path(urlparse(data["uri"]).path)
                if source.exists():
                    shutil.copy2(source, dest)
                    thumb_path = self._create_thumbnail(dest)
                    return str(dest), thumb_path
        except Exception:
            pass

        return None

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

    # ──────────────── Vidéos ─────────────────────────────────────────

    def import_video(self, source_path: str) -> tuple[str, float]:
        """Copie la vidéo dans le dossier media/video.
        Retourne (filepath, duration_seconds)."""
        source    = Path(source_path)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"vid_{timestamp}{source.suffix.lower()}"
        dest      = config.VIDEO_DIR / filename

        shutil.copy2(source, dest)
        duration = self._get_video_duration(dest)
        return str(dest), duration

    def _get_video_duration(self, video_path: Path) -> float:
        """Retourne la durée en secondes via ffprobe, ou 0.0 si indisponible."""
        if not shutil.which("ffprobe"):
            return 0.0
        try:
            import subprocess, json
            result = subprocess.run(
                [
                    "ffprobe", "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    str(video_path),
                ],
                capture_output=True, text=True, timeout=10
            )
            data = json.loads(result.stdout)
            return float(data.get("format", {}).get("duration", 0))
        except Exception:
            return 0.0

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
