#!/usr/bin/env python3
import argparse
import pickle
from pathlib import Path

import numpy as np
import pandas as pd


SENSOR_NAMES = [
    "bendDieLatT","bendDieRotT","bendDieVerT","bendDieLatM","bendDieRotA","bendDieVerM",
    "colletAxT","colletRotT","colletAxMov","colletRotMov",
    "mandrelAxLoad","mandrelAxMov",
    "pressAxT","pressLatT","pressLeftAxT","pressAxMov","pressLatMov","pressLeftAxMov",
    "clampLatT","clampLatMov"
]

# TubeBEND column mapping (ground-truth from your Exp_11 inspection)
MAP_LOADS = {
    "bendDieLatT": "MACHINE_BEND-DIE_LATERAL_Max_Torque_[%]",
    "bendDieRotT": "MACHINE_BEND-DIE_ROTATING_Max_Torque_[%]",
    "bendDieVerT": "MACHINE_BEND-DIE_VERTICAL_Max_Torque_[%]",
    "clampLatT":   "MACHINE_CLAMP-DIE_LATERAL_Max_Torque_[%]",
    "colletAxT":   "MACHINE_COLLET_AXIAL_Max_Torque_[%]",
    "colletRotT":  "MACHINE_COLLET_ROTATING_Max_Torque_[%]",
    "mandrelAxLoad":"MACHINE_MANDREL_AXIAL_Max_Torque_[%]",
    "pressAxT":    "MACHINE_PRESSURE-DIE_AXIAL_Max_Torque_[%]",
    "pressLatT":   "MACHINE_PRESSURE-DIE_LATERAL_Max_Torque_[%]",
    "pressLeftAxT":"MACHINE_PRESSURE-DIE_LEFT_AXIAL_Max_Torque_[%]",
}

MAP_MOVES = {
    "bendDieLatM": "BEND-DIE_LATERAL_Movement_[mm]",
    "bendDieRotA": "BEND-DIE_ROTATING_Angle_[°]",
    "bendDieVerM": "BEND-DIE_VERTICAL_Movement_[mm]",
    "clampLatMov": "CLAMP-DIE_LATERAL_Movement_[mm]",
    "colletAxMov": "COLLET_AXIAL_Movement_[mm]",
    "colletRotMov":"COLLET_ROTATING_Movement_[mm]",
    "mandrelAxMov":"MANDREL_AXIAL_Movement_[mm]",
    "pressAxMov":  "PRESSURE-DIE_AXIAL_Movement_[mm]",
    "pressLatMov": "PRESSURE-DIE_LATERAL_Movement_[mm]",
    "pressLeftAxMov":"PRESSURE-DIE_LEFT_AXIAL_Movement_[mm]",
}


def get_time_vector(df: pd.DataFrame) -> np.ndarray:
    """
    Return a numeric time vector for df.
    Preference order:
      1) a column containing 'Time' (case-insensitive)
      2) the index if numeric-like
      3) range(len(df))
    """
    # 1) Find a 'Time' column
    time_cols = [c for c in df.columns if "time" in str(c).lower()]
    if time_cols:
        t = pd.to_numeric(df[time_cols[0]], errors="coerce").to_numpy()
        if np.isfinite(t).sum() >= max(2, int(0.5 * len(t))):
            return t

    # 2) Try index
    try:
        idx = pd.to_numeric(df.index, errors="coerce").to_numpy()
        if np.isfinite(idx).sum() >= max(2, int(0.5 * len(idx))):
            return idx
    except Exception:
        pass

    # 3) Fallback: sample index as time
    return np.arange(len(df), dtype=float)


def resample_series(t: np.ndarray, y: np.ndarray, n: int) -> np.ndarray:
    """
    Resample (t, y) to n points using linear interpolation.
    We normalize time to [0,1] for stability.
    """
    t = np.asarray(t, dtype=float)
    y = np.asarray(y, dtype=float)

    mask = np.isfinite(t) & np.isfinite(y)
    t = t[mask]
    y = y[mask]
    if t.size < 2:
        return np.zeros(n, dtype=float)

    order = np.argsort(t)
    t = t[order]
    y = y[order]

    t_unique, idx = np.unique(t, return_index=True)
    y_unique = y[idx]
    if t_unique.size < 2:
        return np.zeros(n, dtype=float)

    t0, t1 = t_unique[0], t_unique[-1]
    if t1 == t0:
        return np.zeros(n, dtype=float)

    tn = (t_unique - t0) / (t1 - t0)
    grid = np.linspace(0.0, 1.0, n)
    return np.interp(grid, tn, y_unique)


