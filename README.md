# Stock Floating Widget

A lightweight Windows desktop stock price floating widget for personal investment workflow.

Stock Floating Widget displays a compact, always-on-top view of a selected A-share stock. It is designed to stay unobtrusive while you work and provide quick access to the latest price and percentage change.

## Features

- Displays the stock name, current price, and percentage change.
- Uses red for price increases and green for price decreases.
- Provides a borderless, always-on-top floating window.
- Supports drag-to-move and remembers the last window position.
- Searches stocks by name, pinyin, or stock code.
- Refreshes quote data automatically and supports pausing updates.
- Keeps the last successful quote visible when a network request fails.
- Includes a Windows system tray menu for showing, hiding, changing the stock, pausing updates, and quitting.
- Supports the global `Alt+\`` shortcut on Windows to show or hide the widget.
- Stores preferences locally between runs.

## Technology

- Python 3.10+
- [PySide6](https://doc.qt.io/qtforpython-6/)
- [Requests](https://requests.readthedocs.io/)
- Windows `RegisterHotKey` API through Python `ctypes`
- Tencent quote and stock-search endpoints

## Installation

1. Install Python 3.10 or later. On Windows, enable **Add Python to PATH** during installation.
2. Clone or download this repository.
3. Open a terminal in the project directory.
4. Optional but recommended: create and activate a virtual environment.

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

5. Install the dependencies.

   ```powershell
   python -m pip install -r requirements.txt
   ```

## Running the Application

Run the existing entry point from the project root:

```powershell
python main.py
```

The widget appears near the upper-right corner on first launch. Drag it to reposition it, right-click it for more actions, or use the system tray menu.

## Configuration

The application creates its local configuration after the first run at:

```text
%APPDATA%\StockWidget\config.json
```

This file stores the selected stock, refresh interval, window position, font size, opacity, colors, and hotkey. It is local runtime data and is not part of the repository.

## Project Structure

```text
Stock-Floating-Widget/
├── assets/
│   └── screenshots/
├── config/
│   ├── __init__.py
│   └── settings.py
├── services/
│   ├── __init__.py
│   └── stock_api.py
├── ui/
│   ├── __init__.py
│   ├── floating_window.py
│   └── stock_picker.py
├── utils/
│   ├── __init__.py
│   └── win_hotkey.py
├── .gitignore
├── main.py
├── README.md
└── requirements.txt
```

## Screenshot

Project screenshots belong in [`assets/screenshots/`](assets/screenshots/). A recommended filename for the main screenshot is `stock-floating-widget.png`.

After adding the image, it can be embedded here with:

```markdown
![Stock Floating Widget](assets/screenshots/stock-floating-widget.png)
```

## Notes

- The application is intended primarily for Windows. The floating window can run on other platforms, but the global hotkey is Windows-specific.
- Quote data requires an internet connection and is retrieved from Tencent endpoints.
- No API key or account credentials are required by the current implementation.
