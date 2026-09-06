"""nyiso-207 phase 0 — the NYISO reliability-floor coefficient BASIS CENSUS.

ZERO LP. Source data ONLY (rule 23 ``[R-FROZEN-DERIVE]``, rule 1 ``[R-STRUCT]``): the same
CAMPD unit-level extract, guard-corrected outage extract, bin assignments and archived zone
TMAX that the two derive scripts read. **No metrics file, no solve output, no price or volume
residual is opened at any point.**

THE OBJECT — every live NYISO reliability-floor coefficient is a **percentile over a population
of DAILY aggregates** and is applied as an **HOURLY** floor fraction
(``model/interchange/core.py::_apply_frac``: ``frac x pmax x availability[t]``). A percentile of
daily means is not the percentile of the hourly population it is applied to, whenever there is
dispersion inside the aggregation window.

Two sessions have each measured that gap on ONE limb — nyiso-203 §6 on the NYC ``base_24h``
(0.1750 vs 0.1663, -5.0 %) and nyiso-140 §3.2 on the Long_Island ``base_24h`` (0.2623 vs 0.2011
at fixed membership, -23.3 %). **Nobody has measured it on the six other live knots produced by
the same two scripts under the identical construction.** This probe measures all of them, so the
pending owner ruling can be scoped to one coefficient or to a construction.

Pre-registered in ``results/calibration/PREREG-nyiso207-floor-coeff-basis-census.md`` §§4-6,
committed and pushed before any number below was read. The measurements, per limb:

  * **M1 IDENTITY GATE** - re-derive the frozen value on the script's OWN construction, by
    calling the shipped module functions rather than re-implementing them. Tolerance 0.002
    absolute. A limb that fails is reported NOT REPRODUCIBLE and NO gap is computed for it, so a
    pipeline difference can never be reported as a basis difference. Rows flagged "legacy" in
    their own ``threshold_basis`` prose are EXPECTED to fail; that expectation is pre-registered.
  * **M2 BASIS-MATCHED VALUE** - the same percentile on the HOURLY population, with fleet,
    cool/hot day selection, availability normalisation and hour window all held identical.
  * **M3 GAP** - M2 - M1, absolute and relative.
  * **M4 REACHABILITY AND SIZE** - (a) the measured band %: the share of the limb's own
    applicable hours whose metered fleet when-available CF falls strictly between the two
    coefficients, which bounds what a coefficient move can reach; (b) for the ramp limbs, added
    forced energy over h14-21 under the model's own composition (the 24h base and the evening
    ramp combined by maximum), with ONE KNOT MOVED AT A TIME.
  * **M5 PREDICTOR** - the median across days of the within-window coefficient of variation of
    hourly when-available CF, on the limb's own cool-day population.

Rule 22 ``[R-HOLDOUT]``: 2023-2025 ONLY, the derive scripts' own ``--years`` default. The
``NY_2020/2021/2022/2026.parquet`` extracts present in this data profile are NOT read.
Rule 25 ``[R-ISO-SCOPE]``: NYISO only; the per-ISO sibling scripts are not touched.

Reproduce with ``uv run python scripts/probes/_nyiso207_floor_coeff_basis_census.py``.
Writes its machine record to ``results/calibration/_nyiso207_floor_coeff_basis_census.json``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "calibration" / "_nyiso207_floor_coeff_basis_census.json"

YEARS = (2023, 2024, 2025)
M1_TOL = 0.002  # PREREG §4 M1 identity-gate tolerance, absolute
EVENING = range(14, 22)  # HB14-21, both scripts' window
T0_C = 25.0  # both scripts' cool/hot split


def _load(rel: str, name: str) -> ModuleType:
    """Import a derive script by file path (``scripts/`` has no ``__init__.py``)."""
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ST = _load("scripts/data/derive_nyiso_st_reliability_floor.py", "_st_derive")
CT = _load("scripts/data/derive_nyiso_ct_reliability_floor.py", "_ct_derive")
RAW = ST.RAW_DIR


# --------------------------------------------------------------------------- #
# The frozen live limbs (PREREG §3.1). Values read from
# data/raw/reference/reliability_floor_coeffs_NYISO.csv; nothing is written to it.
# --------------------------------------------------------------------------- #
LIMBS = [
    # (id, zone, class, statistic, frozen, window, scope)
    ("NYC_ST_base24", "NYC", "ST_GAS", "base_24h", 0.1750, "all24", "gate"),
    ("LI_ST_base24", "Long_Island", "ST_GAS", "base_24h", 0.2620, "all24", "gate"),
    ("NYC_ST_base_ev", "NYC", "ST_GAS", "base_ev", 0.1850, "evening", "in"),
    ("NYC_ST_cap", "NYC", "ST_GAS", "cap", 1.0000, "evening", "in"),
    ("LI_ST_base_ev", "Long_Island", "ST_GAS", "base_ev", 0.3500, "evening", "in"),
    ("LI_ST_cap", "Long_Island", "ST_GAS", "cap", 0.8820, "evening", "in"),
    ("CH_ST_base_ev", "Capital_Hudson", "ST_GAS", "base_ev", 0.0000, "evening", "census"),
    ("CH_ST_cap", "Capital_Hudson", "ST_GAS", "cap", 0.3200, "evening", "census"),
    ("DS_CT_base", "downstate", "CT_PEAKER", "base", 0.1320, "evening", "census"),
    ("DS_CT_cap", "downstate", "CT_PEAKER", "cap", 0.6790, "evening", "census"),
]

# Ramp knot pairs for the M4(b) sizing: (zone, base_id, cap_id, T_cap, base24_frac).
# base24_frac is the all-hours floor the model composes the ramp with by maximum
# (CLAUDE.md: "floored over ALL hours, with the evening hot-limb layered on top via
# maximum"); Capital_Hudson has no base_24h row, so its ramp stands alone.
RAMPS = [
    ("NYC", "NYC_ST_base_ev", "NYC_ST_cap", 38.00, 0.1750),
    ("Long_Island", "LI_ST_base_ev", "LI_ST_cap", 37.55, 0.2620),
    ("Capital_Hudson", "CH_ST_base_ev", "CH_ST_cap", 38.00, 0.0000),
]


def st_zone_frame(zone: str) -> tuple[pd.DataFrame, dict[int, float]]:
    """Hourly ``gross``/``avail``/``tmax`` for a zone's ST_GAS fleet.

    Built with the SHIPPED :mod:`derive_nyiso_st_reliability_floor` functions
    (``zone_steam_plant_codes``, ``zone_available_capacity``) so the daily statistics
    recomputed from this frame are the script's own, not a re-implementation.
    """
    plant_npl, _ = ST.zone_steam_plant_codes(zone)
    arch = pd.read_csv(
        RAW / "nyiso-weather" / "nyiso_zone_tmax_daily.csv", parse_dates=["date"]
    )
    zt = arch[arch["zone"] == zone].set_index("date")["tmax_c"]
    frames = []
    for yr in YEARS:
        path = RAW / "campd-unit-level" / f"NY_{yr}.parquet"
        if not path.exists():
            continue
        c = pd.read_parquet(path)
        c = c[c["facilityId"].astype(int).isin(plant_npl)].copy()
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        gross_h = c.groupby("ts")["grossLoad"].sum()
        avail_h = ST.zone_available_capacity(plant_npl, gross_h.index)
        g = pd.DataFrame({"gross": gross_h, "avail": avail_h})
        g["date"] = g.index.normalize()
        g["hour"] = g.index.hour
        g["tmax"] = g["date"].map(zt)
        frames.append(g.dropna(subset=["tmax"]))
    return pd.concat(frames), plant_npl


def ct_downstate_frame() -> pd.DataFrame:
    """Hourly ``gross``/``avail``/``tmax`` for the pooled downstate CT_PEAKER fleet.

    Mirrors :mod:`derive_nyiso_ct_reliability_floor`, which normalises by NAMEPLATE and
    applies no outage derate — so ``avail`` here is the constant nameplate, deliberately,
    to keep M1 on the script's own construction.
    """
    codes, nameplate = CT.downstate_peaker_plant_codes()
    arch = pd.read_csv(
        RAW / "nyiso-weather" / "nyiso_downstate_tmax_daily.csv", parse_dates=["date"]
    )
    dt = arch.set_index("date")["tmax_c"]
    frames = []
    for yr in YEARS:
        path = RAW / "campd-unit-level" / f"NY_{yr}.parquet"
        if not path.exists():
            continue
        c = pd.read_parquet(path)
        c = c[c["facilityId"].astype(int).isin(codes)].copy()
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        gross_h = c.groupby("ts")["grossLoad"].sum()
        g = pd.DataFrame({"gross": gross_h})
        g["avail"] = float(nameplate)
        g["date"] = g.index.normalize()
        g["hour"] = g.index.hour
        g["tmax"] = g["date"].map(dt)
        frames.append(g.dropna(subset=["tmax"]))
    return pd.concat(frames)


def daily_cf(g: pd.DataFrame, hours: range | None) -> pd.DataFrame:
    """The scripts' daily aggregate: ``sum(gross) / sum(avail)`` per date, with TMAX."""
    sub = g if hours is None else g[g["hour"].isin(hours)]
    d = sub.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
    cf = (d["gross"] / d["avail"]).where(d["avail"] > 0)
    out = pd.DataFrame({"cf": cf})
    out["tmax"] = sub.groupby("date")["tmax"].first()
    return out.dropna()


