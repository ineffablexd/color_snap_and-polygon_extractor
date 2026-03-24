from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox,
    QColorDialog, QTextEdit
)
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature,
    QgsGeometry, QgsPointXY
)
import traceback


class PluginDialog(QDialog):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.color = None

        self.setWindowTitle("Canvas Color Extractor 🔥")

        layout = QVBoxLayout()

        self.tolerance = QDoubleSpinBox()
        self.tolerance.setRange(0, 255)
        self.tolerance.setValue(30)

        self.pick_btn = QPushButton("Pick Color")
        self.run_btn = QPushButton("Extract from Canvas")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(QLabel("Tolerance"))
        layout.addWidget(self.tolerance)
        layout.addWidget(self.pick_btn)
        layout.addWidget(self.run_btn)
        layout.addWidget(QLabel("Debug Log"))
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        self.pick_btn.clicked.connect(self.pick_color)
        self.run_btn.clicked.connect(self.run_extraction)

    def log(self, msg):
        self.log_box.append(msg)
        print(msg)

    def pick_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = (color.red(), color.green(), color.blue())
            self.pick_btn.setText(f"RGB: {self.color}")
            self.log(f"🎨 Picked: {self.color}")

    def run_extraction(self):
        try:
            self.log("🚀 Capturing canvas...")

            img = self.canvas.grab().toImage()
            width = img.width()
            height = img.height()

            self.log(f"Canvas size: {width} x {height}")

            if not self.color:
                self.log("❌ No color selected")
                return

            r, g, b = self.color
            tol = self.tolerance.value()

            visited = set()
            regions = []

            def match(x, y):
                c = img.pixelColor(x, y)
                return (
                    abs(c.red() - r) <= tol and
                    abs(c.green() - g) <= tol and
                    abs(c.blue() - b) <= tol
                )

            # 🔥 REGION GROWING
            for x in range(width):
                for y in range(height):
                    if (x, y) in visited:
                        continue
                    if not match(x, y):
                        continue

                    stack = [(x, y)]
                    region = []

                    while stack:
                        px, py = stack.pop()

                        if (px, py) in visited:
                            continue
                        if px < 0 or py < 0 or px >= width or py >= height:
                            continue
                        if not match(px, py):
                            continue

                        visited.add((px, py))
                        region.append((px, py))

                        stack.extend([
                            (px+1, py), (px-1, py),
                            (px, py+1), (px, py-1)
                        ])

                    if len(region) > 100:
                        regions.append(region)

            self.log(f"Regions found: {len(regions)}")

            # 🔥 CORRECT CRS FROM CANVAS
            crs = self.canvas.mapSettings().destinationCrs().authid()
            vl = QgsVectorLayer(f"Polygon?crs={crs}", "Extracted", "memory")
            pr = vl.dataProvider()

            # 🔥 CORRECT TRANSFORM
            map_settings = self.canvas.mapSettings()
            transform = map_settings.mapToPixel()

            for region in regions:
                pts = []

                # reduce density for cleaner shapes
                for x, y in region[::8]:
                    map_pt = transform.toMapCoordinates(x, y)
                    pts.append(QgsPointXY(map_pt))

                if len(pts) < 3:
                    continue

                feat = QgsFeature()
                feat.setGeometry(QgsGeometry.fromPolygonXY([pts]))
                pr.addFeature(feat)

            vl.updateExtents()
            QgsProject.instance().addMapLayer(vl)

            self.log("✅ Extraction complete")

        except Exception:
            self.log("💥 ERROR:")
            self.log(traceback.format_exc())


class ColorSnapPlugin:
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("Canvas Extractor", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Ineffable Tools", self.action)

    def unload(self):
        self.iface.removePluginMenu("&Ineffable Tools", self.action)

    def run(self):
        self.dlg = PluginDialog(self.iface.mapCanvas())
        self.dlg.show()