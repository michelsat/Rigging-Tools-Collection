# CurvesCVcopier (batch version)
# ------------------------------------------------------------------
# Copies CV positions from SOURCE nurbs-curve controllers onto TARGET
# controllers. Sources and targets are paired by list position
# (1st source -> 1st target, 2nd -> 2nd, ...). Each pair must have the
# same shape count and the same CV count per shape.
#
# Usage (Maya Python):
#     from sattools.tools import CurvesCVcopier
#     CurvesCVcopier.show()
#
#   1. Select the SOURCE controllers in order  -> 'Load Sources'
#   2. Select the TARGET controllers, same order -> 'Load Targets'
#      (or use 'Auto-match targets by name' to find them by search/replace)
#   3. Check the two lists line up, then click 'Copy CVs (Batch)'

import re
import maya.cmds as cmds

WIN = 'curvesCVcopierWin'
SRC_LIST = 'curvesCVcopierSrcList'
TGT_LIST = 'curvesCVcopierTgtList'
SPACE_RB = 'curvesCVcopierSpace'
ORDER_MENU = 'curvesCVcopierOrder'
SEARCH_FLD = 'curvesCVcopierSearch'
REPLACE_FLD = 'curvesCVcopierReplace'
STATUS_TXT = 'curvesCVcopierStatus'

_DATA = {'src': [], 'tgt': []}   # long names, same order as the lists
_LISTS = {'src': SRC_LIST, 'tgt': TGT_LIST}


# ---------------------------------------------------------------- helpers
def _short(name):
    return name.split('|')[-1]


def _natural_key(name):
    return [int(t) if t.isdigit() else t.lower() for t in re.split('([0-9]+)', _short(name))]


def get_curve_shapes(node):
    if not cmds.objExists(node):
        return []
    if cmds.nodeType(node) == 'nurbsCurve':
        return [node]
    return cmds.listRelatives(node, shapes=True, type='nurbsCurve',
                              noIntermediate=True, fullPath=True) or []


def get_cvs(shape):
    return cmds.ls(shape + '.cv[*]', flatten=True) or []


def selected_curve_transforms(alphabetical=False):
    # curve transforms from the current selection, in selection order
    sel = cmds.ls(orderedSelection=True, long=True, objectsOnly=True) or []
    out, skipped = [], []
    for node in sel:
        if cmds.nodeType(node) == 'nurbsCurve':
            parent = cmds.listRelatives(node, parent=True, fullPath=True)
            node = parent[0] if parent else node
        if not get_curve_shapes(node):
            skipped.append(_short(node))
            continue
        if node not in out:
            out.append(node)
    if skipped:
        cmds.warning('Skipped (no curve shape): ' + ', '.join(skipped))
    if alphabetical:
        out.sort(key=_natural_key)
    return out


# ---------------------------------------------------------------- core
def _check_pair(source, target):
    # returns None if the pair is valid, otherwise a reason string
    if source == target:
        return 'source and target are the same object'
    ss, ts = get_curve_shapes(source), get_curve_shapes(target)
    if not ss:
        return 'source has no curve shape'
    if not ts:
        return 'target has no curve shape'
    if len(ss) != len(ts):
        return 'shape count differs ({} vs {})'.format(len(ss), len(ts))
    for s, t in zip(ss, ts):
        a, b = len(get_cvs(s)), len(get_cvs(t))
        if a != b:
            return 'CV count differs ({} vs {})'.format(a, b)
    return None


def _copy_pair(source, target, space):
    use_ws = (space == 'world')
    for s, t in zip(get_curve_shapes(source), get_curve_shapes(target)):
        for scv, tcv in zip(get_cvs(s), get_cvs(t)):
            if use_ws:
                pos = cmds.xform(scv, query=True, worldSpace=True, translation=True)
                cmds.xform(tcv, worldSpace=True, translation=pos)
            else:
                pos = cmds.xform(scv, query=True, objectSpace=True, translation=True)
                cmds.xform(tcv, objectSpace=True, translation=pos)


