# T4T - Extensible Automated Task Executor

T4T (Task for Things) is a powerful automated task execution tool built with Python and PyQt. It provides a graphical user interface for creating, managing, and monitoring various automated tasks. The core design philosophy of T4T is modularity and extensibility, allowing users to infinitely expand its functionality by developing custom modules.

## Core Features

*   **Graphical User Interface**: Provides an intuitive and easy-to-use graphical interface for users to manage and monitor tasks.
*   **Task Scheduling**: Built-in powerful task scheduler that supports timed, recurring, and event-driven tasks.
*   **Modular Design**: Users can develop and integrate new functional modules according to their own needs.
*   **Message Bus**: MQTT-based message bus for decoupling and asynchronous communication between modules and tasks.
*   **State Management**: Real-time monitoring and management of the state of tasks and the entire system.
*   **Multi-language Support**: Supports Chinese, English, and French interfaces.
*   **Theme Customization**: Supports light and dark themes, and allows users to customize themes.
*   **Logging System**: Built-in logging and viewing functions for easy debugging and tracking.

## Quick Start

### Prerequisites

*   Python 3.10+
*   PyQt5

### Installation

1.  Clone this repository to your local machine:
    ```bash
    git clone https://github.com/your-username/T4T.git
    cd T4T
    ```

2.  Create and activate a Python virtual environment:
    ```bash
    python -m venv venv
    source venv/bin/activate  # on Windows, use `venv\Scripts\activate`
    ```

3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

### Running

```bash
python main.py
```

## Usage Guide

1.  **Create a Task**:
    *   Click the "New Task" button on the main interface.
    *   In the pop-up dialog, select a task module.
    *   Configure the task parameters according to the module's needs.
    *   Click "OK" to create the task.

2.  **Manage Tasks**:
    *   In the task list on the main interface, you can view the status of all tasks.
    *   Select a task to view its detailed information, logs, and output in the details area on the right.
    *   You can start, stop, edit, and delete tasks.

3.  **System Settings**:
    *   In the "Settings" menu, you can configure system parameters such as language, theme, etc.

## Project Structure

```
T4T/
├───core/         # Core business logic
├───docs/         # Project documentation
├───i18n/         # Internationalization language files
├───logs/         # Log files
├───modules/      # Pluggable functional modules
├───services/     # Background services (e.g., MQTT Broker)
├───tests/        # Test cases
├───themes/       # Theme files
├───utils/        # Utility classes
├───view/         # PyQt interface components
├───main.py       # Main program entry point
└───requirements.txt # Python dependencies
```

## Module Development

One of the core advantages of T4T is its modular design. You can easily create your own modules to extend its functionality.

1.  **Create a Module Directory**:
    *   In the `modules/` directory, create a new folder for your module (e.g., `my_module`).

2.  **Write Module Code**:
    *   In the module directory, create a Python file (e.g., `my_module.py`).
    *   In this file, implement a class that inherits from `core.module_manager.BaseModule`.
    *   Implement the `run` method, which is the core logic of the module.

3.  **Create manifest.yaml**:
    *   In the module directory, create a `manifest.yaml` file to describe the module's metadata, such as name, description, version, and entry class.

For more details, please refer to `docs/development_guide.md`.

## Contributing

We welcome contributions of all forms! Whether it's reporting a bug, submitting a feature request, or contributing code directly.

Please ensure your code adheres to the project's existing coding style and passes all tests before submitting a Pull Request.

## License

This project is open-sourced under the [MIT License](LICENSE).