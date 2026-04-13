"""MdfFile ラッパーのユニットテスト。"""

from pathlib import Path

from mdf_signal_inspector.mdf import MdfFile


class TestMdfFileSignalNames:
    def test_returns_all_signals(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            names = mdf.signal_names()
            assert set(names) == {"Speed", "StuckZero", "StuckFortyTwo", "Temperature"}

    def test_excludes_time_channel(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            assert "time" not in mdf.signal_names()

    def test_sorted_alphabetically(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            names = mdf.signal_names()
            assert names == sorted(names)


class TestMdfFileFilterSignals:
    def test_empty_keyword_returns_all(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            assert mdf.filter_signals("") == mdf.signal_names()

    def test_keyword_match_case_insensitive(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            assert mdf.filter_signals("stuck") == mdf.filter_signals("STUCK")

    def test_keyword_partial_match(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            result = mdf.filter_signals("Stuck")
            assert set(result) == {"StuckZero", "StuckFortyTwo"}

    def test_keyword_no_match(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            assert mdf.filter_signals("XYZ_NotExist") == []


class TestMdfFileReadSignal:
    def test_read_returns_correct_shape(self, sample_mdf_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            sig = mdf.read_signal("Speed")
            assert len(sig.samples) == 1000
            assert len(sig.timestamps) == 1000

    def test_no_interpolation_preserves_raw_timestamps(
        self, sample_mdf_path: Path
    ) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            sig = mdf.read_signal("Speed")
            # タイムスタンプが元データのまま（0〜10秒、1000点）
            assert abs(float(sig.timestamps[0]) - 0.0) < 1e-6
            assert abs(float(sig.timestamps[-1]) - 10.0) < 1e-6

    def test_empty_signal(self, empty_signal_mdf_path: Path) -> None:
        with MdfFile(empty_signal_mdf_path) as mdf:
            sig = mdf.read_signal("EmptySignal")
            assert len(sig.samples) == 0
            assert len(sig.timestamps) == 0


class TestMdfFileExportCsv:
    def test_csv_header(self, sample_mdf_path: Path, tmp_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            mdf.export_csv(["Speed"], tmp_path / "out.csv")
        lines = (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()
        assert lines[0] == "signal_name,timestamp,value,unit"

    def test_csv_row_count(self, sample_mdf_path: Path, tmp_path: Path) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            mdf.export_csv(["Speed"], tmp_path / "out.csv")
        lines = (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()
        assert len(lines) == 1 + 1000  # header + 1000 samples

    def test_csv_multi_signal_no_interpolation(
        self, sample_mdf_path: Path, tmp_path: Path
    ) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            mdf.export_csv(["Speed", "Temperature"], tmp_path / "out.csv")
        lines = (tmp_path / "out.csv").read_text(encoding="utf-8").splitlines()
        # 2信号 × 1000サンプル + ヘッダー
        assert len(lines) == 1 + 2000

    def test_csv_contains_signal_name(
        self, sample_mdf_path: Path, tmp_path: Path
    ) -> None:
        with MdfFile(sample_mdf_path) as mdf:
            mdf.export_csv(["Speed"], tmp_path / "out.csv")
        content = (tmp_path / "out.csv").read_text(encoding="utf-8")
        assert "Speed" in content
