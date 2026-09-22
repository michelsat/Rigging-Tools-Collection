import maya.cmds as cmds

def select_joints_in_hierarchy(root_joints):
    all_joints = []
    for root_joint in root_joints:
        descendants = cmds.listRelatives(root_joint, allDescendents=True, type='joint') or []
        all_joints.append(root_joint)
        all_joints.extend(descendants)
    cmds.select(all_joints)

# Usage: Select the root joints first, then call the function
root_joints = cmds.ls(selection=True)
select_joints_in_hierarchy(root_joints)