def batch_copy(pairs, space='world'):
    # pairs: list of (source, target). Returns (done, failed).
    # Invalid pairs are skipped and reported; everything is one undo step.
    done, failed = [], []
    cmds.undoInfo(openChunk=True, chunkName='batchCopyCVs')
    try:
        for src, tgt in pairs:
            reason = _check_pair(src, tgt)
            if reason:
                failed.append((src, tgt, reason))
                continue
            _copy_pair(src, tgt, space)
            done.append((src, tgt))
    finally:
        cmds.undoInfo(closeChunk=True)
    return done, failed


def copy_paste_cvs(source, target, space='world'):
    # single-pair convenience for scripting
    done, failed = batch_copy([(source, target)], space)
    for s, t, reason in failed:
        cmds.warning('{} -> {}: {}'.format(_short(s), _short(t), reason))
    return bool(done)


def match_targets_by_name(sources, search, replace):
    # returns (matched_sources, matched_targets, problems)
    srcs, tgts, problems = [], [], []
    for src in sources:
        name = _short(src)
        if search not in name:
            problems.append('{}: name does not contain the search text'.format(name))
            continue
        new_name = name.replace(search, replace)
        found = [f for f in (cmds.ls(new_name, long=True) or [])
                 if f != src and get_curve_shapes(f)]
        if len(found) == 1:
            srcs.append(src)
            tgts.append(found[0])
        elif not found:
            problems.append('{}: no target curve named {}'.format(name, new_name))
        else:
            problems.append('{}: {} curves share the name {}'.format(name, len(found), new_name))
    return srcs, tgts, problems


# ---------------------------------------------------------------- UI logic
def _update_status(extra=''):
    ns, nt = len(_DATA['src']), len(_DATA['tgt'])
    if not ns and not nt:
        txt = 'Load sources and targets.'
    elif ns == nt:
        txt = '{} sets ready.'.format(ns)
    else:
        txt = 'COUNT MISMATCH: {} sources / {} targets.'.format(ns, nt)
    if cmds.text(STATUS_TXT, exists=True):
        cmds.text(STATUS_TXT, edit=True, label=(txt + ' ' + extra).strip())


def _refresh_lists(extra=''):
    for key, ctl in _LISTS.items():
        cmds.textScrollList(ctl, edit=True, removeAll=True)
        for i, n in enumerate(_DATA[key], 1):
            cmds.textScrollList(ctl, edit=True, append='{:02d}   {}'.format(i, _short(n)))
    _update_status(extra)


def _load(key):
    alpha = cmds.optionMenuGrp(ORDER_MENU, query=True, select=True) == 2
    nodes = selected_curve_transforms(alpha)
    if not nodes:
        cmds.warning('Select curve controllers first.')
        return
    _DATA[key] = nodes
    _refresh_lists()


def _clear(*_):
    _DATA['src'], _DATA['tgt'] = [], []
    _refresh_lists()


def _swap(*_):
    _DATA['src'], _DATA['tgt'] = _DATA['tgt'], _DATA['src']
    _refresh_lists()


def _on_select(key):
    other = 'tgt' if key == 'src' else 'src'
    idx = cmds.textScrollList(_LISTS[key], query=True, selectIndexedItem=True) or []
    cmds.textScrollList(_LISTS[other], edit=True, deselectAll=True)
    if idx and idx[0] <= len(_DATA[other]):
        cmds.textScrollList(_LISTS[other], edit=True, selectIndexedItem=idx[0])


def _on_double_click(key):
    idx = cmds.textScrollList(_LISTS[key], query=True, selectIndexedItem=True) or []
    if idx and idx[0] <= len(_DATA[key]) and cmds.objExists(_DATA[key][idx[0] - 1]):
        cmds.select(_DATA[key][idx[0] - 1], replace=True)


def _auto_match(*_):
    search = cmds.textFieldGrp(SEARCH_FLD, query=True, text=True)
    replace = cmds.textFieldGrp(REPLACE_FLD, query=True, text=True)
    if not _DATA['src']:
        cmds.warning('Load sources first.')
        return
    if not search:
        cmds.warning('Enter the text to search for in the source names.')
        return
    srcs, tgts, problems = match_targets_by_name(_DATA['src'], search, replace)
    for p in problems:
        cmds.warning(p)
    if not srcs:
        cmds.warning('No targets found.')
        return
    _DATA['src'], _DATA['tgt'] = srcs, tgts
    _refresh_lists('Matched {} by name.'.format(len(srcs)))


