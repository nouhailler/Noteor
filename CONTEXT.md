# Noteor — Contexte du projet

## Vue d'ensemble

Application PyQt6 de prise de notes avec support audio et images, stockage SQLite local.

- **Version** : 1.0.0
- **Stack** : Python 3.13, PyQt6, SQLite (`~/.local/share/Noteor/notes.db`)
- **Venv** : `./venv/` (Python 3.13)

---

## Architecture

```
Noteor/
├── main.py                   # Point d'entrée
├── config.py                 # Constantes (chemins, audio, UI)
├── database.py               # Toute la couche SQLite (Database class)
├── core/
│   ├── audio_recorder.py     # AudioRecorder + AudioPlayer (sounddevice/numpy)
│   └── file_manager.py       # Copie/miniatures images, import texte, screenshots
└── ui/
    ├── main_window.py        # Fenêtre principale (3 panneaux via QSplitter)
    ├── editor.py             # EditorPanel — panneau droit (éditeur complet)
    ├── widgets.py            # NoteItemDelegate, TagChip, AudioPlayerWidget, ImageThumbnailWidget
    └── styles.py             # QSS global
```

### Schéma SQLite

Tables : `notes`, `categories`, `tags`, `note_tags`, `attachments`
- `notes` ← `categories` (FK nullable, SET NULL on delete)
- `notes` ← `attachments` (FK CASCADE on delete)
- `attachments.type` : `'image'` | `'audio'`

---

## Fonctionnalités implémentées

- [x] Création / édition / suppression douce (corbeille) / restauration / suppression définitive de notes
- [x] Catégories hiérarchiques avec couleur (tree widget, menu contextuel)
- [x] Tags colorés (chips dans l'éditeur, filtrage dans la liste)
- [x] Recherche full-text (titre + contenu)
- [x] Filtre par type : toutes / avec audio / avec images
- [x] Éditeur Markdown avec barre de formatage et aperçu HTML (`QTextBrowser`)
- [x] Auto-sauvegarde 3 s après la dernière frappe
- [x] **Enregistrement audio** via `sounddevice` + `numpy` → fichier WAV dans `~/.local/share/Noteor/media/audio/`
- [x] **Import d'images** (copie + miniature Pillow/Qt) dans `media/images/` + `media/thumbnails/`
- [x] **Capture d'écran** (`screen.grabWindow(0)`) → image + miniature
- [x] Import de dossiers de fichiers `.txt`/`.md` comme notes
- [x] Délégué personnalisé (`NoteItemDelegate`) : affiche titre, date, icônes audio/image, bande couleur catégorie
- [x] Menu principal (Fichier, Affichage, Aide)

---

## Bugs connus (point d'arrêt de la dernière session)

### Bug 1 — `AttributeError` sur `sqlite3.Row` (audio recording)

**Contexte** : se produisait lors du flux de sauvegarde post-enregistrement.
**Cause probable** : accès à un objet `sqlite3.Row` après fermeture/GC de la connexion qui l'a créé,
ou accès en notation attribut (`row.field`) au lieu de subscript (`row["field"]`).
**État** : le code actuel utilise partout `row["field"]` — à surveiller si l'erreur réapparaît.
**À tester** : déclencher un enregistrement complet et vérifier la sortie console.

### Bug 2 — `sounddevice` bloque dans la VM (lecture ET enregistrement)

**Symptôme** : `sd.play()` et `sd.InputStream.start()` ne retournent jamais — le thread audio se bloque indéfiniment.
**Cause** : dans cette VM, le backend PortAudio n'arrive pas à ouvrir/utiliser les périphériques audio (`pipewire`/ALSA). La commande `sd.query_devices()` fonctionne (retourne 4 devices), mais toute ouverture réelle de stream bloque.
**Impact** : le bouton "🎤 Enregistrer" se bloque, de même que "▶ Lire".
**Piste de résolution** : remplacer `sounddevice` par `QMediaRecorder`/`QMediaPlayer` (Qt Multimedia) ou `pyaudio` + thread avec timeout, ou utiliser `subprocess` vers `arecord`/`aplay`.

### Bug 3 — `date_str` incorrect dans `NoteItemDelegate`

**Fichier** : `ui/widgets.py` ligne 62
**Code actuel** :
```python
date_str = index.data(Qt.ItemDataRole.UserRole) or ""   # ← récupère l'ID note, pas la date
```
**Correct** :
```python
date_str = index.data(Qt.ItemDataRole.UserRole + 1) or ""  # ROLE_DATE = UserRole + 1
```
Les rôles définis dans `main_window.py` :
- `UserRole + 0` = `ROLE_NOTE_ID` (ID entier)
- `UserRole + 1` = `ROLE_DATE` (chaîne `"YYYY-MM-DD HH:MM"`)
- `UserRole + 2` = `ROLE_CAT_COLOR`
- `UserRole + 3` = `ROLE_AUDIO`
- `UserRole + 4` = `ROLE_IMAGE`

---

## État de la base de données

- 1 note existante (id=1, titre="1 ere note")
- 2 pièces jointes audio (enregistrées lors de tests précédents) :
  - `audio_20260320_133847.wav` (5.6 s)
  - `audio_20260320_133944.wav` (4.6 s)

---

## Prochaines étapes suggérées

1. **Corriger le bug 3** (`date_str`) — trivial, 1 ligne
2. **Résoudre le bug audio VM** — évaluer `QMediaPlayer`/`QMediaRecorder` comme alternative à `sounddevice`
3. **Confirmer ou clore le bug 1** — lancer l'app et tester l'enregistrement complet
4. Fonctionnalités futures envisageables : export PDF/HTML, transcription Whisper, sync cloud

---

## Commandes utiles

```bash
# Lancer l'application
source venv/bin/activate && python main.py

# Installer les dépendances manquantes
pip install sounddevice numpy pillow markdown PyQt6

# Vérifier les devices audio
python -c "import sounddevice as sd; print(sd.query_devices())"
```
