import maya.cmds as cmds
import maya.api.OpenMaya as om

class VertexTransferTool:
    def __init__(self):
        self.stored_points = None
        self.window_name = "vertexTransferUI"
        self.create_ui()
    
    def create_ui(self):
        # Delete window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # Create window
        window = cmds.window(self.window_name, title="Vertex Transfer Tool", width=150)
        
        # Create main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnOffset=["both", 5])
        
        # Add instructions
        cmds.text(label="Instructions:", align="left", font="boldLabelFont")
        cmds.text(label="1. Select source mesh and click 'Get Vertex Positions'", align="left", wordWrap=True)
        cmds.text(label="2. Select target mesh and click 'Set Vertex Positions'", align="left", wordWrap=True)
        cmds.text(label="3. Use the slider to control interpolation amount", align="left", wordWrap=True)
        
        cmds.separator(height=10, style='double')
        
        # Add interpolation slider
        cmds.text(label="Interpolation Amount:", align="left")
        self.interpolation_slider = cmds.floatSliderGrp(
            field=True,
            minValue=0.0,
            maxValue=1.0,
            value=1.0,
            step=0.1,
            precision=2
        )
        
        cmds.separator(height=10, style='in')
        
        # Fixed width for both buttons
        button_width = 280
        
        # Create buttons with fixed width
        self.create_3d_button(
            label="Get Vertex Positions",
            command=self.get_vertex_positions,
            base_color=[0.2, 0.6, 1.0],
            width=button_width,
            height=40
        )
        
        # Add spacing between buttons
        cmds.separator(height=5, style='none')
        
        self.create_3d_button(
            label="Set Vertex Positions",
            command=self.set_vertex_positions,
            base_color=[0.3, 0.8, 0.3],
            width=button_width,
            height=40
        )
        
        # Add spacing before progress bar
        cmds.separator(height=10, style='none')
        
        # Add progress bar
        self.progress_bar = cmds.progressBar(
            maxValue=100,
            width=button_width,
            visible=False
        )
        
        # Add spacing before status text
        cmds.separator(height=10, style='none')
        
        # Add status text with fixed width
        self.status_text = cmds.text(
            label="Status: Ready", 
            align="left",
            width=button_width
        )
        
        # Add final spacing at bottom
        cmds.separator(height=10, style='none')
        
        # Show window
        cmds.showWindow(window)
    
    def create_3d_button(self, label, command, base_color, width, height):
        """Create a button with 3D appearance and fixed width"""
        # Calculate highlight and shadow colors
        highlight_color = [min(c * 1.3, 1.0) for c in base_color]
        shadow_color = [c * 0.7 for c in base_color]
        
        # Create button frame with fixed width
        frame = cmds.frameLayout(labelVisible=False, borderVisible=False, width=width)
        form = cmds.formLayout(width=width)
        
        # Create main button
        btn = cmds.button(
            label=label,
            command=command,
            height=height,
            backgroundColor=base_color,
            width=width-2  # Accommodate shadow
        )
        
        # Create highlight and shadow effect
        highlight = cmds.button(
            height=2,
            backgroundColor=highlight_color,
            enable=False,
            width=width-2  # Accommodate shadow
        )
        
        shadow = cmds.button(
            width=2,
            backgroundColor=shadow_color,
            enable=False,
            height=height
        )
        
        # Position elements
        cmds.formLayout(
            form,
            edit=True,
            attachForm=[
                (btn, 'left', 0),
                (btn, 'top', 0),
                (btn, 'right', 2),
                (btn, 'bottom', 2),
                (highlight, 'left', 0),
                (highlight, 'top', 0),
                (highlight, 'right', 2),
                (shadow, 'right', 0),
                (shadow, 'top', 0),
                (shadow, 'bottom', 2),
            ]
        )
        
        cmds.setParent('..')  # Exit form
        cmds.setParent('..')  # Exit frame
        
        return btn

    # [Rest of the class methods remain the same]
    def update_progress(self, progress, total):
        percentage = int((progress / total) * 100)
        cmds.progressBar(self.progress_bar, edit=True, progress=percentage)
        cmds.refresh()
    
    def get_vertex_positions(self, *args):
        try:
            sel = cmds.ls(sl=True)
            if not sel:
                self.update_status("Error: Please select a mesh", error=True)
                return
            
            cmds.progressBar(self.progress_bar, edit=True, visible=True, progress=0)
            
            selection_list = om.MSelectionList()
            selection_list.add(sel[0])
            dag_path = selection_list.getDagPath(0)
            
            mfn_mesh = om.MFnMesh(dag_path)
            self.stored_points = mfn_mesh.getPoints()
            
            self.source_mesh = sel[0]
            
            self.update_status(f"Vertex positions stored from: {sel[0]}")
            
            cmds.progressBar(self.progress_bar, edit=True, visible=False)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", error=True)
            cmds.progressBar(self.progress_bar, edit=True, visible=False)
    
    def interpolate_points(self, original_points, target_points, weight):
        result_points = []
        for i in range(len(original_points)):
            orig = original_points[i]
            target = target_points[i]
            x = orig.x + (target.x - orig.x) * weight
            y = orig.y + (target.y - orig.y) * weight
            z = orig.z + (target.z - orig.z) * weight
            result_points.append(om.MPoint(x, y, z))
        return result_points
    
    def set_vertex_positions(self, *args):
        try:
            if self.stored_points is None:
                self.update_status("Error: No vertex positions stored. Get positions first.", error=True)
                return
            
            sel = cmds.ls(sl=True)
            if not sel:
                self.update_status("Error: Please select a target mesh", error=True)
                return
            
            cmds.progressBar(self.progress_bar, edit=True, visible=True, progress=0)
            
            selection_list = om.MSelectionList()
            selection_list.add(sel[0])
            dag_path = selection_list.getDagPath(0)
            mfn_mesh = om.MFnMesh(dag_path)
            
            if mfn_mesh.numVertices != len(self.stored_points):
                self.update_status("Error: Vertex count doesn't match source mesh", error=True)
                return
            
            original_points = mfn_mesh.getPoints()
            weight = cmds.floatSliderGrp(self.interpolation_slider, query=True, value=True)
            
            self.update_progress(25, 100)
            interpolated_points = self.interpolate_points(original_points, self.stored_points, weight)
            
            self.update_progress(75, 100)
            mfn_mesh.setPoints(interpolated_points)
            
            self.update_status(f"Vertex positions applied to: {sel[0]} (Interpolation: {weight*100}%)")
            
            cmds.progressBar(self.progress_bar, edit=True, visible=False)
            
        except Exception as e:
            self.update_status(f"Error: {str(e)}", error=True)
            cmds.progressBar(self.progress_bar, edit=True, visible=False)
    
    def update_status(self, message, error=False):
        if error:
            cmds.text(self.status_text, edit=True, label=f"Status: {message}", backgroundColor=[0.8, 0.3, 0.3])
        else:
            cmds.text(self.status_text, edit=True, label=f"Status: {message}", backgroundColor=[0.3, 0.6, 0.3])

# Create and show the UI
tool = VertexTransferTool()