def hourly_cf(g: pd.DataFrame, hours: range | None) -> pd.DataFrame:
    """The applied basis: the HOURLY when-available CF, same fleet and same window."""
    sub = g if hours is None else g[g["hour"].isin(hours)]
    sub = sub[sub["avail"] > 0].copy()
    sub["cf"] = sub["gross"] / sub["avail"]
    return sub[["cf", "tmax", "date", "hour"]]


def within_window_cv(g: pd.DataFrame, hours: range | None, cool_only: bool) -> float:
    """M5 — median across days of the within-window CV of hourly when-available CF."""
    h = hourly_cf(g, hours)
    if cool_only:
        h = h[h["tmax"] < T0_C]
    grp = h.groupby("date")["cf"]
    cv = (grp.std() / grp.mean()).replace([np.inf, -np.inf], np.nan).dropna()
    return float(cv.median()) if len(cv) else float("nan")


def band_share(g: pd.DataFrame, hours: range | None, lo: float, hi: float) -> float:
    """M4(a) — share of the limb's applicable hours with metered CF strictly in (lo, hi)."""
    h = hourly_cf(g, hours)
    if len(h) == 0 or not np.isfinite(lo) or not np.isfinite(hi):
        return float("nan")
    a, b = (lo, hi) if lo <= hi else (hi, lo)
    return float(((h["cf"] > a) & (h["cf"] < b)).mean() * 100.0)


