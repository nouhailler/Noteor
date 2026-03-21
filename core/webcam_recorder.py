"""Enregistrement vidéo depuis la webcam via ffmpeg + v4l2."""

import glob
import shutil
import signal
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal

import config

FFMPEG_AVAILABLE = bool(shutil.which("ffmpeg"))


def _find_webcam_device() -> str | None:
    """Retourne le premier device webcam disponible (/dev/video*)."""
    devices = sorted(glob.glob("/dev/video*"))
    # Certains /dev/video* sont des devices de métadonnées (pas de capture).
    # On prend le premier disponible ; l'utilisateur peut en choisir un autre.
    return devices[0] if devices else None


class WebcamRecorder(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str, float)   # filepath, duration_seconds
    recording_error   = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._recording        = False
        self._process          = None
        self._start_time       = None
        self._current_filepath = None

    @property
    def is_recording(self) -> bool:
        return self._recording

    @staticmethod
    def is_available() -> bool:
        return FFMPEG_AVAILABLE and _find_webcam_device() is not None

    # ── API publique ──────────────────────────────────────────────────────────

    def start(self):
        if self._recording:
            return

        if not FFMPEG_AVAILABLE:
            self.recording_error.emit(
                "ffmpeg est requis pour enregistrer depuis la webcam.\n"
                "Installez-le : sudo apt install ffmpeg"
            )
            return

        device = _find_webcam_device()
        if not device:
            self.recording_error.emit(
                "Aucune webcam détectée.\n"
                "Vérifiez que votre webcam est connectée (/dev/video*)."
            )
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"webcam_{timestamp}.mp4"
        self._current_filepath = str(config.VIDEO_DIR / filename)

        # Ordre de tentatives : (mjpeg+audio), (raw+audio), (raw sans audio)
        attempts = [
            self._build_ffmpeg_cmd(device, self._current_filepath, use_mjpeg=True,  with_audio=True),
            self._build_ffmpeg_cmd(device, self._current_filepath, use_mjpeg=False, with_audio=True),
            self._build_ffmpeg_cmd(device, self._current_filepath, use_mjpeg=False, with_audio=False),
        ]
        last_stderr = ""
        for cmd in attempts:
            try:
                self._process = subprocess.Popen(
                    cmd,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                )
            except FileNotFoundError:
                self.recording_error.emit("ffmpeg introuvable.")
                return
            except Exception as exc:
                self.recording_error.emit(f"Impossible de lancer ffmpeg :\n{exc}")
                return

            time.sleep(0.8)
            if self._process.poll() is None:
                break   # ffmpeg tourne — on continue avec cette commande
            last_stderr = self._process.stderr.read().decode(errors="replace")
            self._process = None
        else:
            self.recording_error.emit(
                f"Impossible d'ouvrir la webcam {device}.\n"
                f"Détail : {last_stderr[-400:]}"
            )
            return

        self._start_time = time.monotonic()
        self._recording  = True
        self.recording_started.emit()
        threading.Thread(target=self._monitor, daemon=True).start()

    def stop(self):
        if not self._recording:
            return
        self._recording = False
        duration = time.monotonic() - self._start_time if self._start_time else 0.0

        if self._process is not None:
            try:
                # SIGINT → ffmpeg finalise le fichier proprement
                self._process.send_signal(signal.SIGINT)
                self._process.wait(timeout=6)
            except Exception:
                try:
                    self._process.terminate()
                    self._process.wait(timeout=2)
                except Exception:
                    try:
                        self._process.kill()
                    except Exception:
                        pass
            self._process = None

        self.recording_stopped.emit(self._current_filepath or "", duration)

    # ── Interne ───────────────────────────────────────────────────────────────

    @staticmethod
    def _build_ffmpeg_cmd(device: str, output: str, use_mjpeg: bool, with_audio: bool = True) -> list[str]:
        cmd = ["ffmpeg", "-y", "-f", "v4l2"]
        if use_mjpeg:
            cmd += ["-input_format", "mjpeg"]
        cmd += ["-i", device]
        if with_audio:
            cmd += ["-f", "alsa", "-i", "default"]
        cmd += [
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-crf", "23",
        ]
        if with_audio:
            cmd += ["-c:a", "aac", "-b:a", "128k"]
        cmd += ["-movflags", "+faststart", output]
        return cmd

    def _monitor(self):
        """Surveille la fin prématurée du processus ffmpeg."""
        proc = self._process
        if proc:
            proc.wait()
        # Si on est toujours censé enregistrer → crash inattendu
        if self._recording:
            self._recording = False
            self.recording_error.emit(
                "L'enregistrement webcam s'est arrêté de manière inattendue.\n"
                "Vérifiez que la webcam n'est pas utilisée par une autre application."
            )
