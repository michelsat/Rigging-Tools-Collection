import maya.cmds as cmds

class MeshSelectionTransferTool:
    def __init__(self):
        self.window_name = "meshSelectionTransferTool"
        self.source_mesh = ""
        self.target_mesh = ""
        self.component_type = "vertex"
        self.source_count = 0
        self.target_count = 0
        self.create_ui()
        
    def create_ui(self):
        # Delete window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name, window=True)
            
        # Create window
        cmds.window(self.window_name, title="Mesh Component Selection Tool", width=300)
        
        # Create main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAttach=("both", 5))
        
        # Mesh selection section
        cmds.frameLayout(label="Mesh Setup", collapsable=False, marginWidth=5, marginHeight=5)
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 130, 50), adjustableColumn=2)
        cmds.text(label="Source Mesh:")
        self.source_mesh_field = cmds.textField(editable=False)
        cmds.button(label="Set", command=self.set_source_mesh)
        cmds.setParent('..')
        
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 130, 50), adjustableColumn=2)
        cmds.text(label="Target Mesh:")
        self.target_mesh_field = cmds.textField(editable=False)
        cmds.button(label="Set", command=self.set_target_mesh)
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        # Component type selection
        cmds.frameLayout(label="Component Type", collapsable=False, marginWidth=5, marginHeight=5)
        
        cmds.radioButtonGrp(
            "componentTypeRadio", 
            label="Select by:",
            labelArray3=["Vertex", "Edge", "Face"],
            numberOfRadioButtons=3,
            select=1,
            onCommand1=lambda *args: self.set_component_type("vertex"),
            onCommand2=lambda *args: self.set_component_type("edge"),
            onCommand3=lambda *args: self.set_component_type("face"),
            columnWidth=[(1, 80), (2, 70), (3, 70), (4, 70)]
        )
        
        cmds.setParent('..')
        
        # Count display section
        cmds.frameLayout(label="Selection Count", collapsable=False, marginWidth=5, marginHeight=5)
        
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(150, 150))
        cmds.columnLayout()
        cmds.text(label="Source Components:")
        self.source_count_field = cmds.text(label="0", align="left", font="boldLabelFont")
        cmds.setParent('..')
        
        cmds.columnLayout()
        cmds.text(label="Target Components:")
        self.target_count_field = cmds.text(label="0", align="left", font="boldLabelFont")
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.setParent('..')
        
        # Action buttons
        cmds.button(label="Select", command=self.transfer_selection, 
                   backgroundColor=[1, 0.6, 0.2], height=40)
        
        # Help section
        cmds.frameLayout(label="Help", collapsable=True, collapse=True, marginWidth=5, marginHeight=5)
        cmds.text(align="left", label="1. Set source and target meshes\n"
                                    "2. Choose component type\n"
                                    "3. Select components on source mesh\n"
                                    "4. Click 'Transfer Selection' to apply\n"
                                    "   the same selection to target mesh")
        cmds.setParent('..')
        
        # Show window
        cmds.showWindow(self.window_name)
        
    def set_source_mesh(self, *args):
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning("Nothing selected. Please select a mesh.")
            return
            
        # Check if the selection is a mesh
        shapes = cmds.listRelatives(selection[0], shapes=True)
        if shapes and cmds.objectType(shapes[0]) == "mesh":
            self.source_mesh = selection[0]
            cmds.textField(self.source_mesh_field, edit=True, text=self.source_mesh)
            self.update_counts()
        else:
            cmds.warning("Please select a mesh object.")
            
    def set_target_mesh(self, *args):
        selection = cmds.ls(selection=True)
        if not selection:
            cmds.warning("Nothing selected. Please select a mesh.")
            return
            
        # Check if the selection is a mesh
        shapes = cmds.listRelatives(selection[0], shapes=True)
        if shapes and cmds.objectType(shapes[0]) == "mesh":
            self.target_mesh = selection[0]
            cmds.textField(self.target_mesh_field, edit=True, text=self.target_mesh)
            self.update_counts()
        else:
            cmds.warning("Please select a mesh object.")
            
    def set_component_type(self, component_type):
        self.component_type = component_type
        self.update_counts()
        
        # Update the UI to show the corresponding Maya component syntax
        suffix = ""
        if component_type == "vertex":
            suffix = ".vtx[#]"
        elif component_type == "edge":
            suffix = ".e[#]"
        else:  # face
            suffix = ".f[#]"
        
        # Update UI to reflect selected component type
        try:
            cmds.radioButtonGrp("componentTypeRadio", edit=True, 
                               select={"vertex": 1, "edge": 2, "face": 3}[component_type])
        except:
            pass
    
    def update_counts(self):
        """Update the count display in the UI"""
        # Update source count
        if self.source_mesh:
            source_components = cmds.ls(selection=True, flatten=True)
            source_components = [comp for comp in source_components if self.source_mesh in comp]
            self.source_count = len(source_components)
        else:
            self.source_count = 0
            
        # Update target count
        if self.target_mesh:
            target_components = cmds.ls(selection=True, flatten=True)
            target_components = [comp for comp in target_components if self.target_mesh in comp]
            self.target_count = len(target_components)
        else:
            self.target_count = 0
            
        # Update UI
        cmds.text(self.source_count_field, edit=True, label=str(self.source_count))
        cmds.text(self.target_count_field, edit=True, label=str(self.target_count))
        
    def transfer_selection(self, *args):
        # Check if all required fields are set
        if not self.source_mesh or not self.target_mesh:
            cmds.warning("Please set both source and target meshes.")
            return
            
        # Get current selection
        selection = cmds.ls(selection=True, flatten=True)
        if not selection:
            cmds.warning("Nothing selected. Please select components on the source mesh.")
            return
            
        # Store the original source components for later selection
        original_source_components = [comp for comp in selection if self.source_mesh in comp]
            
        # Check if the selection contains components from our source mesh
        source_components = []
        for comp in selection:
            if self.source_mesh in comp or (len(selection) > 0 and len(comp.split('.')) == 1):
                source_components.append(comp)
                
        if not source_components:
            # Try to convert the selection to the correct component type
            try:
                # Convert to the mesh's vertices, edges, or faces
                if self.component_type == "vertex":
                    converted = cmds.polyListComponentConversion(selection, toVertex=True)
                elif self.component_type == "edge":
                    converted = cmds.polyListComponentConversion(selection, toEdge=True)
                else:  # face
                    converted = cmds.polyListComponentConversion(selection, toFace=True)
                
                if converted:
                    source_components = cmds.ls(converted, flatten=True)
            except:
                pass
                
        if not source_components:
            cmds.warning(f"No components from {self.source_mesh} selected. Please select components on the source mesh.")
            return
            
        # Get component indices
        component_indices = self.get_component_indices(source_components)
        if not component_indices:
            # Try using Maya's polyListComponentConversion command to convert the selection
            try:
                if self.component_type == "vertex":
                    converted = cmds.polyListComponentConversion(selection, toVertex=True)
                    flattened = cmds.ls(converted, flatten=True)
                    component_indices = self.get_component_indices(flattened)
                elif self.component_type == "edge":
                    converted = cmds.polyListComponentConversion(selection, toEdge=True)
                    flattened = cmds.ls(converted, flatten=True)
                    component_indices = self.get_component_indices(flattened)
                else:  # face
                    converted = cmds.polyListComponentConversion(selection, toFace=True)
                    flattened = cmds.ls(converted, flatten=True)
                    component_indices = self.get_component_indices(flattened)
            except:
                pass
                
        if not component_indices:
            cmds.warning(f"No valid {self.component_type} components found in selection.")
            return
            
        # Create target components
        if self.component_type == "vertex":
            comp_type = "vtx"
        elif self.component_type == "edge":
            comp_type = "e"
        else:
            comp_type = "f"
            
        target_components = [f"{self.target_mesh}.{comp_type}[{idx}]" for idx in component_indices]
        
        # Apply selection to target mesh AND keep source components selected
        cmds.select(original_source_components + target_components, replace=True)
        
        # Update counts
        self.source_count = len(original_source_components)
        self.target_count = len(target_components)
        cmds.text(self.source_count_field, edit=True, label=str(self.source_count))
        cmds.text(self.target_count_field, edit=True, label=str(self.target_count))
            
        print(f"Successfully transferred {len(component_indices)} {self.component_type} components to {self.target_mesh}")
    
    def get_component_indices(self, components):
        """Extract component indices from the component names"""
        indices = []
        
        # Convert selection to specific component type if necessary
        component_selection = []
        
        # Handle standard component naming (.vtx[], .e[], .f[])
        component_map = {
            "vertex": ["vtx", "verts", "vertices", "vtxs", "vertex"],
            "edge": ["e", "edge", "edges"],
            "face": ["f", "face", "faces", "facet", "facets"]
        }
        
        component_aliases = component_map[self.component_type]
        
        for comp in components:
            # Handle different ways Maya might report the selection
            for alias in component_aliases:
                if alias in comp:
                    component_selection.append(comp)
                    break
            
            # If not found by alias, add if it matches the main component type
            if self.component_type in comp and comp not in component_selection:
                component_selection.append(comp)
        
        # Try to convert the selection to component indices
        if not component_selection:
            # Try to convert the entire selection to the specified component type
            try:
                converted = cmds.ls(components, flatten=True, type=f"{self.component_type}s")
                if converted:
                    component_selection = converted
            except:
                pass
                
        # Extract indices from components
        for comp in component_selection:
            # Extract indices using regex pattern matching for any component format
            if '[' in comp and ']' in comp:
                index_str = comp.split('[')[1].split(']')[0]
                # Handle multiple indices like [1:3]
                if ':' in index_str:
                    try:
                        start, end = map(int, index_str.split(':'))
                        indices.extend(range(start, end+1))
                    except ValueError:
                        # Handle more complex ranges like [1:3][4:6]
                        pass
                else:
                    try:
                        indices.append(int(index_str))
                    except ValueError:
                        # Handle non-integer indices
                        pass
                        
        # If still no indices found, try direct conversion using Maya commands
        if not indices and components:
            try:
                # Get the mesh from the first component
                mesh_name = components[0].split('.')[0]
                
                # Convert the component type to Maya's internal format
                component_flag = ""
                if self.component_type == "vertex":
                    component_flag = "vtx"
                elif self.component_type == "edge":
                    component_flag = "e"
                elif self.component_type == "face":
                    component_flag = "f"
                
                # Try to convert using the flattened selection
                converted = cmds.ls(f"{mesh_name}.{component_flag}[*]", selection=True, flatten=True)
                
                # Extract indices from the converted components
                for comp in converted:
                    if '[' in comp and ']' in comp:
                        index_str = comp.split('[')[1].split(']')[0]
                        try:
                            indices.append(int(index_str))
                        except ValueError:
                            pass
            except:
                pass
                
        return indices

# Function to create the tool
def launch_selection_transfer_tool():
    return MeshSelectionTransferTool()

# Run the tool when the script is executed
if __name__ == "__main__":
    launch_selection_transfer_tool()