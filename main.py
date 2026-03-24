from qgis.PyQt.QtWidgets import (
    QAction, QDialog, QVBoxLayout, QLabel,
    QPushButton, QDoubleSpinBox,
    QColorDialog, QTextEdit, QWidget
)
from qgis.PyQt.QtGui import QColor, QPainter, QBrush
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature,
    QgsGeometry, QgsPointXY, QgsWkbTypes, QgsRectangle
)
from qgis.gui import QgsMapTool, QgsRubberBand
from qgis.PyQt.QtCore import Qt
import traceback
import colorsys

class CanvasColorPicker(QgsMapTool):
    def __init__(self, canvas, callback):
        super().__init__(canvas)
        self.canvas = canvas
        self.callback = callback

    def canvasReleaseEvent(self, e):
        img = self.canvas.grab().toImage()
        x = int(e.pos().x())
        y = int(e.pos().y())

        if 0 <= x < img.width() and 0 <= y < img.height():
            c = img.pixelColor(x, y)
            rgb = (c.red(), c.green(), c.blue())
            self.callback(rgb)

        self.canvas.unsetMapTool(self)


class ColorSwatchList(QWidget):
    def __init__(self, get_colors):
        super().__init__()
        self.get_colors = get_colors
        self.setMinimumHeight(50)

    def paintEvent(self, event):
        painter = QPainter(self)
        colors = self.get_colors()

        if not colors:
            return

        w = self.width() // len(colors)

        for i, (r, g, b) in enumerate(colors):
            painter.setBrush(QColor(r, g, b))
            painter.setPen(Qt.NoPen)
            painter.drawRect(i * w, 0, w, self.height())


class TolerancePreview(QWidget):
    def __init__(self, get_color):
        super().__init__()
        self.get_color = get_color
        self.setMinimumHeight(50)
        self.min_factor = 0.25
        self.max_factor = 0.75
        self.dragging = None

    def paintEvent(self, event):
        painter = QPainter(self)

        colors = self.get_color()
        if not colors:
            return

        # Use last selected color
        r, g, b = colors[-1]

        # Convert to HSV
        h, s, v = colorsys.rgb_to_hsv(r/255, g/255, b/255)

        for x in range(self.width()):
            factor = x / self.width()
            # vary VALUE (brightness) from 0 to 1
            rr, gg, bb = colorsys.hsv_to_rgb(h, s, factor)
            painter.setBrush(QBrush(QColor(int(rr*255), int(gg*255), int(bb*255))))
            painter.setPen(Qt.NoPen)
            painter.drawRect(x, 0, 1, self.height())

        # draw selection overlay
        painter.setPen(Qt.red)
        painter.drawLine(int(self.min_factor * self.width()), 0,
                         int(self.min_factor * self.width()), self.height())

        painter.drawLine(int(self.max_factor * self.width()), 0,
                         int(self.max_factor * self.width()), self.height())

    def mousePressEvent(self, e):
        x = e.pos().x() / self.width()
        if abs(x - self.min_factor) < 0.05:
            self.dragging = "min"
        elif abs(x - self.max_factor) < 0.05:
            self.dragging = "max"

    def mouseMoveEvent(self, e):
        if not self.dragging:
            return
        x = max(0, min(1, e.pos().x() / self.width()))
        if self.dragging == "min":
            self.min_factor = min(x, self.max_factor - 0.01)
        else:
            self.max_factor = max(x, self.min_factor + 0.01)
        self.update()

    def mouseReleaseEvent(self, e):
        self.dragging = None



