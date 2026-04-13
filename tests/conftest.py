"""テスト用共通フィクスチャ。"""

from pathlib import Path

import numpy as np
import pytest

from mdflib._testing import SignalSpec, create_mdf4


@pytest.fixture
def sample_mdf_path(tmp_path: Path) -> Path:
    """テスト用MDF4ファイルを生成して返す。

    含まれる信号:
    - Speed: 0〜100 の変動信号 (1000サンプル)
    - StuckZero: 全サンプル 0.0 の固着信号
    - StuckFortyTwo: 全サンプル 42.0 の固着信号
    - Temperature: 20〜80 の変動信号
    """
    t = np.linspace(0, 10, 1000)
    specs = [
        SignalSpec("Speed", np.linspace(0, 100, 1000), t, "km/h"),
        SignalSpec("StuckZero", np.zeros(1000), t, "V"),
        SignalSpec("StuckFortyTwo", np.full(1000, 42.0), t, "deg"),
        SignalSpec("Temperature", np.linspace(20, 80, 1000), t, "degC"),
    ]
    return create_mdf4(specs, tmp_path / "test.mf4")


@pytest.fixture
def empty_signal_mdf_path(tmp_path: Path) -> Path:
    """空の信号を含むMDF4ファイル。"""
    specs = [
        SignalSpec(
            "EmptySignal",
            np.array([], dtype=np.float64),
            np.array([], dtype=np.float64),
            "V",
        ),
    ]
    return create_mdf4(specs, tmp_path / "empty.mf4")
