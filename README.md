# Structure Analyzer

## Overview
The Structure Analyzer is a Python application designed to analyze structural systems by calculating and visualizing the effects of applied loads, including active and reactive forces on nodes and bars. The application features a graphical user interface (GUI) that allows users to interactively define structures and visualize the results.

## Project Structure
```
structure-analyzer
├── pyproject.toml
├── requirements.txt
├── README.md
├── src
│   └── pef_analyzer
│       ├── __init__.py
│       ├── gui
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── main_window.py
│       │   ├── widgets
│       │   │   ├── __init__.py
│       │   │   ├── canvas.py
│       │   │   └── controls.py
│       │   └── resources
│       │       └── styles.qss
│       ├── core
│       │   ├── __init__.py
│       │   ├── model.py
│       │   ├── node.py
│       │   ├── bar.py
│       │   ├── load.py
│       │   └── solver.py
│       ├── io
│       │   ├── __init__.py
│       │   ├── project_io.py
│       │   └── parsers.py
│       ├── visualization
│       │   ├── __init__.py
│       │   ├── renderer.py
│       │   └── colormap.py
│       └── utils
│           ├── __init__.py
│           └── helpers.py
├── tests
│   ├── __init__.py
│   ├── test_model.py
│   └── test_io.py
└── docs
    └── architecture.md
```

## Installation
To set up the project, follow these steps:

1. Clone the repository:
   ```
   git clone <repository-url>
   cd structure-analyzer
   ```

2. Create a virtual environment (optional but recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Usage
To run the application, execute the following command:
```
python -m src.pef_analyzer.gui.app
```

Once the application is running, you can:

- Add nodes and bars to define your structure.
- Apply loads to the structure.
- Visualize the active and reactive forces on the bars and nodes.
- Customize the appearance of the interface using the provided styles.

## Contributing
Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License
This project is licensed under the MIT License. See the LICENSE file for details.