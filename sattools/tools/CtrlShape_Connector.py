import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
from shiboken2 import wrapInstance
import maya.OpenMayaUI as omui

def get_maya_main_window():
    """Get Maya main window as a Python object"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class VisibilityConnectorUI(QtWidgets.QDialog):
    
    def __init__(self, parent=get_maya_main_window()):
        super(VisibilityConnectorUI, self).__init__(parent)
        
        self.setWindowTitle("Shape Visibility Connector")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
    def create_widgets(self):
        """Create UI widgets"""
        # Controllers section
        self.controllers_label = QtWidgets.QLabel("Controllers (shapes to hide):")
        self.controllers_list = QtWidgets.QListWidget()
        self.controllers_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        self.add_selected_btn = QtWidgets.QPushButton("Add Selected Controllers")
        self.remove_selected_btn = QtWidgets.QPushButton("Remove Selected")
        self.clear_list_btn = QtWidgets.QPushButton("Clear List")
        
        # Master controller section
        self.master_label = QtWidgets.QLabel("Master Controller:")
        self.master_line_edit = QtWidgets.QLineEdit()
        self.master_line_edit.setPlaceholderText("Select object and click 'Set Master'")
        self.set_master_btn = QtWidgets.QPushButton("Set Master from Selection")
        
        # Attribute section
        self.attr_label = QtWidgets.QLabel("Attribute:")
        self.attr_combo = QtWidgets.QComboBox()
        self.attr_combo.setEditable(True)
        self.attr_combo.addItems(["showControllers", "ctrlVis", "controlVisibility"])
        
        self.refresh_attr_btn = QtWidgets.QPushButton("Refresh Attributes")
        self.create_new_attr_cb = QtWidgets.QCheckBox("Create if doesn't exist")
        self.create_new_attr_cb.setChecked(True)
        
        # Action buttons
        self.connect_btn = QtWidgets.QPushButton("Connect Visibility")
        self.connect_btn.setStyleSheet("background-color: #4CAF50; font-weight: bold; padding: 8px;")
        
        self.disconnect_btn = QtWidgets.QPushButton("Disconnect All")
        self.close_btn = QtWidgets.QPushButton("Close")
        
    def create_layouts(self):
        """Create UI layouts"""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Controllers section
        controllers_group = QtWidgets.QGroupBox("Controllers")
        controllers_layout = QtWidgets.QVBoxLayout()
        controllers_layout.addWidget(self.controllers_label)
        controllers_layout.addWidget(self.controllers_list)
        
        btn_layout = QtWidgets.QHBoxLayout()
        btn_layout.addWidget(self.add_selected_btn)
        btn_layout.addWidget(self.remove_selected_btn)
        btn_layout.addWidget(self.clear_list_btn)
        controllers_layout.addLayout(btn_layout)
        controllers_group.setLayout(controllers_layout)
        
        # Master controller section
        master_group = QtWidgets.QGroupBox("Master Controller")
        master_layout = QtWidgets.QVBoxLayout()
        master_layout.addWidget(self.master_label)
        master_h_layout = QtWidgets.QHBoxLayout()
        master_h_layout.addWidget(self.master_line_edit)
        master_h_layout.addWidget(self.set_master_btn)
        master_layout.addLayout(master_h_layout)
        master_group.setLayout(master_layout)
        
        # Attribute section
        attr_group = QtWidgets.QGroupBox("Attribute Settings")
        attr_layout = QtWidgets.QVBoxLayout()
        attr_layout.addWidget(self.attr_label)
        
        attr_h_layout = QtWidgets.QHBoxLayout()
        attr_h_layout.addWidget(self.attr_combo)
        attr_h_layout.addWidget(self.refresh_attr_btn)
        attr_layout.addLayout(attr_h_layout)
        attr_layout.addWidget(self.create_new_attr_cb)
        attr_group.setLayout(attr_layout)
        
        # Add all groups to main layout
        main_layout.addWidget(controllers_group)
        main_layout.addWidget(master_group)
        main_layout.addWidget(attr_group)
        
        # Action buttons
        main_layout.addSpacing(10)
        main_layout.addWidget(self.connect_btn)
        
        bottom_layout = QtWidgets.QHBoxLayout()
        bottom_layout.addWidget(self.disconnect_btn)
        bottom_layout.addWidget(self.close_btn)
        main_layout.addLayout(bottom_layout)
        
    def create_connections(self):
        """Connect signals to slots"""
        self.add_selected_btn.clicked.connect(self.add_selected_controllers)
        self.remove_selected_btn.clicked.connect(self.remove_selected_items)
        self.clear_list_btn.clicked.connect(self.controllers_list.clear)
        self.set_master_btn.clicked.connect(self.set_master_controller)
        self.refresh_attr_btn.clicked.connect(self.refresh_attributes)
        self.connect_btn.clicked.connect(self.connect_visibility)
        self.disconnect_btn.clicked.connect(self.disconnect_visibility)
        self.close_btn.clicked.connect(self.close)
        self.master_line_edit.textChanged.connect(self.refresh_attributes)
        
    def add_selected_controllers(self):
        """Add selected objects to the controllers list"""
        sel = cmds.ls(selection=True, transforms=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Warning", "No objects selected!")
            return
            
        for obj in sel:
            # Check if already in list
            items = [self.controllers_list.item(i).text() for i in range(self.controllers_list.count())]
            if obj not in items:
                self.controllers_list.addItem(obj)
                
        cmds.select(clear=True)
        
    def remove_selected_items(self):
        """Remove selected items from the list"""
        for item in self.controllers_list.selectedItems():
            self.controllers_list.takeItem(self.controllers_list.row(item))
            
    def set_master_controller(self):
        """Set the master controller from selection"""
        sel = cmds.ls(selection=True, transforms=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Warning", "No object selected!")
            return
        
        if len(sel) > 1:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select only one master controller!")
            return
            
        self.master_line_edit.setText(sel[0])
        cmds.select(clear=True)
        
    def refresh_attributes(self):
        """Refresh the attribute list from master controller"""
        master = self.master_line_edit.text()
        if not master or not cmds.objExists(master):
            return
            
        # Get all keyable attributes
        attrs = cmds.listAttr(master, keyable=True, scalar=True) or []
        
        current_text = self.attr_combo.currentText()
        self.attr_combo.clear()
        
        # Add default suggestions
        defaults = ["showControllers", "ctrlVis", "controlVisibility"]
        for default in defaults:
            if default not in attrs:
                self.attr_combo.addItem(default)
        
        # Add existing attributes
        for attr in attrs:
            self.attr_combo.addItem(attr)
            
        # Try to restore previous selection
        index = self.attr_combo.findText(current_text)
        if index >= 0:
            self.attr_combo.setCurrentIndex(index)
            
    def connect_visibility(self):
        """Connect shape visibility to master attribute"""
        # Get controllers list
        controllers = [self.controllers_list.item(i).text() for i in range(self.controllers_list.count())]
        if not controllers:
            QtWidgets.QMessageBox.warning(self, "Warning", "No controllers in list!")
            return
            
        # Get master controller
        master = self.master_line_edit.text()
        if not master or not cmds.objExists(master):
            QtWidgets.QMessageBox.warning(self, "Warning", "Master controller doesn't exist!")
            return
            
        # Get attribute name
        attr_name = self.attr_combo.currentText()
        if not attr_name:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please specify an attribute name!")
            return
            
        # Check/create attribute
        if not cmds.attributeQuery(attr_name, node=master, exists=True):
            if self.create_new_attr_cb.isChecked():
                cmds.addAttr(master, longName=attr_name, attributeType='bool', defaultValue=1, keyable=True)
                print("Created attribute: {}.{}".format(master, attr_name))
            else:
                QtWidgets.QMessageBox.warning(self, "Warning", 
                    "Attribute '{}' doesn't exist on '{}'!".format(attr_name, master))
                return
                
        master_attr = "{}.{}".format(master, attr_name)
        connected_count = 0
        
        # Connect each controller's shapes
        for ctrl in controllers:
            if not cmds.objExists(ctrl):
                print("Warning: {} doesn't exist, skipping...".format(ctrl))
                continue
                
            shapes = cmds.listRelatives(ctrl, shapes=True, fullPath=True) or []
            
            for shape in shapes:
                shape_vis_attr = "{}.visibility".format(shape)
                
                # Check if already connected
                if not cmds.isConnected(master_attr, shape_vis_attr):
                    cmds.connectAttr(master_attr, shape_vis_attr, force=True)
                    print("Connected: {} -> {}".format(master_attr, shape_vis_attr))
                    connected_count += 1
                    
        QtWidgets.QMessageBox.information(self, "Success", 
            "Connected {} shape visibilities to {}.{}".format(connected_count, master, attr_name))
            
    def disconnect_visibility(self):
        """Disconnect all shape visibilities from controllers"""
        controllers = [self.controllers_list.item(i).text() for i in range(self.controllers_list.count())]
        if not controllers:
            QtWidgets.QMessageBox.warning(self, "Warning", "No controllers in list!")
            return
            
        disconnected_count = 0
        
        for ctrl in controllers:
            if not cmds.objExists(ctrl):
                continue
                
            shapes = cmds.listRelatives(ctrl, shapes=True, fullPath=True) or []
            
            for shape in shapes:
                shape_vis_attr = "{}.visibility".format(shape)
                connections = cmds.listConnections(shape_vis_attr, source=True, destination=False, plugs=True) or []
                
                for conn in connections:
                    cmds.disconnectAttr(conn, shape_vis_attr)
                    print("Disconnected: {} -X- {}".format(conn, shape_vis_attr))
                    disconnected_count += 1
                    
        QtWidgets.QMessageBox.information(self, "Success", 
            "Disconnected {} shape visibilities".format(disconnected_count))


def show_ui():
    """Show the UI - use this as your button command"""
    global visibility_connector_dialog
    
    try:
        visibility_connector_dialog.close()
        visibility_connector_dialog.deleteLater()
    except:
        pass
    
    visibility_connector_dialog = VisibilityConnectorUI()
    visibility_connector_dialog.show()
    
    return visibility_connector_dialog


# Run the UI
show_ui()
