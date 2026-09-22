import os
import sys
import urllib.request
import json
import types
import shutil
import maya.cmds as cmds

from .config import load_config as load_collection_config
from .config import save_config as save_collection_config
from .help import edit_tool_help, show_tool_help

class RiggingToolsCollection:
  def __init__(self, scripts_directory):
    self.scripts_directory = scripts_directory
    self.window_name = "RiggingToolsCollectionUI"
    self.content_layout = "toolsContentLayout"
    self.tool_scripts = {}
    self.columns = 4
    self.max_columns = 4
    self.minimum_button_width = 150
    self.button_height = 38
    self.grid_spacing = 4
    self._resize_filter = None
    self._resize_pending = False
    
    # Save user preferences locally so colors/order persist
    self.config_file = os.path.join(
        scripts_directory, "rigging_tools_config.json"
    )
    
    # Cloud OTA Settings
    self.MANIFEST_URL = "https://raw.githubusercontent.com/michelsat/Rigging-Tools-Collection/main/manifest.json"
    self.GITHUB_TOKEN = "" 
    
    # Toggle State: Read from Maya preferences (defaults to True if not set)
    self.use_cache = cmds.optionVar(query="rtc_use_cache") if cmds.optionVar(exists="rtc_use_cache") else True
    
    # Setup offline cache directory
    self.cache_dir = os.path.join(self.scripts_directory, ".cloud_cache")
    if self.use_cache and not os.path.exists(self.cache_dir):
      os.makedirs(self.cache_dir)
    
    self.button_order = []
    self.categories = []
    self.button_categories = {}
    self.tool_help = {}
    self.uncategorized_label = "Uncategorized"
    
    self.default_button_color = [0.3, 0.3, 0.32, 1.0]
    self.current_button_color = self.default_button_color.copy()
    self.button_colors = {}
    
    self.selected_button = None
    self.drag_source_index = None
    self._grid_rebuild_pending = False
    self.window_width = 720
    self.window_height = 580

    self.fetch_cloud_tools()
    self.load_config()

  def toggle_cache_mode(self, value, *args):
    """Toggle between Pure Cloud (In-Memory) and Smart Offline Cache."""
    self.use_cache = value
    cmds.optionVar(intValue=("rtc_use_cache", self.use_cache))
    
    if self.use_cache:
      if not os.path.exists(self.cache_dir):
        os.makedirs(self.cache_dir)
      cmds.inViewMessage(amg="Mode: Smart Offline Cache Enabled", pos="midCenter", fade=True)
    else:
      cmds.inViewMessage(amg="Mode: Pure Cloud Streaming Enabled", pos="midCenter", fade=True)

  def fetch_cloud_tools(self):
    """Fetch manifest from GitHub; respect cache toggle for offline fallback."""
    self.tool_scripts = {}
    manifest_cache = os.path.join(self.cache_dir, "manifest.json")
    data = {}

    try:
      headers = {"Authorization": f"Bearer {self.GITHUB_TOKEN}"} if self.GITHUB_TOKEN else {}
      req = urllib.request.Request(self.MANIFEST_URL, headers=headers)
      with urllib.request.urlopen(req, timeout=5) as response:
        raw_text = response.read().decode("utf-8")
        data = json.loads(raw_text)

      if self.use_cache:
        if not os.path.exists(self.cache_dir): 
          os.makedirs(self.cache_dir)
        with open(manifest_cache, "w", encoding="utf-8") as f:
          f.write(raw_text)

    except Exception:
      if self.use_cache and os.path.exists(manifest_cache):
        try:
          with open(manifest_cache, "r", encoding="utf-8") as f:
            data = json.load(f)
          cmds.inViewMessage(amg="Offline Mode Active", pos="midCenter", fade=True)
        except Exception:
          cmds.warning("Failed to read cached manifest.")
          return
      else:
        cmds.warning("Cannot reach server (Pure Cloud Mode requires internet).")
        return

    tools_data = data.get("tools", {})
    for tool_id, tool_info in tools_data.items():
      self.tool_scripts[tool_id] = tool_info.get("url")
      if tool_id not in self.tool_help and "help" in tool_info:
        self.tool_help[tool_id] = tool_info["help"]

  def load_config(self):
    # 1. Backup the help data we just fetched from GitHub
    cloud_help_backup = dict(self.tool_help)

    # 2. Load the local configuration file
    (
        self.button_order,
        self.current_button_color,
        self.button_colors,
        self.categories,
        self.button_categories,
        local_help,
    ) = load_collection_config(
        self.config_file, self.tool_scripts, self.default_button_color
    )

    # 3. Restore the cloud help, but let local custom edits override it
    self.tool_help = cloud_help_backup
    if local_help:
        for tool, help_data in local_help.items():
            if help_data and (help_data.get("description") or help_data.get("links")):
                self.tool_help[tool] = help_data

  def save_config(self):
    try:
      save_collection_config(
          self.config_file,
          self.button_order,
          self.current_button_color,
          self.button_colors,
          self.categories,
          self.button_categories,
          self.tool_help,
      )
    except Exception as e:
      cmds.warning(f"Error saving configuration: {str(e)}")

  def run_script(self, module_name, *args):
    """Execute tool based on the active Cloud/Cache mode."""
    remote_url = self.tool_scripts.get(module_name)
    cached_tool_path = os.path.join(self.cache_dir, f"{module_name}.py")
    mod = types.ModuleType(module_name)

    # MODE 1: SMART OFFLINE CACHE
    if self.use_cache:
      if not os.path.exists(cached_tool_path):
        if not remote_url: 
          cmds.warning(f"No URL found for {module_name}")
          return
        cmds.inViewMessage(amg=f"Caching {module_name}...", pos="midCenter", fade=True)
        
        try:
          headers = {"Authorization": f"Bearer {self.GITHUB_TOKEN}"} if self.GITHUB_TOKEN else {}
          req = urllib.request.Request(remote_url, headers=headers)
          with urllib.request.urlopen(req, timeout=8) as response:
            with open(cached_tool_path, "w", encoding="utf-8") as f:
              f.write(response.read().decode("utf-8"))
        except Exception as e:
          cmds.warning(f"Download failed: {e}")
          return

      try:
        with open(cached_tool_path, "r", encoding="utf-8") as f:
          source_code = f.read()
        mod.__file__ = cached_tool_path
        mod.__dict__["__name__"] = "__main__"
        exec(compile(source_code, cached_tool_path, "exec"), mod.__dict__)
      except Exception as e:
        cmds.warning(f"Cache execution error: {e}")
        return

    # MODE 2: PURE CLOUD STREAMING (In-Memory)
    else:
      if not remote_url: 
        cmds.warning(f"No URL found for {module_name}")
        return
      cmds.inViewMessage(amg=f"Streaming {module_name}...", pos="midCenter", fade=True)
      
      try:
        headers = {"Authorization": f"Bearer {self.GITHUB_TOKEN}"} if self.GITHUB_TOKEN else {}
        req = urllib.request.Request(remote_url, headers=headers)
        with urllib.request.urlopen(req, timeout=8) as response:
          source_code = response.read().decode("utf-8")
          
        mod.__file__ = f"<cloud>/{module_name}.py"
        mod.__dict__["__name__"] = "__main__"
        exec(compile(source_code, f"<cloud>/{module_name}", "exec"), mod.__dict__)
      except Exception as e:
        cmds.warning(f"Streaming failed: {e}")
        return

    # Launch UI (Shared)
    for entry in ("main", "run", "show_ui"):
      fn = getattr(mod, entry, None)
      if callable(fn):
        fn()
        break

  # -------------------------------------------------------------------------
  # Tool Help Methods
  # -------------------------------------------------------------------------

  def show_tool_help_dialog(self, module_name, *args):
    help_data = self.tool_help.get(module_name, {})
    show_tool_help(
        module_name, help_data, on_edit_callback=self.edit_tool_help_dialog
    )

  def edit_tool_help_dialog(self, module_name, *args):
    existing_help = self.tool_help.get(module_name, {})
    changed, updated_help = edit_tool_help(module_name, existing_help)

    if changed:
      if updated_help is None or (
          not updated_help.get("description") and not updated_help.get("links")
      ):
        if module_name in self.tool_help:
          del self.tool_help[module_name]
        cmds.inViewMessage(
            amg=f"Help removed for {module_name.replace('_', ' ').title()}",
            pos="midCenter", fade=True,
        )
      else:
        self.tool_help[module_name] = updated_help
        cmds.inViewMessage(
            amg=f"Help saved for {module_name.replace('_', ' ').title()}",
            pos="midCenter", fade=True,
        )
      self.save_config()
      self._refresh_help_selector()
      self._defer_grid_rebuild()

  def delete_tool_help(self, module_name, *args):
    if module_name in self.tool_help:
      tool_display = module_name.replace("_", " ").title()
      result = cmds.confirmDialog(
          title="Delete Tool Help",
          message=f"Delete help settings and links for '{tool_display}'?",
          button=["Delete", "Cancel"],
          defaultButton="Delete", cancelButton="Cancel", dismissString="Cancel",
      )
      if result == "Delete":
        del self.tool_help[module_name]
        self.save_config()
        self._refresh_help_selector()
        self._defer_grid_rebuild()
        cmds.inViewMessage(amg=f"Deleted help for {tool_display}", pos="midCenter", fade=True)
    else:
      cmds.inViewMessage(amg="No help exists for this tool.", pos="midCenter", fade=True)

  def _refresh_help_selector(self):
    if not cmds.optionMenu("helpToolSelector", exists=True): return
    menu_items = cmds.optionMenu("helpToolSelector", query=True, itemListLong=True) or []
    for item in menu_items:
      cmds.deleteUI(item)

    if self.button_order:
      for tool in self.button_order:
        has_help = bool(self.tool_help.get(tool, {}).get("description") or self.tool_help.get(tool, {}).get("links"))
        suffix = "  [*Help]" if has_help else ""
        label = tool.replace("_", " ").title() + suffix
        cmds.menuItem(label=label, parent="helpToolSelector")
    else:
      cmds.menuItem(label="No tools available", enable=False, parent="helpToolSelector")
    self._update_selected_help_status()

  def _get_selected_help_module(self):
    if not cmds.optionMenu("helpToolSelector", exists=True): return None
    val = cmds.optionMenu("helpToolSelector", query=True, value=True) or ""
    cleaned = val.replace("  [*Help]", "").strip()
    for tool in self.button_order:
      if tool.replace("_", " ").title() == cleaned: return tool
    return None

  def _update_selected_help_status(self, *args):
    if not cmds.text("helpStatusText", exists=True): return
    module_name = self._get_selected_help_module()
    if not module_name:
      cmds.text("helpStatusText", edit=True, label="Status: No tool selected")
      return

    help_info = self.tool_help.get(module_name)
    if help_info and (help_info.get("description") or help_info.get("links")):
      links_count = len(help_info.get("links", []))
      desc_len = len(help_info.get("description", ""))
      status = f"Configured ({desc_len} chars, {links_count} link(s))"
    else:
      status = "No help or links added yet."
    cmds.text("helpStatusText", edit=True, label=f"Status: {status}")

  def _open_selected_tool_help(self, *args):
    module_name = self._get_selected_help_module()
    if module_name: self.show_tool_help_dialog(module_name)

  def _edit_selected_tool_help(self, *args):
    module_name = self._get_selected_help_module()
    if module_name: self.edit_tool_help_dialog(module_name)

  def _delete_selected_tool_help(self, *args):
    module_name = self._get_selected_help_module()
    if module_name: self.delete_tool_help(module_name)

  def create_help_settings(self, parent_layout):
    self.help_frame = cmds.frameLayout(
        label="Tool Help & Video Settings", collapsable=True, collapse=True,
        parent=parent_layout, marginWidth=5, marginHeight=5,
        collapseCommand=self.adjust_window_height, expandCommand=self.adjust_window_height,
    )

    help_layout = cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5), rowSpacing=4)
    cmds.text(label="(Tip: You can also right-click any tool button to view or edit help)", align="left", font="smallPlainLabelFont")

    select_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(70, 250), parent=help_layout)
    cmds.text(label="Select Tool:", align="left")
    cmds.optionMenu("helpToolSelector", changeCommand=self._update_selected_help_status)
    cmds.setParent(help_layout)

    cmds.text("helpStatusText", label="Status: Select a tool", align="left", font="smallBoldLabelFont")

    btn_row = cmds.rowLayout(numberOfColumns=3, adjustableColumn=1, columnWidth3=(120, 130, 90), parent=help_layout)
    cmds.button(label="View Help", height=28, command=self._open_selected_tool_help, annotation="View help and open video links")
    cmds.button(label="Add / Edit Help...", height=28, command=self._edit_selected_tool_help, annotation="Add or edit description and video links")
    cmds.button(label="Delete Help", height=28, command=self._delete_selected_tool_help, annotation="Delete help settings for selected tool")
    cmds.setParent(parent_layout)
    self._refresh_help_selector()

  # -------------------------------------------------------------------------
  # Reordering & Groups
  # -------------------------------------------------------------------------

  def swap_buttons(self, source_index, target_index):
    if source_index == target_index: return
    if 0 <= source_index < len(self.button_order) and 0 <= target_index < len(self.button_order):
      self.button_order[source_index], self.button_order[target_index] = (
          self.button_order[target_index], self.button_order[source_index],
      )
      self.save_config()
      self._defer_grid_rebuild()
      cmds.inViewMessage(amg="Button positions updated", pos="midCenter", fade=True)

  def _finish_deferred_grid_rebuild(self):
    self._grid_rebuild_pending = False
    if cmds.window(self.window_name, exists=True): self._rebuild_grid()

  def _defer_grid_rebuild(self):
    if self._grid_rebuild_pending: return
    self._grid_rebuild_pending = True
    try:
      import maya.utils
      maya.utils.executeDeferred(self._finish_deferred_grid_rebuild)
    except Exception:
      cmds.evalDeferred(self._finish_deferred_grid_rebuild)

  def start_drag(self, button_index, *args):
    self.drag_source_index = button_index
    source_name = self.button_order[button_index].replace("_", " ").title()
    cmds.inViewMessage(amg=f"Marked <hl>{source_name}</hl>. Right-click a target and choose Drop Here.", pos="midCenter", fade=True)

  def drop_on_target(self, target_index, *args):
    source_index = self.drag_source_index
    self.drag_source_index = None
    if source_index is None:
      cmds.inViewMessage(amg="Choose Start Drag on a tool first.", pos="midCenter", fade=True)
      return
    self.swap_buttons(source_index, target_index)

  def drag_tool_button(self, module_name, *args):
    return ["RiggingToolsCollectionTool", module_name]

  def drop_tool_button(self, target_module_name, messages, *args):
    if len(messages) < 2 or messages[0] != "RiggingToolsCollectionTool": return
    source_module_name = messages[1]
    if source_module_name == target_module_name: return
    try:
      source_index = self.button_order.index(source_module_name)
      target_index = self.button_order.index(target_module_name)
    except ValueError: return
    self.swap_buttons(source_index, target_index)

  def _refresh_group_selector(self):
    if not cmds.optionMenu("groupManagerSelector", exists=True): return
    menu_items = cmds.optionMenu("groupManagerSelector", query=True, itemListLong=True) or []
    for item in menu_items: cmds.deleteUI(item)
    if self.categories:
      for category in self.categories:
        cmds.menuItem(label=category, parent="groupManagerSelector")
    else:
      cmds.menuItem(label="No custom groups", enable=False, parent="groupManagerSelector")

  def add_category(self, *args):
    category = cmds.textField("newGroupNameField", query=True, text=True).strip()
    if not category: return
    if category == self.uncategorized_label or category in self.categories:
      cmds.inViewMessage(amg="Invalid or duplicate group name.", pos="midCenter", fade=True)
      return
    self.categories.append(category)
    cmds.textField("newGroupNameField", edit=True, text="")
    self.save_config()
    self._refresh_group_selector()
    self._defer_grid_rebuild()

  def rename_selected_category(self, *args):
    if not self.categories: return
    old_name = cmds.optionMenu("groupManagerSelector", query=True, value=True)
    if old_name not in self.categories: return

    result = cmds.promptDialog(
        title="Rename Tool Group", message="New group name:", text=old_name,
        button=["Rename", "Cancel"], defaultButton="Rename", cancelButton="Cancel", dismissString="Cancel",
    )
    if result != "Rename": return
    new_name = cmds.promptDialog(query=True, text=True).strip()
    if not new_name or new_name == self.uncategorized_label or new_name in self.categories:
      cmds.warning('Choose a unique group name.')
      return

    category_index = self.categories.index(old_name)
    self.categories[category_index] = new_name
    self.button_categories = {
        module: new_name if category == old_name else category
        for module, category in self.button_categories.items()
    }
    self.save_config()
    self._refresh_group_selector()
    cmds.optionMenu("groupManagerSelector", edit=True, value=new_name)
    self._defer_grid_rebuild()

  def remove_selected_category(self, *args):
    if not self.categories: return
    category = cmds.optionMenu("groupManagerSelector", query=True, value=True)
    if category not in self.categories: return

    self.categories.remove(category)
    self.button_categories = {
        module: assigned_category
        for module, assigned_category in self.button_categories.items()
        if assigned_category != category
    }
    self.save_config()
    self._refresh_group_selector()
    self._defer_grid_rebuild()

  def assign_button_category(self, module_name, category, *args):
    if category in self.categories:
      self.button_categories[module_name] = category
    else:
      self.button_categories.pop(module_name, None)
      category = self.uncategorized_label
    self.save_config()
    self._defer_grid_rebuild()

  def create_group_settings(self, parent_layout):
    self.group_frame = cmds.frameLayout(
        label="Tool Groups", collapsable=True, collapse=True,
        parent=parent_layout, marginWidth=5, marginHeight=5,
        collapseCommand=self.adjust_window_height, expandCommand=self.adjust_window_height,
    )
    group_layout = cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5), rowSpacing=4)
    add_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
    cmds.textField("newGroupNameField", placeholderText="New group name (e.g. Skinning)")
    cmds.button(label="Add Group", width=90, command=self.add_category)
    cmds.setParent(group_layout)

    manage_row = cmds.rowLayout(numberOfColumns=3, adjustableColumn=1, columnWidth3=(250, 90, 90))
    cmds.optionMenu("groupManagerSelector")
    cmds.button(label="Rename", command=self.rename_selected_category)
    cmds.button(label="Remove", command=self.remove_selected_category)
    cmds.setParent(parent_layout)
    self._refresh_group_selector()

  # -------------------------------------------------------------------------
  # Color & Opacity Transparency Settings
  # -------------------------------------------------------------------------

  def get_blended_bgc(self, color_values):
    r = color_values[0]
    g = color_values[1]
    b = color_values[2]
    a = color_values[3] if len(color_values) > 3 else 1.0
    bg = 0.25
    return [
        max(0.0, min(1.0, (r * a) + (bg * (1.0 - a)))),
        max(0.0, min(1.0, (g * a) + (bg * (1.0 - a)))),
        max(0.0, min(1.0, (b * a) + (bg * (1.0 - a)))),
    ]

  def update_button_color(self, *args):
    r = cmds.floatSliderGrp("redSlider", query=True, value=True)
    g = cmds.floatSliderGrp("greenSlider", query=True, value=True)
    b = cmds.floatSliderGrp("blueSlider", query=True, value=True)
    a = cmds.floatSliderGrp("alphaSlider", query=True, value=True)

    self.current_button_color = [r, g, b, a]
    blended_color = self.get_blended_bgc(self.current_button_color)

    if self.selected_button is not None:
      self.button_colors[self.selected_button] = self.current_button_color.copy()
      self.save_config()

      button_index = self.button_order.index(self.selected_button)
      button_name = f"button_{button_index}"
      if cmds.button(button_name, exists=True):
        cmds.button(button_name, edit=True, backgroundColor=blended_color)

    cmds.canvas("colorPreview", edit=True, rgbValue=blended_color)
    self.update_selected_button_display()

  def select_button_for_editing(self, module_name, *args):
    self.selected_button = module_name
    button_color = self.button_colors.get(module_name, self.default_button_color)
    self.current_button_color = button_color.copy()

    alpha = button_color[3] if len(button_color) > 3 else 1.0
    cmds.floatSliderGrp("redSlider", edit=True, value=button_color[0])
    cmds.floatSliderGrp("greenSlider", edit=True, value=button_color[1])
    cmds.floatSliderGrp("blueSlider", edit=True, value=button_color[2])
    cmds.floatSliderGrp("alphaSlider", edit=True, value=alpha)
    
    blended_color = self.get_blended_bgc(button_color)
    cmds.canvas("colorPreview", edit=True, rgbValue=blended_color)
    
    self.update_selected_button_display()
    cmds.inViewMessage(amg=f"Selected button: {module_name}", pos="midCenter", fade=True)

  def update_selected_button_display(self):
    if cmds.text("selectedButtonText", exists=True):
      if self.selected_button:
        display_name = self.selected_button.replace("_", " ").title()
        cmds.text("selectedButtonText", edit=True, label=f"Selected Button: {display_name}")
      else:
        cmds.text("selectedButtonText", edit=True, label="No Button Selected")

  def reset_button_color(self, *args):
    if self.selected_button:
      if self.selected_button in self.button_colors:
        del self.button_colors[self.selected_button]

      self.current_button_color = self.default_button_color.copy()
      blended_color = self.get_blended_bgc(self.current_button_color)

      cmds.floatSliderGrp("redSlider", edit=True, value=self.current_button_color[0])
      cmds.floatSliderGrp("greenSlider", edit=True, value=self.current_button_color[1])
      cmds.floatSliderGrp("blueSlider", edit=True, value=self.current_button_color[2])
      cmds.floatSliderGrp("alphaSlider", edit=True, value=self.current_button_color[3])
      
      cmds.canvas("colorPreview", edit=True, rgbValue=blended_color)
      self.save_config()

      button_index = self.button_order.index(self.selected_button)
      button_name = f"button_{button_index}"
      if cmds.button(button_name, exists=True):
        cmds.button(button_name, edit=True, backgroundColor=blended_color)
    else:
      cmds.inViewMessage(amg="No button selected", pos="midCenter", fade=True)

  def preset_color(self, color_values, *args):
    if self.selected_button:
      if len(color_values) == 3:
        color_values = color_values + [1.0]

      self.current_button_color = color_values.copy()
      self.button_colors[self.selected_button] = color_values.copy()
      blended_color = self.get_blended_bgc(self.current_button_color)

      cmds.floatSliderGrp("redSlider", edit=True, value=color_values[0])
      cmds.floatSliderGrp("greenSlider", edit=True, value=color_values[1])
      cmds.floatSliderGrp("blueSlider", edit=True, value=color_values[2])
      cmds.floatSliderGrp("alphaSlider", edit=True, value=color_values[3])
      cmds.canvas("colorPreview", edit=True, rgbValue=blended_color)
      self.save_config()

      button_index = self.button_order.index(self.selected_button)
      button_name = f"button_{button_index}"
      if cmds.button(button_name, exists=True):
        cmds.button(button_name, edit=True, backgroundColor=blended_color)
    else:
      cmds.inViewMessage(amg="No button selected", pos="midCenter", fade=True)

  def create_color_settings(self, parent_layout):
    self.color_frame = cmds.frameLayout(
        label="Button Color Settings", collapsable=True, collapse=True,
        parent=parent_layout, marginWidth=5, marginHeight=5,
        collapseCommand=self.adjust_window_height, expandCommand=self.adjust_window_height,
    )
    color_layout = cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5))
    cmds.text("selectedButtonText", label="No Button Selected", align="left", font="boldLabelFont")
    cmds.text(label="(Right-click a button and select 'Edit Color')", font="smallPlainLabelFont")
    cmds.separator(height=10, style="in")

    preview_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, columnAlign2=("left", "center"))
    cmds.text(label="Current Color:", width=80)
    initial_blended = self.get_blended_bgc(self.current_button_color)
    cmds.canvas("colorPreview", width=50, height=20, rgbValue=initial_blended)
    cmds.setParent(color_layout)

    cmds.floatSliderGrp(
        "redSlider", label="Red", field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0,
        value=self.current_button_color[0], dragCommand=self.update_button_color, changeCommand=self.update_button_color,
    )
    cmds.floatSliderGrp(
        "greenSlider", label="Green", field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0,
        value=self.current_button_color[1], dragCommand=self.update_button_color, changeCommand=self.update_button_color,
    )
    cmds.floatSliderGrp(
        "blueSlider", label="Blue", field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0,
        value=self.current_button_color[2], dragCommand=self.update_button_color, changeCommand=self.update_button_color,
    )
    cmds.floatSliderGrp(
        "alphaSlider", label="Opacity", field=True, minValue=0.0, maxValue=1.0, fieldMinValue=0.0, fieldMaxValue=1.0,
        value=self.current_button_color[3] if len(self.current_button_color) > 3 else 1.0, 
        dragCommand=self.update_button_color, changeCommand=self.update_button_color,
    )

    cmds.separator(height=10, style="in")
    cmds.text(label="Color Presets:", align="left")

    preset_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
    presets = [
        ("Blue", [0.2, 0.3, 0.6]), ("Green", [0.2, 0.6, 0.3]), ("Red", [0.6, 0.2, 0.2]),
        ("Purple", [0.5, 0.2, 0.5]), ("Orange", [0.8, 0.4, 0.1]), ("Teal", [0.1, 0.6, 0.6]),
        ("Grey", [0.4, 0.4, 0.4]), ("Pink", [0.8, 0.3, 0.5]), ("Yellow", [0.8, 0.8, 0.2]),
        ("Dark", [0.2, 0.2, 0.2]),
    ]

    for row_start in range(0, len(presets), 5):
      preset_row = cmds.formLayout(parent=preset_layout, height=26)
      row_presets = presets[row_start : row_start + 5]

      for column_index, (name, values) in enumerate(row_presets):
        preset_button = cmds.button(
            label=name, backgroundColor=values, command=lambda x, c=values: self.preset_color(c),
            height=26, recomputeSize=False, parent=preset_row,
        )

        left_pos = int(round((100.0 / len(row_presets)) * column_index))
        right_pos = int(round((100.0 / len(row_presets)) * (column_index + 1)))

        attachments = [(preset_button, "top", 0), (preset_button, "bottom", 0)]
        if column_index == 0: attachments.append((preset_button, "left", 0))
        else: cmds.formLayout(preset_row, edit=True, attachPosition=(preset_button, "left", 3, left_pos))
        if column_index == len(row_presets) - 1: attachments.append((preset_button, "right", 0))
        else: cmds.formLayout(preset_row, edit=True, attachPosition=(preset_button, "right", 3, right_pos))
        cmds.formLayout(preset_row, edit=True, attachForm=attachments)

    cmds.setParent(color_layout)
    cmds.separator(height=5)
    cmds.button(label="Reset to Default", command=self.reset_button_color, height=30)
    cmds.setParent(parent_layout)

  # -------------------------------------------------------------------------
  # Grid Construction & Rows
  # -------------------------------------------------------------------------

  def _clear_content(self):
    children = cmds.layout(self.content_layout, query=True, childArray=True) or []
    for child in children: cmds.deleteUI(child)

  def _create_responsive_row(self, parent_layout, row_modules, row_start_index):
    row = cmds.formLayout(parent=parent_layout, height=self.button_height)
    column_count = len(row_modules)

    for column_index, module_name in enumerate(row_modules):
      button_index = self.button_order.index(module_name)
      display_name = module_name.replace("_", " ").title()
      button_name = f"button_{button_index}"
      button_color = self.button_colors.get(module_name, self.default_button_color)
      blended_color = self.get_blended_bgc(button_color)

      tool_help_data = self.tool_help.get(module_name, {})
      has_help = bool(tool_help_data.get("description") or tool_help_data.get("links"))
      desc = tool_help_data.get("description", "").strip()
      
      if desc:
        first_line = desc.split("\n")[0]
        if len(first_line) > 55: first_line = first_line[:52] + "..."
        button_annotation = f"{display_name}: {first_line}\n(Right-click for Help & options)"
      else:
        button_annotation = f"Run {display_name}\n(Right-click for Help & options)"

      button = cmds.button(
          button_name, label=display_name, command=lambda x, mn=module_name: self.run_script(mn),
          annotation=button_annotation, backgroundColor=blended_color, height=self.button_height, recomputeSize=False,
          dragCallback=(lambda drag_control, x, y, modifiers, mn=module_name: (self.drag_tool_button(mn))),
          dropCallback=(lambda drag_control, drop_control, messages, x, y, drag_type, mn=module_name: self.drop_tool_button(mn, messages)),
          parent=row,
      )

      attachments = [(button, "top", 0), (button, "bottom", 0)]
      left_position = int(round((100.0 / column_count) * column_index))
      right_position = int(round((100.0 / column_count) * (column_index + 1)))

      if column_index == 0: attachments.append((button, "left", 0))
      else: cmds.formLayout(row, edit=True, attachPosition=(button, "left", self.grid_spacing, left_position))
      if column_index == column_count - 1: attachments.append((button, "right", 0))
      else: cmds.formLayout(row, edit=True, attachPosition=(button, "right", self.grid_spacing, right_position))
      cmds.formLayout(row, edit=True, attachForm=attachments)

      # --- Right-Click Popup Menu ---
      cmds.popupMenu(parent=button)
      cmds.menuItem(label="Help / Video Links", command=lambda x, mn=module_name: self.show_tool_help_dialog(mn))
      cmds.menuItem(label="Add / Edit Help...", command=lambda x, mn=module_name: self.edit_tool_help_dialog(mn))
      if has_help: cmds.menuItem(label="Delete Help", command=lambda x, mn=module_name: self.delete_tool_help(mn))
      cmds.menuItem(divider=True)
      cmds.menuItem(label="Start Drag (Menu Fallback)", command=lambda x, idx=button_index: self.start_drag(idx))
      cmds.menuItem(label="Drop Here (Menu Fallback)", command=lambda x, idx=button_index: self.drop_on_target(idx))
      cmds.menuItem(divider=True)
      cmds.menuItem(label="Assign to Group", subMenu=True)
      cmds.menuItem(label=self.uncategorized_label, command=lambda x, mn=module_name: self.assign_button_category(mn, None))
      for category in self.categories:
        cmds.menuItem(label=category, command=lambda x, mn=module_name, cat=category: (self.assign_button_category(mn, cat)))
      cmds.setParent("..", menu=True)
      cmds.menuItem(divider=True)
      cmds.menuItem(label="Edit Color", command=lambda x, mn=module_name: self.select_button_for_editing(mn))

  def create_grid_layout(self, parent_layout):
    module_names = self.button_order
    if not module_names:
      cmds.text(label="No Python scripts found in the Cloud Manifest.", align="center", parent=parent_layout)
      return

    cmds.setParent(parent_layout)
    grid_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=8)

    group_names = list(self.categories)
    uncategorized_tools = [module for module in module_names if self.button_categories.get(module) not in self.categories]
    if uncategorized_tools or not group_names: group_names.append(self.uncategorized_label)

    for category in group_names:
      if category == self.uncategorized_label: group_tools = uncategorized_tools
      else: group_tools = [module for module in module_names if self.button_categories.get(module) == category]

      group_frame = cmds.frameLayout(label=category, collapsable=True, collapse=False, marginWidth=6, marginHeight=6, parent=grid_layout)
      group_layout = cmds.columnLayout(adjustableColumn=True, rowSpacing=self.grid_spacing, parent=group_frame)

      if group_tools:
        for row_start in range(0, len(group_tools), self.columns):
          self._create_responsive_row(group_layout, group_tools[row_start : row_start + self.columns], row_start)
      else: cmds.text(label="No tools assigned to this group yet.", align="left", parent=group_layout)
      cmds.setParent(grid_layout)

  def _rebuild_grid(self):
    if not cmds.layout(self.content_layout, exists=True): return
    self._clear_content()
    cmds.setParent(self.content_layout)
    self.create_grid_layout(self.content_layout)

  def _update_responsive_grid(self):
    self._resize_pending = False
    if not cmds.window(self.window_name, exists=True): return
    window_width = cmds.window(self.window_name, query=True, width=True)
    available_width = max(1, window_width - 34)
    new_columns = max(1, min(self.max_columns, int(available_width / self.minimum_button_width)))

    if new_columns != self.columns:
      self.columns = new_columns
      self._rebuild_grid()

  def _schedule_responsive_grid(self):
    if self._resize_pending: return
    self._resize_pending = True
    try:
      from PySide6 import QtCore
    except ImportError:
      from PySide2 import QtCore
    QtCore.QTimer.singleShot(60, self._update_responsive_grid)

  def _install_resize_filter(self):
    try:
      from maya import OpenMayaUI as omui
      try:
        from PySide6 import QtCore, QtWidgets
        from shiboken6 import wrapInstance
      except ImportError:
        from PySide2 import QtCore, QtWidgets
        from shiboken2 import wrapInstance

      window_pointer = omui.MQtUtil.findWindow(self.window_name)
      if not window_pointer: return
      owner = self

      class ResizeFilter(QtCore.QObject):
        def eventFilter(self, watched, event):
          if event.type() == QtCore.QEvent.Resize: owner._schedule_responsive_grid()
          return False

      maya_window = wrapInstance(int(window_pointer), QtWidgets.QWidget)
      maya_window.setMinimumSize(470, 360)

      self._resize_filter = ResizeFilter(maya_window)
      maya_window.installEventFilter(self._resize_filter)
    except Exception as error: cmds.warning(f"Responsive resize support could not be installed: {error}")

  def refresh_content(self, *args):
    if hasattr(self, 'cache_dir') and os.path.exists(self.cache_dir):
      try:
        shutil.rmtree(self.cache_dir)
      except Exception as e:
        cmds.warning(f"Could not clear cache: {e}")

    self.tool_scripts.clear()
    self.fetch_cloud_tools()
    self.load_config()

    self._refresh_group_selector()
    self._refresh_help_selector()

    if cmds.layout(self.content_layout, exists=True):
      self._update_responsive_grid()
      self._rebuild_grid()
      cmds.inViewMessage(amg="Cache cleared & tools synced with server", pos="midCenter", fade=True)
    else: self.show_ui()

  def adjust_window_height(self, *args):
    self._schedule_responsive_grid()

  def show_ui(self):
    if cmds.window(self.window_name, exists=True): cmds.deleteUI(self.window_name)
    window = cmds.window(
        self.window_name, title="Rigging Tools Collection (Dual Engine)",
        widthHeight=(self.window_width, self.window_height), sizeable=True, resizeToFitChildren=False,
    )

    main_form = cmds.formLayout(numberOfDivisions=100)
    header_column = cmds.columnLayout(adjustableColumn=True, columnAttach=("both", 5), parent=main_form)

    cmds.text(label="Rigging Tools Collection (OTA)", font="boldLabelFont", height=30)
    cmds.text(
        label="(Drag to reorder; right-click for help, groups, and colors)",
        font="smallPlainLabelFont", height=20, backgroundColor=[0.2, 0.2, 0.22],
    )
    cmds.separator(height=10, style="in")

    self.create_group_settings(header_column)
    cmds.separator(height=10, style="in")
    self.create_color_settings(header_column)
    cmds.separator(height=10, style="in")
    self.create_help_settings(header_column)
    cmds.separator(height=10, style="in")
    cmds.setParent(main_form)

    footer_layout = cmds.formLayout(parent=main_form, height=44, backgroundColor=[0.22, 0.22, 0.24])
    
    cache_checkbox = cmds.checkBox(
        label="Smart Offline Cache", 
        value=self.use_cache, 
        changeCommand=self.toggle_cache_mode, 
        parent=footer_layout
    )

    refresh_button = cmds.button(
        label="Sync with Server", command=self.refresh_content,
        height=30, width=140, backgroundColor=[0.2, 0.5, 0.35], parent=footer_layout,
    )
    
    close_button = cmds.button(
        label="Close Window", command=lambda x: cmds.deleteUI(self.window_name),
        height=30, width=120, backgroundColor=[0.6, 0.25, 0.25], parent=footer_layout,
    )

    cmds.formLayout(
        footer_layout, edit=True,
        attachForm=[
            (cache_checkbox, "left", 15), (cache_checkbox, "top", 14),
            (refresh_button, "top", 7), (refresh_button, "bottom", 7), 
            (close_button, "top", 7), (close_button, "bottom", 7), (close_button, "right", 10)
        ],
        attachControl=[
            (refresh_button, "right", 10, close_button)
        ]
    )
    cmds.setParent(main_form)

    scroll_layout = cmds.scrollLayout(childResizable=True, verticalScrollBarThickness=16, backgroundColor=[0.25, 0.25, 0.25], parent=main_form)
    cmds.columnLayout(self.content_layout, adjustableColumn=True, columnAttach=("both", 5))
    self.create_grid_layout(self.content_layout)

    cmds.formLayout(
        main_form, edit=True,
        attachForm=[
            (header_column, "top", 0), (header_column, "left", 0), (header_column, "right", 0),
            (footer_layout, "left", 0), (footer_layout, "right", 0), (footer_layout, "bottom", 0),
            (scroll_layout, "left", 0), (scroll_layout, "right", 0),
        ],
        attachControl=[(scroll_layout, "top", 5, header_column), (scroll_layout, "bottom", 5, footer_layout)],
    )
    cmds.showWindow(window)
    self._install_resize_filter()
    self._schedule_responsive_grid()

def launch_rigging_tools_collection():
  local_preferences_directory = r"C:/Users/sat/Documents/maya/scripts/sattools"
  tools_collection = RiggingToolsCollection(local_preferences_directory)
  tools_collection.show_ui()

if __name__ == "__main__":
  launch_rigging_tools_collection()
