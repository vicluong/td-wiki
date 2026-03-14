from logging import root

import maya.cmds as cmds
import mayaUsd.lib as mayaUsdLib
import os

def getAllStages():
    stages = []

    for base_prim in cmds.ls(type = "mayaUsdProxyShapeBase"):
        stage = mayaUsdLib.GetPrim(base_prim).GetStage()
        stages.append(stage)

    return stages

def get_proxy_shape_for_stage(stage):
    for proxy in cmds.ls(type="mayaUsdProxyShape"):
        proxy_stage = mayaUsdLib.GetPrim(proxy).GetStage()
        if proxy_stage.GetRootLayer().identifier == stage.GetRootLayer().identifier:
            return proxy
    return None

def get_stage_transform(stage):
    proxy = get_proxy_shape_for_stage(stage)
    if not proxy:
        return None
    parents = cmds.listRelatives(proxy, parent=True)
    return parents[0] if parents else None

# -------------------------------------------------------------

def is_reference_missing(refs, main_path):
    missing = []

    for ref in refs.GetAppliedItems():
        if ref.assetPath[0] == ".":
            path = main_path + ref.assetPath[1:]
        else:
            path = ref.assetPath

        if not os.path.isfile(path):
            missing.append(path)

    return missing

def get_missing_references(main_path):
    stages = getAllStages()
    if stages:
        all_missing_refs = {}
        for stage in stages:
            stage.Reload()

            prims_with_missing_references = {}

            for prim in stage.Traverse():
                refs = prim.GetMetadata("references")
                if refs:
                    missing = is_reference_missing(refs, main_path)
                    if missing:
                        prims_with_missing_references[prim.GetPath()] = missing
            all_missing_refs[stage] = prims_with_missing_references

        return all_missing_refs 
    
    else:
        print("No USD stage found in the current scene.")

        return {}

# -------------------------------------------------------------

def clear_references(stage, prim_path, missing_ref_path):
    root = stage.GetRootLayer()
    stage.SetEditTarget(root)

    prim = stage.GetPrimAtPath(prim_path)
    refs = prim.GetMetadata("references")
    other_ref_paths = []

    for ref in refs.GetAppliedItems():
        if not missing_ref_path.endswith(ref.assetPath[1:]):
            other_ref_paths.append(ref.assetPath)

    refs_to_clear = prim.GetReferences()
    refs_to_clear.ClearReferences()

    return other_ref_paths 

def add_reference(stage, prim_path, main_folder_path, correct_ref_path, other_ref_paths, seek_relative_path=True):
    root = stage.GetRootLayer()
    stage.SetEditTarget(root)

    prim = stage.GetPrimAtPath(prim_path)
    refs = prim.GetReferences()

    if seek_relative_path and correct_ref_path.startswith(main_folder_path):
        relative_path = "./" + os.path.relpath(correct_ref_path, main_folder_path).replace("\\", "/")
        refs.AddReference(relative_path)
    else:
        refs.AddReference(correct_ref_path)

    for ref_path in other_ref_paths:
        refs.AddReference(ref_path)

    root.Save()
    stage.Reload()

# -------------------------------------------------------------

def auto_find_reference(main_path, main_file_name):
    # Gets all files in main_path andsubfolders and returns the latest file that ends with file_name
    latest_file = None

    for dir_path, dir_names, file_names in os.walk(main_path):
        for file_name in file_names:
            file_path = os.path.join(dir_path, file_name).replace("\\", "/")
            if (file_path.split("/")[-1] == main_file_name.split("/")[-1] 
                and (not latest_file or os.path.getmtime(file_path) > os.path.getmtime(latest_file))):
                latest_file = file_path
            
    return latest_file
            
def auto_find_latest_reference(main_path, main_file_name):
    # Gets file_name and gets file with latest version number separated by a v or a _
    root, ext = os.path.splitext(main_file_name)

    latest_file = None
    latest_version = 0

    for dir_path, dir_names, file_names in os.walk(main_path):
        for file_name in file_names:
            root, ext = os.path.splitext(file_name)

            version = root.rsplit("v", 1)[-1]
            if version.isdigit():
                version = int(version)
                if version > latest_version:
                    latest_file = os.path.join(dir_path, file_name)

            version = root.rsplit("_", 1)[-1]
            if version.isdigit(): 
                version = int(version)
                if version > latest_version:
                    latest_file = os.path.join(dir_path, file_name)

    return latest_file


