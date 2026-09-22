import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance


def get_maya_window():
    """Get Maya main window as QWidget"""
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class BlendshapeControlConnector(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(BlendshapeControlConnector, self).__init__(parent or get_maya_window())
        
        self.setWindowTitle("Blendshape Control Connector")
        self.setMinimumWidth(500)
        self.setMinimumHeight(400)
        
        self.selected_mesh = None
        self.blendshape_node = None
        self.targets = []
        self.combo_targets = []
        
        self.setup_ui()
        
    def setup_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Mesh Selection Section
        mesh_group = QtWidgets.QGroupBox("Mesh Selection")
        mesh_layout = QtWidgets.QVBoxLayout()
        
        mesh_h_layout = QtWidgets.QHBoxLayout()
        self.mesh_line = QtWidgets.QLineEdit()
        self.mesh_line.setPlaceholderText("Select mesh with blendshape...")
        self.mesh_line.setReadOnly(True)
        mesh_h_layout.addWidget(self.mesh_line)
        
        self.select_mesh_btn = QtWidgets.QPushButton("Get Selected Mesh")
        self.select_mesh_btn.clicked.connect(self.get_selected_mesh)
        mesh_h_layout.addWidget(self.select_mesh_btn)
        
        mesh_layout.addLayout(mesh_h_layout)
        
        # Blendshape info
        self.blendshape_label = QtWidgets.QLabel("Blendshape Node: None")
        self.blendshape_label.setStyleSheet("color: #888; font-style: italic;")
        mesh_layout.addWidget(self.blendshape_label)
        
        mesh_group.setLayout(mesh_layout)
        main_layout.addWidget(mesh_group)
        
        # Targets List Section
        targets_group = QtWidgets.QGroupBox("Blendshape Targets")
        targets_layout = QtWidgets.QVBoxLayout()
        
        targets_info = QtWidgets.QLabel("Targets with incoming connections are automatically skipped (shown in gray)")
        targets_info.setStyleSheet("color: #666; font-size: 10px; font-style: italic;")
        targets_layout.addWidget(targets_info)
        
        self.targets_list = QtWidgets.QListWidget()
        self.targets_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        targets_layout.addWidget(self.targets_list)
        
        select_btns_layout = QtWidgets.QHBoxLayout()
        self.select_all_btn = QtWidgets.QPushButton("Select All Available Targets")
        self.select_all_btn.clicked.connect(self.select_all_targets)
        select_btns_layout.addWidget(self.select_all_btn)
        
        self.deselect_all_btn = QtWidgets.QPushButton("Deselect All")
        self.deselect_all_btn.clicked.connect(self.deselect_all_targets)
        select_btns_layout.addWidget(self.deselect_all_btn)
        
        self.show_connected_check = QtWidgets.QCheckBox("Show Connected Targets")
        self.show_connected_check.setChecked(False)
        self.show_connected_check.stateChanged.connect(self.refresh_target_list)
        select_btns_layout.addWidget(self.show_connected_check)
        
        targets_layout.addLayout(select_btns_layout)
        targets_group.setLayout(targets_layout)
        main_layout.addWidget(targets_group)
        
        # Connection Options Section
        options_group = QtWidgets.QGroupBox("Connection Options")
        options_layout = QtWidgets.QVBoxLayout()
        
        # Radio buttons for control selection
        self.use_existing_radio = QtWidgets.QRadioButton("Connect to Existing Controls")
        self.use_existing_radio.setChecked(True)
        self.use_existing_radio.toggled.connect(self.update_control_options)
        options_layout.addWidget(self.use_existing_radio)
        
        self.create_new_radio = QtWidgets.QRadioButton("Create New Controls")
        options_layout.addWidget(self.create_new_radio)
        
        # Existing controls section
        self.existing_widget = QtWidgets.QWidget()
        existing_layout = QtWidgets.QVBoxLayout(self.existing_widget)
        existing_layout.setContentsMargins(20, 0, 0, 0)
        
        existing_info = QtWidgets.QLabel("Select ONE control in Maya to add all target attributes")
        existing_info.setStyleSheet("color: #666; font-size: 10px;")
        existing_layout.addWidget(existing_info)
        
        self.get_controls_btn = QtWidgets.QPushButton("Get Selected Controls")
        self.get_controls_btn.clicked.connect(self.get_selected_controls)
        existing_layout.addWidget(self.get_controls_btn)
        
        self.controls_label = QtWidgets.QLabel("Controls: None selected")
        self.controls_label.setStyleSheet("color: #888; font-style: italic;")
        existing_layout.addWidget(self.controls_label)
        
        options_layout.addWidget(self.existing_widget)
        
        # New controls section
        self.new_controls_widget = QtWidgets.QWidget()
        new_controls_layout = QtWidgets.QVBoxLayout(self.new_controls_widget)
        new_controls_layout.setContentsMargins(20, 0, 0, 0)
        
        prefix_layout = QtWidgets.QHBoxLayout()
        prefix_layout.addWidget(QtWidgets.QLabel("Control Name:"))
        self.prefix_line = QtWidgets.QLineEdit("ctrl_blendshape")
        prefix_layout.addWidget(self.prefix_line)
        new_controls_layout.addLayout(prefix_layout)
        
        options_layout.addWidget(self.new_controls_widget)
        self.new_controls_widget.setVisible(False)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Action Buttons
        btn_layout = QtWidgets.QHBoxLayout()
        
        self.connect_btn = QtWidgets.QPushButton("Connect Blendshapes")
        self.connect_btn.setStyleSheet("background-color: #5285a6; color: white; font-weight: bold; padding: 8px;")
        self.connect_btn.clicked.connect(self.connect_blendshapes)
        self.connect_btn.setEnabled(False)
        btn_layout.addWidget(self.connect_btn)
        
        self.close_btn = QtWidgets.QPushButton("Close")
        self.close_btn.clicked.connect(self.close)
        btn_layout.addWidget(self.close_btn)
        
        main_layout.addLayout(btn_layout)
        
        # Status bar
        self.status_label = QtWidgets.QLabel("")
        self.status_label.setStyleSheet("color: #666; font-style: italic; padding: 5px;")
        main_layout.addWidget(self.status_label)
        
    def update_control_options(self):
        """Toggle visibility of control options"""
        use_existing = self.use_existing_radio.isChecked()
        self.existing_widget.setVisible(use_existing)
        self.new_controls_widget.setVisible(not use_existing)
        
    def get_selected_mesh(self):
        """Get the selected mesh and find its blendshape node"""
        selection = cmds.ls(selection=True, type='transform')
        
        if not selection:
            self.show_status("Please select a mesh with blendshape", error=True)
            return
            
        self.selected_mesh = selection[0]
        self.mesh_line.setText(self.selected_mesh)
        
        # Find blendshape node
        shapes = cmds.listRelatives(self.selected_mesh, shapes=True, fullPath=True)
        if not shapes:
            self.show_status("No shape node found", error=True)
            return
            
        history = cmds.listHistory(shapes[0], pruneDagObjects=True)
        blendshapes = cmds.ls(history, type='blendShape')
        
        if not blendshapes:
            self.show_status("No blendshape node found on selected mesh", error=True)
            self.blendshape_node = None
            self.blendshape_label.setText("Blendshape Node: None")
            self.targets_list.clear()
            self.connect_btn.setEnabled(False)
            return
            
        self.blendshape_node = blendshapes[0]
        self.blendshape_label.setText(f"Blendshape Node: {self.blendshape_node}")
        self.blendshape_label.setStyleSheet("color: #5285a6; font-weight: bold;")
        
        # Get targets
        self.get_blendshape_targets()
        
    def get_blendshape_targets(self):
        """Get all targets from the blendshape node"""
        self.targets_list.clear()
        self.targets = []
        self.combo_targets = []
        
        if not self.blendshape_node:
            return
            
        # Get weight indices
        weight_indices = cmds.getAttr(f"{self.blendshape_node}.weight", multiIndices=True)
        
        if not weight_indices:
            self.show_status("No targets found in blendshape", error=True)
            return
        
        print("\n=== Analyzing Blendshape Targets ===")
        print(f"Blendshape Node: {self.blendshape_node}")
        print(f"Total Weight Indices: {len(weight_indices)}")
        
        for idx in weight_indices:
            alias = cmds.aliasAttr(f"{self.blendshape_node}.weight[{idx}]", query=True)
            
            # Check if weight has INCOMING connections (driven by something)
            has_incoming = self.has_incoming_connections(idx)
            
            print(f"\nTarget [{idx}]: {alias}")
            print(f"  Has Incoming Connections: {has_incoming}")
            
            if has_incoming:
                self.combo_targets.append({'name': alias, 'index': idx})
            else:
                self.targets.append({'name': alias, 'index': idx})
        
        print(f"\n=== Summary ===")
        print(f"Available Targets (no incoming): {len(self.targets)}")
        print(f"Connected Targets (has incoming): {len(self.combo_targets)}")
        
        # Refresh the display
        self.refresh_target_list()
            
        self.connect_btn.setEnabled(len(self.targets) > 0)
        
        # Update status
        if self.combo_targets:
            connected_count = len(self.combo_targets)
            available_count = len(self.targets)
            self.show_status(f"Found {available_count} available targets, {connected_count} already connected (hidden)")
        else:
            self.show_status(f"Found {len(self.targets)} targets")
    
    def has_incoming_connections(self, weight_index):
        """
        Check if a weight attribute has INCOMING connections.
        If it has incoming connections, it's either:
        - A combo target driven by combinationShape
        - Already connected to a control
        """
        try:
            weight_attr = f"{self.blendshape_node}.weight[{weight_index}]"
            
            # Check for INCOMING connections ONLY
            incoming = cmds.listConnections(weight_attr,
                                           source=True,      # Look for incoming (source)
                                           destination=False, # Don't look for outgoing
                                           plugs=True,
                                           skipConversionNodes=True)
            
            if incoming:
                print(f"    -> Has incoming connections:")
                for conn in incoming:
                    node = conn.split('.')[0]
                    node_type = cmds.nodeType(node)
                    print(f"       Driven by: {conn} (type: {node_type})")
                return True
            
            print(f"    -> No incoming connections - AVAILABLE")
            return False
            
        except Exception as e:
            print(f"    -> Error checking connections: {e}")
            return False
    
    def refresh_target_list(self):
        """Refresh the target list based on show connected checkbox"""
        self.targets_list.clear()
        
        show_connected = self.show_connected_check.isChecked()
        
        print(f"\n=== Refreshing List (Show Connected: {show_connected}) ===")
        
        # Add available targets (no incoming connections - can be connected)
        for target in self.targets:
            self.targets_list.addItem(target['name'])
            print(f"Added available target: {target['name']}")
        
        # Add connected/combo targets ONLY if checkbox is checked
        if show_connected and self.combo_targets:
            for combo in self.combo_targets:
                item = QtWidgets.QListWidgetItem(f"{combo['name']} [DRIVEN]")
                item.setForeground(QtGui.QColor("#888888"))
                item.setFlags(item.flags() & ~QtCore.Qt.ItemIsEnabled)  # Disable selection
                self.targets_list.addItem(item)
                print(f"Added driven target (disabled): {combo['name']}")
    
    def select_all_targets(self):
        """Select all available targets in the list"""
        for i in range(self.targets_list.count()):
            item = self.targets_list.item(i)
            if item.flags() & QtCore.Qt.ItemIsEnabled:
                item.setSelected(True)
        
    def deselect_all_targets(self):
        """Deselect all targets"""
        self.targets_list.clearSelection()
        
    def get_selected_controls(self):
        """Get selected controls from Maya scene"""
        controls = cmds.ls(selection=True, type='transform')
        
        if not controls:
            self.show_status("No controls selected", error=True)
            self.controls_label.setText("Controls: None selected")
            return
            
        self.selected_controls = controls
        self.controls_label.setText(f"Controls: {len(controls)} selected")
        self.controls_label.setStyleSheet("color: #5285a6; font-weight: bold;")
        self.show_status(f"Got {len(controls)} controls")
        
    def connect_blendshapes(self):
        """Main function to connect blendshapes to controls"""
        if not self.blendshape_node:
            self.show_status("No blendshape node selected", error=True)
            return
            
        selected_items = self.targets_list.selectedItems()
        if not selected_items:
            self.show_status("No targets selected", error=True)
            return
            
        # Get clean target names
        selected_target_names = [item.text().replace(' [DRIVEN]', '') for item in selected_items]
        
        if self.use_existing_radio.isChecked():
            self.connect_to_existing_controls(selected_target_names)
        else:
            self.connect_to_new_controls(selected_target_names)
            
    def connect_to_existing_controls(self, target_names):
        """Connect targets to existing controls"""
        if not hasattr(self, 'selected_controls') or not self.selected_controls:
            self.show_status("No controls selected. Use 'Get Selected Controls' button", error=True)
            return
        
        control = self.selected_controls[0]
        connected = 0
        skipped = 0
        
        for target_name in target_names:
            # Find target in available targets list ONLY
            target_idx = None
            for t in self.targets:
                if t['name'] == target_name:
                    target_idx = t['index']
                    break
            
            # If not in available targets, skip it
            if target_idx is None:
                print(f"SKIPPING: {target_name} (has incoming connections)")
                skipped += 1
                continue
            
            # Add attribute if it doesn't exist
            if not cmds.attributeQuery(target_name, node=control, exists=True):
                cmds.addAttr(control, longName=target_name, attributeType='double', 
                           minValue=0, maxValue=1, defaultValue=0, keyable=True)
            
            # Connect
            source_attr = f"{control}.{target_name}"
            target_attr = f"{self.blendshape_node}.weight[{target_idx}]"
            
            # Double-check if target already has incoming connections
            existing_conn = cmds.listConnections(target_attr, source=True, destination=False, plugs=True)
            if existing_conn:
                print(f"SKIPPING: {target_name} - already has incoming connection from {existing_conn}")
                skipped += 1
                continue
            
            if not cmds.isConnected(source_attr, target_attr):
                cmds.connectAttr(source_attr, target_attr, force=True)
                connected += 1
                print(f"✓ Connected: {source_attr} -> {target_attr}")
            else:
                print(f"Already connected: {source_attr} -> {target_attr}")
                connected += 1
        
        status_msg = f"Connected {connected} targets to control '{control}'"
        if skipped > 0:
            status_msg += f" (skipped {skipped})"
        self.show_status(status_msg)
        
    def connect_to_new_controls(self, target_names):
        """Create a single control and connect all targets to it"""
        ctrl_name = self.prefix_line.text()
        
        if cmds.objExists(ctrl_name):
            ctrl_name = cmds.ls(ctrl_name)[0]
            print(f"Using existing control: {ctrl_name}")
        else:
            ctrl = cmds.circle(name=ctrl_name, normal=(0, 1, 0), radius=2)[0]
            ctrl_name = ctrl
            print(f"Created new control: {ctrl_name}")
        
        connected = 0
        skipped = 0
        
        for target_name in target_names:
            # Find target in available targets list ONLY
            target_idx = None
            for t in self.targets:
                if t['name'] == target_name:
                    target_idx = t['index']
                    break
            
            # If not in available targets, skip it
            if target_idx is None:
                print(f"SKIPPING: {target_name} (has incoming connections)")
                skipped += 1
                continue
            
            # Add attribute
            if not cmds.attributeQuery(target_name, node=ctrl_name, exists=True):
                cmds.addAttr(ctrl_name, longName=target_name, attributeType='double',
                           minValue=0, maxValue=1, defaultValue=0, keyable=True)
            
            # Connect
            source_attr = f"{ctrl_name}.{target_name}"
            target_attr = f"{self.blendshape_node}.weight[{target_idx}]"
            
            # Double-check if target already has incoming connections
            existing_conn = cmds.listConnections(target_attr, source=True, destination=False, plugs=True)
            if existing_conn:
                print(f"SKIPPING: {target_name} - already has incoming connection from {existing_conn}")
                skipped += 1
                continue
            
            if not cmds.isConnected(source_attr, target_attr):
                cmds.connectAttr(source_attr, target_attr, force=True)
                connected += 1
                print(f"✓ Connected: {source_attr} -> {target_attr}")
            else:
                print(f"Already connected: {source_attr} -> {target_attr}")
                connected += 1
        
        cmds.select(ctrl_name)
        
        status_msg = f"Created control '{ctrl_name}' with {connected} connected targets"
        if skipped > 0:
            status_msg += f" (skipped {skipped})"
        self.show_status(status_msg)
        
    def show_status(self, message, error=False):
        """Show status message"""
        if error:
            self.status_label.setStyleSheet("color: #d9534f; font-weight: bold; padding: 5px;")
        else:
            self.status_label.setStyleSheet("color: #5cb85c; font-weight: bold; padding: 5px;")
        self.status_label.setText(message)


def show_ui():
    """Show the UI"""
    global blendshape_tool_window
    try:
        blendshape_tool_window.close()
        blendshape_tool_window.deleteLater()
    except:
        pass
        
    blendshape_tool_window = BlendshapeControlConnector()
    blendshape_tool_window.show()
    return blendshape_tool_window


# Run the tool
if __name__ == "__main__":
    show_ui()
