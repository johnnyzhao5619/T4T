import os
import logging
import markdown
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextBrowser

logger = logging.getLogger(__name__)


class HelpWidget(QWidget):
    """
    A widget to display the user manual from a Markdown file.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(0, 0, 0, 0)

        self.text_browser = QTextBrowser()
        self.text_browser.setOpenExternalLinks(True)
        self.layout().addWidget(self.text_browser)

        self.load_manual()

    def load_manual_from_file(self, manual_path):
        """
        Loads and displays the user manual from the given file path.
        """
        try:
            if os.path.exists(manual_path):
                with open(manual_path, 'r', encoding='utf-8') as f:
                    md_content = f.read()
                html_content = markdown.markdown(
                    md_content, extensions=['fenced_code', 'tables'])
                self.text_browser.setHtml(html_content)
            else:
                error_msg = (
                    "<h1>Error</h1>"
                    f"<p>User manual file not found at: {manual_path}</p>")
                self.text_browser.setHtml(error_msg)
                logger.error(f"User manual not found at {manual_path}")
        except Exception as e:
            error_msg = (
                "<h1>Error</h1>"
                f"<p>Could not load user manual.</p><p>Reason: {e}</p>")
            self.text_browser.setHtml(error_msg)
            logger.exception("Failed to load and render user manual.")

    def load_manual(self, manual_name="user_manual.md"):
        """
        Loads and displays the user manual from docs/, with i18n support.
        """
        try:
            from utils.i18n import language_manager
            lang = language_manager.current_language
            base_name, ext = os.path.splitext(manual_name)

            app_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

            manual_path_i18n = os.path.join(app_root, 'docs', f"{base_name}.{lang}{ext}")
            manual_path_default = os.path.join(app_root, 'docs', manual_name)

            final_path = manual_path_i18n if os.path.exists(manual_path_i18n) else manual_path_default

            self.load_manual_from_file(final_path)
        except Exception as e:
            error_msg = (
                "<h1>Error</h1>"
                f"<p>Could not load user manual.</p><p>Reason: {e}</p>")
            self.text_browser.setHtml(error_msg)
            logger.exception("Failed to load and render user manual.")
