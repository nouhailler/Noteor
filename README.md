# Noteor

Application de prise de notes desktop avec support audio, images et vidéos. Stockage 100 % local via SQLite.

## Captures d'écran

> Interface en 3 panneaux : catégories / liste des notes / éditeur

## Fonctionnalités

- **Notes Markdown** — éditeur avec barre de formatage et aperçu HTML en temps réel
- **Auto-sauvegarde** — 3 secondes après la dernière frappe
- **Catégories hiérarchiques** — avec couleur personnalisable, menu contextuel
- **Tags colorés** — chips dans l'éditeur, filtrage dans la liste
- **Recherche full-text** — titre et contenu
- **Pièces jointes**
  - 🎤 Enregistrement audio (via `arecord` / `sounddevice`)
  - 🖼 Import d'images + génération de miniatures (Pillow / Qt)
  - 📷 Capture d'écran (portail XDG sur Wayland, Qt sur X11)
  - 📹 Import de vidéos
- **Filtres**
  - Par type : audio, images, vidéos
  - Par date : aujourd'hui, 7 jours, 30 jours, cette année, période libre
  - Par catégorie et par tag
- **Corbeille** — suppression douce, restauration, suppression définitive
- **Import de dossiers** — fichiers `.txt` / `.md` importés comme notes

## Stack technique

| Composant | Technologie |
|---|---|
| Interface | PyQt6 |
| Base de données | SQLite (`~/.local/share/Noteor/notes.db`) |
| Audio | `arecord` / `aplay` (ALSA) ou `sounddevice` |
| Images | Pillow + Qt |
| Capture écran | Portail XDG (D-Bus) |
| Vidéos | Copie locale, lecture via `mpv` / `vlc` / `xdg-open` |
| Markdown | bibliothèque `markdown` |

## Installation

### Prérequis système (Linux)

```bash
# Debian / Ubuntu
sudo apt install python3 python3-pip python3-venv \
                 alsa-utils python3-dbus python3-gi
```

### Installation

```bash
git clone https://github.com/nouhailler/Noteor.git
cd Noteor
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Lancement

```bash
source venv/bin/activate
python3 main.py
```

Ou directement (si les dépendances sont dans le Python système) :

```bash
python3 main.py
```

## Structure du projet

```
Noteor/
├── main.py                # Point d'entrée
├── config.py              # Constantes (chemins, paramètres audio/UI)
├── database.py            # Couche SQLite (class Database)
├── requirements.txt
├── core/
│   ├── audio_recorder.py  # AudioRecorder + AudioPlayer (arecord/sounddevice)
│   └── file_manager.py    # Images, miniatures, captures d'écran, vidéos
└── ui/
    ├── main_window.py     # Fenêtre principale — 3 panneaux (QSplitter)
    ├── editor.py          # Panneau éditeur (markdown, pièces jointes)
    ├── widgets.py         # Délégué liste, TagChip, AudioPlayer, VideoPlayer, ImageThumbnail
    └── styles.py          # Feuille de style QSS globale
```

## Données

Toutes les données sont stockées localement dans `~/.local/share/Noteor/` :

```
~/.local/share/Noteor/
├── notes.db              # Base de données SQLite
└── media/
    ├── audio/            # Enregistrements WAV
    ├── images/           # Images importées et captures d'écran
    ├── thumbnails/       # Miniatures des images
    └── video/            # Vidéos importées
```

## Notes Wayland

Sur les sessions Wayland, la capture d'écran utilise le **portail XDG** via D-Bus (`org.freedesktop.portal.Desktop`), ce qui nécessite `python3-dbus` et `python3-gi`. L'application bascule automatiquement sur le backend X11 (`xcb`) pour garantir la compatibilité.

## Licence

MIT
