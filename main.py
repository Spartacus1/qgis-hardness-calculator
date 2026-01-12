from qgis.PyQt.QtWidgets import QAction, QMenu, QMessageBox
from qgis.core import QgsVectorLayer, QgsWkbTypes
from .hardness import HardnessDialog

class HardnessPlugin:
    def __init__(self, iface):
        self.iface = iface
        self.action = None

    def initGui(self):
        self.action = QAction("Hardness Calculator", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("&Hardness Calculator", self.action)

    def unload(self):
        self.iface.removePluginMenu("&Hardness Calculator", self.action)
        # Note: we are not adding a toolbar icon, so no need to remove it here.

    def run(self):
        layer = self.iface.activeLayer()

        # 1) No active layer or not a vector layer
        if not isinstance(layer, QgsVectorLayer):
            QMessageBox.information(
                self.iface.mainWindow(),
                "Hardness Calculator",
                "Please select a POINT vector layer first."
            )
            return

        # 2) Vector layer exists but is not a point layer
        if layer.geometryType() != QgsWkbTypes.PointGeometry:
            QMessageBox.information(
                self.iface.mainWindow(),
                "Hardness Calculator",
                "This plugin requires a POINT vector layer. Please select a point layer and try again."
            )
            return

        # 3) Everything is OK → open the dialog
        dialog = HardnessDialog(self.iface)
        dialog.exec_()