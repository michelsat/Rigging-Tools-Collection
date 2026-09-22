"""
═══════════════════════════════════════════════════════════════════════════
    MAYA ADVANCED PLAYBLAST TOOL v3.2 - PRODUCTION STABLE
═══════════════════════════════════════════════════════════════════════════

    By: The Creative Disciplinary
    
    DESCRIPTION:
    Professional playblast tool with FFmpeg H.264 encoding, bypassing Maya's 
    QuickTime limitations on Intel 12+ core systems. Features include:
    
    - Two-pass PNG → H.264 workflow with FFmpeg
    - Multi-camera batch playblast (all renderable cameras at once)
    - Camera name suffix in filename (e.g., _renderCAM, _persp)
    - Frame range suffix option (e.g., _001-100)
    - Quality presets (CRF 15-28) and encoding speeds
    - Auto-versioning with smart folder management
    - Audio extraction and sync with offset handling
    - Four lighting modes: Default, All Lights, Grayscale, Flat Shaded
    - Viewport options: AA, SSAO, Shadows, Textures, etc.
    - Frame range options (Playback, Animation, Custom)
    - Cross-platform (Windows, macOS, Linux)
    - Maya 2019-2026+ compatible (Python 2.7 & 3.x)
    
    CRITICAL FIXES v3.2:
    - FIXED: Camera namespace colons (rig:cam) causing 0KB files on Windows
    - FIXED: File size validation - catches 0KB files and reports errors
    - FIXED: Path length validation - warns on Windows MAX_PATH issues
    - FIXED: Preferences now persist across sessions
    - IMPROVED: Better error messages and debug output
    - IMPROVED: Race condition prevention with file write delays
    
═══════════════════════════════════════════════════════════════════════════
"""

import maya.cmds as cmds
import maya.mel as mel
import os
import sys
import subprocess
import platform
import multiprocessing
import re
import time
import glob
import shutil

PY3 = sys.version_info[0] >= 3
W_WINDOW = 520


