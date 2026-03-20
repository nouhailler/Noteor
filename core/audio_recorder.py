import wave
import threading
import tempfile
from pathlib import Path
from datetime import datetime

from PyQt6.QtCore import QObject, pyqtSignal

import config

try:
    import numpy as np
    import sounddevice as sd
    AUDIO_AVAILABLE = True
except (ImportError, OSError):
    AUDIO_AVAILABLE = False


class AudioRecorder(QObject):
    recording_started = pyqtSignal()
    recording_stopped = pyqtSignal(str, float)   # filepath, duration_seconds
    recording_error   = pyqtSignal(str)
    level_updated     = pyqtSignal(float)         # 0.0 – 1.0

    def __init__(self):
        super().__init__()
        self._recording = False
        self._frames: list = []
        self._stream = None

    @property
    def is_recording(self):
        return self._recording

    def start(self):
        if not AUDIO_AVAILABLE:
            self.recording_error.emit(
                "Les bibliothèques audio ne sont pas disponibles.\n"
                "Installez-les avec :\n  pip install sounddevice numpy"
            )
            return
        if self._recording:
            return

        self._frames = []
        self._recording = True

        def _callback(indata, frames, time, status):
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

    def stop(self):
        if not self._recording:
            return
        self._recording = False
        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        threading.Thread(target=self._save, daemon=True).start()

    def _save(self):
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
                wf.setsampwidth(2)            # int16 → 2 bytes
                wf.setframerate(config.SAMPLE_RATE)
                wf.writeframes(audio_data.tobytes())

            self.recording_stopped.emit(str(filepath), duration)
        except Exception as exc:
            self.recording_error.emit(f"Erreur lors de la sauvegarde audio :\n{exc}")


class AudioPlayer(QObject):
    playback_started = pyqtSignal()
    playback_stopped = pyqtSignal()
    playback_error   = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._playing  = False
        self._thread   = None

    @property
    def is_playing(self):
        return self._playing

    def play(self, filepath: str):
        if self._playing:
            self._playing = False   # signal au thread de s'arrêter
        self._thread = threading.Thread(
            target=self._play_audio, args=(filepath,), daemon=True
        )
        self._thread.start()

    def stop(self):
        # On positionne juste le flag ; c'est le thread audio qui appellera
        # sd.stop() depuis son propre contexte, évitant tout deadlock.
        self._playing = False

    def _play_audio(self, filepath: str):
        if not AUDIO_AVAILABLE:
            self.playback_error.emit("sounddevice n'est pas installé.")
            return
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

            # Boucle de polling : évite sd.wait() qui bloque et cause un
            # deadlock quand stop() est appelé depuis le thread principal.
            import time
            try:
                stream = sd.get_stream()
                while stream.active and self._playing:
                    time.sleep(0.05)
            except Exception:
                pass

            # Arrêt propre si l'utilisateur a cliqué sur Stop
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
