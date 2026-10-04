"""Close-out CAISO w4, phase 0 (ZERO LP): validate the unprinted formula's shape DRIVER on printed Palo Verde hours.

The R-CAISO-18 formula prices Palo Verde in unprinted hours as
``gas_AZ(month) x 13.0 x shape(t)`` (w3 adds the CA citygate daily factor),
where ``shape`` is the CISO EIA-930 NET load (demand - solar - wind) normalised
to its annual mean (``neighbor_price.caiso_hub_load_shape``, docstring: "The CISO
series proxies the neighbor (same solar resource / time zone)").

Candidate (rule 14, measured over proxy): the same construction on the hub's
OWN region's net load, the EIA-930 Desert Southwest region (``Region == "SW"``
in the committed BALANCE archive: AZPS, DEAA, EPE, GRIF, HGMA, PNM, SRP, TEPC,
WALC), mapped onto the CISO model clock by UTC end-of-hour. Same exponent
(1.0), same clip, same heat rate, same gas — no parameter added.

Gate, fixed before computing (desk status 2026-10-04): the SW-driver formula
beats the CISO-proxy formula against the measured OASIS DAM Palo Verde hourly
print on BOTH hourly r and RMSE in >= 3 of 4 years 2022-2025. 2021 (May-Dec
printed) is reported, not gated. Also reported: mean (formula - print) by
object month (Jun-Sep, Dec) x hod band.

Usage::

    PYTHONPATH=.:src:scripts .venv/bin/python scripts/probes/_closeout_caiso_w4_shape_validation.py [--out PATH]
"""

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path[:0] = [".", "src", "scripts", str(Path(__file__).resolve().parent)]

from market_sim.data.eia930.envelopes import measured_intertie_hub_price_raw  # noqa: E402
from market_sim.data.eia930.frames import (  # noqa: E402
    _eia_hourly_frame_filled,
    set_caiso_eia930_clock_repair,
)
from market_sim.data.neighbor_price import (  # noqa: E402
    caiso_hub_load_shape,
    caiso_hub_measured_gas_reference_price,
)
from market_sim.model.interchange.spec import CAISO_PER_HUB_NEIGHBORS  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BAL = ROOT / "data/raw/eia-930/EIA930_BALANCE_{y}_{h}.parquet"
T = 8760
_DAYS = np.array([31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31])
MONTH = np.repeat(np.arange(1, 13), _DAYS * 24)
HOD = np.arange(T) % 24
BANDS = {"00-05": (0, 5), "06-16": (6, 16), "17-21": (17, 21), "22-23": (22, 23)}
OBJ = (6, 7, 8, 9, 12)


def sw_net_load(year: int) -> np.ndarray | None:
    """EIA-930 SW-region net load on the CISO model clock (UTC end-of-hour join)."""
    frames = []
    for y in (year, year + 1):
        for h in ("Jan_Jun", "Jul_Dec"):
            p = Path(BAL.as_posix().format(y=y, h=h))
            if p.exists():
                frames.append(pd.read_parquet(p))
    if not frames:
        return None
    b = pd.concat(frames)
    b = b[b.Region.astype(str) == "SW"]
    utc = pd.to_datetime(b["UTC Time at End of Hour"], format="%m/%d/%Y %I:%M:%S %p")
    num = lambda c: pd.to_numeric(b[c], errors="coerce")  # noqa: E731
    # solar / wind: the legacy single column, or (mid-2024 taxonomy) the sum of
    # its with/without integrated-storage split; imputed/adjusted copies excluded
    vre = [
        c
        for c in b.columns
        if c.startswith(
            ("Net Generation (MW) from Solar", "Net Generation (MW) from Wind")
        )
        and "(Imputed)" not in c
        and "(Adjusted)" not in c
    ]
    net = num("Demand (MW)").fillna(0) - sum(num(c).fillna(0) for c in vre)
    dem_ok = num("Demand (MW)").notna()
    s = (
        pd.DataFrame({"utc": utc, "net": net, "ok": dem_ok})
        .groupby("utc")
        .agg(net=("net", "sum"), n=("ok", "sum"))
    )
    ciso = _eia_hourly_frame_filled("CISO", year)
    if ciso is None:
        return None
    clock = pd.DatetimeIndex(ciso["UTC time"])
    s = s.reindex(clock)
    full = s.n.max()
    v = s.net.where(s.n >= full).interpolate().bfill().ffill().to_numpy(float)
    return v[:T]


