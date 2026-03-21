"""Fenêtre d'aide complète de Noteor."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextBrowser, QPushButton, QLabel,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

import config

# ─── CSS commun à tous les topics ────────────────────────────────────────────

_CSS = """
<style>
  body       { font-family: 'Segoe UI', Arial, sans-serif; font-size: 10pt;
               line-height: 1.65; color: #1f2937; margin: 20px 24px; }
  h1         { font-size: 16pt; font-weight: bold; color: #4F46E5;
               border-bottom: 2px solid #e5e7eb; padding-bottom: 8px;
               margin-bottom: 16px; }
  h2         { font-size: 11pt; font-weight: bold; color: #374151;
               margin-top: 22px; margin-bottom: 6px; border-left: 3px solid #4F46E5;
               padding-left: 8px; }
  p          { margin: 6px 0 10px; }
  ul, ol     { margin: 4px 0 10px; padding-left: 22px; }
  li         { margin-bottom: 4px; }
  kbd        { display: inline-block; background: #f3f4f6; border: 1px solid #d1d5db;
               border-radius: 4px; padding: 1px 6px; font-family: monospace;
               font-size: 9pt; color: #374151; }
  .tip       { background: #eff6ff; border-left: 4px solid #3b82f6;
               border-radius: 4px; padding: 8px 12px; margin: 12px 0; }
  .warn      { background: #fefce8; border-left: 4px solid #eab308;
               border-radius: 4px; padding: 8px 12px; margin: 12px 0; }
  .shortcut  { display: inline-block; min-width: 130px; font-weight: bold;
               color: #4F46E5; }
  table      { border-collapse: collapse; width: 100%; margin: 10px 0; }
  th         { background: #f9fafb; text-align: left; padding: 6px 10px;
               border: 1px solid #e5e7eb; color: #374151; font-size: 9.5pt; }
  td         { padding: 6px 10px; border: 1px solid #e5e7eb; font-size: 9.5pt; }
  tr:nth-child(even) td { background: #f9fafb; }
  .icon      { font-size: 13pt; margin-right: 4px; }
  .badge     { display:inline-block; background:#4F46E5; color:white;
               border-radius:4px; padding:1px 7px; font-size:8.5pt; }
</style>
"""


def _page(title: str, body: str) -> str:
    return f"<html><head><meta charset='utf-8'>{_CSS}</head><body>{body}</body></html>"


# ─── Contenu de chaque topic ──────────────────────────────────────────────────

QUICK_START = _page("Démarrage rapide", """
<h1>🚀 Démarrage rapide</h1>

<p>Bienvenue dans <b>Noteor</b> — votre gestionnaire de notes local avec support
audio, image et vidéo. Toutes vos données sont stockées <b>localement</b> dans
<code>~/.local/share/Noteor/</code>, rien n'est envoyé sur internet.</p>

<h2>L'interface en 3 panneaux</h2>
<table>
  <tr><th>Panneau</th><th>Rôle</th></tr>
  <tr><td><b>Gauche</b></td><td>Navigation : dossiers, catégories, tags, filtres</td></tr>
  <tr><td><b>Centre</b></td><td>Liste des notes (titre, date, icônes de pièces jointes)</td></tr>
  <tr><td><b>Droite</b></td><td>Éditeur complet de la note sélectionnée</td></tr>
</table>

<h2>En 4 étapes pour commencer</h2>
<ol>
  <li>Cliquez sur <b>+ Nouvelle note</b> ou appuyez sur <kbd>Ctrl+N</kbd></li>
  <li>Donnez un titre à votre note</li>
  <li>Rédigez le contenu en Markdown dans la zone de texte</li>
  <li>La note est <b>sauvegardée automatiquement</b> 3 secondes après la dernière frappe</li>
</ol>

<div class="tip">
  💡 <b>Astuce :</b> Activez le bouton <b>Aperçu</b> (en haut à droite de l'éditeur)
  pour voir le rendu Markdown de votre note en temps réel.
</div>

<h2>Markdown supporté</h2>
<table>
  <tr><th>Syntaxe</th><th>Résultat</th></tr>
  <tr><td><code>**texte**</code></td><td><b>Gras</b></td></tr>
  <tr><td><code>*texte*</code></td><td><i>Italique</i></td></tr>
  <tr><td><code>`code`</code></td><td>Code en ligne</td></tr>
  <tr><td><code># Titre</code></td><td>Titre de niveau 1</td></tr>
  <tr><td><code>## Sous-titre</code></td><td>Titre de niveau 2</td></tr>
  <tr><td><code>- élément</code></td><td>Liste à puces</td></tr>
  <tr><td><code>1. élément</code></td><td>Liste numérotée</td></tr>
  <tr><td><code>| col | col |</code></td><td>Tableau</td></tr>
</table>
""")

NOTES = _page("Gérer les notes", """
<h1>📝 Gérer les notes</h1>

<h2>Créer une note</h2>
<ul>
  <li>Bouton <b>+ Nouvelle note</b> dans le panneau gauche</li>
  <li>Raccourci <kbd>Ctrl+N</kbd></li>
  <li>Si un dossier ou une catégorie est sélectionné(e), la note y est automatiquement placée</li>
</ul>

<h2>Modifier une note</h2>
<p>Cliquez sur une note dans la liste centrale pour l'ouvrir dans l'éditeur.
Vous pouvez modifier le titre et le contenu librement.</p>
<ul>
  <li><b>Sauvegarde automatique</b> : 3 secondes après la dernière frappe</li>
  <li><b>Sauvegarde manuelle</b> : bouton <b>💾 Sauvegarder</b> ou <kbd>Ctrl+S</kbd></li>
</ul>

<h2>Barre de formatage Markdown</h2>
<p>Des boutons de mise en forme rapide sont disponibles au-dessus de l'éditeur :</p>
<table>
  <tr><th>Bouton</th><th>Action</th></tr>
  <tr><td><b>**B**</b></td><td>Met le texte sélectionné en <b>gras</b></td></tr>
  <tr><td><i>*I*</i></td><td>Met le texte sélectionné en <i>italique</i></td></tr>
  <tr><td><code>`Code`</code></td><td>Formate en code en ligne</td></tr>
  <tr><td>— Liste</td><td>Insère un élément de liste à puces</td></tr>
  <tr><td>1. Liste</td><td>Insère un élément de liste numérotée</td></tr>
  <tr><td># Titre</td><td>Insère un titre de niveau 2</td></tr>
</table>

<h2>Tags</h2>
<p>Ajoutez des tags en tapant un nom dans le champ <b>+ Ajouter un tag…</b> et
en appuyant sur <kbd>Entrée</kbd>. Les tags permettent de retrouver rapidement
vos notes grâce au filtre par tag dans le panneau gauche.</p>

<h2>Supprimer une note</h2>
<p>Clic droit sur la note → <b>Mettre à la corbeille</b>.<br>
La note n'est <b>pas supprimée définitivement</b> — elle est déplacée dans la corbeille.</p>

<h2>Corbeille</h2>
<ul>
  <li>Cliquez sur <b>🗑 Corbeille</b> pour voir les notes supprimées</li>
  <li>Clic droit → <b>Restaurer</b> pour récupérer une note</li>
  <li>Clic droit → <b>Supprimer définitivement</b> pour effacement total (irréversible)</li>
</ul>

<div class="warn">
  ⚠️ <b>Attention :</b> La suppression définitive efface aussi toutes les pièces jointes
  (images, enregistrements audio et vidéo) liées à la note.
</div>
""")

FOLDERS = _page("Dossiers", """
<h1>📂 Dossiers</h1>

<p>Les dossiers vous permettent d'organiser vos notes en arborescence,
comme un explorateur de fichiers. Ils sont <b>indépendants</b> des catégories.</p>

<h2>Accéder aux dossiers</h2>
<p>Dans le panneau gauche, cliquez sur l'onglet <b>📂 Dossiers</b>.</p>

<h2>Créer un dossier</h2>
<ul>
  <li>Bouton <b>+ Dossier</b> en haut de l'onglet → crée un dossier racine</li>
  <li>Clic droit sur un dossier → <b>Nouveau sous-dossier</b></li>
</ul>

<h2>Naviguer dans les dossiers</h2>
<ul>
  <li>Clic sur <b>📂 Tous les dossiers</b> → affiche toutes les notes</li>
  <li>Clic sur un dossier → affiche uniquement les notes de ce dossier</li>
  <li>Le nombre de notes est affiché entre parenthèses : <b>📁 Projets (3)</b></li>
</ul>

<h2>Déplacer une note dans un dossier</h2>
<p>Deux méthodes :</p>
<ol>
  <li><b>Glisser-déposer</b> : saisissez une note dans la liste centrale et
      faites-la glisser sur un dossier. Le dossier cible se surligne en violet.</li>
  <li><b>Menu contextuel</b> : clic droit sur une note →
      <b>Déplacer vers un dossier…</b> → choisissez le dossier dans la fenêtre.</li>
</ol>

<div class="tip">
  💡 Pour retirer une note de tout dossier, faites-la glisser sur
  <b>📂 Tous les dossiers</b>, ou choisissez <b>(Aucun dossier)</b>
  dans la fenêtre de déplacement.
</div>

<h2>Renommer / Supprimer un dossier</h2>
<p>Clic droit sur le dossier → <b>Renommer</b> ou <b>Supprimer</b>.</p>
<div class="warn">
  ⚠️ Supprimer un dossier supprime aussi ses <b>sous-dossiers</b> (cascade).
  Les notes qu'il contient ne sont <b>pas supprimées</b> — elles perdent juste
  leur dossier d'appartenance.
</div>
""")

CATEGORIES = _page("Catégories & Tags", """
<h1>🏷 Catégories & Tags</h1>

<p>Cliquez sur l'onglet <b>🏷 Organisation</b> dans le panneau gauche pour accéder
aux catégories et aux tags.</p>

<h2>Catégories</h2>
<p>Les catégories sont organisées en arborescence et identifiées par une couleur.
Une bande colorée apparaît à gauche de chaque note dans la liste.</p>
<ul>
  <li><b>Créer</b> : clic droit dans l'arbre → <b>Nouvelle catégorie</b></li>
  <li><b>Renommer</b> : clic droit → <b>Renommer</b></li>
  <li><b>Couleur</b> : clic droit → <b>Changer la couleur</b></li>
  <li><b>Supprimer</b> : clic droit → <b>Supprimer</b> (les notes sont décatégorisées)</li>
</ul>

<h2>Tags</h2>
<p>Les tags sont des étiquettes libres que vous attribuez à vos notes.</p>
<ul>
  <li><b>Ajouter un tag</b> : dans l'éditeur, tapez un nom dans <b>+ Ajouter un tag…</b>
      et appuyez sur <kbd>Entrée</kbd></li>
  <li><b>Supprimer un tag d'une note</b> : cliquez sur la croix ✕ du chip de tag</li>
  <li><b>Filtrer par tag</b> : cliquez sur un tag dans la liste du panneau gauche</li>
  <li><b>Supprimer un tag globalement</b> : clic droit sur le tag → <b>Supprimer</b></li>
</ul>

<div class="tip">
  💡 Combinez catégorie et tag : une note peut appartenir à la catégorie
  <i>Travail</i> et porter les tags <i>urgent</i> et <i>client-X</i>.
</div>
""")

AUDIO = _page("Enregistrement audio", """
<h1>🎤 Enregistrement audio</h1>

<p>Noteor enregistre l'audio directement depuis votre microphone et joint
le fichier WAV à la note.</p>

<h2>Enregistrer</h2>
<ol>
  <li>Ouvrez ou créez une note</li>
  <li>Cliquez sur <b>🎤 Enregistrer</b> dans la barre des pièces jointes</li>
  <li>Une barre de niveau rouge s'anime pendant l'enregistrement</li>
  <li>Cliquez sur <b>⏹ Arrêter</b> pour terminer — le fichier est automatiquement attaché</li>
</ol>

<h2>Écouter</h2>
<p>Les enregistrements apparaissent dans la zone des pièces jointes (en bas de l'éditeur).
Cliquez sur <b>▶ Lire</b> pour écouter, <b>⏹</b> pour arrêter.</p>

<h2>Supprimer un enregistrement</h2>
<p>Cliquez sur le bouton <b>🗑</b> de la pièce jointe audio.</p>

<div class="tip">
  💡 <b>Backend audio :</b> Noteor utilise <code>arecord</code> / <code>aplay</code>
  (ALSA) sur Linux, avec repli automatique sur <code>sounddevice</code> si ALSA
  n'est pas disponible.
</div>
""")

IMAGES = _page("Images & Captures d'écran", """
<h1>🖼 Images & Captures d'écran</h1>

<h2>Importer une image</h2>
<ol>
  <li>Ouvrez une note</li>
  <li>Cliquez sur <b>📁 Importer</b> dans la barre des pièces jointes</li>
  <li>Sélectionnez une image (PNG, JPG, GIF, BMP, WEBP, TIFF)</li>
</ol>
<p>Une miniature est générée automatiquement et affichée dans les pièces jointes.</p>

<h2>Capture d'écran</h2>
<ol>
  <li>Ouvrez une note</li>
  <li>Cliquez sur <b>📷 Capture</b></li>
  <li>Un compte à rebours de 3 secondes s'affiche pour que vous prépariez l'écran</li>
  <li>La fenêtre Noteor se minimise automatiquement</li>
  <li>La capture est prise via le portail XDG (compatible Wayland et X11)</li>
</ol>

<div class="tip">
  💡 La capture utilise le portail de sécurité de votre bureau — une boîte de dialogue
  système peut apparaître pour confirmer l'autorisation.
</div>

<h2>Supprimer une image</h2>
<p>Cliquez sur le bouton <b>🗑</b> qui apparaît sous la miniature.</p>

<h2>Images dans l'export PDF</h2>
<p>Lors d'un export PDF (<kbd>Ctrl+E</kbd>), les images attachées à la note
sont incluses dans une section <b>Captures et images</b> en fin de document,
à pleine résolution (jusqu'à 2000 px de large).</p>
""")

VIDEO = _page("Vidéo & Webcam", """
<h1>🎬 Vidéo & Webcam</h1>

<h2>Importer une vidéo existante</h2>
<ol>
  <li>Ouvrez une note</li>
  <li>Cliquez sur <b>📹 Vidéo</b> dans la barre des pièces jointes</li>
  <li>Sélectionnez un fichier vidéo (MP4, MKV, AVI, MOV, WEBM…)</li>
</ol>
<p>Si <code>ffprobe</code> est installé, la durée est lue automatiquement.</p>

<h2>Enregistrer depuis la webcam</h2>
<ol>
  <li>Ouvrez une note</li>
  <li>Cliquez sur <b>🎥 Webcam</b></li>
  <li>Un compteur <span class="badge">00:00</span> indique la durée en cours</li>
  <li>Cliquez sur <b>⏹ Arrêter</b> — le fichier MP4 est attaché à la note</li>
</ol>

<div class="tip">
  💡 <b>Prérequis :</b> <code>ffmpeg</code> doit être installé.<br>
  <code>sudo apt install ffmpeg</code><br><br>
  Noteor essaie automatiquement plusieurs modes de capture (MJPEG puis RAW,
  avec et sans audio) pour s'adapter à votre webcam.
</div>

<h2>Lecture</h2>
<p>Les vidéos apparaissent dans la zone des pièces jointes. Cliquez sur
<b>▶ Lire</b> pour les ouvrir dans votre lecteur vidéo système.</p>

<div class="warn">
  ⚠️ L'audio et la vidéo des pièces jointes ne sont <b>pas inclus</b> dans
  l'export PDF (seules les images sont exportées).
</div>
""")

SEARCH = _page("Recherche & Filtres", """
<h1>🔍 Recherche & Filtres</h1>

<h2>Recherche textuelle</h2>
<p>La barre de recherche (en haut du panneau gauche) filtre les notes en temps
réel sur le <b>titre</b> et le <b>contenu</b>.</p>

<h2>Filtre par dossier</h2>
<p>Onglet <b>📂 Dossiers</b> → cliquez sur un dossier pour n'afficher que
les notes qu'il contient.</p>

<h2>Filtre par catégorie</h2>
<p>Onglet <b>🏷 Organisation</b> → cliquez sur une catégorie dans l'arbre.</p>

<h2>Filtre par tag</h2>
<p>Onglet <b>🏷 Organisation</b> → cliquez sur un tag dans la liste.
Cliquez à nouveau sur le même tag pour désactiver le filtre.</p>

<h2>Filtre par type de pièce jointe</h2>
<table>
  <tr><th>Option</th><th>Notes affichées</th></tr>
  <tr><td>Toutes les notes</td><td>Toutes</td></tr>
  <tr><td>Avec audio 🎤</td><td>Notes ayant au moins un enregistrement audio</td></tr>
  <tr><td>Avec images 🖼</td><td>Notes ayant au moins une image</td></tr>
  <tr><td>Avec vidéos 🎬</td><td>Notes ayant au moins une vidéo</td></tr>
</table>

<h2>Filtre par date</h2>
<table>
  <tr><th>Option</th><th>Période</th></tr>
  <tr><td>Toutes les dates</td><td>Pas de filtre</td></tr>
  <tr><td>Aujourd'hui</td><td>Notes modifiées aujourd'hui</td></tr>
  <tr><td>7 derniers jours</td><td>Notes modifiées dans la semaine</td></tr>
  <tr><td>30 derniers jours</td><td>Notes modifiées dans le mois</td></tr>
  <tr><td>Cette année</td><td>Notes modifiées cette année</td></tr>
  <tr><td>Période…</td><td>Choisissez une date de début et de fin</td></tr>
</table>

<div class="tip">
  💡 Tous les filtres sont <b>cumulables</b> : vous pouvez chercher
  « réunion » dans les notes du dossier Travail modifiées ce mois-ci.
</div>
""")

EXPORT = _page("Export PDF", """
<h1>📄 Export PDF</h1>

<p>Noteor peut exporter n'importe quelle note en fichier PDF avec mise en page
soignée, rendu Markdown complet et captures d'écran intégrées.</p>

<h2>Exporter la note en cours</h2>
<ul>
  <li>Menu <b>Fichier → Exporter en PDF…</b></li>
  <li>Raccourci <kbd>Ctrl+E</kbd></li>
</ul>

<h2>Exporter une note depuis la liste</h2>
<p>Clic droit sur n'importe quelle note dans la liste centrale →
<b>Exporter en PDF…</b> (la note n'a pas besoin d'être ouverte).</p>

<h2>Contenu du PDF</h2>
<table>
  <tr><th>Section</th><th>Contenu</th></tr>
  <tr><td>En-tête</td><td>Titre, date de création, date de modification, tags</td></tr>
  <tr><td>Corps</td><td>Texte Markdown rendu (titres, listes, tableaux, code…)</td></tr>
  <tr><td>Images</td><td>Toutes les captures et images attachées (pleine résolution)</td></tr>
</table>

<div class="tip">
  💡 Le nom du fichier PDF est pré-rempli avec le titre de la note.
  Les caractères interdits sont automatiquement retirés.
</div>

<div class="warn">
  ⚠️ Les fichiers audio et vidéo ne sont <b>pas inclus</b> dans le PDF.
</div>
""")

SHORTCUTS = _page("Raccourcis clavier", """
<h1>⌨ Raccourcis clavier</h1>

<h2>Notes</h2>
<p>
  <span class="shortcut"><kbd>Ctrl+N</kbd></span> Nouvelle note<br>
  <span class="shortcut"><kbd>Ctrl+S</kbd></span> Sauvegarder la note en cours<br>
  <span class="shortcut"><kbd>Ctrl+E</kbd></span> Exporter en PDF<br>
</p>

<h2>Navigation</h2>
<p>
  <span class="shortcut"><kbd>F5</kbd></span> Actualiser l'interface<br>
  <span class="shortcut"><kbd>F1</kbd></span> Ouvrir cette aide<br>
</p>

<h2>Édition</h2>
<p>
  <span class="shortcut"><kbd>Ctrl+Z</kbd></span> Annuler<br>
  <span class="shortcut"><kbd>Ctrl+Y</kbd></span> Rétablir<br>
  <span class="shortcut"><kbd>Ctrl+A</kbd></span> Sélectionner tout<br>
  <span class="shortcut"><kbd>Ctrl+C</kbd></span> Copier<br>
  <span class="shortcut"><kbd>Ctrl+V</kbd></span> Coller<br>
  <span class="shortcut"><kbd>Ctrl+X</kbd></span> Couper<br>
</p>

<h2>Application</h2>
<p>
  <span class="shortcut"><kbd>Ctrl+Q</kbd></span> Quitter Noteor<br>
</p>

<div class="tip">
  💡 <b>Astuce tag :</b> Dans le champ tag de l'éditeur, appuyez sur
  <kbd>Entrée</kbd> pour valider et ajouter le tag immédiatement.
</div>
""")

# ─── Fenêtre d'aide ───────────────────────────────────────────────────────────

_TOPICS = [
    ("🚀  Démarrage rapide",      QUICK_START),
    ("📝  Gérer les notes",        NOTES),
    ("📂  Dossiers",               FOLDERS),
    ("🏷  Catégories & Tags",      CATEGORIES),
    ("🎤  Enregistrement audio",   AUDIO),
    ("🖼  Images & Captures",      IMAGES),
    ("🎬  Vidéo & Webcam",         VIDEO),
    ("🔍  Recherche & Filtres",    SEARCH),
    ("📄  Export PDF",             EXPORT),
    ("⌨  Raccourcis clavier",     SHORTCUTS),
]


class HelpWindow(QDialog):
    """Fenêtre d'aide non-modale avec navigation par topics."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Aide — {config.APP_NAME}")
        self.setMinimumSize(820, 560)
        self.resize(960, 660)
        # Non-modale : l'utilisateur peut consulter l'aide tout en travaillant
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinMaxButtonsHint
        )
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 8)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        # ── Panneau de navigation ─────────────────────────────────────
        nav = QListWidget()
        nav.setObjectName("help_nav")
        nav.setFixedWidth(210)
        nav.setStyleSheet("""
            QListWidget {
                background: #f9fafb; border: none;
                border-right: 1px solid #e5e7eb;
                font-size: 10pt;
            }
            QListWidget::item {
                padding: 9px 12px;
                border-bottom: 1px solid #f3f4f6;
                color: #374151;
            }
            QListWidget::item:selected {
                background: #ede9fe; color: #4F46E5;
                font-weight: bold; border-left: 3px solid #4F46E5;
            }
            QListWidget::item:hover:!selected { background: #f3f4f6; }
        """)
        for label, _ in _TOPICS:
            nav.addItem(QListWidgetItem(label))
        nav.currentRowChanged.connect(self._show_topic)
        splitter.addWidget(nav)

        # ── Panneau de contenu ────────────────────────────────────────
        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setStyleSheet("""
            QTextBrowser {
                border: none; background: white;
                font-size: 10pt;
            }
        """)
        splitter.addWidget(self._browser)

        splitter.setSizes([210, 750])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, 1)

        # ── Pied de page ──────────────────────────────────────────────
        footer = QHBoxLayout()
        footer.setContentsMargins(12, 4, 12, 0)
        version_lbl = QLabel(f"{config.APP_NAME} v{config.VERSION}")
        version_lbl.setStyleSheet("color: #9ca3af; font-size: 9pt;")
        footer.addWidget(version_lbl)
        footer.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.setFixedWidth(90)
        close_btn.clicked.connect(self.close)
        footer.addWidget(close_btn)
        root.addLayout(footer)

        nav.setCurrentRow(0)

    def _show_topic(self, row: int):
        if 0 <= row < len(_TOPICS):
            _, html = _TOPICS[row]
            self._browser.setHtml(html)
            self._browser.verticalScrollBar().setValue(0)

    def show_topic(self, label: str):
        """Ouvre la fenêtre et navigue directement vers un topic par son label."""
        for i, (lbl, _) in enumerate(_TOPICS):
            if label.lower() in lbl.lower():
                self._browser.parent().parent()  # splitter
                self.show()
                self.raise_()
                # trouver le QListWidget
                for child in self.findChildren(QListWidget):
                    child.setCurrentRow(i)
                    break
                return
        self.show()
        self.raise_()
