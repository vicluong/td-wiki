import maya.cmds as cmds
import mayaUsd.lib as mayaUsdLib
import os

def getFirstStage():
    for base_prim in cmds.ls(type = "mayaUsdProxyShapeBase"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()

        return stage

def getAllStages():
    stages = []

    for base_prim in cmds.ls(type = "mayaUsdProxyShapeBase"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        stages.append(stage)

    return stages

# -------------------------------------------------------------

def isReferenceMissing(refs):
    for ref in refs.GetAppliedItems():
        path = cmds.workspace(q=True, rd=True) + "Kitchen_set" + ref.assetPath[1:]

        return not os.path.isfile(path)

def checkMissingReferences():
    stage = getFirstStage()
    stage.Reload()

    missing_refs = []

    for prim in stage.Traverse():
        refs = prim.GetMetadata("references")
        if refs:
            missing = isReferenceMissing(refs)
            if missing:
                missing_refs.append(prim.GetPath())

    return missing_refs

# -------------------------------------------------------------

def clearReferences(prim_path):
    stage = getFirstStage()
    root = stage.GetRootLayer()
    stage.SetEditTarget(root)

    prim = stage.GetPrimAtPath(prim_path)
    refs = prim.GetReferences()
    refs.ClearReferences()

def addReference(prim_path, file_path):
    stage = getFirstStage()
    root = stage.GetRootLayer()
    stage.SetEditTarget(root)

    prim = stage.GetPrimAtPath(prim_path)
    refs = prim.GetReferences()
    refs.AddReference(file_path)

# -------------------------------------------------------------

"""Creates a UI 

"""
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


class CheckReferencesDialog(QtWidgets.QDialog):
    FILE_FILTERS = "All Image Files (*.usd *.usda);;All Files (*.*)"
    selected_filter = "All Image Files (*.usd *.usda)"

    dlg_instance = None
    
    @classmethod
    def show_dialog(cls):
        if not cls.dlg_instance:
            cls.dlg_instance = CheckReferencesDialog()
            
        if cls.dlg_instance.isHidden():
            cls.dlg_instance.show()
        else:
            cls.dlg_instance.raise_()
            cls.dlg_instance.activateWindow()

    def __init__(self, parent=maya_main_window()):
        """Initialise CheckReferencesDialog"""
        super(CheckReferencesDialog, self).__init__(parent)

        self.setWindowTitle("Check Missing References")

        size = maya_main_window().screen().size()
        screen_w, screen_h = size.width(), size.height()
        self.resize(int(screen_w * 0.19), int(screen_h * 0.5))

        self.thumbnail_height = int(screen_w * 0.044)
        self.input_width = int(screen_w * 0.035)
        self.checkbox_margin = int(screen_w * 0.004)
        
        # On macOS make the window a Tool to keep it on top of Maya
        if sys.platform == "darwin":
            self.setWindowFlag(QtCore.Qt.Tool, True)

        self.problems_list = []

        self.create_widgets()
        self.create_layout()
        self.create_connections()

    def create_widgets(self):
        """Create all widgets for the UI"""
        self.check_btn = QtWidgets.QPushButton("Check Missing References")

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)

        self.problems_table = QtWidgets.QTableWidget(0, 4)
        self.problems_table.setHorizontalHeaderLabels(["Problem Prim", "Reference Path", "Change", "Confirm"])
        self.problems_table.resizeColumnsToContents()
        
        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        check_layout = QtWidgets.QHBoxLayout()
        check_layout.addWidget(self.check_btn)

        problems_form_layout = QtWidgets.QVBoxLayout()
        problems_form_layout.addWidget(self.problems_table)
        problems_grp = QtWidgets.QGroupBox("Problem Prims")
        problems_grp.setLayout(problems_form_layout)

        self.splitter.addWidget(problems_grp)

        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addLayout(check_layout)
        main_layout.addWidget(self.splitter)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        """Create all connections for the UI"""
        self.check_btn.clicked.connect(self.get_missing_references)
        self.close_btn.clicked.connect(self.close)

    def get_missing_references(self):
        missing_refs = checkMissingReferences()

        # Setup problems table
        for ref in missing_refs:
            index = self.problems_table.rowCount()
            self.problems_table.setRowCount(index + 1)

            # Problem Prim
            problem_prim_le = QtWidgets.QLabel()
            problem_prim_le.setText(str(ref))
            self.problems_table.setCellWidget(index, 0, problem_prim_le)

            # Reference Path
            file_path_le = QtWidgets.QLineEdit()
            file_path_le.setReadOnly(True)
            self.problems_table.setCellWidget(index, 1, file_path_le)

            # Folder Button
            folder_btn = QtWidgets.QPushButton()
            folder_btn.setIcon(QtGui.QIcon(":addClip.png"))
            self.problems_table.setCellWidget(index, 2, folder_btn)
            folder_btn.clicked.connect(
                partial(self.show_file_select_dialog, file_path_le)
            )

            # Apply Button
            apply_btn = QtWidgets.QPushButton()
            apply_btn.setIcon(QtGui.QIcon(":trash.png"))
            self.problems_table.setCellWidget(index, 3, apply_btn)
            apply_btn.clicked.connect(
                partial(self.fix_ref_path, ref, file_path_le)
            )

    def fix_ref_path(self, prim_path, widget):
        file_path = widget.text()
        clearReferences(prim_path)
        addReference(prim_path, file_path)

    def show_file_select_dialog(self, widget):
        """Create the dialog for file selection"""
        file_path = widget.text()

        if not file_path:
            file_path = cmds.workspace(rootDirectory=True, q=True) + "/sourceimages"
            
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", file_path, self.FILE_FILTERS, self.selected_filter)
        if file_path:
            widget.setText(file_path)

if __name__ == "__main__":
    CheckReferencesDialog.show_dialog()