def shape_from(driver: np.ndarray) -> np.ndarray:
    """The caiso_hub_load_shape construction (mean-normalised, clip 0.05, exponent 1)."""
    return np.clip(driver / driver.mean(), 0.05, None) ** 1.0


def score(year: int) -> dict:
    """Hourly r / RMSE of the CISO-proxy vs SW-own formula against the Palo Verde print."""
    spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
    base = caiso_hub_measured_gas_reference_price(
        spec, year, T, eia923_fallback=True, daily_gas_shape=True
    )
    proxy_shape = caiso_hub_load_shape(spec, year, T)
    meas = measured_intertie_hub_price_raw("CAISO", year, T, spec.hub)
    sw = sw_net_load(year)
    if base is None or meas is None or sw is None or proxy_shape is None:
        return {"hours": 0}
    gas_hr = base / proxy_shape  # gas x HR x daily factor
    cand = gas_hr * shape_from(sw)
    sel = np.isfinite(meas) & np.isfinite(base) & np.isfinite(cand)
    out = {"hours": int(sel.sum())}
    for name, f in (("ciso_proxy", base), ("sw_own", cand)):
        e = f[sel] - meas[sel]
        out[name] = {
            "r": round(float(np.corrcoef(f[sel], meas[sel])[0, 1]), 4),
            "rmse": round(float(np.sqrt(np.mean(e**2))), 3),
            "bias": round(float(e.mean()), 3),
        }
        cells = {}
        for b, (h0, h1) in BANDS.items():
            k = sel & np.isin(MONTH, OBJ) & (HOD >= h0) & (HOD <= h1)
            cells[b] = round(float((f[k] - meas[k]).mean()), 2) if k.any() else None
        out[name]["obj_month_bias_by_band"] = cells
    out["sw_wins"] = bool(
        out["sw_own"]["r"] > out["ciso_proxy"]["r"]
        and out["sw_own"]["rmse"] < out["ciso_proxy"]["rmse"]
    )
    return out


def main() -> None:
    """Score 2021-2025, apply the gate, and report the 2019-2021 shape change."""
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--out",
        default=str(
            ROOT / "docs/records/caiso/closeout-caiso-w4/_shape_validation.json"
        ),
    )
    a = ap.parse_args()
    set_caiso_eia930_clock_repair(True)
    res = {str(y): score(y) for y in (2021, 2022, 2023, 2024, 2025)}
    wins = sum(res[str(y)].get("sw_wins", False) for y in (2022, 2023, 2024, 2025))
    res["gate"] = {"sw_wins_2022_2025": int(wins), "pass": bool(wins >= 3)}
    spec = CAISO_PER_HUB_NEIGHBORS["WECC_DSW"]
    ratio = {}
    for y in (2019, 2020, 2021):
        p = caiso_hub_load_shape(spec, y, T)
        sw = sw_net_load(y)
        if p is None or sw is None:
            continue
        r = shape_from(sw) / p
        ratio[str(y)] = {
            f"m{m:02d}": {
                b: round(float(r[(MONTH == m) & (HOD >= h0) & (HOD <= h1)].mean()), 3)
                for b, (h0, h1) in BANDS.items()
            }
            for m in range(1, 13)
        }
    res["sw_over_proxy_shape_ratio_unprinted_years"] = ratio
    Path(a.out).write_text(json.dumps(res, indent=1, default=float))
    print(
        json.dumps(
            {k: v for k, v in res.items() if not k.startswith("sw_over")}, indent=1
        )
    )
    for y, t in ratio.items():
        print(y, {m: t[m] for m in ("m06", "m09", "m10", "m12")})


if __name__ == "__main__":
    main()
