import sys
import os
import subprocess
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
    QTextEdit,  # Ditambahkan
    QLabel,     # Ditambahkan
)
from PySide6.QtCore import Qt, QThread, QObject, Signal, Slot
from PySide6.QtGui import QIcon

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

QMainWindow {
    border-radius: 8px;
}

QPushButton {
    background-color: #4c566a;
    color: #eceff4;
    border: 1px solid #434c5e;
    padding: 8px 16px;
    border-radius: 4px;
}

QPushButton:hover {
    background-color: #5e81ac;
}

QPushButton:pressed {
    background-color: #81a1c1;
}

QPushButton:disabled {
    background-color: #3b4252;
    color: #4c566a;
}

QTableWidget {
    background-color: #3b4252;
    border: 1px solid #434c5e;
    gridline-color: #434c5e;
    border-radius: 4px;
}

QTableWidget::item {
    padding: 5px;
}

QHeaderView::section {
    background-color: #434c5e;
    color: #eceff4;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #2e3440;
}

QTableWidget::item:selected {
    background-color: #5e81ac;
    color: #eceff4;
}

QMessageBox {
    background-color: #3b4252;
}

QProgressBar {
    border: 1px solid #434c5e;
    border-radius: 4px;
    text-align: center;
    color: #d8dee9;
}

QProgressBar::chunk {
    background-color: #88c0d0;
    border-radius: 3px;
    margin: 1px;
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
# 1. KELAS WORKER (UNTUK PEKERJAAN DI BACKGROUND)
# ======================================================================
class Worker(QObject):
    """
    Worker object that runs long-running tasks in a separate thread.
    Inherits from QObject to use the signal/slot mechanism.
    """
    finished = Signal(str, str)
    error = Signal(str, str)
    progress_log = Signal(str, str) # Sinyal baru untuk logging

    @Slot(str, list)
    def run_command(self, identifier, command):
        """
        Runs a command and emits signals for logs in real-time and a final signal on completion.
        """
        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Gabungkan stderr ke stdout untuk menangkap semua output
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0,
            )

            output_lines = []
            if process.stdout:
                for line in iter(process.stdout.readline, ''):
                    line_stripped = line.strip()
                    self.progress_log.emit(identifier, line_stripped) # Kirim setiap baris log
                    output_lines.append(line_stripped)
            
            process.wait() # Tunggu proses selesai

            full_output = "\n".join(output_lines)

            if process.returncode != 0:
                self.error.emit(identifier, f"Command failed with exit code {process.returncode}.\nSee logs for details.")
            else:
                self.finished.emit(identifier, full_output)

        except FileNotFoundError:
            self.error.emit(identifier, "The 'pip' command was not found. Please ensure Python and pip are installed correctly.")
        except Exception as e:
            self.error.emit(identifier, f"An unexpected error occurred:\n{str(e)}")


