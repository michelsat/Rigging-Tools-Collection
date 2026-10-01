import maya.cmds as cmds
import json

class RiggerSetupTool:
    def __init__(self):
        self.window_name = "RiggerSetupUI"
        self.network_node = "RigReset_Metadata"
        self.script_node_name = "RigReset_AutoLaunchNode"
        self.show_ui()

    def show_ui(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        cmds.window(self.window_name, title="Rig Reset Setup Tool", widthHeight=(360, 310), sizeable=False)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=8, columnAttach=('both', 20))

        cmds.separator(height=15, style="none")
        
        cmds.text(label="1. Rig Metadata", align="left", font="boldLabelFont")
        self.author_field = cmds.textFieldGrp(label="Author Name: ", text="Your Name", columnWidth2=(90, 210))
        self.version_field = cmds.textFieldGrp(label="Rig Version: ", text="1.0", columnWidth2=(90, 210))

        cmds.separator(height=10, style="in")
        
        cmds.text(label="2. Setup Instructions", align="left", font="boldLabelFont")
        cmds.text(label="  - Pose controllers in their default zero/rest state.", align="left")
        cmds.text(label="  - Select all the controllers in the viewport.", align="left")
        cmds.text(label="  - Click 'DONE' below to bake data and embed.", align="left")

        cmds.separator(height=15, style="none")

        cmds.button(label="DONE: Bake States and Embed UI", height=50, backgroundColor=(0.25, 0.65, 0.35), command=self.build_and_embed)

        cmds.separator(height=15, style="none")
        cmds.showWindow(self.window_name)

    def build_and_embed(self, *args):
        author = cmds.textFieldGrp(self.author_field, query=True, text=True)
        version = cmds.textFieldGrp(self.version_field, query=True, text=True)
        selection = cmds.ls(selection=True)

        if not selection:
            cmds.warning("Please select at least one controller before clicking Done.")
            return

        if not cmds.objExists(self.network_node):
            cmds.createNode("network", name=self.network_node)

        for attr in ["author", "version"]:
            if not cmds.attributeQuery(attr, node=self.network_node, exists=True):
                cmds.addAttr(self.network_node, longName=attr, dataType="string")
                
        cmds.setAttr(self.network_node + ".author", author, type="string")
        cmds.setAttr(self.network_node + ".version", version, type="string")

        if cmds.attributeQuery("rigControls", node=self.network_node, exists=True):
            cmds.deleteAttr(self.network_node + ".rigControls")
            
        cmds.addAttr(self.network_node, longName="rigControls", attributeType="message", multi=True)
        
        if not cmds.attributeQuery("resetData", node=self.network_node, exists=True):
            cmds.addAttr(self.network_node, longName="resetData", dataType="string")

        reset_data_list = []

        for i, ctrl in enumerate(selection):
            cmds.connectAttr(ctrl + ".message", self.network_node + ".rigControls[" + str(i) + "]", force=True)
            
            ctrl_defaults = {}
            keyable_attrs = cmds.listAttr(ctrl, keyable=True, unlocked=True) or []
            
            for attr in keyable_attrs:
                plug = ctrl + "." + attr
                try:
                    val = cmds.getAttr(plug)
                    if isinstance(val, (int, float, bool)):
                        ctrl_defaults[attr] = val
                except:
                    pass
            
            reset_data_list.append(ctrl_defaults)

        json_payload = json.dumps(reset_data_list)
        cmds.setAttr(self.network_node + ".resetData", json_payload, type="string")

        if cmds.objExists(self.script_node_name):
            cmds.delete(self.script_node_name)

        animator_payload = """import maya.cmds as cmds
import json
import __main__

def show_animator_ui(*args):
    win_name = "AnimatorRigResetUI"
    net_node = "RigReset_Metadata"
    
    if cmds.window(win_name, exists=True):
        cmds.deleteUI(win_name)
        
    if not cmds.objExists(net_node):
        cmds.warning("Rig Reset metadata node missing!")
        return
        
    author = cmds.getAttr(net_node + ".author") or "Unknown"
    version = cmds.getAttr(net_node + ".version") or "N/A"
    
    cmds.window(win_name, title="Rig Tools", widthHeight=(200, 130), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=10, columnAttach=('both', 10))
    
    cmds.separator(height=5, style="none")
    cmds.text(label="Author: " + author, font="boldLabelFont", align="center")
    cmds.text(label="Version: " + version, align="center")
    cmds.separator(height=5, style="in")
    
    cmds.button(label="Reset Rig Controls", height=35, backgroundColor=(0.2, 0.4, 0.6), command=lambda x: __main__.do_reset(net_node))
    cmds.showWindow(win_name)

def do_reset(net_node):
    if not cmds.attributeQuery("resetData", node=net_node, exists=True):
        cmds.warning("No baked default states found!")
        return
        
    json_data = cmds.getAttr(net_node + ".resetData")
    try:
        reset_data_list = json.loads(json_data)
    except:
        cmds.warning("Could not read reset data.")
        return
        
    indices = cmds.getAttr(net_node + ".rigControls", multiIndices=True) or []
    reset_count = 0
    
    for i in indices:
        connections = cmds.listConnections(net_node + ".rigControls[" + str(i) + "]", source=True, destination=False)
        if not connections:
            continue
            
        ctrl = connections[0]
        
        if i < len(reset_data_list):
            defaults = reset_data_list[i]
            for attr, default_val in defaults.items():
                plug = ctrl + "." + attr
                try:
                    if cmds.getAttr(plug, settable=True) and not cmds.listConnections(plug, destination=False):
                        cmds.setAttr(plug, default_val)
                        reset_count += 1
                except:
                    pass
                    
    cmds.inViewMessage(amg="<hl>Rig Reset Complete!</hl>", pos='midCenter', fade=True)

__main__.show_animator_ui = show_animator_ui
__main__.do_reset = do_reset

menu_name = "RigTools_TopMenu"
if cmds.menu(menu_name, exists=True):
    cmds.deleteUI(menu_name)
    
cmds.menu(menu_name, label="Rig Tools", parent="MayaWindow", tearOff=True)
cmds.menuItem(label="Open Rig Reset UI", command="import __main__; __main__.show_animator_ui()")

cmds.evalDeferred("import __main__; __main__.show_animator_ui()")
"""

        cmds.scriptNode(scriptType=2, beforeScript=animator_payload, name=self.script_node_name, sourceType="python")

        cmds.inViewMessage(amg="<hl>Success!</hl> Rig bound, states baked, and UI embedded.", pos='midCenter', fade=True)
        cmds.deleteUI(self.window_name)

def launch():
    """Call this function to launch the tool safely from other scripts/shelves."""
    global rigger_setup_tool_instance
    rigger_setup_tool_instance = RiggerSetupTool()

# This ensures it still opens if you run it directly in the Script Editor
if __name__ == "__main__":
    launch()