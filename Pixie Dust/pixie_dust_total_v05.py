from pathlib import Path
import json

main_folder_path = Path("F:\ALA Projects\Pixie Dust\sheeping_beauty\\03_production")
assignment_data_path = Path("F:\ALA Projects\Pixie Dust\\assignment.json")
test_path = Path("F:\ALA Projects\Pixie Dust\\test.json")

try:
    from PySide6 import QtCore
    from PySide6 import QtWidgets
    from PySide6 import QtGui
    from shiboken6 import wrapInstance
except:
    from PySide2 import QtCore
    from PySide2 import QtWidgets
    from PySide2 import QtGui
    from shiboken2 import wrapInstance

from functools import partial

import maya.OpenMayaUI as omui

import sys
sys.path.append("F:\ALA Projects\Pixie Dust\code")
import helper_functions

def maya_main_window():
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)

class PixieDustDialog(QtWidgets.QDialog):
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

        self.create_widgets()
        self.create_layout()
        self.create_connections()

        self.switch_creation_type(0)
        self.show_asset_assignment_table(1)
        self.show_tasks_table()

    def get_assignment_data(self):
        with open(str(assignment_data_path), 'r') as file:
            assignment_data = json.load(file)

        return assignment_data

    def create_widgets(self):
        """Create all widgets for the UI"""
        assignment_data = self.get_assignment_data()

        # Tab 1: Creation
        self.creation_type_dropdown = QtWidgets.QComboBox()
        self.creation_type_dropdown.addItems(["Asset", "Sequence/Shot"])

            # Asset
        self.create_asset_dropdown = QtWidgets.QComboBox()
        self.create_asset_dropdown.addItems(["camera", "character", "charfx", "fx", "prop", "set", "setPiece"])
        self.create_asset_le = QtWidgets.QLineEdit()
        self.create_asset_btn = QtWidgets.QPushButton("Create Asset")

            # Sequence
        self.create_sequence_le = QtWidgets.QLineEdit()
        self.create_sequence_btn = QtWidgets.QPushButton("Create Sequence")

            # Shot
        self.create_shot_dropdown = QtWidgets.QComboBox()
        self.create_shot_le = QtWidgets.QLineEdit()
        self.create_shot_btn = QtWidgets.QPushButton("Create Shot")

        self.creation_table = QtWidgets.QTableWidget()

        # Tab 2: Assignment
        self.assignment_type_dropdown = QtWidgets.QComboBox()
        self.assignment_type_dropdown.addItems(["Asset", "Sequence/Shot"])

        self.users_list = QtWidgets.QListWidget()
        self.users_list.addItems(assignment_data["users"])

        self.assignment_btn = QtWidgets.QPushButton("Assign")

        self.assignment_table = QtWidgets.QTableWidget()

        # Tab 3: Assignment
        """
        self.tasks_tree = QtWidgets.QTreeWidget()
        self.tasks_tree.setHeaderLabels(["Main Type", "Asset Type", "Asset Name", "Asset Part", "Current WIP Version", "Published Version"])
        main_type_tree_item = QtWidgets.QTreeWidgetItem()
        main_type_tree_item.setText(0, "Asset")
        main_type_tree_item2 = QtWidgets.QTreeWidgetItem()
        main_type_tree_item2.setText(0, "Asset2")
        main_type_tree_item.addChild(main_type_tree_item2)
        self.tasks_tree.addTopLevelItems([main_type_tree_item, main_type_tree_item2])
        """

        # self.tasks_cards = QtWidgets.QListView()
        # self.tasks_cards.setViewMode(QtWidgets.QListView.ViewMode.IconMode)
        # model = QtGui.QStandardItemModel()
        # item = QtGui.QStandardItem("New Item Text")
        # model.appendRow(item)
        # self.tasks_cards.setModel(model)

        self.assignee_tasks_le = QtWidgets.QLineEdit()

        self.get_tasks_btn = QtWidgets.QPushButton("Get Tasks")
        self.new_file_btn = QtWidgets.QPushButton("New File")
        self.open_file_btn = QtWidgets.QPushButton("Open File")

        # Tab 5: Generate Info
        self.generate_btn = QtWidgets.QPushButton("Generate")

    def create_layout(self):
        """Create all layouts and add widgets to them"""

        # Create tab widget
        self.main_tab_widget = QtWidgets.QTabWidget()

        # Tab 1: Creation
        creation_tab = QtWidgets.QWidget()
        creation_layout = QtWidgets.QHBoxLayout(creation_tab)

        creation_menu_layout = QtWidgets.QVBoxLayout()

        creation_table_layout = QtWidgets.QVBoxLayout()
        creation_table_layout.addWidget(self.creation_table)

        creation_layout.addLayout(creation_menu_layout)
        creation_layout.addLayout(creation_table_layout)

        creation_type__form_layout = QtWidgets.QFormLayout()
        creation_type__form_layout.addRow("Create:", self.creation_type_dropdown)
        creation_menu_layout.addLayout(creation_type__form_layout)

            # Asset Layout
        self.creation_asset_widget = QtWidgets.QWidget()
        creation_asset_layout = QtWidgets.QVBoxLayout()

        creation_asset_form_layout = QtWidgets.QFormLayout()
        creation_asset_form_layout.addRow("Asset Type:", self.create_asset_dropdown)
        creation_asset_form_layout.addRow("Asset Name:", self.create_asset_le)
        creation_asset_layout.addLayout(creation_asset_form_layout)

        creation_asset_layout.addWidget(self.create_asset_btn)

        creation_asset_layout.addStretch()
        self.creation_asset_widget.setLayout(creation_asset_layout)
        creation_menu_layout.addWidget(self.creation_asset_widget)

            # Shot / Sequence Layout
        self.creation_shot_sequence_widget = QtWidgets.QWidget()
        self.creation_shot_sequence_layout = QtWidgets.QVBoxLayout()
        self.creation_shot_sequence_widget.setLayout(self.creation_shot_sequence_layout)

            # Sequence Layout
        creation_sequence_group = QtWidgets.QGroupBox("Sequence")
        creation_sequence_layout = QtWidgets.QVBoxLayout()

        creation_sequence_form_layout = QtWidgets.QFormLayout()
        creation_sequence_form_layout.addRow("Sequence Name:", self.create_sequence_le)

        creation_sequence_layout.addLayout(creation_sequence_form_layout)
        creation_sequence_layout.addWidget(self.create_sequence_btn)

        creation_sequence_group.setLayout(creation_sequence_layout)

            # Shot Layout
        creation_shot_group = QtWidgets.QGroupBox("Shot")
        creation_shot_layout = QtWidgets.QVBoxLayout()

        creation_shot_form_layout = QtWidgets.QFormLayout()
        creation_shot_form_layout.addRow("Sequence:", self.create_shot_dropdown)
        creation_shot_form_layout.addRow("Shot Name:", self.create_shot_le)

        creation_shot_layout.addLayout(creation_shot_form_layout)
        creation_shot_layout.addWidget(self.create_shot_btn)

        creation_shot_group.setLayout(creation_shot_layout)

            # Add Groups
        self.creation_shot_sequence_layout.addWidget(creation_sequence_group)
        self.creation_shot_sequence_layout.addWidget(creation_shot_group)
        self.creation_shot_sequence_layout.addStretch()

        creation_menu_layout.addWidget(self.creation_shot_sequence_widget)

        self.main_tab_widget.addTab(creation_tab, "Creation")

        # Tab 2: Assignment
        assignment_tab = QtWidgets.QWidget()
        assignment_layout = QtWidgets.QHBoxLayout(assignment_tab)

        assignment_menu_layout = QtWidgets.QVBoxLayout()
        assignment_menu_layout.addWidget(self.assignment_type_dropdown)
        assignment_menu_layout.addWidget(self.users_list)
        assignment_menu_layout.addWidget(self.assignment_btn)

        assignment_table_layout = QtWidgets.QVBoxLayout()
        assignment_table_layout.addWidget(self.assignment_table)

        assignment_layout.addLayout(assignment_menu_layout, 1)
        assignment_layout.addLayout(assignment_table_layout, 5)

        self.main_tab_widget.addTab(assignment_tab, "Assignment")

        # Tab 3: Production
        production_tab = QtWidgets.QWidget()
        production_layout = QtWidgets.QVBoxLayout(production_tab)

        production_layout.addWidget(self.assignee_tasks_le)

        production_main_tab = QtWidgets.QTabWidget()
        production_tasks_tab = QtWidgets.QWidget()
        production_assets_tab = QtWidgets.QWidget()
        production_shots_tab = QtWidgets.QWidget()
        production_main_tab.addTab(production_tasks_tab, "My Tasks")
        production_main_tab.addTab(production_assets_tab, "Assets")
        production_main_tab.addTab(production_shots_tab, "Shots / Sequences")
        production_layout.addWidget(production_main_tab)

        self.production_tasks_layout = QtWidgets.QVBoxLayout(production_tasks_tab)
        # production_tasks_layout.addWidget(self.tasks_cards)
        # production_tasks_layout.addWidget(self.card1)
        # production_tasks_layout.addWidget(self.card2)

        file_creation_layout = QtWidgets.QHBoxLayout(production_tab)
        file_creation_layout.addWidget(self.get_tasks_btn)
        file_creation_layout.addWidget(self.new_file_btn)
        file_creation_layout.addWidget(self.open_file_btn)
        production_layout.addLayout(file_creation_layout)

        self.main_tab_widget.addTab(production_tab, "Production")

        # Tab 4: Save
        save_tab = QtWidgets.QWidget()
        save_layout = QtWidgets.QVBoxLayout(save_tab)

        self.main_tab_widget.addTab(save_tab, "Save")

        # Tab 4: Publish
        publish_tab = QtWidgets.QWidget()
        publish_layout = QtWidgets.QVBoxLayout(publish_tab)

        self.main_tab_widget.addTab(publish_tab, "Publish")

        # Tab 5: Import/Reference
        import_tab = QtWidgets.QWidget()
        import_layout = QtWidgets.QVBoxLayout(import_tab)

        self.main_tab_widget.addTab(import_tab, "Import/Reference")

        # Tab 6: Information
        information_tab = QtWidgets.QWidget()
        information_layout = QtWidgets.QVBoxLayout(information_tab)
        information_layout.addWidget(self.generate_btn)

        self.main_tab_widget.addTab(information_tab, "Information")
        
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.main_tab_widget)

    def create_connections(self):
        """Create all connections for the UI"""
        self.creation_type_dropdown.currentTextChanged.connect(partial(self.switch_creation_type, 0))
        self.create_asset_btn.pressed.connect(self.create_asset)
        self.create_sequence_btn.pressed.connect(self.create_sequence)
        self.create_shot_btn.pressed.connect(self.create_shot)
        self.main_tab_widget.tabBarClicked.connect(self.switch_creation_type)
        self.main_tab_widget.tabBarClicked.connect(self.show_asset_assignment_table)
        self.assignment_btn.pressed.connect(self.assign_user)
        self.get_tasks_btn.pressed.connect(self.show_tasks_table)

    def switch_creation_type(self, index):
        # To ensure the right tab is clicked
        if index != 0:
            return

        creation_type = self.creation_type_dropdown.currentText()
        self.creation_table.verticalHeader().setVisible(False)

        self.creation_asset_widget.setVisible(False)
        self.creation_shot_sequence_widget.setVisible(False)

        if creation_type == "Asset":
            self.show_creation_asset_widgets()
        elif creation_type == "Sequence/Shot":
            self.show_creation_shot_sequence_widgets()                      

    def show_creation_asset_widgets(self):
        self.creation_asset_widget.setVisible(True)

        asset_path = main_folder_path / "assets"
        asset_types = [x for x in asset_path.iterdir() if x.is_dir()]

        self.creation_table.setColumnCount(2)
        self.creation_table.setHorizontalHeaderLabels(["Asset Type", "Asset Name"])
        self.creation_table.setRowCount(0)

        for asset_type in asset_types:
            index = self.creation_table.rowCount()
            self.creation_table.setRowCount(index + 1)

            asset_type_item = QtWidgets.QTableWidgetItem(asset_type.name)
            self.creation_table.setItem(index, 0, asset_type_item)
            self.creation_table.setSpan(index, 0, 1, 2)

            asset_type_path = asset_path / f"{asset_type.name}"
            asset_names = [x for x in asset_type_path.iterdir() if x.is_dir()]

            for asset_name in asset_names:
                index = self.creation_table.rowCount()
                self.creation_table.setRowCount(index + 1)

                name_le = QtWidgets.QLabel()
                name_le.setText(asset_name.name) 
                self.creation_table.setCellWidget(index, 1, name_le)

        self.creation_table.resizeColumnsToContents()

    def show_creation_shot_sequence_widgets(self):
        self.creation_shot_sequence_widget.setVisible(True)

        sequences_path = main_folder_path / "sequences"
        sequences = [x for x in sequences_path.iterdir() if x.is_dir()]

        current_sequence = self.create_shot_dropdown.currentText()
        self.create_shot_dropdown.clear()
        self.create_shot_dropdown.addItems([x.name for x in sequences])
        self.create_shot_dropdown.setCurrentText(current_sequence)

        self.creation_table.setColumnCount(2)
        self.creation_table.setHorizontalHeaderLabels(["Sequences", "Shots"])
        self.creation_table.setRowCount(0)

        for sequence in sequences:
            index = self.creation_table.rowCount()
            self.creation_table.setRowCount(index + 1)

            sequence_item = QtWidgets.QTableWidgetItem(sequence.name)
            self.creation_table.setItem(index, 0, sequence_item)
            self.creation_table.setSpan(index, 0, 1, 2)

            shots = [x for x in sequence.iterdir() if x.is_dir()]

            for shot in shots:
                index = self.creation_table.rowCount()
                self.creation_table.setRowCount(index + 1)

                name_le = QtWidgets.QLabel()
                name_le.setText(shot.name) 
                self.creation_table.setCellWidget(index, 1, name_le)

        self.creation_table.resizeColumnsToContents()

    def create_asset(self):
        asset_type = self.create_asset_dropdown.currentText()
        asset_name = self.create_asset_le.text()

        if not asset_name:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"Please input a name for the asset."
            )
            return

        try:
            helper_functions.create_asset_folders(main_folder_path, asset_type, asset_name)
            QtWidgets.QMessageBox.information(
                None, 
                "Creation Succeeded", 
                f"Asset {asset_name} of asset type {asset_type} has been created."
            )
        except FileNotFoundError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"{e}"
            )
        except FileExistsError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"There is already an asset type of {asset_type} called {asset_name}."
            )
        self.show_creation_asset_widgets()

    def create_sequence(self):
        sequence_name = self.create_sequence_le.text()
        sequence_path = main_folder_path / "sequences" / sequence_name

        if not sequence_name:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"Please input a name for the asset."
            )
            return

        try:
            sequence_path.mkdir()
            QtWidgets.QMessageBox.information(
                None, 
                "Creation Succeeded", 
                f"Sequence {sequence_name} has been created."
            )
        except FileNotFoundError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"{e}"
            )
        except FileExistsError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"There is already a sequence called {sequence_name}."
            )
        self.show_creation_shot_sequence_widgets()

    def create_shot(self):
        sequence_name = self.create_shot_dropdown.currentText()
        shot_name = self.create_shot_le.text()
        shot_path = main_folder_path / "sequences" / sequence_name / shot_name

        if not sequence_name:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"Make sure a sequence exists first."
            )
            return

        if not shot_name:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"Please input a name for the shot."
            )
            return

        try:
            helper_functions.create_shot_folders(shot_path)
            QtWidgets.QMessageBox.information(
                None, 
                "Creation Succeeded", 
                f"Shot {shot_name} has been created."
            )
        except FileNotFoundError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"{e}"
            )
        except FileExistsError as e:
            QtWidgets.QMessageBox.warning(
                None, 
                "File Error", 
                f"There is already a shot called {shot_name}."
            )
        self.show_creation_shot_sequence_widgets()

    def show_asset_assignment_table(self, index):
        # To ensure the right tab is clicked
        if index != 1:
            return

        assets_path = main_folder_path / "assets"
        assets_types = [x for x in assets_path.iterdir() if x.is_dir()]

        self.assignment_table.setColumnCount(4)
        self.assignment_table.setHorizontalHeaderLabels(["Asset Type", "Asset Name", "Asset Part", "Assignees"])
        self.assignment_table.setRowCount(0)
        self.assignment_table.verticalHeader().setVisible(False)

        for assets_type in assets_types:
            index = self.assignment_table.rowCount()
            self.assignment_table.setRowCount(index + 1)

            asset_type_item = QtWidgets.QTableWidgetItem(assets_type.name)
            self.assignment_table.setItem(index, 0, asset_type_item)
            self.assignment_table.setSpan(index, 0, 1, 3)

            n_a_item = QtWidgets.QTableWidgetItem("N/A")
            self.assignment_table.setItem(index, 3, n_a_item)

            assets = [x for x in assets_type.iterdir() if x.is_dir()]

            for asset in assets:
                index = self.assignment_table.rowCount()
                self.assignment_table.setRowCount(index + 1)

                asset_item = QtWidgets.QTableWidgetItem(asset.name)
                self.assignment_table.setItem(index, 1, asset_item)
                self.assignment_table.setSpan(index, 1, 1, 2)

                n_a_item = QtWidgets.QTableWidgetItem("N/A")
                self.assignment_table.setItem(index, 3, n_a_item)

                asset_parts = [x for x in asset.iterdir() if x.is_dir()]

                for asset_part in asset_parts:
                    index = self.assignment_table.rowCount()
                    self.assignment_table.setRowCount(index + 1)

                    asset_part_item = QtWidgets.QTableWidgetItem(asset_part.name)
                    self.assignment_table.setItem(index, 2, asset_part_item)

                    assignments = self.get_assignment_data()["assignments"]

                    assignees = []

                    for assignment in assignments:
                        if (assignment["main_type"] == "asset" 
                            and assignment["asset_type"] == assets_type.name
                            and assignment["asset_name"] == asset.name
                            and assignment["asset_part"] == asset_part.name 
                            ):
                            assignees.append(assignment["assignee"])
                    
                    assignment_item = QtWidgets.QTableWidgetItem(", ".join(assignees))

                    assignment_data = {
                        "main_type": "asset",
                        "asset_type": assets_type.name,
                        "asset_name": asset.name,
                        "asset_part": asset_part.name
                    }

                    assignment_item.setData(QtCore.Qt.UserRole, assignment_data)
                    self.assignment_table.setItem(index, 3, assignment_item)

        self.assignment_table.resizeColumnsToContents()

    def assign_user(self):
        selected_user_item = self.users_list.currentItem()
        if not selected_user_item:
            QtWidgets.QMessageBox.warning(
                None, 
                "Assignment Error", 
                "Please select a user to assign."
            )
            return

        selected_user = selected_user_item.text()
        assignment_table_item = self.assignment_table.currentItem()

        if not assignment_table_item:
            QtWidgets.QMessageBox.warning(
                None, 
                "Assignment Error", 
                "Select an assignee cell next to the asset part you want to assign the user to."
            )
            return

        assignment_data = assignment_table_item.data(QtCore.Qt.UserRole)

        if assignment_data:
            assignment_data["assignee"] = selected_user

            with open(assignment_data_path, 'r') as file:
                data = json.load(file)
                for assignment in data["assignments"]:
                    if (assignment["main_type"] == assignment_data["main_type"]
                        and assignment["asset_name"] == assignment_data["asset_name"]
                        and assignment["asset_part"] == assignment_data["asset_part"]
                        and assignment["assignee"] == selected_user):
                        QtWidgets.QMessageBox.warning(
                        None, 
                        "Assignment Error", 
                        "Assignee already assigned to this asset part."
                        )
                        return
                data["assignments"].append(assignment_data)

            with open(assignment_data_path, 'w') as file:
                json.dump(data, file, indent=4)

            self.show_asset_assignment_table(1)
        else:
            QtWidgets.QMessageBox.warning(
                None, 
                "Assignment Error", 
                "Select a valid assignee cell."
            )
            return

    def show_tasks_table(self):
        with open(assignment_data_path, 'r') as file:
            data = json.load(file)

        card_data = []

        for assignment in data["assignments"]:
            if assignment["assignee"] == self.assignee_tasks_le.text(): 
                card_data.append((assignment["asset_name"], assignment["asset_part"]))

        card_data.sort()

        for card in card_data:
            self.production_tasks_layout.addWidget(Card(card[0], card[1]))

        # self.tasks.setColumnCount(5)
        # self.assignment_table.setHorizontalHeaderLabels(["Main Type", "Asset Type", "Asset Name", "Asset Part", "Assignees"])
        # self.assignment_table.setRowCount(0)
        # self.assignment_table.verticalHeader().setVisible(False)

        # for assets_type in assets_types:
        #     index = self.assignment_table.rowCount()
        #     self.assignment_table.setRowCount(index + 1)

        #     asset_type_item = QtWidgets.QTableWidgetItem(assets_type.name)
        #     self.assignment_table.setItem(index, 0, asset_type_item)
        #     self.assignment_table.setSpan(index, 0, 1, 3)

        #     n_a_item = QtWidgets.QTableWidgetItem("N/A")
        #     self.assignment_table.setItem(index, 3, n_a_item)

        #     assets = [x for x in assets_type.iterdir() if x.is_dir()]

        #     for asset in assets:
        #         index = self.assignment_table.rowCount()
        #         self.assignment_table.setRowCount(index + 1)

        #         asset_item = QtWidgets.QTableWidgetItem(asset.name)
        #         self.assignment_table.setItem(index, 1, asset_item)
        #         self.assignment_table.setSpan(index, 1, 1, 2)

        #         n_a_item = QtWidgets.QTableWidgetItem("N/A")
        #         self.assignment_table.setItem(index, 3, n_a_item)

        #         asset_parts = [x for x in asset.iterdir() if x.is_dir()]

        #         for asset_part in asset_parts:
        #             index = self.assignment_table.rowCount()
        #             self.assignment_table.setRowCount(index + 1)

        #             asset_part_item = QtWidgets.QTableWidgetItem(asset_part.name)
        #             self.assignment_table.setItem(index, 2, asset_part_item)

        #             assignments = self.get_assignment_data()["assignments"]

        #             assignees = []

        #             for assignment in assignments:
        #                 if (assignment["main_type"] == "asset" 
        #                     and assignment["asset_type"] == assets_type.name
        #                     and assignment["asset_name"] == asset.name
        #                     and assignment["asset_part"] == asset_part.name 
        #                     ):
        #                     assignees.append(assignment["assignee"])
                    
        #             assignment_item = QtWidgets.QTableWidgetItem(", ".join(assignees))

        #             assignment_data = {
        #                 "main_type": "asset",
        #                 "asset_type": assets_type.name,
        #                 "asset_name": asset.name,
        #                 "asset_part": asset_part.name
        #             }

        #             assignment_item.setData(QtCore.Qt.UserRole, assignment_data)
        #             self.assignment_table.setItem(index, 3, assignment_item)

        # self.assignment_table.resizeColumnsToContents()

class Card(QtWidgets.QFrame):
    def __init__(self, title, content):
        super().__init__()

        self.setObjectName("card")

        layout = QtWidgets.QVBoxLayout(self)

        title_label = QtWidgets.QLabel(title)
        content_label = QtWidgets.QLabel(content)

        layout.addWidget(title_label)
        layout.addWidget(content_label)

        self.setStyleSheet("""
        QFrame#card {
            border-radius: 10px;
            border: 1px solid #ddd;
            padding: 10px;
        }
        QLabel {
            font-size: 30px;
        }
        """)

if __name__ == "__main__":
    PixieDustDialog.show_dialog()