# ======================================================================
# 2. JENDELA UTAMA APLIKASI
# ======================================================================
class PythonPackageUpdater(QMainWindow):
    start_work = Signal(str, list)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Python Package Updater by Danx")
        self.setGeometry(100, 100, 800, 700) # Tinggi jendela ditambah
        icon_path = "icon.ico"
        if hasattr(sys, "_MEIPASS"):
            icon_path = os.path.join(sys._MEIPASS, icon_path)
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))
        self.setStyleSheet(MODERN_QSS)

        # --- Pengaturan Thread ---
        self.thread = QThread()
        self.worker = Worker()
        self.worker.moveToThread(self.thread)

        self.worker.finished.connect(self.handle_worker_finish)
        self.worker.error.connect(self.handle_worker_error)
        self.worker.progress_log.connect(self.append_log) # Hubungkan sinyal log
        self.start_work.connect(self.worker.run_command)

        self.thread.start()

        # --- UI Setup ---
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(4)
        self.table_widget.setHorizontalHeaderLabels(
            ["Package", "Current Version", "Latest Version", "Type"]
        )
        self.table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_widget.setSelectionBehavior(QTableWidget.SelectRows)
        self.table_widget.itemSelectionChanged.connect(self.update_button_states)
        self.layout.addWidget(self.table_widget)

        # --- Area Log (Baru) ---
        self.log_label = QLabel("Logs:")
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setFixedHeight(150) # Batasi tinggi awal
        self.layout.addWidget(self.log_label)
        self.layout.addWidget(self.log_output)
        self.log_label.setVisible(False)
        self.log_output.setVisible(False)
        
        # --- Progress Bar ---
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)
        
        self.check_button = QPushButton("Check for Updates")
        self.check_button.clicked.connect(self.check_outdated_packages)
        self.layout.addWidget(self.check_button)
        
        self.button_layout = QHBoxLayout()
        self.update_button = QPushButton("Update All")
        self.update_button.clicked.connect(self.update_all_packages)
        self.button_layout.addWidget(self.update_button)
        
        self.uninstall_button = QPushButton("Uninstall Selected")
        self.uninstall_button.clicked.connect(self.uninstall_selected_packages)
        self.button_layout.addWidget(self.uninstall_button)
        
        self.layout.addLayout(self.button_layout)
        
        self.update_button_states()

    def update_button_states(self, is_working=False):
        """Enables or disables buttons and manages progress bar visibility."""
        self.progress_bar.setVisible(is_working)
        
        if is_working:
            self.check_button.setEnabled(False)
            self.update_button.setEnabled(False)
            self.uninstall_button.setEnabled(False)
        else:
            has_outdated = self.table_widget.rowCount() > 0
            has_selection = len(self.table_widget.selectedItems()) > 0
            self.check_button.setEnabled(True)
            self.update_button.setEnabled(has_outdated)
            self.uninstall_button.setEnabled(has_selection)

    def prepare_for_work(self):
        """Membersihkan dan menampilkan area log sebelum memulai pekerjaan."""
        self.log_output.clear()
        self.log_label.setVisible(True)
        self.log_output.setVisible(True)
        self.update_button_states(is_working=True)

    # ======================================================================
    # 3. METODE YANG MEMICU PEKERJAAN
    # ======================================================================
    def check_outdated_packages(self):
        """Emits a signal to start checking for outdated packages."""
        self.check_button.setText("Checking...")
        self.prepare_for_work()
        command = [sys.executable, "-m", "pip", "list", "--outdated"]
        self.start_work.emit("check", command)

    def update_all_packages(self):
        """Emits a signal to update all outdated packages."""
        packages = [self.table_widget.item(row, 0).text() for row in range(self.table_widget.rowCount())]
        if not packages:
            QMessageBox.warning(self, "Warning", "There are no packages to update.")
            return

        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to update {len(packages)} packages?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.update_button.setText("Updating...")
            self.prepare_for_work()
            command = [sys.executable, "-m", "pip", "install", "--upgrade"] + packages
            self.start_work.emit("update", command)
            
    def uninstall_selected_packages(self):
        """Emits a signal to uninstall selected packages."""
        selected_rows = self.table_widget.selectionModel().selectedRows()
        if not selected_rows: return

        packages = [self.table_widget.item(row.row(), 0).text() for row in selected_rows]
        reply = QMessageBox.question(self, "Confirmation", f"Are you sure you want to uninstall:\n\n- {'\n- '.join(packages)}", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply == QMessageBox.Yes:
            self.uninstall_button.setText("Uninstalling...")
            self.prepare_for_work()
            command = [sys.executable, "-m", "pip", "uninstall", "-y"] + packages
            self.start_work.emit("uninstall", command)

    # ======================================================================
    # 4. SLOT UNTUK MENANGANI HASIL DARI WORKER
    # ======================================================================
    @Slot(str, str)
    def append_log(self, identifier, log_line):
        """Menambahkan baris log ke area teks log."""
        if log_line: # Hanya tambahkan jika baris tidak kosong
            self.log_output.append(log_line)

    @Slot(str, str)
    def handle_worker_finish(self, identifier, output):
        """Handles the 'finished' signal from the worker."""
        if identifier == "check":
            self.table_widget.setRowCount(0)
            # Parsing outputnya sekarang berdasarkan list yang sudah dipisah per baris
            lines = output.strip().split("\n")
            # Mencari baris pemisah '---' untuk menemukan data tabel yang sebenarnya
            header_index = -1
            for i, line in enumerate(lines):
                if line.startswith("---"):
                    header_index = i
                    break
            
            table_data = lines[header_index + 1:] if header_index != -1 else []

            if not table_data:
                QMessageBox.information(self, "Information", "All packages are up to date! 👍")
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
            QMessageBox.information(self, "Success", "All packages have been updated successfully! 🎉")
            self.check_outdated_packages() 
            return 
            
        elif identifier == "uninstall":
            self.log_output.append("\n--- UNINSTALL COMPLETE ---")
            QMessageBox.information(self, "Success", "Selected packages have been uninstalled. ✅")
            self.check_outdated_packages() 
            return 

        # Reset tombol dan sembunyikan progress bar
        self.check_button.setText("Check for Updates")
        self.update_button.setText("Update All")
        self.uninstall_button.setText("Uninstall Selected")
        self.update_button_states(is_working=False)

    @Slot(str, str)
    def handle_worker_error(self, identifier, error_message):
        """Handles the 'error' signal from the worker."""
        self.log_output.append(f"\n--- ERROR ENCOUNTERED ---\n{error_message}")
        QMessageBox.critical(self, "Error", f"An error occurred during '{identifier}' operation:\n{error_message}")
        
        # Reset tombol dan sembunyikan progress bar
        self.check_button.setText("Check for Updates")
        self.update_button.setText("Update All")
        self.uninstall_button.setText("Uninstall Selected")
        self.update_button_states(is_working=False)
        
    def closeEvent(self, event):
        """Ensures the thread is properly shut down when closing the app."""
        self.thread.quit()
        self.thread.wait()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PythonPackageUpdater()
    window.show()
    sys.exit(app.exec())