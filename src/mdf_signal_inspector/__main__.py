"""MDF Signal Inspector エントリポイント。"""

import sys

from PySide6.QtWidgets import QApplication

from mdf_signal_inspector.ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
