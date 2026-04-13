"""MDF4ファイルの読み込みと信号メタデータ抽出。

asammdf は直接使わず mdf_signal_inspector.mdf ラッパーを介する。
PySide6 にも依存しない純粋な Python モジュール。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from mdf_signal_inspector.mdf import MdfFile, SignalData  # re-export SignalData

__all__ = ["FileInfo", "MdfLoader", "SignalData", "SignalInfo"]


@dataclass(frozen=True)
class SignalInfo:
    """信号のメタデータ。"""

    name: str
    unit: str
    sample_count: int


@dataclass(frozen=True)
class FileInfo:
    """MDFファイルの基本情報。"""

    path: Path
    start_time: datetime
    duration_s: float
    signal_count: int


class MdfLoader:
    """MDF4ファイルを読み込み、信号情報とデータを提供する。

    内部では mdf_signal_inspector.mdf.MdfFile を使用する。
    """

    def __init__(self, path: str | Path) -> None:
        self._file = MdfFile(path)

    def close(self) -> None:
        self._file.close()

    def __enter__(self) -> MdfLoader:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def get_file_info(self) -> FileInfo:
        """ファイルの基本情報を返す。"""
        signals = self.list_signals()
        return FileInfo(
            path=self._file.path,
            start_time=self._file.start_time,
            duration_s=self._calc_duration(),
            signal_count=len(signals),
        )

    def list_signals(self) -> list[SignalInfo]:
        """全信号のメタデータを一覧で返す。"""
        result: list[SignalInfo] = []
        for name in self._file.signal_names():
            sig = self._file.read_signal(name)
            result.append(SignalInfo(
                name=name,
                unit=sig.unit,
                sample_count=len(sig.samples),
            ))
        return result

    def get_signal_data(self, name: str) -> SignalData:
        """指定した信号名のデータを内挿なしで返す。"""
        return self._file.read_signal(name)

    def _calc_duration(self) -> float:
        """計測期間（秒）を計算する。"""
        for name in self._file.signal_names():
            sig = self._file.read_signal(name)
            if len(sig.timestamps) > 1:
                return float(sig.timestamps[-1] - sig.timestamps[0])
        return 0.0
