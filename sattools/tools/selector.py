import maya.cmds as cmds

# ==========================================
# 1. CORE LOGIC
# ==========================================
class SelectorLogic:
    def __init__(self):
        self.types_mapping = {
            "All": "*",
            "Geometry (Mesh)": "mesh",
            "Curves": "nurbsCurve",
            "Joints": "joint",
            "Locators": "locator",
            "Constraints": "constraint",
            "Groups": "group",
            "Surfaces": "nurbsSurface",
            "Clusters": "clusterHandle",
            "Lattice": "lattice",
            "Cameras": "camera",
            "Lights": "light",
            "IK Handles": "ikHandle"
        }

    def get_filtered_items(self, sel_type_label, prefix, suffix, exact, target_parent=""):
        sel_type = self.types_mapping.get(sel_type_label, "*")
        raw_items = []
        shape_types = ['mesh', 'nurbsCurve', 'locator', 'clusterHandle', 'lattice', 'nurbsSurface','camera', 'light']
        
        if sel_type_label == "All":
            raw_items = cmds.ls(transforms=True, long=True) + cmds.ls(type='joint', long=True)
        elif sel_type == "group":
            all_transforms = cmds.ls(exactType='transform', long=True) or []
            for t in all_transforms:
                if not cmds.listRelatives(t, shapes=True):
                    raw_items.append(t)
        else:
            if sel_type in shape_types:
                shapes = cmds.ls(type=sel_type, long=True) or []
                if shapes:
                    transforms = cmds.listRelatives(shapes, parent=True, fullPath=True) or []
                    raw_items = list(set(transforms))
            else:
                raw_items = cmds.ls(type=sel_type, long=True) or []
                
        if target_parent:
            parent_long = cmds.ls(target_parent, long=True)
            if parent_long:
                parent_path = parent_long[0] + "|"
                raw_items = [item for item in raw_items if item.startswith(parent_path)]

        item_mapping = {}
        display_names = []
        
       for full_path in raw_items:
            short_name = full_path.split('|')[-1] 
            
            # Isolate the core name by splitting off any namespace
            clean_name = short_name.split(':')[-1]
            
            # Apply filters against the clean name, ignoring the namespace
            if exact and exact != clean_name: continue
            if prefix and not clean_name.startswith(prefix): continue
            if suffix and not clean_name.endswith(suffix): continue
            
            ui_name = short_name
            if ui_name in item_mapping:
                ui_name = full_path
                
            item_mapping[ui_name] = full_path
            display_names.append(ui_name)
            
        display_names.sort()
        return display_names, item_mapping

    def select_items(self, item_mapping, selected_ui):
        if selected_ui and selected_ui[0] != "< No Matches Found >":
            objects_to_select = [item_mapping[name] for name in selected_ui if name in item_mapping]
            cmds.select(objects_to_select, replace=True)
        else:
            cmds.select(clear=True)

