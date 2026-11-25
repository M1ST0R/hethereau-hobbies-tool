from PySide6.QtGui import QGuiApplication, QImage, QPainter
from PySide6.QtSvg import QSvgRenderer
app = QGuiApplication([])
renderer = QSvgRenderer("assets/app_icon.svg")
if not renderer.isValid(): raise SystemExit("assets/app_icon.svg is invalid")
image = QImage(1024, 1024, QImage.Format.Format_RGBA8888)
image.fill(0)
painter = QPainter(image)
renderer.render(painter)
painter.end()
if image.isNull() or not image.save("assets/app_icon.png"): raise SystemExit("Failed to render PNG icon")
print("Rendered app icon from SVG")
