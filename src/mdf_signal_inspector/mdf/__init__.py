"""asammdf ラッパーライブラリ。

このパッケージのみ asammdf を import する。
asammdf の複雑な API を隠蔽し、必要な操作だけを提供する。

公開 API:
    MdfFile  - MDF4ファイルの読み込み・フィルタ・CSV出力
    SignalData - 信号の生データ（内挿なし）
"""

from ._reader import MdfFile, SignalData

__all__ = ["MdfFile", "SignalData"]
