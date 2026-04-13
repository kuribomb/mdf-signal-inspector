"""PySide6 メインウィンドウ。

ビジネスロジックは持たず、core モジュールへの委譲のみ。
"""

from __future__ import annotations

import re
from pathlib import Path

from PySide6.QtCore import (
    QAbstractTableModel,
    QModelIndex,
    QObject,
    Qt,
    QThread,
    Signal,
)
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStatusBar,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from mdf_signal_inspector.core.mdf_loader import MdfLoader
from mdf_signal_inspector.core.stuck_detector import (
    StuckCheckRow,
    StuckResult,
    export_csv,
    filter_signals_by_regex,
    run_stuck_check,
)

# ---------------------------------------------------------------------------
# テーブルモデル
# ---------------------------------------------------------------------------

_HEADERS = ["信号名", "判定", "固着値", "サンプル数"]


class ResultTableModel(QAbstractTableModel):
    """固着チェック結果のテーブルモデル。"""

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._rows: list[StuckCheckRow] = []

    def rowCount(self, parent: QModelIndex | None = None) -> int:
        return len(self._rows)

    def columnCount(self, parent: QModelIndex | None = None) -> int:
        return len(_HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):  # type: ignore[override]
        if not index.isValid():
            return None
        row = self._rows[index.row()]
        col = index.column()
        if role == Qt.ItemDataRole.DisplayRole:
            return self._display_data(row, col)
        if role == Qt.ItemDataRole.ForegroundRole:
            return self._foreground_data(row, col)
        return None

    def _display_data(self, row: StuckCheckRow, col: int) -> str | None:
        match col:
            case 0:
                return row.signal_name
            case 1:
                return row.result.value
            case 2:
                return str(row.stuck_value) if row.stuck_value is not None else "-"
            case 3:
                return str(row.sample_count)
        return None

    def _foreground_data(self, row: StuckCheckRow, col: int):
        from PySide6.QtGui import QColor

        if col != 1:
            return None
        if row.result == StuckResult.FAIL:
            return QColor("red")
        if row.result == StuckResult.OK:
            return QColor("green")
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ):
        if (
            role == Qt.ItemDataRole.DisplayRole
            and orientation == Qt.Orientation.Horizontal
        ):
            return _HEADERS[section]
        return None

    def update_data(self, rows: list[StuckCheckRow]) -> None:
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()

    @property
    def rows(self) -> list[StuckCheckRow]:
        return list(self._rows)


# ---------------------------------------------------------------------------
# バックグラウンドワーカー
# ---------------------------------------------------------------------------


class LoadWorker(QObject):
    """MDF4ファイルの読み込みをバックグラウンドで実行する。"""

    finished = Signal(object)  # MdfLoader
    error = Signal(str)

    def __init__(self, path: str) -> None:
        super().__init__()
        self._path = path

    def run(self) -> None:
        try:
            loader = MdfLoader(self._path)
            self.finished.emit(loader)
        except Exception as e:
            self.error.emit(str(e))


class StuckCheckWorker(QObject):
    """固着チェックをバックグラウンドで実行する。"""

    finished = Signal(list)  # list[StuckCheckRow]
    error = Signal(str)

    def __init__(self, loader: MdfLoader, pattern: str) -> None:
        super().__init__()
        self._loader = loader
        self._pattern = pattern

    def run(self) -> None:
        try:
            signals = self._loader.list_signals()
            filtered = filter_signals_by_regex(signals, self._pattern)
            results = run_stuck_check(self._loader, filtered)
            self.finished.emit(results)
        except re.error as e:
            self.error.emit(f"正規表現エラー: {e}")
        except Exception as e:
            self.error.emit(str(e))