def quantize_and_offset(sensors: np.ndarray, quant: int = 100) -> np.ndarray:
    """
    bendviz-style quantization + stacking for display.
    """
    numChannels, n = sensors.shape

    TORQ_CHANNELS = {0,1,2,6,7,12,13,14,18}
    DIST_CHANNELS = {3,4,5,8,9,11,15,16,17,19}

    mins = np.nanmin(sensors, axis=1)
    maxs = np.nanmax(sensors, axis=1)

    # Shared ranges (forces vs movements)
    tmin = np.nanmin([mins[i] for i in TORQ_CHANNELS])
    tmax = np.nanmax([maxs[i] for i in TORQ_CHANNELS])
    dmin = np.nanmin([mins[i] for i in DIST_CHANNELS])
    dmax = np.nanmax([maxs[i] for i in DIST_CHANNELS])

    tspan = (tmax - tmin) if (tmax - tmin) != 0 else 1.0
    dspan = (dmax - dmin) if (dmax - dmin) != 0 else 1.0

    out = np.zeros_like(sensors, dtype=float)

    for ch in range(numChannels):
        arr = sensors[ch]
        arr = np.nan_to_num(arr, nan=0.0)

        if ch in TORQ_CHANNELS:
            q = quant * (((arr - tmin) / tspan) - 0.5)
        elif ch in DIST_CHANNELS:
            q = quant * (((arr - dmin) / dspan) - 0.5)
        else:
            span = (maxs[ch] - mins[ch]) if (maxs[ch] - mins[ch]) != 0 else 1.0
            q = quant * (((arr - mins[ch]) / span) - 0.5)

        # offsets to match bendviz stacked layout
        if ch < 3:
            q += 450
        elif ch < 6:
            q += 400
        elif ch < 10:
            q += 300
        elif ch < 12:
            q += 220
        elif ch < 18:
            q += 100

        out[ch] = np.round(q).astype(int)

    return out


def build_dta_for_exp(exp: dict, exp_id: int, n_samples: int) -> tuple[np.ndarray, str]:
    dfL = exp["process_parameters_loads_machine"]
    dfM = exp["process_parameters_movements"]

    tL = get_time_vector(dfL)
    tM = get_time_vector(dfM)

    sensors = np.zeros((len(SENSOR_NAMES), n_samples), dtype=float)

    # Loads
    for sensor, col in MAP_LOADS.items():
        if col in dfL.columns:
            y = pd.to_numeric(dfL[col], errors="coerce").to_numpy()
            sensors[SENSOR_NAMES.index(sensor), :] = resample_series(tL, y, n_samples)

    # Movements
    for sensor, col in MAP_MOVES.items():
        if col in dfM.columns:
            y = pd.to_numeric(dfM[col], errors="coerce").to_numpy()
            sensors[SENSOR_NAMES.index(sensor), :] = resample_series(tM, y, n_samples)

    info = f"Experiment: {exp_id}\\nSamples (resampled): {n_samples}\\nSource: TubeBEND"
    return sensors, info


def write_dta_js(out_path: Path, sensors_q: np.ndarray, info: str):
    n = sensors_q.shape[1]
    data_slice = slice(None, n-2) if n > 2 else slice(None)

    with out_path.open("w") as f:
        for i, name in enumerate(SENSOR_NAMES):
            arr = sensors_q[i, data_slice]
            f.write(f"var {name}=[")
            f.write(",".join(str(int(x)) for x in arr))
            f.write("];\n")
        f.write(f"var info='{info}';\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pkl", required=True, help="Path to experiments_process_and_results.pkl")
    ap.add_argument("--out-dir", required=True, help="Where to write dta<id>.js")
    ap.add_argument("--n-samples", type=int, default=2000)
    ap.add_argument("--start", type=int, default=1)
    ap.add_argument("--end", type=int, default=318)
    args = ap.parse_args()

    pkl_path = Path(args.pkl)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with pkl_path.open("rb") as f:
        data = pickle.load(f)

    for exp_id in range(args.start, args.end + 1):
        key = f"Exp_{exp_id}"
        if key not in data:
            print(f"SKIP: {key} not found")
            continue

        exp = data[key]
        sensors, info = build_dta_for_exp(exp, exp_id, args.n_samples)
        sensors_q = quantize_and_offset(sensors, quant=100)

        out_path = out_dir / f"dta{exp_id}.js"
        write_dta_js(out_path, sensors_q, info)

        if exp_id % 25 == 0:
            print(f"Done up to Exp_{exp_id}")

    print("Finished generating dta files.")


if __name__ == "__main__":
    main()