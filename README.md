# Technolize Organizer

Technolize Organizer is a desktop file organizer that sorts files in a selected folder into categorized subfolders and keeps a history of what was moved. It includes a dashboard, preview mode, and simple analytics so you can organize quickly and confidently.

## What this project helps with

- Reduce clutter by auto-sorting common file types.
- Preview moves before applying changes.
- Track past organization runs with a local history file.
- Keep a clean, repeatable workflow for your Downloads or any folder.

## Skills and tech used

- Python 3
- CustomTkinter (GUI)
- Tkinter (dialogs and app shell)
- File system operations (Path, shutil)
- JSON persistence for history
- Threading for responsive UI

## Features

- Category-based organization (Documents, Media, Other)
- Preview of planned moves
- History log stored locally
- Stats and dashboard views
- Safe handling for name conflicts

## Getting started (Python)

1. Install Python 3.10+.
2. Install dependencies:

```bash
python -m pip install customtkinter
```

3. Run the app:

```bash
python organize_gui_riot.py
```

## Start the app (Windows executable)

If you want a standalone app, build it with PyInstaller:

```bash
python -m pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/logo.ico --name="Technolize Organizer" organize_gui_riot.py
```

The executable will be created in the `dist` folder. Run `Technolize Organizer.exe` to launch the app.

## Project files

- `organize_gui_riot.py`: main application entry point
- `assets/`: app assets (icon)
- `Technolize Organizer.spec`: PyInstaller spec file

## Notes

The history file is saved to:

`~/Documents/Technolize/organizer_history.json`
