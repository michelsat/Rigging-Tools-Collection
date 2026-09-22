import maya.cmds as cmds
from PySide2 import QtWidgets, QtCore, QtGui
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance


def maya_main_window():
    """Get Maya's main window as a QWidget"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class ControlDuplicatorUI(QtWidgets.QDialog):
    """UI for duplicating controls with scaled CVs and hierarchy management"""
    
    def __init__(self, parent=maya_main_window()):
        super(ControlDuplicatorUI, self).__init__(parent)
        
        self.setWindowTitle("Control Duplicator")
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        self.setMinimumWidth(350)
        self.setMinimumHeight(200)
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
    def create_widgets(self):
        """Create UI widgets"""
        # Title
        self.title_label = QtWidgets.QLabel("Control Duplicator Tool")
        self.title_label.setStyleSheet("font-size: 14px; font-weight: bold; padding: 5px;")
        self.title_label.setAlignment(QtCore.Qt.AlignCenter)
        
        # Selected control display
        self.selected_label = QtWidgets.QLabel("Selected Control:")
        self.selected_display = QtWidgets.QLineEdit()
        self.selected_display.setReadOnly(True)
        self.selected_display.setPlaceholderText("No control selected")
        
        self.refresh_btn = QtWidgets.QPushButton("Refresh Selection")
        self.refresh_btn.setIcon(self.style().standardIcon(QtWidgets.QStyle.SP_BrowserReload))
        
        # Scale factor
        self.scale_label = QtWidgets.QLabel("CV Scale Factor:")
        self.scale_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.scale_slider.setMinimum(10)
        self.scale_slider.setMaximum(100)
        self.scale_slider.setValue(80)
        self.scale_slider.setTickPosition(QtWidgets.QSlider.TicksBelow)
        self.scale_slider.setTickInterval(10)
        
        self.scale_spinbox = QtWidgets.QDoubleSpinBox()
        self.scale_spinbox.setMinimum(0.1)
        self.scale_spinbox.setMaximum(1.0)
        self.scale_spinbox.setSingleStep(0.05)
        self.scale_spinbox.setValue(0.8)
        self.scale_spinbox.setSuffix(" (80%)")
        
        # Placement options
        self.placement_group = QtWidgets.QGroupBox("Control Placement")
        self.under_radio = QtWidgets.QRadioButton("Create UNDER selected control")
        self.under_radio.setChecked(True)
        self.under_radio.setToolTip("New control will be parented under the selected control")
        
        self.above_radio = QtWidgets.QRadioButton("Create ABOVE selected control")
        self.above_radio.setToolTip("New control will be inserted as parent of the selected control")
        
        # Options
        self.options_group = QtWidgets.QGroupBox("Options")
        self.reparent_checkbox = QtWidgets.QCheckBox("Reparent children to new control (UNDER mode only)")
        self.reparent_checkbox.setChecked(True)
        self.reparent_checkbox.setToolTip("Move all children of the original control under the new control")
        
        self.zero_transforms_checkbox = QtWidgets.QCheckBox("Zero out transforms")
        self.zero_transforms_checkbox.setChecked(True)
        self.zero_transforms_checkbox.setToolTip("Reset translation and rotation to zero (recommended)")
        
        # Info section
        self.info_text = QtWidgets.QTextEdit()
        self.info_text.setReadOnly(True)
        self.info_text.setMaximumHeight(80)
        self.info_text.setPlaceholderText("Status and information will appear here...")
        
        # Buttons
        self.create_btn = QtWidgets.QPushButton("Create Control")
        self.create_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 8px; }")
        self.create_btn.setMinimumHeight(40)
        
        self.close_btn = QtWidgets.QPushButton("Close")
        
    def create_layouts(self):
        """Create and set layouts"""
        main_layout = QtWidgets.QVBoxLayout(self)
        
        # Title
        main_layout.addWidget(self.title_label)
        
        # Separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Sunken)
        main_layout.addWidget(line)
        
        # Selection section
        selection_layout = QtWidgets.QVBoxLayout()
        selection_layout.addWidget(self.selected_label)
        
        selection_row = QtWidgets.QHBoxLayout()
        selection_row.addWidget(self.selected_display)
        selection_row.addWidget(self.refresh_btn)
        selection_layout.addLayout(selection_row)
        
        main_layout.addLayout(selection_layout)
        
        # Scale factor section
        scale_layout = QtWidgets.QVBoxLayout()
        scale_layout.addWidget(self.scale_label)
        
        scale_controls = QtWidgets.QHBoxLayout()
        scale_controls.addWidget(self.scale_slider, 2)
        scale_controls.addWidget(self.scale_spinbox, 1)
        scale_layout.addLayout(scale_controls)
        
        main_layout.addLayout(scale_layout)
        
        # Placement group
        placement_layout = QtWidgets.QVBoxLayout()
        placement_layout.addWidget(self.under_radio)
        placement_layout.addWidget(self.above_radio)
        self.placement_group.setLayout(placement_layout)
        main_layout.addWidget(self.placement_group)
        
        # Options group
        options_layout = QtWidgets.QVBoxLayout()
        options_layout.addWidget(self.reparent_checkbox)
        options_layout.addWidget(self.zero_transforms_checkbox)
        self.options_group.setLayout(options_layout)
        main_layout.addWidget(self.options_group)
        
        # Info section
        main_layout.addWidget(QtWidgets.QLabel("Status:"))
        main_layout.addWidget(self.info_text)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addWidget(self.create_btn)
        button_layout.addWidget(self.close_btn)
        main_layout.addLayout(button_layout)
        
        main_layout.addStretch()
        
    def create_connections(self):
        """Connect signals to slots"""
        self.refresh_btn.clicked.connect(self.refresh_selection)
        self.scale_slider.valueChanged.connect(self.update_spinbox_from_slider)
        self.scale_spinbox.valueChanged.connect(self.update_slider_from_spinbox)
        self.create_btn.clicked.connect(self.create_control)
        self.close_btn.clicked.connect(self.close)
        self.under_radio.toggled.connect(self.update_reparent_option)
        
        # Initial refresh
        self.refresh_selection()
        
    def update_reparent_option(self):
        """Enable/disable reparent option based on placement mode"""
        if self.under_radio.isChecked():
            self.reparent_checkbox.setEnabled(True)
            self.reparent_checkbox.setText("Reparent children to new control (UNDER mode only)")
        else:
            self.reparent_checkbox.setEnabled(False)
            self.reparent_checkbox.setText("Reparent children to new control (UNDER mode only)")
        
    def refresh_selection(self):
        """Update the selected control display"""
        sel = cmds.ls(selection=True, type='transform')
        if sel:
            self.selected_display.setText(sel[0])
            self.selected_display.setStyleSheet("background-color: #E8F5E9;")
            
            # Check for children
            children = cmds.listRelatives(sel[0], children=True, type='transform') or []
            if children:
                self.add_info(f"Selected: {sel[0]}\nFound {len(children)} child transform(s)", "info")
            else:
                self.add_info(f"Selected: {sel[0]}\nNo children found", "info")
        else:
            self.selected_display.setText("")
            self.selected_display.setStyleSheet("")
            self.add_info("No control selected. Please select a control in Maya.", "warning")
            
    def update_spinbox_from_slider(self, value):
        """Update spinbox when slider changes"""
        scale_value = value / 100.0
        self.scale_spinbox.blockSignals(True)
        self.scale_spinbox.setValue(scale_value)
        self.scale_spinbox.setSuffix(f" ({value}%)")
        self.scale_spinbox.blockSignals(False)
        
    def update_slider_from_spinbox(self, value):
        """Update slider when spinbox changes"""
        slider_value = int(value * 100)
        self.scale_slider.blockSignals(True)
        self.scale_slider.setValue(slider_value)
        self.scale_slider.blockSignals(False)
        self.scale_spinbox.setSuffix(f" ({slider_value}%)")
        
    def add_info(self, message, msg_type="info"):
        """Add information to the info text area"""
        if msg_type == "success":
            color = "#4CAF50"
        elif msg_type == "warning":
            color = "#FF9800"
        elif msg_type == "error":
            color = "#F44336"
        else:
            color = "#2196F3"
            
        self.info_text.append(f'<span style="color: {color};">• {message}</span>')
        
    def create_control(self):
        """Execute the control duplication"""
        sel = cmds.ls(selection=True, type='transform')
        
        if not sel:
            self.add_info("ERROR: Please select a control first!", "error")
            return
            
        if len(sel) > 1:
            self.add_info("ERROR: Please select only one control!", "error")
            return
            
        original = sel[0]
        scale_factor = self.scale_spinbox.value()
        create_above = self.above_radio.isChecked()
        
        try:
            # Store children if reparenting is enabled (UNDER mode only)
            children = []
            if self.reparent_checkbox.isChecked() and not create_above:
                children = cmds.listRelatives(original, children=True, type='transform', fullPath=True) or []
            
            # Get shapes
            shapes = cmds.listRelatives(original, shapes=True, fullPath=True) or []
            
            if not shapes:
                self.add_info(f"ERROR: {original} has no shape nodes!", "error")
                return
            
            # Get parent of original (for ABOVE mode)
            original_parent = None
            if create_above:
                parents = cmds.listRelatives(original, parent=True, fullPath=True)
                if parents:
                    original_parent = parents[0]
            
            # Create new transform
            duplicate = cmds.createNode('transform', name=f"{original}_offset" if create_above else f"{original}_child")
            
            # Copy world space transformation
            world_matrix = cmds.xform(original, query=True, matrix=True, worldSpace=True)
            cmds.xform(duplicate, matrix=world_matrix, worldSpace=True)
            
            # Copy pivot points
            rp = cmds.xform(original, query=True, rotatePivot=True, worldSpace=True)
            sp = cmds.xform(original, query=True, scalePivot=True, worldSpace=True)
            cmds.xform(duplicate, rotatePivot=rp, worldSpace=True)
            cmds.xform(duplicate, scalePivot=sp, worldSpace=True)
            
            # Duplicate and parent shape nodes
            for shape in shapes:
                dup_shape = cmds.duplicate(shape, returnRootsOnly=False)[0]
                dup_shapes = cmds.listRelatives(dup_shape, shapes=True, fullPath=True)
                
                if dup_shapes:
                    for ds in dup_shapes:
                        cmds.parent(ds, duplicate, shape=True, relative=True)
                
                if cmds.objExists(dup_shape):
                    cmds.delete(dup_shape)
            
            # Scale down the CVs
            dup_shapes = cmds.listRelatives(duplicate, shapes=True, fullPath=True) or []
            for dup_shape in dup_shapes:
                if cmds.nodeType(dup_shape) == 'nurbsCurve':
                    degree = cmds.getAttr(f"{dup_shape}.degree")
                    spans = cmds.getAttr(f"{dup_shape}.spans")
                    num_cvs = degree + spans
                    
                    for i in range(num_cvs):
                        cv_pos = cmds.xform(f"{dup_shape}.cv[{i}]", query=True, translation=True, objectSpace=True)
                        scaled_pos = [cv_pos[0] * scale_factor, cv_pos[1] * scale_factor, cv_pos[2] * scale_factor]
                        cmds.xform(f"{dup_shape}.cv[{i}]", translation=scaled_pos, objectSpace=True)
                
                elif cmds.nodeType(dup_shape) == 'mesh':
                    num_verts = cmds.polyEvaluate(dup_shape, vertex=True)
                    for i in range(num_verts):
                        vert_pos = cmds.xform(f"{dup_shape}.vtx[{i}]", query=True, translation=True, objectSpace=True)
                        scaled_pos = [vert_pos[0] * scale_factor, vert_pos[1] * scale_factor, vert_pos[2] * scale_factor]
                        cmds.xform(f"{dup_shape}.vtx[{i}]", translation=scaled_pos, objectSpace=True)
            
            if create_above:
                # ABOVE MODE: Insert new control as parent of selected
                # Store original's current parent before making changes
                original_parent_before = cmds.listRelatives(original, parent=True, fullPath=True)
                
                # First, unparent the original temporarily to world
                if original_parent_before:
                    cmds.parent(original, world=True)
                
                # Parent new control to original's old parent (if it had one)
                if original_parent:
                    cmds.parent(duplicate, original_parent)
                
                # Zero out duplicate's transforms first (while in its parent space)
                if self.zero_transforms_checkbox.isChecked():
                    cmds.setAttr(f"{duplicate}.translateX", 0)
                    cmds.setAttr(f"{duplicate}.translateY", 0)
                    cmds.setAttr(f"{duplicate}.translateZ", 0)
                    cmds.setAttr(f"{duplicate}.rotateX", 0)
                    cmds.setAttr(f"{duplicate}.rotateY", 0)
                    cmds.setAttr(f"{duplicate}.rotateZ", 0)
                    cmds.setAttr(f"{duplicate}.scaleX", 1)
                    cmds.setAttr(f"{duplicate}.scaleY", 1)
                    cmds.setAttr(f"{duplicate}.scaleZ", 1)
                
                # Now parent original under the new control
                cmds.parent(original, duplicate)
                
                # Zero out the original's transforms so it sits at duplicate's position
                if self.zero_transforms_checkbox.isChecked():
                    cmds.setAttr(f"{original}.translateX", 0)
                    cmds.setAttr(f"{original}.translateY", 0)
                    cmds.setAttr(f"{original}.translateZ", 0)
                    cmds.setAttr(f"{original}.rotateX", 0)
                    cmds.setAttr(f"{original}.rotateY", 0)
                    cmds.setAttr(f"{original}.rotateZ", 0)
                    cmds.setAttr(f"{original}.scaleX", 1)
                    cmds.setAttr(f"{original}.scaleY", 1)
                    cmds.setAttr(f"{original}.scaleZ", 1)
                
                self.add_info(f"SUCCESS: Created '{duplicate}' ABOVE '{original}'", "success")
                
            else:
                # UNDER MODE: Parent new control under original
                cmds.parent(duplicate, original)
                
                # Zero out transforms if enabled
                if self.zero_transforms_checkbox.isChecked():
                    cmds.setAttr(f"{duplicate}.translateX", 0)
                    cmds.setAttr(f"{duplicate}.translateY", 0)
                    cmds.setAttr(f"{duplicate}.translateZ", 0)
                    cmds.setAttr(f"{duplicate}.rotateX", 0)
                    cmds.setAttr(f"{duplicate}.rotateY", 0)
                    cmds.setAttr(f"{duplicate}.rotateZ", 0)
                    cmds.setAttr(f"{duplicate}.scaleX", 1)
                    cmds.setAttr(f"{duplicate}.scaleY", 1)
                    cmds.setAttr(f"{duplicate}.scaleZ", 1)
                
                # Reparent children (UNDER mode only)
                reparented_count = 0
                if self.reparent_checkbox.isChecked() and children:
                    for child in children:
                        if cmds.objExists(child) and cmds.nodeType(child) == 'transform':
                            try:
                                cmds.parent(child, duplicate)
                                reparented_count += 1
                            except Exception as e:
                                self.add_info(f"Could not reparent {child}: {str(e)}", "warning")
                
                self.add_info(f"SUCCESS: Created '{duplicate}' UNDER '{original}'", "success")
                if reparented_count > 0:
                    self.add_info(f"Reparented {reparented_count} child(ren)", "info")
            
            # Select new control
            cmds.select(duplicate)
            
            # Success message
            percentage = int(scale_factor * 100)
            self.add_info(f"CVs scaled to {percentage}% of original size", "info")
            
            # Update selection display
            self.refresh_selection()
            
        except Exception as e:
            self.add_info(f"ERROR: {str(e)}", "error")
            import traceback
            traceback.print_exc()


def show_ui():
    """Show the UI"""
    global control_duplicator_ui
    
    try:
        control_duplicator_ui.close()
        control_duplicator_ui.deleteLater()
    except:
        pass
    
    control_duplicator_ui = ControlDuplicatorUI()
    control_duplicator_ui.show()


# Run the UI
if __name__ == "__main__":
    show_ui()