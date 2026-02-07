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

## 🖼️ The GUI consists of:
Table Widget → package list (Name, Current Version, Latest Version, Type).
Action Buttons → Check, Update All, Uninstall Selected.
Progress Bar → appears while the process is running.
---
## 📸 Screenshot
<img width="853" height="634" alt="image" src="https://github.com/user-attachments/assets/3be714d7-73e9-43ab-88fd-7d4b9ed44470" />


