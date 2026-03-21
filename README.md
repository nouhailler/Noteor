<div align="center">

# 📓 Noteor

**Gestionnaire de notes desktop — 100 % local, sans cloud**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-6.x-41CD52?logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![SQLite](https://img.shields.io/badge/SQLite-local-003B57?logo=sqlite&logoColor=white)](https://sqlite.org)
[![Platform](https://img.shields.io/badge/Platform-Linux-FCC624?logo=linux&logoColor=black)](https://kernel.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

*Prenez des notes en Markdown, enregistrez votre voix, capturez l'écran, filmez depuis la webcam et organisez tout dans des dossiers — le tout stocké localement.*

</div>

---

## ✨ Fonctionnalités

### 📝 Notes & Édition
- Éditeur **Markdown** avec barre de formatage rapide (gras, italique, code, listes, titres)
- **Aperçu HTML** en temps réel (rendu Markdown)
- **Auto-sauvegarde** 3 secondes après la dernière frappe
- **Tags colorés** — chips dans l'éditeur, filtrage instantané

### 📂 Organisation
- **Dossiers hiérarchiques** — arborescence de dossiers indépendante, comme un explorateur de fichiers
- **Glisser-déposer** — déplacez une note dans un dossier en la faisant glisser
- **Catégories colorées** — arborescence avec bande couleur visible dans la liste
- **Corbeille** — suppression douce, restauration, suppression définitive

### 🎙️ Audio
- **Enregistrement micro** depuis l'application (bouton 🎤)
- Lecture intégrée avec contrôles ▶ / ⏹
- Backend : `arecord` / `aplay` (ALSA) avec repli sur `sounddevice`

### 🖼️ Images
- **Import d'images** (PNG, JPG, GIF, WEBP, TIFF…) avec miniatures automatiques
- **Capture d'écran** (portail XDG — compatible Wayland & X11) avec compte à rebours 3 s

### 🎬 Vidéo
- **Import de vidéos** (MP4, MKV, AVI, MOV, WEBM…)
- **Enregistrement webcam** en direct → fichier MP4 (via `ffmpeg` + V4L2)
- Compteur de durée pendant l'enregistrement

### 🔍 Recherche & Filtres
- **Recherche full-text** — titre + contenu en temps réel
- **Filtres par type** : audio 🎤 / images 🖼 / vidéos 🎬
- **Filtres par date** : aujourd'hui, 7 j, 30 j, cette année, période libre
- **Filtre par dossier, catégorie ou tag**

### 📄 Export PDF
- Export de n'importe quelle note en **PDF** (Ctrl+E ou clic droit)
- Contenu : titre, métadonnées, texte Markdown rendu, **captures d'écran intégrées**
- Format A4, mise en page soignée

### ❓ Aide intégrée
- Fenêtre d'aide complète (`F1` ou menu Aide)
- Navigation par topics : notes, dossiers, audio, vidéo, raccourcis…

---

## 📸 Interface

> L'interface est divisée en **3 panneaux** redimensionnables :

```
┌─────────────────┬─────────────────┬────────────────────────────────┐
│  📂 Dossiers    │  📋 Liste notes  │  📝 Éditeur                    │
│  🏷 Catégories  │                  │                                │
│  Tags           │  • Ma note 1 🎤  │  Titre de la note              │
│  Filtres        │  • Ma note 2 🖼  │  ─────────────────────────     │
│  🗑 Corbeille   │  • Ma note 3 🎬  │  Contenu en **Markdown**...    │
│                 │                  │                                │
│                 │                  │  [Pièces jointes]              │
└─────────────────┴─────────────────┴────────────────────────────────┘
```

---

## 🚀 Installation

### Prérequis système (Linux)

```bash
# Debian / Ubuntu / Linux Mint
sudo apt install python3 python3-pip python3-venv \
                 alsa-utils python3-dbus python3-gi

# Pour l'enregistrement webcam
sudo apt install ffmpeg

# Optionnel — pour la durée des vidéos importées
sudo apt install ffprobe
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

> **Sans venv** (si les dépendances sont dans le Python système) :
> ```bash
> python3 main.py
> ```

---

## ⌨️ Raccourcis clavier

| Raccourci | Action |
|-----------|--------|
| `Ctrl+N` | Nouvelle note |
| `Ctrl+S` | Sauvegarder |
| `Ctrl+E` | Exporter en PDF |
| `F1` | Aide complète |
| `F5` | Actualiser |
| `Ctrl+Q` | Quitter |

---

## 📦 Dépendances Python

```
PyQt6
markdown
Pillow
sounddevice   # optionnel — fallback audio si arecord absent
numpy         # requis par sounddevice
```

---

## 🗂️ Structure du projet

```
Noteor/
├── main.py                  # Point d'entrée
├── config.py                # Constantes (chemins, paramètres)
├── database.py              # Couche SQLite (class Database)
├── requirements.txt
├── core/
│   ├── audio_recorder.py    # AudioRecorder + AudioPlayer
│   ├── webcam_recorder.py   # WebcamRecorder (ffmpeg + V4L2)
│   └── file_manager.py      # Images, miniatures, captures, vidéos
└── ui/
    ├── main_window.py        # Fenêtre principale (3 panneaux)
    ├── editor.py             # Panneau éditeur
    ├── widgets.py            # Composants UI réutilisables
    ├── help_window.py        # Fenêtre d'aide complète
    └── styles.py             # Feuille de style QSS
```

---

## 💾 Données locales

Toutes les données sont stockées dans **`~/.local/share/Noteor/`** — rien n'est envoyé sur internet.

```
~/.local/share/Noteor/
├── notes.db           # Base SQLite (notes, dossiers, catégories, tags, pièces jointes)
└── media/
    ├── audio/         # Enregistrements WAV
    ├── images/        # Images importées et captures d'écran
    ├── thumbnails/    # Miniatures (220×160 px)
    └── video/         # Vidéos importées et enregistrements webcam
```

---

## 🖥️ Notes de compatibilité

### Wayland
La capture d'écran utilise le **portail XDG** via D-Bus (`org.freedesktop.portal.Desktop`).
Noteor bascule automatiquement sur le backend XCB si Wayland est détecté.

```bash
# Dépendances portail XDG
sudo apt install python3-dbus python3-gi
```

### Webcam
L'enregistrement webcam nécessite `ffmpeg` et un device `/dev/video*`.
Noteor essaie automatiquement plusieurs modes (MJPEG → RAW, avec/sans audio)
pour s'adapter à votre matériel.

---

## 🛠️ Stack technique

| Composant | Technologie |
|-----------|-------------|
| Interface graphique | PyQt6 |
| Base de données | SQLite (WAL mode) |
| Rendu Markdown | `markdown` |
| Images / Miniatures | Pillow + Qt |
| Audio | `arecord` / `aplay` (ALSA) + `sounddevice` |
| Capture d'écran | Portail XDG (D-Bus / gi) |
| Vidéo / Webcam | `ffmpeg` + V4L2 |
| Export PDF | Qt PrintSupport (`QPrinter` + `QTextDocument`) |

---

## 📃 Licence

[MIT](LICENSE) — Noteor est un logiciel libre.