class PluginDialog(QDialog):
    def __init__(self, canvas):
        super().__init__()
        self.canvas = canvas
        self.colors = []
        self.layer = None

        self.setWindowTitle("Canvas Color Extractor 🔥")

        layout = QVBoxLayout()

        self.swatches = ColorSwatchList(lambda: self.colors)
        self.preview = TolerancePreview(lambda: self.colors)

        self.pick_btn = QPushButton("Pick Color")
        self.run_btn = QPushButton("Extract from Canvas")

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)

        layout.addWidget(QLabel("Picked Colors"))
        layout.addWidget(self.swatches)
        layout.addWidget(QLabel("Tolerance Spectrum (Drag Red Lines)"))
        layout.addWidget(self.preview)
        layout.addWidget(self.pick_btn)
        layout.addWidget(self.run_btn)
        layout.addWidget(QLabel("Debug Log"))
        layout.addWidget(self.log_box)

        self.setLayout(layout)

        self.pick_btn.clicked.connect(self.pick_color)
        self.run_btn.clicked.connect(self.run_extraction)

        self.map_tool = None

    def log(self, msg):
        self.log_box.append(msg)
        print(msg)

    def pick_color(self):
        self.log("🎯 Click on canvas to pick color...")
        self.canvas.setMapTool(CanvasColorPicker(self.canvas, self.add_color))

    def add_color(self, rgb):
        self.colors.append(rgb)
        self.pick_btn.setText(f"{len(self.colors)} colors selected")
        self.swatches.update()   # 🔥 update UI
        self.preview.update()    # also update spectrum
        self.log(f"🎨 Picked from canvas: {rgb}")

    def run_extraction(self):
        try:
            self.log("🚀 Capturing canvas...")

            img = self.canvas.grab().toImage()
            width = img.width()
            height = img.height()

            self.log(f"Canvas size: {width} x {height}")

            if not self.colors:
                self.log("❌ No color selected")
                return

            factor_min = self.preview.min_factor
            factor_max = self.preview.max_factor

            visited = set()
            regions = []

            def match(x, y):
                c = img.pixelColor(x, y)
                r2, g2, b2 = c.red(), c.green(), c.blue()
                h2, s2, v2 = colorsys.rgb_to_hsv(r2/255, g2/255, b2/255)
                
                for (r, g, b) in self.colors:
                    h1, s1, v1 = colorsys.rgb_to_hsv(r/255, g/255, b/255)
                    
                    # Same color family (handle hue wrap-around)
                    hue_diff = abs(h1 - h2)
                    if hue_diff > 0.5: hue_diff = 1.0 - hue_diff

                    if hue_diff < 0.05:
                        if factor_min <= v2 <= factor_max:
                            return True
                return False

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
            
            if not self.layer:
                self.layer = QgsVectorLayer(f"Polygon?crs={crs}", "Extracted", "memory")
                QgsProject.instance().addMapLayer(self.layer)
            
            pr = self.layer.dataProvider()

            # 🔥 CORRECT TRANSFORM
            map_settings = self.canvas.mapSettings()
            transform = map_settings.mapToPixel()

            all_new_geoms = []
            for region in regions:
                if len(region) < 10:
                    continue

                # 1. Group pixels by rows (y-coordinate)
                lines = {}
                for px, py in region:
                    if py not in lines:
                        lines[py] = []
                    lines[py].append(px)

                # 2. Find contiguous horizontal segments
                region_segments_geoms = []
                for py, x_coords in lines.items():
                    x_coords.sort()
                    start = x_coords[0]
                    prev = start

                    segments = []
                    for i in range(1, len(x_coords)):
                        x = x_coords[i]
                        if x == prev + 1:
                            prev = x
                        else:
                            segments.append((start, py, prev, py))
                            start = x
                            prev = x
                    segments.append((start, py, prev, py))

                    # 3. Create map geometry for each segment
                    for (startX, startY, endX, endY) in segments:
                        p1 = transform.toMapCoordinates(startX, startY)
                        p2 = transform.toMapCoordinates(endX + 1, startY)
                        p3 = transform.toMapCoordinates(endX + 1, startY + 1)
                        p4 = transform.toMapCoordinates(startX, startY + 1)

                        poly = QgsGeometry.fromPolygonXY([[
                            QgsPointXY(p1), QgsPointXY(p2), 
                            QgsPointXY(p3), QgsPointXY(p4)
                        ]])
                        region_segments_geoms.append(poly)

                if not region_segments_geoms:
                    continue

                # 4. Union all segments for this region
                combined = QgsGeometry.unaryUnion(region_segments_geoms)
                
                # 5. Smooth + Simplify
                combined = combined.buffer(0.5, 3)
                combined = combined.simplify(0.3)
                
                if combined and not combined.isEmpty():
                    all_new_geoms.append(combined)

            # 6. Merge ALL new regions with existing layer content
            if all_new_geoms:
                final_new_geom = QgsGeometry.unaryUnion(all_new_geoms)
                existing_feats = list(self.layer.getFeatures())

                if existing_feats:
                    merged_geom = final_new_geom
                    for f in existing_feats:
                        merged_geom = merged_geom.combine(f.geometry())

                    # clear old and add merged
                    self.layer.dataProvider().truncate()
                    feat = QgsFeature()
                    feat.setGeometry(merged_geom)
                    pr.addFeature(feat)
                else:
                    feat = QgsFeature()
                    feat.setGeometry(final_new_geom)
                    pr.addFeature(feat)

            self.layer.updateExtents()
            self.canvas.refresh()

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