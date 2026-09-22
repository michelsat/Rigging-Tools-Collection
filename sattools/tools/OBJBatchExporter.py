"""
Maya OBJ Batch Exporter Tool

Exports selected meshes as individual OBJ files with proper naming
"""

import maya.cmds as cmds
import os

from PySide2 import QtWidgets, QtCore, QtGui


class OBJBatchExporter(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(OBJBatchExporter, self).__init__(parent)

        self.setWindowTitle("OBJ Batch Exporter")
        self.setMinimumWidth(500)

        self.init_ui()

    def init_ui(self):

        main_layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel("OBJ Batch Exporter")
        title.setStyleSheet("font-size: 16px; font-weight: bold; padding: 10px;")
        title.setAlignment(QtCore.Qt.AlignCenter)

        main_layout.addWidget(title)

        # Selection info group
        selection_group = QtWidgets.QGroupBox("Selection")
        selection_layout = QtWidgets.QVBoxLayout()

        self.selection_label = QtWidgets.QLabel("No meshes selected")
        self.selection_label.setStyleSheet("padding: 5px;")

        selection_layout.addWidget(self.selection_label)

        refresh_btn = QtWidgets.QPushButton("Refresh Selection")
        refresh_btn.clicked.connect(self.update_selection_info)
        selection_layout.addWidget(refresh_btn)

        selection_group.setLayout(selection_layout)
        main_layout.addWidget(selection_group)

        # Export settings group
        settings_group = QtWidgets.QGroupBox("Export Settings")
        settings_layout = QtWidgets.QVBoxLayout()

        # Output directory
        dir_layout = QtWidgets.QHBoxLayout()
        dir_label = QtWidgets.QLabel("Output Directory:")

        self.dir_path = QtWidgets.QLineEdit()
        self.dir_path.setPlaceholderText("Select export directory...")

        dir_btn = QtWidgets.QPushButton("Browse")
        dir_btn.clicked.connect(self.browse_directory)

        dir_layout.addWidget(dir_label)
        dir_layout.addWidget(self.dir_path)
        dir_layout.addWidget(dir_btn)

        settings_layout.addLayout(dir_layout)

        # Naming options
        naming_layout = QtWidgets.QHBoxLayout()

        prefix_label = QtWidgets.QLabel("Prefix:")
        self.prefix_input = QtWidgets.QLineEdit()
        self.prefix_input.setPlaceholderText("Optional prefix")

        suffix_label = QtWidgets.QLabel("Suffix:")
        self.suffix_input = QtWidgets.QLineEdit()
        self.suffix_input.setPlaceholderText("Optional suffix")

        naming_layout.addWidget(prefix_label)
        naming_layout.addWidget(self.prefix_input)
        naming_layout.addWidget(suffix_label)
        naming_layout.addWidget(self.suffix_input)

        settings_layout.addLayout(naming_layout)

        # Numbering options
        number_layout = QtWidgets.QHBoxLayout()
        self.use_numbering = QtWidgets.QCheckBox("Add numbering (01, 02, 03...)")
        self.use_numbering.setChecked(True)
        number_layout.addWidget(self.use_numbering)
        settings_layout.addLayout(number_layout)

        settings_group.setLayout(settings_layout)
        main_layout.addWidget(settings_group)

        # Export options group
        options_group = QtWidgets.QGroupBox("OBJ Export Options")
        options_layout = QtWidgets.QVBoxLayout()

        self.export_materials = QtWidgets.QCheckBox("Export Materials")
        self.export_materials.setChecked(True)

        self.export_normals = QtWidgets.QCheckBox("Export Normals")
        self.export_normals.setChecked(True)

        self.export_uvs = QtWidgets.QCheckBox("Export UVs")
        self.export_uvs.setChecked(True)

        options_layout.addWidget(self.export_materials)
        options_layout.addWidget(self.export_normals)
        options_layout.addWidget(self.export_uvs)

        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)

        # Progress bar
        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setValue(0)
        main_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: green; padding: 5px;")
        self.status_label.setAlignment(QtCore.Qt.AlignCenter)
        main_layout.addWidget(self.status_label)

        # Export button
        export_btn = QtWidgets.QPushButton("Export Selected Meshes")
        export_btn.setStyleSheet("background-color: #4CAF50; color: white; padding: 10px; font-weight: bold;")
        export_btn.clicked.connect(self.export_meshes)
        main_layout.addWidget(export_btn)

        # Initialize selection info
        self.update_selection_info()

    def update_selection_info(self):
        """Update the selection information display"""
        selected = cmds.ls(selection=True, type='transform')
        mesh_list = []

        for obj in selected:
            shapes = cmds.listRelatives(obj, shapes=True, type='mesh')
            if shapes:
                mesh_list.append(obj)

        if mesh_list:
            self.selection_label.setText(
                "Selected meshes: {0}\n{1}".format(
                    len(mesh_list),
                    "\n".join(mesh_list[:5])
                )
            )
            if len(mesh_list) > 5:
                self.selection_label.setText(
                    self.selection_label.text() +
                    "\n... and {0} more".format(len(mesh_list) - 5)
                )
        else:
            self.selection_label.setText("No meshes selected")

    def browse_directory(self):
        """Open directory browser"""
        # Use Maya main window as parent, no stay-on-top flags
        directory = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            "Select Export Directory",
            "",
            QtWidgets.QFileDialog.ShowDirsOnly
        )

        if directory:
            self.dir_path.setText(directory)
        self.raise_()
        self.activateWindow()

    def get_clean_name(self, mesh_name):
        """Get clean name without namespace and special characters"""
        if ':' in mesh_name:
            mesh_name = mesh_name.split(':')[-1]
        return mesh_name

    def export_meshes(self):
        """Export selected meshes as individual OBJ files"""

        # Validate directory
        export_dir = self.dir_path.text()
        if not export_dir or not os.path.exists(export_dir):
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                "Error",
                "Please select a valid export directory!"
            )
            msgBox.exec_()
            self.raise_()
            return

        # Get selected meshes
        selected = cmds.ls(selection=True, type='transform')
        mesh_list = []

        for obj in selected:
            shapes = cmds.listRelatives(obj, shapes=True, type='mesh')
            if shapes:
                mesh_list.append(obj)

        if not mesh_list:
            msgBox = QtWidgets.QMessageBox(
                QtWidgets.QMessageBox.Warning,
                "Error",
                "No meshes selected!"
            )
            msgBox.exec_()
            self.raise_()
            return

        # Reset progress
        self.progress_bar.setValue(0)
        self.status_label.setText("Exporting...")
        self.status_label.setStyleSheet("color: blue; padding: 5px;")

        # Export each mesh
        exported_count = 0
        prefix = self.prefix_input.text()
        suffix = self.suffix_input.text()

        for i, mesh in enumerate(mesh_list):
            try:
                # Build filename
                clean_name = self.get_clean_name(mesh)

                if self.use_numbering.isChecked():
                    number = str(i + 1).zfill(2)
                    filename = "{0}{1}_{2}{3}.obj".format(
                        prefix, clean_name, number, suffix
                    )
                else:
                    filename = "{0}{1}{2}.obj".format(prefix, clean_name, suffix)

                filepath = os.path.join(export_dir, filename)

                # Select only this mesh
                cmds.select(mesh, replace=True)

                # Export OBJ
                cmds.file(
                    filepath,
                    force=True,
                    options="groups=0;ptgroups=0;materials={0};smoothing=1;normals={1}".format(
                        1 if self.export_materials.isChecked() else 0,
                        1 if self.export_normals.isChecked() else 0
                    ),
                    type="OBJexport",
                    preserveReferences=False,
                    exportSelected=True
                )

                exported_count += 1

                # Update progress
                progress = int(float(i + 1) / float(len(mesh_list)) * 100.0)
                self.progress_bar.setValue(progress)

            except Exception as e:
                print("Error exporting {0}: {1}".format(mesh, str(e)))

        # Restore selection
        cmds.select(mesh_list, replace=True)

        # Update status
        self.progress_bar.setValue(100)
        self.status_label.setText(
            "Successfully exported {0} meshes!".format(exported_count)
        )
        self.status_label.setStyleSheet("color: green; padding: 5px;")

        msgBox = QtWidgets.QMessageBox(
            QtWidgets.QMessageBox.Information,
            "Export Complete",
            "Successfully exported {0} meshes to:\n{1}".format(
                exported_count, export_dir
            )
        )
        msgBox.exec_()
        self.raise_()


def show_exporter():
    """Show the OBJ Batch Exporter window"""
    global obj_exporter_window

    try:
        obj_exporter_window.close()
        obj_exporter_window.deleteLater()
    except:
        pass

    # Get Maya's main window
    maya_window = None
    try:
        from maya import OpenMayaUI as omui
        from shiboken2 import wrapInstance
        maya_main_window_ptr = omui.MQtUtil.mainWindow()
        maya_window = wrapInstance(int(maya_main_window_ptr), QtWidgets.QWidget)
    except:
        pass

    obj_exporter_window = OBJBatchExporter(parent=maya_window)

    # Normal tool window, no global always-on-top flag
    obj_exporter_window.setWindowFlags(QtCore.Qt.Window)

    obj_exporter_window.show()
    obj_exporter_window.raise_()
    obj_exporter_window.activateWindow()


# Run the tool
if __name__ == "__main__":
    show_exporter()
