import maya.cmds as cmds
import json

def store_custom_attributes():
    selected_controls = cmds.ls(selection=True)
    
    if not selected_controls:
        print("No controls selected.")
        return
    
    stored_attributes = {}

    for ctrl in selected_controls:
        attributes = cmds.listAttr(ctrl, userDefined=True)
        
        if attributes:
            stored_attributes[ctrl] = {}
            for attr in attributes:
                try:
                    attr_value = cmds.getAttr(f"{ctrl}.{attr}")
                    stored_attributes[ctrl][attr] = attr_value
                except Exception as e:
                    print(f"Error retrieving value for attribute {attr} on {ctrl}: {e}")
        else:
            print(f"No custom attributes found on {ctrl}.")
    
    # Store the attribute values in Maya's optionVar
    cmds.optionVar(sv=("storedAttributes", json.dumps(stored_attributes)))
    print("\nCustom attributes and their values have been stored.")

# Execute the function
store_custom_attributes()
