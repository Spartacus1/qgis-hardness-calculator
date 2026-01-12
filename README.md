# Hardness Calculator (QGIS Plugin)

Hardness Calculator is a QGIS plugin that computes **hardness values for point layers**
using sonar-derived attributes such as **Depth, E1, E2 and PeakSV**.

The plugin is designed for geophysical and geotechnical workflows where a rapid,
reproducible hardness indicator is required directly inside QGIS.

---

## Features

- Works with **point vector layers**
- Uses sonar-derived attributes:
  - Depth
  - E1
  - E2
  - PeakSV
- Writes results directly to the layer attribute table
- Optional confidence estimation
- Processing log for traceability
- Automatic handling of existing output fields

---

## Requirements

- **QGIS ≥ 3.10**
- Python packages available in the QGIS Python environment:
  - `numpy`
  - `pandas`
  - `scipy`
  - `scikit-learn`

> **Note**  
> These packages may not be available in a default QGIS installation and may need
> to be installed manually in the QGIS Python environment.

---

## Installation

### Install from ZIP

1. Download the plugin ZIP from the GitHub *Releases* page.
2. Open QGIS → **Plugins → Manage and Install Plugins → Install from ZIP**.
3. Select the ZIP file and install.

### Development installation

Clone this repository and place (or symlink) the plugin folder into your QGIS plugins directory:

- **Linux**  
  `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/`

- **macOS**  
  `~/Library/Application Support/QGIS/QGIS3/profiles/default/python/plugins/`

- **Windows**  
  `%APPDATA%\QGIS\QGIS3\profiles\default\python\plugins\`

Restart QGIS after installation.

---

## Usage

1. Load a **point layer** containing the required attributes.
2. Select the layer in the Layers panel.
3. Open **Plugins → Hardness Calculator**.
4. Configure the input fields.
5. Run the calculation.

The plugin adds one or more new fields (e.g. `Hardness`, `Confidence`) to the layer.

---

## License

This project is licensed under the **MIT License**.  
See the `LICENSE` file for details.
