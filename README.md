## 🐍 Python Package Updater by Danx
Python Package Updater is a GUI application based on PySide6 (Qt for Python) that makes it easy for developers to:
Check for outdated Python packages.
Update all packages at once.
Uninstall selected packages.
The application runs in a separate thread to keep the GUI responsive when executing pip commands.
---
## ✨ Features
Check for Updates → displays a list of Python packages that need updating.
Update All → upgrades all outdated packages with a single click.
Uninstall Selected → removes selected packages directly from the table.
Modern UI/UX → dark mode with custom QSS (similar to the Nord theme).
Progress Bar → indicates progress, preventing GUI freezes.
Error Handling → clear error messages if pip is not found or the command fails.
---

## 📝 Changelog v2.5.0
- ✨ Added
Requirements.txt Management:
  - "Create requirements.txt": Added a new function to scan the current environment (pip freeze) and generate a requirements.txt file containing only the package names.
  - "Install from requirements.txt": Added a new function to read an existing requirements.txt file and install all specified packages.
  - Contextual Dependency Scanning:
    - "Scan File & Check...": Implemented a new feature that allows users to select a .py file.
    - The application now uses an AST (Abstract Syntax Tree) parser to identify all import statements within that file.
  - The outdated package check can now be filtered to show only the dependencies relevant to the scanned file.
  - UI/UX Enhancements:
Integrated custom SVG icons for all primary-action buttons ("Check", "Scan", "Update", "Uninstall", "Create Reqs", "Install Reqs") to improve visual clarity and user experience.

- 🔄 Changed
  - Button Layout & Naming:
    - Renamed the original "Check for Updates" button to "Check All Outdated" to better differentiate it from the new scan feature.
    - The main button layout was refactored from a single row to three distinct, logically grouped rows (Check/Scan, Actions, Requirements).
---

## 🖼️ The GUI consists of:
Table Widget → package list (Name, Current Version, Latest Version, Type).
Action Buttons → Check, Update All, Uninstall Selected.
Progress Bar → appears while the process is running.
---
## 📸 Screenshot
<img width="800" height="632" alt="Screenshot 2025-11-13 060548" src="https://github.com/user-attachments/assets/e08fca76-7b29-442b-ad53-f3f156189a13" />

