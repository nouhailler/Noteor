import wave
import threading
import subprocess
import shutil
import time
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

import config

# ─── sounddevice (optionnel) ──────────────────────────────────────────────────
try:
    import numpy as np
    import sounddevice as sd
    SOUNDDEVICE_AVAILABLE = True
except (ImportError, OSError):
    SOUNDDEVICE_AVAILABLE = False

# ─── arecord / aplay (Linux ALSA) ────────────────────────────────────────────
ARECORD_AVAILABLE = bool(shutil.which("arecord"))
APLAY_AVAILABLE   = bool(shutil.which("aplay"))


class AudioRecorder(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str, float)   # filepath, duration_seconds
    recording_error   = pyqtSignal(str)
    level_updated     = pyqtSignal(float)         # 0.0 – 1.0

    def __init__(self):
        super().__init__()
        self._recording  = False
        self._process    = None   # subprocess.Popen (mode arecord)
        self._start_time = None
        # sounddevice
        self._frames     = []
        self._stream     = None

    @property
    def is_recording(self):
        return self._recording

    # ── API publique ──────────────────────────────────────────────────────────

    def start(self):
        if self._recording:
            return
        if ARECORD_AVAILABLE:
            self._start_arecord()
        elif SOUNDDEVICE_AVAILABLE:
            self._start_sounddevice()
        else:
            self.recording_error.emit(
                "Aucun backend audio disponible.\n"
                "Installez alsa-utils (arecord) ou sounddevice+numpy."
            )

    def stop(self):
        if not self._recording:
            return
        self._recording = False
        if self._process is not None:
            self._stop_arecord()
        else:
            self._stop_sounddevice()

    # ── Backend arecord ───────────────────────────────────────────────────────

    def _start_arecord(self):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename  = f"audio_{timestamp}.wav"
        self._current_filepath = str(config.AUDIO_DIR / filename)

        cmd = [
            "arecord",
            "-f", "S16_LE",
            "-r", str(config.SAMPLE_RATE),
            "-c", str(config.CHANNELS),
            self._current_filepath,
        ]
        try:
            self._process    = subprocess.Popen(cmd,
                                                stdout=subprocess.DEVNULL,
                                                stderr=subprocess.DEVNULL)
            self._start_time = time.monotonic()
            self._recording  = True
            self.recording_started.emit()

            # Thread de surveillance du niveau (synthétique) + fin de process
            threading.Thread(target=self._monitor_arecord, daemon=True).start()
        except Exception as exc:
            self._process   = None
            self._recording = False
            self.recording_error.emit(f"Impossible de démarrer arecord :\n{exc}")

    def _monitor_arecord(self):
        """Pulse de niveau synthétique toutes les 100 ms pendant l'enregistrement."""
        import math, random
        while self._recording:
            # Niveau fictif ondulant (pas de lecture micro réelle depuis le thread)
            t     = time.monotonic() - self._start_time
            level = 0.3 + 0.2 * math.sin(t * 3) + random.uniform(0, 0.05)
            self.level_updated.emit(min(1.0, max(0.0, level)))
            time.sleep(0.1)

    def _stop_arecord(self):
        duration = time.monotonic() - self._start_time
        try:
            self._process.terminate()
            self._process.wait(timeout=2)
        except Exception:
            try:
                self._process.kill()
            except Exception:
                pass
        self._process = None
        self.recording_stopped.emit(self._current_filepath, duration)

    # ── Backend sounddevice ───────────────────────────────────────────────────

    def _start_sounddevice(self):
        import numpy as np
        self._frames     = []
        self._recording  = True
        self._start_time = time.monotonic()

        def _callback(indata, frames, time_info, status):
            if self._recording:
                self._frames.append(indata.copy())
                level = float(np.abs(indata).mean()) / 32768.0
                self.level_updated.emit(min(1.0, level * 15))

        try:
            self._stream = sd.InputStream(
                samplerate=config.SAMPLE_RATE,
                channels=config.CHANNELS,
                dtype=config.AUDIO_DTYPE,
                callback=_callback,
            )
            self._stream.start()
            self.recording_started.emit()
        except Exception as exc:
            self._recording = False
            self.recording_error.emit(f"Impossible de démarrer l'enregistrement :\n{exc}")

    def _stop_sounddevice(self):
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        threading.Thread(target=self._save_sounddevice, daemon=True).start()

    def _save_sounddevice(self):
        import numpy as np
        if not self._frames:
            return
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename  = f"audio_{timestamp}.wav"
            filepath  = config.AUDIO_DIR / filename

            audio_data = np.concatenate(self._frames, axis=0)
            duration   = len(audio_data) / config.SAMPLE_RATE

            with wave.open(str(filepath), "wb") as wf:
                wf.setnchannels(config.CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(config.SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())

            self.recording_stopped.emit(str(filepath), duration)
        except Exception as exc:
            self.recording_error.emit(f"Erreur lors de la sauvegarde audio :\n{exc}")


# ─────────────────────────────────────────────────────────────────────────────

class AudioPlayer(QObject):
    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()
    playback_error   = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._playing = False
        self._process = None   # subprocess.Popen (mode aplay)
        self._thread  = None

    @property
    def is_playing(self):
        return self._playing

    def play(self, filepath: str):
        if self._playing:
            self.stop()
        if APLAY_AVAILABLE:
            self._play_aplay(filepath)
        elif SOUNDDEVICE_AVAILABLE:
            self._thread = threading.Thread(
                target=self._play_sounddevice, args=(filepath,), daemon=True
            )
            self._thread.start()
        else:
            self.playback_error.emit("Aucun backend audio disponible.")

    def stop(self):
        self._playing = False
        if self._process is not None:
            try:
                self._process.terminate()
            except Exception:
                pass

    # ── Backend aplay ─────────────────────────────────────────────────────────

    def _play_aplay(self, filepath: str):
        try:
            self._process = subprocess.Popen(
                ["aplay", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            self._playing = True
            self.playback_started.emit()
            threading.Thread(target=self._wait_aplay, daemon=True).start()
        except Exception as exc:
            self.playback_error.emit(f"Erreur aplay :\n{exc}")

    def _wait_aplay(self):
        try:
            self._process.wait()
        except Exception:
            pass
        self._process = None
        self._playing = False
        self.playback_stopped.emit()

    # ── Backend sounddevice ───────────────────────────────────────────────────

    def _play_sounddevice(self, filepath: str):
        import numpy as np
        try:
            with wave.open(str(filepath), "rb") as wf:
                n_frames   = wf.getnframes()
                samplerate = wf.getframerate()
                n_channels = wf.getnchannels()
                sampwidth  = wf.getsampwidth()
                raw        = wf.readframes(n_frames)

            dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
            dtype = dtype_map.get(sampwidth, np.int16)
            data  = np.frombuffer(raw, dtype=dtype)
            if n_channels > 1:
                data = data.reshape(-1, n_channels)

            self._playing = True
            self.playback_started.emit()
            sd.play(data, samplerate)

            try:
                stream = sd.get_stream()
                while stream.active and self._playing:
                    time.sleep(0.05)
            except Exception:
                pass

            if not self._playing:
                try:
                    sd.stop()
                except Exception:
                    pass

        except Exception as exc:
            self.playback_error.emit(f"Erreur de lecture audio :\n{exc}")
        finally:
            self._playing = False
            self.playback_stopped.emit()
