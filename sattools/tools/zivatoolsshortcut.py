"""
Maya Ziva Tools UI
A minimal utility script that provides buttons to call Ziva's built-in functionality
"""

import maya.cmds as cmds
import maya.mel as mel


class ZivaTissueUI:
    """UI for enabling/disabling Ziva tissue nodes"""
    
    def __init__(self):
        self.window_name = "zivaTissueUI"
        self.tissue_list = []
        
    def create_ui(self):
        """Create the main UI window"""
        
        # Delete existing window if it exists
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # Create window
        self.window_name = cmds.window(
            self.window_name,
            title="Ziva Tissue Enable/Disable",
            widthHeight=(400, 500),
            sizeable=True
        )
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)
        
        # Title
        cmds.text(label="Ziva Tissue Manager", font="boldLabelFont", height=30)
        cmds.separator(height=10)
        
        # Refresh and Debug buttons
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 195), (2, 195)])
        
        cmds.button(
            label="Refresh List",
            command=lambda x: self.refresh_tissue_list(),
            backgroundColor=[0.3, 0.5, 0.7]
        )
        
        cmds.button(
            label="Debug Selection",
            command=lambda x: self.debug_viewport_selection(),
            backgroundColor=[0.7, 0.5, 0.3],
            annotation="Check what's selected in viewport"
        )
        
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Tissue list with scroll
        cmds.text(label="Select Tissues:", align="left")
        self.tissue_scroll_list = cmds.textScrollList(
            numberOfRows=12,
            allowMultiSelection=True,
            selectCommand=lambda: self.update_selection_info()
        )
        
        # Selection info
        self.selection_info = cmds.text(label="No tissues selected", align="left", height=20)
        
        cmds.separator(height=10)
        
        # Buttons for selected tissues
        cmds.text(label="Selected Tissues:", align="left", font="boldLabelFont")
        cmds.rowColumnLayout(numberOfColumns=3, columnWidth=[(1, 130), (2, 130), (3, 130)])
        
        cmds.button(
            label="Enable Selected",
            command=lambda x: self.enable_selected_tissues(),
            annotation="Works with UI selection OR viewport selection",
            backgroundColor=[0.3, 0.7, 0.3]
        )
        
        cmds.button(
            label="Disable Selected",
            command=lambda x: self.disable_selected_tissues(),
            annotation="Works with UI selection OR viewport selection",
            backgroundColor=[0.7, 0.3, 0.3]
        )
        
        cmds.button(
            label="Toggle Selected",
            command=lambda x: self.toggle_selected_tissues(),
            annotation="Works with UI selection OR viewport selection",
            backgroundColor=[0.5, 0.5, 0.7]
        )
        
        cmds.setParent('..')
        
        cmds.separator(height=15)
        
        # Buttons for all tissues
        cmds.text(label="All Tissues:", align="left", font="boldLabelFont")
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 195), (2, 195)])
        
        cmds.button(
            label="Enable All",
            command=lambda x: self.enable_all_tissues(),
            backgroundColor=[0.3, 0.7, 0.3]
        )
        
        cmds.button(
            label="Disable All",
            command=lambda x: self.disable_all_tissues(),
            backgroundColor=[0.7, 0.3, 0.3]
        )
        
        cmds.setParent('..')
        
        cmds.separator(height=15)
        
        # Filter options
        cmds.text(label="Filter by Pattern:", align="left", font="boldLabelFont")
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 280), (2, 110)])
        
        self.pattern_field = cmds.textField(placeholderText="e.g., *trapezius*")
        
        cmds.button(
            label="Filter",
            command=lambda x: self.filter_tissues()
        )
        
        cmds.setParent('..')
        
        cmds.separator(height=10)
        
        # Status bar
        self.status_text = cmds.text(
            label="Ready",
            align="left",
            backgroundColor=[0.2, 0.2, 0.2],
            height=25
        )
        
        # Show window
        cmds.showWindow(self.window_name)
        
        # Initial refresh
        self.refresh_tissue_list()
    
    def refresh_tissue_list(self):
        """Refresh the list of Ziva tissues"""
        
        # Clear current list
        cmds.textScrollList(self.tissue_scroll_list, edit=True, removeAll=True)
        
        # Get all tissues
        self.tissue_list = cmds.ls(type='zTissue')
        
        if not self.tissue_list:
            self.update_status("No Ziva tissues found in scene")
            return
        
        # Add tissues to list with status indicators
        for tissue in self.tissue_list:
            try:
                enabled = cmds.getAttr(f"{tissue}.enable")
                status = "[ON]" if enabled else "[OFF]"
                display_name = f"{status} {tissue}"
                cmds.textScrollList(
                    self.tissue_scroll_list,
                    edit=True,
                    append=display_name
                )
            except:
                pass
        
        self.update_status(f"Found {len(self.tissue_list)} tissue(s)")
        self.update_selection_info()
    
    def get_selected_tissue_names(self):
        """Get the actual tissue names from selected items or viewport selection"""
        
        # First check UI selection
        selected_items = cmds.textScrollList(
            self.tissue_scroll_list,
            query=True,
            selectItem=True
        )
        
        if selected_items:
            # Remove status indicators to get actual names
            tissue_names = []
            for item in selected_items:
                # Remove "[ON]" or "[OFF]" prefix
                name = item.replace("[ON] ", "").replace("[OFF] ", "")
                tissue_names.append(name)
            return tissue_names
        
        # If no UI selection, check viewport selection
        viewport_selection = cmds.ls(selection=True, long=True)
        
        if not viewport_selection:
            return []
        
        # Find tissue nodes connected to selected objects
        tissue_names = []
        
        for obj in viewport_selection:
            # Check if object itself is a tissue node
            obj_type = cmds.objectType(obj)
            
            if obj_type == 'zTissue':
                tissue_names.append(obj)
                continue
            
            # Get the base name of the object (without path and suffixes)
            obj_short = obj.split('|')[-1]
            obj_base = obj_short.replace('_grp', '').replace('Shape', '').replace('Orig', '')
            
            # Check history for tissue nodes
            history = cmds.listHistory(obj)
            if history:
                tissues = cmds.ls(history, type='zTissue')
                if tissues:
                    # Filter to get ONLY the tissue that matches this specific mesh
                    for tissue in tissues:
                        # Check if tissue name starts with the object base name
                        # e.g., r_bicep_muscle should match r_bicep_muscle_zTissue
                        if tissue.startswith(obj_base):
                            tissue_names.append(tissue)
                            print(f"Matched tissue: {tissue} for object: {obj_base}")
                            break  # Only get the first matching tissue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tissues = []
        for tissue in tissue_names:
            if tissue not in seen:
                seen.add(tissue)
                unique_tissues.append(tissue)
        
        return unique_tissues
    
    def update_selection_info(self):
        """Update the selection info text"""
        
        selected = self.get_selected_tissue_names()
        count = len(selected)
        
        if count == 0:
            cmds.text(self.selection_info, edit=True, label="No tissues selected (UI or Viewport)")
        else:
            # Check if selection is from UI or viewport
            ui_selection = cmds.textScrollList(
                self.tissue_scroll_list,
                query=True,
                selectItem=True
            )
            source = "UI" if ui_selection else "Viewport"
            cmds.text(self.selection_info, edit=True, label=f"{count} tissue(s) selected ({source})")
    
    def enable_selected_tissues(self):
        """Enable selected tissues"""
        
        selected = self.get_selected_tissue_names()
        
        if not selected:
            self.update_status("No tissues selected in UI or Viewport")
            return
        
        count = 0
        for tissue in selected:
            try:
                cmds.setAttr(f"{tissue}.enable", 1)
                count += 1
                print(f"Enabled: {tissue}")
            except Exception as e:
                print(f"Failed to enable {tissue}: {str(e)}")
        
        self.update_status(f"Enabled {count} tissue(s)")
        self.refresh_tissue_list()
    
    def disable_selected_tissues(self):
        """Disable selected tissues"""
        
        selected = self.get_selected_tissue_names()
        
        if not selected:
            self.update_status("No tissues selected in UI or Viewport")
            return
        
        count = 0
        for tissue in selected:
            try:
                cmds.setAttr(f"{tissue}.enable", 0)
                count += 1
                print(f"Disabled: {tissue}")
            except Exception as e:
                print(f"Failed to disable {tissue}: {str(e)}")
        
        self.update_status(f"Disabled {count} tissue(s)")
        self.refresh_tissue_list()
    
    def toggle_selected_tissues(self):
        """Toggle selected tissues"""
        
        selected = self.get_selected_tissue_names()
        
        if not selected:
            self.update_status("No tissues selected in UI or Viewport")
            return
        
        count = 0
        for tissue in selected:
            try:
                current = cmds.getAttr(f"{tissue}.enable")
                cmds.setAttr(f"{tissue}.enable", not current)
                count += 1
                state = "enabled" if not current else "disabled"
                print(f"{tissue}: {state}")
            except Exception as e:
                print(f"Failed to toggle {tissue}: {str(e)}")
        
        self.update_status(f"Toggled {count} tissue(s)")
        self.refresh_tissue_list()
    
    def enable_all_tissues(self):
        """Enable all tissues in the list"""
        
        if not self.tissue_list:
            self.update_status("No tissues found")
            return
        
        count = 0
        for tissue in self.tissue_list:
            try:
                cmds.setAttr(f"{tissue}.enable", 1)
                count += 1
            except Exception as e:
                print(f"Failed to enable {tissue}: {str(e)}")
        
        self.update_status(f"Enabled all {count} tissue(s)")
        self.refresh_tissue_list()
    
    def disable_all_tissues(self):
        """Disable all tissues in the list"""
        
        if not self.tissue_list:
            self.update_status("No tissues found")
            return
        
        count = 0
        for tissue in self.tissue_list:
            try:
                cmds.setAttr(f"{tissue}.enable", 0)
                count += 1
            except Exception as e:
                print(f"Failed to disable {tissue}: {str(e)}")
        
        self.update_status(f"Disabled all {count} tissue(s)")
        self.refresh_tissue_list()
    
    def filter_tissues(self):
        """Filter tissues by pattern"""
        
        pattern = cmds.textField(self.pattern_field, query=True, text=True)
        
        if not pattern:
            self.refresh_tissue_list()
            return
        
        # Clear current list
        cmds.textScrollList(self.tissue_scroll_list, edit=True, removeAll=True)
        
        # Filter tissues
        filtered = cmds.ls(pattern, type='zTissue')
        
        if not filtered:
            self.update_status(f"No tissues match pattern: {pattern}")
            return
        
        # Add filtered tissues to list
        for tissue in filtered:
            try:
                enabled = cmds.getAttr(f"{tissue}.enable")
                status = "[ON]" if enabled else "[OFF]"
                display_name = f"{status} {tissue}"
                cmds.textScrollList(
                    self.tissue_scroll_list,
                    edit=True,
                    append=display_name
                )
            except:
                pass
        
        self.tissue_list = filtered
        self.update_status(f"Filtered: {len(filtered)} tissue(s) match '{pattern}'")
    
    def update_status(self, message):
        """Update status bar message"""
        cmds.text(self.status_text, edit=True, label=message)
        print(message)
    
    def debug_viewport_selection(self):
        """Debug tool to check viewport selection and find tissue connections"""
        
        viewport_selection = cmds.ls(selection=True, long=True)
        
        if not viewport_selection:
            self.update_status("Nothing selected in viewport")
            print("\n=== DEBUG: No viewport selection ===\n")
            return
        
        print("\n" + "="*60)
        print("DEBUG: VIEWPORT SELECTION ANALYSIS")
        print("="*60)
        
        for obj in viewport_selection:
            print(f"\n>>> Object: {obj}")
            print(f"    Type: {cmds.objectType(obj)}")
            
            # Check shapes
            shapes = cmds.listRelatives(obj, shapes=True, fullPath=True)
            print(f"    Shapes: {shapes}")
            
            # Check ALL connections
            print("\n    ALL Connections:")
            all_conn = cmds.listConnections(obj, plugs=True, connections=True)
            if all_conn:
                for i in range(0, len(all_conn), 2):
                    print(f"      {all_conn[i]} -> {all_conn[i+1]}")
            
            # Check for zTissue specifically
            print("\n    zTissue nodes found:")
            
            # Method 1: Direct connections
            tissues_all = cmds.listConnections(obj, type='zTissue')
            if tissues_all:
                print(f"      Direct: {tissues_all}")
            
            # Method 2: Source only
            tissues_source = cmds.listConnections(obj, source=True, destination=False, type='zTissue')
            if tissues_source:
                print(f"      Source: {tissues_source}")
            
            # Method 3: Destination only
            tissues_dest = cmds.listConnections(obj, source=False, destination=True, type='zTissue')
            if tissues_dest:
                print(f"      Destination: {tissues_dest}")
            
            # Method 4: Check shape connections
            if shapes:
                for shape in shapes:
                    print(f"\n    Shape {shape} connections:")
                    shape_tissues = cmds.listConnections(shape, type='zTissue')
                    if shape_tissues:
                        print(f"      Found: {shape_tissues}")
                    
                    # Check shape plugs
                    shape_conn = cmds.listConnections(shape, plugs=True, connections=True, type='zTissue')
                    if shape_conn:
                        print(f"      Detailed connections:")
                        for i in range(0, len(shape_conn), 2):
                            print(f"        {shape_conn[i]} -> {shape_conn[i+1]}")
            
            # Method 5: History
            print("\n    History check:")
            history = cmds.listHistory(obj)
            history_tissues = cmds.ls(history, type='zTissue')
            if history_tissues:
                print(f"      In history: {history_tissues}")
            
            print("\n" + "-"*60)
        
        print("\n" + "="*60 + "\n")
        self.update_status("Debug info printed to Script Editor")


