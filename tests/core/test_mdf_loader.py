"""MdfLoader のユニットテスト。"""

from pathlib import Path

from mdf_signal_inspector.core.mdf_loader import MdfLoader


class TestMdfLoader:
    def test_load_file(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            info = loader.get_file_info()
            assert info.path == sample_mdf_path
            assert info.signal_count == 4
            assert info.duration_s > 0

    def test_list_signals(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            signals = loader.list_signals()
            names = [s.name for s in signals]
            assert "Speed" in names
            assert "StuckZero" in names
            assert "StuckFortyTwo" in names
            assert "Temperature" in names
            # time チャンネルは除外されること
            assert "time" not in names

    def test_signal_metadata(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            signals = loader.list_signals()
            speed = next(s for s in signals if s.name == "Speed")
            assert speed.unit == "km/h"
            assert speed.sample_count == 1000

    def test_get_signal_data(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            data = loader.get_signal_data("Speed")
            assert data.name == "Speed"
            assert data.unit == "km/h"
            assert len(data.samples) == 1000
            assert len(data.timestamps) == 1000

    def test_empty_signal(self, empty_signal_mdf_path: Path) -> None:
        with MdfLoader(empty_signal_mdf_path) as loader:
            signals = loader.list_signals()
            empty = next(s for s in signals if s.name == "EmptySignal")
            assert empty.sample_count == 0