class AdvancedPlayblastTool:
    VERSION = "3.2"

    CRF_LABELS = {
        15: "15 | Best",        16: "16 | Excellent",    17: "17 | Very High",
        18: "18 | High (Rec.)", 19: "19 | Good+",        20: "20 | Good",
        21: "21 | Medium+",     22: "22 | Medium",        23: "23 | Standard",
        24: "24 | Below Std",   25: "25 | Below Std",
        26: "26 | Low",         27: "27 | Very Low",      28: "28 | Lowest",
    }

    QUALITY_PRESETS = [
        ("Master Quality",   15, "Archival / Master (largest)"),
        ("High Quality",     18, "Client Review (recommended)"),
        ("Good Quality",     21, "Internal Review"),
        ("Standard Quality", 23, "Quick Preview"),
        ("Web Quality",      28, "Web / Streaming (smallest)"),
    ]

    SPEED_LABELS = [
        ("ultrafast", "Ultra Fast (largest file, fastest encode)"),
        ("superfast", "Super Fast"),
        ("veryfast",  "Very Fast"),
        ("faster",    "Faster"),
        ("fast",      "Fast"),
        ("medium",    "Medium (recommended balance)"),
        ("slow",      "Slow (better compression)"),
        ("slower",    "Slower (best compression, slowest encode)"),
    ]

    def __init__(self):
        self.window_name      = "advPlayblastV32"
        self.dock_name        = "advPlayblastV32_dock"
        self.cpu_cores        = multiprocessing.cpu_count()
        self.system           = platform.system()
        self.playblast_report = {}
        self.camera_checkboxes = {}

    def create_ui(self, dockable=False):
        if cmds.dockControl(self.dock_name, exists=True):
            cmds.deleteUI(self.dock_name)
        if cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

        cmds.window(
            self.window_name,
            title    = "Advanced Playblast  v{}".format(self.VERSION),
            width    = W_WINDOW,
            height   = 900,
            sizeable = True,
        )

        cmds.scrollLayout(childResizable=True)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4, columnOffset=("both", 6))

        cmds.separator(height=6, style="none")
        cmds.text(label="Advanced Playblast Tool  v{}".format(self.VERSION),
                  font="boldLabelFont", height=20, align="center")
        cmds.text(label="By: The Creative Disciplinary",
                  font="smallPlainLabelFont", height=15, align="center")
        cmds.text(label="{}  CPU cores  |  {}".format(self.cpu_cores, self.system),
                  font="smallPlainLabelFont", height=15, align="center")
        cmds.separator(height=8)

        self._build_ffmpeg_section()
        self._build_output_section()
        self._build_quality_section()
        self._build_playblast_section()
        self._build_viewport_camera_section()
        self._build_output_options_section()
        self._build_progress_section()

        cmds.separator(height=6)
        btn_form = cmds.formLayout(height=44)
        btn_create = cmds.button(label="Create Playblast", height=40,
                                 backgroundColor=[0.13, 0.55, 0.13],
                                 command=self._execute_playblast)
        btn_cancel = cmds.button(label="Cancel", height=40,
                                 backgroundColor=[0.75, 0.12, 0.12],
                                 command=self._close_window)
        cmds.formLayout(btn_form, edit=True,
            attachForm=[
                (btn_create, "left",   0), (btn_create, "top",    2), (btn_create, "bottom", 2),
                (btn_cancel, "right",  0), (btn_cancel, "top",    2), (btn_cancel, "bottom", 2),
            ],
            attachPosition=[
                (btn_create, "right", 1, 50),
                (btn_cancel, "left",  1, 50),
            ],
        )
        cmds.setParent("..")
        cmds.separator(height=8, style="none")

        if dockable:
            try:
                cmds.dockControl(self.dock_name, label="Playblast Tool", area="right",
                                 content=self.window_name, floating=True,
                                 allowedArea=["right", "left", "float", "bottom"])
            except Exception as e:
                print("Dock failed ({}), opening as window.".format(e))
                cmds.showWindow(self.window_name)
        else:
            cmds.showWindow(self.window_name)

        self._init_defaults()

    def _build_ffmpeg_section(self):
        cmds.frameLayout(label="FFmpeg Configuration", collapsable=True,
                         collapse=True, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        cmds.text(label="FFmpeg Executable Path:", align="left", font="smallBoldLabelFont")
        cmds.rowLayout(numberOfColumns=3, adjustableColumn=1)
        self.ui_ffmpeg_path = cmds.textField(text="")
        cmds.button(label="Browse", width=70, command=self._browse_ffmpeg)
        cmds.button(label="Test",   width=52, command=self._test_ffmpeg)
        cmds.setParent("..")
        cmds.text(label="Recommended: FFmpeg 4.0 or newer  (libx264 / H.264)",
                  align="left", font="smallPlainLabelFont")
        cmds.setParent("..")
        cmds.setParent("..")

    def _build_output_section(self):
        cmds.frameLayout(label="Output Settings", collapsable=True,
                         collapse=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

        cmds.text(label="Output Location:", align="left", font="smallBoldLabelFont")
        self.ui_location_menu = cmds.optionMenu(changeCommand=self._on_location_change)
        cmds.menuItem(label="Same as Maya Scene")
        cmds.menuItem(label="Last Used Location")
        cmds.menuItem(label="Project Movies Folder")
        cmds.menuItem(label="Custom Location")

        self.ui_custom_loc_row = cmds.rowLayout(numberOfColumns=2, adjustableColumn=1, visible=False)
        self.ui_custom_folder = cmds.textField(text="")
        cmds.button(label="Browse", width=70, command=self._browse_output_folder)
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
        self.ui_location_display = cmds.text(label="", align="left", font="smallPlainLabelFont")
        cmds.button(label="Open Folder", width=88, command=self._open_output_folder)
        cmds.setParent("..")

        cmds.separator(height=5)
        cmds.text(label="Filename:", align="left", font="smallBoldLabelFont")
        cmds.rowLayout(numberOfColumns=2, adjustableColumn=1)
        self.ui_filename = cmds.textField(text="", changeCommand=self._refresh_filename_preview)
        self.ui_auto_version = cmds.checkBox(label="Auto-version", value=True, width=108,
                                             changeCommand=self._refresh_filename_preview)
        cmds.setParent("..")
        
        self.ui_include_frame_range = cmds.checkBox(
            label="Include frame range in filename (e.g., _001-100)", 
            value=False,
            changeCommand=self._refresh_filename_preview
        )
        
        self.ui_filename_preview = cmds.text(label="", align="left", font="smallPlainLabelFont")

        cmds.setParent("..")
        cmds.setParent("..")

    def _build_quality_section(self):
        cmds.frameLayout(label="Quality Settings", collapsable=True,
                         collapse=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

        cmds.text(label="Resolution:", align="left", font="smallBoldLabelFont")
        self.ui_resolution = cmds.optionMenu(changeCommand=self._on_resolution_change)
        cmds.menuItem(label="Current Viewport")
        cmds.menuItem(label="HD 720p  (1280 x 720)")
        cmds.menuItem(label="HD 1080p  (1920 x 1080)")
        cmds.menuItem(label="2K  (2048 x 1152)")
        cmds.menuItem(label="4K  (3840 x 2160)")
        cmds.menuItem(label="Custom")
        cmds.optionMenu(self.ui_resolution, edit=True, value="HD 1080p  (1920 x 1080)")

        self.ui_custom_res_row = cmds.rowLayout(numberOfColumns=4,
                                                columnWidth4=(50, 88, 50, 88), visible=False)
        cmds.text(label="Width:")
        self.ui_custom_w = cmds.intField(value=1920)
        cmds.text(label="Height:")
        self.ui_custom_h = cmds.intField(value=1080)
        cmds.setParent("..")

        cmds.separator(height=4)
        cmds.text(label="Quality Preset:", align="left", font="smallBoldLabelFont")
        self.ui_quality_preset = cmds.optionMenu(changeCommand=self._on_quality_preset_change)
        for name, crf, desc in self.QUALITY_PRESETS:
            cmds.menuItem(label="{} - {}".format(name, desc))
        cmds.optionMenu(self.ui_quality_preset, edit=True, select=2)

        cmds.separator(height=3)
        cmds.text(label="CRF (Constant Rate Factor): Lower number = better quality but larger file.",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="Higher number = smaller file but more compression artifacts.",
                  align="left", font="smallPlainLabelFont")
        cmds.separator(height=2)

        cmds.rowLayout(numberOfColumns=3, adjustableColumn=2, columnWidth3=(158, 10, 148))
        cmds.text(label="CRF [15=Best | 28=Lowest]:", align="left", font="smallBoldLabelFont")
        self.ui_crf_slider = cmds.intSlider(minValue=15, maxValue=28, value=18, step=1,
                                            changeCommand=self._on_crf_change)
        self.ui_crf_label = cmds.text(label=self.CRF_LABELS[18], align="left",
                                      font="smallBoldLabelFont")
        cmds.setParent("..")

        cmds.separator(height=4)

        cmds.rowLayout(numberOfColumns=2, adjustableColumn=2, columnWidth2=(110, 10))
        cmds.text(label="Encoding Speed:", align="left", font="smallBoldLabelFont")
        self.ui_speed_desc = cmds.text(label="Medium (recommended balance)",
                                       align="left", font="smallPlainLabelFont")
        cmds.setParent("..")

        self.ui_speed = cmds.optionMenu(changeCommand=self._on_speed_change)
        for _, desc in self.SPEED_LABELS:
            cmds.menuItem(label=desc)
        cmds.optionMenu(self.ui_speed, edit=True, select=6)

        cmds.setParent("..")
        cmds.setParent("..")

    def _build_playblast_section(self):
        cmds.frameLayout(label="Playblast Settings", collapsable=True,
                         collapse=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

        cmds.text(label="Frame Range:", align="left", font="smallBoldLabelFont")
        self.ui_range_menu = cmds.optionMenu(changeCommand=self._on_range_change)
        cmds.menuItem(label="Playback Range")
        cmds.menuItem(label="Animation Range")
        cmds.menuItem(label="Custom")

        cmds.text(label="Playback Range:  The grey inner slider (your working playback region).",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="Animation Range:  Full scene start/end (may extend beyond playback slider).",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="Custom:  Manual entry (useful for handles, pre-roll, post-roll).",
                  align="left", font="smallPlainLabelFont")

        self.ui_custom_range_row = cmds.rowLayout(numberOfColumns=4,
                                                  columnWidth4=(50, 85, 50, 85), visible=False)
        cmds.text(label="Start:")
        self.ui_start_frame = cmds.intField(value=1)
        cmds.text(label="End:")
        self.ui_end_frame   = cmds.intField(value=100)
        cmds.setParent("..")

        cmds.separator(height=5)
        cmds.text(label="Display Options:", align="left", font="smallBoldLabelFont")
        self.ui_offscreen = cmds.checkBox(label="Off-screen rendering  (recommended)", value=True)

        cmds.separator(height=4)
        cmds.text(label="Audio:", align="left", font="smallBoldLabelFont")
        self.ui_audio = cmds.checkBox(
            label="Include Audio  (auto-detects and syncs Maya timeline audio)", value=True)

        cmds.setParent("..")
        cmds.setParent("..")

    def _build_viewport_camera_section(self):
        cmds.frameLayout(label="Viewport Options & Camera", collapsable=True,
                         collapse=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=4)

        cmds.text(label="Camera Selection:", align="left", font="smallBoldLabelFont")
        
        self.ui_camera_mode = cmds.radioCollection()
        cmds.rowLayout(numberOfColumns=3, columnWidth3=(140, 180, 140))
        self.ui_cam_active = cmds.radioButton(
            label="Active Viewport",
            collection=self.ui_camera_mode,
            select=True,
            onCommand=lambda *args: self._on_camera_mode_change("active"),
        )
        self.ui_cam_renderable = cmds.radioButton(
            label="All Renderable Cameras",
            collection=self.ui_camera_mode,
            onCommand=lambda *args: self._on_camera_mode_change("renderable"),
        )
        self.ui_cam_selected = cmds.radioButton(
            label="Selected Cameras",
            collection=self.ui_camera_mode,
            onCommand=lambda *args: self._on_camera_mode_change("selected"),
        )
        cmds.setParent("..")

        cmds.separator(height=3)
        cmds.text(label="  Active Viewport: Use current viewport camera",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  All Renderable: Batch-playblast ALL cameras marked renderable",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  Selected Cameras: Choose specific cameras to playblast",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  NOTE: Camera name will be appended to filename (e.g., _renderCAM)",
                  align="left", font="smallPlainLabelFont")

        cmds.separator(height=5)

        self.ui_camera_frame = cmds.frameLayout(
            label="Select Cameras to Playblast",
            collapsable=False,
            borderStyle="in",
            visible=False,
        )
        cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
        
        self.ui_camera_list = cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
        cmds.setParent("..")
        
        cmds.rowLayout(numberOfColumns=2, columnWidth2=(250, 200))
        cmds.button(label="Refresh Camera List", command=self._refresh_cameras)
        cmds.button(label="Select All Cameras", command=self._select_all_cameras)
        cmds.setParent("..")
        
        cmds.setParent("..")
        cmds.setParent("..")

        cmds.separator(height=5)

        cmds.text(label="Viewport Options:", align="left", font="smallBoldLabelFont")
        cmds.text(label="Settings applied before playblast, restored after.",
                  align="left", font="smallPlainLabelFont")

        cmds.separator(height=3)

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(240, 220))
        self.ui_vp_aa = cmds.checkBox(label="Anti-Aliasing (MSAA)", value=True)
        self.ui_vp_ao = cmds.checkBox(label="Screen Space Ambient Occlusion", value=True)
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(240, 220))
        self.ui_vp_textures  = cmds.checkBox(label="Textures", value=True)
        self.ui_vp_wireframe = cmds.checkBox(label="Wireframe on Shaded", value=False)
        cmds.setParent("..")

        cmds.separator(height=3)
        cmds.text(label="Lighting Mode:", align="left", font="smallBoldLabelFont")
        self.ui_lighting_mode = cmds.optionMenu()
        cmds.menuItem(label="Default Lighting")
        cmds.menuItem(label="All Lights")
        cmds.menuItem(label="Grayscale Lighting")
        cmds.menuItem(label="Flat Shaded")

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(240, 220))
        self.ui_vp_shadows = cmds.checkBox(label="Shadows", value=False)
        self.ui_vp_mblur   = cmds.checkBox(label="Motion Blur", value=False)
        cmds.setParent("..")

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(240, 220))
        self.ui_vp_dof         = cmds.checkBox(label="Depth of Field (DOF)", value=False)
        self.ui_vp_image_plane = cmds.checkBox(label="Image Planes", value=False)
        cmds.setParent("..")

        self.ui_vp_ornaments = cmds.checkBox(label="Show Ornaments (HUD)", value=False)

        cmds.separator(height=3)
        cmds.text(label="  Default Lighting = Maya headlamp (recommended)",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  All Lights = Use all scene lights",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  Grayscale Lighting = Grey default material with lighting",
                  align="left", font="smallPlainLabelFont")
        cmds.text(label="  Flat Shaded = Colors with NO shading (true flat)",
                  align="left", font="smallPlainLabelFont")

        cmds.setParent("..")
        cmds.setParent("..")

    def _build_output_options_section(self):
        cmds.frameLayout(label="Output Options", collapsable=True,
                         collapse=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=3)
        self.ui_keep_pngs  = cmds.checkBox(
            label="Keep PNG sequence  (useful for compositing or backup)", value=False)
        self.ui_open_after = cmds.checkBox(
            label="Open video automatically after completion", value=True)
        cmds.setParent("..")
        cmds.setParent("..")

    def _build_progress_section(self):
        cmds.frameLayout(label="Progress", collapsable=False, borderStyle="etchedIn")
        cmds.columnLayout(adjustableColumn=True, rowSpacing=2)
        self.ui_progress_text = cmds.text(label="Ready.", align="left", height=20)
        self.ui_progress_bar  = cmds.progressBar(maxValue=100, width=500, visible=False)
        cmds.setParent("..")
        cmds.setParent("..")

    def _init_defaults(self):
        cmds.textField(self.ui_ffmpeg_path, edit=True, text=self._default_ffmpeg_path())
        cmds.textField(self.ui_filename,    edit=True, text=self._scene_basename())
        self._refresh_cameras()
        self._refresh_location_display()
        self._load_preferences()
        self._refresh_filename_preview()

    def _scene_basename(self):
        short = cmds.file(query=True, sceneName=True, shortName=True)
        if short:
            return os.path.splitext(short)[0]
        return "playblast"

    def _default_ffmpeg_path(self):
        if self.system == "Windows":
            candidates = [
                "C:/ffmpeg/bin/ffmpeg.exe",
                "C:/Program Files/ffmpeg/bin/ffmpeg.exe",
                os.path.join(os.path.expanduser("~"), "AppData", "Local",
                             "ffmpeg", "bin", "ffmpeg.exe"),
            ]
            for p in candidates:
                if os.path.exists(p):
                    return p
            return "ffmpeg.exe"
        elif self.system == "Darwin":
            for p in ["/opt/homebrew/bin/ffmpeg", "/usr/local/bin/ffmpeg"]:
                if os.path.exists(p):
                    return p
            return "/usr/local/bin/ffmpeg"
        return "/usr/bin/ffmpeg"

    def _sanitize_filename(self, name):
        """Remove illegal characters from filenames.
        
        Windows illegal chars: < > : " / \ | ? *
        Also replace spaces with underscores for cleaner names.
        """
        illegal_chars = [':', '/', '\\', '<', '>', '"', '|', '?', '*']
        clean_name = name
        for char in illegal_chars:
            clean_name = clean_name.replace(char, '_')
        # Replace multiple underscores with single
        while '__' in clean_name:
            clean_name = clean_name.replace('__', '_')
        return clean_name.strip('_')

    def _save_preferences(self):
        """Save UI settings to Maya preferences."""
        try:
            cmds.optionVar(intValue=("advPlayblast_resolution", 
                cmds.optionMenu(self.ui_resolution, query=True, select=True)))
            cmds.optionVar(intValue=("advPlayblast_crf", 
                cmds.intSlider(self.ui_crf_slider, query=True, value=True)))
            cmds.optionVar(intValue=("advPlayblast_speed", 
                cmds.optionMenu(self.ui_speed, query=True, select=True)))
            cmds.optionVar(intValue=("advPlayblast_rangeMode", 
                cmds.optionMenu(self.ui_range_menu, query=True, select=True)))
            cmds.optionVar(intValue=("advPlayblast_offscreen", 
                cmds.checkBox(self.ui_offscreen, query=True, value=True)))
            cmds.optionVar(intValue=("advPlayblast_audio", 
                cmds.checkBox(self.ui_audio, query=True, value=True)))
            cmds.optionVar(intValue=("advPlayblast_keepPngs", 
                cmds.checkBox(self.ui_keep_pngs, query=True, value=True)))
            cmds.optionVar(intValue=("advPlayblast_openAfter", 
                cmds.checkBox(self.ui_open_after, query=True, value=True)))
            cmds.optionVar(intValue=("advPlayblast_includeRange", 
                cmds.checkBox(self.ui_include_frame_range, query=True, value=True)))
        except Exception as e:
            print("Could not save preferences: {}".format(e))

    def _load_preferences(self):
        """Load UI settings from Maya preferences."""
        try:
            if cmds.optionVar(exists="advPlayblast_resolution"):
                cmds.optionMenu(self.ui_resolution, edit=True, 
                    select=cmds.optionVar(query="advPlayblast_resolution"))
            if cmds.optionVar(exists="advPlayblast_crf"):
                crf = cmds.optionVar(query="advPlayblast_crf")
                cmds.intSlider(self.ui_crf_slider, edit=True, value=crf)
                cmds.text(self.ui_crf_label, edit=True, label=self.CRF_LABELS.get(crf, str(crf)))
            if cmds.optionVar(exists="advPlayblast_speed"):
                cmds.optionMenu(self.ui_speed, edit=True, 
                    select=cmds.optionVar(query="advPlayblast_speed"))
            if cmds.optionVar(exists="advPlayblast_rangeMode"):
                cmds.optionMenu(self.ui_range_menu, edit=True, 
                    select=cmds.optionVar(query="advPlayblast_rangeMode"))
            if cmds.optionVar(exists="advPlayblast_offscreen"):
                cmds.checkBox(self.ui_offscreen, edit=True, 
                    value=cmds.optionVar(query="advPlayblast_offscreen"))
            if cmds.optionVar(exists="advPlayblast_audio"):
                cmds.checkBox(self.ui_audio, edit=True, 
                    value=cmds.optionVar(query="advPlayblast_audio"))
            if cmds.optionVar(exists="advPlayblast_keepPngs"):
                cmds.checkBox(self.ui_keep_pngs, edit=True, 
                    value=cmds.optionVar(query="advPlayblast_keepPngs"))
            if cmds.optionVar(exists="advPlayblast_openAfter"):
                cmds.checkBox(self.ui_open_after, edit=True, 
                    value=cmds.optionVar(query="advPlayblast_openAfter"))
            if cmds.optionVar(exists="advPlayblast_includeRange"):
                cmds.checkBox(self.ui_include_frame_range, edit=True, 
                    value=cmds.optionVar(query="advPlayblast_includeRange"))
        except Exception as e:
            print("Could not load preferences: {}".format(e))

    def _refresh_cameras(self, *args):
        if cmds.columnLayout(self.ui_camera_list, exists=True):
            children = cmds.columnLayout(self.ui_camera_list, query=True, childArray=True) or []
            for child in children:
                try:
                    cmds.deleteUI(child)
                except:
                    pass

        self.camera_checkboxes = {}
        
        cmds.setParent(self.ui_camera_list)
        
        all_cameras = []
        for cam_shape in cmds.ls(type="camera"):
            try:
                parents = cmds.listRelatives(cam_shape, parent=True, fullPath=False)
                if not parents:
                    continue
                
                transform = parents[0]
                if transform in [c[0] for c in all_cameras]:
                    continue
                
                is_renderable = False
                try:
                    is_renderable = cmds.getAttr(cam_shape + ".renderable")
                except:
                    pass
                
                all_cameras.append((transform, cam_shape, is_renderable))
            except:
                continue
        
        all_cameras.sort(key=lambda x: (not x[2], x[0]))
        
        for transform, cam_shape, is_renderable in all_cameras:
            label = "{} {}".format(transform, "(renderable)" if is_renderable else "")
            checkbox = cmds.checkBox(label=label, value=False)
            self.camera_checkboxes[transform] = checkbox
        
        if not all_cameras:
            cmds.text(label="No cameras found in scene", align="left", 
                     font="smallPlainLabelFont")

    def _select_all_cameras(self, *args):
        for checkbox in self.camera_checkboxes.values():
            try:
                cmds.checkBox(checkbox, edit=True, value=True)
            except:
                pass

    def _on_camera_mode_change(self, mode):
        """Show/hide camera selection frame based on mode."""
        print("\n" + "="*70)
        print("CAMERA MODE CHANGED TO: {}".format(mode))
        print("="*70)
        
        try:
            is_selected_mode = (mode == "selected")
            cmds.frameLayout(self.ui_camera_frame, edit=True, visible=is_selected_mode)
            print("Camera frame visible: {}".format(is_selected_mode))
            
            if is_selected_mode:
                self._refresh_cameras()
                
        except Exception as e:
            print("ERROR in _on_camera_mode_change: {}".format(e))
            import traceback
            print(traceback.format_exc())

    def _get_selected_cameras(self):
        """Get list of cameras to playblast based on mode."""
        selected_radio = cmds.radioCollection(self.ui_camera_mode, query=True, select=True)
        
        try:
            selected_label = cmds.radioButton(selected_radio, query=True, label=True)
        except:
            selected_label = "Active Viewport"
        
        print("\n" + "="*70)
        print("GETTING SELECTED CAMERAS")
        print("Selected radio button: {}".format(selected_radio))
        print("Selected label: {}".format(selected_label))
        print("="*70)
        
        if selected_label == "Active Viewport":
            print("MODE: Active Viewport")
            return ["__ACTIVE__"]
        
        elif selected_label == "All Renderable Cameras":
            print("MODE: All Renderable Cameras")
            renderable_cameras = []
            
            for cam_shape in cmds.ls(type="camera"):
                try:
                    is_renderable = cmds.getAttr(cam_shape + ".renderable")
                    parents = cmds.listRelatives(cam_shape, parent=True, fullPath=False)
                    transform = parents[0] if parents else None
                    
                    print("  Camera shape: {} | Transform: {} | Renderable: {}".format(
                        cam_shape, transform, is_renderable))
                    
                    if is_renderable and transform:
                        renderable_cameras.append(transform)
                        print("    -> ADDED to renderable list")
                        
                except Exception as e:
                    print("  Error checking camera {}: {}".format(cam_shape, e))
            
            print("\nTotal renderable cameras found: {}".format(len(renderable_cameras)))
            for cam in renderable_cameras:
                print("  - {}".format(cam))
            
            if not renderable_cameras:
                cmds.warning("No renderable cameras found in Render Settings")
            
            print("="*70 + "\n")
            return renderable_cameras
        
        elif selected_label == "Selected Cameras":
            print("MODE: Selected Cameras")
            selected_cameras = []
            for transform, checkbox in self.camera_checkboxes.items():
                try:
                    if cmds.checkBox(checkbox, query=True, value=True):
                        selected_cameras.append(transform)
                        print("  - {} (CHECKED)".format(transform))
                except:
                    pass
            
            print("Total selected cameras: {}".format(len(selected_cameras)))
            
            if not selected_cameras:
                cmds.warning("No cameras selected")
            
            print("="*70 + "\n")
            return selected_cameras
        
        print("FALLBACK: Returning Active Viewport")
        print("="*70 + "\n")
        return ["__ACTIVE__"]

    def _generate_filename(self, base_name, camera_name, frame_range, folder, auto_version):
        """Generate filename with sanitization and path length validation."""
        parts = [self._sanitize_filename(base_name)]
        
        if camera_name and camera_name != "__ACTIVE__":
            parts.append(self._sanitize_filename(camera_name))
        
        if frame_range:
            parts.append("{}-{}".format(frame_range[0], frame_range[1]))
        
        name_without_version = "_".join(parts)
        
        if auto_version:
            v = 1
            while v <= 9999:
                final_name = "{}_v{}.mp4".format(name_without_version, str(v).zfill(3))
                full_path = os.path.join(folder, final_name)
                
                # Check path length (Windows MAX_PATH = 260)
                if len(full_path) > 250:
                    print("\n" + "!"*70)
                    print("WARNING: Output path is very long ({} characters)".format(len(full_path)))
                    print("Path: {}".format(full_path))
                    print("This may cause issues on Windows (MAX_PATH = 260)")
                    print("Consider using a shorter base name or output folder")
                    print("!"*70 + "\n")
                
                if not os.path.exists(full_path):
                    return final_name
                v += 1
            return "{}_v9999.mp4".format(name_without_version)
        else:
            final_name = "{}.mp4".format(name_without_version)
            full_path = os.path.join(folder, final_name)
            
            if len(full_path) > 250:
                print("\n" + "!"*70)
                print("WARNING: Output path is very long ({} characters)".format(len(full_path)))
                print("Path: {}".format(full_path))
                print("!"*70 + "\n")
            
            return final_name

    def _setup_camera(self, cam_choice):
        panel = None
        try:
            focused = cmds.getPanel(withFocus=True)
            if focused and cmds.getPanel(typeOf=focused) == "modelPanel":
                panel = focused
        except:
            pass
        if not panel:
            panels = cmds.getPanel(type="modelPanel") or []
            panel = panels[0] if panels else None
        if not panel:
            return None, None

        original = cmds.modelEditor(panel, query=True, camera=True)

        if cam_choice == "__ACTIVE__":
            return panel, None
        else:
            if cam_choice != original:
                try:
                    cmds.modelEditor(panel, edit=True, camera=cam_choice)
                    print("Switched viewport to camera: {}".format(cam_choice))
                    return panel, original
                except Exception as e:
                    print("Warning: could not switch camera: {}".format(e))
            return panel, None

    def _save_viewport_settings(self, panel):
        saved = {}
        
        for flag in ("shadows", "imagePlane", "wireframeOnShaded", "displayTextures", "useDefaultMaterial"):
            try:
                saved[flag] = cmds.modelEditor(panel, query=True, **{flag: True})
            except:
                saved[flag] = False
        
        try:
            saved["displayLights"] = cmds.modelEditor(panel, query=True, displayLights=True)
        except:
            saved["displayLights"] = "default"
        
        for attr in ("ssaoEnable", "multiSampleEnable", "motionBlurEnable"):
            try:
                saved[attr] = cmds.getAttr("hardwareRenderingGlobals." + attr)
            except:
                saved[attr] = False
        
        return saved

    def _apply_viewport_settings(self, panel, s):
        print("\n" + "="*70)
        print("APPLYING VIEWPORT SETTINGS")
        print("="*70)
        print("Panel: {}".format(panel))
        
        lighting_mode = s["lighting_mode"]
        
        if lighting_mode == "Default Lighting":
            use_default_mat = False
            display_lights_mode = "default"
            print("LIGHTING: Default Lighting (Maya headlamp)")
        elif lighting_mode == "All Lights":
            use_default_mat = False
            display_lights_mode = "all"
            print("LIGHTING: All Lights (all scene lights)")
        elif lighting_mode == "Grayscale Lighting":
            use_default_mat = True
            display_lights_mode = "default"
            print("LIGHTING: Grayscale Lighting (grey material + headlamp)")
        elif lighting_mode == "Flat Shaded":
            use_default_mat = False
            display_lights_mode = "flat"
            print("LIGHTING: Flat Shaded (colors with NO shading)")
        
        try:
            cmds.modelEditor(panel, edit=True,
                imagePlane=s["vp_image_plane"],
                displayTextures=s["vp_textures"],
                wireframeOnShaded=s["vp_wireframe"],
                shadows=s["vp_shadows"],
                useDefaultMaterial=use_default_mat,
                displayLights=display_lights_mode,
            )
            
            print("Applied modelEditor settings:")
            print("  imagePlane: {}".format(s["vp_image_plane"]))
            print("  displayTextures: {}".format(s["vp_textures"]))
            print("  wireframeOnShaded: {}".format(s["vp_wireframe"]))
            print("  shadows: {}".format(s["vp_shadows"]))
            print("  useDefaultMaterial: {}".format(use_default_mat))
            print("  displayLights: {}".format(display_lights_mode))
            
        except Exception as e:
            print("ERROR applying modelEditor settings: {}".format(e))

        print("\nApplying VP2 hardware globals:")
        for attr, val in [
            ("ssaoEnable",        s["vp_ao"]),
            ("multiSampleEnable", s["vp_aa"]),
            ("motionBlurEnable",  s["vp_mblur"]),
        ]:
            try:
                cmds.setAttr("hardwareRenderingGlobals." + attr, val)
                print("  {}: {}".format(attr, val))
            except Exception as e:
                print("  ERROR setting {}: {}".format(attr, e))

        print("="*70)
        print("VIEWPORT SETTINGS APPLIED SUCCESSFULLY")
        print("="*70 + "\n")

    def _restore_viewport_settings(self, panel, saved):
        print("\n" + "="*70)
        print("RESTORING VIEWPORT SETTINGS")
        print("="*70)
        
        for flag in ("shadows", "imagePlane", "wireframeOnShaded", "displayTextures", "useDefaultMaterial"):
            try:
                val = saved.get(flag, False)
                cmds.modelEditor(panel, edit=True, **{flag: val})
                print("  Restored {}: {}".format(flag, val))
            except Exception as e:
                print("  ERROR restoring {}: {}".format(flag, e))
        
        try:
            light_val = saved.get("displayLights", "default")
            cmds.modelEditor(panel, edit=True, displayLights=light_val)
            print("  Restored displayLights: {}".format(light_val))
        except Exception as e:
            print("  ERROR restoring displayLights: {}".format(e))
        
        for attr in ("ssaoEnable", "multiSampleEnable", "motionBlurEnable"):
            try:
                val = saved.get(attr, False)
                cmds.setAttr("hardwareRenderingGlobals." + attr, val)
                print("  Restored {}: {}".format(attr, val))
            except Exception as e:
                print("  ERROR restoring {}: {}".format(attr, e))
        
        print("="*70)
        print("VIEWPORT SETTINGS RESTORED")
        print("="*70 + "\n")

    def _get_cam_dof_shape(self, panel):
        try:
            cam = cmds.modelEditor(panel, query=True, camera=True)
            shapes = cmds.listRelatives(cam, shapes=True, type="camera") or []
            return shapes[0] if shapes else None
        except:
            return None

    def _save_dof(self, cam_shape):
        if not cam_shape:
            return None
        try:
            return cmds.getAttr(cam_shape + ".depthOfField")
        except:
            return None

    def _apply_dof(self, cam_shape, value):
        if cam_shape is None or value is None:
            return
        try:
            cmds.setAttr(cam_shape + ".depthOfField", value)
            print("Applied DOF: {}".format(value))
        except:
            pass

    def _hide_all_huds(self):
        states = {}
        try:
            huds = cmds.headsUpDisplay(listHeadsUpDisplays=True) or []
            for hud in huds:
                try:
                    vis = cmds.headsUpDisplay(hud, query=True, visible=True)
                    states[hud] = vis
                    if vis:
                        cmds.headsUpDisplay(hud, edit=True, visible=False)
                except:
                    pass
        except:
            pass
        return states

    def _restore_huds(self, states):
        for hud, vis in states.items():
            try:
                cmds.headsUpDisplay(hud, edit=True, visible=vis)
            except:
                pass

    def _hide_all_image_planes(self):
        """Hide all image planes in the scene."""
        states = {}
        try:
            image_planes = cmds.ls(type="imagePlane")
            for img_plane in image_planes:
                try:
                    vis = cmds.getAttr(img_plane + ".displayMode")
                    states[img_plane] = vis
                    cmds.setAttr(img_plane + ".displayMode", 0)
                    print("Hidden image plane: {}".format(img_plane))
                except Exception as e:
                    print("Error hiding image plane {}: {}".format(img_plane, e))
        except Exception as e:
            print("Error in _hide_all_image_planes: {}".format(e))
        return states

    def _restore_image_planes(self, states):
        """Restore image plane visibility."""
        for img_plane, vis in states.items():
            try:
                cmds.setAttr(img_plane + ".displayMode", vis)
                print("Restored image plane {}: {}".format(img_plane, vis))
            except Exception as e:
                print("Error restoring image plane {}: {}".format(img_plane, e))

    def _resolve_output_folder(self):
        choice = cmds.optionMenu(self.ui_location_menu, query=True, value=True)
        if choice == "Same as Maya Scene":
            scene = cmds.file(query=True, sceneName=True)
            if scene:
                return os.path.dirname(scene)
            proj = cmds.workspace(query=True, rootDirectory=True)
            return os.path.join(proj, "movies") if proj else os.path.expanduser("~")
        elif choice == "Last Used Location":
            if cmds.optionVar(exists="advPlayblast_lastFolder"):
                last = cmds.optionVar(query="advPlayblast_lastFolder")
                if os.path.exists(last):
                    return last
            scene = cmds.file(query=True, sceneName=True)
            if scene:
                return os.path.dirname(scene)
            proj = cmds.workspace(query=True, rootDirectory=True)
            return os.path.join(proj, "movies") if proj else os.path.expanduser("~")
        elif choice == "Project Movies Folder":
            proj = cmds.workspace(query=True, rootDirectory=True)
            return os.path.join(proj, "movies") if proj else os.path.expanduser("~")
        elif choice == "Custom Location":
            custom = cmds.textField(self.ui_custom_folder, query=True, text=True).strip()
            return custom if custom else os.path.expanduser("~")
        return os.path.expanduser("~")

    def _on_location_change(self, *args):
        choice = cmds.optionMenu(self.ui_location_menu, query=True, value=True)
        cmds.rowLayout(self.ui_custom_loc_row, edit=True, visible=(choice == "Custom Location"))
        self._refresh_location_display()

    def _refresh_location_display(self):
        cmds.text(self.ui_location_display, edit=True,
                  label="Saving to:  {}".format(self._resolve_output_folder()))

    def _on_resolution_change(self, *args):
        cmds.rowLayout(self.ui_custom_res_row, edit=True,
                       visible=(cmds.optionMenu(self.ui_resolution, q=True, value=True) == "Custom"))

    def _on_quality_preset_change(self, *args):
        label = cmds.optionMenu(self.ui_quality_preset, query=True, value=True)
        for name, crf, desc in self.QUALITY_PRESETS:
            if label.startswith(name):
                cmds.intSlider(self.ui_crf_slider, edit=True, value=crf)
                cmds.text(self.ui_crf_label, edit=True, label=self.CRF_LABELS.get(crf, str(crf)))
                break

    def _on_crf_change(self, val):
        crf = int(val)
        cmds.text(self.ui_crf_label, edit=True, label=self.CRF_LABELS.get(crf, str(crf)))

    def _on_speed_change(self, *args):
        idx = cmds.optionMenu(self.ui_speed, query=True, select=True)
        _, desc = self.SPEED_LABELS[idx - 1]
        cmds.text(self.ui_speed_desc, edit=True, label=desc)

    def _on_range_change(self, *args):
        sel = cmds.optionMenu(self.ui_range_menu, query=True, value=True)
        cmds.rowLayout(self.ui_custom_range_row, edit=True, visible=(sel == "Custom"))
        if sel == "Custom":
            cmds.intField(self.ui_start_frame, edit=True,
                          value=int(cmds.playbackOptions(query=True, minTime=True)))
            cmds.intField(self.ui_end_frame, edit=True,
                          value=int(cmds.playbackOptions(query=True, maxTime=True)))
        self._refresh_filename_preview()

    def _refresh_filename_preview(self, *args):
        base = cmds.textField(self.ui_filename, query=True, text=True).strip() or "playblast"
        auto = cmds.checkBox(self.ui_auto_version, query=True, value=True)
        include_range = cmds.checkBox(self.ui_include_frame_range, query=True, value=True)
        
        rng = cmds.optionMenu(self.ui_range_menu, query=True, value=True)
        if rng == "Playback Range":
            start = int(cmds.playbackOptions(query=True, minTime=True))
            end = int(cmds.playbackOptions(query=True, maxTime=True))
        elif rng == "Animation Range":
            start = int(cmds.playbackOptions(query=True, animationStartTime=True))
            end = int(cmds.playbackOptions(query=True, animationEndTime=True))
        elif rng == "Custom":
            try:
                start = cmds.intField(self.ui_start_frame, query=True, value=True)
                end = cmds.intField(self.ui_end_frame, query=True, value=True)
            except:
                start, end = 1, 100
        else:
            start, end = 1, 100
        
        parts = [base]
        
        cameras = self._get_selected_cameras()
        if len(cameras) > 1 or (len(cameras) == 1 and cameras[0] != "__ACTIVE__"):
            parts.append("[cameraName]")
        
        if include_range:
            parts.append("{}-{}".format(start, end))
        
        name_preview = "_".join(parts)
        
        if auto:
            preview = "e.g.  {}_v001.mp4".format(name_preview)
        else:
            preview = "Will save as:  {}.mp4".format(name_preview)
        
        cmds.text(self.ui_filename_preview, edit=True, label=preview)

    def _browse_ffmpeg(self, *args):
        filt = "Executable (*.exe)" if self.system == "Windows" else "All (*)"
        r = cmds.fileDialog2(fileMode=1, caption="Select FFmpeg Executable", fileFilter=filt)
        if r:
            cmds.textField(self.ui_ffmpeg_path, edit=True, text=r[0])

    def _test_ffmpeg(self, *args):
        ffmpeg = cmds.textField(self.ui_ffmpeg_path, query=True, text=True).strip()
        try:
            code, out, err = self._run_cmd([ffmpeg, "-version"], timeout=10)
            if code == 0:
                cmds.confirmDialog(title="FFmpeg OK",
                                   message="Working!\n\n{}".format((out or err).split("\n")[0]),
                                   button=["OK"])
            else:
                cmds.confirmDialog(title="FFmpeg Failed",
                                   message="Test failed. Check the path.", button=["OK"])
        except Exception as e:
            cmds.confirmDialog(title="FFmpeg Error", message=str(e), button=["OK"])

    def _browse_output_folder(self, *args):
        r = cmds.fileDialog2(fileMode=3, caption="Select Output Folder")
        if r:
            cmds.textField(self.ui_custom_folder, edit=True, text=r[0])
            self._refresh_location_display()

    def _open_output_folder(self, *args):
        folder = self._resolve_output_folder()
        if not os.path.exists(folder):
            try:
                os.makedirs(folder)
            except Exception as e:
                cmds.confirmDialog(title="Error", message=str(e), button=["OK"])
                return
        self._open_in_explorer(folder)

    def _open_in_explorer(self, path):
        try:
            if self.system == "Windows":
                subprocess.Popen(["explorer", os.path.normpath(path)])
            elif self.system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print("Could not open folder: {}".format(e))

    def _open_file(self, path):
        for _ in range(50):
            if os.path.exists(path) and os.path.getsize(path) > 1024:
                break
            time.sleep(0.1)
        if not os.path.exists(path):
            print("Warning: file not found for auto-open: {}".format(path))
            return
        try:
            if self.system == "Windows":
                os.startfile(path)
            elif self.system == "Darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            print("Could not open file: {}".format(e))

    def _execute_playblast(self, *args):
        try:
            ffmpeg = cmds.textField(self.ui_ffmpeg_path, query=True, text=True).strip()
            if not self._ffmpeg_ok(ffmpeg):
                cmds.confirmDialog(title="Error",
                                   message="FFmpeg not found.\nInstall FFmpeg and set the correct path.",
                                   button=["OK"])
                return

            folder = self._resolve_output_folder()
            if not os.path.exists(folder):
                os.makedirs(folder)
            cmds.optionVar(stringValue=("advPlayblast_lastFolder", folder))
            
            # Save preferences before playblast
            self._save_preferences()

            cameras = self._get_selected_cameras()
            if not cameras:
                cmds.confirmDialog(title="Error",
                                   message="No cameras selected for playblast.",
                                   button=["OK"])
                return

            total_cameras = len(cameras)
            print("\n" + "="*70)
            print("MULTI-CAMERA PLAYBLAST: {} camera(s)".format(total_cameras))
            print("="*70)
            for i, cam in enumerate(cameras):
                print("  {}. {}".format(i+1, cam))
            print("="*70 + "\n")

            base_settings = self._collect_settings(ffmpeg, folder)
            
            completed_files = []
            for cam_idx, camera in enumerate(cameras):
                print("\n" + "="*70)
                print("PROCESSING CAMERA {}/{}: {}".format(cam_idx+1, total_cameras, camera))
                print("="*70 + "\n")
                
                progress_pct = int((cam_idx / float(total_cameras)) * 100)
                self._set_progress("Camera {}/{}: {}".format(cam_idx+1, total_cameras, camera), 
                                  progress_pct)
                
                try:
                    output_file = self._process_single_camera(camera, base_settings, cam_idx, total_cameras)
                    if output_file:
                        completed_files.append((camera, output_file))
                except Exception as e:
                    print("ERROR processing camera {}: {}".format(camera, e))
                    import traceback
                    print(traceback.format_exc())
            
            self._set_progress("Done: {} camera(s) completed".format(len(completed_files)), 100)
            self._show_multi_camera_completion(completed_files, folder)

        except Exception as exc:
            import traceback
            print(traceback.format_exc())
            cmds.confirmDialog(title="Error",
                               message="Playblast failed:\n\n{}".format(str(exc)), button=["OK"])
            self._set_progress("Error - see Script Editor.", 0)
            cmds.progressBar(self.ui_progress_bar, edit=True, visible=False)

    def _process_single_camera(self, camera, base_settings, cam_idx, total_cameras):
        panel = None
        orig_cam = None
        vp_backup = {}
        dof_shape = None
        dof_backup = None
        hud_backup = {}
        img_plane_backup = {}

        try:
            s = dict(base_settings)
            
            panel, orig_cam = self._setup_camera(camera)
            if not panel:
                print("ERROR: Could not get panel for camera: {}".format(camera))
                return None

            camera_name = camera if camera != "__ACTIVE__" else None
            frame_range = (s["start"], s["end"]) if s["include_frame_range"] else None
            s["final_filename"] = self._generate_filename(
                s["base_name"], camera_name, frame_range, s["folder"], s["auto_version"]
            )
            s["final_path"] = os.path.join(s["folder"], s["final_filename"])

            print("\n" + ">"*70)
            print("OUTPUT FILE DETAILS:")
            print("  Folder: {}".format(s["folder"]))
            print("  Filename: {}".format(s["final_filename"]))
            print("  Full path: {}".format(s["final_path"]))
            print("  Path length: {} characters".format(len(s["final_path"])))
            print(">"*70 + "\n")

            if panel:
                vp_backup = self._save_viewport_settings(panel)
                dof_shape = self._get_cam_dof_shape(panel)
                dof_backup = self._save_dof(dof_shape)
                self._apply_viewport_settings(panel, s)
                self._apply_dof(dof_shape, s["vp_dof"])

            if not s["vp_ornaments"]:
                hud_backup = self._hide_all_huds()
            
            if not s["vp_image_plane"]:
                img_plane_backup = self._hide_all_image_planes()

            temp_dir = os.path.join(s["folder"], "_temp_playblast_{}".format(
                self._sanitize_filename(camera)))
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)

            try:
                self._do_png_sequence(temp_dir, s)
                
                # Add small delay to ensure PNG writes complete
                time.sleep(0.5)
                
                audio_info = self._do_encode(temp_dir, s)
                
                if s["keep_pngs"]:
                    png_folder = self._move_pngs(temp_dir, s["final_filename"], s["folder"])
                else:
                    self._remove_dir(temp_dir)
                
                return s["final_path"]
                
            finally:
                if hud_backup:
                    self._restore_huds(hud_backup)
                if img_plane_backup:
                    self._restore_image_planes(img_plane_backup)
                if panel and vp_backup:
                    self._restore_viewport_settings(panel, vp_backup)
                    self._apply_dof(dof_shape, dof_backup)
                if panel and orig_cam:
                    try:
                        cmds.modelEditor(panel, edit=True, camera=orig_cam)
                        print("Restored viewport to original camera: {}".format(orig_cam))
                    except:
                        pass

        except Exception as e:
            print("ERROR in _process_single_camera: {}".format(e))
            import traceback
            print(traceback.format_exc())
            return None

    def _close_window(self, *args):
        # Save preferences before closing
        self._save_preferences()
        
        if cmds.dockControl(self.dock_name, exists=True):
            cmds.deleteUI(self.dock_name)
        elif cmds.window(self.window_name, exists=True):
            cmds.deleteUI(self.window_name)

    def _collect_settings(self, ffmpeg, folder):
        s = {}
        s["ffmpeg"]         = ffmpeg
        s["folder"]         = folder
        s["base_name"]      = cmds.textField(self.ui_filename, query=True, text=True).strip() or "playblast"
        s["auto_version"]   = cmds.checkBox(self.ui_auto_version, query=True, value=True)
        s["include_frame_range"] = cmds.checkBox(self.ui_include_frame_range, query=True, value=True)

        res = cmds.optionMenu(self.ui_resolution, query=True, value=True)
        res_map = {
            "Current Viewport":        (None, None),
            "HD 720p  (1280 x 720)":   (1280, 720),
            "HD 1080p  (1920 x 1080)": (1920, 1080),
            "2K  (2048 x 1152)":       (2048, 1152),
            "4K  (3840 x 2160)":       (3840, 2160),
        }
        s["width"], s["height"] = res_map.get(res, (
            cmds.intField(self.ui_custom_w, query=True, value=True),
            cmds.intField(self.ui_custom_h, query=True, value=True),
        ))

        s["crf"]    = cmds.intSlider(self.ui_crf_slider, query=True, value=True)
        idx         = cmds.optionMenu(self.ui_speed, query=True, select=True)
        s["preset"] = self.SPEED_LABELS[idx - 1][0]

        rng = cmds.optionMenu(self.ui_range_menu, query=True, value=True)
        if rng == "Playback Range":
            s["start"] = int(cmds.playbackOptions(query=True, minTime=True))
            s["end"]   = int(cmds.playbackOptions(query=True, maxTime=True))
        elif rng == "Animation Range":
            s["start"] = int(cmds.playbackOptions(query=True, animationStartTime=True))
            s["end"]   = int(cmds.playbackOptions(query=True, animationEndTime=True))
        else:
            s["start"] = cmds.intField(self.ui_start_frame, query=True, value=True)
            s["end"]   = cmds.intField(self.ui_end_frame,   query=True, value=True)

        s["fps"]       = self._maya_fps()
        s["offscreen"] = cmds.checkBox(self.ui_offscreen,  query=True, value=True)
        s["audio"]     = cmds.checkBox(self.ui_audio,      query=True, value=True)
        s["keep_pngs"] = cmds.checkBox(self.ui_keep_pngs,  query=True, value=True)
        s["open_after"]= cmds.checkBox(self.ui_open_after, query=True, value=True)

        s["lighting_mode"] = cmds.optionMenu(self.ui_lighting_mode, query=True, value=True)

        s["vp_image_plane"] = cmds.checkBox(self.ui_vp_image_plane, query=True, value=True)
        s["vp_textures"]    = cmds.checkBox(self.ui_vp_textures,    query=True, value=True)
        s["vp_wireframe"]   = cmds.checkBox(self.ui_vp_wireframe,   query=True, value=True)
        s["vp_ao"]          = cmds.checkBox(self.ui_vp_ao,          query=True, value=True)
        s["vp_shadows"]     = cmds.checkBox(self.ui_vp_shadows,     query=True, value=True)
        s["vp_aa"]          = cmds.checkBox(self.ui_vp_aa,          query=True, value=True)
        s["vp_mblur"]       = cmds.checkBox(self.ui_vp_mblur,       query=True, value=True)
        s["vp_dof"]         = cmds.checkBox(self.ui_vp_dof,         query=True, value=True)
        s["vp_ornaments"]   = cmds.checkBox(self.ui_vp_ornaments,   query=True, value=True)

        return s

    def _maya_fps(self):
        unit = cmds.currentUnit(query=True, time=True)
        lut = {"game": 15, "film": 24, "pal": 25, "ntsc": 30, "show": 48,
               "palf": 50, "ntscf": 60, "23.976fps": 23.976, "29.97fps": 29.97,
               "29.97df": 29.97, "47.952fps": 47.952, "59.94fps": 59.94}
        if "fps" in unit:
            try:
                return float(unit.replace("fps", "").replace("df", ""))
            except ValueError:
                pass
        if unit in lut:
            return float(lut[unit])
        try:
            return float(mel.eval("currentTimeUnitToFPS()"))
        except:
            return 24.0

    def _do_png_sequence(self, temp_dir, s):
        show_ornaments = s["vp_ornaments"]
        kwargs = {
            "filename": os.path.join(temp_dir, "frame"), "format": "image",
            "compression": "png", "startTime": s["start"], "endTime": s["end"],
            "viewer": False, "showOrnaments": show_ornaments,
            "offScreen": s["offscreen"], "percent": 100, "quality": 100,
        }
        if s["width"] and s["height"]:
            kwargs["widthHeight"] = [s["width"], s["height"]]
        
        print("\n" + ">"*70)
        print("CREATING PNG SEQUENCE")
        print("  Directory: {}".format(temp_dir))
        print("  Frames: {} to {}".format(s["start"], s["end"]))
        print("  Resolution: {}x{}".format(s["width"] or "viewport", s["height"] or "viewport"))
        print(">"*70 + "\n")
        
        cmds.playblast(**kwargs)
        
        # Verify PNGs were created
        png_count = len(glob.glob(os.path.join(temp_dir, "*.png")))
        expected_count = s["end"] - s["start"] + 1
        print("\nPNG Sequence Created: {} files (expected {})".format(png_count, expected_count))
        
        if png_count == 0:
            raise RuntimeError("No PNG files were created in temp directory!")
        if png_count < expected_count:
            print("WARNING: Fewer PNGs than expected ({} vs {})".format(png_count, expected_count))

    def _do_encode(self, temp_dir, s):
        in_pat = os.path.join(temp_dir, "frame.%04d.png")
        cmd = [s["ffmpeg"], "-y", "-framerate", str(s["fps"]),
               "-start_number", str(s["start"]), "-i", in_pat]

        audio_info = {"included": False, "status": "Disabled by user"}
        if s["audio"]:
            wav, delay = self._extract_audio(s, temp_dir)
            if wav and os.path.exists(wav):
                if delay > 0:
                    cmd.extend(["-itsoffset", str(delay)])
                cmd.extend(["-i", wav, "-map", "0:v:0", "-map", "1:a:0",
                            "-c:a", "aac", "-b:a", "192k", "-vsync", "cfr"])
                audio_info = {"included": True, "offset_sec": delay, "status": "Included and synced"}
            else:
                audio_info = {"included": False, "status": "No audio found in scene"}

        cmd.extend(["-c:v", "libx264", "-r", str(s["fps"]), "-preset", s["preset"],
                    "-crf", str(s["crf"]), "-profile:v", "high", "-level:v", "4.2",
                    "-pix_fmt", "yuv420p", "-movflags", "+faststart", s["final_path"]])

        print("\n" + ">"*70)
        print("ENCODING WITH FFMPEG")
        print("FFmpeg command:")
        print("  " + " ".join(cmd))
        print(">"*70 + "\n")
        
        code, _, err = self._run_cmd(cmd, timeout=900)
        
        if code != 0:
            raise RuntimeError("FFmpeg encoding failed (exit code {}):\n{}".format(code, err))
        
        # CRITICAL: Validate output file exists and has data
        if not os.path.exists(s["final_path"]):
            raise RuntimeError(
                "FFmpeg reported success but output file was not created!\n"
                "Expected: {}".format(s["final_path"])
            )
        
        file_size = os.path.getsize(s["final_path"])
        if file_size < 1024:  # Less than 1KB
            raise RuntimeError(
                "FFmpeg encoding failed - output file is empty or corrupted!\n"
                "File: {}\n"
                "Size: {} bytes".format(s["final_path"], file_size)
            )
        
        size_mb = file_size / (1024.0 * 1024.0)
        print("\n" + "✓"*70)
        print("ENCODING SUCCESSFUL")
        print("  File: {}".format(os.path.basename(s["final_path"])))
        print("  Size: {:.2f} MB ({} bytes)".format(size_mb, file_size))
        print("  Path: {}".format(s["final_path"]))
        print("✓"*70 + "\n")
        
        return audio_info

    def _extract_audio(self, s, temp_dir):
        try:
            nodes = cmds.ls(type="audio")
            if not nodes:
                return None, 0
            wav = os.path.join(temp_dir, "_audio.wav")
            fps = float(s["fps"])
            pb_start_sec = s["start"] / fps
            pb_dur_sec   = (s["end"] - s["start"] + 1) / fps
            for node in nodes:
                try:
                    audio_path = cmds.getAttr("{}.filename".format(node))
                    if not audio_path or not os.path.exists(audio_path):
                        continue
                    try:
                        offset_frames = float(cmds.getAttr("{}.offset".format(node)))
                    except:
                        offset_frames = 1.0
                    try:
                        src_start = float(cmds.getAttr("{}.sourceStart".format(node)))
                        src_end   = float(cmds.getAttr("{}.sourceEnd".format(node)))
                    except:
                        src_start = 0.0
                        src_end   = self._audio_duration(audio_path, s["ffmpeg"])
                    clip_start_sec = offset_frames / fps
                    extract_from   = src_start + max(0.0, pb_start_sec - clip_start_sec)
                    extract_dur    = min(pb_dur_sec, src_end - extract_from)
                    video_delay    = max(0.0, clip_start_sec - pb_start_sec)
                    if extract_dur <= 0:
                        continue
                    code, _, _ = self._run_cmd([
                        s["ffmpeg"], "-y", "-i", audio_path,
                        "-ss", str(extract_from), "-t", str(extract_dur),
                        "-acodec", "pcm_s16le", "-ar", "48000", wav,
                    ], timeout=60)
                    if code == 0 and os.path.exists(wav):
                        return wav, video_delay
                except Exception as e:
                    print("Audio node '{}': {}".format(node, e))
            return None, 0
        except Exception as e:
            print("_extract_audio: {}".format(e))
            return None, 0

    def _audio_duration(self, path, ffmpeg):
        try:
            _, _, err = self._run_cmd([ffmpeg, "-i", path, "-f", "null", "-"], timeout=30)
            m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", err)
            if m:
                return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        except:
            pass
        return 60.0

    def _run_cmd(self, cmd, timeout=30):
        if PY3:
            proc = subprocess.run(cmd, stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE, timeout=timeout)
            return (proc.returncode,
                    proc.stdout.decode("utf-8", errors="replace"),
                    proc.stderr.decode("utf-8", errors="replace"))
        else:
            proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate()
            return (proc.returncode,
                    out.decode("utf-8", errors="replace"),
                    err.decode("utf-8", errors="replace"))

    def _ffmpeg_ok(self, ffmpeg):
        try:
            code, _, _ = self._run_cmd([ffmpeg, "-version"], timeout=8)
            return code == 0
        except:
            return False

    def _move_pngs(self, temp_dir, final_filename, folder):
        dest = os.path.join(folder, final_filename.replace(".mp4", "_PNGs"))
        if not os.path.exists(dest):
            os.makedirs(dest)
        for f in glob.glob(os.path.join(temp_dir, "*.png")):
            shutil.move(f, os.path.join(dest, os.path.basename(f)))
        try:
            os.rmdir(temp_dir)
        except:
            pass
        return dest

    def _remove_dir(self, path):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
        except Exception as e:
            print("Cleanup: {}".format(e))

    def _show_multi_camera_completion(self, completed_files, folder):
        win = "advPlayblastComplete"
        if cmds.window(win, exists=True):
            cmds.deleteUI(win)

        cmds.window(win, title="Playblast Complete - {} Cameras".format(len(completed_files)), 
                   width=620, height=600, sizeable=True)
        cmds.columnLayout(adjustableColumn=True, rowSpacing=5)

        cmds.separator(height=5, style="none")
        cmds.text(label="Multi-Camera Playblast Complete  -  v{}".format(self.VERSION),
                  font="boldLabelFont", height=24)
        cmds.text(label="{} camera(s) processed".format(len(completed_files)),
                  font="smallBoldLabelFont", height=20)

        cmds.separator(height=8)
        
        report_lines = []
        report_lines.append("=" * 52)
        report_lines.append("  MULTI-CAMERA PLAYBLAST REPORT")
        report_lines.append("=" * 52)
        report_lines.append("")
        report_lines.append("COMPLETED CAMERAS: {}".format(len(completed_files)))
        report_lines.append("")
        
        for i, (camera, filepath) in enumerate(completed_files):
            filename = os.path.basename(filepath)
            try:
                size_mb = os.path.getsize(filepath) / (1024.0 * 1024.0)
            except:
                size_mb = 0.0
            report_lines.append("{}. {}".format(i+1, camera))
            report_lines.append("   File: {}".format(filename))
            report_lines.append("   Size: {:.2f} MB".format(size_mb))
            report_lines.append("")
        
        report_lines.append("OUTPUT FOLDER")
        report_lines.append("  {}".format(folder))
        report_lines.append("")
        report_lines.append("=" * 52)
        
        report_text = "\n".join(report_lines)
        print("\n" + report_text)
        
        cmds.scrollField(text=report_text, editable=False, wordWrap=True, height=400)
        cmds.separator(height=8)

        cmds.rowLayout(numberOfColumns=2, columnWidth2=(310, 310))
        cmds.button(label="Open Folder", height=36,
                    command=lambda *args: self._open_in_explorer(folder))
        cmds.button(label="Close", height=36,
                    command='import maya.cmds as cmds; cmds.deleteUI("{}")'.format(win))
        cmds.setParent("..")
        cmds.separator(height=5, style="none")

        cmds.showWindow(win)

    def _set_progress(self, msg, pct=None):
        cmds.text(self.ui_progress_text, edit=True, label=msg)
        if pct is not None:
            cmds.progressBar(self.ui_progress_bar, edit=True, visible=True, progress=pct)
        cmds.refresh()


def show_advanced_playblast_tool(dockable=False):
    """
    Launch the Advanced Playblast Tool v3.2
    
    Usage:
        show_advanced_playblast_tool()              # floating window
        show_advanced_playblast_tool(dockable=True) # dockable panel
    """
    global _adv_playblast_instance
    _adv_playblast_instance = AdvancedPlayblastTool()
    _adv_playblast_instance.create_ui(dockable=dockable)


if __name__ == "__main__":
    show_advanced_playblast_tool()


def show_ui():
    show_advanced_playblast_tool()
