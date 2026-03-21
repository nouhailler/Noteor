#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(dirname "$SCRIPT_DIR")"
PKG_NAME="noteor"
VERSION="1.0.0"
ARCH="amd64"
DEB_NAME="${PKG_NAME}_${VERSION}_${ARCH}.deb"
BUILD_DIR="/tmp/${PKG_NAME}_build"

echo "=== Build du paquet Debian $DEB_NAME ==="

# Nettoyage
rm -rf "$BUILD_DIR"
mkdir -p "$BUILD_DIR"

# --- Structure du paquet ---
mkdir -p "$BUILD_DIR/DEBIAN"
mkdir -p "$BUILD_DIR/usr/bin"
mkdir -p "$BUILD_DIR/usr/lib/noteor/core"
mkdir -p "$BUILD_DIR/usr/lib/noteor/ui"
mkdir -p "$BUILD_DIR/usr/share/applications"
mkdir -p "$BUILD_DIR/usr/share/pixmaps"
mkdir -p "$BUILD_DIR/usr/share/doc/noteor"

# --- DEBIAN/control ---
cp "$SCRIPT_DIR/DEBIAN/control" "$BUILD_DIR/DEBIAN/control"

# --- postinst ---
cp "$SCRIPT_DIR/DEBIAN/postinst" "$BUILD_DIR/DEBIAN/postinst"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# --- Fichiers Python de l'application ---
for f in main.py config.py database.py; do
    cp "$REPO_DIR/$f" "$BUILD_DIR/usr/lib/noteor/"
done
cp "$REPO_DIR"/core/*.py "$BUILD_DIR/usr/lib/noteor/core/"
cp "$REPO_DIR"/ui/*.py   "$BUILD_DIR/usr/lib/noteor/ui/"

if [ -f "$REPO_DIR/requirements.txt" ]; then
    cp "$REPO_DIR/requirements.txt" "$BUILD_DIR/usr/lib/noteor/"
fi

# --- Lanceur /usr/bin/noteor ---
cat > "$BUILD_DIR/usr/bin/noteor" << 'EOF'
#!/bin/bash
exec python3 /usr/lib/noteor/main.py "$@"
EOF
chmod 755 "$BUILD_DIR/usr/bin/noteor"

# --- .desktop ---
cp "$SCRIPT_DIR/noteor.desktop" "$BUILD_DIR/usr/share/applications/"

# --- Icône ---
python3 "$SCRIPT_DIR/gen_icon.py" "$BUILD_DIR/usr/share/pixmaps/noteor.png"

# --- Copyright ---
cat > "$BUILD_DIR/usr/share/doc/noteor/copyright" << 'EOF'
Format: https://www.debian.org/doc/packaging-manuals/copyright-format/1.0/
Upstream-Name: Noteor
Upstream-Contact: https://github.com/nouhailler/Noteor
Source: https://github.com/nouhailler/Noteor

Files: *
Copyright: 2024 Noteor Project
License: MIT
EOF

# --- Permissions ---
find "$BUILD_DIR" -type f -name "*.py" -exec chmod 644 {} \;
chmod 755 "$BUILD_DIR/usr/bin/noteor"
chmod 755 "$BUILD_DIR/DEBIAN/postinst"

# --- Installed-Size ---
SIZE_KB=$(du -sk "$BUILD_DIR/usr" | cut -f1)
echo "Installed-Size: $SIZE_KB" >> "$BUILD_DIR/DEBIAN/control"

# --- Build ---
OUTPUT="$REPO_DIR/$DEB_NAME"
dpkg-deb --build --root-owner-group "$BUILD_DIR" "$OUTPUT"
echo ""
echo "✅ Paquet créé : $OUTPUT"
echo "   Taille : $(du -sh "$OUTPUT" | cut -f1)"
dpkg-deb --info "$OUTPUT"
