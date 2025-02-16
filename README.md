# PyQt 3D Printer Application

This project is a PyQt application designed for controlling a 3D printer via a touchscreen interface. It connects to an OctoPrint instance using the OctoPrint client API, providing an intuitive user experience for managing print jobs and monitoring printer status.

## Features

- Touchscreen-friendly interface for easy navigation and control.
- Start, stop, and pause print jobs directly from the application.
- Real-time monitoring of printer status, including progress and current state.
- Integration with OctoPrint API for seamless communication with the 3D printer.

## Project Structure

```
pyqt-3d-printer-app
├── src
│   ├── main.py                # Entry point of the application
│   ├── ui
│   │   ├── main_window.py     # Main user interface definition
│   │   ├── home_screen.py     # Home screen UI
│   │   ├── loading_screen.py  # Loading screen UI
│   │   ├── ui_files
│   │   │   ├── home_screen.ui # Home screen UI file
│   │   │   ├── home_screen_ui.py # Generated Python file from home_screen.ui
│   │   │   ├── loading_screen.ui # Loading screen UI file
│   │   │   ├── loading_screen_ui.py # Generated Python file from loading_screen.ui
│   │   │   └── resources
│   │   │       └── resource_rc.py # Resource file
│   ├── octoprint_client
│   │   ├── __init__.py        # Package marker for octoprint_client
│   │   └── client.py          # OctoPrint API client
│   ├── models
│   │   └── printer_status.py  # Printer status representation
│   └── utils
│       └── helpers.py         # Utility functions
├── requirements.txt           # Project dependencies
└── README.md                  # Project documentation
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd pyqt-3d-printer-app
   ```

2. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Run the application:
   ```
   python src/main.py
   ```

## Usage

- Launch the application on your Raspberry Pi with a touchscreen.
- Use the main interface to control your 3D printer.
- Monitor the printer's status and progress in real-time.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## Developing

- Download QT Designer from: [QT Designer Download](https://build-system.fman.io/qt-designer-download)
- You can refer to the readme file at [Julia-Touch-UI-Documentation](https://github.com/FracktalWorks/Julia-Touch-UI-Documentation). For this project, I'm using VSCode and Copilot to develop, so taking a slightly different approach to the toolchain.
- Refer to this to understand how to properly use images inside a QT project: [text](https://www.youtube.com/watch?v=LceWgvYSVkQ)
- Convert the resource file: `pyrcc5 -o src/ui/ui_files/resources/resource_rc.py src/ui/ui_files/resources/resource.qrc`