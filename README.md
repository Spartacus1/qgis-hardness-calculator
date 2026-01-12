# Hardness Calculator

[![QGIS](https://img.shields.io/badge/QGIS-3.10%2B-93b023?logo=qgis&logoColor=white)](https://qgis.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Version](https://img.shields.io/badge/version-0.1.0-orange.svg)](https://github.com/Spartacus1/qgis-hardness-calculator/releases)

A QGIS plugin for computing **seafloor hardness indices** from sonar-derived acoustic attributes. Designed for geophysical and geotechnical workflows requiring rapid, reproducible substrate characterization directly within QGIS.

---

## Table of Contents

- [Overview](#overview)
- [Scientific Background](#scientific-background)
- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
- [Usage](#usage)
- [Parameters Reference](#parameters-reference)
- [Output](#output)
- [Troubleshooting](#troubleshooting)
- [License](#license)
- [Author](#author)

---

## Overview

**Hardness Calculator** estimates substrate hardness from acoustic backscatter data typically acquired with single-beam echosounders (e.g., BioSonics, Simrad). The plugin implements a weighted linear model combining three sonar-derived metrics:

- **E1** — First echo energy (direct seafloor return)
- **E2** — Second echo energy (sub-bottom return)
- **PeakSV** — Peak volume backscattering strength
- **Depth** — Water depth (used for calibration in Optimized Mode)

These parameters are sensitive to seafloor composition, roughness, and consolidation, making them effective proxies for substrate hardness classification.

---

## Scientific Background

### The Hardness Model

The plugin computes hardness using a weighted linear combination:

```
H = k1*E1 + k2*f(E1,E2) + k3*PeakSV
```

Where:
- **H** is the computed hardness index
- **k1, k2, k3** are weighting coefficients
- **f(E1,E2)** is the echo ratio function

### Echo Ratio Formulations

Two formulations are available for the E1/E2 relationship:

| Mode | Formula | Use Case |
|------|---------|----------|
| **Standard** | E1 / E2 | Linear sonar data |
| **Linearized** | 10^((E1-E2)/10) | Logarithmic (dB) sonar data |

The linearized mode converts decibel differences back to linear ratios, appropriate when E1 and E2 are recorded in dB units.

### Physical Interpretation

| Parameter | Physical Meaning | Hardness Correlation |
|-----------|------------------|----------------------|
| **E1** (First Echo) | Energy reflected from the water-sediment interface | Higher E1 indicates harder substrate |
| **E2** (Second Echo) | Energy penetrating sediment and reflecting from sub-bottom | Higher E2 indicates softer, more penetrable sediment |
| **E1/E2 Ratio** | Relative surface vs. sub-surface reflectivity | Higher ratio indicates harder surface layer |
| **PeakSV** | Maximum volume scattering strength | Higher values indicate rougher, harder substrates |

### Calibration Approach

The **Optimized Mode** uses depth as a proxy target variable, based on the empirical observation that substrate hardness often correlates with bathymetric position (e.g., harder substrates on slopes, softer in depressions). The regression identifies coefficient weights that best explain depth variation through acoustic parameters.

**Note**: This assumes a site-specific relationship between depth and hardness. For rigorous applications, ground-truth calibration with sediment samples is recommended.

---

## Features

- Point vector layer support
- Flexible field mapping for E1, E2, PeakSV, and Depth
- **Manual Mode** — User-defined coefficients
- **Optimized Mode** — Regression-based coefficient estimation
- Standard and linearized (dB) echo ratio options
- Bounded least-squares optimization with physical constraints
- Percentile-based outlier removal
- Confidence estimation (High/Low based on data completeness)
- Detailed processing log for traceability and QA/QC
- Progress bar for large datasets
- Automatic field naming to avoid overwrites

---

## Requirements

### Software

- **QGIS 3.10 or higher** (tested up to 3.34)

### Python Dependencies

The following packages must be available in the QGIS Python environment:

| Package | Purpose |
|---------|---------|
| `numpy` | Numerical operations |
| `pandas` | Data manipulation |
| `scipy` | Bounded least-squares regression |
| `scikit-learn` | Linear regression |

### Installing Dependencies

**Windows (OSGeo4W Shell):**
```bash
python -m pip install numpy pandas scipy scikit-learn
```

**Linux:**
```bash
pip3 install --user numpy pandas scipy scikit-learn
```

**macOS:**
```bash
/Applications/QGIS.app/Contents/MacOS/bin/pip3 install numpy pandas scipy scikit-learn
```

---

## Installation

### From ZIP (Recommended)

1. Download the latest release ZIP from [Releases](https://github.com/Spartacus1/qgis-hardness-calculator/releases)
2. Open QGIS and navigate to **Plugins > Manage and Install Plugins**
3. Select **Install from ZIP**
4. Browse to the downloaded file and click **Install Plugin**

### Development Installation

Clone the repository directly into your QGIS plugins folder:

```bash
# Linux
cd ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/
git clone https://github.com/Spartacus1/qgis-hardness-calculator.git

# macOS
cd ~/Library/Application\ Support/QGIS/QGIS3/profiles/default/python/plugins/
git clone https://github.com/Spartacus1/qgis-hardness-calculator.git

# Windows (PowerShell)
cd $env:APPDATA\QGIS\QGIS3\profiles\default\python\plugins\
git clone https://github.com/Spartacus1/qgis-hardness-calculator.git
```

Restart QGIS and enable the plugin in **Plugins > Manage and Install Plugins**.

---

## Usage

### Quick Start

1. Load a **point layer** with sonar attributes (E1, E2, PeakSV, Depth)
2. Select the layer in the Layers panel
3. Open **Plugins > Hardness Calculator**
4. Map the attribute fields to the corresponding parameters
5. Choose calculation mode and parameters
6. Click **Calculate Hardness**

### Step-by-Step Guide

#### 1. Prepare Your Data

Ensure your point layer contains numeric fields for:
- First echo energy (E1)
- Second echo energy (E2)
- Peak volume scattering (PeakSV)
- Water depth (required for Optimized Mode)

#### 2. Configure Field Mapping

Select the corresponding field from your layer for each parameter. The plugin reads field names from the active layer.

#### 3. Select Calculation Mode

**Manual Mode:**
- Enter custom k1, k2, k3 values
- Use when you have pre-calibrated coefficients
- Recommended for production/operational use

**Optimized Mode:**
- Coefficients estimated via bounded regression
- Uses depth as the target variable
- Includes outlier removal (configurable percentiles)
- Best for exploratory analysis or initial calibration

#### 4. Linearization Option

Enable **"Use linearized E1/E2"** if your sonar data is recorded in decibels (dB). This converts the E1-E2 difference back to a linear ratio.

#### 5. Run Calculation

Click **Calculate Hardness**. The plugin will:
1. Extract and validate data
2. Apply outlier removal (Optimized Mode)
3. Compute or estimate coefficients
4. Calculate hardness for all features
5. Write results to new attribute fields

---

## Parameters Reference

### Weighting Coefficients

| Parameter | Description | Default | Recommended Range |
|-----------|-------------|---------|-------------------|
| **k1** | Weight for E1 (first echo) | 0.7 | 0.5 – 1.5 |
| **k2** | Weight for E1/E2 ratio | 0.5 (standard) / 0.03 (linearized) | 0.1 – 0.7 (standard) / 0.01 – 0.05 (linearized) |
| **k3** | Weight for PeakSV | 0.3 | 0.2 – 0.5 |

### Optimized Mode Settings

| Parameter | Description | Default |
|-----------|-------------|---------|
| **Lower Percentile** | Lower bound for outlier removal | 5% |
| **Upper Percentile** | Upper bound for outlier removal | 95% |

### Bounded Regression Constraints

The optimized mode constrains coefficients within physically meaningful ranges:

| Coefficient | Standard Mode | Linearized Mode |
|-------------|---------------|-----------------|
| k1 | [0.5, 1.5] | [0.5, 1.5] |
| k2 | [0.1, 0.7] | [0.01, 0.05] |
| k3 | [0.2, 0.5] | [0.2, 0.5] |

---

## Output

### Modified Layer

The plugin writes results directly to the input layer — no new file is created. The original vector file (Shapefile, GeoPackage, etc.) is modified in place with two new attribute fields:

| Field | Type | Description |
|-------|------|-------------|
| `Hardness` | Double | Computed hardness index (dimensionless) |
| `Confidence` | String | "High" (full formula with E2) or "Low" (simplified formula, E2 missing or invalid) |

If fields with these names already exist, the plugin appends a numeric suffix (e.g., `Hardness_1`, `Confidence_1`) to avoid overwriting previous calculations.

### Processing Log

A detailed log file is created alongside the input layer:

```
<layer_name>_hardness_processing.txt
```

The log includes:
- Input parameters and field mappings
- Data statistics and outlier removal summary
- Correlation matrix (Optimized Mode)
- Regression diagnostics (bounded and unbounded results)
- Per-feature calculation details (debug mode)
- Processing timestamps

---

## Troubleshooting

### Common Issues

| Problem | Cause | Solution |
|---------|-------|----------|
| Plugin not visible in menu | Not enabled | Go to **Plugins > Manage and Install > Installed** and enable |
| "No valid data found" | NULL values or non-numeric fields | Check data; ensure fields contain valid numbers |
| Import errors on launch | Missing dependencies | Install numpy, pandas, scipy, scikit-learn |
| Hardness values are NULL | E1 or PeakSV <= 0 | Check for invalid/missing sonar readings |
| Very high/low hardness values | Uncalibrated coefficients | Use Optimized Mode or calibrate with ground truth |

### Checking Dependencies

Open the QGIS Python Console (**Plugins > Python Console**) and run:

```python
import numpy, pandas, scipy, sklearn
print("All dependencies OK")
```

### Log File Location

The processing log is saved in the same directory as the input layer. For debugging, check this file for detailed error messages and calculation traces.

---

## Roadmap

- Support for polygon layers (zonal statistics)
- Export hardness classification maps
- Integration with RoxAnn / QTC classification schemes
- Batch processing for multiple layers
- GPU acceleration for large datasets

---

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit your changes (`git commit -am 'Add new feature'`)
4. Push to the branch (`git push origin feature/new-feature`)
5. Open a Pull Request

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## Author

**Renato Henriques**  
University of Minho, Portugal  
rhenriques@dct.uminho.pt

---

## Citation

If you use this plugin in your research, please cite:

```bibtex
@software{henriques2025hardness,
  author = {Henriques, Renato},
  title = {Hardness Calculator: A QGIS Plugin for Sonar-Based Substrate Classification},
  year = {2025},
  url = {https://github.com/Spartacus1/qgis-hardness-calculator}
}
```

---

## Acknowledgments

- University of Minho, Department of Earth Sciences; Institute of Earth Sciences
