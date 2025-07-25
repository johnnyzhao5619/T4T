import logging
import psutil
import os
import shutil
import json
from functools import partial
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QLabel,
    QStatusBar,
    QToolBar,
    QAction,
    QSplitter,
    QMessageBox,
    QInputDialog,
    QTextBrowser,
    QPushButton,
    QToolButton,
    QMenu,
)
from PyQt5.QtCore import Qt, QTimer, QSize, QSettings
from view.task_list_widget import TaskListWidget
from view.detail_area_widget import DetailAreaWidget
from view.message_bus_monitor_widget import MessageBusMonitorWidget
from utils.i18n import language_manager, _
from utils.theme import theme_manager
from utils.config import ConfigManager
from utils.icon_manager import get_icon, set_theme as set_icon_theme
from utils.signals import global_signals
from utils.message_bus import message_bus_manager, BusConnectionState

logger = logging.getLogger(__name__)


class DevGuideWidget(QWidget):
    """A widget to display the development guide."""

    def __init__(self, module_manager, parent=None):
        super().__init__(parent)
        self.module_manager = module_manager
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Add a button to create a new module from the template
        self.create_module_button = QPushButton(
            get_icon('fa5s.plus-square', color_key='success'),
            _("create_new_module"))
        self.create_module_button.clicked.connect(self.create_new_module)
        layout.addWidget(self.create_module_button)

        # Text browser to display the guide
        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        layout.addWidget(self.text_browser)

        self.load_guide()

    def load_guide(self):
        """
        Loads and displays the development guide from docs/, with i18n support.
        """
        try:
            from utils.i18n import language_manager
            lang = language_manager.current_language

            app_root = os.path.dirname(
                os.path.dirname(os.path.abspath(__file__)))

            manual_name = "development_guide.md"
            base_name, ext = os.path.splitext(manual_name)

            manual_path_i18n = os.path.join(app_root, 'docs',
                                            f"{base_name}.{lang}{ext}")
            manual_path_default = os.path.join(app_root, 'docs', manual_name)

            final_path = manual_path_i18n if os.path.exists(
                manual_path_i18n) else manual_path_default

            if os.path.exists(final_path):
                with open(final_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.text_browser.setMarkdown(content)
            else:
                self.text_browser.setText(_("dev_guide_not_found"))
                logger.error(f"Development guide not found at {final_path}")
        except Exception:
            self.text_browser.setText(_("dev_guide_not_found"))
            logger.exception("Failed to load and render development guide.")

    def create_new_module(self):
        module_name, ok = QInputDialog.getText(self, _("create_new_module"),
                                               _("enter_module_name"))
        if ok and module_name:
            try:
                # Sanitize module name to be a valid directory name
                safe_module_name = "".join(c for c in module_name
                                           if c.isalnum() or c in ('_', '-'))
                safe_module_name = safe_module_name.rstrip()
                if not safe_module_name:
                    QMessageBox.warning(self, _("invalid_name"),
                                        _("module_name_invalid_chars"))
                    return

                src_dir = 'modules/template'
                dest_dir = f'modules/{safe_module_name}'

                if os.path.exists(dest_dir):
                    QMessageBox.warning(
                        self, _("module_exists"),
                        _("module_already_exists").format(
                            name=safe_module_name))
                    return

                # Copy the template directory
                shutil.copytree(src_dir, dest_dir)

                # Rename the files
                py_path = os.path.join(dest_dir, 'template_template.py')
                new_py_path = os.path.join(dest_dir,
                                           f'{safe_module_name}_template.py')
                os.rename(py_path, new_py_path)

                json_path = os.path.join(dest_dir, 'template_template.json')
                new_json_path = os.path.join(
                    dest_dir, f'{safe_module_name}_template.json')
                os.rename(json_path, new_json_path)

                # Update the module_type in the new json file
                with open(new_json_path, 'r+', encoding='utf-8') as f:
                    data = json.load(f)
                    data['module_type'] = safe_module_name
                    data['name'] = module_name
                    f.seek(0)
                    json.dump(data, f, indent=4)
                    f.truncate()

                QMessageBox.information(
                    self, _("success"),
                    _("module_created_successfully").format(
                        name=safe_module_name))
                self.module_manager.discover_modules()  # Refresh modules
            except Exception as e:
                QMessageBox.critical(
                    self, _("error"),
                    _("module_creation_failed").format(error=e))


class T4TMainWindow(QMainWindow):
    """Main window for the T4T Task Management Platform."""

    def __init__(self, scheduler, task_manager, module_manager):
        super().__init__()
        self.setGeometry(100, 100, 1280, 720)
        self.setMinimumSize(1280, 720)

        # Store managers
        self.scheduler = scheduler
        self.task_manager = task_manager
        self.module_manager = module_manager
        self._mqtt_stats_slot_connected = False

        # Setup UI
        self.setup_ui()
        self.retranslate_ui()  # Set initial text

        # Status bar timer
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.update_status_bar)
        self.status_timer.start(2000)  # Update every 2 seconds
        self.update_status_bar()

        # Connect to signals for dynamic updates
        language_manager.language_changed.connect(self.retranslate_ui)
        theme_manager.theme_changed.connect(self.on_theme_changed)
        global_signals.theme_changed.connect(self.refresh_theme)
        global_signals.task_manager_updated.connect(self.update_status_bar)
        global_signals.execute_in_main_thread.connect(
            self.execute_task_in_main_thread)
        global_signals.message_bus_status_changed.connect(
            self._update_message_bus_status)
        global_signals.service_state_changed.connect(
            self.on_service_state_changed)
        global_signals.ui_scaling_changed.connect(self.on_ui_scaling_changed)
        global_signals.font_family_changed.connect(self.update_font_family)

        # Start tasks that are marked as enabled in their config
        self.autostart_enabled_tasks()

        # Initially connect the message bus
        message_bus_manager.connect()

        # Set initial font size and family from config
        self.apply_global_style()

    def apply_global_style(self):
        """
        Sets all dynamic style properties (font size, family) and then
        re-applies the current theme's stylesheet to ensure all changes
        are rendered correctly. This is the definitive method for updating
        the application's look and feel.
        """
        config = ConfigManager()
        app = QApplication.instance()
        if not app:
            return

        # 1. Set Font Size Property
        try:
            level = int(config.get('appearance', 'font_size_level', 2))
        except (ValueError, TypeError):
            level = 2
        font_sizes = {0: 12, 1: 13, 2: 14, 3: 15, 4: 16}
        base_font_size = 14
        size_px = font_sizes.get(level, base_font_size)
        app.setProperty("fontSize", f"{size_px}px")

        # 2. Set Font Family Property
        font_family = config.get('appearance', 'font_family', 'Segoe UI')
        app.setProperty("fontFamily", font_family)

        # 3. Re-apply the current theme's stylesheet
        # This forces Qt to re-evaluate the QSS with the new properties
        theme_manager.apply_theme(theme_manager.current_theme_name)

        # 4. Emit scaling signal for widgets that need manual adjustments
        scaling_factor = size_px / base_font_size
        global_signals.ui_scaling_changed.emit(scaling_factor)

    def update_font_family(self, font_family=None):
        """
        Slot for when the font family is changed in settings.
        Triggers a global style refresh.
        """
        # The config is the source of truth, so we just need to trigger a refresh.
        self.apply_global_style()

    def update_font_size(self):
        """
        Slot for when the font size is changed in settings.
        Triggers a global style refresh.
        """
        # The config is the source of truth, so we just need to trigger a refresh.
        self.apply_global_style()

    def on_ui_scaling_changed(self, factor: float):
        """Adjusts UI elements that need explicit size changes."""
        # Scale toolbar icon sizes
        base_icon_size = 24  # The original, unscaled size
        scaled_size = int(base_icon_size * factor)
        self.toolbar.setIconSize(QSize(scaled_size, scaled_size))

    def execute_task_in_main_thread(self, task_name: str):
        """
        Executes a task function in the main GUI thread, triggered by a
        signal from a background worker. This is crucial for thread-unsafe
        libraries like pynput on macOS.
        """
        logger.debug(
            f"Main thread received request to execute task: {task_name}")
        task_info = self.task_manager.get_task_info(task_name)
        if not task_info:
            logger.error(
                f"Cannot execute task: '{task_name}' not found in TaskManager."
            )
            return

        # All task-loading and execution now happens safely in the main thread.
        try:
            executable_func = self.task_manager._load_task_executable(
                task_info['script'])
            if not executable_func:
                return

            log_emitter = partial(global_signals.log_message.emit, task_name)
            task_config = task_info.get('config_data', {})

            # Re-create the final callable function within the main thread
            task_callable = partial(executable_func,
                                    config=task_config,
                                    log_emitter=log_emitter,
                                    debug=task_config.get('debug', False),
                                    config_path=task_info['config'])

            # Execute the task
            task_callable()

        except Exception as e:
            logger.error(
                f"An error occurred while executing task '{task_name}'"
                f" in main thread: {e}")

    def on_service_state_changed(self, service_name: str, state):
        if service_name == 'mqtt_broker':
            if state.name == 'RUNNING':
                self._update_message_bus_status(
                    BusConnectionState.CONNECTED.value, _("status_connected"))
            elif state.name == 'STOPPED':
                self._update_message_bus_status(
                    BusConnectionState.DISCONNECTED.value,
                    _("status_disconnected"))
            elif state.name == 'FAILED':
                self._update_message_bus_status(
                    BusConnectionState.DISCONNECTED.value, _("status_failed"))
            else:
                self._update_message_bus_status(
                    BusConnectionState.CONNECTING.value,
                    _("status_connecting"))

    def autostart_enabled_tasks(self):
        """
        Automatically starts tasks that are marked as 'enabled' in their
        configuration file.
        """
        for task_name in self.task_manager.get_task_list():
            task_config = self.task_manager.get_task_config(task_name)
            if task_config and task_config.get('enabled', False):
                self.task_manager.start_task(task_name)

    def on_theme_changed(self, stylesheet):
        """
        Slot to handle theme changes.
        The stylesheet is already applied globally, but this slot can be
        used for any component-specific updates if needed in the future.
        """
        logger.info(f"Theme changed to {theme_manager.current_theme_name}.")
        self.refresh_theme()

    def refresh_theme(self):
        """
        Refreshes theme-dependent elements like icons.
        """
        set_icon_theme(theme_manager.current_theme_name)
        self.setup_toolbar_icons()
        # Optionally, re-translate UI if some elements depend on theme + lang
        # self.retranslate_ui()
        pass

    def setup_ui(self):
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # Splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)

        # Left panel: Task List with Title
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_panel.setLayout(left_layout)

        self.task_list_title = QLabel()
        self.task_list_title.setObjectName("task_list_title")  # For styling
        left_layout.addWidget(self.task_list_title)

        self.task_list_widget = TaskListWidget(self.task_manager,
                                               self.scheduler, self)
        left_layout.addWidget(self.task_list_widget)

        splitter.addWidget(left_panel)

        self.task_list_widget.itemSelectionChanged.connect(
            self.on_task_selection_changed)

        # Right panel: Task Details (Tabbed view)
        self.detail_area_widget = DetailAreaWidget(self.task_manager)
        splitter.addWidget(self.detail_area_widget)

        # Set minimum widths for the panels
        left_panel.setMinimumWidth(300)
        self.detail_area_widget.setMinimumWidth(500)

        # Set initial sizes for splitter, now handled by load_splitter_state
        self.splitter = splitter
        self.load_splitter_state()

        # Toolbar at the top
        self.toolbar = QToolBar("Main Toolbar")
        self.addToolBar(self.toolbar)

        # Toolbar actions
        self.add_task_action = QAction("", self)
        self.add_task_action.triggered.connect(self.add_task)

        self.start_action = QAction("", self)
        self.start_action.triggered.connect(self.start_task)
        self.pause_action = QAction("", self)
        self.pause_action.triggered.connect(self.pause_task)
        self.stop_action = QAction("", self)
        self.stop_action.triggered.connect(self.stop_task)

        self.start_all_action = QAction("", self)
        self.start_all_action.triggered.connect(self.start_all_tasks)
        self.pause_all_action = QAction("", self)
        self.pause_all_action.triggered.connect(self.pause_all_tasks)
        self.stop_all_action = QAction("", self)
        self.stop_all_action.triggered.connect(self.stop_all_tasks)

        self.toolbar.addSeparator()

        self.logs_action = QAction("", self)
        self.logs_action.triggered.connect(self.open_logs_tab)
        self.dev_guide_action = QAction("", self)
        self.dev_guide_action.triggered.connect(self.open_dev_guide_tab)
        self.monitor_action = QAction("", self)
        self.monitor_action.triggered.connect(self.open_monitor_tab)
        self.help_action = QAction("", self)
        self.help_action.triggered.connect(self.open_help_tab)

        self.toolbar.addSeparator()

        self.settings_action = QAction("", self)
        self.settings_action.triggered.connect(self.open_settings_tab)

        self.toolbar.addAction(self.add_task_action)
        self.toolbar.addAction(self.start_action)
        self.toolbar.addAction(self.pause_action)
        self.toolbar.addAction(self.stop_action)
        self.toolbar.addAction(self.start_all_action)
        self.toolbar.addAction(self.pause_all_action)
        self.toolbar.addAction(self.stop_all_action)
        self.toolbar.addAction(self.logs_action)
        self.toolbar.addAction(self.dev_guide_action)
        self.toolbar.addAction(self.monitor_action)
        self.toolbar.addAction(self.help_action)
        self.toolbar.addAction(self.settings_action)

        self.setup_toolbar_icons()

        # Initial state for task-specific actions
        self.start_action.setEnabled(False)
        self.pause_action.setEnabled(False)
        self.stop_action.setEnabled(False)

        # Status bar at the bottom
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.system_info_label = QLabel()

        # Service Control Button
        self.service_control_button = QToolButton()
        self.service_control_button.setPopupMode(QToolButton.InstantPopup)
        self.service_control_button.setToolButtonStyle(
            Qt.ToolButtonTextBesideIcon)
        self.service_control_button.setIconSize(QSize(16, 16))
        self.service_menu = QMenu(self)
        self.service_control_button.setMenu(self.service_menu)

        self.connect_action = QAction(self)
        self.connect_action.triggered.connect(message_bus_manager.connect)
        self.disconnect_action = QAction(self)
        self.disconnect_action.triggered.connect(
            message_bus_manager.disconnect)
        self.switch_to_mqtt_action = QAction("MQTT", self)
        self.switch_to_mqtt_action.setCheckable(True)
        self.switch_to_mqtt_action.triggered.connect(
            lambda: message_bus_manager.switch_service('mqtt'))

        self.service_menu.addAction(self.connect_action)
        self.service_menu.addAction(self.disconnect_action)

        self.status_bar.addPermanentWidget(self.system_info_label)
        self.status_bar.addPermanentWidget(self.service_control_button)

        self._update_message_bus_status(BusConnectionState.DISCONNECTED.value,
                                        _("message_bus_disconnected"))

    def _on_mqtt_stats_updated(self, stats: dict):
        client_count = stats.get('client_count', 0)
        text = f"MQTT: {client_count} " + _('clients')
        self.service_control_button.setText(text)

    def setup_toolbar_icons(self):
        """Set icons for all toolbar actions."""
        self.add_task_action.setIcon(get_icon('fa5s.plus',
                                              color_key='success'))
        self.start_action.setIcon(get_icon('fa5s.play', color_key='success'))
        self.pause_action.setIcon(get_icon('fa5s.pause', color_key='warning'))
        self.stop_action.setIcon(get_icon('fa5s.stop', color_key='danger'))
        self.start_all_action.setIcon(
            get_icon('fa5s.play-circle', color_key='success'))
        self.pause_all_action.setIcon(
            get_icon('fa5s.pause-circle', color_key='warning'))
        self.stop_all_action.setIcon(
            get_icon('fa5s.stop-circle', color_key='danger'))
        self.logs_action.setIcon(get_icon('fa5s.file-alt', color_key='info'))
        self.dev_guide_action.setIcon(get_icon('fa5s.book', color_key='info'))
        self.monitor_action.setIcon(
            get_icon('fa5s.tachometer-alt', color_key='info'))
        self.help_action.setIcon(
            get_icon('fa5s.question-circle', color_key='info'))
        self.settings_action.setIcon(get_icon('fa5s.cogs'))

    def retranslate_ui(self):
        """
        Update all UI text elements with the current language translations.
        """
        self.setWindowTitle(_("app_title"))
        self.toolbar.setWindowTitle(_("main_toolbar_title"))
        self.task_list_title.setText(_("task_list_title"))
        self.add_task_action.setText(_("add_task_action"))
        self.start_action.setText(_("start_action"))
        self.pause_action.setText(_("pause_action"))
        self.start_all_action.setText(_("start_all_action"))
        self.pause_all_action.setText(_("pause_all_action"))
        self.stop_action.setText(_("stop_action"))
        self.stop_all_action.setText(_("stop_all_action"))
        self.logs_action.setText(_("logs_action"))
        self.dev_guide_action.setText(_("dev_guide_title"))
        self.monitor_action.setText(_("message_bus_monitor_title"))
        self.help_action.setText(_("help_action"))
        self.settings_action.setText(_("settings_action"))
        self.connect_action.setText(_("connect_service"))
        self.disconnect_action.setText(_("disconnect_service"))

        # Also retranslate child widgets if they don't handle it themselves
        self.task_list_widget.retranslate_ui()
        self.detail_area_widget.retranslate_ui()
        self.update_status_bar()

    def _update_message_bus_status(self, status_str: str, message: str):
        """
        Update the message bus status icon, text, and menu availability.
        """
        is_connected = (status_str == BusConnectionState.CONNECTED.value)
        is_disconnected = (status_str == BusConnectionState.DISCONNECTED.value)

        self.connect_action.setEnabled(is_disconnected)
        self.disconnect_action.setEnabled(is_connected)

        status_map = {
            BusConnectionState.CONNECTED.value: {
                "icon": "fa5s.check-circle",
                "color_key": "success",
                "text": _("status_connected")
            },
            BusConnectionState.CONNECTING.value: {
                "icon": "fa5s.spinner",
                "color_key": "info",
                "text": _("status_connecting")
            },
            BusConnectionState.RECONNECTING.value: {
                "icon": "fa5s.sync-alt",
                "color_key": "warning",
                "text": _("status_reconnecting")
            },
            BusConnectionState.DISCONNECTED.value: {
                "icon": "fa5s.unlink",
                "color_key": "danger",
                "text": _("status_disconnected")
            },
        }
        visual_config = status_map.get(
            status_str, {
                "icon": "fa5s.question-circle",
                "color_key": "danger",
                "text": "Unknown"
            })

        icon = get_icon(visual_config["icon"],
                        color_key=visual_config["color_key"])
        self.service_control_button.setIcon(icon)
        # Default text, will be overwritten by stats updater if connected
        self.service_control_button.setText(visual_config["text"])
        tooltip_text = f"<b>{status_str}</b><br>{message}"
        self.service_control_button.setToolTip(tooltip_text)

        # Update service type menu
        active_service = message_bus_manager.get_active_service_type()
        is_mqtt_active = (active_service == 'mqtt')

        # Connect/disconnect the stats signal
        should_be_connected = is_connected and is_mqtt_active
        if should_be_connected and not self._mqtt_stats_slot_connected:
            global_signals.mqtt_stats_updated.connect(
                self._on_mqtt_stats_updated)
            self._mqtt_stats_slot_connected = True
            logger.debug("Connected MQTT stats signal.")
        elif not should_be_connected and self._mqtt_stats_slot_connected:
            global_signals.mqtt_stats_updated.disconnect(
                self._on_mqtt_stats_updated)
            self._mqtt_stats_slot_connected = False
            logger.debug("Disconnected MQTT stats signal.")

    def closeEvent(self, event):
        """
        Handles the window close event to ensure a graceful shutdown.
        """
        logger.info("Close event triggered. Starting graceful shutdown...")
        self.status_bar.showMessage(_("shutting_down_message"), 0)

        # 1. Stop TaskManager and wait for all tasks to complete
        logger.info("Shutting down TaskManager...")
        self.task_manager.shutdown(wait=True)
        logger.info("TaskManager shut down.")

        # 2. Disconnect from the message bus
        logger.info("Disconnecting from Message Bus...")
        message_bus_manager.disconnect()
        logger.info("Message Bus disconnected.")

        # 3. Perform other cleanup tasks
        self.save_splitter_state()
        logger.info("Window state saved.")

        # 4. Accept the event to close the application
        logger.info("Graceful shutdown complete. Accepting close event.")
        event.accept()

    def save_splitter_state(self):
        """Saves the current state of the splitter to settings."""
        settings = QSettings("T4T", "T4T_App")
        settings.setValue("main_splitter_state", self.splitter.saveState())

    def load_splitter_state(self):
        """Loads the splitter state from settings."""
        settings = QSettings("T4T", "T4T_App")
        state = settings.value("main_splitter_state")
        if state:
            self.splitter.restoreState(state)
        else:
            # Set default sizes if no state is saved
            self.splitter.setSizes(
                [int(self.width() * 0.25),
                 int(self.width() * 0.75)])

    def on_task_selection_changed(self):
        """
        Handles the logic when a task selection changes in the list.
        """
        selected_items = self.task_list_widget.selectedItems()
        if selected_items:
            task_name = selected_items[0].text(0)  # Column 0 for task name
            status = self.task_manager.get_task_status(task_name)
            self.detail_area_widget.update_details(task_name, status)
            self.start_action.setEnabled(True)
            self.pause_action.setEnabled(True)
            self.stop_action.setEnabled(True)
        else:
            self.detail_area_widget.clear_details()
            self.start_action.setEnabled(False)
            self.pause_action.setEnabled(False)
            self.stop_action.setEnabled(False)

    def update_status_bar(self):
        """
        Update the status bar with current task counts and system
        resource usage.
        """
        total_tasks = self.task_manager.get_task_count()
        running_tasks = self.task_manager.get_running_task_count()

        cpu_percent = psutil.cpu_percent()
        memory_info = psutil.virtual_memory()
        memory_percent = memory_info.percent

        status_text = (
            f"{_('status_bar_tasks').format(count=total_tasks)} | "
            f"{_('status_bar_running').format(count=running_tasks)} | "
            f"CPU: {cpu_percent:.1f}% | "
            f"Mem: {memory_percent:.1f}%")
        self.system_info_label.setText(status_text)

    def add_task(self):
        """
        Opens a new tab to create a new task.
        """
        self.detail_area_widget.open_new_task_tab()

    def start_task(self):
        selected_items = self.task_list_widget.selectedItems()
        if selected_items:
            task_name = selected_items[0].text(0)
            status = self.task_manager.get_task_status(task_name)
            if status == 'paused':
                success = self.task_manager.resume_task(task_name)
            else:
                success = self.task_manager.start_task(task_name)
            if success:
                self.on_task_selection_changed()
                logger.info(f"Task {task_name} started or resumed.")
            else:
                logger.error(f"Failed to start or resume task {task_name}.")
        else:
            logger.warning("No task selected to start.")

    def pause_task(self):
        selected_items = self.task_list_widget.selectedItems()
        if selected_items:
            task_name = selected_items[0].text(0)
            success = self.task_manager.pause_task(task_name)
            if success:
                self.on_task_selection_changed()
                logger.info(f"Task {task_name} paused.")
            else:
                logger.error(f"Failed to pause task {task_name}.")
        else:
            logger.warning("No task selected to pause.")

    def start_all_tasks(self):
        self.task_manager.start_all_tasks()
        self.on_task_selection_changed()
        logger.info("Attempted to start all tasks.")

    def pause_all_tasks(self):
        self.task_manager.pause_all_tasks()
        self.on_task_selection_changed()
        logger.info("Attempted to pause all tasks.")

    def stop_all_tasks(self):
        self.task_manager.stop_all_tasks()
        self.on_task_selection_changed()
        logger.info("Attempted to stop all tasks.")

    def stop_task(self):
        selected_items = self.task_list_widget.selectedItems()
        if selected_items:
            task_name = selected_items[0].text(0)
            success = self.task_manager.stop_task(task_name)
            if success:
                self.on_task_selection_changed()
                logger.info(f"Task {task_name} stopped.")
            else:
                logger.error(f"Failed to stop task {task_name}.")
        else:
            logger.warning("No task selected to stop.")

    def delete_task(self):
        selected_items = self.task_list_widget.selectedItems()
        if selected_items:
            task_name = selected_items[0].text(0)
            success = self.task_manager.delete_task(task_name)
            if success:
                self.task_list_widget.refresh_tasks()
                self.update_status_bar()
                logger.info(f"Task {task_name} deleted.")
            else:
                logger.error(f"Failed to delete task {task_name}.")
        else:
            logger.warning("No task selected to delete.")

    def open_settings_tab(self):
        """
        Opens the settings widget in a new tab.
        """
        self.detail_area_widget.open_settings_tab()

    def open_logs_tab(self):
        """
        Opens the log viewer widget in a new tab.
        """
        self.detail_area_widget.open_log_viewer_tab()

    def open_help_tab(self):
        """
        Opens the help widget in a new tab.
        """
        self.detail_area_widget.open_help_tab()

    def open_dev_guide_tab(self):
        """
        Opens the development guide widget in a new tab.
        """
        self.detail_area_widget.open_widget_as_tab(
            widget_id="dev_guide_tab",
            widget_class=DevGuideWidget,
            title=_("dev_guide_title"),
            icon_name='fa5s.book',
            constructor_args=[self.module_manager])

    def open_monitor_tab(self):
        """
        Opens the message bus monitor widget in a new tab.
        """
        self.detail_area_widget.open_widget_as_tab(
            widget_id="message_bus_monitor_tab",
            widget_class=MessageBusMonitorWidget,
            title=_("message_bus_monitor_title"),
            icon_name='fa5s.tachometer-alt')