# ==========================================
# 2. USER INTERFACE
# ==========================================
class SelectorUI:
    def __init__(self):
        self.window_name = "AdvancedSelectorUI"
        self.title = "Selector (Outliner Alt)"
        self.size = (350, 690) # Increased height for the refresh button
        self.logic = SelectorLogic()
        self.current_mapping = {}
        self.current_total = 0

    def show(self):
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        self.window = cmds.window(self.window_name, title=self.title, widthHeight=self.size, sizeable=False)
        self.main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

        cmds.frameLayout(label="1 & 2. Category Isolator", collapsable=True, marginHeight=5, marginWidth=40, bgc=[0.15, 0.15, 0.15])
        cmds.columnLayout(adjustableColumn=False)
        self.type_menu = cmds.optionMenu(label="  Isolate Type: ", width=250, changeCommand=self.update_list)
        for t in self.logic.types_mapping.keys():
            cmds.menuItem(label=t)
        cmds.setParent('..')
        cmds.setParent('..') 

        cmds.frameLayout(label="3. Name Filters", collapsable=True, marginHeight=5, marginWidth=5, bgc=[0.15, 0.15, 0.15])
        cmds.rowColumnLayout(numberOfColumns=2, columnWidth=[(1, 80), (2, 230)], rowSpacing=[(1,4), (2,4), (3,4)])
        
        cmds.text(label="Prefix: ", align="right")
        self.prefix_fld = cmds.textField(changeCommand=self.update_list, placeholderText="e.g., L_")
        
        cmds.text(label="Suffix: ", align="right")
        self.suffix_fld = cmds.textField(changeCommand=self.update_list, placeholderText="e.g., _JNT")
        
        cmds.text(label="Exact Name: ", align="right")
        self.exact_fld = cmds.textField(changeCommand=self.update_list, placeholderText="e.g., center_ctrl")
        
        cmds.setParent('..')
        cmds.setParent('..')
        
        cmds.frameLayout(label="4. Hierarchy Focus (Specific Group)", collapsable=True, marginHeight=5, marginWidth=5, bgc=[0.15, 0.15, 0.15])
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
        
        self.parent_fld = cmds.textField(editable=False, placeholderText="Looking in: Entire Scene (Default)", font="obliqueLabelFont")
        
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(165, 165))
        cmds.button(label="Set Selected Group", width=165, backgroundColor=[0.3, 0.5, 0.4], command=self.set_parent)
        cmds.button(label="Clear Focus", width=165, backgroundColor=[0.5, 0.3, 0.3], command=self.clear_parent)
        
        cmds.setParent('..')
        cmds.setParent('..')
        cmds.setParent('..')

        # Restored the manual refresh button to catch parenting and deletion events
        cmds.separator(height=10, style='none')
        cmds.button(label="Manual Refresh / Apply Filters", command=self.update_list, height=30, backgroundColor=[0.2, 0.4, 0.6])
        cmds.separator(height=10, style='none')

        cmds.frameLayout(label="Selector Outliner View", collapsable=False)
        self.item_list = cmds.textScrollList(allowMultiSelection=True, height=300, selectCommand=self.select_from_ui, font="plainLabelFont")
        
        cmds.separator(height=3, style='none')
        self.count_text = cmds.text(label="Selected: 0  |  Total: 0", align="center", font="boldLabelFont")
        cmds.separator(height=3, style='none') 
        cmds.setParent('..')

        cmds.showWindow(self.window)
        self.update_list()
        self.create_script_jobs()

    def set_parent(self, *args):
        sel = cmds.ls(selection=True)
        if sel:
            cmds.textField(self.parent_fld, edit=True, text=sel[0])
            self.update_list()
        else:
            cmds.warning("Please select a group or object in Maya first.")

    def clear_parent(self, *args):
        cmds.textField(self.parent_fld, edit=True, text="")
        self.update_list()

    def create_script_jobs(self):
        cmds.scriptJob(event=["DagObjectCreated", self.update_list], parent=self.window_name)
        cmds.scriptJob(event=["NameChanged", self.update_list], parent=self.window_name)
        cmds.scriptJob(event=["Undo", self.update_list], parent=self.window_name)
        cmds.scriptJob(event=["Redo", self.update_list], parent=self.window_name)

    def update_list(self, *args):
        if not cmds.window(self.window_name, exists=True):
            return

        sel_type_label = cmds.optionMenu(self.type_menu, query=True, value=True)
        prefix = cmds.textField(self.prefix_fld, query=True, text=True).strip()
        suffix = cmds.textField(self.suffix_fld, query=True, text=True).strip()
        exact = cmds.textField(self.exact_fld, query=True, text=True).strip()
        target_parent = cmds.textField(self.parent_fld, query=True, text=True).strip()

        display_names, self.current_mapping = self.logic.get_filtered_items(
            sel_type_label, prefix, suffix, exact, target_parent
        )

        cmds.textScrollList(self.item_list, edit=True, removeAll=True)
        
        if display_names:
            cmds.textScrollList(self.item_list, edit=True, append=display_names)
            self.current_total = len(display_names)
        else:
            cmds.textScrollList(self.item_list, edit=True, append=["< No Matches Found >"])
            self.current_total = 0
            
        cmds.text(self.count_text, edit=True, label="Selected: 0  |  Total: {}".format(self.current_total))

    def select_from_ui(self):
        selected_ui = cmds.textScrollList(self.item_list, query=True, selectItem=True)
        self.logic.select_items(self.current_mapping, selected_ui)
        
        sel_count = len(selected_ui) if selected_ui and selected_ui[0] != "< No Matches Found >" else 0
        cmds.text(self.count_text, edit=True, label="Selected: {}  |  Total: {}".format(sel_count, self.current_total))

# ==========================================
# 3. EXECUTE
# ==========================================
SelectorUI().show()
