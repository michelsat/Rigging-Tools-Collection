import maya.cmds as cmds

def generate_values(*args):
    num_objects = cmds.intField("numObjects", query=True, value=True)
    start_value = cmds.floatField("startValue", query=True, value=True)
    end_value = cmds.floatField("endValue", query=True, value=True)
    attribute_name = cmds.textField("attributeName", query=True, text=True)

    step = (end_value - start_value) / (num_objects - 1)

    values = {f"{attribute_name}_{i + 1}": round(start_value + (step * i), 4) for i in range(num_objects)}

    cmds.scrollField("outputField", edit=True, text="\n".join([f"{key} = {value}" for key, value in values.items()]))

def create_ui():
    if cmds.window("valueDistributorUI", exists=True):
        cmds.deleteUI("valueDistributorUI")

    cmds.window("valueDistributorUI", title="Value Distributor", widthHeight=(400, 300))
    
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label="Number of Objects:")
    cmds.intField("numObjects", value=16)

    cmds.text(label="Start Value:")
    cmds.floatField("startValue", value=0.0)

    cmds.text(label="End Value:")
    cmds.floatField("endValue", value=1.0)

    cmds.text(label="Attribute Name:")
    cmds.textField("attributeName", text="bindjoints")

    cmds.button(label="Generate Values", command=generate_values)

    # Make the scrollField stretch when the UI expands
    cmds.formLayout("formLayout", width=400, height=200)
    output_field = cmds.scrollField("outputField", editable=False, wordWrap=True)

    cmds.formLayout("formLayout", edit=True,
                    attachForm=[(output_field, 'top', 5), (output_field, 'left', 5),
                                (output_field, 'right', 5), (output_field, 'bottom', 5)])

    cmds.showWindow("valueDistributorUI")

create_ui()