def _run(*_):
    src, tgt = _DATA['src'], _DATA['tgt']
    if not src or not tgt:
        cmds.warning('Load sources and targets first.')
        return
    if len(src) != len(tgt):
        cmds.warning('Source/target counts differ ({} vs {}); nothing copied.'.format(len(src), len(tgt)))
        return
    space = 'world' if cmds.radioButtonGrp(SPACE_RB, query=True, select=True) == 1 else 'object'
    done, failed = batch_copy(list(zip(src, tgt)), space)
    for s, t, reason in failed:
        cmds.warning('Skipped {} -> {}: {}'.format(_short(s), _short(t), reason))
    msg = 'Copied {} of {} sets.'.format(len(done), len(src))
    if failed:
        msg += ' {} skipped (see Script Editor).'.format(len(failed))
    _update_status(msg)
    cmds.inViewMessage(amg=msg, pos='midCenter', fade=True)


def _list_column(key, title, button_label):
    cmds.columnLayout(adjustableColumn=True, rowSpacing=4)
    cmds.text(label=title, align='left', font='boldLabelFont')
    cmds.textScrollList(_LISTS[key], numberOfRows=10, allowMultiSelection=False,
                        selectCommand=lambda *_: _on_select(key),
                        doubleClickCommand=lambda *_: _on_double_click(key))
    cmds.button(label=button_label, height=28, command=lambda *_: _load(key))
    cmds.setParent('..')


def show():
    cmds.selectPref(trackSelectionOrder=True)
    _DATA['src'], _DATA['tgt'] = [], []
    if cmds.window(WIN, exists=True):
        cmds.deleteUI(WIN)

    cmds.window(WIN, title='Curves CV Copier - Batch', widthHeight=(540, 560))
    cmds.columnLayout(adjustableColumn=True, rowSpacing=6, columnOffset=('both', 8))
    cmds.separator(height=4, style='none')

    cmds.optionMenuGrp(ORDER_MENU, label='List order', columnWidth2=(70, 260))
    cmds.menuItem(label='Selection order (click controllers in order)')
    cmds.menuItem(label='Alphabetical (natural sort)')

    cmds.rowLayout(numberOfColumns=2, columnWidth2=(258, 258), columnAttach2=('both', 'both'),
                   columnOffset2=(0, 4))
    _list_column('src', 'SOURCES  (copy from)', 'Load Sources from Selection')
    _list_column('tgt', 'TARGETS  (paste to)', 'Load Targets from Selection')
    cmds.setParent('..')

    cmds.text(label='Row N of the left list pastes onto row N of the right list. '
                    'Click a row to highlight its partner, double-click to select it in the scene.',
              align='left', wordWrap=True)

    cmds.frameLayout(label='Auto-match targets by name (optional)', collapsable=True,
                     collapse=True, marginWidth=6, marginHeight=4)
    cmds.textFieldGrp(SEARCH_FLD, label='Search', columnWidth2=(60, 200), text='')
    cmds.textFieldGrp(REPLACE_FLD, label='Replace', columnWidth2=(60, 200), text='')
    cmds.button(label='Find Targets for Loaded Sources', command=_auto_match)
    cmds.setParent('..')

    cmds.radioButtonGrp(SPACE_RB, label='Space', labelArray2=['World', 'Object'],
                        numberOfRadioButtons=2, select=1, columnWidth3=(70, 100, 100))
    cmds.separator(height=4)
    cmds.text(STATUS_TXT, label='Load sources and targets.', align='left')
    cmds.button(label='Copy CVs (Batch)', height=38, backgroundColor=(0.3, 0.55, 0.3),
                command=_run)
    cmds.rowLayout(numberOfColumns=2, columnWidth2=(258, 258), columnAttach2=('both', 'both'),
                   columnOffset2=(0, 4))
    cmds.button(label='Swap Sources / Targets', height=24, command=_swap)
    cmds.button(label='Clear All', height=24, command=_clear)
    cmds.setParent('..')

    cmds.showWindow(WIN)


if __name__ == '__main__':
    show()
