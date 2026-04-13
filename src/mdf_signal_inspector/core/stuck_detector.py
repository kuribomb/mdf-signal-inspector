"""信号の固着（スタック）判定ロジック。

PySide6 に依存しない純粋な Python モジュール。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum

import numpy as np

from .mdf_loader import MdfLoader, SignalInfo


class StuckResult(Enum):
    """固着判定の結果。"""

    OK = "OK"
    FAIL = "FAIL"
    NA = "N/A"


@dataclass(frozen=True)
class StuckCheckRow:
    """固着チェック結果の1行。"""

    signal_name: str
    result: StuckResult
    stuck_value: float | None
    sample_count: int


def filter_signals_by_regex(
    signals: list[SignalInfo], pattern: str
) -> list[SignalInfo]:
    """正規表現パターンで信号名をフィルタリングする。

    Args:
        signals: 全信号リスト
        pattern: 正規表現パターン（空文字列の場合は全信号を返す）

    Returns:
        マッチした信号のリスト

    Raises:
        re.error: 正規表現が不正な場合
    """
    if not pattern:
        return list(signals)
    compiled = re.compile(pattern)
    return [s for s in signals if compiled.search(s.name)]


def check_stuck(samples: np.ndarray) -> tuple[StuckResult, float | None]:
    """1信号分のサンプルデータに対して固着判定を行う。

    Args:
        samples: 信号のサンプル値配列

    Returns:
        (判定結果, 固着値)
        - OK の場合: (StuckResult.OK, None)
        - FAIL の場合: (StuckResult.FAIL, 固着値)
        - N/A の場合: (StuckResult.NA, None)
    """
    if len(samples) == 0:
        return StuckResult.NA, None

    # NaN のみのデータ
    valid = samples[~np.isnan(samples)] if samples.dtype.kind == "f" else samples
    if len(valid) == 0:
        return StuckResult.NA, None

    min_val = np.min(valid)
    max_val = np.max(valid)

    if min_val == max_val:
        return StuckResult.FAIL, float(min_val)
    return StuckResult.OK, None


def run_stuck_check(
    loader: MdfLoader,
    signals: list[SignalInfo],
) -> list[StuckCheckRow]:
    """指定された信号リストに対して固着チェックを実行する。

    Args:
        loader: MDFファイルローダー
        signals: チェック対象の信号リスト

    Returns:
        チェック結果のリスト
    """
    results: list[StuckCheckRow] = []
    for sig_info in signals:
        sig_data = loader.get_signal_data(sig_info.name)
        result, stuck_value = check_stuck(sig_data.samples)
        results.append(
            StuckCheckRow(
                signal_name=sig_info.name,
                result=result,
                stuck_value=stuck_value,
                sample_count=len(sig_data.samples),
            )
        )
    return results


def export_csv(rows: list[StuckCheckRow], path: str) -> None:
    """固着チェック結果をCSVファイルに出力する。

    Args:
        rows: チェック結果リスト
        path: 出力先ファイルパス
    """
    import csv

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["signal_name", "result", "stuck_value", "sample_count"])
        for row in rows:
            writer.writerow([
                row.signal_name,
                row.result.value,
                row.stuck_value if row.stuck_value is not None else "",
                row.sample_count,
            ])
