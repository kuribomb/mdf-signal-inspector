"""テスト用 MDF4 ファイル生成ユーティリティ。

このモジュールも asammdf を使うが、テスト専用。
プロダクションコードからは import しないこと。
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

import numpy as np
from asammdf import MDF as _MDF  # テスト用途のみ
from asammdf import Signal as _Signal


class SignalSpec(NamedTuple):
    """テスト信号の仕様。"""

    name: str
    samples: np.ndarray
    timestamps: np.ndarray
    unit: str = ""


def create_mdf4(specs: list[SignalSpec], path: str | Path) -> Path:
    """指定した信号を含む MDF4 ファイルを生成する。

    Args:
        specs: 生成する信号の仕様リスト。
        path: 出力先ファイルパス。

    Returns:
        生成したファイルのパス。
    """
    mdf = _MDF()
    signals = [
        _Signal(
            samples=spec.samples,
            timestamps=spec.timestamps,
            name=spec.name,
            unit=spec.unit,
        )
        for spec in specs
    ]
    mdf.append(signals)
    out = Path(path)
    mdf.save(str(out), overwrite=True)
    mdf.close()
    return out
