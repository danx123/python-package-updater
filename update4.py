import sys
import os
import subprocess
import ast
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
    QMessageBox,
    QHeaderView,
    QTableWidget,
    QTableWidgetItem,
    QHBoxLayout,
    QProgressBar,
    QTextEdit,
    QLabel,
    QFileDialog,
    QMenu,
    QSplitter,
)
from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot, QByteArray
from PySide6.QtGui import QIcon, QPixmap

# ======================================================================
# 0. QSS STYLESHEET (UNTUK TAMPILAN MODERN)
# ======================================================================
MODERN_QSS = """
QWidget {
    background-color: #2e3440;
    color: #d8dee9;
    font-family: 'Segoe UI', 'Roboto', 'Arial', sans-serif;
    font-size: 10pt;
}
QPushButton {
    background-color: #4c566a;
    color: #eceff4;
    border: 1px solid #434c5e;
    padding: 8px 12px;
    border-radius: 4px;
    text-align: left;
}
QPushButton:hover {
    background-color: #5e81ac;
}
QPushButton:disabled {
    background-color: #3b4252;
    color: #4c566a;
}
QTableWidget {
    gridline-color: #434c5e;
    background-color: #3b4252;
    selection-background-color: #88c0d0;
    selection-color: #2e3440;
}
QHeaderView::section {
    background-color: #434c5e;
    color: #eceff4;
    padding: 5px;
    border: 1px solid #2e3440;
}
QTextEdit {
    background-color: #262b35;
    border: 1px solid #434c5e;
    border-radius: 4px;
    color: #d8dee9;
    font-family: 'Consolas', 'Courier New', monospace;
}
"""

# ======================================================================
# DEFINISI IKON SVG (XML STRING)
# ======================================================================
SVG_WRAPPER = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" '
    'viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
    'stroke-linecap="round" stroke-linejoin="round" class="feather feather-{}">{}</svg>'
)

SVG_ICONS = {
    "check_all": SVG_WRAPPER.format(
        "refresh-cw",
        '<polyline points="23 4 23 10 17 10"></polyline>'
        '<path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path>',
    ),
    "scan_file": SVG_WRAPPER.format(
        "file-text",
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="16" y1="13" x2="8" y2="13"></line>'
        '<line x1="16" y1="17" x2="8" y2="17"></line>'
        '<polyline points="10 9 8 9"></polyline>',
    ),
    "update": SVG_WRAPPER.format(
        "upload-cloud",
        '<polyline points="16 16 12 12 8 16"></polyline>'
        '<line x1="12" y1="12" x2="12" y2="21"></line>'
        '<path d="M20.39 18.39A5 5 0 0 0 18 9h-1.26A8 8 0 1 0 3 16.3"></path>'
        '<polyline points="16 16 12 12 8 16"></polyline>',
    ),
    "uninstall": SVG_WRAPPER.format(
        "trash-2",
        '<polyline points="3 6 5 6 21 6"></polyline>'
        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path>'
        '<line x1="10" y1="11" x2="10" y2="17"></line>'
        '<line x1="14" y1="11" x2="14" y2="17"></line>',
    ),
    "create_reqs": SVG_WRAPPER.format(
        "file-plus",
        '<path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>'
        '<polyline points="14 2 14 8 20 8"></polyline>'
        '<line x1="12" y1="18" x2="12" y2="12"></line>'
        '<line x1="9" y1="15" x2="15" y2="15"></line>',
    ),
    "install_reqs": SVG_WRAPPER.format(
        "download",
        '<path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path>'
        '<polyline points="7 10 12 15 17 10"></polyline>'
        '<line x1="12" y1="15" x2="12" y2="3"></line>',
    ),
    "clear_cache": SVG_WRAPPER.format(
        "zap",
        '<polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"></polygon>',
    ),
}


