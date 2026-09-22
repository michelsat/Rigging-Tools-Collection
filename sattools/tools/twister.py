import maya.cmds as cmds

class LocatorToJointsUI:
    def __init__(self):
        self.window_name = "locatorToJointsUI"
        self.top_locator_fields = []
        self.bottom_locator_fields = []
        self.constraint_target_fields = []
        
        # Default settings
        self.ulna_axis = "z"
        self.ulna_offset_dir = 1
        self.radius_axis = "z" 
        self.radius_offset_dir = 1
        self.offset_distance = 1.0
        self.mirror_axis = "x"       # Axis to negate when mirroring locators
        self.prefix = "L_"  # Default prefix for auto-created locators
        
        # Default locator names
        self.default_top_names = ["Ulna_pos", "Radius_pos"]
        self.default_bottom_names = ["Ulna_tgt", "Radius_tgt"]
        
        self.create_ui()
    
    def set_prefix(self, prefix):
        """Set the prefix and refresh locator field names for the new limb."""
        self.prefix = prefix
        cmds.textField(self.prefix_field, edit=True, text=prefix)

        # Update locator name fields to reflect the new prefix so user
        # can immediately click "Create Ulna/Radius Locators" or pick
        # existing ones with the correct naming.
        default_tops    = ["Ulna_pos",  "Radius_pos"]
        default_bottoms = ["Ulna_tgt",  "Radius_tgt"]

        for i, field in enumerate(self.top_locator_fields):
            cmds.textField(field, edit=True, text=f"{prefix}{default_tops[i]}")

        for i, field in enumerate(self.bottom_locator_fields):
            cmds.textField(field, edit=True, text=f"{prefix}{default_bottoms[i]}")

        for field in self.constraint_target_fields:
            cmds.textField(field, edit=True, text="")
    
    def create_ui(self):
        # Check if window exists and delete it
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)
        
        # Define layout control variables
        spacing = 5
        field_width = 150  # Field width to prevent text shrinking
        label_height = 20
        field_height = 25
        button_height = 25
        
        # Create window with fixed size
        cmds.window(self.window_name, title="Twister[SAT]", width=450, sizeable=False)
        
        # Main layout
        main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=10)
        
        # Header
        cmds.text(label="Create twist joints from locator pairs", font="boldLabelFont")
        cmds.separator(height=10, style="double")
        
        # Add buttons to create locator pairs
        locator_buttons = cmds.rowLayout(numberOfColumns=2, parent=main_layout)
        cmds.button(label="Create Ulna Locators", 
                   command=lambda x: self.create_locator_pair("Ulna", 0, 5, 0),
                   backgroundColor=[0.5, 0.7, 1.0])
        cmds.button(label="Create Radius Locators", 
                   command=lambda x: self.create_locator_pair("Radius", 0, 2, 0),
                   backgroundColor=[0.7, 0.5, 1.0])
        cmds.setParent('..')
        
        cmds.separator(height=10, style="single")
        
        # Create field layout
        form = cmds.formLayout(parent=main_layout)
        
        # Headers
        pos_label = cmds.text(label="Pos_Loc", font="boldLabelFont")
        tgt_label = cmds.text(label="Tgt_Loc", font="boldLabelFont")
        cnst_label = cmds.text(label="Const_Tgt", font="boldLabelFont")
        
        # First pair - specify width to prevent shrinking
        top_field1 = cmds.textField(text=self.default_top_names[0], width=field_width)
        bottom_field1 = cmds.textField(text=self.default_bottom_names[0], width=field_width)
        constraint_field1 = cmds.textField(width=field_width)
        
        # Get buttons for first pair - shorter labels
        get_top1 = cmds.button(label="Choose_Ulna_pos_loc", command=lambda x: self.get_selected(top_field1))
        get_bottom1 = cmds.button(label="Choose_Ulna_tgt_loc", command=lambda x: self.get_selected(bottom_field1))
        get_constraint1 = cmds.button(label="Choose_Constraints_Source", command=lambda x: self.get_selected(constraint_field1))
        
        # Second pair - specify width to prevent shrinking
        top_field2 = cmds.textField(text=self.default_top_names[1], width=field_width)
        bottom_field2 = cmds.textField(text=self.default_bottom_names[1], width=field_width)
        constraint_field2 = cmds.textField(width=field_width)
        
        # Get buttons for second pair - shorter labels
        get_top2 = cmds.button(label="Choose_Radius_pos_loc", command=lambda x: self.get_selected(top_field2))
        get_bottom2 = cmds.button(label="Choose_Radius_tgt_loc", command=lambda x: self.get_selected(bottom_field2))
        get_constraint2 = cmds.button(label="Choose_Constraints_Source", command=lambda x: self.get_selected(constraint_field2))

        # Position controls using formLayout
        # spacing, field_width, label_height, field_height, and button_height are already defined above
        
        # Position headers
        cmds.formLayout(form, edit=True, 
                        attachForm=[(pos_label, 'top', spacing), (pos_label, 'left', spacing*10)])
        cmds.formLayout(form, edit=True, 
                        attachForm=[(tgt_label, 'top', spacing)],
                        attachControl=[(tgt_label, 'left', spacing*20, pos_label)])
        cmds.formLayout(form, edit=True, 
                        attachForm=[(cnst_label, 'top', spacing)],
                        attachControl=[(cnst_label, 'left', spacing*30, tgt_label)])
        
        # Position first row fields and buttons
        cmds.formLayout(form, edit=True, 
                        attachForm=[(top_field1, 'left', spacing)],
                        attachControl=[(top_field1, 'top', spacing, pos_label)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(bottom_field1, 'left', spacing*2, top_field1), (bottom_field1, 'top', spacing, tgt_label)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(constraint_field1, 'left', spacing*2, bottom_field1), (constraint_field1, 'top', spacing, cnst_label)])
        
        # Position first row buttons
        cmds.formLayout(form, edit=True, 
                        attachForm=[(get_top1, 'left', spacing)],
                        attachControl=[(get_top1, 'top', spacing, top_field1)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(get_bottom1, 'left', spacing*2, get_top1), (get_bottom1, 'top', spacing, bottom_field1)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(get_constraint1, 'left', spacing*2, get_bottom1), (get_constraint1, 'top', spacing, constraint_field1)])
        
        # Position second row fields
        cmds.formLayout(form, edit=True, 
                        attachForm=[(top_field2, 'left', spacing)],
                        attachControl=[(top_field2, 'top', spacing*2, get_top1)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(bottom_field2, 'left', spacing*2, top_field2), (bottom_field2, 'top', spacing*2, get_bottom1)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(constraint_field2, 'left', spacing*2, bottom_field2), (constraint_field2, 'top', spacing*2, get_constraint1)])
        
        # Position second row buttons
        cmds.formLayout(form, edit=True, 
                        attachForm=[(get_top2, 'left', spacing)],
                        attachControl=[(get_top2, 'top', spacing, top_field2)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(get_bottom2, 'left', spacing*2, get_top2), (get_bottom2, 'top', spacing, bottom_field2)])
        cmds.formLayout(form, edit=True, 
                        attachControl=[(get_constraint2, 'left', spacing*2, get_bottom2), (get_constraint2, 'top', spacing, constraint_field2)])
        
        # Store field references
        self.top_locator_fields = [top_field1, top_field2]
        self.bottom_locator_fields = [bottom_field1, bottom_field2]
        self.constraint_target_fields = [constraint_field1, constraint_field2]
        
        # Add some spacing
        cmds.setParent(main_layout)
        cmds.separator(height=10, style="single")
        
        # Offset distance
        offset_row = cmds.rowLayout(numberOfColumns=2, parent=main_layout)
        cmds.text(label="Offset Distance:", align="left", width=100)
        self.offset_field = cmds.floatField(value=self.offset_distance, minValue=0.1, maxValue=10.0)
        cmds.setParent('..')
        
        # Prefix for auto-created locators
        prefix_row = cmds.rowLayout(numberOfColumns=2, parent=main_layout)
        cmds.text(label="Prefix:", align="left", width=100)
        self.prefix_field = cmds.textField(text=self.prefix, width=150)
        cmds.setParent('..')

        # ── Limb preset section ──────────────────────────────────────────
        cmds.text(label="Quick Prefix Presets:", align="left", font="boldLabelFont",
                  parent=main_layout)

        # Row 1 – Front limbs
        front_row = cmds.rowLayout(numberOfColumns=5, parent=main_layout,
                                   columnAttach5=("left","left","left","left","left"),
                                   columnWidth5=(55, 65, 65, 65, 65))
        cmds.text(label="Front:", align="right", width=50)
        cmds.button(label="FL_",  width=60,
                    command=lambda x: self.set_prefix("FL_"),
                    backgroundColor=[0.4, 0.7, 1.0],
                    annotation="Front Left")
        cmds.button(label="FR_",  width=60,
                    command=lambda x: self.set_prefix("FR_"),
                    backgroundColor=[0.4, 0.7, 1.0],
                    annotation="Front Right")
        cmds.button(label="F_",   width=60,
                    command=lambda x: self.set_prefix("F_"),
                    backgroundColor=[0.55, 0.8, 1.0],
                    annotation="Front (generic)")
        cmds.setParent('..')

        # Row 2 – Back limbs
        back_row = cmds.rowLayout(numberOfColumns=5, parent=main_layout,
                                  columnAttach5=("left","left","left","left","left"),
                                  columnWidth5=(55, 65, 65, 65, 65))
        cmds.text(label="Back:", align="right", width=50)
        cmds.button(label="BL_",  width=60,
                    command=lambda x: self.set_prefix("BL_"),
                    backgroundColor=[1.0, 0.7, 0.4],
                    annotation="Back Left")
        cmds.button(label="BR_",  width=60,
                    command=lambda x: self.set_prefix("BR_"),
                    backgroundColor=[1.0, 0.7, 0.4],
                    annotation="Back Right")
        cmds.button(label="B_",   width=60,
                    command=lambda x: self.set_prefix("B_"),
                    backgroundColor=[1.0, 0.8, 0.55],
                    annotation="Back (generic)")
        cmds.setParent('..')

        # Row 3 – Side-only / other
        side_row = cmds.rowLayout(numberOfColumns=5, parent=main_layout,
                                  columnAttach5=("left","left","left","left","left"),
                                  columnWidth5=(55, 65, 65, 65, 65))
        cmds.text(label="Side:", align="right", width=50)
        cmds.button(label="L_",   width=60,
                    command=lambda x: self.set_prefix("L_"),
                    backgroundColor=[0.6, 1.0, 0.6],
                    annotation="Left")
        cmds.button(label="R_",   width=60,
                    command=lambda x: self.set_prefix("R_"),
                    backgroundColor=[1.0, 0.6, 0.6],
                    annotation="Right")
        cmds.button(label="C_",   width=60,
                    command=lambda x: self.set_prefix("C_"),
                    backgroundColor=[0.85, 0.85, 0.85],
                    annotation="Centre")
        cmds.setParent('..')
        # ────────────────────────────────────────────────────────────────

        # ── Mirror Locators section ──────────────────────────────────────
        cmds.separator(height=10, style="single", parent=main_layout)
        cmds.text(label="Mirror Locators:", align="left", font="boldLabelFont",
                  parent=main_layout)

        # Mirror axis radio
        mirror_axis_row = cmds.rowLayout(numberOfColumns=4, parent=main_layout,
                                         columnWidth4=(80, 60, 60, 60))
        cmds.text(label="Mirror Axis:", align="left", width=78)
        self.mirror_axis_radio = cmds.radioCollection()
        cmds.radioButton(label="X", select=True,
                         onCommand=lambda x: setattr(self, 'mirror_axis', 'x'))
        cmds.radioButton(label="Y",
                         onCommand=lambda x: setattr(self, 'mirror_axis', 'y'))
        cmds.radioButton(label="Z",
                         onCommand=lambda x: setattr(self, 'mirror_axis', 'z'))
        cmds.setParent('..')

        # Mirror button — full width, prominent colour
        cmds.button(label="Mirror Locators to Opposite Side",
                    parent=main_layout,
                    height=32,
                    backgroundColor=[0.9, 0.75, 1.0],
                    annotation=(
                        "Mirrors the 4 locators in the fields above to the opposite side.\n"
                        "FL_→FR_, FR_→FL_, BL_→BR_, BR_→BL_, L_→R_, R_→L_"
                    ),
                    command=lambda x: self.mirror_locators())
        # ────────────────────────────────────────────────────────────────

        # Settings tabs
        tabs = cmds.tabLayout(innerMarginWidth=5, innerMarginHeight=5, parent=main_layout)
        
        # Ulna settings tab
        ulna_tab = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="Forward Axis:", align="left")
        ulna_axis_row = cmds.rowLayout(numberOfColumns=3)
        self.ulna_axis_radio = cmds.radioCollection()
        cmds.radioButton(label="X", select=(self.ulna_axis == "x"), onCommand=lambda x: setattr(self, 'ulna_axis', 'x'))
        cmds.radioButton(label="Y", select=(self.ulna_axis == "y"), onCommand=lambda x: setattr(self, 'ulna_axis', 'y'))
        cmds.radioButton(label="Z", select=(self.ulna_axis == "z"), onCommand=lambda x: setattr(self, 'ulna_axis', 'z'))
        cmds.setParent('..')
        
        cmds.text(label="Offset Direction:", align="left")
        ulna_dir_row = cmds.rowLayout(numberOfColumns=2)
        self.ulna_dir_radio = cmds.radioCollection()
        cmds.radioButton(label="Positive", select=(self.ulna_offset_dir == 1), onCommand=lambda x: setattr(self, 'ulna_offset_dir', 1))
        cmds.radioButton(label="Negative", select=(self.ulna_offset_dir == -1), onCommand=lambda x: setattr(self, 'ulna_offset_dir', -1))
        cmds.setParent('..')
        cmds.setParent('..')
        
        # Radius settings tab
        radius_tab = cmds.columnLayout(adjustableColumn=True)
        cmds.text(label="Forward Axis:", align="left")
        radius_axis_row = cmds.rowLayout(numberOfColumns=3)
        self.radius_axis_radio = cmds.radioCollection()
        cmds.radioButton(label="X", select=(self.radius_axis == "x"), onCommand=lambda x: setattr(self, 'radius_axis', 'x'))
        cmds.radioButton(label="Y", select=(self.radius_axis == "y"), onCommand=lambda x: setattr(self, 'radius_axis', 'y'))
        cmds.radioButton(label="Z", select=(self.radius_axis == "z"), onCommand=lambda x: setattr(self, 'radius_axis', 'z'))
        cmds.setParent('..')
        
        cmds.text(label="Offset Direction:", align="left")
        radius_dir_row = cmds.rowLayout(numberOfColumns=2)
        self.radius_dir_radio = cmds.radioCollection()
        cmds.radioButton(label="Positive", select=(self.radius_offset_dir == 1), onCommand=lambda x: setattr(self, 'radius_offset_dir', 1))
        cmds.radioButton(label="Negative", select=(self.radius_offset_dir == -1), onCommand=lambda x: setattr(self, 'radius_offset_dir', -1))
        cmds.setParent('..')
        cmds.setParent('..')
        
        # Set tab labels
        cmds.tabLayout(tabs, edit=True, tabLabel=((ulna_tab, "Ulna Settings"), (radius_tab, "Radius Settings")))
        
        # Create joints button
        cmds.setParent(main_layout)
        cmds.separator(height=10, style="double")
        cmds.button(label="Create", 
                   backgroundColor=[1, 1, 2],
                   height=40,
                   command=self.create_all_joints)
        
        # Show the window
        cmds.showWindow(self.window_name)
    

    # ── Prefix mirror map ────────────────────────────────────────────────
    MIRROR_PREFIX = {
        "FL_": "FR_", "FR_": "FL_",
        "BL_": "BR_", "BR_": "BL_",
        "L_":  "R_",  "R_":  "L_",
        "F_":  "F_",  "B_":  "B_",
        "C_":  "C_",
    }

    def get_mirror_prefix(self, prefix):
        """Return the mirrored prefix e.g. FL_ to FR_. Falls back to same."""
        return self.MIRROR_PREFIX.get(prefix, prefix)

    def mirror_locators(self):
        """
        Mirror the 4 source locators (Ulna_pos, Ulna_tgt, Radius_pos, Radius_tgt)
        listed in the UI fields to the opposite side.
          - Negates the chosen mirror axis in world translation.
          - Mirrors euler rotation appropriately for the chosen axis.
          - Creates new locators with the mirror prefix, grouped under
            <mirrorPrefix>Ulna_Radius_grp.
          - Switches the UI prefix to the mirror side ready for Create.
        """
        src_prefix = cmds.textField(self.prefix_field, query=True, text=True).strip()
        mir_prefix = self.get_mirror_prefix(src_prefix)
        axis       = self.mirror_axis
        axis_idx   = {"x": 0, "y": 1, "z": 2}[axis]

        # Collect source locator names from UI fields
        src_locators = []
        for top_f, bot_f in zip(self.top_locator_fields, self.bottom_locator_fields):
            src_locators.append(cmds.textField(top_f, query=True, text=True).strip())
            src_locators.append(cmds.textField(bot_f, query=True, text=True).strip())

        # Validate – all must exist
        missing  = [n for n in src_locators if n and not cmds.objExists(n)]
        not_set  = [n for n in src_locators if not n]

        if not_set:
            cmds.confirmDialog(
                title="Mirror – Empty Fields",
                message="Some locator fields are empty.\nFill all 4 Pos/Tgt fields before mirroring.",
                button="OK"
            )
            return

        if missing:
            cmds.confirmDialog(
                title="Mirror – Missing Locators",
                message=(
                    "Cannot mirror. These source locators do not exist in the scene:\n"
                    + "\n".join(missing)
                    + "\n\nCreate and position the source locators first, then mirror."
                ),
                button="OK"
            )
            return

        # Ensure mirror group exists
        mir_group = f"{mir_prefix}Ulna_Radius_grp"
        if not cmds.objExists(mir_group):
            cmds.group(empty=True, name=mir_group)

        created_pairs = []
        for src_name in src_locators:
            if not src_name:
                continue

            # Build mirrored name by swapping prefix
            if src_name.startswith(src_prefix):
                mir_name = mir_prefix + src_name[len(src_prefix):]
            else:
                mir_name = mir_prefix + src_name  # safety fallback

            # Delete old mirror if re-mirroring
            if cmds.objExists(mir_name):
                cmds.delete(mir_name)

            # Read source world transform
            src_t = cmds.xform(src_name, query=True, worldSpace=True, translation=True)
            src_r = cmds.xform(src_name, query=True, worldSpace=True, rotation=True)

            # --- Mirror translation: negate chosen axis ---
            mir_t = list(src_t)
            mir_t[axis_idx] = -src_t[axis_idx]

            # --- Mirror rotation ---
            # For X axis mirror (left/right): negate Y and Z euler angles
            # For Y axis mirror (top/bottom): negate X and Z euler angles
            # For Z axis mirror (front/back): negate X and Y euler angles
            mir_r = list(src_r)
            if axis == "x":
                mir_r[1] = -src_r[1]
                mir_r[2] = -src_r[2]
            elif axis == "y":
                mir_r[0] = -src_r[0]
                mir_r[2] = -src_r[2]
            else:  # z
                mir_r[0] = -src_r[0]
                mir_r[1] = -src_r[1]

            # Create the mirror locator
            mir_loc = cmds.spaceLocator(name=mir_name)[0]
            cmds.xform(mir_loc, worldSpace=True, translation=mir_t)
            cmds.xform(mir_loc, worldSpace=True, rotation=mir_r)

            # Parent into mirror group (unparent first if already parented elsewhere)
            try:
                cmds.parent(mir_loc, mir_group)
            except Exception:
                pass

            created_pairs.append((src_name, mir_name))

        # Switch the entire UI over to the mirror prefix so the user
        # can immediately click Create for the opposite side.
        self.set_prefix(mir_prefix)

        # Build a readable summary
        pair_lines = "\n".join(f"  {s}  ->  {m}" for s, m in created_pairs)
        cmds.confirmDialog(
            title="Mirror Complete",
            message=(
                f"Mirrored {len(created_pairs)} locators\n"
                f"Source prefix : {src_prefix}\n"
                f"Mirror prefix : {mir_prefix}\n"
                f"Mirror axis   : {axis.upper()}\n\n"
                f"{pair_lines}\n\n"
                f"UI is now set to '{mir_prefix}'.\n"
                f"Adjust the new locators if needed, then click Create."
            ),
            button="OK"
        )

    def create_locator_pair(self, bone_type, x_pos, y_pos, z_pos):
        """Create a pair of locators (pos and tgt) for the specified bone type"""
        self.prefix = cmds.textField(self.prefix_field, query=True, text=True)
        
        # Create parent group if it doesn't exist
        group_name = f"{self.prefix}Ulna_Radius_grp"
        if not cmds.objExists(group_name):
            cmds.group(empty=True, name=group_name)
        
        # Create position locator (top)
        pos_loc = f"{self.prefix}{bone_type}_pos"
        if cmds.objExists(pos_loc):
            cmds.delete(pos_loc)
        pos_loc = cmds.spaceLocator(name=pos_loc)[0]
        cmds.move(x_pos, y_pos + 2, z_pos, pos_loc)  # Position higher
        
        # Create target locator (bottom)
        tgt_loc = f"{self.prefix}{bone_type}_tgt"
        if cmds.objExists(tgt_loc):
            cmds.delete(tgt_loc)
        tgt_loc = cmds.spaceLocator(name=tgt_loc)[0]
        cmds.move(x_pos, y_pos, z_pos, tgt_loc)  # Position lower
        
        # Parent to group
        cmds.parent(pos_loc, tgt_loc, group_name)
        
        # Update the UI fields
        if bone_type == "Ulna":
            cmds.textField(self.top_locator_fields[0], edit=True, text=pos_loc)
            cmds.textField(self.bottom_locator_fields[0], edit=True, text=tgt_loc)
        else:  # Radius
            cmds.textField(self.top_locator_fields[1], edit=True, text=pos_loc)
            cmds.textField(self.bottom_locator_fields[1], edit=True, text=tgt_loc)
        
        cmds.select(clear=True)
    
    def get_selected(self, text_field):
        selection = cmds.ls(selection=True)
        if selection:
            cmds.textField(text_field, edit=True, text=selection[0])
        else:
            cmds.warning("Nothing selected")
    
    def create_all_joints(self, *args):
        self.offset_distance = cmds.floatField(self.offset_field, query=True, value=True)
        self.prefix = cmds.textField(self.prefix_field, query=True, text=True)
        
        # Create a parent group for all locators
        group_name = f"{self.prefix}Ulna_Radius_grp"
        if not cmds.objExists(group_name):
            cmds.group(empty=True, name=group_name)
        
        created_pairs = 0
        locators_to_group = []
        missing = []

        for i in range(len(self.top_locator_fields)):
            top_locator      = cmds.textField(self.top_locator_fields[i],       query=True, text=True).strip()
            bottom_locator   = cmds.textField(self.bottom_locator_fields[i],    query=True, text=True).strip()
            constraint_target = cmds.textField(self.constraint_target_fields[i], query=True, text=True).strip()

            # Check existence before attempting anything
            top_exists    = top_locator    and cmds.objExists(top_locator)
            bottom_exists = bottom_locator and cmds.objExists(bottom_locator)

            if top_locator and not top_exists:
                missing.append(top_locator)
            if bottom_locator and not bottom_exists:
                missing.append(bottom_locator)

            if top_exists:
                locators_to_group.append(top_locator)
            if bottom_exists:
                locators_to_group.append(bottom_locator)

            if top_exists and bottom_exists:
                result = self.create_joints_from_locators(top_locator, bottom_locator, constraint_target)
                if result:
                    created_pairs += 1

        # Parent all existing locators to the group
        for locator in locators_to_group:
            if cmds.objExists(locator) and cmds.listRelatives(locator, parent=True) != [group_name]:
                try:
                    cmds.parent(locator, group_name)
                except Exception as e:
                    cmds.warning(f"Could not parent {locator} to {group_name}: {e}")

        if created_pairs > 0:
            msg = f"Created {created_pairs} joint pair(s) successfully!\nAll locators grouped under {group_name}"
            if missing:
                msg += f"\n\nSkipped (not found in scene):\n" + "\n".join(missing)
            cmds.confirmDialog(title="Success", message=msg, button="OK")
        elif missing:
            msg = (
                f"No locators found in scene for prefix '{self.prefix}'.\n\n"
                f"Missing:\n" + "\n".join(missing) +
                f"\n\nFix: Click 'Create Ulna Locators' and 'Create Radius Locators' first,\n"
                f"or use the Choose buttons to select existing locators."
            )
            cmds.confirmDialog(title="Missing Locators", message=msg, button="OK")
        else:
            cmds.confirmDialog(title="Error", message="No locator names entered. Please fill in the Pos/Tgt fields or use the Create Locator buttons.", button="OK")
    
    def create_joints_from_locators(self, top_locator, bottom_locator, constraint_target=None):
        # Check if locators exist
        if not cmds.objExists(top_locator) or not cmds.objExists(bottom_locator):
            cmds.warning(f"Locators '{top_locator}' and/or '{bottom_locator}' do not exist in the scene.")
            return False
        
        # Get locator positions and rotations
        top_pos = cmds.xform(top_locator, query=True, worldSpace=True, translation=True)
        bottom_pos = cmds.xform(bottom_locator, query=True, worldSpace=True, translation=True)
        top_rot = cmds.xform(top_locator, query=True, worldSpace=True, rotation=True)
        bottom_rot = cmds.xform(bottom_locator, query=True, worldSpace=True, rotation=True)
        
        # Extract bone name from locator name
        bone_name = top_locator.replace("_pos", "") if "_pos" in top_locator else top_locator
        
        # Create joints with prefix
        cmds.select(clear=True)
        top_joint = cmds.joint(position=top_pos, name=f"{self.prefix}{bone_name}_root")
        cmds.xform(top_joint, rotation=top_rot, worldSpace=True)
        
        cmds.select(clear=True)
        bottom_joint = cmds.joint(position=bottom_pos, name=f"{self.prefix}{bone_name}_tip")
        cmds.xform(bottom_joint, rotation=bottom_rot, worldSpace=True)
        
        # Parent joints
        cmds.parent(bottom_joint, top_joint, absolute=True)
        
        # Handle special setup for Ulna and Radius
        if "Ulna" in top_locator:
            self.setup_ulna(top_locator, bottom_locator, top_pos, top_rot, constraint_target, top_joint, bottom_joint)
        elif "Radius" in top_locator:
            self.setup_radius(top_locator, bottom_locator, top_pos, top_rot, bottom_pos, bottom_rot, constraint_target, top_joint, bottom_joint)
        
        print(f"Created joint pair '{self.prefix}{bone_name}_root' and '{self.prefix}{bone_name}_tip' from locators")
        return True
    
    def setup_ulna(self, top_locator, bottom_locator, top_pos, top_rot, constraint_target, top_joint, bottom_joint):
        # Get the parent group
        group_name = f"{self.prefix}Ulna_Radius_grp"
        if not cmds.objExists(group_name):
            cmds.group(empty=True, name=group_name)
            
        # Create Ulna_up locator with prefix
        ulna_up = cmds.spaceLocator(name=f"{self.prefix}Ulna_up")[0]
        cmds.xform(ulna_up, translation=top_pos, rotation=top_rot, worldSpace=True)
        self.apply_offset(ulna_up, self.ulna_axis, self.ulna_offset_dir)
        
        # Create Ulna_aim locator with prefix
        ulna_aim = cmds.spaceLocator(name=f"{self.prefix}Ulna_aim")[0]
        cmds.xform(ulna_aim, translation=top_pos, rotation=top_rot, worldSpace=True)
        
        # Parent to the respective locators while maintaining world position
        cmds.parent(ulna_up, top_locator)
        cmds.parent(ulna_aim, top_locator)
        
        # Parent top joint to Ulna_aim
        cmds.parent(top_joint, ulna_aim)
        
        # Create aim constraint for Ulna
        if cmds.objExists(bottom_locator):
            self.create_aim_constraint(
                driver=bottom_locator,
                driven=ulna_aim,
                up_object=ulna_up,
                joint_chain=[top_joint, bottom_joint]
            )
        
        # Create parent constraint if target specified
        if constraint_target and cmds.objExists(constraint_target):
            self.create_parent_constraint(constraint_target, bottom_locator)
    
    def setup_radius(self, top_locator, bottom_locator, top_pos, top_rot, bottom_pos, bottom_rot, constraint_target, top_joint, bottom_joint):
        # Get the parent group
        group_name = f"{self.prefix}Ulna_Radius_grp"
        if not cmds.objExists(group_name):
            cmds.group(empty=True, name=group_name)
            
        # Create Radius_aim locator with prefix
        radius_aim = cmds.spaceLocator(name=f"{self.prefix}Radius_aim")[0]
        cmds.xform(radius_aim, translation=top_pos, rotation=top_rot, worldSpace=True)
        
        # Parent to the respective locators while maintaining world position
        cmds.parent(radius_aim, top_locator)
        
        # Parent top joint to Radius_aim
        cmds.parent(top_joint, radius_aim)
        
        # Create Radius_up locator with prefix
        if cmds.objExists(bottom_locator):
            radius_up = cmds.spaceLocator(name=f"{self.prefix}Radius_up")[0]
            cmds.xform(radius_up, translation=bottom_pos, rotation=bottom_rot, worldSpace=True)
            self.apply_offset(radius_up, self.radius_axis, self.radius_offset_dir)
            cmds.parent(radius_up, bottom_locator)
            
            # Create aim constraint for Radius
            self.create_aim_constraint(
                driver=bottom_locator,
                driven=radius_aim,
                up_object=radius_up,
                joint_chain=[top_joint, bottom_joint]
            )
        
        # Create parent constraint if target specified
        if constraint_target and cmds.objExists(constraint_target):
            self.create_parent_constraint(constraint_target, bottom_locator)
    
    def apply_offset(self, locator, axis, direction):
        """Apply offset to locator based on axis and direction"""
        distance = self.offset_distance * direction
        offset = [0, 0, 0]
        
        if axis == "x":
            offset[0] = distance
        elif axis == "y":
            offset[1] = distance
        else:  # z-axis
            offset[2] = distance
            
        cmds.move(offset[0], offset[1], offset[2], locator, relative=True, objectSpace=True)
    
    def create_aim_constraint(self, driver, driven, up_object, joint_chain):
        """Create aim constraint with automatic vector calculation"""
        if not all(cmds.objExists(obj) for obj in [driver, driven, up_object]):
            cmds.warning("Cannot create aim constraint - missing objects")
            return
        
        # Calculate vectors for constraint
        parent_pos = cmds.xform(joint_chain[0], q=True, ws=True, t=True)
        child_pos = cmds.xform(joint_chain[1], q=True, ws=True, t=True)
        
        # Calculate aim vector (direction from parent to child)
        aim_vector = self.normalize([
            child_pos[0] - parent_pos[0],
            child_pos[1] - parent_pos[1],
            child_pos[2] - parent_pos[2]
        ])
        
        # Determine which joint axis to use as up vector based on the bone direction
        if "Ulna" in joint_chain[0]:
            # Use the selected axis from UI for Ulna
            up_axis = self.ulna_axis
            up_dir = self.ulna_offset_dir
        else:  # Radius or other
            # Use the selected axis from UI for Radius
            up_axis = self.radius_axis
            up_dir = self.radius_offset_dir
        
        # Set the up vector based on the joint's up axis
        up_vector = [0, 0, 0]
        if up_axis == "x":
            up_vector = [1 * up_dir, 0, 0]
        elif up_axis == "y":
            up_vector = [0, 1 * up_dir, 0]
        else:  # z-axis
            up_vector = [0, 0, 1 * up_dir]
        
        # Create constraint
        constraint = cmds.aimConstraint(
            driver,
            driven,
            maintainOffset=True,
            aimVector=aim_vector,
            upVector=up_vector,
            worldUpType="object",
            worldUpObject=up_object
        )
        
        # Clean up naming
        cmds.rename(constraint, f"{driven}_aimConstraint")
    
    def normalize(self, vector):
        """Normalize a vector"""
        length = sum(v*v for v in vector)**0.5
        if length > 0:
            return [v/length for v in vector]
        return [0, 1, 0]  # Default to Y-up if vector has zero length
    
    def create_parent_constraint(self, driver, driven):
        """Create parent constraint between driver and driven objects"""
        if not cmds.objExists(driver) or not cmds.objExists(driven):
            cmds.warning(f"Cannot create parent constraint - missing objects")
            return
        
        constraint = cmds.parentConstraint(
            driver,
            driven,
            maintainOffset=True,
            weight=1.0
        )
        
        # Clean up naming
        cmds.rename(constraint, f"{driven}_parentConstraint")

# Launch the UI
ui = LocatorToJointsUI()