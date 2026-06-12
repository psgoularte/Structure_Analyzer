# Architecture of the Structure Analyzer Application

## Overview

The Structure Analyzer is a Python application designed to analyze structural systems by calculating and visualizing the effects of applied loads, including active and reactive forces on nodes and bars. The application features a graphical user interface (GUI) that allows users to interact with the model and visualize results in a user-friendly manner.

## Project Structure

The project is organized into several key directories and files, each serving a specific purpose:

- **pyproject.toml**: Configuration file for the Python project, specifying metadata and dependencies.
- **requirements.txt**: Lists required Python packages and their versions.
- **README.md**: Documentation for setup instructions and usage guidelines.

### Source Code

The source code is located in the `src/pef_analyzer` directory and is divided into several modules:

- **gui**: Contains the graphical user interface components.
  - `app.py`: Entry point for the GUI application.
  - `main_window.py`: Manages the main application window and layout.
  - **widgets**: Contains custom widgets for the GUI.
    - `canvas.py`: Responsible for rendering diagrams of forces and constraints.
    - `controls.py`: Provides user interface elements for interaction.
  - **resources**: Contains stylesheets for customizing the GUI appearance.

- **core**: Implements the core functionality of the application.
  - `model.py`: Defines the data model for nodes, bars, and loads.
  - `node.py`: Represents a node in the structure.
  - `bar.py`: Represents a structural element.
  - `load.py`: Represents external forces applied to the structure.
  - `solver.py`: Implements logic for calculating effects of loads.

- **io**: Handles input/output operations.
  - `project_io.py`: Manages saving and loading project data.
  - `parsers.py`: Contains functions for parsing input data.

- **visualization**: Responsible for rendering and visualizing the structure.
  - `renderer.py`: Draws the structure and visualizes forces.
  - `colormap.py`: Generates color maps for visualizing forces and constraints.

- **utils**: Contains utility functions that assist with various tasks throughout the application.

### Tests

The `tests` directory contains unit tests for the application, ensuring the reliability and correctness of the core functionalities:

- `test_model.py`: Unit tests for the model components.
- `test_io.py`: Unit tests for input/output functionality.

## Conclusion

The Structure Analyzer application is designed with a modular architecture, allowing for easy maintenance and extensibility. Each component is responsible for a specific aspect of the application, promoting separation of concerns and enhancing code readability. The GUI is designed to be intuitive, providing users with a seamless experience while analyzing structural systems.