import maya.cmds as cmds
import math

def create_center_locator(locator1, locator2, new_locator_name="center_locator"):
    # Get the positions of the two locators
    pos1 = cmds.xform(locator1, query=True, worldSpace=True, translation=True)
    pos2 = cmds.xform(locator2, query=True, worldSpace=True, translation=True)

    # Get the rotations of the two locators (in degrees)
    rot1 = cmds.xform(locator1, query=True, worldSpace=True, rotation=True)
    rot2 = cmds.xform(locator2, query=True, worldSpace=True, rotation=True)

    # Calculate the center point between the two locators
    center_pos = [(pos1[0] + pos2[0]) / 2, 
                 (pos1[1] + pos2[1]) / 2, 
                 (pos1[2] + pos2[2]) / 2]

    # Calculate the average rotation (in degrees)
    # Handle the case where rotations might be more than 180 degrees apart
    avg_rot = []
    for i in range(3):
        # Convert angles to radians for calculation
        angle1 = math.radians(rot1[i])
        angle2 = math.radians(rot2[i])
        
        # Calculate the average using circular interpolation
        x = (math.cos(angle1) + math.cos(angle2)) / 2
        y = (math.sin(angle1) + math.sin(angle2)) / 2
        
        # Convert back to degrees
        avg_angle = math.degrees(math.atan2(y, x))
        avg_rot.append(avg_angle)

    # Create a new locator at the center point
    new_locator = cmds.spaceLocator(name=new_locator_name)[0]
    
    # Set position and rotation
    cmds.xform(new_locator, worldSpace=True, translation=center_pos)
    cmds.xform(new_locator, worldSpace=True, rotation=avg_rot)

    return new_locator

# Example usage:
# Make sure you have two locators in your scene
locator1 = "locator1"  # Replace with the name of the first locator
locator2 = "locator2"  # Replace with the name of the second locator

new_locator = create_center_locator(locator1, locator2)
print(f"New locator created at the center: {new_locator}")