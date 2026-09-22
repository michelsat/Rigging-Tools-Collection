import maya.cmds as cmds

def select_deform_joints():
    # Get the selected mesh
    selected_mesh = cmds.ls(selection=True)
    if not selected_mesh:
        cmds.warning("Please select a skinned mesh.")
        return
    
    # Find the skinCluster associated with the selected mesh
    skin_cluster = cmds.ls(cmds.listHistory(selected_mesh), type='skinCluster')
    if not skin_cluster:
        cmds.warning("Selected mesh is not skinned.")
        return
    
    # Get the influence joints of the skinCluster
    influence_joints = cmds.skinCluster(skin_cluster[0], query=True, influence=True)
    
    # Select the influence joints
    cmds.select(influence_joints, replace=True)
    print("Selected deform joints: ", influence_joints)

# Run the function
select_deform_joints()
