import maya.cmds as cmds
import maya.OpenMayaUI as omui

try:
    from PySide2 import QtCore, QtWidgets, QtGui
    import shiboken2
except ImportError:
    from PySide import QtCore, QtGui, QtWidgets
    import shiboken

# Define a unique window name that will be consistent
WINDOW_NAME = "blendshapeConnectionToolWindow"

def maya_main_window():
    """
    Return the Maya main window widget
    """
    main_window_ptr = omui.MQtUtil.mainWindow()
    if main_window_ptr is not None:
        if hasattr(shiboken2, 'wrapInstance'):
            return shiboken2.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
        else:
            return shiboken.wrapInstance(int(main_window_ptr), QtWidgets.QMainWindow)
    return None

def check_window_exists():
    """
    Check if the window already exists
    """
    # First check if the window exists through Qt
    for widget in QtWidgets.QApplication.topLevelWidgets():
        if widget.objectName() == WINDOW_NAME and widget.isVisible():
            return widget
    
    # Also check through Maya's UI commands as a fallback
    if cmds.window(WINDOW_NAME, exists=True):
        try:
            ptr = omui.MQtUtil.findWindow(WINDOW_NAME)
            if ptr:
                if hasattr(shiboken2, 'wrapInstance'):
                    return shiboken2.wrapInstance(int(ptr), QtWidgets.QWidget)
                else:
                    return shiboken.wrapInstance(int(ptr), QtWidgets.QWidget)
        except:
            pass
    
    return None

class BlendshapeConnectionTool(QtWidgets.QDialog):
    def __init__(self, parent=maya_main_window()):
        super(BlendshapeConnectionTool, self).__init__(parent)
        
        # Window properties
        self.setWindowTitle("Blendshape Connection Tool")
        self.setMinimumWidth(300)
        self.setObjectName(WINDOW_NAME)
        
        # Make sure the window will be deleted when closed
        self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
        
        # Create the main layout
        self.main_layout = QtWidgets.QVBoxLayout()
        
        # Namespace input
        namespace_layout = QtWidgets.QHBoxLayout()
        namespace_label = QtWidgets.QLabel("Namespace:")
        self.namespace_input = QtWidgets.QLineEdit('blend_')
        namespace_layout.addWidget(namespace_label)
        namespace_layout.addWidget(self.namespace_input)
        self.main_layout.addLayout(namespace_layout)
        
        # Blendshape suffix input
        suffix_layout = QtWidgets.QHBoxLayout()
        suffix_label = QtWidgets.QLabel("Blendshape Suffix:")
        self.suffix_input = QtWidgets.QLineEdit('_corrective')
        suffix_layout.addWidget(suffix_label)
        suffix_layout.addWidget(self.suffix_input)
        self.main_layout.addLayout(suffix_layout)
        
        # Origin selection
        origin_layout = QtWidgets.QHBoxLayout()
        origin_label = QtWidgets.QLabel("Origin Type:")
        self.main_layout.addLayout(origin_layout)
        origin_layout.addWidget(origin_label)
        
        # Radio buttons for origin selection
        self.origin_group = QtWidgets.QButtonGroup(self)
        self.world_radio = QtWidgets.QRadioButton("World")
        self.local_radio = QtWidgets.QRadioButton("Local")
        self.world_radio.setChecked(True)  # Default to world
        
        self.origin_group.addButton(self.world_radio)
        self.origin_group.addButton(self.local_radio)
        
        origin_layout.addWidget(self.world_radio)
        origin_layout.addWidget(self.local_radio)
        
        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        
        # Create Blendshapes button
        create_btn = QtWidgets.QPushButton("Create Blendshapes")
        create_btn.clicked.connect(self.create_blendshapes)
        button_layout.addWidget(create_btn)
        
        # Close button
        close_btn = QtWidgets.QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        self.main_layout.addLayout(button_layout)
        
        # Set the layout
        self.setLayout(self.main_layout)
    
    def create_blendshapes(self):
        """
        Create blendshapes based on selected objects
        """
        # Get selected objects
        sel = cmds.ls(sl=True)
        
        if not sel:
            cmds.confirmDialog(title='Error', message='Please select objects first!', button=['OK'])
            return
        
        # Get namespace and suffix from input fields
        nameSpace = self.namespace_input.text()
        blendshapeName = self.suffix_input.text()
        
        # Determine origin type
        origin_type = 'world' if self.world_radio.isChecked() else 'local'
        
        try:
            # First pass: Create blendshape connections
            for obj in sel:
                # Select source and target
                cmds.select('%s%s' % (nameSpace, obj), obj)
                
                # Create blendshape with selected origin type
                cmds.blendShape(n='%s%s' % (obj, blendshapeName), tc=False, o=origin_type)
            
            # Clear selection
            cmds.select(d=True)
            
            # Second pass: Add to selection
            for obj in sel:
                cmds.select('%s%s' % (obj, blendshapeName), add=True)
            
            # Third pass: Set blendshape weight
            for obj in sel:
                cmds.setAttr('%s%s.%s%s' % (obj, blendshapeName, nameSpace, obj), 1)
            
            # Success message
            cmds.confirmDialog(title='Success', 
                               message=f'Blendshapes created successfully with {origin_type} origin!', 
                               button=['OK'])
        
        except Exception as e:
            # Error handling
            cmds.confirmDialog(title='Error', 
                               message=f'An error occurred: {str(e)}', 
                               button=['OK'])

def show_blendshape_tool():
    """
    Show the Blendshape Connection Tool
    """
    # Check if window already exists
    existing_window = check_window_exists()
    
    if existing_window:
        # If it exists, bring it to front
        existing_window.show()
        existing_window.raise_()
        existing_window.activateWindow()
    else:
        # If it doesn't exist, create a new one
        tool = BlendshapeConnectionTool()
        tool.show()

# Clean up any existing UI with the same name before showing
# This is important for Maya's UI system
if cmds.window(WINDOW_NAME, exists=True):
    cmds.deleteUI(WINDOW_NAME, window=True)

# Call to show the tool
show_blendshape_tool()