# --------------------------VARIANTS---------------------------

def get_missing_variants():
    stages = getAllStages()
    if stages:
        all_missing_variants = {}
        for stage in stages:
            stage.Reload()

            for prim in stage.Traverse():
                prims_with_missing_references = {}

                vsets = prim.GetVariantSets()

                if "modelingVariant" in vsets.GetNames():
                    vset = vsets.GetVariantSet("modelingVariant")
                    
                    # Get current selection
                    current_variant = vset.GetVariantSelection()
                    all_variants = vset.GetVariantNames()

                    if current_variant not in all_variants:
                        prims_with_missing_references[prim.GetPath()] = vset
            all_missing_variants[stage] = prims_with_missing_references

        return all_missing_variants

    else:
        print("No USD stage found in the current scene.")

        return {}

# -------------------------------------------------------------


""" Creates a UI 

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
    FILE_FILTERS = "All Image Files (*.usd *.usda, *.usdc);;All Files (*.*)"
    selected_filter = "All Image Files (*.usd *.usda, *.usdc)"

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
        self.resize(int(screen_w * 0.65), int(screen_h * 0.5))
        
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
        self.check_refs_btn = QtWidgets.QPushButton("Check Missing References")
        self.check_variants_btn = QtWidgets.QPushButton("Check Missing Variants")

        self.main_ref_dir_le = QtWidgets.QLineEdit()
        workspace_root = cmds.workspace(q=True, rootDirectory=True)
        self.main_ref_dir_le.setText(workspace_root if workspace_root else "")
        self.main_ref_dir_le.setReadOnly(True)
        self.main_ref_dir_btn = QtWidgets.QPushButton()

        self.create_relative_path_checkbox = QtWidgets.QCheckBox()
        self.create_relative_path_checkbox.setChecked(True)
        self.auto_find_refs_checker = QtWidgets.QCheckBox()

        self.main_variant_dir_le = QtWidgets.QLineEdit()
        workspace_root = cmds.workspace(q=True, rootDirectory=True)
        self.main_variant_dir_le.setText(workspace_root if workspace_root else "")
        self.main_variant_dir_le.setReadOnly(True)
        self.main_variant_dir_btn = QtWidgets.QPushButton()

        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self.splitter.setChildrenCollapsible(False)

        self.problems_table = QtWidgets.QTableWidget(0, 6)
        self.problems_table.setHorizontalHeaderLabels(["Stage", "Problem Prim", "Bad Reference", "Reference Path", "Change", "Confirm"])
        self.problems_table.resizeColumnsToContents()

        self.variants_table = QtWidgets.QTableWidget(0, 4)
        self.variants_table.setHorizontalHeaderLabels(["Stage", "Problem Prim", "Variants", "Confirm"])
        self.variants_table.resizeColumnsToContents()

        self.close_btn = QtWidgets.QPushButton("Close")

    def create_layout(self):
        """Create all layouts and add widgets to them"""
        # Create tab widget
        self.tab_widget = QtWidgets.QTabWidget()

        # Tab 1: References
        references_tab = QtWidgets.QWidget()
        references_layout = QtWidgets.QVBoxLayout(references_tab)

        check_ref_layout = QtWidgets.QHBoxLayout()
        check_ref_layout.addWidget(self.check_refs_btn)
        references_layout.addLayout(check_ref_layout)

        main_ref_folder_layout = QtWidgets.QHBoxLayout()
        main_ref_folder_layout.addWidget(self.main_ref_dir_le)
        main_ref_folder_layout.addWidget(self.main_ref_dir_btn)
        references_layout.addLayout(main_ref_folder_layout)

        auto_refs_checker = QtWidgets.QVBoxLayout()
        auto_refs_checker.addWidget(self.auto_find_refs_checker)
        create_relative_path_layout = QtWidgets.QVBoxLayout()
        create_relative_path_layout.addWidget(self.create_relative_path_checkbox)

        form_ref_options_layout = QtWidgets.QFormLayout()
        form_ref_options_layout.addRow("Create Relative Paths When Possible:", create_relative_path_layout)
        form_ref_options_layout.addRow("Auto-Find Missing References If Possible:", auto_refs_checker)

        references_layout.addLayout(form_ref_options_layout)

        problems_table_layout = QtWidgets.QVBoxLayout()
        problems_table_layout.addWidget(self.problems_table)
        references_layout.addLayout(problems_table_layout)

        self.tab_widget.addTab(references_tab, "References")

        # Tab 2: Variants
        variants_tab = QtWidgets.QWidget()
        variants_layout = QtWidgets.QVBoxLayout(variants_tab)

        check_variant_layout = QtWidgets.QHBoxLayout()
        check_variant_layout.addWidget(self.check_variants_btn)
        variants_layout.addLayout(check_variant_layout)

        main_variant_folder_layout = QtWidgets.QHBoxLayout()
        main_variant_folder_layout.addWidget(self.main_variant_dir_le)
        main_variant_folder_layout.addWidget(self.main_variant_dir_btn)
        variants_layout.addLayout(main_variant_folder_layout)

        variants_table_layout = QtWidgets.QVBoxLayout()
        variants_table_layout.addWidget(self.variants_table)
        variants_layout.addLayout(variants_table_layout)

        self.tab_widget.addTab(variants_tab, "Variants")

        # Bottom Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.tab_widget)
        main_layout.addLayout(button_layout)

    def create_connections(self):
        """Create all connections for the UI"""
        self.main_ref_dir_btn.clicked.connect(
            partial(self.show_main_folder_select_dialog, self.main_ref_dir_le)
        )
        self.main_variant_dir_btn.clicked.connect(
            partial(self.show_main_folder_select_dialog, self.main_variant_dir_le)
        )
        self.check_refs_btn.clicked.connect(self.create_references_table)
        self.check_variants_btn.clicked.connect(self.create_variants_table)
        self.close_btn.clicked.connect(self.close)

    def create_references_table(self):
        self.main_folder_path = self.main_ref_dir_le.text()
        if self.main_folder_path and os.path.isdir(self.main_folder_path):
            self.missing_refs = get_missing_references(self.main_folder_path)

            self.problems_table.setRowCount(0)

            # Setup problems table
            for stage in self.missing_refs:
                for prim_path in self.missing_refs[stage]:
                    for missing_ref in self.missing_refs[stage][prim_path]:
                        index = self.problems_table.rowCount()
                        self.problems_table.setRowCount(index + 1)

                        # Stage
                        stage_le = QtWidgets.QLabel()
                        stage_le.setText(get_stage_transform(stage)) 
                        self.problems_table.setCellWidget(index, 0, stage_le)

                        # Problem Prim
                        problem_prim_le = QtWidgets.QLabel()
                        problem_prim_le.setText(str(prim_path))
                        self.problems_table.setCellWidget(index, 1, problem_prim_le)

                        # Bad Reference
                        bad_ref_le = QtWidgets.QLabel()
                        bad_ref_le.setText(str(missing_ref))
                        self.problems_table.setCellWidget(index, 2, bad_ref_le)

                        # Reference Path
                        ref_path_le = QtWidgets.QLineEdit()
                        if self.auto_find_refs_checker.isChecked():
                            ref_path_le.setText(auto_find_reference(self.main_folder_path, missing_ref))
                        ref_path_le.setReadOnly(True)
                        self.problems_table.setCellWidget(index, 3, ref_path_le)

                        # Folder Button
                        folder_btn = QtWidgets.QPushButton()
                        folder_btn.setIcon(QtGui.QIcon(":addClip.png"))
                        self.problems_table.setCellWidget(index, 4, folder_btn)
                        folder_btn.clicked.connect(
                            partial(self.show_file_select_dialog, ref_path_le)
                        )

                        # Apply Button
                        apply_btn = QtWidgets.QPushButton()
                        apply_btn.setIcon(QtGui.QIcon(":trash.png"))
                        self.problems_table.setCellWidget(index, 5, apply_btn)
                        apply_btn.clicked.connect(
                            partial(self.fix_ref_path, stage, prim_path, missing_ref, ref_path_le)
                        )

            # self.problems_table.cellClicked.connect(partial(self.select_prim_in_viewport))
            self.problems_table.resizeColumnsToContents()
        else:
            print("Please select a valid main folder.")

    def fix_ref_path(self, stage, prim_path, missing_ref, widget):
        file_path = widget.text()
        if not file_path or not os.path.isfile(file_path):
            print("Please select a valid file before confirming.")
        elif self.main_folder_path != self.main_ref_dir_le.text():
            print("Main folder path has changed. Please check missing references again.")
        else:
            # clearReferences(stage, prim_path)
            other_ref_paths = clear_references(stage, prim_path, missing_ref)
            add_reference(stage, prim_path, self.main_folder_path, file_path, other_ref_paths, self.create_relative_path_checkbox.isChecked())
            self.create_references_table()

    def create_variants_table(self):
        self.main_folder_path = self.main_variant_dir_le.text()
        if self.main_folder_path and os.path.isdir(self.main_folder_path):
            self.missing_variants = get_missing_variants()

            self.variants_table.setRowCount(0)

            # Setup variants table
            for stage in self.missing_variants:
                for prim_path in self.missing_variants[stage]:
                    vset = self.missing_variants[stage][prim_path]
                    index = self.variants_table.rowCount()
                    self.variants_table.setRowCount(index + 1)

                    # Stage
                    stage_le = QtWidgets.QLabel()
                    stage_le.setText(get_stage_transform(stage)) 
                    self.variants_table.setCellWidget(index, 0, stage_le)

                    # Problem Prim
                    problem_prim_le = QtWidgets.QLabel()
                    problem_prim_le.setText(str(prim_path))
                    self.variants_table.setCellWidget(index, 1, problem_prim_le)

                    # Variant Set
                    vset_combo = QtWidgets.QComboBox()
                    vset_combo.addItems(vset.GetVariantNames())
                    self.variants_table.setCellWidget(index, 2, vset_combo)

                    # Apply Button
                    apply_btn = QtWidgets.QPushButton()
                    apply_btn.setIcon(QtGui.QIcon(":trash.png"))
                    self.variants_table.setCellWidget(index, 3, apply_btn)
                    apply_btn.clicked.connect(
                        partial(self.set_new_variant, stage, vset, vset_combo)
                    )

            # self.variants_table.cellClicked.connect(partial(self.select_prim_in_viewport))
            self.variants_table.resizeColumnsToContents()
        else:
            print("Please select a valid main folder.")

    def set_new_variant(self, stage, vset, widget):
        if self.main_folder_path != self.main_ref_dir_le.text():
            print("Main folder path has changed. Please check missing references again.")
        else:
            variant_name = widget.currentText()

            root = stage.GetRootLayer()
            stage.SetEditTarget(root)
            vset.SetVariantSelection(variant_name)

            root.Save()
            stage.Reload()

            self.create_variants_table()

    # def select_prim_in_viewport(self, row, column):
    #     prim_path = self.problems_table.cellWidget(row, column).text()
    #     proxies = cmds.ls(type="mayaUsdProxyShape")
    #     if proxies:
    #         proxy = proxies[0]
    #         transform = cmds.listRelatives(proxy, parent=True)[0]
    #         cmds.select(f"|{transform}|{proxy},{prim_path}")

    def show_main_folder_select_dialog(self, widget):
        """Create the dialog for file selection"""
        file_path = widget.text()
            
        file_path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Folder")
        if file_path and os.path.isdir(file_path):
            widget.setText(file_path)

    def show_file_select_dialog(self, widget):
        """Create the dialog for file selection"""
        file_path = widget.text()
            
        file_path, self.selected_filter = QtWidgets.QFileDialog.getOpenFileName(self, "Select File", file_path, self.FILE_FILTERS, self.selected_filter)
        if file_path and os.path.isfile(file_path):
            widget.setText(file_path)

if __name__ == "__main__":
    CheckReferencesDialog.show_dialog()
