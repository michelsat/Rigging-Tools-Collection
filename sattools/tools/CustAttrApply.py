import maya.cmds as cmds
import json

def reset_custom_attributes():
    stored_attributes_str = cmds.optionVar(query="storedAttributes")
    if not stored_attributes_str:
        print("No stored attributes found. Please run the store script first.")
        return

    stored_attributes = json.loads(stored_attributes_str)
    
    for ctrl, attributes in stored_attributes.items():
        if cmds.objExists(ctrl):
            for attr, value in attributes.items():
                if cmds.attributeQuery(attr, node=ctrl, exists=True):
                    cmds.setAttr(f"{ctrl}.{attr}", value)
                else:
                    print(f"Attribute {attr} does not exist on {ctrl}")
        else:
            print(f"Controller {ctrl} does not exist in the scene")

    print("\nAttributes have been reset to stored values.")

# Execute the function
reset_custom_attributes()
