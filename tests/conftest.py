"""テスト用共通フィクスチャ。"""

from pathlib import Path

import numpy as np
import pytest
from asammdf import MDF, Signal


@pytest.fixture
def sample_mdf_path(tmp_path: Path) -> Path:
    """テスト用MDF4ファイルを生成して返す。

    含まれる信号:
    - Speed: 0〜100 の変動信号 (1000サンプル)
    - StuckZero: 全サンプル 0.0 の固着信号
    - StuckFortyTwo: 全サンプル 42.0 の固着信号
    - Temperature: 20〜80 の変動信号
    """
    mdf = MDF()
    t = np.linspace(0, 10, 1000)

    signals = [
        Signal(
            samples=np.linspace(0, 100, 1000),
            timestamps=t, name="Speed", unit="km/h",
        ),
        Signal(
            samples=np.zeros(1000),
            timestamps=t, name="StuckZero", unit="V",
        ),
        Signal(
            samples=np.full(1000, 42.0),
            timestamps=t, name="StuckFortyTwo", unit="deg",
        ),
        Signal(
            samples=np.linspace(20, 80, 1000),
            timestamps=t, name="Temperature", unit="degC",
        ),
    ]
    mdf.append(signals)

    path = tmp_path / "test.mf4"
    mdf.save(str(path), overwrite=True)
    mdf.close()
    return path


@pytest.fixture
def empty_signal_mdf_path(tmp_path: Path) -> Path:
    """空の信号を含むMDF4ファイル。"""
    mdf = MDF()
    sig = Signal(
        samples=np.array([], dtype=np.float64),
        timestamps=np.array([], dtype=np.float64),
        name="EmptySignal",
        unit="V",
    )
    mdf.append([sig])

    path = tmp_path / "empty.mf4"
    mdf.save(str(path), overwrite=True)
    mdf.close()
    return path