def ramp_frac(tmax: pd.Series, base: float, cap: float, t_cap: float) -> pd.Series:
    """The two-knot linear ramp the CSV encodes: base @T0, cap @t_cap, clamped."""
    if t_cap <= T0_C:
        return pd.Series(base, index=tmax.index)
    slope = (cap - base) / (t_cap - T0_C)
    return (base + slope * (tmax - T0_C)).clip(lower=base, upper=cap)


def added_twh(
    g: pd.DataFrame, base: float, cap: float, t_cap: float, base24: float
) -> float:
    """Forced energy the composed floor adds above metered conduct, pooled, in TWh.

    The model composes the all-hours ``base_24h`` floor with the evening ramp by MAXIMUM,
    so the ramp's marginal contribution is only what it adds above ``base24``. Evaluated
    over every hour so the composition is honest, then reported as the total.
    """
    frac = pd.Series(base24, index=g.index)
    ev = g["hour"].isin(EVENING)
    frac[ev] = np.maximum(base24, ramp_frac(g.loc[ev, "tmax"], base, cap, t_cap))
    floor_mw = frac * g["avail"]
    return float(np.maximum(0.0, floor_mw - g["gross"]).sum() / 1e6)


def main() -> None:
    """Run the census and write the machine record."""
    frames: dict[str, pd.DataFrame] = {}
    for zone in ("NYC", "Long_Island", "Capital_Hudson"):
        frames[zone], _ = st_zone_frame(zone)
    frames["downstate"] = ct_downstate_frame()

    rows = []
    derived: dict[str, dict] = {}
    for lid, zone, klass, stat, frozen, window, scope in LIMBS:
        g = frames[zone]
        hours = None if window == "all24" else EVENING
        cool_only = stat != "cap"  # the p97 cap is taken over ALL days in both scripts
        q = 0.97 if stat == "cap" else 0.25

        d = daily_cf(g, hours)
        h = hourly_cf(g, hours)
        if cool_only:
            d, h = d[d["tmax"] < T0_C], h[h["tmax"] < T0_C]

        m1 = float(d["cf"].quantile(q))
        m2 = float(h["cf"].quantile(q))
        reproduces = abs(m1 - frozen) <= M1_TOL
        gap_abs = m2 - m1
        gap_rel = 100.0 * gap_abs / m1 if m1 > 0 else float("nan")

        rec = {
            "limb": lid,
            "zone": zone,
            "class": klass,
            "statistic": stat,
            "scope": scope,
            "window": window,
            "quantile": q,
            "frozen": frozen,
            "M1_rederived": round(m1, 5),
            "M1_abs_err_vs_frozen": round(abs(m1 - frozen), 5),
            "M1_reproduces": bool(reproduces),
            "M2_basis_matched_hourly": round(m2, 5) if reproduces else None,
            "M3_gap_abs": round(gap_abs, 5) if reproduces else None,
            "M3_gap_rel_pct": round(gap_rel, 2) if reproduces else None,
            "M4a_measured_band_pct": (
                round(band_share(g, hours, m1, m2), 3) if reproduces else None
            ),
            "M5_within_window_cv": round(within_window_cv(g, hours, cool_only), 4),
            "n_days": int(len(d)),
            "n_hours": int(len(h)),
        }
        rows.append(rec)
        derived[lid] = {"m1": m1, "m2": m2, "reproduces": reproduces}

    # --- M4(b): one knot at a time, under the model's own max-composition --------
    sizing = []
    for zone, bid, cid, t_cap, base24 in RAMPS:
        g = frames[zone]
        b0 = next(r["frozen"] for r in rows if r["limb"] == bid)
        c0 = next(r["frozen"] for r in rows if r["limb"] == cid)
        frozen_twh = added_twh(g, b0, c0, t_cap, base24)
        entry = {
            "zone": zone,
            "base_knot": bid,
            "cap_knot": cid,
            "t_cap_c": t_cap,
            "base24_composed": base24,
            "added_twh_frozen": round(frozen_twh, 5),
        }
        for tag, lid in (("base", bid), ("cap", cid)):
            d = derived[lid]
            if not d["reproduces"]:
                entry[f"added_twh_{tag}_basis_matched"] = None
                entry[f"delta_twh_{tag}"] = None
                continue
            bb, cc = (d["m2"], c0) if tag == "base" else (b0, d["m2"])
            alt = added_twh(g, bb, cc, t_cap, base24)
            entry[f"added_twh_{tag}_basis_matched"] = round(alt, 5)
            entry[f"delta_twh_{tag}"] = round(alt - frozen_twh, 5)
        sizing.append(entry)

    # --- pre-registered verdicts (PREREG §5, §6) --------------------------------
    in_scope = [r for r in rows if r["scope"] == "in" and r["M1_reproduces"]]
    signs_ok = all(
        (r["M3_gap_abs"] < 0) if r["statistic"] != "cap" else (r["M3_gap_abs"] > 0)
        for r in in_scope
    )
    big = [r for r in in_scope if abs(r["M3_gap_rel_pct"]) >= 5.0]
    ordered = sorted(
        [r for r in rows if r["M1_reproduces"]], key=lambda r: r["M5_within_window_cv"]
    )
    mono = all(
        abs(ordered[i]["M3_gap_rel_pct"]) <= abs(ordered[i + 1]["M3_gap_rel_pct"])
        for i in range(len(ordered) - 1)
    )

    record = {
        "session": "nyiso-207",
        "prereg": "results/calibration/PREREG-nyiso207-floor-coeff-basis-census.md",
        "years": list(YEARS),
        "m1_tolerance_abs": M1_TOL,
        "limbs": rows,
        "ramp_sizing_m4b": sizing,
        "verdicts": {
            "P1_signs_as_predicted": bool(signs_ok),
            "P3_monotone_in_M5": bool(mono),
            "M5_ascending_order": [
                [r["limb"], r["M5_within_window_cv"], r["M3_gap_rel_pct"]]
                for r in ordered
            ],
            "class_verdict_ge2_limbs_ge5pct": bool(len(big) >= 2),
            "in_scope_reproducing": [r["limb"] for r in in_scope],
            "not_reproducible": [r["limb"] for r in rows if not r["M1_reproduces"]],
        },
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(record, indent=2) + "\n")

    def fmt(v: float | None, spec: str) -> str:
        """Render an optional measurement, or ``--`` where the M1 gate withheld it."""
        return "--" if v is None else format(v, spec)

    hdr = (
        f"{'limb':16s} {'scope':7s} {'frozen':>8s} {'M1':>8s} {'ok':>3s} "
        f"{'M2':>8s} {'gap%':>8s} {'band%':>7s} {'CV':>7s}"
    )
    print(hdr)
    print("-" * len(hdr))
    for r in rows:
        print(
            f"{r['limb']:16s} {r['scope']:7s} {r['frozen']:8.4f} "
            f"{r['M1_rederived']:8.4f} {'Y' if r['M1_reproduces'] else 'N':>3s} "
            f"{fmt(r['M2_basis_matched_hourly'], '.4f'):>8s} "
            f"{fmt(r['M3_gap_rel_pct'], '+.2f'):>8s} "
            f"{fmt(r['M4a_measured_band_pct'], '.2f'):>7s} "
            f"{r['M5_within_window_cv']:7.4f}"
        )
    print("\nramp sizing (M4b, TWh pooled 2023-2025):")
    for s in sizing:
        print(f"  {s}")
    print("\nverdicts:", json.dumps(record["verdicts"], indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
