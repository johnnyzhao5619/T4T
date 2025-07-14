from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QFormLayout, QComboBox,
                             QLabel, QListWidget, QPushButton, QHBoxLayout,
                             QFileDialog, QMessageBox, QListWidgetItem,
                             QGroupBox, QScrollArea, QSlider, QMainWindow)
from PyQt5.QtCore import Qt
from utils.config import ConfigManager
from PyQt5.QtWidgets import QApplication
from utils.theme import theme_manager, switch_theme
from utils.i18n import language_manager, switch_language, _
from core.module_manager import module_manager
from utils.signals import global_signals
from utils.icon_manager import get_icon


class SettingsWidget(QWidget):
    """
    A widget for changing application settings, designed to be embedded
    in a tab.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config_manager = ConfigManager()

        # Store base sizes for scaling
        self.base_form_spacing = 10

        self.init_ui()
        self.populate_and_connect()
        # Set an object name for styling
        self.setObjectName("SettingsWidget")

        global_signals.ui_scaling_changed.connect(self.on_ui_scaling_changed)

    def on_ui_scaling_changed(self, factor: float):
        """Adjusts UI elements based on the scaling factor."""
        self.form_layout.setSpacing(int(self.base_form_spacing * factor))

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setObjectName("SettingsScrollArea")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(20, 20, 20, 20)
        container_layout.setSpacing(15)
        container_layout.setAlignment(Qt.AlignTop)

        # --- Appearance and Language Group ---
        appearance_group = QGroupBox(_("appearance_language_group_title"))
        appearance_group.setObjectName("appearance_language_group_title")
        self.form_layout = QFormLayout(appearance_group)
        self.form_layout.setLabelAlignment(Qt.AlignLeft)
        self.form_layout.setFormAlignment(Qt.AlignLeft)
        self.form_layout.setFieldGrowthPolicy(
            QFormLayout.AllNonFixedFieldsGrow)
        self.form_layout.setSpacing(self.base_form_spacing)

        self.theme_combo = QComboBox()
        self.theme_label = QLabel(_("theme_label"))
        self.form_layout.addRow(self.theme_label, self.theme_combo)

        self.language_combo = QComboBox()
        self.language_label = QLabel(_("language_label"))
        self.form_layout.addRow(self.language_label, self.language_combo)

        # --- Font Family ComboBox ---
        self.font_family_combo = QComboBox()
        self.font_family_label = QLabel(_("font_family_label"))
        self.form_layout.addRow(self.font_family_label,
                                self.font_family_combo)

        # --- Font Size Slider ---
        self.font_size_label = QLabel(_("font_size_label"))
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_size_slider.setRange(0, 4)
        self.font_size_slider.setTickInterval(1)
        self.font_size_slider.setTickPosition(QSlider.TicksBelow)
        self.current_font_size_label = QLabel()

        font_slider_layout = QHBoxLayout()
        font_slider_layout.addWidget(self.font_size_slider)
        font_slider_layout.addSpacing(10)
        font_slider_layout.addWidget(self.current_font_size_label)
        self.form_layout.addRow(self.font_size_label, font_slider_layout)

        container_layout.addWidget(appearance_group)

        # --- Module Management Group ---
        module_group = QGroupBox(_("module_management_group_title"))
        module_group.setObjectName("module_management_group_title")
        module_layout = QVBoxLayout(module_group)

        self.module_list_widget = QListWidget()
        self.module_list_widget.setObjectName("ModuleList")
        module_layout.addWidget(self.module_list_widget)

        import_button_layout = QHBoxLayout()
        self.import_module_button = QPushButton(get_icon("fa5s.plus-circle"),
                                                _("import_module_button"))
        import_button_layout.addWidget(self.import_module_button)
        import_button_layout.addStretch()
        module_layout.addLayout(import_button_layout)

        container_layout.addWidget(module_group)

        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

    def populate_and_connect(self):
        self.populate_themes()
        self.populate_languages()
        self.populate_font_families()
        self.load_font_size_setting()
        self.populate_modules()

        self.theme_combo.currentTextChanged.connect(self.on_theme_changed)
        self.language_combo.currentTextChanged.connect(
            self.on_language_changed)
        self.font_family_combo.currentTextChanged.connect(
            self.on_font_family_changed)
        self.font_size_slider.valueChanged.connect(self.on_font_size_changed)
        self.import_module_button.clicked.connect(self.import_module)

        global_signals.language_changed.connect(self.retranslate_ui)
        global_signals.modules_updated.connect(self.populate_modules)

    def populate_themes(self):
        available_themes = theme_manager.get_available_themes()
        current_theme = theme_manager.current_theme_name
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItems(available_themes)
        if current_theme in available_themes:
            self.theme_combo.setCurrentText(current_theme)
        self.theme_combo.blockSignals(False)

    def populate_languages(self):
        available_languages = language_manager.get_available_languages(
        )  # Returns dict
        current_lang_code = language_manager.current_language
        current_lang_name = available_languages.get(current_lang_code,
                                                    current_lang_code)

        self.language_combo.blockSignals(True)
        self.language_combo.clear()

        for name in sorted(available_languages.values()):
            self.language_combo.addItem(name)

        self.language_combo.setCurrentText(current_lang_name)
        self.language_combo.blockSignals(False)

    def populate_font_families(self):
        # Common cross-platform fonts
        fonts = [
            "Segoe UI", "Arial", "Verdana", "Tahoma", "Calibri", "Helvetica",
            "Times New Roman", "Courier New", "Consolas", "Monaco"
        ]
        current_font = self.config_manager.get('appearance', 'font_family',
                                               "Segoe UI")

        self.font_family_combo.blockSignals(True)
        self.font_family_combo.clear()
        self.font_family_combo.addItems(fonts)
        if current_font in fonts:
            self.font_family_combo.setCurrentText(current_font)
        self.font_family_combo.blockSignals(False)

    def on_theme_changed(self, theme_name):
        if theme_name:
            switch_theme(theme_name)
            self.config_manager.set('appearance', 'theme', theme_name)

    def on_language_changed(self, language_name):
        if language_name:
            # Find the language code from the name
            lang_code = language_manager.get_language_code(language_name)
            if lang_code:
                switch_language(lang_code)
                self.config_manager.set('appearance', 'language', lang_code)

    def on_font_family_changed(self, font_family):
        if font_family:
            self.config_manager.set('appearance', 'font_family', font_family)
            global_signals.font_family_changed.emit(font_family)

    def load_font_size_setting(self):
        try:
            level = self.config_manager.get('appearance', 'font_size_level', 2)
            level = int(level)
        except (ValueError, TypeError):
            level = 2

        self.font_size_slider.blockSignals(True)
        self.font_size_slider.setValue(level)
        self.font_size_slider.blockSignals(False)
        self.update_font_size_label(level)

    def on_font_size_changed(self, level):
        self.config_manager.set('appearance', 'font_size_level', str(level))
        self.update_font_size_label(level)

        # Get the main window and call its update_font_size method
        main_window = next((w for w in QApplication.topLevelWidgets()
                            if isinstance(w, QMainWindow)), None)
        if main_window:
            main_window.update_font_size()

    def update_font_size_label(self, level):
        size_names = {
            0: _("font_size_smallest"),
            1: _("font_size_small"),
            2: _("font_size_normal"),
            3: _("font_size_large"),
            4: _("font_size_largest"),
        }
        self.current_font_size_label.setText(
            size_names.get(level, _("font_size_normal")))

    def populate_modules(self):
        self.module_list_widget.clear()
        module_names = module_manager.get_module_names()
        for name in module_names:
            item_widget = QWidget()
            item_layout = QHBoxLayout(item_widget)
            item_layout.setContentsMargins(5, 2, 5, 2)

            label = QLabel(name)
            export_button = QPushButton(get_icon("fa5s.download"), "")
            export_button.setToolTip(_("export_module_tooltip"))
            export_button.clicked.connect(
                lambda _, n=name: self.export_module(n))

            item_layout.addWidget(label)
            item_layout.addStretch()
            item_layout.addWidget(export_button)

            list_item = QListWidgetItem(self.module_list_widget)
            list_item.setSizeHint(item_widget.sizeHint())
            self.module_list_widget.addItem(list_item)
            self.module_list_widget.setItemWidget(list_item, item_widget)

    def import_module(self):
        file_path, _unused = QFileDialog.getOpenFileName(
            self, _("import_module_dialog_title"), "", _("zip_files_filter"))
        if file_path:
            if module_manager.import_module(file_path):
                QMessageBox.information(self, _("import_success_title"),
                                        _("import_success_message"))
            else:
                QMessageBox.warning(self, _("import_error_title"),
                                    _("import_error_message"))

    def export_module(self, module_name):
        file_path, _unused = QFileDialog.getSaveFileName(
            self, _("export_module_dialog_title"), f"{module_name}.zip",
            _("zip_files_filter"))
        if file_path:
            if module_manager.export_module(module_name, file_path):
                QMessageBox.information(self, _("export_success_title"),
                                        _("export_success_message"))
            else:
                QMessageBox.warning(self, _("export_error_title"),
                                    _("export_error_message"))

    def retranslate_ui(self):
        # This method is called when the language changes
        self.findChild(QGroupBox, "appearance_language_group_title").setTitle(
            _("appearance_language_group_title"))
        self.findChild(QGroupBox, "module_management_group_title").setTitle(
            _("module_management_group_title"))

        self.theme_label.setText(_("theme_label"))
        self.language_label.setText(_("language_label"))
        self.font_family_label.setText(_("font_family_label"))
        self.font_size_label.setText(_("font_size_label"))
        self.update_font_size_label(self.font_size_slider.value())

        self.import_module_button.setText(_("import_module_button"))
        self.populate_modules()

    def __del__(self):
        try:
            global_signals.language_changed.disconnect(self.retranslate_ui)
            global_signals.modules_updated.disconnect(self.populate_modules)
        except TypeError:
            pass  # Signals already disconnected