# ======================================================================
# 1. KELAS WORKER (TETAP SAMA)
# ======================================================================
class Worker(QObject):
    finished = Signal(str, str)
    error = Signal(str, str)
    progress_log = Signal(str, str)

    @Slot(str, list)
    def run_command(self, identifier, command):
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )

            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line_stripped = line.strip()
                    self.progress_log.emit(identifier, line_stripped)
                    output_lines.append(line_stripped)
            
            process.wait()

            full_output = "\n".join(output_lines)

            if process.returncode != 0:
                self.error.emit(identifier, f"Command failed with exit code {process.returncode}.\nSee logs for details.")
            else:
                self.finished.emit(identifier, full_output)

        except FileNotFoundError:
            error_msg = f"The command '{command[0]}' was not found. Please ensure Python is installed and accessible via the system's PATH."
            self.error.emit(identifier, error_msg)
        except Exception as e:
            self.error.emit(identifier, f"An unexpected error occurred:\n{str(e)}")


# ======================================================================
# 2. JENDELA UTAMA APLIKASI
# ======================================================================
class PythonPackageUpdater(QMainWindow):
    start_work = Signal(str, list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Package Updater by Danx (v4.0)")
        self.setGeometry(100, 100, 1100, 620)
        icon_path = "icon.ico"
        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet(MODERN_QSS)

        self.current_filter = None

        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.handle_worker_finish)
        self.worker.error.connect(self.handle_worker_error)
        self.worker.progress_log.connect(self.append_log)
        self.start_work.connect(self.worker.run_command)

        self.thread.start()

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_h_layout = QHBoxLayout(self.central_widget)

        # --- SPLITTER: kiri (konten utama) | kanan (log sidebar) ---
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_h_layout.addWidget(self.splitter)

        # === Panel kiri ===
        self.left_panel = QWidget()
        self.layout = QVBoxLayout(self.left_panel)
        self.splitter.addWidget(self.left_panel)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Package", "Current Version", "Latest Version", "Type"]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.itemSelectionChanged.connect(self.update_button_states)
        
        # [MODIFIED] Mengaktifkan Context Menu
        self.table_widget.setContextMenuPolicy(Qt.CustomContextMenu)
        self.table_widget.customContextMenuRequested.connect(self.show_context_menu)
        
        self.layout.addWidget(self.table_widget)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        
        self.check_layout = QHBoxLayout()
        self.check_all_button = QPushButton("Check All Outdated")
        self.check_all_button.setIcon(self.create_svg_icon(SVG_ICONS["check_all"]))
        self.check_all_button.clicked.connect(self.check_outdated_packages)
        self.check_layout.addWidget(self.check_all_button)
        
        self.scan_file_button = QPushButton("Scan File & Check...")
        self.scan_file_button.setIcon(self.create_svg_icon(SVG_ICONS["scan_file"]))
        self.scan_file_button.clicked.connect(self.scan_file_and_check)
        self.check_layout.addWidget(self.scan_file_button)
        
        self.layout.addLayout(self.check_layout)
        
        self.action_layout = QHBoxLayout()
        
        self.update_button = QPushButton("Update All")
        self.update_button.setIcon(self.create_svg_icon(SVG_ICONS["update"]))
        self.update_button.clicked.connect(self.update_all_packages)
        self.action_layout.addWidget(self.update_button)

        # [ADDED] Tombol Update Selected
        self.update_selected_button = QPushButton("Update Selected")
        self.update_selected_button.setIcon(self.create_svg_icon(SVG_ICONS["update"]))
        self.update_selected_button.clicked.connect(self.update_selected_packages)
        self.action_layout.addWidget(self.update_selected_button)
        
        self.uninstall_button = QPushButton("Uninstall Selected")
        self.uninstall_button.setIcon(self.create_svg_icon(SVG_ICONS["uninstall"]))
        self.uninstall_button.clicked.connect(self.uninstall_selected_packages)
        self.action_layout.addWidget(self.uninstall_button)
        
        self.layout.addLayout(self.action_layout)
        
        self.reqs_layout = QHBoxLayout()
        self.create_reqs_button = QPushButton("Create requirements.txt")
        self.create_reqs_button.setIcon(self.create_svg_icon(SVG_ICONS["create_reqs"]))
        self.create_reqs_button.clicked.connect(self.create_requirements)
        self.reqs_layout.addWidget(self.create_reqs_button)
        
        self.install_reqs_button = QPushButton("Install from requirements.txt")
        self.install_reqs_button.setIcon(self.create_svg_icon(SVG_ICONS["install_reqs"]))
        self.install_reqs_button.clicked.connect(self.install_requirements)
        self.reqs_layout.addWidget(self.install_reqs_button)

        # [ADDED] Tombol Clear pip Cache
        self.clear_cache_button = QPushButton("Clear pip Cache")
        self.clear_cache_button.setIcon(self.create_svg_icon(SVG_ICONS["clear_cache"]))
        self.clear_cache_button.clicked.connect(self.clear_pip_cache)
        self.reqs_layout.addWidget(self.clear_cache_button)
        
        self.layout.addLayout(self.reqs_layout)

        # === Panel kanan (Log Sidebar) ===
        self.right_panel = QWidget()
        self.right_layout = QVBoxLayout(self.right_panel)
        self.right_layout.setContentsMargins(4, 0, 0, 0)
        self.splitter.addWidget(self.right_panel)

        self.log_header_layout = QHBoxLayout()
        self.log_label = QLabel("📋 Logs")
        self.log_label.setStyleSheet("font-weight: bold; color: #88c0d0;")
        self.log_header_layout.addWidget(self.log_label)

        self.clear_log_button = QPushButton("Clear")
        self.clear_log_button.setFixedWidth(55)
        self.clear_log_button.setStyleSheet(
            "QPushButton { padding: 2px 6px; font-size: 8pt; background-color: #3b4252; }"
            "QPushButton:hover { background-color: #bf616a; }"
        )
        self.clear_log_button.clicked.connect(self.log_output.clear if hasattr(self, 'log_output') else lambda: None)
        self.log_header_layout.addWidget(self.clear_log_button)
        self.right_layout.addLayout(self.log_header_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.right_layout.addWidget(self.log_output)

        # Hubungkan tombol Clear Log setelah log_output dibuat
        self.clear_log_button.clicked.disconnect()
        self.clear_log_button.clicked.connect(self.log_output.clear)

        # Atur proporsi splitter: 65% kiri, 35% kanan
        self.splitter.setSizes([700, 380])
        self.splitter.setCollapsible(0, False)
        self.splitter.setCollapsible(1, False)
        
        self.update_button_states()

    def create_svg_icon(self, svg_data):
        ba = QByteArray(svg_data.encode("utf-8"))
        pixmap = QPixmap()
        pixmap.loadFromData(ba, "SVG")
        return QIcon(pixmap)

    def update_button_states(self, is_working=False):
        self.progress_bar.setVisible(is_working)
        
        if is_working:
            self.check_all_button.setEnabled(False)
            self.scan_file_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.update_selected_button.setEnabled(False) # [MODIFIED]
            self.uninstall_button.setEnabled(False)
            self.create_reqs_button.setEnabled(False)
            self.install_reqs_button.setEnabled(False)
            self.clear_cache_button.setEnabled(False)
        else:
            has_outdated = self.table_widget.rowCount() > 0
            has_selection = len(self.table_widget.selectedItems()) > 0
            
            self.check_all_button.setEnabled(True)
            self.scan_file_button.setEnabled(True)
            self.create_reqs_button.setEnabled(True)
            self.install_reqs_button.setEnabled(True)
            self.clear_cache_button.setEnabled(True)
            
            self.update_button.setEnabled(has_outdated)
            self.update_selected_button.setEnabled(has_selection) # [MODIFIED]
            self.uninstall_button.setEnabled(has_selection)

    def prepare_for_work(self):
        self.log_output.clear()
        self.update_button_states(is_working=True)

    def get_python_executable(self):
        if getattr(sys, 'frozen', False):
            return self._find_python_executable()
        return sys.executable

    def _find_python_executable(self):
        """
        Cari Python yang valid saat berjalan sebagai .exe (PyInstaller).
        Windows 11 25H2 memperketat App Execution Aliases sehingga 'python'
        di PATH bisa mengarah ke stub Microsoft Store (exit code 9009).
        Fungsi ini mencari Python yang benar-benar bisa dieksekusi.
        """
        import shutil

        # 1. Coba kandidat nama python secara eksplisit via shutil.which
        #    (shutil.which me-resolve path penuh dan memvalidasi bahwa file ada)
        candidates = ["python3", "python", "py"]
        for name in candidates:
            path = shutil.which(name)
            if path:
                # Validasi: pastikan bukan stub Microsoft Store
                # Stub biasanya ada di %LOCALAPPDATA%\Microsoft\WindowsApps
                lower_path = path.lower().replace("\\", "/")
                if "windowsapps" not in lower_path and "microsoft store" not in lower_path:
                    try:
                        result = subprocess.run(
                            [path, "--version"],
                            capture_output=True, text=True, timeout=5,
                            creationflags=subprocess.CREATE_NO_WINDOW
                        )
                        if result.returncode == 0:
                            return path
                    except Exception:
                        continue

        # 2. Cek lokasi instalasi Python yang umum di Windows
        common_paths = []
        localappdata = os.environ.get("LOCALAPPDATA", "")
        appdata = os.environ.get("APPDATA", "")
        userprofile = os.environ.get("USERPROFILE", "")

        # Python dari installer resmi
        for drive in ["C:", "D:"]:
            for ver in ["313", "312", "311", "310", "39", "38"]:
                common_paths.append(rf"{drive}\Python{ver}\python.exe")
                common_paths.append(rf"{drive}\Program Files\Python{ver}\python.exe")
                common_paths.append(rf"{drive}\Program Files (x86)\Python{ver}\python.exe")

        # Python dari Microsoft Store (path yang valid, bukan stub)
        if localappdata:
            packages_dir = os.path.join(localappdata, "Programs", "Python")
            if os.path.isdir(packages_dir):
                for folder in sorted(os.listdir(packages_dir), reverse=True):
                    candidate = os.path.join(packages_dir, folder, "python.exe")
                    common_paths.insert(0, candidate)

        # Python dari Conda / Miniconda / Anaconda
        for base in [userprofile, "C:", "D:"]:
            for conda in ["anaconda3", "miniconda3", "conda"]:
                common_paths.append(os.path.join(base, conda, "python.exe"))

        for path in common_paths:
            if os.path.isfile(path):
                try:
                    result = subprocess.run(
                        [path, "--version"],
                        capture_output=True, text=True, timeout=5,
                        creationflags=subprocess.CREATE_NO_WINDOW
                    )
                    if result.returncode == 0:
                        return path
                except Exception:
                    continue

        # 3. Fallback terakhir — tampilkan error yang informatif
        QMessageBox.critical(
            self, "Python Not Found",
            "Could not find a valid Python installation on this system.\n\n"
            "Please ensure Python is installed from python.org and added to PATH.\n\n"
            "If you installed Python from the Microsoft Store, make sure App Execution\n"
            "Aliases are enabled in:\n"
            "Settings → Apps → Advanced app settings → App execution aliases"
        )
        return "python"

    def get_imports_from_file(self, file_path):
        imports = set()
        std_lib = set(sys.builtin_module_names) | {'os', 'sys', 'datetime', 'json', 're', 'math', 'collections'}
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                tree = ast.parse(content, filename=file_path)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        top_level_module = alias.name.split('.')[0]
                        if top_level_module not in std_lib:
                            imports.add(top_level_module.lower())
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        top_level_module = node.module.split('.')[0]
                        if top_level_module not in std_lib:
                            imports.add(top_level_module.lower())
        except Exception as e:
            QMessageBox.critical(self, "Parse Error", f"Could not parse file: {e}")
            return None
        self.log_output.append(f"--- Found {len(imports)} non-standard modules: {', '.join(imports)} ---")
        return imports

    # ======================================================================
    # 3. METODE YANG MEMICU PEKERJAAN
    # ======================================================================
    
    # [ADDED] Method untuk Context Menu
    def show_context_menu(self, pos):
        """Menampilkan Context Menu pada Klik Kanan."""
        menu = QMenu(self)
        
        has_selection = len(self.table_widget.selectedItems()) > 0
        if not has_selection:
            return

        # Add Action: Update Selected
        update_action = menu.addAction(self.create_svg_icon(SVG_ICONS["update"]), "Update Selected")
        update_action.triggered.connect(self.update_selected_packages)
        
        # Add Action: Uninstall Selected
        uninstall_action = menu.addAction(self.create_svg_icon(SVG_ICONS["uninstall"]), "Uninstall Selected")
        uninstall_action.triggered.connect(self.uninstall_selected_packages)
        
        menu.exec(self.table_widget.mapToGlobal(pos))

    def check_outdated_packages(self, filter_modules=None):
        self.check_all_button.setText("Checking...")
        self.scan_file_button.setText("Scanning...")
        self.prepare_for_work()
        self.current_filter = filter_modules
        python_exe = self.get_python_executable()
        command = [python_exe, "-m", "pip", "list", "--outdated"]
        self.start_work.emit("check", command)

    def scan_file_and_check(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Python File to Scan", "", "Python Files (*.py)"
        )
        if file_path:
            self.log_output.append(f"--- Scanning file: {file_path} ---")
            imported_modules = self.get_imports_from_file(file_path)
            if imported_modules is not None:
                self.check_outdated_packages(filter_modules=imported_modules)
            else:
                self.log_output.append("--- File scan cancelled or failed ---")

    def update_all_packages(self):
        packages = [self.table_widget.item(row, 0).text() for row in range(self.table_widget.rowCount())]
        if not packages:
            QMessageBox.warning(self, "Warning", "No packages to update.")
            return

        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to update {len(packages)} packages?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.update_button.setText("Updating...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "install", "--upgrade"] + packages
            self.start_work.emit("update", command)
    
    # [ADDED] Method Update Selected
    def update_selected_packages(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return

        packages = [self.table_widget.item(row.row(), 0).text() for row in selected_rows]
        
        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to update these packages:\n\n- {'\n- '.join(packages)}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.update_selected_button.setText("Updating...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "install", "--upgrade"] + packages
            self.start_work.emit("update", command)

    def uninstall_selected_packages(self):
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return

        packages = [self.table_widget.item(row.row(), 0).text() for row in selected_rows]
        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to uninstall:\n\n- {'\n- '.join(packages)}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.uninstall_button.setText("Uninstalling...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "uninstall", "-y"] + packages
            self.start_work.emit("uninstall", command)

    def create_requirements(self):
        reply = QMessageBox.question(self, "Confirmation", "This will run 'pip freeze' and overwrite any existing 'requirements.txt' with package names only.\n\nContinue?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.create_reqs_button.setText("Creating...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "freeze"]
            self.start_work.emit("freeze_for_reqs", command)

    def install_requirements(self):
        req_file = "requirements.txt"
        if not os.path.exists(req_file):
            QMessageBox.warning(self, "File Not Found", f"The file '{req_file}' was not found in the same folder.")
            return
        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to install all packages from '{req_file}'?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.install_reqs_button.setText("Installing...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "install", "-r", req_file]
            self.start_work.emit("install_reqs", command)

    # [ADDED] Method Clear pip Cache
    def clear_pip_cache(self):
        reply = QMessageBox.question(
            self, "Confirmation",
            "This will run 'pip cache purge' to delete all cached packages.\n\nContinue?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            self.clear_cache_button.setText("Clearing...")
            self.prepare_for_work()
            python_exe = self.get_python_executable()
            command = [python_exe, "-m", "pip", "cache", "purge"]
            self.start_work.emit("clear_cache", command)

    # ======================================================================
    # 4. SLOT UNTUK MENANGANI HASIL DARI WORKER
    # ======================================================================
    @Slot(str, str)
    def append_log(self, identifier, log_line):
        if log_line:
            self.log_output.append(log_line)

    @Slot(str, str)
    def handle_worker_finish(self, identifier, output):
        if identifier == "check":
            self.table_widget.setRowCount(0)
            lines = output.strip().split("\n")
            header_index = -1
            for i, line in enumerate(lines):
                if line.startswith("---"):
                    header_index = i
                    break
            
            table_data = lines[header_index + 1:] if header_index != -1 else []
            
            if self.current_filter:
                self.log_output.append(f"--- Filtering {len(table_data)} packages based on scan results... ---")
                filtered_data = []
                for line in table_data:
                    parts = line.split()
                    if parts:
                        pkg_name = parts[0].lower() 
                        pkg_name_norm = pkg_name.replace('-', '_') 
                        
                        if pkg_name in self.current_filter or pkg_name_norm in self.current_filter:
                            filtered_data.append(line)
                        elif 'beautifulsoup4' in pkg_name and 'bs4' in self.current_filter:
                             filtered_data.append(line)
                        elif 'pyyaml' in pkg_name and 'yaml' in self.current_filter:
                             filtered_data.append(line)
                             
                table_data = filtered_data
                self.log_output.append(f"--- Displaying {len(table_data)} matching packages ---")
                
            self.current_filter = None

            if not table_data:
                QMessageBox.information(self, "Information", "All packages are up to date! 👍\n(Or no packages matched the scan filter)")
            else:
                self.table_widget.setRowCount(len(table_data))
                for i, line in enumerate(table_data):
                    parts = line.split()
                    if len(parts) >= 4:
                        name, current, latest, type = parts[:4]
                        self.table_widget.setItem(i, 0, QTableWidgetItem(name))
                        self.table_widget.setItem(i, 1, QTableWidgetItem(current))
                        self.table_widget.setItem(i, 2, QTableWidgetItem(latest))
                        self.table_widget.setItem(i, 3, QTableWidgetItem(type))
        
        elif identifier == "update":
            self.log_output.append("\n--- UPDATE COMPLETE ---")
            # Kita panggil check lagi untuk refresh list
            QMessageBox.information(self, "Success", "Package update process finished! 🎉")
            self.check_outdated_packages() 
            return 
            
        elif identifier == "uninstall":
            self.log_output.append("\n--- UNINSTALL COMPLETE ---")
            QMessageBox.information(self, "Success", "Selected packages have been uninstalled. ✅")
            self.check_outdated_packages() 
            return
            
        elif identifier == "freeze_for_reqs":
            try:
                lines = output.strip().split("\n")
                package_names = [line.split('==')[0] for line in lines if '==' in line]
                
                with open('requirements.txt', 'w', encoding='utf-8') as f:
                    f.write("\n".join(package_names))
                    f.write("\n")
                    
                self.log_output.append(f"\n--- requirements.txt CREATED/OVERWRITTEN ({len(package_names)} packages) ---")
                QMessageBox.information(self, "Success", f"requirements.txt (names only) successfully created with {len(package_names)} packages. ✅")
            except Exception as e:
                self.handle_worker_error("create_reqs", f"Failed to write requirements.txt file: {e}")
            
        elif identifier == "install_reqs":
            self.log_output.append("\n--- INSTALLATION FROM REQUIREMENTS.TXT COMPLETE ---")
            QMessageBox.information(self, "Success", "Packages from requirements.txt have been installed! ✅")
            self.check_outdated_packages() 
            return

        elif identifier == "clear_cache":
            self.log_output.append("\n--- PIP CACHE PURGE COMPLETE ---")
            QMessageBox.information(self, "Success", "pip cache has been cleared successfully! 🗑️")

        self.reset_all_button_text()
        self.update_button_states(is_working=False)

    @Slot(str, str)
    def handle_worker_error(self, identifier, error_message):
        self.log_output.append(f"\n--- ERROR ENCOUNTERED ---\n{error_message}")
        QMessageBox.critical(self, "Error", f"An error occurred during '{identifier}' operation:\n{error_message}")
        
        self.reset_all_button_text()
        self.update_button_states(is_working=False)
        
    def reset_all_button_text(self):
        self.check_all_button.setText("Check All Outdated")
        self.scan_file_button.setText("Scan File & Check...")
        self.update_button.setText("Update All")
        self.update_selected_button.setText("Update Selected") # [ADDED]
        self.uninstall_button.setText("Uninstall Selected")
        self.create_reqs_button.setText("Create requirements.txt")
        self.install_reqs_button.setText("Install from requirements.txt")
        self.clear_cache_button.setText("Clear pip Cache")
        
    def closeEvent(self, event):
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonPackageUpdater()
    window.show()
    sys.exit(app.exec())
