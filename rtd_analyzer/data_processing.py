from __future__ import annotations

from dataclasses import dataclass
import io
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


CHANNEL_PREFIX = "Wylew "


@dataclass(frozen=True)
class TransitionResult:
    channel: str
    t_02: float | None
    t_08: float | None
    delta_t: float | None
    status: str


def _try_read_csv(data: bytes, encoding: str) -> pd.DataFrame:
    return pd.read_csv(
        io.BytesIO(data),
        sep=";",
        decimal=",",
        encoding=encoding,
    )


def load_measurements(source: str | Path | bytes) -> pd.DataFrame:
    if isinstance(source, (str, Path)):
        raw = Path(source).read_bytes()
    else:
        raw = source

    last_error: Exception | None = None
    for enc in ("utf-8", "cp1250", "latin-1"):
        try:
            df = _try_read_csv(raw, enc)
            break
        except Exception as exc:  # noqa: PERF203
            last_error = exc
    else:
        raise ValueError("Nie udało się wczytać pliku CSV.") from last_error

    if "Nr" not in df.columns:
        raise ValueError("Brak kolumny 'Nr' w danych wejściowych.")

    channel_cols = [col for col in df.columns if "Przewodnosc" in str(col)]
    if len(channel_cols) < 2:
        raise ValueError("Wymagane są co najmniej 2 kanały przewodności.")

    ordered_cols = ["Nr"]
    if "Data i czas" in df.columns:
        ordered_cols.append("Data i czas")
    ordered_cols.extend(channel_cols)
    out = df[ordered_cols].copy()

    rename_map = {
        column_name: f"{CHANNEL_PREFIX}{idx + 1}"
        for idx, column_name in enumerate(channel_cols)
    }
    out = out.rename(columns=rename_map)

    for col in out.columns:
        if col.startswith(CHANNEL_PREFIX):
            out[col] = pd.to_numeric(out[col], errors="coerce")

    out = out.dropna(subset=[c for c in out.columns if c.startswith(CHANNEL_PREFIX)])
    out = out.reset_index(drop=True)
    return out


def channel_columns(df: pd.DataFrame) -> list[str]:
    return [c for c in df.columns if c.startswith(CHANNEL_PREFIX)]


def prepare_experiment_window(
    df: pd.DataFrame,
    discard_rows: int,
    start_offset: int,
    sample_interval_s: float = 0.3,
) -> pd.DataFrame:
    if discard_rows < 0 or start_offset < 0:
        raise ValueError("Liczba odrzucanych wierszy nie może być ujemna.")

    start_idx = discard_rows + start_offset
    if start_idx >= len(df):
        raise ValueError("Po odrzuceniu danych nie pozostały żadne pomiary.")

    out = df.iloc[start_idx:].copy().reset_index(drop=True)
    out["czas_s"] = np.arange(len(out), dtype=float) * sample_interval_s
    return out


def normalize_dimensionless(
    df: pd.DataFrame,
    channels: Iterable[str],
    c_infinity_mode: str,
) -> pd.DataFrame:
    selected = list(channels)
    if not selected:
        raise ValueError("Wybierz przynajmniej jeden kanał.")

    if c_infinity_mode not in {"max", "last"}:
        raise ValueError("Nieznany tryb C∞.")

    out = pd.DataFrame({"czas_s": df["czas_s"]})
    for channel in selected:
        c0 = float(df[channel].iloc[0])
        c_inf = float(df[channel].max() if c_infinity_mode == "max" else df[channel].iloc[-1])
        denominator = c_inf - c0
        if np.isclose(denominator, 0.0):
            raise ValueError(
                f"Nie można znormalizować kanału {channel}: C∞ i C0 są równe."
            )
        out[channel] = (df[channel] - c0) / denominator
    return out


def _crossing_time(time_s: np.ndarray, values: np.ndarray, target: float) -> float | None:
    for i in range(len(values) - 1):
        y1, y2 = values[i], values[i + 1]
        if np.isnan(y1) or np.isnan(y2):
            continue
        if y1 == target:
            return float(time_s[i])
        if (y1 - target) * (y2 - target) < 0 or y2 == target:
            t1, t2 = time_s[i], time_s[i + 1]
            if y2 == y1:
                return float(t1)
            alpha = (target - y1) / (y2 - y1)
            return float(t1 + alpha * (t2 - t1))
    return None


def compute_transition_zones(
    df_dimensionless: pd.DataFrame,
    channels: Iterable[str],
) -> list[TransitionResult]:
    results: list[TransitionResult] = []
    time_s = df_dimensionless["czas_s"].to_numpy(dtype=float)

    for channel in channels:
        values = df_dimensionless[channel].to_numpy(dtype=float)
        t02 = _crossing_time(time_s, values, 0.2)
        t08 = _crossing_time(time_s, values, 0.8)
        if t02 is None or t08 is None:
            results.append(
                TransitionResult(
                    channel=channel,
                    t_02=t02,
                    t_08=t08,
                    delta_t=None,
                    status="Brak przecięcia 0.2 i/lub 0.8",
                )
            )
            continue
        if t08 < t02:
            results.append(
                TransitionResult(
                    channel=channel,
                    t_02=t02,
                    t_08=t08,
                    delta_t=None,
                    status="Niepoprawna kolejność przecięć",
                )
            )
            continue
        results.append(
            TransitionResult(
                channel=channel,
                t_02=t02,
                t_08=t08,
                delta_t=t08 - t02,
                status="OK",
            )
        )

    return results

