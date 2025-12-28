# Technolize Folder Organizer

A Tkinter desktop app that tidies a chosen folder into documents, media, and other buckets, with a dashboard, history, and light/dark themes.

## Features
- One-click organize by extension (Documents/Excel, Documents/Word, Documents/PDF, Documents/Text, Media/Images, Media/Videos, Other).
- Dashboard with last run summary, activity log, and quick actions.
- Persistent history stored on disk (includes file moves and theme preference).
- Light/dark theme toggle; rounded button styling and gradient hero.
- Safeguards: no overwrites—colliding names get numbered.

## Requirements
- Python 3.10+ (tkinter standard library module must be available).

## Run
1) Optional: create/activate a virtual environment.
2) From the repo root, launch the app:
```
python organize_gui.py
```

## Usage
- Pick a folder (defaults to your Downloads) and click Organize now.
- Check History to review past runs and moved files.
- Toggle the theme in Settings; your choice is saved.

## Data Storage
- History and theme are saved to `Documents/Technolize/organizer_history.json` in your user profile.

## Notes
- Only top-level files are organized; subfolders are untouched.
- Legacy top-level folders named Excel/Word/PDF/Text are merged under Documents/* when present.
