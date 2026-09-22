from maya import cmds
from expcol import collider, detection
try:
    from PySide2 import QtWidgets, QtCore, QtGui
    from shiboken2 import wrapInstance
except ImportError:
    from PySide6 import QtWidgets, QtCore, QtGui
    from shiboken6 import wrapInstance
from maya import OpenMayaUI as omui
import maya.cmds as cmds


def maya_main_window():
    """Get Maya's main window as a Qt object"""
    main_window_ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(main_window_ptr), QtWidgets.QWidget)


class CollisionToolUI(QtWidgets.QDialog):
    
    def __init__(self, parent=maya_main_window()):
        super(CollisionToolUI, self).__init__(parent)
        
        self.setWindowTitle("Collision Detection Tool")
        self.setMinimumWidth(450)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)
        
        # Initialize variables
        self.control_obj = None
        self.root_joint = None
        self.collider_objects = []
        
        self.create_widgets()
        self.create_layouts()
        self.create_connections()
        
    def create_widgets(self):
        """Create all UI widgets"""
        
        # Control selection
        self.control_label = QtWidgets.QLabel("Control Object:")
        self.control_line = QtWidgets.QLineEdit()
        self.control_line.setPlaceholderText("Select control and click <<")
        self.control_line.setReadOnly(True)
        self.control_btn = QtWidgets.QPushButton("<<")
        self.control_btn.setMaximumWidth(40)
        self.control_btn.setToolTip("Load selected object as control")
        
        # Root joint selection
        self.root_label = QtWidgets.QLabel("Root Joint:")
        self.root_line = QtWidgets.QLineEdit()
        self.root_line.setPlaceholderText("Select root joint and click <<")
        self.root_line.setReadOnly(True)
        self.root_btn = QtWidgets.QPushButton("<<")
        self.root_btn.setMaximumWidth(40)
        self.root_btn.setToolTip("Load selected joint as root")
        
        # Number of joints display
        self.joints_count_label = QtWidgets.QLabel("Total Joints:")
        self.joints_count_value = QtWidgets.QLabel("0")
        self.joints_count_value.setStyleSheet("font-weight: bold; color: #4CAF50;")
        
        # Separator
        self.separator1 = QtWidgets.QFrame()
        self.separator1.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator1.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        # Collider section
        self.collider_label = QtWidgets.QLabel("Collider Types:")
        self.collider_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        
        # Collider type checkboxes with spinboxes
        self.infinite_plane_cb = QtWidgets.QCheckBox("Infinite Plane")
        self.infinite_plane_cb.setChecked(True)
        self.infinite_plane_cb.setToolTip("collider.iplane()")
        self.infinite_plane_spin = QtWidgets.QSpinBox()
        self.infinite_plane_spin.setMinimum(1)
        self.infinite_plane_spin.setMaximum(10)
        self.infinite_plane_spin.setValue(1)
        self.infinite_plane_spin.setMaximumWidth(60)
        
        self.sphere_cb = QtWidgets.QCheckBox("Sphere")
        self.sphere_cb.setToolTip("collider.sphere()")
        self.sphere_spin = QtWidgets.QSpinBox()
        self.sphere_spin.setMinimum(1)
        self.sphere_spin.setMaximum(10)
        self.sphere_spin.setValue(1)
        self.sphere_spin.setMaximumWidth(60)
        
        self.capsule_cb = QtWidgets.QCheckBox("Capsule")
        self.capsule_cb.setChecked(True)
        self.capsule_cb.setToolTip("collider.capsule()")
        self.capsule_spin = QtWidgets.QSpinBox()
        self.capsule_spin.setMinimum(1)
        self.capsule_spin.setMaximum(10)
        self.capsule_spin.setValue(1)
        self.capsule_spin.setMaximumWidth(60)
        
        self.capsule2_cb = QtWidgets.QCheckBox("Capsule2 (Individual Radius)")
        self.capsule2_cb.setToolTip("collider.capsule2() - radius individually")
        self.capsule2_spin = QtWidgets.QSpinBox()
        self.capsule2_spin.setMinimum(1)
        self.capsule2_spin.setMaximum(10)
        self.capsule2_spin.setValue(1)
        self.capsule2_spin.setMaximumWidth(60)
        
        self.cuboid_cb = QtWidgets.QCheckBox("Cuboid")
        self.cuboid_cb.setToolTip("collider.cuboid()")
        self.cuboid_spin = QtWidgets.QSpinBox()
        self.cuboid_spin.setMinimum(1)
        self.cuboid_spin.setMaximum(10)
        self.cuboid_spin.setValue(1)
        self.cuboid_spin.setMaximumWidth(60)
        
        # Custom colliders from scene
        self.custom_collider_label = QtWidgets.QLabel("Custom Collider Objects:")
        self.custom_collider_list = QtWidgets.QListWidget()
        self.custom_collider_list.setMaximumHeight(100)
        self.custom_collider_list.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        
        self.add_collider_btn = QtWidgets.QPushButton("Add Selected")
        self.remove_collider_btn = QtWidgets.QPushButton("Remove Selected")
        self.clear_colliders_btn = QtWidgets.QPushButton("Clear All")
        
        # Separator
        self.separator2 = QtWidgets.QFrame()
        self.separator2.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator2.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        # Detection options
        self.options_label = QtWidgets.QLabel("Detection Options:")
        self.options_label.setStyleSheet("font-weight: bold; font-size: 11pt;")
        
        self.ground_collision_cb = QtWidgets.QCheckBox("Ground Collision")
        self.ground_collision_cb.setChecked(True)
        self.ground_collision_cb.setToolTip("Enable ground collision detection")
        
        self.scalable_cb = QtWidgets.QCheckBox("Scalable")
        self.scalable_cb.setChecked(True)
        self.scalable_cb.setToolTip("Make detection scalable")
        
        # Separator
        self.separator3 = QtWidgets.QFrame()
        self.separator3.setFrameShape(QtWidgets.QFrame.HLine)
        self.separator3.setFrameShadow(QtWidgets.QFrame.Sunken)
        
        # Action buttons
        self.create_btn = QtWidgets.QPushButton("Create Collision Setup")
        self.create_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px;")
        self.create_btn.setMinimumHeight(40)
        
        self.close_btn = QtWidgets.QPushButton("Close")
        
    def create_layouts(self):
        """Create and arrange layouts"""
        
        # Control layout
        control_layout = QtWidgets.QHBoxLayout()
        control_layout.addWidget(self.control_line)
        control_layout.addWidget(self.control_btn)
        
        # Root joint layout
        root_layout = QtWidgets.QHBoxLayout()
        root_layout.addWidget(self.root_line)
        root_layout.addWidget(self.root_btn)
        
        # Joint count layout
        joint_count_layout = QtWidgets.QHBoxLayout()
        joint_count_layout.addWidget(self.joints_count_label)
        joint_count_layout.addWidget(self.joints_count_value)
        joint_count_layout.addStretch()
        
        # Collider type layout with spinboxes
        collider_type_layout = QtWidgets.QGridLayout()
        collider_type_layout.setColumnStretch(0, 1)
        
        row = 0
        collider_type_layout.addWidget(self.infinite_plane_cb, row, 0)
        collider_type_layout.addWidget(QtWidgets.QLabel("Count:"), row, 1)
        collider_type_layout.addWidget(self.infinite_plane_spin, row, 2)
        
        row += 1
        collider_type_layout.addWidget(self.sphere_cb, row, 0)
        collider_type_layout.addWidget(QtWidgets.QLabel("Count:"), row, 1)
        collider_type_layout.addWidget(self.sphere_spin, row, 2)
        
        row += 1
        collider_type_layout.addWidget(self.capsule_cb, row, 0)
        collider_type_layout.addWidget(QtWidgets.QLabel("Count:"), row, 1)
        collider_type_layout.addWidget(self.capsule_spin, row, 2)
        
        row += 1
        collider_type_layout.addWidget(self.capsule2_cb, row, 0)
        collider_type_layout.addWidget(QtWidgets.QLabel("Count:"), row, 1)
        collider_type_layout.addWidget(self.capsule2_spin, row, 2)
        
        row += 1
        collider_type_layout.addWidget(self.cuboid_cb, row, 0)
        collider_type_layout.addWidget(QtWidgets.QLabel("Count:"), row, 1)
        collider_type_layout.addWidget(self.cuboid_spin, row, 2)
        
        # Custom collider buttons layout
        collider_btn_layout = QtWidgets.QHBoxLayout()
        collider_btn_layout.addWidget(self.add_collider_btn)
        collider_btn_layout.addWidget(self.remove_collider_btn)
        collider_btn_layout.addWidget(self.clear_colliders_btn)
        
        # Detection options layout
        options_layout = QtWidgets.QVBoxLayout()
        options_layout.addWidget(self.ground_collision_cb)
        options_layout.addWidget(self.scalable_cb)
        
        # Bottom buttons layout
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()
        button_layout.addWidget(self.close_btn)
        
        # Main layout
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.addWidget(self.control_label)
        main_layout.addLayout(control_layout)
        
        main_layout.addWidget(self.root_label)
        main_layout.addLayout(root_layout)
        
        main_layout.addLayout(joint_count_layout)
        main_layout.addWidget(self.separator1)
        
        main_layout.addWidget(self.collider_label)
        main_layout.addLayout(collider_type_layout)
        
        main_layout.addWidget(self.custom_collider_label)
        main_layout.addWidget(self.custom_collider_list)
        main_layout.addLayout(collider_btn_layout)
        
        main_layout.addWidget(self.separator2)
        main_layout.addWidget(self.options_label)
        main_layout.addLayout(options_layout)
        
        main_layout.addWidget(self.separator3)
        main_layout.addWidget(self.create_btn)
        main_layout.addLayout(button_layout)
        
    def create_connections(self):
        """Connect signals to slots"""
        self.control_btn.clicked.connect(self.load_control)
        self.root_btn.clicked.connect(self.load_root_joint)
        
        self.add_collider_btn.clicked.connect(self.add_custom_collider)
        self.remove_collider_btn.clicked.connect(self.remove_custom_collider)
        self.clear_colliders_btn.clicked.connect(self.clear_custom_colliders)
        
        self.create_btn.clicked.connect(self.create_collision_setup)
        self.close_btn.clicked.connect(self.close)
        
    def load_control(self):
        """Load selected object as control"""
        sel = cmds.ls(sl=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a control object.")
            return
        
        self.control_obj = sel[0]
        self.control_line.setText(self.control_obj)
        
    def load_root_joint(self):
        """Load selected joint as root"""
        sel = cmds.ls(sl=True, type="joint")
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a joint.")
            return
        
        self.root_joint = sel[0]
        self.root_line.setText(self.root_joint)
        
        # Update joint count
        joints = self.get_all_joints()
        self.joints_count_value.setText(str(len(joints)))
        
    def get_children(self, node):
        """Get all child joints recursively"""
        children = []
        child = cmds.listRelatives(node, c=True, type=["joint", "transform"])
        if child:
            children.append(child[0])
            children.extend(self.get_children(child[0]))
        return children
    
    def get_all_joints(self):
        """Get all joints from root"""
        if not self.root_joint:
            return []
        return [self.root_joint] + self.get_children(self.root_joint)
    
    def add_custom_collider(self):
        """Add selected objects as custom colliders"""
        sel = cmds.ls(sl=True)
        if not sel:
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select collider objects.")
            return
        
        for obj in sel:
            if obj not in self.collider_objects:
                self.collider_objects.append(obj)
                self.custom_collider_list.addItem(obj)
                
    def remove_custom_collider(self):
        """Remove selected colliders from list"""
        selected_items = self.custom_collider_list.selectedItems()
        if not selected_items:
            return
        
        for item in selected_items:
            obj_name = item.text()
            if obj_name in self.collider_objects:
                self.collider_objects.remove(obj_name)
            self.custom_collider_list.takeItem(self.custom_collider_list.row(item))
            
    def clear_custom_colliders(self):
        """Clear all custom colliders"""
        self.collider_objects = []
        self.custom_collider_list.clear()
        
    def create_collision_setup(self):
        """Main function to create collision detection setup"""
        
        # Validate inputs
        if not self.control_obj:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a control object.")
            return
        
        if not self.root_joint:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select a root joint.")
            return
        
        # Get all joints
        joints = self.get_all_joints()
        
        if len(joints) < 2:
            QtWidgets.QMessageBox.warning(self, "Error", "Need at least 2 joints in the chain.")
            return
        
        # Create colliders based on selection with counts
        collider_list = []
        
        if self.infinite_plane_cb.isChecked():
            count = self.infinite_plane_spin.value()
            for i in range(count):
                collider_list.append(collider.iplane())
            
        if self.sphere_cb.isChecked():
            count = self.sphere_spin.value()
            for i in range(count):
                collider_list.append(collider.sphere())
            
        if self.capsule_cb.isChecked():
            count = self.capsule_spin.value()
            for i in range(count):
                collider_list.append(collider.capsule())
            
        if self.capsule2_cb.isChecked():
            count = self.capsule2_spin.value()
            for i in range(count):
                collider_list.append(collider.capsule2())
            
        if self.cuboid_cb.isChecked():
            count = self.cuboid_spin.value()
            for i in range(count):
                collider_list.append(collider.cuboid())
        
        # Add custom colliders
        if not collider_list and not self.collider_objects:
            QtWidgets.QMessageBox.warning(self, "Error", "Please select at least one collider type.")
            return
        
        # Get detection options
        ground_col = self.ground_collision_cb.isChecked()
        scalable = self.scalable_cb.isChecked()
        
        # Create collision setup
        try:
            parents = []
            inputs = []
            outputs = []
            
            # Iterate over pairs of joints
            for a, b in zip(joints, joints[1:]):
                
                p = cmds.listRelatives(a, p=True)
                if p:
                    p = p[0]
                
                a_pos = cmds.xform(a, q=True, ws=True, t=True)
                a_rot = cmds.xform(a, q=True, ws=True, ro=True)
                b_pos = cmds.xform(b, q=True, ws=True, t=True)
                
                # Create auxiliary transforms
                prt = cmds.createNode('transform', n='{}_parent'.format(a), p=p)
                ipt = cmds.createNode('transform', n='{}_input'.format(a), p=p)
                out = cmds.createNode('transform', n='{}_output'.format(a), p=p)
                
                # Set positions and rotations
                cmds.xform(prt, ws=True, t=a_pos)
                cmds.xform(prt, ws=True, ro=a_rot)
                cmds.xform(ipt, ws=True, t=b_pos)
                cmds.xform(out, ws=True, t=b_pos)
                
                # Create aim constraint
                cmds.aimConstraint(out, a, aim=[1,0,0], u=[0,0,1], wu=[0,0,1], 
                                 wut='objectrotation', wuo=prt)
                
                parents.append(prt)
                inputs.append(ipt)
                outputs.append(out)
            
            # Combine built-in colliders with custom collider objects
            final_collider_list = collider_list + self.collider_objects
            
            # Create detections
            for prt, ipt, out in zip(parents, inputs, outputs):
                detection.create(
                    ipt, 
                    out, 
                    self.control_obj, 
                    parent=prt, 
                    colliders=final_collider_list, 
                    groundCol=ground_col, 
                    scalable=scalable
                )
            
            QtWidgets.QMessageBox.information(
                self, 
                "Success", 
                "Collision setup created successfully!\\n{} detection nodes created with {} colliders.".format(
                    len(joints)-1, len(final_collider_list))
            )
            
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Error", "Failed to create collision setup:\\n{}".format(str(e)))


def show_ui():
    """Show the UI"""
    global collision_tool_window
    
    try:
        collision_tool_window.close()
        collision_tool_window.deleteLater()
    except:
        pass
    
    collision_tool_window = CollisionToolUI()
    collision_tool_window.show()


# Run the UI
if __name__ == "__main__":
    show_ui()