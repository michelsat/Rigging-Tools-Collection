import maya.cmds as cmds
import maya.api.OpenMaya as om

def create_joints_from_vertex_normals(mesh_name, selected_vertices=None, joint_length=1.0, prefix="vtx_jnt", create_single_joint=True):
    """
    Creates joints at selected vertices with orientation aligned to vertex normals.
    
    Parameters:
    mesh_name (str): Name of the mesh to use
    selected_vertices (list): List of vertex indices (if None, uses current selection)
    joint_length (float): Length of the joint chain segments
    prefix (str): Prefix for naming the created joints
    create_single_joint (bool): If True, creates only one joint per vertex; if False, creates parent-child joints
    
    Returns:
    list: List of created root joints
    """
    # Get the mesh's DAG path and create a function set for it
    selection_list = om.MSelectionList()
    selection_list.add(mesh_name)
    dag_path = selection_list.getDagPath(0)
    mesh = om.MFnMesh(dag_path)
    
    # Get selected vertices if not provided
    if selected_vertices is None:
        selected_vertices = []
        selected_components = cmds.ls(selection=True, flatten=True)
        for comp in selected_components:
            if ".vtx[" in comp:
                idx = int(comp.split('[')[-1].split(']')[0])
                selected_vertices.append(idx)
    
    # If nothing selected, inform the user
    if not selected_vertices:
        cmds.warning("No vertices selected. Please select vertices on the mesh.")
        return []
    
    created_joints = []
    
    # Store current parent to restore after operation
    current_parent = cmds.ls(selection=True, long=True)
    
    # Make sure we're not parenting under the mesh
    cmds.select(clear=True)
    
    # Create a joint for each selected vertex
    for i, vertex_id in enumerate(selected_vertices):
        # Get vertex position in world space
        point = mesh.getPoint(vertex_id, om.MSpace.kWorld)
        
        # Get vertex normal in world space
        normal = mesh.getVertexNormal(vertex_id, True, om.MSpace.kWorld)
        
        # Calculate the end position using the normal
        end_point = [
            point.x + normal.x * joint_length,
            point.y + normal.y * joint_length,
            point.z + normal.z * joint_length
        ]
        
        # Create a joint at the vertex position (not parented to mesh)
        cmds.select(clear=True)
        joint_name = f"{prefix}_{i:03d}"
        root_joint = cmds.joint(name=joint_name, position=[point.x, point.y, point.z])
        
        # Create a temporary locator to help calculate orientation
        temp_loc = cmds.spaceLocator()[0]
        cmds.xform(temp_loc, translation=end_point)
        
        # Create a temporary aim constraint to orient the joint
        constraint = cmds.aimConstraint(
            temp_loc, 
            root_joint, 
            aimVector=[1, 0, 0], 
            upVector=[0, 1, 0], 
            worldUpType="vector",
            worldUpVector=[0, 1, 0]
        )[0]
        
        # Delete the temporary nodes
        cmds.delete(constraint, temp_loc)
        
        # Create a child joint if requested
        if not create_single_joint:
            cmds.select(root_joint)
            child_joint = cmds.joint(
                name=f"{joint_name}_end",
                position=end_point
            )
        
        created_joints.append(root_joint)
    
    # Restore original selection
    if current_parent:
        cmds.select(current_parent)
    else:
        cmds.select(clear=True)
        
    return created_joints

def create_normal_joint_controls(mesh_name, joint_length=1.0, num_vertices=None, prefix="normal_jnt"):
    """
    Creates a UI for generating joints based on vertex normals
    """
    if cmds.window("normalJointsWindow", exists=True):
        cmds.deleteUI("normalJointsWindow")
    
    window = cmds.window("normalJointsWindow", title="Create Joints from Vertex Normals", width=300)
    
    # Column layout without the padding flag
    cmds.columnLayout(adjustableColumn=True, columnAlign="left", rowSpacing=5)
    
    # Add some spacing manually
    cmds.text(label="")
    
    # Mesh selection field
    cmds.text(label="Target Mesh:")
    mesh_field = cmds.textField(text=mesh_name if mesh_name else "")
    cmds.button(label="Get Selected Mesh", command=lambda x: cmds.textField(mesh_field, edit=True, text=cmds.ls(selection=True)[0] if cmds.ls(selection=True) else ""))
    
    cmds.separator(height=10, style="in")
    
    # Joint length field
    cmds.text(label="Joint Length:")
    length_field = cmds.floatField(value=joint_length, min=0.01, precision=3)
    
    cmds.separator(height=10, style="in")
    
    # Prefix field
    cmds.text(label="Joint Prefix:")
    prefix_field = cmds.textField(text=prefix)
    
    cmds.separator(height=10, style="in")
    
    # Joint type
    cmds.text(label="Joint Type:")
    joint_radio = cmds.radioCollection()
    single_joint_rb = cmds.radioButton(label="Single Joint (Oriented)", select=True)
    joint_chain_rb = cmds.radioButton(label="Joint Chain (Parent-Child)")
    
    cmds.separator(height=10, style="in")
    
    # Mode selection
    cmds.text(label="Create joints for:")
    mode_radio = cmds.radioCollection()
    selected_rb = cmds.radioButton(label="Selected Vertices", select=True)
    random_rb = cmds.radioButton(label="Random Vertices")
    
    # Random vertex count field
    cmds.text(label="Number of Random Vertices:")
    vertex_count_field = cmds.intField(value=num_vertices if num_vertices else 5, min=1)
    
    cmds.separator(height=15, style="in")
    
    # Create button
    cmds.button(label="Create Joints", 
               command=lambda x: execute_joint_creation(
                   cmds.textField(mesh_field, query=True, text=True),
                   cmds.floatField(length_field, query=True, value=True),
                   cmds.textField(prefix_field, query=True, text=True),
                   cmds.radioButton(selected_rb, query=True, select=True),
                   cmds.intField(vertex_count_field, query=True, value=True),
                   cmds.radioButton(single_joint_rb, query=True, select=True)
               ))
    
    cmds.showWindow(window)

def execute_joint_creation(mesh_name, joint_length, prefix, use_selection, random_count, create_single_joint):
    """Helper function to execute the joint creation based on UI input"""
    if not mesh_name or not cmds.objExists(mesh_name):
        cmds.warning("Please select a valid mesh")
        return
    
    if use_selection:
        # Create joints from selected vertices
        create_joints_from_vertex_normals(mesh_name, None, joint_length, prefix, create_single_joint)
    else:
        # Create joints from random vertices
        import random
        
        # Get total number of vertices in the mesh
        vertex_count = cmds.polyEvaluate(mesh_name, vertex=True)
        
        # Generate random vertex indices
        if random_count > vertex_count:
            random_count = vertex_count
            
        random_vertices = random.sample(range(vertex_count), random_count)
        create_joints_from_vertex_normals(mesh_name, random_vertices, joint_length, prefix, create_single_joint)

# Example usage:
# 1. Select vertices on a mesh and run:
# create_joints_from_vertex_normals("pSphere1", create_single_joint=True)
#
# 2. Or open the UI:
create_normal_joint_controls("")