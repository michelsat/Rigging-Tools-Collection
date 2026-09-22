import maya.cmds as cmds

def connect_matrix_nodes(*args):
    selected = cmds.ls(selection=True)
    total_nodes = len(selected)
    
    if total_nodes < 2 or total_nodes % 2 != 0:
        cmds.warning("Please select an even number of nodes (source1, target1, source2, target2, etc.)")
        return
    
    # Split selection into pairs
    pairs = [(selected[i], selected[i+1]) for i in range(0, total_nodes, 2)]
    
    for transform, mult_matrix in pairs:
        try:
            cmds.connectAttr(f"{transform}.parentInverseMatrix[0]", f"{mult_matrix}.matrixIn[1]")
            print(f"Connected {transform} to {mult_matrix}")
        except Exception as e:
            cmds.warning(f"Error connecting {transform} to {mult_matrix}: {str(e)}")

def connect_decompose_to_transform(*args):
    selected = cmds.ls(selection=True)
    total_nodes = len(selected)
    
    if total_nodes < 2 or total_nodes % 2 != 0:
        cmds.warning("Please select an even number of nodes (source1, target1, source2, target2, etc.)")
        return
    
    pairs = [(selected[i], selected[i+1]) for i in range(0, total_nodes, 2)]
    
    for decompose, transform in pairs:
        try:
            cmds.connectAttr(f"{decompose}.outputTranslate", f"{transform}.translate")
            cmds.connectAttr(f"{decompose}.outputRotate", f"{transform}.rotate")
            print(f"Connected {decompose} to {transform}")
        except Exception as e:
            cmds.warning(f"Error connecting {decompose} to {transform}: {str(e)}")

def connect_four_by_four(*args):
    selected = cmds.ls(selection=True)
    total_nodes = len(selected)
    
    if total_nodes < 2 or total_nodes % 2 != 0:
        cmds.warning("Please select an even number of nodes (source1, target1, source2, target2, etc.)")
        return
    
    pairs = [(selected[i], selected[i+1]) for i in range(0, total_nodes, 2)]
    
    for four_by_four, mult_matrix in pairs:
        try:
            cmds.connectAttr(f"{four_by_four}.output", f"{mult_matrix}.matrixIn[0]")
            print(f"Connected {four_by_four} to {mult_matrix}")
        except Exception as e:
            cmds.warning(f"Error connecting {four_by_four} to {mult_matrix}: {str(e)}")

def connect_mult_to_decompose(*args):
    selected = cmds.ls(selection=True)
    total_nodes = len(selected)
    
    if total_nodes < 2 or total_nodes % 2 != 0:
        cmds.warning("Please select an even number of nodes (source1, target1, source2, target2, etc.)")
        return
    
    pairs = [(selected[i], selected[i+1]) for i in range(0, total_nodes, 2)]
    
    for mult_matrix, decompose in pairs:
        try:
            cmds.connectAttr(f"{mult_matrix}.matrixSum", f"{decompose}.inputMatrix")
            print(f"Connected {mult_matrix} to {decompose}")
        except Exception as e:
            cmds.warning(f"Error connecting {mult_matrix} to {decompose}: {str(e)}")

def connect_point_on_surface_to_matrix(*args):
    selected = cmds.ls(selection=True)
    total_nodes = len(selected)
    
    if total_nodes < 2 or total_nodes % 2 != 0:
        cmds.warning("Please select an even number of nodes (source1, target1, source2, target2, etc.)")
        return
    
    pairs = [(selected[i], selected[i+1]) for i in range(0, total_nodes, 2)]
    
    for pos_info, four_matrix in pairs:
        try:
            # Position connections
            cmds.connectAttr(f"{pos_info}.positionX", f"{four_matrix}.in30")
            cmds.connectAttr(f"{pos_info}.positionY", f"{four_matrix}.in31")
            cmds.connectAttr(f"{pos_info}.positionZ", f"{four_matrix}.in32")
            
            # Normal connections
            cmds.connectAttr(f"{pos_info}.normalizedNormalX", f"{four_matrix}.in00")
            cmds.connectAttr(f"{pos_info}.normalizedNormalY", f"{four_matrix}.in01")
            cmds.connectAttr(f"{pos_info}.normalizedNormalZ", f"{four_matrix}.in02")
            
            # Tangent U connections
            cmds.connectAttr(f"{pos_info}.normalizedTangentUX", f"{four_matrix}.in10")
            cmds.connectAttr(f"{pos_info}.normalizedTangentUY", f"{four_matrix}.in11")
            cmds.connectAttr(f"{pos_info}.normalizedTangentUZ", f"{four_matrix}.in12")
            
            # Tangent V connections
            cmds.connectAttr(f"{pos_info}.normalizedTangentVX", f"{four_matrix}.in20")
            cmds.connectAttr(f"{pos_info}.normalizedTangentVY", f"{four_matrix}.in21")
            cmds.connectAttr(f"{pos_info}.normalizedTangentVZ", f"{four_matrix}.in22")
            
            print(f"Connected {pos_info} to {four_matrix}")
        except Exception as e:
            cmds.warning(f"Error connecting {pos_info} to {four_matrix}: {str(e)}")

def create_matrix_ui():
    # Check if window exists
    if cmds.window("matrixConnectorUI", exists=True):
        cmds.deleteUI("matrixConnectorUI")
    
    # Create window
    window = cmds.window("matrixConnectorUI", title="Matrix Connector", sizeable=True)
    
    # Create main layout
    main_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=5, columnAttach=('both', 5))
    
    # Add buttons with full width
    cmds.button(label="Connect Parent Inverse Matrix", command=connect_matrix_nodes, width=200)
    cmds.button(label="Connect Decompose Outputs", command=connect_decompose_to_transform, width=200)
    cmds.button(label="Connect Four By Four Matrix", command=connect_four_by_four, width=200)
    cmds.button(label="Connect Point On Surface", command=connect_point_on_surface_to_matrix, width=200)
    cmds.button(label="Connect MultMatrix to Decompose", command=connect_mult_to_decompose, width=200)
    
    # Add help text
    cmds.text(label="\nSelection Instructions:", align="left", font="boldLabelFont")
    cmds.text(label="Parent Inverse: select transforms then multMatrices", align="left", width=300)
    cmds.text(label="Decompose: select decomposeMatrices then transforms", align="left", width=300)
    cmds.text(label="Four By Four: select fourByFourMatrices then multMatrices", align="left", width=300)
    cmds.text(label="Point On Surface: select pointOnSurfaces then fourByFourMatrices", align="left", width=300)
    cmds.text(label="MultMatrix to Decompose: select multMatrices then decomposeMatrices", align="left", width=300)
    
    # Add multiple selection info
    cmds.text(label="\nMultiple Selection:", align="left", font="boldLabelFont")
    cmds.text(label="Select nodes in pairs (source1, target1, source2, target2, etc.)", align="left", width=300)
    
    # Show window
    cmds.showWindow(window)

# Create the UI when script is run
if __name__ == "__main__":
    create_matrix_ui()