import maya.cmds as cmds

def reset_attributes(attr_type):
    selected = cmds.ls(selection=True)
    if not selected:
        cmds.warning("No object selected.")
        return

    for obj in selected:
        for axis in ['X', 'Y', 'Z']:
            attr = f"{obj}.{attr_type}{axis}"
            if cmds.getAttr(attr, lock=True):
                cmds.warning(f"{attr} is locked.")
                continue
            if attr_type == 'scale':
                cmds.setAttr(attr, 1)
            else:
                cmds.setAttr(attr, 0)

def create_ui():
    if cmds.window("resetUI", exists=True):
        cmds.deleteUI("resetUI", window=True)

    window = cmds.window("resetUI", title="Reset Attributes", widthHeight=(200, 100))
    cmds.columnLayout(adjustableColumn=True)
    cmds.button(label="Reset Translate", command=lambda *args: reset_attributes('translate'))
    cmds.button(label="Reset Rotate", command=lambda *args: reset_attributes('rotate'))
    cmds.button(label="Reset Scale", command=lambda *args: reset_attributes('scale'))
    cmds.showWindow(window)

create_ui()
