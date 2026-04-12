import maya.cmds as cmds
import os
from pathlib import Path

main_folder_path = Path("F:\ALA Projects\Pixie Dust\Main Folder")

try:
    from PySide6 import QtCore
    from PySide6 import QtGui
    from PySide6 import QtWidgets
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore
    from PySide2 import QtGui
    from PySide2 import QtWidgets
    from shiboken2 import wrapInstance

import os
import sys
from functools import partial

import maya.OpenMaya as om
import maya.OpenMayaUI as omui
import maya.cmds as cmds


def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class PixieDustDialog(QtWidgets.QDialog):
    FILE_FILTERS = "All Image Files (*.usd *.usda, *.usdc);;All Files (*.*)"
    selected_filter = "All Image Files (*.usd *.usda, *.usdc)"

    dlg_instance = None
    
    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = PixieDustDialog()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        """Initialise PixieDustDialog"""
        super(PixieDustDialog, self).__init__(parent)

        self.setWindowTitle("Check Missing References")

        size = maya_main_window().screen().size()
        screen_w, screen_h = size.width(), size.height()
        self.resize(int(screen_w * 0.3), int(screen_h * 0.5))
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)

        self.missing_refs = {}
        self.missing_variants = {}

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create all widgets for the UI"""
        self.type_dropdown = QtWidgets.QComboBox()
        self.entity_type_dropdown = QtWidgets.QComboBox()

        type_folders = [f for f in main_folder_path.iterdir() if f.is_dir()]
        for folder in type_folders:
            self.type_dropdown.addItems([folder.name])

        current_type_folder = main_folder_path / self.type_dropdown.currentText()

        entity_type_folders = [f for f in current_type_folder.iterdir() if f.is_dir()]
        for folder in entity_type_folders:
            self.entity_type_dropdown.addItems([folder.name])

        self.entity_name_dropdown = QtWidgets.QComboBox()
        self.entity_name_dropdown.addItems(["Cat", "Dog", "Option 3"])

        self.get_dropdown()

        self.entity_table = QtWidgets.QTableWidget(0, 2)
        self.entity_table.setHorizontalHeaderLabels(["Type", "Date"])
        self.entity_table.resizeColumnsToContents()

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        dropdown_layout = QtWidgets.QVBoxLayout()
        dropdown_layout.addWidget(self.type_dropdown)
        dropdown_layout.addWidget(self.entity_type_dropdown)
        dropdown_layout.addWidget(self.entity_name_dropdown)

        selection_layout = QtWidgets.QVBoxLayout()
        selection_layout.addWidget(self.entity_table)

        main_layout = QtWidgets.QHBoxLayout(self)
        main_layout.addLayout(dropdown_layout)
        main_layout.addStretch()
        main_layout.addLayout(selection_layout)

    def create_connections(self):
        """Create all connections for the UI"""
        self.type_dropdown.activated.connect(self.get_dropdown)

    def get_dropdown(self):
        print("Test")


if __name__ == "__main__":
    PixieDustDialog.show_dialog()
