#!/usr/bin/env python3
"""Génère l'icône Noteor (noteor.png) dans le répertoire courant."""
import sys
from PyQt6.QtWidgets import QApplication
from PyQt6.QtGui import (QPainter, QColor, QLinearGradient, QPen,
                          QFont, QFontMetrics, QPixmap, QBrush,
                          QPainterPath)
from PyQt6.QtCore import Qt, QRectF, QPointF

app = QApplication(sys.argv)

SIZE = 256
pix = QPixmap(SIZE, SIZE)
pix.fill(Qt.GlobalColor.transparent)

p = QPainter(pix)
p.setRenderHint(QPainter.RenderHint.Antialiasing)

# Fond arrondi dégradé indigo→violet
grad = QLinearGradient(0, 0, SIZE, SIZE)
grad.setColorAt(0.0, QColor("#4F46E5"))
grad.setColorAt(1.0, QColor("#7C3AED"))
p.setBrush(QBrush(grad))
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(QRectF(8, 8, SIZE-16, SIZE-16), 48, 48)

# Feuille blanche (corps de la note)
p.setBrush(QColor(255, 255, 255, 230))
p.setPen(Qt.PenStyle.NoPen)
p.drawRoundedRect(QRectF(64, 52, 132, 156), 10, 10)

# Coin replié (effet page tournée)
path = QPainterPath()
path.moveTo(164, 52)
path.lineTo(196, 52)
path.lineTo(196, 84)
path.closeSubpath()
p.setBrush(QColor("#E0E7FF"))
p.drawPath(path)

# Lignes de texte symboliques
p.setPen(QPen(QColor("#6366F1"), 6, Qt.PenStyle.SolidLine, Qt.PenCapStyle.RoundCap))
for y in [100, 122, 144, 166]:
    w = 90 if y != 166 else 55
    p.drawLine(int(84), y, int(84 + w), y)

# Micro (symbole audio) en bas à droite
p.setBrush(QColor("#EC4899"))
p.setPen(Qt.PenStyle.NoPen)
p.drawEllipse(QRectF(150, 158, 42, 42))
p.setPen(QPen(Qt.GlobalColor.white, 3))
p.drawLine(171, 167, 171, 183)
p.drawLine(162, 190, 180, 190)

p.end()

output = sys.argv[1] if len(sys.argv) > 1 else "noteor.png"
pix.save(output, "PNG")
print(f"Icône générée : {output} ({SIZE}x{SIZE})")
