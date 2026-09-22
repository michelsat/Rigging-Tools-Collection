import maya.cmds as cmds
import json
import os

class TransformManager:
    def __init__(self):
        self.saved_data = {}
        self.file_path = ""
        self.namespace_mode = "keep"  # Options: "keep", "replace", "strip"
        self.target_namespace = ""
        self.create_ui()
    
    def create_ui(self):
        """Create the UI for the transform manager"""
        # Check if window exists and delete it
        if cmds.window("transformManagerWindow", exists=True):
            cmds.deleteUI("transformManagerWindow", window=True)
        
        # Create window
        window = cmds.window("transformManagerWindow", title="Transform Manager", widthHeight=(400, 350))
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnOffset=["both", 10])
        
        cmds.text(label="Transform Manager", font="boldLabelFont", height=30)
        cmds.separator(height=10, style="none")
        
        # File path controls
        file_layout = cmds.rowLayout(numberOfColumns=3, columnWidth3=(280, 60, 60), adjustableColumn=1, columnAttach=[(1, 'left', 0), (2, 'left', 0), (3, 'left', 0)])
        self.file_path_field = cmds.textField(text=self.file_path, placeholderText="File path for saved transform data")
        cmds.button(label="Browse", command=self.browse_file)
        cmds.setParent(main_layout)
        
        # File operation buttons
        file_buttons_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=(195, 195), adjustableColumn=1, columnAttach=[(1, 'left', 0), (2, 'left', 0)])
        cmds.button(label="Save To File", command=self.save_to_file, height=30)
        cmds.button(label="Open File", command=self.open_file, height=30)
        cmds.setParent(main_layout)
        
        cmds.separator(height=10, style="in")
        
        # Namespace controls - Namespace mode radio buttons
        cmds.text(label="Namespace Handling:", align="left")
        namespace_layout = cmds.rowLayout(numberOfColumns=3, columnWidth3=(130, 130, 130), adjustableColumn=1, columnAttach=[(1, 'left', 0), (2, 'left', 0), (3, 'left', 0)])
        
        self.namespace_radio_group = cmds.radioCollection()
        self.keep_rb = cmds.radioButton(label="Keep Original", select=True, 
                                        onCommand=lambda x: self.set_namespace_mode("keep"))
        self.replace_rb = cmds.radioButton(label="Replace", 
                                          onCommand=lambda x: self.set_namespace_mode("replace"))
        self.strip_rb = cmds.radioButton(label="Strip Namespaces", 
                                        onCommand=lambda x: self.set_namespace_mode("strip"))
        cmds.setParent(main_layout)
        
        # Target namespace field (only used when "replace" is selected)
        target_ns_layout = cmds.rowLayout(numberOfColumns=2, columnWidth2=(130, 260), adjustableColumn=2,
                                         columnAttach=[(1, 'left', 0), (2, 'left', 0)])
        cmds.text(label="Target Namespace:", align="left")
        self.target_namespace_field = cmds.textField(text=self.target_namespace, 
                                                   placeholderText="New namespace (for Replace mode)",
                                                   enable=False)
        cmds.setParent(main_layout)
        
        cmds.separator(height=10, style="in")
        
        # Action buttons
        cmds.button(label="Save Selected Controls Transform Values", command=self.save_transform_values, height=40)
        cmds.button(label="Apply Saved Transform Values", command=self.apply_transform_values, height=40)
        
        cmds.separator(height=10, style="in")
        
        # Status field
        self.status_field = cmds.textField(editable=False, text="Ready")
        
        # Show window
        cmds.showWindow(window)
    
    def set_namespace_mode(self, mode):
        """Set the namespace handling mode"""
        self.namespace_mode = mode
        # Enable/disable target namespace field based on mode
        if mode == "replace":
            cmds.textField(self.target_namespace_field, edit=True, enable=True)
        else:
            cmds.textField(self.target_namespace_field, edit=True, enable=False)
    
    def get_object_with_namespace(self, obj_name, mode, target_ns=""):
        """Handle object name based on namespace mode"""
        # If no colon, there's no namespace
        if ":" not in obj_name:
            if mode == "replace" and target_ns:
                return f"{target_ns}:{obj_name}"
            return obj_name
            
        # Split the namespace and object name
        namespace, base_name = obj_name.split(":", 1)
        
        if mode == "keep":
            return obj_name
        elif mode == "strip":
            return base_name
        elif mode == "replace" and target_ns:
            return f"{target_ns}:{base_name}"
        else:
            return obj_name
    
    def browse_file(self, *args):
        """Open file browser to select a file path"""
        file_result = cmds.fileDialog2(fileMode=0, caption="Select Transform Data File", fileFilter="JSON Files (*.json)")
        if file_result:
            self.file_path = file_result[0]
            cmds.textField(self.file_path_field, edit=True, text=self.file_path)
    
    def save_to_file(self, *args):
        """Save the current transform data to a file"""
        if not self.saved_data:
            self.update_status("No transform data to save")
            return
            
        file_path = cmds.textField(self.file_path_field, query=True, text=True)
        if not file_path:
            file_result = cmds.fileDialog2(fileMode=0, caption="Save Transform Data As", fileFilter="JSON Files (*.json)")
            if not file_result:
                return
            file_path = file_result[0]
            cmds.textField(self.file_path_field, edit=True, text=file_path)
        
        try:
            with open(file_path, 'w') as file:
                json.dump(self.saved_data, file, indent=4)
            self.update_status(f"Saved transform data for {len(self.saved_data)} controllers to file")
        except Exception as e:
            self.update_status(f"Error saving to file: {str(e)}")
    
    def open_file(self, *args):
        """Open and load transform data from a file"""
        file_path = cmds.textField(self.file_path_field, query=True, text=True)
        if not file_path:
            file_result = cmds.fileDialog2(fileMode=1, caption="Open Transform Data File", fileFilter="JSON Files (*.json)")
            if not file_result:
                return
            file_path = file_result[0]
            cmds.textField(self.file_path_field, edit=True, text=file_path)
        
        if not os.path.exists(file_path):
            self.update_status(f"File not found: {file_path}")
            return
            
        try:
            with open(file_path, 'r') as file:
                self.saved_data = json.load(file)
            self.update_status(f"Loaded transform data for {len(self.saved_data)} controllers from file")
        except Exception as e:
            self.update_status(f"Error loading file: {str(e)}")
    
    def save_transform_values(self, *args):
        """Save transform values of selected controllers"""
        selected = cmds.ls(selection=True)
        
        if not selected:
            self.update_status("No objects selected")
            return
        
        # Get namespace mode
        mode = self.namespace_mode
        
        # Reset saved data
        self.saved_data = {}
        objects_count = 0
        
        for obj in selected:
            # Check if the object exists
            if not cmds.objExists(obj):
                continue
            
            # Get object name based on namespace mode
            target_obj = self.get_object_with_namespace(obj, mode)
                
            # Save transform data and track attribute state (locked/hidden)
            obj_data = {
                "translate": [],
                "rotate": [],
                "scale": [],
                "attr_state": {},  # Store information about locked/hidden attributes
                "original_name": obj  # Store original name for reference
            }
            
            # Check and save translate attributes
            axes = ['X', 'Y', 'Z']
            for i, axis in enumerate(axes):
                for attr_type in ["translate", "rotate", "scale"]:
                    attr_name = f"{attr_type}{axis}"
                    full_attr = f"{obj}.{attr_name}"
                    
                    # Check if attribute exists
                    if not cmds.attributeQuery(attr_name, node=obj, exists=True):
                        continue
                    
                    # Store attribute state (locked and hidden)
                    locked = cmds.getAttr(full_attr, lock=True)
                    hidden = not cmds.getAttr(full_attr, settable=True)
                    obj_data["attr_state"][attr_name] = {
                        "locked": locked,
                        "hidden": hidden
                    }
                    
                    # Store the value
                    if attr_type == "translate":
                        obj_data["translate"].append(cmds.getAttr(full_attr))
                    elif attr_type == "rotate":
                        obj_data["rotate"].append(cmds.getAttr(full_attr))
                    elif attr_type == "scale":
                        obj_data["scale"].append(cmds.getAttr(full_attr))
            
            self.saved_data[target_obj] = obj_data
            objects_count += 1
        
        self.update_status(f"Saved transform values for {objects_count} controllers in memory" + 
                          (f" ({self.namespace_mode} namespace mode)" if objects_count > 0 else ""))
    
    def apply_transform_values(self, *args):
        """Apply saved transform values to controllers"""
        if not self.saved_data:
            self.update_status("No transform data available")
            return
        
        # Get namespace mode and target namespace
        mode = self.namespace_mode
        target_ns = cmds.textField(self.target_namespace_field, query=True, text=True) if mode == "replace" else ""
        
        # Apply values to objects
        applied_count = 0
        skipped_attrs = 0
        skipped_objects = 0
        
        # Create a list of all objects in scene for faster lookup
        scene_objects = set(cmds.ls())
        
        for stored_obj, transform_data in self.saved_data.items():
            # Get the target object name based on namespace mode
            if mode == "keep":
                target_obj = stored_obj
            else:
                # In strip or replace mode, get the original name then reapply current mode
                original_name = transform_data.get("original_name", stored_obj)
                target_obj = self.get_object_with_namespace(original_name, mode, target_ns)
            
            # Check if the target object exists
            if target_obj not in scene_objects:
                skipped_objects += 1
                continue
                
            try:
                # Set translate values
                axes = ['X', 'Y', 'Z']
                for i, axis in enumerate(axes):
                    for attr_type in ["translate", "rotate", "scale"]:
                        attr_name = f"{attr_type}{axis}"
                        full_attr = f"{target_obj}.{attr_name}"
                        
                        # Skip if attribute doesn't exist
                        if not cmds.attributeQuery(attr_name, node=target_obj, exists=True):
                            continue
                        
                        # Check if attribute is locked or hidden
                        attr_state = transform_data.get("attr_state", {}).get(attr_name, {})
                        locked = cmds.getAttr(full_attr, lock=True)
                        hidden = not cmds.getAttr(full_attr, settable=True)
                        
                        # Skip locked or hidden attributes
                        if locked or hidden:
                            skipped_attrs += 1
                            continue
                        
                        # Apply the value
                        if attr_type == "translate" and i < len(transform_data["translate"]):
                            cmds.setAttr(full_attr, transform_data["translate"][i])
                        elif attr_type == "rotate" and i < len(transform_data["rotate"]):
                            cmds.setAttr(full_attr, transform_data["rotate"][i])
                        elif attr_type == "scale" and i < len(transform_data["scale"]):
                            cmds.setAttr(full_attr, transform_data["scale"][i])
                
                applied_count += 1
            except Exception as e:
                print(f"Error applying transforms to {target_obj}: {str(e)}")
        
        status_msg = f"Applied transform values to {applied_count} controllers"
        if skipped_attrs > 0:
            status_msg += f" (skipped {skipped_attrs} locked/hidden attributes)"
        if skipped_objects > 0:
            status_msg += f" (couldn't find {skipped_objects} objects)"
        self.update_status(status_msg)
    
    def update_status(self, message):
        """Update the status field with a message"""
        cmds.textField(self.status_field, edit=True, text=message)
        print(message)

# Create and show the UI
transform_manager = TransformManager()