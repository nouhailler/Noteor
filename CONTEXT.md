# Noteor — Contexte du projet

## Vue d'ensemble

Application PyQt6 de prise de notes avec support audio, images et vidéos, stockage SQLite local.

- **Version** : 1.0.0
- **Stack** : Python 3.13, PyQt6, SQLite (`~/.local/share/Noteor/notes.db`)
- **Venv** : `./venv/` (Python 3.13) — absent de la machine actuelle, dépendances dans le Python système
- **Dépôt GitHub** : https://github.com/nouhailler/Noteor (commit `8506f89`)

---

## Architecture

```
Noteor/
├── main.py                   # Point d'entrée
├── config.py                 # Constantes (chemins, audio, UI)
├── database.py               # Toute la couche SQLite (Database class)
├── core/
│   ├── audio_recorder.py     # AudioRecorder + AudioPlayer (arecord/aplay + sounddevice fallback)
│   ├── webcam_recorder.py    # WebcamRecorder (ffmpeg + v4l2, SIGINT pour arrêt propre)
│   └── file_manager.py       # Copie/miniatures images, import texte/vidéo, screenshots
└── ui/
    ├── main_window.py        # Fenêtre principale (3 panneaux via QSplitter)
    ├── editor.py             # EditorPanel — panneau droit (éditeur complet)
    ├── widgets.py            # NoteItemDelegate, TagChip, AudioPlayerWidget, ImageThumbnailWidget, VideoPlayerWidget
    └── styles.py             # QSS global
```

### Schéma SQLite

Tables : `notes`, `categories`, `tags`, `note_tags`, `attachments`
- `notes` ← `categories` (FK nullable, SET NULL on delete)
- `notes` ← `attachments` (FK CASCADE on delete)
- `attachments.type` : `'image'` | `'audio'` | `'video'`
- Migration automatique au démarrage : si la table `attachments` existante ne contient pas `'video'` dans son CHECK, elle est recréée transparentement.

### Rôles QListWidgetItem (`main_window.py`)

- `UserRole + 0` = `ROLE_NOTE_ID`
- `UserRole + 1` = `ROLE_DATE` (chaîne `"YYYY-MM-DD HH:MM"`)
- `UserRole + 2` = `ROLE_CAT_COLOR`
- `UserRole + 3` = `ROLE_AUDIO`
- `UserRole + 4` = `ROLE_IMAGE`
- `UserRole + 5` = `ROLE_VIDEO`

---

## Fonctionnalités implémentées

