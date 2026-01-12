from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QMessageBox, QProgressBar, QRadioButton, QButtonGroup
from qgis.core import QgsProject, QgsVectorLayer, QgsField, edit
from qgis.PyQt.QtCore import QVariant, Qt
import pandas as pd
import numpy as np
import time
from scipy.optimize import lsq_linear
from sklearn.linear_model import LinearRegression
from datetime import datetime
import os

class HardnessDialog(QDialog):
    def __init__(self, iface):
        super().__init__()
        self.iface = iface
        self.setWindowTitle("Hardness Calculator")
        self.resize(400, 500)

        layout = QVBoxLayout()

        # Layer selection
        self.layer_label = QLabel("Select Layer:")
        self.layer_combo = QComboBox()
        for layer in QgsProject.instance().mapLayers().values():
            if isinstance(layer, QgsVectorLayer):
                self.layer_combo.addItem(layer.name())
        layout.addWidget(self.layer_label)
        layout.addWidget(self.layer_combo)

        # Field selections
        self.field_labels = {}
        self.field_combos = {}
        for field in ["E1", "E2", "PeakSV", "Depth"]:
            label = QLabel(f"Select {field} field:")
            combo = QComboBox()
            layout.addWidget(label)
            layout.addWidget(combo)
            self.field_labels[field] = label
            self.field_combos[field] = combo

        self.layer_combo.currentIndexChanged.connect(self.update_field_combos)
        self.update_field_combos()

        # Mode selection
        self.mode_label = QLabel("Select Calculation Mode:")
        self.manual_mode = QRadioButton("Manual (User-defined k1, k2, k3)")
        self.optimized_mode = QRadioButton("Optimized (Regression-based)")
        self.manual_mode.setChecked(True)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.manual_mode)
        self.mode_group.addButton(self.optimized_mode)

        layout.addWidget(self.mode_label)
        layout.addWidget(self.manual_mode)
        layout.addWidget(self.optimized_mode)

        # Manual input for k1, k2, k3
        self.k1_label = QLabel("k1 (recommended: 0.7 (0.5-1)):")
        self.k1_input = QLineEdit("0.7")
        self.k2_label = QLabel("k2 (recommended: 0.5 (0.3-0.7)):")
        self.k2_input = QLineEdit("0.5")
        self.k3_label = QLabel("k3 (recommended: 0.3 (0.2-0.5)):")
        self.k3_input = QLineEdit("0.3")

        layout.addWidget(self.k1_label)
        layout.addWidget(self.k1_input)
        layout.addWidget(self.k2_label)
        layout.addWidget(self.k2_input)
        layout.addWidget(self.k3_label)
        layout.addWidget(self.k3_input)

        # Percentile input for optimized mode
        self.percentile_label = QLabel("Set Percentiles for Outlier Removal (Optimized Mode):")
        self.percentile_lower_label = QLabel("Lower Percentile (%):")
        self.percentile_lower_input = QLineEdit("5")
        self.percentile_upper_label = QLabel("Upper Percentile (%):")
        self.percentile_upper_input = QLineEdit("95")

        layout.addWidget(self.percentile_label)
        layout.addWidget(self.percentile_lower_label)
        layout.addWidget(self.percentile_lower_input)
        layout.addWidget(self.percentile_upper_label)
        layout.addWidget(self.percentile_upper_input)

        # Calculate button
        self.calculate_button = QPushButton("Calculate Hardness")
        self.calculate_button.clicked.connect(self.calculate_hardness)
        layout.addWidget(self.calculate_button)

        # Output display
        self.result_label = QLabel("Results (k1, k2, k3):")
        self.result_field = QLineEdit()
        self.result_field.setReadOnly(True)
        layout.addWidget(self.result_label)
        layout.addWidget(self.result_field)

        # Progress bar
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)

        # Connect mode change to UI updates
        self.manual_mode.toggled.connect(self.update_ui_mode)
        self.update_ui_mode()

    def update_field_combos(self):
        layer_name = self.layer_combo.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        fields = [field.name() for field in layer.fields()]
        for combo in self.field_combos.values():
            combo.clear()
            combo.addItems(fields)

    def update_ui_mode(self):
        is_manual = self.manual_mode.isChecked()

        # Enable/disable manual k inputs
        self.k1_label.setEnabled(is_manual)
        self.k1_input.setEnabled(is_manual)
        self.k2_label.setEnabled(is_manual)
        self.k2_input.setEnabled(is_manual)
        self.k3_label.setEnabled(is_manual)
        self.k3_input.setEnabled(is_manual)

        # Enable/disable optimized mode percentiles
        is_optimized = self.optimized_mode.isChecked()
        self.percentile_label.setEnabled(is_optimized)
        self.percentile_lower_label.setEnabled(is_optimized)
        self.percentile_lower_input.setEnabled(is_optimized)
        self.percentile_upper_label.setEnabled(is_optimized)
        self.percentile_upper_input.setEnabled(is_optimized)

    def normalize_data(self, data):
        """Normalize data to range [0,1] using min-max scaling"""
        return (data - data.min()) / (data.max() - data.min())

    def write_to_log(self, log_path, content):
        """Write content to log file with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        with open(log_path, 'a', encoding='utf-8') as f:
            f.write(f"[{timestamp}] {content}\n")

    def calculate_hardness(self):
        # Retrieve layer and field selections
        layer_name = self.layer_combo.currentText()
        layer = QgsProject.instance().mapLayersByName(layer_name)[0]
        
        # Get layer path and create log path
        layer_path = layer.source()
        log_path = layer_path.replace('.shp', '_hardness_processing.txt')
        
        # Initialize log file with header
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(f"Hardness Calculator Processing Log\n")
            f.write(f"===================================\n\n")

        # Log basic information
        self.write_to_log(log_path, f"Processing layer: {layer_name}")
        self.write_to_log(log_path, f"Layer path: {layer_path}")

        field_names = {key: combo.currentText() for key, combo in self.field_combos.items()}
        self.write_to_log(log_path, f"Selected fields:")
        for key, value in field_names.items():
            self.write_to_log(log_path, f"  {key}: {value}")

        # Extract data from layer
        data = []
        features = list(layer.getFeatures())
        total_features = len(features)
        self.write_to_log(log_path, f"\nTotal features in layer: {total_features}")

        for index, feature in enumerate(features):
            try:
                e1 = float(feature[field_names["E1"]])
                e2 = float(feature[field_names["E2"]])
                peak_sv = float(feature[field_names["PeakSV"]])
                depth = float(feature[field_names["Depth"]])

                if e1 > 0 and peak_sv > 0:
                    data.append([e1, e2, peak_sv, depth])
            except (ValueError, KeyError):
                continue

            progress = int((index + 1) / total_features * 100)
            self.progress_bar.setValue(progress)
            time.sleep(0.001)

        if not data:
            QMessageBox.warning(self, "Error", "No valid data found in the selected fields.")
            return

        df = pd.DataFrame(data, columns=["E1", "E2", "PeakSV", "Depth"])
        self.write_to_log(log_path, f"Valid features for processing: {len(df)}")

        if self.manual_mode.isChecked():
            try:
                k1 = float(self.k1_input.text())
                k2 = float(self.k2_input.text())
                k3 = float(self.k3_input.text())
                
                self.write_to_log(log_path, "\nManual Mode Selected")
                self.write_to_log(log_path, f"User defined parameters:")
                self.write_to_log(log_path, f"  k1: {k1:.4f}")
                self.write_to_log(log_path, f"  k2: {k2:.4f}")
                self.write_to_log(log_path, f"  k3: {k3:.4f}")
                
            except ValueError:
                QMessageBox.warning(self, "Error", "Please enter valid numeric values for k1, k2, and k3.")
                return

        elif self.optimized_mode.isChecked():
            try:
                self.write_to_log(log_path, "\nOptimized Mode Selected")
                
                lower_percentile = float(self.percentile_lower_input.text()) / 100
                upper_percentile = float(self.percentile_upper_input.text()) / 100
                
                self.write_to_log(log_path, f"Percentile settings:")
                self.write_to_log(log_path, f"  Lower: {lower_percentile*100}%")
                self.write_to_log(log_path, f"  Upper: {upper_percentile*100}%")

                if not (0 <= lower_percentile < upper_percentile <= 1):
                    QMessageBox.warning(self, "Error", "Percentiles must be between 0 and 100, with lower < upper.")
                    return

                # Remove outliers
                Q_low = df.quantile(lower_percentile)
                Q_high = df.quantile(upper_percentile)
                df_filtered = df[(df >= Q_low) & (df <= Q_high)].dropna()
                
                self.write_to_log(log_path, f"\nData points after outlier removal: {len(df_filtered)}")
                self.write_to_log(log_path, f"Outliers removed: {len(df) - len(df_filtered)}")

                # Correlation matrix
                correlation_matrix = df_filtered[['E1', 'E2', 'PeakSV', 'Depth']].corr()
                self.write_to_log(log_path, f"\nCorrelation Matrix:")
                self.write_to_log(log_path, f"{correlation_matrix.round(3).to_string()}")

                # Prepare data for regression
                df_filtered["E1_div_E2"] = df_filtered["E1"] / df_filtered["E2"]

                # Normalize variables for regression only
                X_e1 = self.normalize_data(df_filtered["E1"])
                X_div = self.normalize_data(df_filtered["E1_div_E2"]).fillna(0)
                X_peak = self.normalize_data(df_filtered["PeakSV"])
                y_normalized = self.normalize_data(df_filtered["Depth"])

                X_normalized = pd.concat([X_e1, X_div, X_peak], axis=1).to_numpy()

                # Unbounded regression
                reg = LinearRegression()
                reg.fit(X_normalized, y_normalized)
                unbounded_k1, unbounded_k2, unbounded_k3 = reg.coef_
                
                self.write_to_log(log_path, f"\nUnbounded Regression Results:")
                self.write_to_log(log_path, f"  k1: {unbounded_k1:.4f}")
                self.write_to_log(log_path, f"  k2: {unbounded_k2:.4f}")
                self.write_to_log(log_path, f"  k3: {unbounded_k3:.4f}")
                self.write_to_log(log_path, f"  Intercept: {reg.intercept_:.4f}")

                # Bounded regression
                bounds_low = [0.5, 0.3, 0.2]
                bounds_high = [1.0, 0.7, 0.5]
                result = lsq_linear(X_normalized, y_normalized, bounds=(bounds_low, bounds_high))
                k1, k2, k3 = result.x
                
                self.write_to_log(log_path, f"\nBounded Regression Results (Final Parameters):")
                self.write_to_log(log_path, f"  k1: {k1:.4f}")
                self.write_to_log(log_path, f"  k2: {k2:.4f}")
                self.write_to_log(log_path, f"  k3: {k3:.4f}")

            except Exception as e:
                QMessageBox.warning(self, "Error", f"An error occurred during regression: {e}")
                return

        # Write results back to the layer
        with edit(layer):
            existing_fields = [field.name() for field in layer.fields()]
            hardness_field_name = "Hardness"
            confidence_field_name = "Confidence"

            counter = 1
            while hardness_field_name in existing_fields:
                hardness_field_name = f"Hardness_{counter}"
                counter += 1

            counter = 1
            while confidence_field_name in existing_fields:
                confidence_field_name = f"Confidence_{counter}"
                counter += 1

            self.write_to_log(log_path, f"\nCreated fields:")
            self.write_to_log(log_path, f"  Hardness field: {hardness_field_name}")
            self.write_to_log(log_path, f"  Confidence field: {confidence_field_name}")

            # Adiciona os novos campos
            layer.dataProvider().addAttributes([
                QgsField(hardness_field_name, QVariant.Double),
                QgsField(confidence_field_name, QVariant.String),
            ])
            layer.updateFields()

            # Obtém os índices dos campos
            hardness_idx = layer.fields().indexOf(hardness_field_name)
            confidence_idx = layer.fields().indexOf(confidence_field_name)

            # Dicionário para armazenar todas as mudanças
            changes_dict = {}
            
            # Prepara a barra de progresso para a fase de cálculo
            total_features = layer.featureCount()
            self.write_to_log(log_path, f"\nStarting hardness calculation for {total_features} features")
            
            # Contador para atualização da barra de progresso
            feature_count = 0
            update_interval = max(1, min(1000, total_features // 100))  # Atualiza a cada 1% ou 1000 features

            for feature in layer.getFeatures():
                try:
                    # Use valores originais (não normalizados) da tabela
                    e1 = float(feature[field_names["E1"]])
                    e2 = float(feature[field_names["E2"]])
                    peak_sv = float(feature[field_names["PeakSV"]])

                    if e1 > 0 and peak_sv > 0:
                        if e2 > 0:
                            # Cálculo com valores originais
                            hardness = k1 * e1 + k2 * (e1 / e2) + k3 * peak_sv
                            confidence = "High"
                        else:
                            # Fórmula simplificada com valores originais
                            hardness = k1 * e1 + k3 * peak_sv
                            confidence = "Low"
                    else:
                        hardness = None
                        confidence = None

                    # Armazena as mudanças no dicionário
                    changes_dict[feature.id()] = {
                        hardness_idx: hardness,
                        confidence_idx: confidence
                    }

                    # Atualiza o progresso periodicamente
                    feature_count += 1
                    if feature_count % update_interval == 0:
                        progress = (feature_count / total_features) * 100
                        self.progress_bar.setValue(int(progress))
                        self.write_to_log(log_path, f"Progress: {progress:.1f}% ({feature_count}/{total_features} features)")

                except (ValueError, KeyError) as e:
                    self.write_to_log(log_path, f"Warning: Error processing feature {feature.id()}: {str(e)}")
                    continue

            # Aplica todas as mudanças de uma vez
            self.write_to_log(log_path, "\nApplying changes to layer...")
            success = layer.dataProvider().changeAttributeValues(changes_dict)
            
            if not success:
                self.write_to_log(log_path, "Warning: Some changes might not have been applied successfully")
                QMessageBox.warning(self, "Warning", "Some changes might not have been applied successfully")
            else:
                self.write_to_log(log_path, "All changes applied successfully")

        self.result_field.setText(f"k1: {k1:.4f}, k2: {k2:.4f}, k3: {k3:.4f}")
        QMessageBox.information(self, "Success", "Hardness calculation completed and updated in the layer.")
        self.write_to_log(log_path, "\nProcessing completed successfully.")
        
        self.progress_bar.setValue(100)