#!/usr/bin/env bash
# ──────────────────────────────────────────────────────────────────────────────
#  Script d'installation de Noteor pour Debian / Ubuntu
# ──────────────────────────────────────────────────────────────────────────────
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "════════════════════════════════════════"
echo "  Installation de Noteor"
echo "════════════════════════════════════════"

# ── 1. Dépendances système ────────────────────────────────────────────────────
echo ""
echo "▶ Installation des dépendances système (sudo requis)…"
sudo apt-get update -qq
sudo apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    portaudio19-dev \
    libsndfile1 \
    libsndfile1-dev \
    libasound2-dev

echo "  ✓ Dépendances système installées"

# ── 2. Environnement virtuel ──────────────────────────────────────────────────
echo ""
echo "▶ Création de l'environnement virtuel Python…"
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  ✓ Environnement virtuel créé dans $VENV_DIR"
else
    echo "  ℹ  Environnement virtuel déjà existant, mise à jour…"
fi

source "$VENV_DIR/bin/activate"

# ── 3. Paquets Python ─────────────────────────────────────────────────────────
echo ""
echo "▶ Installation des paquets Python…"
pip install --upgrade pip -q
pip install -r "$SCRIPT_DIR/requirements.txt"
echo "  ✓ Paquets Python installés"

# ── 4. Entrée de bureau (optionnel) ───────────────────────────────────────────
DESKTOP_FILE="$HOME/.local/share/applications/noteor.desktop"
echo ""
echo "▶ Création de l'entrée de bureau…"
mkdir -p "$HOME/.local/share/applications"
cat > "$DESKTOP_FILE" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Noteor
Comment=Gestionnaire de notes avec audio et images
Exec=bash -c 'source "$VENV_DIR/bin/activate" && python "$SCRIPT_DIR/main.py"'
Icon=text-editor
Terminal=false
Categories=Office;Notes;
Keywords=notes;todo;audio;images;
EOF
chmod +x "$DESKTOP_FILE"
echo "  ✓ Entrée de bureau créée : $DESKTOP_FILE"

# ── 5. Script de lancement rapide ─────────────────────────────────────────────
LAUNCHER="$SCRIPT_DIR/noteor"
cat > "$LAUNCHER" <<'LAUNCHER_EOF'
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/venv/bin/activate"
exec python "$SCRIPT_DIR/main.py" "$@"
LAUNCHER_EOF
chmod +x "$LAUNCHER"

echo ""
echo "════════════════════════════════════════"
echo "  Installation terminée !"
echo "════════════════════════════════════════"
echo ""
echo "  Pour lancer Noteor :"
echo "    ./noteor"
echo "  ou depuis n'importe où :"
echo "    $LAUNCHER"
echo ""
