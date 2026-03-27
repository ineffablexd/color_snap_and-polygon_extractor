# 🎨 Color Snap Polygon `v1.0`

> **QGIS Plugin for Color-Based Area Extraction & Digitization**

[![QGIS Version](https://img.shields.io/badge/QGIS-3.0+-green.svg)](https://qgis.org/)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Suite](https://img.shields.io/badge/Suite-Ineffable_Tools-orange.svg)](#)

Draw polygons automatically snapping to selected colors directly from the QGIS canvas. This tool utilizes an advanced pixel-based region-growing algorithm to trace contiguous color areas, making complex digitization tasks fast and precise. Part of the **Ineffable Tools** suite.

---

## 📸 Visual Workflow

<p align="center">
  <img src="assets/ui_overview.png" alt="UI Overview" width="45%" style="margin: 5px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />
  <img src="assets/extraction_progress.png" alt="Extraction Progress" width="45%" style="margin: 5px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />
</p>
<p align="center">
  <img src="assets/shape_smoother.png" alt="Shape Smoothing" width="70%" style="margin-top: 15px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);" />
</p>

---

## 🔥 Key Features

- **🎯 Interactive Color Picking**: Use the dedicated map tool to sample colors directly from any visible layer on the QGIS canvas.
- **🌈 Multi-Color Selection**: Pick and manage multiple color swatches to extract complex multi-tonal features in one go.
- **🎚️ Spectrum Tolerance Control**: Fine-tune the extraction sensitivity with an interactive Value (Brightness) spectrum preview.
- **✨ Boundary Smoothing**: Intelligent post-processing applying buffer, smoothing, and simplification to create clean vector shapes.
- **💾 Memory Layer Integration**: Automatically saves and merges extractions into a high-speed memory layer for instant viewing.

---

## 🛠️ Installation

1. **Locate Plugin Directory**:
   Open terminal and navigate to your QGIS plugins folder:

   ```bash
   cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
   ```

2. **Clone the Repository**:

   ```bash
   git clone https://github.com/ineffablexd/color_snap_and-polygon_extractor.git
   ```

3. **Reload QGIS**:
   Restart QGIS or use the **Plugin Reloader** to activate the tool. You'll find it under the `Ineffable Tools` menu.

---

## 📖 How to Use

1. **Launch the Tool**: Open the **Canvas Color Extractor** from the `Ineffable Tools` top-level menu.
2. **Sample Colors**: Click **Pick Color** and select the target regions on your map canvas. You can pick multiple colors.
3. **Refine Tolerance**: Use the **Active Color Tolerance Spectrum** sliders to adjust how much brightness variation is allowed.
4. **Generate Vector**: Click **Extract from Canvas**. The plugin will process the current view and add a new layer named `Extracted`.
5. **Iterate**: New extractions will automatically merge with existing features in the `Extracted` layer, allowing for additive workflows.

---

<p align="center">
  Made with ❤️ by <b><a href="https://github.com/ineffablexd">Ineffable</a></b>
</p>

<p align="center">
  <i>Part of the Ineffable Tools Suite for QGIS</i>
</p>
