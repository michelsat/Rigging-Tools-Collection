import re
import time
from maya import cmds

def parseVtxIdx(idxList):
    """Convert vertex index list from strings to indexes."""
    parseIdxList = []
    if not idxList:
        return parseIdxList
        
    for idxName in idxList:
        match = re.search(r'\[.+\]', idxName)
        if match:
            content = match.group()[1:-1]
            if ':' in content:
                tokens = content.split(':')
                startTok = int(tokens[0])
                endTok = int(tokens[1])
                for rangeIdx in range(startTok, endTok + 1):
                    parseIdxList.append(rangeIdx)
            else:
                parseIdxList.append(int(content))

    return parseIdxList


def recoverMesh(bsNode, weightIdx, startTime, totalTargets, currentTarget, progressBar, progressLabel):
    """Recover a single blendshape target using native maya.cmds."""
    cmds.setAttr(f"{bsNode}.envelope", 0)

    # Get target alias name
    aliasName = cmds.aliasAttr(f"{bsNode}.weight[{weightIdx}]", query=True)
    print(f"Processing blendshape target: {aliasName} (Index: {weightIdx})")

    # Find connected meshes natively
    finalMeshes = cmds.listHistory(bsNode, future=True, type="mesh") or []
    
    finalParent = None
    newParent = None

    if finalMeshes:
        parents = cmds.listRelatives(finalMeshes[0], parent=True, fullPath=True)
        if parents:
            finalParent = parents[0]

    if finalParent:
        newParent = cmds.createNode('transform', name=aliasName)
        constraint = cmds.parentConstraint(finalParent, newParent, mo=False)[0]
        cmds.delete(constraint)

    for finalIdx, finalMesh in enumerate(finalMeshes):
        newMesh = cmds.duplicate(finalMesh)[0]
        shapes = cmds.listRelatives(newMesh, shapes=True, fullPath=True)
        newMeshShape = shapes[0] if shapes else None

        # Format attribute strings
        pts_attr = f"{bsNode}.inputTarget[{finalIdx}].inputTargetGroup[{weightIdx}].inputTargetItem[6000].inputPointsTarget"
        comps_attr = f"{bsNode}.inputTarget[{finalIdx}].inputTargetGroup[{weightIdx}].inputTargetItem[6000].inputComponentsTarget"

        # Safely attempt fetching deltas (bypasses targets with no mesh edits)
        try:
            vtxDeltaList = cmds.getAttr(pts_attr)
            vtxIdxList = cmds.getAttr(comps_attr)
        except ValueError:
            vtxDeltaList = None
            vtxIdxList = None

        if vtxIdxList and vtxDeltaList:
            singleIdxList = parseVtxIdx(vtxIdxList)
            print(f"Applying deltas to {len(singleIdxList)} vertices for mesh: {finalMesh}")

            for vtxIdx, moveAmount in zip(singleIdxList, vtxDeltaList):
                cmds.move(moveAmount[0], moveAmount[1], moveAmount[2], f"{newMesh}.vtx[{vtxIdx}]", relative=True)

        if newMeshShape:
            geom_attr = f"{bsNode}.inputTarget[{finalIdx}].inputTargetGroup[{weightIdx}].inputTargetItem[6000].inputGeomTarget"
            try:
                cmds.connectAttr(f"{newMeshShape}.worldMesh[0]", geom_attr, force=True)
            except RuntimeError:
                pass # Bypass if the connection is already active or locked

        if newParent:
            cmds.parent(newMesh, newParent)
            cmds.rename(newMesh, finalMesh.split('|')[-1])
        else:
            cmds.rename(newMesh, aliasName)
            if cmds.listRelatives(newMesh, parent=True):
                cmds.parent(newMesh, world=True)

    cmds.setAttr(f"{bsNode}.envelope", 1)

    # Update progress bar and label
    elapsedTime = time.time() - startTime
    progress = (currentTarget + 1) / totalTargets * 100
    avgTimePerTarget = elapsedTime / (currentTarget + 1) if (currentTarget + 1) > 0 else 0
    remainingTime = avgTimePerTarget * (totalTargets - currentTarget - 1)

    cmds.progressBar(progressBar, edit=True, progress=progress)
    cmds.text(progressLabel, edit=True, label=f"Progress: {progress:.2f}% | Elapsed: {elapsedTime:.2f}s | Remaining: {remainingTime:.2f}s")

    return newParent if newParent else finalMeshes[0] if finalMeshes else None


def recoverAllBlendshapes(bsNode, progressBar, progressLabel):
    """Recover all blendshape targets from the given blendshape node."""
    # Find active weight indices
    weight_indices = cmds.getAttr(f"{bsNode}.weight", multiIndices=True) or []
    numTargets = len(weight_indices)
    
    print(f"Found {numTargets} blendshape targets in {bsNode}")
    startTime = time.time()

    for idx, weightIdx in enumerate(weight_indices):
        recoverMesh(bsNode, weightIdx, startTime, numTargets, idx, progressBar, progressLabel)

    # Close the progress bar when done
    cmds.progressBar(progressBar, edit=True, endProgress=True)
    cmds.text(progressLabel, edit=True, label="Extraction Complete!")


def createUI():
    """Create a UI with a progress bar and start button."""
    windowName = "blendshapeExtractorUI"
    if cmds.window(windowName, exists=True):
        cmds.deleteUI(windowName)

    cmds.window(windowName, title="Blendshape Extractor", widthHeight=(400, 100))
    cmds.columnLayout(adjustableColumn=True)

    # Progress Bar
    progressBar = cmds.progressBar(maxValue=100, width=380)

    # Progress Label
    progressLabel = cmds.text(label="Progress: 0.00% | Elapsed: 0.00s | Remaining: 0.00s")

    # Start Button
    cmds.button(label="Start Extraction", command=lambda *args: startExtraction(progressBar, progressLabel))
    cmds.showWindow(windowName)


def startExtraction(progressBar, progressLabel):
    """Start the blendshape extraction process."""
    blendShapeNode = cmds.ls(selection=True, type="blendShape")
    if not blendShapeNode:
        cmds.warning("Please select a blendShape node.")
        return

    recoverAllBlendshapes(blendShapeNode[0], progressBar, progressLabel)


# Run the UI
createUI()