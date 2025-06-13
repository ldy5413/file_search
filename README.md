# File Search Application

This project provides a simple file search utility with a Tkinter-based GUI. The code indexes files in a SQLite database and allows real-time search and monitoring of the filesystem.

## Repository layout

All application code now lives inside the `file_search` package:

- `database.py` – Functions for building and updating the SQLite index. Includes a Tkinter prompt for selecting a directory and utilities for keeping the database in sync with the filesystem.
- `monitor.py` – Uses the `watchdog` package to monitor filesystem changes and update the index accordingly.
- `search.py` – Simple search helper that queries the database for paths containing given keywords.
- `gui.py` – The main GUI application tying together search, indexing and monitoring features.
- `__init__.py` – Exposes the main functions and `FileSearchApp` class.
- `requirements.txt` – Python dependencies; currently only `watchdog` is required.

## Suggested improvements

- Add unit tests for database operations and the search logic.
- Provide a setup script and command-line interface in addition to the GUI.
- Support indexing multiple directories and choose monitoring paths from the GUI.

