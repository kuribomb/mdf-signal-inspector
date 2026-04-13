"""MDF4ファイルの読み込みと信号メタデータ抽出。

PySide6 に依存しない純粋な Python モジュール。
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
from asammdf import MDF


@dataclass(frozen=True)
class SignalInfo:
    """信号のメタデータ。"""

    name: str
    unit: str
    sample_count: int
    group_index: int
    channel_index: int


@dataclass(frozen=True)
class FileInfo:
    """MDFファイルの基本情報。"""

    path: Path
    start_time: datetime
    duration_s: float
    signal_count: int


@dataclass(frozen=True)
class SignalData:
    """信号の値データ。"""

    name: str
    unit: str
    samples: np.ndarray
    timestamps: np.ndarray


class MdfLoader:
    """MDF4ファイルを読み込み、信号情報とデータを提供する。"""

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._mdf = MDF(self._path)

    def close(self) -> None:
        self._mdf.close()

    def __enter__(self) -> MdfLoader:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def get_file_info(self) -> FileInfo:
        """ファイルの基本情報を返す。"""
        signals = self.list_signals()
        duration = self._calc_duration()
        return FileInfo(
            path=self._path,
            start_time=self._mdf.header.start_time,
            duration_s=duration,
            signal_count=len(signals),
        )

    def list_signals(self) -> list[SignalInfo]:
        """全信号のメタデータを一覧で返す。"""
        signals: list[SignalInfo] = []
        for name, occurrences in self._mdf.channels_db.items():
            if name == "time":
                continue
            group_idx, channel_idx = occurrences[0]
            channel = self._mdf.groups[group_idx].channels[channel_idx]
            # サンプル数はグループのデータブロックから取得
            try:
                sig = self._mdf.get(
                    name, group=group_idx, index=channel_idx, raw=True
                )
                sample_count = len(sig.samples)
            except Exception:
                sample_count = 0
            signals.append(
                SignalInfo(
                    name=name,
                    unit=channel.unit,
                    sample_count=sample_count,
                    group_index=group_idx,
                    channel_index=channel_idx,
                )
            )
        return sorted(signals, key=lambda s: s.name)

    def get_signal_data(self, name: str) -> SignalData:
        """指定した信号名のデータを返す。"""
        sig = self._mdf.get(name)
        return SignalData(
            name=sig.name,
            unit=sig.unit,
            samples=sig.samples,
            timestamps=sig.timestamps,
        )

    def _calc_duration(self) -> float:
        """計測期間（秒）を計算する。"""
        for _name, occurrences in self._mdf.channels_db.items():
            if _name == "time":
                continue
            group_idx, channel_idx = occurrences[0]
            duration = self._read_duration(_name, group_idx, channel_idx)
            if duration is not None:
                return duration
        return 0.0

    def _read_duration(
        self, name: str, group_idx: int, channel_idx: int
    ) -> float | None:
        """1信号からタイムスタンプ幅を読み取る。読めない場合は None。"""
        try:
            sig = self._mdf.get(name, group=group_idx, index=channel_idx, raw=True)
        except Exception:
            return None
        if len(sig.timestamps) > 1:
            return float(sig.timestamps[-1] - sig.timestamps[0])
        return None
