"""Safe importing and execution of individual Maya tool scripts."""

import importlib
import os
import runpy
import sys

import maya.cmds as cmds


def _uses_pyside(module):
    """Detect a Qt-based tool so it is not reloaded into a duplicate window."""
    try:
        source_file = getattr(module, "__file__", "") or ""
        if not source_file or not os.path.exists(source_file):
            return False
        with open(source_file, "r", encoding="utf-8", errors="ignore") as source:
            content = source.read()
        return "PySide2" in content or "PySide6" in content or "shiboken" in content
    except Exception:
        return False


def run_tool(tool_scripts, module_name):
    """Run one discovered tool, supporting regular and PySide Maya scripts."""
    try:
        script_path = tool_scripts[module_name]
        is_reload = module_name in sys.modules
        if is_reload:
            module = sys.modules[module_name]
            if _uses_pyside(module):
                # Existing PySide tools with no entry point traditionally
                # auto-open on reload; keep that behavior without double calls.
                if not _call_entry_point(module):
                    importlib.reload(module)
                return
            module = importlib.reload(module)
        else:
            module = importlib.import_module(module_name)
            if _uses_pyside(module):
                # A first import may have opened a module-level UI already.
                _call_entry_point(module)
                return

        if not _call_entry_point(module):
            cmds.inViewMessage(amg="Running full script: {}".format(module_name), pos="midCenter", fade=True)
            runpy.run_path(script_path, run_name="__main__")
    except Exception as error:
        cmds.warning("Error running {}: {}".format(module_name, error))


def _call_entry_point(module):
    """Call the first standard entry point found on a tool module."""
    for name in ("main", "run", "show_ui"):
        entry_point = getattr(module, name, None)
        if callable(entry_point):
            entry_point()
            return True
    return False
