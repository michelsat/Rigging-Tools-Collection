import sys
import os
import subprocess
import threading
import site
import glob
import shutil
import tempfile

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from PySide2 import QtWidgets, QtCore
from shiboken2 import wrapInstance


def get_maya_main_window():
    ptr = omui.MQtUtil.mainWindow()
    return wrapInstance(int(ptr), QtWidgets.QWidget)


class MayaPipInstallerUI(QtWidgets.QDialog):

    log_signal = QtCore.Signal(str)
    busy_signal = QtCore.Signal(bool)
    refresh_signal = QtCore.Signal()
    installed_signal = QtCore.Signal(object)

    def __init__(self, parent=get_maya_main_window()):
        super(MayaPipInstallerUI, self).__init__(parent)
        self.setWindowTitle("Maya Pip Installer")
        self.setMinimumWidth(620)
        self.setMinimumHeight(560)
        self.setWindowFlags(self.windowFlags() ^ QtCore.Qt.WindowContextHelpButtonHint)

        self.maya_version = str(int(cmds.about(version=True)))
        self._installed_scan_active = False
        self._build_ui()
        self._resolve_default_path()
        self.log_signal.connect(self._append_log)
        self.busy_signal.connect(self._set_busy)
        self.refresh_signal.connect(self._refresh_installed_async)
        self.installed_signal.connect(self._show_installed_packages)

        # Let Maya draw the dialog first; package discovery runs off the UI thread.
        QtCore.QTimer.singleShot(0, self._refresh_installed_async)

    # ─────────────────────────────────────────────────────────────
    # UI
    # ─────────────────────────────────────────────────────────────
    def _build_ui(self):
        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setSpacing(8)
        main_layout.setContentsMargins(12, 12, 12, 12)

        title = QtWidgets.QLabel("🐍 Maya Pip Package Installer")
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #e0a040;")
        main_layout.addWidget(title)

        sep = QtWidgets.QFrame()
        sep.setFrameShape(QtWidgets.QFrame.HLine)
        sep.setStyleSheet("color: #444;")
        main_layout.addWidget(sep)

        # Package input
        pkg_layout = QtWidgets.QHBoxLayout()
        pkg_label = QtWidgets.QLabel("Package(s):")
        pkg_label.setFixedWidth(90)
        self.pkg_input = QtWidgets.QLineEdit()
        self.pkg_input.setPlaceholderText("e.g. numpy   or   scipy requests zBuilder")
        self.pkg_input.setToolTip("Space-separated for multiple packages")
        pkg_layout.addWidget(pkg_label)
        pkg_layout.addWidget(self.pkg_input)
        main_layout.addLayout(pkg_layout)

        # Flags
        flags_layout = QtWidgets.QHBoxLayout()
        self.chk_upgrade = QtWidgets.QCheckBox("--upgrade")
        self.chk_upgrade.setToolTip("Upgrade if already installed")
        self.chk_no_deps = QtWidgets.QCheckBox("--no-deps")
        self.chk_no_deps.setToolTip("Skip installing dependencies")
        self.chk_user = QtWidgets.QCheckBox("--user")
        self.chk_user.setToolTip(
            "Install to mayapy user site-packages.\n"
            "When checked, the 'Install To' directory is ignored."
        )
        self.chk_user.stateChanged.connect(self._on_user_flag_changed)
        self.chk_admin = QtWidgets.QCheckBox("Use Administrator")
        self.chk_admin.setChecked(True)
        self.chk_admin.setToolTip(
            "Required to install into Maya's Program Files site-packages folder.\n"
            "Windows will show a UAC prompt only when needed."
        )

        flags_layout.addWidget(self.chk_upgrade)
        flags_layout.addWidget(self.chk_no_deps)
        flags_layout.addWidget(self.chk_user)
        flags_layout.addWidget(self.chk_admin)
        flags_layout.addStretch()
        main_layout.addLayout(flags_layout)

        # Target directory
        target_layout = QtWidgets.QHBoxLayout()
        target_label = QtWidgets.QLabel("Install To:")
        target_label.setFixedWidth(90)
        self.target_input = QtWidgets.QLineEdit()
        self.target_input.setToolTip("Custom install target directory (ignored when --user is checked)")
        self.browse_btn = QtWidgets.QPushButton("Browse")
        self.browse_btn.setFixedWidth(80)
        self.browse_btn.clicked.connect(self._browse_directory)
        target_layout.addWidget(target_label)
        target_layout.addWidget(self.target_input)
        target_layout.addWidget(self.browse_btn)
        main_layout.addLayout(target_layout)

        # mayapy path
        mayapy_layout = QtWidgets.QHBoxLayout()
        mayapy_label = QtWidgets.QLabel("mayapy:")
        mayapy_label.setFixedWidth(90)
        self.mayapy_input = QtWidgets.QLineEdit()
        self.mayapy_input.setReadOnly(True)
        self.mayapy_input.setStyleSheet("color: #aaa;")
        mayapy_layout.addWidget(mayapy_label)
        mayapy_layout.addWidget(self.mayapy_input)
        main_layout.addLayout(mayapy_layout)

        # Installed packages label
        installed_label = QtWidgets.QLabel(
            "Installed Packages   "
            "[Maya Install] needs Administrator permission  |  "
            "[Maya Site] / [Custom Target] / [User Site] are user-writable"
        )
        installed_label.setStyleSheet("color: #aaa; font-size: 10px;")
        main_layout.addWidget(installed_label)

        # Installed packages list
        self.installed_list = QtWidgets.QListWidget()
        self.installed_list.setFixedHeight(140)
        self.installed_list.setStyleSheet("font-size: 11px; background: #2b2b2b;")
        self.installed_list.itemClicked.connect(self._fill_selected_package)
        main_layout.addWidget(self.installed_list)

        # Buttons
        btn_layout = QtWidgets.QHBoxLayout()

        self.install_btn = QtWidgets.QPushButton("Install")
        self.install_btn.setFixedHeight(34)
        self.install_btn.setStyleSheet(
            "background-color: #3a7a3a; color: white; font-weight: bold; border-radius: 4px;"
        )
        self.install_btn.clicked.connect(self._start_install)

        self.uninstall_btn = QtWidgets.QPushButton("Uninstall")
        self.uninstall_btn.setFixedHeight(34)
        self.uninstall_btn.setStyleSheet(
            "background-color: #7a3a3a; color: white; font-weight: bold; border-radius: 4px;"
        )
        self.uninstall_btn.clicked.connect(self._start_uninstall)

        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.refresh_btn.setFixedHeight(34)
        self.refresh_btn.clicked.connect(self._refresh_installed_async)

        self.open_folder_btn = QtWidgets.QPushButton("Open Folder")
        self.open_folder_btn.setFixedHeight(34)
        self.open_folder_btn.clicked.connect(self._open_target_folder)

        clear_btn = QtWidgets.QPushButton("Clear Log")
        clear_btn.setFixedHeight(34)
        clear_btn.clicked.connect(self._clear_log)

        btn_layout.addWidget(self.install_btn)
        btn_layout.addWidget(self.uninstall_btn)
        btn_layout.addWidget(self.refresh_btn)
        btn_layout.addWidget(self.open_folder_btn)
        btn_layout.addStretch()
        btn_layout.addWidget(clear_btn)
        main_layout.addLayout(btn_layout)

        # Progress bar
        self.progress = QtWidgets.QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(6)
        self.progress.setTextVisible(False)
        main_layout.addWidget(self.progress)

        # Log output
        log_label = QtWidgets.QLabel("Output Log:")
        log_label.setStyleSheet("color: #aaa; font-size: 11px;")
        main_layout.addWidget(log_label)

        self.log_output = QtWidgets.QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet(
            "background: #1e1e1e; color: #c8c8c8; font-family: Consolas, monospace; font-size: 11px;"
        )
        main_layout.addWidget(self.log_output)

    # ─────────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────────
    def _on_user_flag_changed(self, state):
        is_user = (state == QtCore.Qt.Checked)
        self.target_input.setEnabled(not is_user)
        self.browse_btn.setEnabled(not is_user)
        self.chk_admin.setEnabled(not is_user)
        self.target_input.setStyleSheet("color: #666;" if is_user else "")

    def _resolve_default_path(self):
        maya_bin = os.path.dirname(sys.executable)
        ext = ".exe" if os.name == "nt" else ""
        mayapy_path = os.path.join(maya_bin, "mayapy" + ext)
        self.mayapy_input.setText(mayapy_path)

        # The active Maya executable determines the matching version path.
        # Do not create this protected directory during startup: that needs UAC.
        default_target = self._get_maya_system_site_packages()
        if not default_target:
            default_target = self._get_maya_user_site_packages()
        self.target_input.setText(default_target)
        self.target_input.setToolTip(
            "Default: active Maya installation site-packages. "
            "Windows asks for Administrator permission when installing here."
        )

    @staticmethod
    def _is_protected_path(path):
        protected = []
        if os.name == "nt":
            pf = os.environ.get("ProgramFiles", r"C:\Program Files")
            pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
            win = os.environ.get("SystemRoot", r"C:\Windows")
            protected = [pf, pf86, win]
        else:
            protected = ["/usr/lib", "/usr/local/lib", "/System", "/Library"]

        norm = os.path.normcase(os.path.normpath(path))
        return any(norm.startswith(os.path.normcase(os.path.normpath(p))) for p in protected)

    def _browse_directory(self):
        path = QtWidgets.QFileDialog.getExistingDirectory(self, "Select Install Directory")
        if path:
            self.target_input.setText(path)

    def _append_log(self, text):
        self.log_output.append(text)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def _clear_log(self):
        self.log_output.clear()

    def _set_busy(self, busy):
        self.install_btn.setEnabled(not busy)
        self.uninstall_btn.setEnabled(not busy)
        self.refresh_btn.setEnabled(not busy)
        self.open_folder_btn.setEnabled(not busy)
        self.progress.setVisible(busy)

    def _fill_selected_package(self, item):
        text = item.text().strip()
        pkg_name = text.split("==")[0].split("[")[0].strip()
        self.pkg_input.setText(pkg_name)

    def _open_target_folder(self):
        path = self.target_input.text().strip()
        if not path:
            return
        if not os.path.exists(path):
            os.makedirs(path, exist_ok=True)

        if os.name == "nt":
            os.startfile(path)
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])

    # ─────────────────────────────────────────────────────────────
    # Package paths
    # ─────────────────────────────────────────────────────────────
    def _get_user_site_packages(self):
        # This tool runs inside the same mayapy version shown above.  Calling
        # site directly avoids starting another mayapy process during every refresh.
        return site.getusersitepackages()

    def _get_maya_user_site_packages(self):
        if os.name == "nt":
            path = os.path.join(
                os.path.expanduser("~"),
                "Documents", "maya",
                self.maya_version,
                "scripts", "site-packages"
            )
        else:
            path = os.path.expanduser("~/maya/{}/scripts/site-packages".format(self.maya_version))

        os.makedirs(path, exist_ok=True)
        return path

    def _get_maya_system_site_packages(self):
        """
        Returns the active Maya installation's built-in site-packages path.
        This is under Program Files on Windows and needs Administrator
        permission when it is used as an install target.
        e.g. C:\\Program Files\\Autodesk\\Maya2023\\Python\\Lib\\site-packages
        """
        # Build the path from the active Maya executable instead of launching
        # a second mayapy just to ask it for sys.path.
        maya_bin = os.path.dirname(self.mayapy_input.text())
        if os.name == "nt":
            candidate = os.path.join(maya_bin, "..", "Python", "Lib", "site-packages")
        else:
            candidate = os.path.join(maya_bin, "..", "lib", "python*", "site-packages")
            matches = glob.glob(candidate)
            if matches:
                return os.path.normpath(matches[0])
            return ""

        candidate = os.path.normpath(candidate)
        if os.path.exists(candidate):
            return candidate
        return ""

    # ─────────────────────────────────────────────────────────────
    # Detect installed packages
    # ─────────────────────────────────────────────────────────────
    @staticmethod
    def _normalise_package_name(name):
        return name.lower().replace("_", "-").replace(".", "-")

    @staticmethod
    def _normalise_path(path):
        return os.path.normcase(os.path.normpath(path)) if path else ""

    def _scan_installed_packages(self, target_path, maya_system_site, maya_site, user_site):
        """Read package metadata directly; no slow mayapy/pip subprocesses."""
        found = {}

        def add_package(name, version, path_label):
            if not name:
                return
            # Keep different installed versions visible instead of silently
            # merging them when a package exists in more than one location.
            key = (self._normalise_package_name(name), version or "")
            record = found.setdefault(key, {
                "name": name,
                "version": version or "",
                "locations": []
            })
            if path_label not in record["locations"]:
                record["locations"].append(path_label)

        def scan_folder(folder, path_label):
            if not folder or not os.path.isdir(folder):
                return

            metadata_names = set()
            try:
                try:
                    from importlib import metadata
                except ImportError:
                    import importlib_metadata as metadata

                for distribution in metadata.distributions(path=[folder]):
                    name = distribution.metadata.get("Name") or distribution.name
                    add_package(name, distribution.version, path_label)
                    metadata_names.add(self._normalise_package_name(name))
            except Exception:
                # A damaged metadata folder must not prevent the rest of the list loading.
                pass

            # Maya ships a few raw packages without package metadata.  Include
            # those as a fallback, but ignore standard library/internal files.
            skip_prefixes = ("python", "_", ".", "pkg_resources", "easy_install")
            skip_exact = {"site.py", "site.pyc", "__pycache__"}
            try:
                entries = os.listdir(folder)
            except OSError:
                return

            for entry in entries:
                lower = entry.lower()
                if entry in skip_exact or any(lower.startswith(prefix) for prefix in skip_prefixes):
                    continue
                if lower.endswith((".dist-info", ".egg-info", ".pth", ".pyd", ".so", ".dll")):
                    continue
                display = entry[:-3] if lower.endswith(".py") else entry
                if self._normalise_package_name(display) not in metadata_names:
                    add_package(display, "", path_label)

        scan_folder(maya_system_site, "[Maya Install]")
        if self._normalise_path(target_path) != self._normalise_path(maya_system_site):
            scan_folder(target_path, "[Custom Target]")
        scan_folder(maya_site, "[Maya Site]")
        scan_folder(user_site, "[User Site]")

        items = []
        for record in sorted(found.values(), key=lambda item: item["name"].lower()):
            label = record["name"]
            if record["version"]:
                label += "==" + record["version"]
            label += "   " + " ".join(record["locations"])
            items.append(label)
        return items

    def _refresh_installed_async(self):
        """Load package information in a worker so opening the UI stays instant."""
        if self._installed_scan_active:
            return
        self._installed_scan_active = True
        self.refresh_btn.setEnabled(False)
        self.installed_list.clear()
        self.installed_list.addItem("Scanning installed packages…")

        paths = (
            self.target_input.text().strip(),
            self._get_maya_system_site_packages(),
            self._get_maya_user_site_packages(),
            self._get_user_site_packages(),
        )

        def worker():
            items = self._scan_installed_packages(*paths)
            self.installed_signal.emit(items)

        threading.Thread(target=worker, daemon=True).start()

    def _show_installed_packages(self, items):
        self._installed_scan_active = False
        self.refresh_btn.setEnabled(True)
        self.installed_list.clear()
        if items:
            self.installed_list.addItems(items)
        else:
            self.installed_list.addItem("No packages detected.")

    # ─────────────────────────────────────────────────────────────
    # Maya.env support
    # ─────────────────────────────────────────────────────────────
    def _append_to_maya_env(self, path_to_add):
        try:
            maya_env_dir = os.path.join(
                os.path.expanduser("~"),
                "Documents", "maya",
                self.maya_version
            )
            os.makedirs(maya_env_dir, exist_ok=True)

            maya_env_path = os.path.join(maya_env_dir, "Maya.env")

            existing = ""
            if os.path.exists(maya_env_path):
                with open(maya_env_path, "r", encoding="utf-8") as f:
                    existing = f.read()

            line = "PYTHONPATH={}".format(path_to_add)

            if path_to_add not in existing:
                with open(maya_env_path, "a", encoding="utf-8") as f:
                    if existing and not existing.endswith("\n"):
                        f.write("\n")
                    f.write(line + "\n")
                self.log_signal.emit("📝 Added to Maya.env: " + path_to_add)
            else:
                self.log_signal.emit("📝 Maya.env already contains path.")

        except Exception as e:
            self.log_signal.emit("⚠ Maya.env update failed: {}".format(e))

    # ─────────────────────────────────────────────────────────────
    # Check if package exists in a specific path
    # ─────────────────────────────────────────────────────────────
    def _package_exists_in_path(self, package_name, folder):
        """
        Returns True if the package is found inside the given folder.
        Works for both dist-info tracked packages AND raw Autodesk-bundled
        packages that have no dist-info (direct folder/file scan).
        """
        if not folder or not os.path.exists(folder):
            return False

        base      = package_name.strip().split("==")[0]
        pkg_under = base.replace("-", "_")
        pkg_dash  = base.replace("_", "-")

        # Check dist-info / egg-info first (case-insensitive via listdir)
        try:
            entries_lower = {e.lower(): e for e in os.listdir(folder)}
        except OSError:
            return False

        for variant in (pkg_under.lower(), pkg_dash.lower()):
            # exact folder/file match (raw bundled package)
            if variant in entries_lower:
                return True
            if variant + ".py" in entries_lower:
                return True
            # dist-info / egg-info match (prefix search)
            prefix_di = variant + "-"
            for key in entries_lower:
                if key.startswith(prefix_di) and (key.endswith(".dist-info") or key.endswith(".egg-info")):
                    return True

        return False

    # ─────────────────────────────────────────────────────────────
    # Build commands
    # ─────────────────────────────────────────────────────────────
    def _build_cmd(self, action, packages=None):
        packages = packages if packages is not None else self.pkg_input.text().strip().split()
        if not packages:
            return None, None, "No package name entered."

        mayapy = self.mayapy_input.text()
        use_user_flag = self.chk_user.isChecked()
        target = self.target_input.text().strip()

        cmd = [mayapy, "-m", "pip", action] + packages
        install_path = None

        if action == "install":
            if use_user_flag:
                cmd.append("--user")
                install_path = self._get_user_site_packages()
            else:
                if target:
                    is_protected = self._is_protected_path(target)
                    if is_protected and not self.chk_admin.isChecked():
                        return None, None, (
                            "Install path is inside a protected system directory:\n  {}\n\n"
                            "Enable 'Use Administrator' to install there, or choose --user."
                        ).format(target)
                    if not is_protected:
                        os.makedirs(target, exist_ok=True)
                    cmd += ["--target", target]
                    install_path = target

            if self.chk_upgrade.isChecked():
                cmd.append("--upgrade")
            if self.chk_no_deps.isChecked():
                cmd.append("--no-deps")

        elif action == "uninstall":
            cmd.append("-y")

        return cmd, install_path, None

    @staticmethod
    def _powershell_quote(value):
        return "'{}'".format(value.replace("'", "''"))

    def _run_elevated_process(self, cmd):
        """Run mayapy/pip through UAC and return its full pip output to the UI."""
        script_handle, script_path = tempfile.mkstemp(prefix="maya_pip_admin_", suffix=".ps1")
        output_handle, output_path = tempfile.mkstemp(prefix="maya_pip_admin_", suffix=".log")
        os.close(script_handle)
        os.close(output_handle)

        try:
            arguments = ",\n    ".join(
                self._powershell_quote(argument) for argument in cmd[1:]
            )
            elevated_script = (
                "$ErrorActionPreference = 'Continue'\n"
                "$arguments = @(\n    {arguments}\n)\n"
                "& {mayapy} @arguments *>&1 | Out-File -FilePath {output} -Encoding utf8\n"
                "$exitCode = $LASTEXITCODE\n"
                "exit $exitCode\n"
            ).format(
                mayapy=self._powershell_quote(cmd[0]),
                arguments=arguments,
                output=self._powershell_quote(output_path)
            )
            with open(script_path, "w", encoding="utf-8") as script_file:
                script_file.write(elevated_script)

            ps_arguments = "-NoProfile -ExecutionPolicy Bypass -File {}".format(
                subprocess.list2cmdline([script_path])
            )
            launcher = (
                "$ErrorActionPreference = 'Stop'; "
                "$process = Start-Process -FilePath 'powershell.exe' "
                "-ArgumentList {arguments} -Verb RunAs -Wait -PassThru; "
                "exit $process.ExitCode"
            ).format(arguments=self._powershell_quote(ps_arguments))
            result = subprocess.run(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", launcher],
                capture_output=True,
                text=True
            )

            try:
                with open(output_path, "r", encoding="utf-8", errors="replace") as output_file:
                    elevated_output = output_file.read().strip()
                if elevated_output:
                    result.stdout = elevated_output
            except OSError:
                pass
            return result
        finally:
            for temporary_path in (script_path, output_path):
                try:
                    os.remove(temporary_path)
                except OSError:
                    pass

    # ─────────────────────────────────────────────────────────────
    # Remove manually from custom folders
    # ─────────────────────────────────────────────────────────────
    def _remove_package_from_folder(self, package_name, folder):
        if not folder or not os.path.exists(folder):
            return

        pkg_clean = package_name.strip().split("==")[0].replace("-", "_")
        pkg_dash = package_name.strip().split("==")[0].replace("_", "-")

        patterns = [
            os.path.join(folder, pkg_clean),
            os.path.join(folder, pkg_clean + ".py"),
            os.path.join(folder, pkg_clean + "*.pyd"),
            os.path.join(folder, pkg_clean + "*.dll"),
            os.path.join(folder, pkg_clean + "-*.dist-info"),
            os.path.join(folder, pkg_clean + "-*.egg-info"),
            os.path.join(folder, pkg_dash + "-*.dist-info"),
            os.path.join(folder, pkg_dash + "-*.egg-info"),
        ]

        removed_any = False

        for pattern in patterns:
            for path in glob.glob(pattern):
                try:
                    if os.path.isdir(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                    self.log_signal.emit("🗑 Removed: {}".format(path))
                    removed_any = True
                except Exception as e:
                    self.log_signal.emit("⚠ Failed to remove {} ({})".format(path, e))

        if not removed_any:
            self.log_signal.emit("⚠ No matching files found in: {}".format(folder))

    # ─────────────────────────────────────────────────────────────
    # Run pip
    # ─────────────────────────────────────────────────────────────
    def _run_pip(self, action):
        packages = self.pkg_input.text().strip().split()
        if not packages:
            self.log_signal.emit("[ERROR] No package name entered.")
            self.busy_signal.emit(False)
            return

        maya_system_site = self._get_maya_system_site_packages()
        maya_site        = self._get_maya_user_site_packages()
        user_site        = self._get_user_site_packages()
        target           = self.target_input.text().strip()

        # ── INSTALL ──────────────────────────────────────────────
        if action == "install":
            skipped  = []
            to_install = []

            if not self.chk_upgrade.isChecked():
                for pkg in packages:
                    if self._package_exists_in_path(pkg, maya_system_site):
                        skipped.append((pkg, maya_system_site, "[Maya Install]"))
                    elif self._package_exists_in_path(pkg, maya_site):
                        skipped.append((pkg, maya_site, "[Maya Site]"))
                    elif self._package_exists_in_path(pkg, target):
                        skipped.append((pkg, target, "[Custom Target]"))
                    elif self._package_exists_in_path(pkg, user_site):
                        skipped.append((pkg, user_site, "[User Site]"))
                    else:
                        to_install.append(pkg)
            else:
                to_install = packages

            for pkg, path, label in skipped:
                self.log_signal.emit(
                    "⏭ Skipped '{}' — already found in {} ({})\n"
                    "   Use --upgrade to force reinstall.".format(pkg, label, path)
                )

            if not to_install:
                self.log_signal.emit("\n✅ All packages already installed. Nothing to do.")
                self.refresh_signal.emit()
                self.busy_signal.emit(False)
                return

            cmd, install_path, err = self._build_cmd("install", to_install)

            if not cmd:
                self.log_signal.emit("[ERROR] " + err)
                self.busy_signal.emit(False)
                return

            self.log_signal.emit(">> Running: " + " ".join(cmd) + "\n")
            requires_admin = bool(install_path and self._is_protected_path(install_path))
            if requires_admin and os.name == "nt":
                self.log_signal.emit(
                    "🔐 Requesting Administrator permission for Maya Install. "
                    "Approve the Windows UAC prompt to continue."
                )
                result = self._run_elevated_process(cmd)
            else:
                result = subprocess.run(cmd, capture_output=True, text=True)

            if result.stdout:
                self.log_signal.emit(result.stdout)
            if result.stderr:
                real_errors = [
                    l for l in result.stderr.strip().splitlines()
                    if not l.startswith("WARNING: You are using pip version")
                    and not l.startswith("You should consider upgrading")
                ]
                if real_errors:
                    self.log_signal.emit("[STDERR]\n" + "\n".join(real_errors))

            if result.returncode == 0:
                self.log_signal.emit("\n✅ Install completed successfully!")
                if requires_admin:
                    self.log_signal.emit("🔐 Installed into the Maya system site-packages folder.")
                if install_path:
                    if install_path not in sys.path:
                        sys.path.insert(0, install_path)
                        self.log_signal.emit("📂 Added to sys.path: " + install_path)
                    else:
                        self.log_signal.emit("📂 Already in sys.path: " + install_path)
                    self._append_to_maya_env(install_path)
            else:
                self.log_signal.emit("\n❌ Install failed (exit code {}).".format(result.returncode))

        # ── UNINSTALL ─────────────────────────────────────────────
        elif action == "uninstall":
            for pkg in packages:
                # Block if found in admin-protected Maya Install path
                if self._package_exists_in_path(pkg, maya_system_site):
                    self.log_signal.emit(
                        "🚫 Cannot uninstall '{}' — it is installed in the Maya system folder:\n"
                        "   {}\n"
                        "   This path requires Administrator rights to modify.\n"
                        "   Run Maya (or your file manager) as Administrator if you really need to remove it.".format(
                            pkg, maya_system_site
                        )
                    )
                    continue  # skip pip uninstall for this package

                # Only remove from writable user-controlled paths
                removed_any = False
                for folder in [maya_site, target, user_site]:
                    if self._package_exists_in_path(pkg, folder):
                        self._remove_package_from_folder(pkg, folder)
                        removed_any = True

                if not removed_any:
                    self.log_signal.emit("⚠ '{}' not found in any writable path.".format(pkg))

        self.refresh_signal.emit()
        self.busy_signal.emit(False)

    # ─────────────────────────────────────────────────────────────
    # Threading
    # ─────────────────────────────────────────────────────────────
    def _start_install(self):
        self._set_busy(True)
        t = threading.Thread(target=self._run_pip, args=("install",), daemon=True)
        t.start()

    def _start_uninstall(self):
        self._set_busy(True)
        t = threading.Thread(target=self._run_pip, args=("uninstall",), daemon=True)
        t.start()


# ─────────────────────────────────────────────────────────────
# Launch
# ─────────────────────────────────────────────────────────────
def show_pip_installer():
    global _pip_ui
    try:
        _pip_ui.close()
        _pip_ui.deleteLater()
    except:
        pass
    _pip_ui = MayaPipInstallerUI()
    _pip_ui.show()


show_pip_installer()
