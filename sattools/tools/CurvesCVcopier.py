"""
CurvesCVcopier
--------------
Copies the CV positions of a SOURCE nurbs-curve controller onto a TARGET
controller that has the same number of CVs (same shape count, same CV order).

Usage (Maya Python):
    from sattools.tools import CurvesCVcopier
    CurvesCVcopier.show()

    1. Select the SOURCE controller -> "Load Source"
    2. Select the TARGET controller -> "Load Target"
    3. Click "Copy CV -> Paste CV"
"""

import maya.cmds as cmds

WIN = "curvesCVcopierWin"
SRC_FIELD = "curvesCVcopierSrc"
TGT_FIELD = "curvesCVcopierTgt"
SPACE_RB = "curvesCVcopierSpace"


# ---------------------------------------------------------------- helpers
def get_curve_shapes(node):
    """Return all non-intermediate nurbsCurve shapes for a transform or shape."""
    if not cmds.objExists(node):
        return []
    if cmds.nodeType(node) == "nurbsCurve":
        return [node]
    shapes = cmds.listRelatives(
        node, shapes=True, type="nurbsCurve", noIntermediate=True, fullPath=True
    )
    return shapes or []


def get_cvs(shape):
    """Return flattened list of CV components of a curve shape."""
    return cmds.ls(shape + ".cv[*]", flatten=True) or []


def _selected_transform():
    sel = cmds.ls(selection=True, long=True, objectsOnly=True)
    if not sel:
        cmds.warning("Nothing selected.")
        return None
    node = sel[0]
    if not get_curve_shapes(node):
        cmds.warning("'{}' has no nurbsCurve shape.".format(node))
        return None
    if cmds.nodeType(node) == "nurbsCurve":
        node = cmds.listRelatives(node, parent=True, fullPath=True)[0]
    return node


# ---------------------------------------------------------------- core
def copy_paste_cvs(source, target, space="world"):
    """Copy CV positions from source curve(s) to target curve(s)."""
    src_shapes = get_curve_shapes(source)
    tgt_shapes = get_curve_shapes(target)

    if not src_shapes or not tgt_shapes:
        cmds.warning("Source or target has no curve shapes.")
        return False

    if len(src_shapes) != len(tgt_shapes):
        cmds.warning(
            "Shape count mismatch: source has {}, target has {}.".format(
                len(src_shapes), len(tgt_shapes)
            )
        )
        return False

    # validate first so nothing is half-applied
    for s, t in zip(src_shapes, tgt_shapes):
        if len(get_cvs(s)) != len(get_cvs(t)):
            cmds.warning("CV count mismatch between {} and {}.".format(s, t))
            return False

    use_ws = space == "world"
    cmds.undoInfo(openChunk=True, chunkName="copyPasteCVs")
    try:
        for s, t in zip(src_shapes, tgt_shapes):
            for scv, tcv in zip(get_cvs(s), get_cvs(t)):
                if use_ws:
                    pos = cmds.xform(scv, query=True, worldSpace=True, translation=True)
                    cmds.xform(tcv, worldSpace=True, translation=pos)
                else:
                    pos = cmds.xform(scv, query=True, objectSpace=True, translation=True)
                    cmds.xform(tcv, objectSpace=True, translation=pos)
    finally:
        cmds.undoInfo(closeChunk=True)

    return True


# ---------------------------------------------------------------- UI
def _load(field):
    node = _selected_transform()
    if node:
        cmds.textFieldButtonGrp(field, edit=True, text=node)


def _swap(*_):
    s = cmds.textFieldButtonGrp(SRC_FIELD, query=True, text=True)
    t = cmds.textFieldButtonGrp(TGT_FIELD, query=True, text=True)
    cmds.textFieldButtonGrp(SRC_FIELD, edit=True, text=t)
    cmds.textFieldButtonGrp(TGT_FIELD, edit=True, text=s)


def _run(*_):
    src = cmds.textFieldButtonGrp(SRC_FIELD, query=True, text=True)
    tgt = cmds.textFieldButtonGrp(TGT_FIELD, query=True, text=True)

    if not src or not tgt:
        cmds.warning("Load both a source and a target controller.")
        return
    if src == tgt:
        cmds.warning("Source and target are the same object.")
        return

    space = "world" if cmds.radioButtonGrp(SPACE_RB, query=True, select=True) == 1 else "object"
    if copy_paste_cvs(src, tgt, space):
        cmds.inViewMessage(
            amg="CVs copied: <hl>{}</hl>  ->  <hl>{}</hl>".format(
                src.split("|")[-1], tgt.split("|")[-1]
            ),
            pos="midCenter",
            fade=True,
        )


def show():
    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN)

    cmds.window(WIN, title="Curves CV Copier", widthHeight=(420, 190), sizeable=False)
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnOffset=("both", 8))

    cmds.separator(height=6, style="none")
    cmds.textFieldButtonGrp(
        SRC_FIELD, label="Source (copy)", buttonLabel="Load Source",
        editable=False, columnWidth3=(85, 210, 90),
        buttonCommand=lambda *_: _load(SRC_FIELD),
    )
    cmds.textFieldButtonGrp(
        TGT_FIELD, label="Target (paste)", buttonLabel="Load Target",
        editable=False, columnWidth3=(85, 210, 90),
        buttonCommand=lambda *_: _load(TGT_FIELD),
    )
    cmds.radioButtonGrp(
        SPACE_RB, label="Space", labelArray2=["World", "Object"],
        numberOfRadioButtons=2, select=1, columnWidth3=(85, 100, 100),
    )
    cmds.separator(height=4)
    cmds.button(label="Copy CV  ->  Paste CV", height=36,
                backgroundColor=(0.3, 0.55, 0.3), command=_run)
    cmds.button(label="Swap Source / Target", height=24, command=_swap)

    cmds.showWindow(WIN)


if __name__ == "__main__":
    show()