# ---------------------------------------------------------------------------
# メインウィンドウ
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("MDF Signal Inspector")
        self.setMinimumSize(800, 500)

        self._loader: MdfLoader | None = None
        self._worker_thread: QThread | None = None
        self._model = ResultTableModel(self)

        self._build_ui()

    # ---- UI構築 ----

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # ファイル選択行
        file_row = QHBoxLayout()
        self._btn_open = QPushButton("ファイルを開く")
        self._btn_open.clicked.connect(self._on_open_file)
        self._lbl_file = QLabel("ファイル未選択")
        file_row.addWidget(self._btn_open)
        file_row.addWidget(self._lbl_file, 1)
        layout.addLayout(file_row)

        # ファイル情報行
        self._lbl_info = QLabel("")
        layout.addWidget(self._lbl_info)

        # フィルタ行
        filter_row = QHBoxLayout()
        filter_row.addWidget(QLabel("信号フィルタ（正規表現）:"))
        self._txt_filter = QLineEdit()
        self._txt_filter.setPlaceholderText("例: ECU1_.*")
        filter_row.addWidget(self._txt_filter, 1)
        layout.addLayout(filter_row)

        # ボタン行
        btn_row = QHBoxLayout()
        self._btn_check = QPushButton("固着チェック実行")
        self._btn_check.setEnabled(False)
        self._btn_check.clicked.connect(self._on_run_check)
        self._btn_csv = QPushButton("CSV保存")
        self._btn_csv.setEnabled(False)
        self._btn_csv.clicked.connect(self._on_export_csv)
        btn_row.addWidget(self._btn_check)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_csv)
        layout.addLayout(btn_row)

        # 結果テーブル
        self._table = QTableView()
        self._table.setModel(self._model)
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSortingEnabled(False)
        layout.addWidget(self._table)

        # ステータスバー
        self._status = QStatusBar()
        self.setStatusBar(self._status)

    # ---- イベントハンドラ ----

    def _on_open_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            "MDF4ファイルを選択",
            "",
            "MDF4 Files (*.mf4 *.mdf);;All Files (*)",
        )
        if not path:
            return
        self._start_load(path)

    def _start_load(self, path: str) -> None:
        self._btn_open.setEnabled(False)
        self._btn_check.setEnabled(False)
        self._status.showMessage("ファイルを読み込み中...")

        thread = QThread()
        worker = LoadWorker(path)
        worker.moveToThread(thread)
        worker.finished.connect(lambda loader: self._on_load_finished(loader))
        worker.error.connect(lambda msg: self._on_load_error(msg))
        self._start_worker(thread, worker)

    def _on_load_finished(self, loader: MdfLoader) -> None:
        if self._loader is not None:
            self._loader.close()
        self._loader = loader

        info = loader.get_file_info()
        self._lbl_file.setText(f"ファイル名: {info.path.name}")
        self._lbl_info.setText(
            f"記録時間: {info.duration_s:.1f} s   信号数: {info.signal_count}"
        )
        self._btn_open.setEnabled(True)
        self._btn_check.setEnabled(True)
        self._model.update_data([])
        self._btn_csv.setEnabled(False)
        self._status.showMessage("読み込み完了", 3000)

    def _on_load_error(self, msg: str) -> None:
        self._btn_open.setEnabled(True)
        self._status.showMessage("")
        QMessageBox.critical(self, "読み込みエラー", msg)

    def _on_run_check(self) -> None:
        if self._loader is None:
            return

        pattern = self._txt_filter.text().strip()
        if not self._validate_regex(pattern):
            return

        self._btn_check.setEnabled(False)
        self._status.showMessage("固着チェック実行中...")

        thread = QThread()
        worker = StuckCheckWorker(self._loader, pattern)
        worker.moveToThread(thread)
        worker.finished.connect(lambda rows: self._on_check_finished(rows))
        worker.error.connect(lambda msg: self._on_check_error(msg))
        self._start_worker(thread, worker)

    def _validate_regex(self, pattern: str) -> bool:
        """正規表現を検証する。エラー時はUIにフィードバックして False を返す。"""
        if not pattern:
            self._txt_filter.setStyleSheet("")
            return True
        try:
            re.compile(pattern)
            self._txt_filter.setStyleSheet("")
            return True
        except re.error as e:
            self._txt_filter.setStyleSheet("background-color: #ffcccc;")
            self._status.showMessage(f"正規表現エラー: {e}")
            return False

    def _start_worker(self, thread: QThread, worker: QObject) -> None:
        """QThread + Worker を起動する共通処理。"""
        thread.started.connect(worker.run)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.error.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        self._worker_thread = thread
        thread.start()

    def _on_check_finished(self, rows: list[StuckCheckRow]) -> None:
        self._model.update_data(rows)
        self._btn_check.setEnabled(True)
        self._btn_csv.setEnabled(len(rows) > 0)

        fail_count = sum(1 for r in rows if r.result == StuckResult.FAIL)
        self._status.showMessage(
            f"完了: {len(rows)} 信号中 {fail_count} 件が固着", 5000
        )

    def _on_check_error(self, msg: str) -> None:
        self._btn_check.setEnabled(True)
        self._status.showMessage("")
        QMessageBox.critical(self, "チェックエラー", msg)

    def _on_export_csv(self) -> None:
        rows = self._model.rows
        if not rows:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "CSV保存先を選択",
            "stuck_check_result.csv",
            "CSV Files (*.csv);;All Files (*)",
        )
        if not path:
            return
        try:
            export_csv(rows, path)
            self._status.showMessage(f"CSV保存完了: {Path(path).name}", 3000)
        except Exception as e:
            QMessageBox.critical(self, "CSV保存エラー", str(e))

    def closeEvent(self, event) -> None:  # type: ignore[override]
        if self._loader is not None:
            self._loader.close()
        super().closeEvent(event)