class ZivaToolsSimple:
    def __init__(self):
        self.window_name = "zivaToolsWindow"
        self.solver_node = None  # Will store the found zSolver node name
        self.create_ui()
        
    def create_ui(self):
        # Check if window exists and delete it
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
            
        # Create window
        cmds.window(self.window_name, title="Ziva Tools", width=300)
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=15, columnOffset=["both", 10])
        
        # Add header
        cmds.separator(height=10, style="none")
        cmds.text(label="ZIVA TOOLS", font="boldLabelFont")
        cmds.separator(height=20, style="in")
        
        # Solver toggle button
        self.solver_button = cmds.button(label="Solver: Checking...", 
                                        height=40,
                                        backgroundColor=[0.2, 0.2, 0.2],
                                        command=self.toggle_solver)
        
        # Find zSolver and update button on creation
        self.find_solver()
        self.update_solver_button()
        
        # Tissue Manager button
        cmds.button(label="Tissue Manager", 
                   height=40,
                   command=self.open_tissue_manager,
                   backgroundColor=[0.3, 0.6, 0.8],
                   annotation="Open Tissue Enable/Disable Manager")
        
        # ZTet Size Adjuster button
        cmds.button(label="ZTet Size Adjuster", 
                   height=40,
                   command=self.open_ztet_adjuster,
                   backgroundColor=[0.6, 0.4, 0.7],
                   annotation="Open ZTet Size Transfer Tool")
        
        # Rename button
        cmds.button(label="Rename Ziva Nodes", 
                   height=40,
                   command=self.rename_ziva_nodes, 
                   annotation="Calls zBuilder's rename_ziva_nodes() function")
        
        # Rivet button
        cmds.button(label="Create Rivet To Bone", 
                   height=40,
                   command=self.create_rivet_to_bone, 
                   annotation="Calls zRivetToBone MEL command")
        
        # Row layout for three buttons
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(100, 100, 100), adjustableColumn=2, columnAlign=(1, "center"))
        
        # Mesh Check button
        cmds.button(label="Mesh Check", 
                   width=100,
                   command=self.mesh_check, 
                   annotation="Calls zMeshCheck -select")
        
        # Select Intersections button  
        cmds.button(label="Intersections", 
                   width=100,
                   command=self.select_intersections, 
                   annotation="Calls ZivaSelectIntersections")
        
        # Select Self Intersections button
        cmds.button(label="Self Intersect", 
                   width=100,
                   command=self.select_self_intersections, 
                   annotation="Calls ZivaSelectSelfIntersections")
        
        cmds.setParent('..')  # Return to main layout
        cmds.separator(height=10)
        
        # Show window
        cmds.showWindow(self.window_name)
    
    def open_tissue_manager(self, *args):
        """Open the Tissue Manager UI"""
        tissue_ui = ZivaTissueUI()
        tissue_ui.create_ui()
    
    def open_ztet_adjuster(self, *args):
        """Open the ZTet Size Adjuster UI"""
        try:
            # Try to import from separate file first
            import ZTetSizeAdjuster
            adjuster = ZTetSizeAdjuster.ZTetSizeAdjuster()
            adjuster.create_ui()
        except ImportError:
            # If not found, try to import from same module
            try:
                adjuster = ZTetSizeAdjuster()
                adjuster.create_ui()
            except:
                cmds.warning("ZTetSizeAdjuster class not found. Make sure the script is loaded or in the same file.")
    
    def find_solver(self):
        """Find any zSolver node in the scene"""
        # First try: Look for nodes with enable attribute that start with zSolver
        all_nodes = cmds.ls()
        for node in all_nodes:
            if node.startswith("zSolver"):
                # Check if it has an enable attribute
                if cmds.attributeQuery("enable", node=node, exists=True):
                    self.solver_node = node
                    return True
        
        # Second try: use MEL to query the active solver
        try:
            # This might work if Ziva has a command to get the current solver
            result = mel.eval("zQuery -type zSolver")
            if result and len(result) > 0:
                self.solver_node = result[0]
                return True
        except:
            pass
            
        # No solver found
        self.solver_node = None
        return False
    
    def update_solver_button(self):
        """Update the solver toggle button appearance based on current state"""
        # Find solver if not already found
        if not self.solver_node:
            if not self.find_solver():
                cmds.button(self.solver_button, edit=True, 
                           label="No Solver Found", 
                           backgroundColor=[0.5, 0.5, 0.5],
                           enable=False)
                return
        
        # Get current solver state
        try:
            # Check if node exists
            if not cmds.objExists(self.solver_node):
                cmds.button(self.solver_button, edit=True, 
                           label="No Solver Found", 
                           backgroundColor=[0.5, 0.5, 0.5],
                           enable=False)
                self.solver_node = None
                return
                
            # Check if it has the enable attribute
            if not cmds.attributeQuery("enable", node=self.solver_node, exists=True):
                cmds.button(self.solver_button, edit=True, 
                           label=f"Invalid Solver ({self.solver_node})", 
                           backgroundColor=[0.7, 0.5, 0.0],
                           enable=False)
                return
                
            # Get the attribute value
            solver_enabled = cmds.getAttr(f"{self.solver_node}.enable")
            
            if solver_enabled:
                # Solver is ON
                cmds.button(self.solver_button, edit=True, 
                           label=f"Solver: ON", 
                           backgroundColor=[0.2, 0.7, 0.2],
                           enable=True)
            else:
                # Solver is OFF
                cmds.button(self.solver_button, edit=True, 
                           label=f"Solver: OFF", 
                           backgroundColor=[0.7, 0.2, 0.2],
                           enable=True)
        except Exception as e:
            # If can't get attribute, disable button
            cmds.warning(f"Error with solver: {str(e)}")
            cmds.button(self.solver_button, edit=True, 
                       label="Solver Error", 
                       backgroundColor=[0.7, 0.5, 0.0],
                       enable=False)
    
    def toggle_solver(self, *args):
        """Toggle the Ziva solver on/off"""
        try:
            # Re-check for solver in case it was created after UI
            if not self.solver_node:
                if not self.find_solver():
                    cmds.warning("No zSolver node found in the scene")
                    return
            
            # Check if solver still exists
            if not cmds.objExists(self.solver_node):
                cmds.warning(f"Solver node {self.solver_node} no longer exists")
                self.solver_node = None
                self.update_solver_button()
                return
                
            # Get current state
            current_state = cmds.getAttr(f"{self.solver_node}.enable")
            
            # Toggle state
            new_state = 0 if current_state else 1
            cmds.setAttr(f"{self.solver_node}.enable", new_state)
            
            # Update button appearance
            self.update_solver_button()
            
        except Exception as e:
            cmds.warning(f"Error toggling solver: {str(e)}")
            self.update_solver_button()
    
    def rename_ziva_nodes(self, *args):
        """Call Ziva's built-in rename function"""
        try:
            # Import zBuilder commands
            import zBuilder.commands as vfx_cmds
            
            # Call rename function
            vfx_cmds.rename_ziva_nodes()
            
        except ImportError:
            cmds.warning("Could not import zBuilder.commands. Make sure Ziva is properly installed.")
        except Exception as e:
            cmds.warning(f"Error calling rename_ziva_nodes(): {str(e)}")
    
    def create_rivet_to_bone(self, *args):
        """Call Ziva's built-in rivet function"""
        try:
            # Call zRivetToBone MEL command
            mel.eval("zRivetToBone")
            
        except Exception as e:
            cmds.warning(f"Error calling zRivetToBone: {str(e)}")
    
    def mesh_check(self, *args):
        """Call Ziva's mesh check function"""
        try:
            # Call zMeshCheck MEL command
            mel.eval("zMeshCheck -select")
            
        except Exception as e:
            cmds.warning(f"Error calling zMeshCheck: {str(e)}")
    
    def select_intersections(self, *args):
        """Call Ziva's select intersections function"""
        try:
            # Call ZivaSelectIntersections MEL command
            mel.eval("ZivaSelectIntersections")
            
        except Exception as e:
            cmds.warning(f"Error calling ZivaSelectIntersections: {str(e)}")
    
    def select_self_intersections(self, *args):
        """Call Ziva's select self intersections function"""
        try:
            # Call ZivaSelectSelfIntersections MEL command
            mel.eval("ZivaSelectSelfIntersections")
            
        except Exception as e:
            cmds.warning(f"Error calling ZivaSelectSelfIntersections: {str(e)}")


# Create instance of the UI
if __name__ == "__main__":
    ziva_tools = ZivaToolsSimple()