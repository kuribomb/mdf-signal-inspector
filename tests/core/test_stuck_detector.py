"""固着判定ロジックのユニットテスト。"""

from pathlib import Path

import numpy as np
import pytest

from mdf_signal_inspector.core.mdf_loader import MdfLoader, SignalInfo
from mdf_signal_inspector.core.stuck_detector import (
    StuckCheckRow,
    StuckResult,
    check_stuck,
    export_csv,
    filter_signals_by_regex,
    run_stuck_check,
)


class TestCheckStuck:
    def test_varying_signal_is_ok(self) -> None:
        samples = np.array([1.0, 2.0, 3.0, 4.0])
        result, value = check_stuck(samples)
        assert result == StuckResult.OK
        assert value is None

    def test_constant_signal_is_fail(self) -> None:
        samples = np.array([42.0, 42.0, 42.0])
        result, value = check_stuck(samples)
        assert result == StuckResult.FAIL
        assert value == 42.0

    def test_zero_stuck(self) -> None:
        samples = np.zeros(100)
        result, value = check_stuck(samples)
        assert result == StuckResult.FAIL
        assert value == 0.0

    def test_single_sample_is_fail(self) -> None:
        samples = np.array([7.0])
        result, value = check_stuck(samples)
        assert result == StuckResult.FAIL
        assert value == 7.0

    def test_empty_signal_is_na(self) -> None:
        samples = np.array([], dtype=np.float64)
        result, value = check_stuck(samples)
        assert result == StuckResult.NA
        assert value is None

    def test_all_nan_is_na(self) -> None:
        samples = np.array([np.nan, np.nan, np.nan])
        result, value = check_stuck(samples)
        assert result == StuckResult.NA
        assert value is None

    def test_nan_with_constant_is_fail(self) -> None:
        samples = np.array([np.nan, 5.0, 5.0, np.nan])
        result, value = check_stuck(samples)
        assert result == StuckResult.FAIL
        assert value == 5.0

    def test_nan_with_varying_is_ok(self) -> None:
        samples = np.array([np.nan, 1.0, 2.0, np.nan])
        result, value = check_stuck(samples)
        assert result == StuckResult.OK
        assert value is None

    def test_integer_signal(self) -> None:
        samples = np.array([3, 3, 3], dtype=np.int32)
        result, value = check_stuck(samples)
        assert result == StuckResult.FAIL
        assert value == 3.0


class TestFilterSignalsByRegex:
    @pytest.fixture
    def signals(self) -> list[SignalInfo]:
        return [
            SignalInfo("ECU1_Speed", "km/h", 100, 0, 1),
            SignalInfo("ECU1_Throttle", "%", 100, 0, 2),
            SignalInfo("ECU2_BrakePress", "bar", 100, 0, 3),
            SignalInfo("Temperature", "degC", 100, 0, 4),
        ]

    def test_empty_pattern_returns_all(self, signals: list[SignalInfo]) -> None:
        result = filter_signals_by_regex(signals, "")
        assert len(result) == 4

    def test_exact_prefix_match(self, signals: list[SignalInfo]) -> None:
        result = filter_signals_by_regex(signals, "^ECU1_")
        assert len(result) == 2
        assert all(s.name.startswith("ECU1_") for s in result)

    def test_partial_match(self, signals: list[SignalInfo]) -> None:
        result = filter_signals_by_regex(signals, "Temp")
        assert len(result) == 1
        assert result[0].name == "Temperature"

    def test_no_match(self, signals: list[SignalInfo]) -> None:
        result = filter_signals_by_regex(signals, "^NonExistent$")
        assert len(result) == 0

    def test_invalid_regex_raises(self, signals: list[SignalInfo]) -> None:
        with pytest.raises(Exception):
            filter_signals_by_regex(signals, "[invalid")


class TestRunStuckCheck:
    def test_integration(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            signals = loader.list_signals()
            results = run_stuck_check(loader, signals)

            assert len(results) == 4
            by_name = {r.signal_name: r for r in results}

            assert by_name["Speed"].result == StuckResult.OK
            assert by_name["Temperature"].result == StuckResult.OK
            assert by_name["StuckZero"].result == StuckResult.FAIL
            assert by_name["StuckZero"].stuck_value == 0.0
            assert by_name["StuckFortyTwo"].result == StuckResult.FAIL
            assert by_name["StuckFortyTwo"].stuck_value == 42.0

    def test_with_regex_filter(self, sample_mdf_path: Path) -> None:
        with MdfLoader(sample_mdf_path) as loader:
            signals = loader.list_signals()
            filtered = filter_signals_by_regex(signals, "^Stuck")
            results = run_stuck_check(loader, filtered)
            assert len(results) == 2
            assert all(r.result == StuckResult.FAIL for r in results)


class TestExportCsv:
    def test_export(self, tmp_path: Path) -> None:
        rows = [
            StuckCheckRow("Speed", StuckResult.OK, None, 1000),
            StuckCheckRow("Stuck", StuckResult.FAIL, 42.0, 1000),
            StuckCheckRow("Empty", StuckResult.NA, None, 0),
        ]
        csv_path = tmp_path / "result.csv"
        export_csv(rows, str(csv_path))

        lines = csv_path.read_text(encoding="utf-8").strip().split("\n")
        assert len(lines) == 4  # header + 3 rows
        assert lines[0] == "signal_name,result,stuck_value,sample_count"
        assert "FAIL" in lines[2]
        assert "42.0" in lines[2]
