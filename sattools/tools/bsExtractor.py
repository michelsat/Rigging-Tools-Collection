import pymel.core as pm
import re
import time
from maya import cmds

def parseVtxIdx(idxList):
    """Convert vertex index list from strings to indexes."""
    parseIdxList = []

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
    """Recover a single blendshape target with progress tracking."""
    bsNode = pm.PyNode(bsNode)
    bsNode.envelope.set(0)

    aliasName = pm.aliasAttr(bsNode.weight[weightIdx], query=True)
    print(f"Processing blendshape target: {aliasName} (Index: {weightIdx})")

    finalMeshes = pm.listFuture(bsNode, type="mesh")
    
    finalParent = None
    newParent = None

    if len(finalMeshes) > 1:
        finalParent = finalMeshes[0].getParent()

    if finalParent:
        newParent = pm.createNode('transform')
        pm.rename(newParent, aliasName)
        pm.delete(pm.parentConstraint(finalParent, newParent, mo=0))

    for finalIdx, finalMesh in enumerate(finalMeshes):
        newMesh = pm.duplicate(finalMesh)[0]
        newMeshShape = newMesh.getShape()

        vtxDeltaList = bsNode.inputTarget[finalIdx].inputTargetGroup[weightIdx].inputTargetItem[6000].inputPointsTarget.get()
        vtxIdxList = bsNode.inputTarget[finalIdx].inputTargetGroup[weightIdx].inputTargetItem[6000].inputComponentsTarget.get()

        if vtxIdxList:
            singleIdxList = parseVtxIdx(vtxIdxList)
            print(f"Applying deltas to {len(singleIdxList)} vertices for mesh: {finalMesh.name()}")

            for vtxIdx, moveAmount in zip(singleIdxList, vtxDeltaList):
                pm.move('%s.vtx[%d]' % (newMesh.name(), vtxIdx), moveAmount, r=1)

        newMeshShape.worldMesh[0] >> bsNode.inputTarget[finalIdx].inputTargetGroup[weightIdx].inputTargetItem[6000].inputGeomTarget

        if newParent:
            pm.parent(newMesh, newParent)
            pm.rename(newMesh, finalMesh.name())
        else:
            pm.rename(newMesh, aliasName)
            if newMesh.getParent():
                pm.parent(newMesh, world=1)

    bsNode.envelope.set(1)

    # Update progress bar and label
    elapsedTime = time.time() - startTime
    progress = (currentTarget + 1) / totalTargets * 100
    avgTimePerTarget = elapsedTime / (currentTarget + 1)
    remainingTime = avgTimePerTarget * (totalTargets - currentTarget - 1)

    cmds.progressBar(progressBar, edit=True, progress=progress)
    cmds.text(progressLabel, edit=True, label=f"Progress: {progress:.2f}% | Elapsed: {elapsedTime:.2f}s | Remaining: {remainingTime:.2f}s")

    if newParent:
        return newParent
    elif newMesh:
        return newMesh


def recoverAllBlendshapes(bsNode, progressBar, progressLabel):
    """Recover all blendshape targets from the given blendshape node with progress tracking."""
    bsNode = pm.PyNode(bsNode)
    numTargets = bsNode.weight.numElements()
    print(f"Found {numTargets} blendshape targets in {bsNode.name()}")

    startTime = time.time()

    for weightIdx in range(numTargets):
        recoverMesh(bsNode, weightIdx, startTime, numTargets, weightIdx, progressBar, progressLabel)

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

    blendShapeNode = blendShapeNode[0]
    recoverAllBlendshapes(blendShapeNode, progressBar, progressLabel)


# Run the UI
createUI()