- [x] Création / édition / suppression douce (corbeille) / restauration / suppression définitive de notes
- [x] Catégories hiérarchiques avec couleur (tree widget, menu contextuel)
- [x] Tags colorés (chips dans l'éditeur, filtrage dans la liste)
- [x] Recherche full-text (titre + contenu)
- [x] Filtre par type : toutes / avec audio / avec images / avec vidéos 🎬
- [x] **Filtre par date** : aujourd'hui / 7 jours / 30 jours / cette année / période libre (QDateEdit)
- [x] Éditeur Markdown avec barre de formatage et aperçu HTML (`QTextBrowser`)
- [x] Auto-sauvegarde 3 s après la dernière frappe
- [x] **Enregistrement audio** via `arecord` (ALSA) → fichier WAV dans `media/audio/`
- [x] **Lecture audio** via `aplay` (ALSA)
- [x] **Import d'images** (copie + miniature Pillow/Qt) dans `media/images/` + `media/thumbnails/`
- [x] **Capture d'écran** via portail XDG (D-Bus, Wayland) → copie dans `media/images/` + miniature
- [x] **Import de vidéos** (copie dans `media/video/`, durée via `ffprobe` si dispo)
- [x] **Enregistrement webcam** via `ffmpeg` + v4l2 → fichier MP4 dans `media/video/` (bouton 🎥 Webcam, indicateur temps écoulé)
- [x] Import de dossiers de fichiers `.txt`/`.md` comme notes
- [x] Délégué personnalisé (`NoteItemDelegate`) : titre, date, icônes 🎤/🖼/🎬, bande couleur catégorie
- [x] Menu principal (Fichier, Affichage, Aide)
- [x] README.md sur GitHub

---

## Bugs corrigés lors de cette session

### Bug 1 — `sounddevice` bloque dans la VM ✅ résolu
**Solution** : `audio_recorder.py` réécrit avec deux backends :
1. **Primaire** : `arecord` / `aplay` via `subprocess.Popen` (non-bloquant, ALSA direct)
2. **Fallback** : `sounddevice` si `arecord` absent (autres plateformes)

### Bug 2 — `date_str` incorrect dans `NoteItemDelegate` ✅ résolu
`UserRole` → `UserRole + 1` dans `ui/widgets.py`.

### Bug 3 — Capture d'écran noire sur Wayland ✅ résolu
- `grabWindow(0)` retourne 0×0 (Wayland bloque la capture Qt)
- **Solution** : portail XDG via D-Bus (`org.freedesktop.portal.Desktop`) exécuté dans un sous-processus Python pour éviter le conflit GLib/Qt
- `main.py` force `QT_QPA_PLATFORM=xcb` si `WAYLAND_DISPLAY` est défini
- Compte à rebours 3 s sur le bouton "📷 Capture" pour laisser le temps de préparer l'écran

### Bug 4 — Bouton 🗑 des images invisible ✅ résolu
Zone pièces jointes (`attach_scroll`) passée de `100 px` à `140 px` — `ImageThumbnailWidget` fait 120 px, le bouton supprimer était rogné.

### Bug 5 — Sélection disparaît lors d'un changement de filtre ✅ résolu
`setCurrentItem` appelé **hors de la boucle** d'ajout d'items (+ `scrollToItem`). Appel pendant la boucle empêchait Qt de calculer correctement l'état visuel de la sélection.

---

## Environnement VM — points de vigilance

| Sujet | État |
|---|---|
| Audio (`sounddevice`) | Non fonctionnel — PortAudio/pipewire bloque. `arecord`/`aplay` utilisés à la place. |
| Capture d'écran Qt | `grabWindow(0)` retourne une image noire. Portail XDG utilisé à la place. |
| `venv` | Absent — dépendances installées dans le Python système (`python3`) |
| Commande Python | `python3` (pas `python`) |
| `ffprobe` | Non installé — durée des vidéos affichée `--:--` si absent |
| `ffmpeg` | Non installé — **requis pour l'enregistrement webcam**. `sudo apt install ffmpeg` |
| Webcam | `/dev/video0` et `/dev/video1` détectés dans la VM |

---

## État de la base de données (au 2026-03-20)

- 1 note existante (id=1, titre="1 ere note")
- 2 pièces jointes audio : `audio_20260320_133847.wav` (5.6 s), `audio_20260320_133944.wav` (4.6 s)
- Table `attachments` migrée pour accepter le type `'video'`

---

## Session du 2026-03-21

### Enregistrement webcam ✅ implémenté

- Nouveau fichier `core/webcam_recorder.py` : classe `WebcamRecorder` (QObject + signaux PyQt6)
  - Backend : `ffmpeg -f v4l2` — SIGINT pour arrêt propre (finalise le MP4)
  - Détection automatique du device (`/dev/video*`)
  - Double tentative : d'abord `-input_format mjpeg`, fallback sans format forcé
  - Délai de 800 ms pour détecter les crashs au démarrage avant d'émettre `recording_started`
- `ui/editor.py` :
  - Bouton "🎥 Webcam" (checkable, style `record_btn`)
  - Indicateur "🔴 Enregistrement webcam…" + compteur temps écoulé MM:SS
  - 4 méthodes : `_toggle_webcam_recording`, `_on_webcam_started`, `_on_webcam_stopped`, `_on_webcam_error`
  - La vidéo enregistrée est sauvée comme pièce jointe `type='video'` (même chemin que les vidéos importées)
- `ui/main_window.py` : instanciation de `WebcamRecorder`, passé à `EditorPanel`
- **Dépendance requise** : `sudo apt install ffmpeg` (non présent dans la VM au moment du dev)

---

## Prochaines étapes suggérées

1. Export PDF / HTML des notes
2. Transcription audio via Whisper (locale)
3. Raccourcis clavier pour les pièces jointes
4. Tri de la liste des notes (par titre, date de création, date de modification)
5. Thème sombre

---

## Commandes utiles

```bash
# Lancer l'application
python3 main.py

# Depuis un venv si disponible
source venv/bin/activate && python3 main.py

# Installer les dépendances
pip install PyQt6 numpy pillow markdown sounddevice

# Dépendances système pour audio et capture (Debian/Ubuntu)
sudo apt install alsa-utils python3-dbus python3-gi

# Vérifier les devices audio ALSA
arecord -l
```
