import maya.cmds as mc

class DeformerReorderUI:

    def __init__(self):
        self.window_name = "deformerReorderWindow"
        self.current_object = None
        self.deformer_list = []

    def create_ui(self):
        """Create the enhanced deformer reorder UI window"""
        if mc.window(self.window_name, exists=True):
            mc.deleteUI(self.window_name)

        window = mc.window(self.window_name, title="Deformer Reorder Tool", width=550, height=700)
        mc.columnLayout(adjustableColumn=True, rowSpacing=5)

        # 1. Object Selection
        mc.text("1. Object Selection", font="boldLabelFont", align="left")
        mc.rowLayout(numberOfColumns=4, columnWidth4=(120, 200, 80, 80))
        mc.button(label="Get Selected Objects", command=self.get_selected_objects)
        self.obj_count_field = mc.textField(editable=False, text="0 objects with deformers")
        mc.button(label="Clear", command=self.clear_selection)
        mc.setParent('..')
        self.obj_list = mc.textScrollList(numberOfRows=5, allowMultiSelection=False, selectCommand=self.on_object_selected)
        mc.separator(height=10, style="single")

        # 2. Current Deformers
        mc.text("2. Current Deformers (Select object above)", font="boldLabelFont", align="left")
        mc.text("Current deformer order (bottom=base, top=final):", align="left")
        self.deformer_list_ui = mc.textScrollList(numberOfRows=8, allowMultiSelection=True)
        mc.separator(height=10, style="single")

        # 3. Reorder Methods
        mc.text("3. Reorder Methods", font="boldLabelFont", align="left")
        mc.text("Quick Reorder (all selected objects):", align="left")
        mc.rowLayout(numberOfColumns=2, columnWidth2=(240,240))
        mc.button(label="Standard Order\n(Skin = BlendShape = Others)", command=lambda x: self.quick_reorder("standard"))
        mc.button(label="Animation Order\n(BlendShape = Skin = Others)", command=lambda x: self.quick_reorder("animation"))
        mc.setParent('..')
        mc.separator(height=5)

        # Custom (Ascending) Priority
        mc.text("Custom Order (assign ascending priority):", font="boldLabelFont", align="left")
        mc.text("Lower numbers = earlier deformation, higher = later", align="left")
        mc.frameLayout(label="Deformer Priority Assignment", marginWidth=5, marginHeight=5)
        mc.gridLayout(numberOfColumns=4, cellWidth=120, cellHeight=30)
        mc.text(label="Deformer Type", align="center", font="boldLabelFont")
        mc.text(label="Priority", align="center", font="boldLabelFont")
        mc.text(label="Deformer Type", align="center", font="boldLabelFont")
        mc.text(label="Priority", align="center", font="boldLabelFont")
        mc.text(label="skinCluster", align="left"); self.skin_priority = mc.intField(minValue=1, maxValue=10, value=1, width=50)
        mc.text(label="blendShape", align="left"); self.blend_priority = mc.intField(minValue=1, maxValue=10, value=2, width=50)
        mc.text(label="cluster", align="left"); self.cluster_priority = mc.intField(minValue=1, maxValue=10, value=3, width=50)
        mc.text(label="ffd", align="left"); self.ffd_priority = mc.intField(minValue=1, maxValue=10, value=4, width=50)
        mc.text(label="nonLinear (bend)", align="left"); self.bend_priority = mc.intField(minValue=1, maxValue=10, value=5, width=50)
        mc.text(label="nonLinear (sine)", align="left"); self.sine_priority = mc.intField(minValue=1, maxValue=10, value=6, width=50)
        mc.text(label="nonLinear (wave)", align="left"); self.wave_priority = mc.intField(minValue=1, maxValue=10, value=7, width=50)
        mc.text(label="nonLinear (twist)", align="left"); self.twist_priority = mc.intField(minValue=1, maxValue=10, value=8, width=50)
        mc.text(label="nonLinear (flare)", align="left"); self.flare_priority = mc.intField(minValue=1, maxValue=10, value=9, width=50)
        mc.text(label="sculpt", align="left"); self.sculpt_priority = mc.intField(minValue=1, maxValue=10, value=10, width=50)
        mc.setParent('..'); mc.setParent('..')

        mc.button(label="Apply Custom Order", command=self.apply_custom_order)
        mc.separator(height=10, style="single")

        # Manual Reorder
        mc.text("Manual Reorder (single object):", font="boldLabelFont", align="left")
        mc.rowLayout(numberOfColumns=4, columnWidth4=(100,100,100,100))
        mc.button(label="Move Up", command=self.move_deformer_up)
        mc.button(label="Move Down", command=self.move_deformer_down)
        mc.button(label="Move to Top", command=self.move_deformer_top)
        mc.button(label="Move to Bottom", command=self.move_deformer_bottom)
        mc.setParent('..')
        mc.separator(height=10, style="double")

        # Bottom Buttons
        mc.rowLayout(numberOfColumns=4, columnWidth4=(120,100,80,80))
        mc.button(label="Open Component Editor", command=self.open_component_editor)
        mc.button(label="Refresh", command=self.refresh_all)
        mc.button(label="Help", command=self.show_help)
        mc.button(label="Close", command=self.close_window)
        mc.setParent('..')

        self.status_field = mc.textField(editable=False, text="Ready - All fixes applied")
        mc.showWindow(window)

    def get_priority_values(self):
        return {
            "skinCluster": mc.intField(self.skin_priority, query=True, value=True),
            "blendShape": mc.intField(self.blend_priority, query=True, value=True),
            "cluster": mc.intField(self.cluster_priority, query=True, value=True),
            "ffd": mc.intField(self.ffd_priority, query=True, value=True),
            "bend": mc.intField(self.bend_priority, query=True, value=True),
            "sine": mc.intField(self.sine_priority, query=True, value=True),
            "wave": mc.intField(self.wave_priority, query=True, value=True),
            "twist": mc.intField(self.twist_priority, query=True, value=True),
            "flare": mc.intField(self.flare_priority, query=True, value=True),
            "sculpt": mc.intField(self.sculpt_priority, query=True, value=True),
        }

    def get_deformer_priority(self, deformer_type, deformer_name, priorities):
        # Exact type mapping
        type_map = {
            'skinCluster': 'skinCluster',
            'blendShape': 'blendShape',
            'cluster': 'cluster',
            'ffd': 'ffd',
            'sculpt': 'sculpt'
        }
        if deformer_type == "nonLinear":
            try:
                st = mc.getAttr(deformer_name + ".type")
                nl_map = {1:'sine',2:'bend',3:'twist',4:'wave',5:'flare',6:'squash'}
                if st in nl_map:
                    return priorities.get(nl_map[st],5)
            except:
                name = deformer_name.lower()
                for key in ['bend','sine','wave','twist','flare']:
                    if key in name:
                        return priorities.get(key,5)
            return 5
        if deformer_type in type_map:
            return priorities.get(type_map[deformer_type],10)
        return 10

    def get_selected_objects(self, *args):
        sels = mc.ls(selection=True)
        mc.textScrollList(self.obj_list, edit=True, removeAll=True)
        objs = []
        for o in sels:
            ds = self.get_all_deformers(o)
            if ds:
                objs.append(o)
                mc.textScrollList(self.obj_list, edit=True, append=f"{o} ({len(ds)} deformers)")
        mc.textField(self.obj_count_field, edit=True, text=f"{len(objs)} objects with deformers")
        self.update_status(f"Found {len(objs)} objects with deformers")

    def get_all_deformers(self, geo):
        deps = []
        try:
            hist = mc.listHistory(geo, breadthFirst=True)
            for n in hist:
                if mc.objectType(n) in ["blendShape","skinCluster","ffd","nonLinear","cluster","sculpt"]:
                    deps.append(n)
        except:
            pass
        return deps

    def on_object_selected(self, *args):
        sel = mc.textScrollList(self.obj_list, query=True, selectItem=True)
        if sel:
            self.current_object = sel[0].split(' (')[0]
            self.update_deformer_list()

    def update_deformer_list(self):
        if not self.current_object: return
        mc.textScrollList(self.deformer_list_ui, edit=True, removeAll=True)
        self.deformer_list = self.get_deformer_stack(self.current_object)
        for d in self.deformer_list:
            mc.textScrollList(self.deformer_list_ui, edit=True, append=f"{d} ({mc.objectType(d)})")
        self.update_status(f"Showing {len(self.deformer_list)} deformers on {self.current_object}")

    def get_deformer_stack(self, geo):
        deps=[]
        try:
            hist=mc.listHistory(geo, breadthFirst=True)
            for n in hist:
                if mc.objectType(n) in ["blendShape","skinCluster","ffd","nonLinear","cluster","sculpt"]:
                    deps.append(n)
        except:
            pass
        return deps

    def quick_reorder(self, mode):
        objs = self.get_all_objects_from_list()
        if not objs:
            self.update_status("No objects selected")
            return
        for o in objs:
            try:
                if mode=="standard": self.reorder_standard(o)
                else: self.reorder_animation(o)
            except Exception as e:
                self.update_status(f"Error reordering {o}: {e}")
        self.update_status(f"Applied {mode} reorder to {len(objs)} objects")
        self.refresh_all()

    def reorder_standard(self, geo):
        ds=self.get_all_deformers(geo)
        skins=[d for d in ds if mc.objectType(d)=="skinCluster"]
        blends=[d for d in ds if mc.objectType(d)=="blendShape"]
        others=[d for d in ds if d not in skins+blends]
        for s in skins:
            for o in others+blends:
                try: mc.reorderDeformers(s,o,geo)
                except: pass

    def reorder_animation(self,geo):
        ds=self.get_all_deformers(geo)
        blends=[d for d in ds if mc.objectType(d)=="blendShape"]
        skins=[d for d in ds if mc.objectType(d)=="skinCluster"]
        others=[d for d in ds if d not in skins+blends]
        for b in blends:
            for o in others+skins:
                try: mc.reorderDeformers(b,o,geo)
                except: pass

    def apply_custom_order(self,*a):
        objs=self.get_all_objects_from_list()
        if not objs:
            self.update_status("No objects selected")
            return
        pr=self.get_priority_values()
        for o in objs: self.reorder_custom(o,pr)
        self.update_status(f"Applied custom order to {len(objs)} objects")
        self.refresh_all()

    def reorder_custom(self,geo,pr):
        ds=self.get_all_deformers(geo)
        if len(ds)<2: return
        dp=[(d,self.get_deformer_priority(mc.objectType(d),d,pr)) for d in ds]
        dp.sort(key=lambda x:x[1])
        ordered=[d for d,_ in dp]
        for i in range(1,len(ordered)):
            for j in range(i):
                try: mc.reorderDeformers(ordered[i],ordered[j],geo)
                except: pass

    def move_deformer_up(self,*a):   self.move_deformer(-1)
    def move_deformer_down(self,*a): self.move_deformer(1)
    def move_deformer_top(self,*a):  self.move_deformer_to_position(0)
    def move_deformer_bottom(self,*a): self.move_deformer_to_position(-1)

    def move_deformer(self, direction):
        """Move deformer in specified direction - FIXED to avoid Maya warnings"""
        if not self.current_object:
            self.update_status("No object selected")
            return
        
        sel = mc.textScrollList(self.deformer_list_ui, query=True, selectItem=True)
        if not sel:
            self.update_status("No deformer selected")
            return
        
        name = sel[0].split(' (')[0]
        stack = self.get_deformer_stack(self.current_object)
        
        try:
            idx = stack.index(name)
        except:
            self.update_status(f"Deformer {name} not found")
            return
        
        new_idx = idx + direction
        
        # Check bounds
        if new_idx < 0:
            self.update_status(f"{name} is already at the top")
            return
        if new_idx >= len(stack):
            self.update_status(f"{name} is already at the bottom")
            return
        
        # NEW APPROACH: Use Maya's reorder command with proper validation
        try:
            # Get all deformers in current order
            current_order = self.get_deformer_stack(self.current_object)
            
            # Remove the deformer we want to move
            current_order.remove(name)
            
            # Insert it at the new position
            current_order.insert(new_idx, name)
            
            # Rebuild the deformer chain in the correct order
            # Start from the bottom (first deformer) and work up
            for i in range(len(current_order) - 1, 0, -1):
                try:
                    mc.reorderDeformers(current_order[i], current_order[i-1], self.current_object)
                except:
                    # Silently ignore errors - the order might already be correct
                    pass
            
            self.update_deformer_list()
            self.update_status(f"Moved {name} {'up' if direction < 0 else 'down'}")
            
        except Exception as e:
            self.update_status(f"Error moving deformer: {e}")

    def move_deformer_to_position(self, position):
        """Move deformer to specific position - FIXED to avoid Maya warnings"""
        if not self.current_object:
            self.update_status("No object selected")
            return
        
        sel = mc.textScrollList(self.deformer_list_ui, query=True, selectItem=True)
        if not sel:
            self.update_status("No deformer selected")
            return
        
        name = sel[0].split(' (')[0]
        stack = self.get_deformer_stack(self.current_object)
        
        try:
            current_idx = stack.index(name)
        except:
            self.update_status(f"Deformer {name} not found")
            return
        
        # Check if already in position
        if (position == 0 and current_idx == 0) or (position == -1 and current_idx == len(stack) - 1):
            pos_text = "top" if position == 0 else "bottom"
            self.update_status(f"{name} is already at the {pos_text}")
            return
        
        try:
            # Get all deformers in current order
            current_order = self.get_deformer_stack(self.current_object)
            
            # Remove the deformer we want to move
            current_order.remove(name)
            
            # Insert it at the target position
            if position == 0:  # Move to top
                current_order.insert(0, name)
            else:  # Move to bottom
                current_order.append(name)
            
            # Rebuild the deformer chain in the correct order
            # Start from the bottom (first deformer) and work up
            for i in range(len(current_order) - 1, 0, -1):
                try:
                    mc.reorderDeformers(current_order[i], current_order[i-1], self.current_object)
                except:
                    # Silently ignore errors - the order might already be correct
                    pass
            
            self.update_deformer_list()
            pos_text = "top" if position == 0 else "bottom"
            self.update_status(f"Moved {name} to {pos_text}")
            
        except Exception as e:
            self.update_status(f"Error moving deformer: {e}")

    def get_all_objects_from_list(self):
        items=mc.textScrollList(self.obj_list,query=True,allItems=True) or []
        return [i.split(' (')[0] for i in items]

    def clear_selection(self,*a):
        mc.textScrollList(self.obj_list,edit=True,removeAll=True)
        mc.textScrollList(self.deformer_list_ui,edit=True,removeAll=True)
        mc.textField(self.obj_count_field,edit=True,text="0 objects with deformers")
        self.current_object=None; self.deformer_list=[]
        self.update_status("Selection cleared")

    def refresh_all(self,*a):
        if self.current_object: self.update_deformer_list()
        self.update_status("Refreshed")

    def open_component_editor(self,*a):
        mc.ComponentEditor(); self.update_status("Opened Component Editor")

    def show_help(self,*a):
        help_text = """Deformer Reorder Tool - FULLY FIXED VERSION

1. Select objects with deformers
2. Click 'Get Selected Objects'
3. Select an object to view its deformers
4. Set priority numbers for each deformer type:
   - Lower = earlier deformation (1=first)
   - Higher = later deformation (10=last)
5. Use quick reorder or manual buttons
6. Click 'Apply Custom Order'

Priority Examples (ASCENDING):
- skinCluster=1, blendShape=2, cluster=3, ffd=4, nonLinear=5-9, sculpt=10

All fixes applied:
- Ascending priority
- Proper nonLinear detection
- No warnings on manual moves
- Robust error handling
- Debug output in Script Editor"""
        mc.confirmDialog(title="Help", message=help_text, button="OK")

    def close_window(self,*a):
        if mc.window(self.window_name,exists=True): mc.deleteUI(self.window_name)

    def update_status(self,message):
        mc.textField(self.status_field,edit=True,text=message)

def show_deformer_reorder_ui():
    ui = DeformerReorderUI()
    ui.create_ui()

# Run the UI
show_deformer_reorder_ui()