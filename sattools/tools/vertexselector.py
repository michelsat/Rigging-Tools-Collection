import maya.cmds as cmds

def select_vertices(*args):
    """Select vertices based on user input with error handling"""
    # Get mesh name from field or selection
    mesh_name = cmds.textField("meshField", query=True, text=True).strip()
    
    if not mesh_name:
        # Get transform node from selection
        selection = cmds.ls(selection=True, transforms=True)
        if not selection:
            cmds.warning("Please select an object or enter mesh name")
            return
        mesh_name = selection[0]
    
    vertex_ids_input = cmds.textField("idField", query=True, text=True).strip()
    
    if not vertex_ids_input:
        cmds.warning("Please enter vertex IDs")
        return
    
    try:
        vertex_ids = [int(vtx.strip()) for vtx in vertex_ids_input.split(",") if vtx.strip()]
        if not vertex_ids:
            cmds.warning("No valid vertex IDs found")
            return
            
        if not cmds.objExists(mesh_name):
            cmds.warning(f"Object '{mesh_name}' not found")
            return
            
        vertex_names = [f"{mesh_name}.vtx[{vtx_id}]" for vtx_id in vertex_ids]
        cmds.select(vertex_names)
        print(f"Selected {len(vertex_names)} vertices on {mesh_name}")
        
    except ValueError:
        cmds.warning("Invalid vertex IDs - use numbers separated by commas")

def get_selected_mesh(*args):
    """Get the currently selected transform node name"""
    selection = cmds.ls(selection=True, transforms=True)
    if selection:
        mesh_name = selection[0]
        cmds.textField("meshField", edit=True, text=mesh_name)
    else:
        cmds.warning("Please select an object in the viewport first")

# Create UI
window_name = "vertexSelectorUI"
if cmds.window(window_name, exists=True):
    cmds.deleteUI(window_name)
    
cmds.window(window_name, title="Vertex Selector", width=300)
cmds.columnLayout(adjustableColumn=True, rowSpacing=10)

# Mesh Selection Row
cmds.rowLayout(numberOfColumns=2, columnWidth2=(70, 200))
cmds.button(label="Get Selected", command=get_selected_mesh, width=70)
cmds.textField("meshField", placeholderText="Select object or type name")
cmds.setParent("..")  # Go back to columnLayout

# Vertex IDs
cmds.text(label="Vertex IDs (comma-separated):")
cmds.textField("idField", placeholderText="0,1,2,3")

# Select Button
cmds.button(label="Select Vertices", command=select_vertices, height=30)

cmds.showWindow(window_name)