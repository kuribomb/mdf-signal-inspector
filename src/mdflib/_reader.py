"""asammdf のラッパー実装。

このファイルのみ asammdf を import する。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from asammdf import MDF as _MDF  # このファイル内でのみ使用


@dataclass(frozen=True)
class SignalData:
    """信号の生データ（内挿なし）。"""

    name: str
    unit: str
    timestamps: np.ndarray
    samples: np.ndarray


class MdfFile:
    """MDF4ファイルへのシンプルなアクセスを提供する。

    asammdf の複雑な channels_db やグループ/インデックス管理を隠蔽し、
    信号名をキーとした直感的な API を提供する。

    使用例::

        with MdfFile("log.mf4") as mdf:
            names = mdf.filter_signals("Speed")
            mdf.export_csv(names, "out.csv")
    """

    def __init__(self, path: str | Path) -> None:
        self._path = Path(path)
        self._mdf = _MDF(str(self._path))

    def __enter__(self) -> MdfFile:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def close(self) -> None:
        """ファイルを閉じる。"""
        self._mdf.close()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def start_time(self):  # noqa: ANN201
        """計測開始日時（datetime）。"""
        return self._mdf.header.start_time

    # ------------------------------------------------------------------
    # 信号一覧・フィルタ
    # ------------------------------------------------------------------

    def signal_names(self) -> list[str]:
        """全信号名をアルファベット順で返す（'time' チャンネルを除く）。"""
        return sorted(
            name for name in self._mdf.channels_db if name != "time"
        )

    def filter_signals(self, keyword: str) -> list[str]:
        """キーワードを含む信号名を返す（大文字小文字区別なし）。

        Args:
            keyword: 検索キーワード。空文字列の場合は全信号を返す。

        Returns:
            マッチした信号名のリスト（アルファベット順）。
        """
        if not keyword:
            return self.signal_names()
        kw = keyword.lower()
        return [name for name in self.signal_names() if kw in name.lower()]

    # ------------------------------------------------------------------
    # データ読み込み
    # ------------------------------------------------------------------

    def read_signal(self, name: str) -> SignalData:
        """信号データを内挿なしで取得する。

        asammdf の get() を直接呼び出し、共通時刻軸への再サンプリングは行わない。
        timestamps / samples はそのまま返す。

        Args:
            name: 信号名。

        Returns:
            SignalData（timestamps と samples は元データのまま）。
        """
        sig = self._mdf.get(name)
        return SignalData(
            name=sig.name,
            unit=sig.unit,
            timestamps=sig.timestamps.copy(),
            samples=sig.samples.copy(),
        )

    # ------------------------------------------------------------------
    # CSV 出力
    # ------------------------------------------------------------------

    def export_csv(self, signal_names: list[str], path: str | Path) -> None:
        """指定した信号を内挿なしで CSV に出力する。

        各信号のサンプルをそのまま出力する。
        共通時刻軸への再サンプリング（内挿）は行わない。

        出力フォーマット（ロング形式）::

            signal_name, timestamp, value, unit
            Speed,       0.000,    10.5,  km/h
            Speed,       0.010,    10.6,  km/h
            Throttle,    0.000,    15.0,  %
            ...

        Args:
            signal_names: 出力する信号名のリスト。
            path: 出力先 CSV ファイルのパス。
        """
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["signal_name", "timestamp", "value", "unit"])
            for name in signal_names:
                sig = self.read_signal(name)
                for t, v in zip(sig.timestamps, sig.samples):
                    writer.writerow([name, float(t), _to_python(v), sig.unit])


def _to_python(value: object) -> object:
    """numpy スカラーを Python ネイティブ型に変換する（CSV 出力用）。"""
    if isinstance(value, (np.floating, np.integer)):
        return value.item()
    return value
