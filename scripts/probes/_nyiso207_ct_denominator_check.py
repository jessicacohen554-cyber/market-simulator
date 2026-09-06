"""nyiso-207 ADDENDUM A — is the CT rows' basis gap an artifact of an un-derated denominator?

ZERO LP. Declared **POST-HOC** in ``PREREG-nyiso207-floor-coeff-basis-census.md`` addendum §A and
committed **before this script was executed**, because it can only WEAKEN this session's largest
evening-window number (``DS_CT_base``, -13.35 %).

THE CONFOUND — ``derive_nyiso_ct_reliability_floor.py`` normalises by NAMEPLATE with no outage
derate, unlike ``derive_nyiso_st_reliability_floor.py`` whose denominator is
``zone_available_capacity``. Outage hours therefore remain in the CT population as near-zero CF
readings, which inflate HOURLY dispersion far more than they move a DAILY mean — so they could
manufacture a large daily-vs-hourly gap for a reason unrelated to the time basis under audit.

THE CHECK — recompute the two ``DS_CT`` limbs' M1/M2/M3 with the denominator derated by the same
``campd-unit-outages-NYISO.csv`` extract and the same ``unit_capacity_mw / plant_capacity_mw``
share basis the ST script uses. ONE change: the denominator. This is a diagnostic on the census
statistic only; it is NOT a proposal to change the CT derive script, and no coefficient is
re-derived into the CSV.

Reproduce with ``uv run python scripts/probes/_nyiso207_ct_denominator_check.py``.
Writes ``results/calibration/_nyiso207_ct_denominator_check.json``.
"""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "results" / "calibration" / "_nyiso207_ct_denominator_check.json"
YEARS = (2023, 2024, 2025)
EVENING = range(14, 22)
T0_C = 25.0
WITHDRAW_BELOW_PCT = 5.0  # addendum §A's declared withdrawal threshold
SURVIVE_AT_PCT = 10.0  # addendum §A's declared survival threshold


def _load(rel: str, name: str) -> ModuleType:
    """Import a derive script by file path (``scripts/`` has no ``__init__.py``)."""
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


CT = _load("scripts/data/derive_nyiso_ct_reliability_floor.py", "_ct_derive2")
RAW = CT.RAW_DIR


def plant_nameplates() -> dict[int, float]:
    """``{plant_code: bin nameplate MW}`` for the pooled downstate CT_PEAKER fleet."""
    b = pd.read_csv(RAW / "_processed-legacy" / "bin_assignments_NYISO.csv")
    ds = b[(b["Plant_Group"] == "CT_PEAKER") & (b["Zone"].isin(CT.DOWNSTATE_ZONES))]
    return dict(zip(ds["Plant_Code"].astype(int), ds["Nameplate_MW"].astype(float)))


def derated_capacity(npl: dict[int, float], index: pd.DatetimeIndex) -> pd.Series:
    """Fleet available capacity — the ST script's derate, applied to the CT fleet."""
    avail = pd.Series(float(sum(npl.values())), index=index)
    path = RAW / "campd-unit-outages-NYISO.csv"
    if not path.exists():
        return avail
    o = pd.read_csv(path)
    o["facility_id"] = pd.to_numeric(o["facility_id"], errors="coerce")
    o = o[o["facility_id"].isin(npl)].copy()
    o["outage_start"] = pd.to_datetime(o["outage_start"])
    o["outage_end"] = pd.to_datetime(o["outage_end"])
    for _, e in o.iterrows():
        pcap = float(e["plant_capacity_mw"]) or 1.0
        share = float(npl.get(int(e["facility_id"]), 0.0)) * float(e["unit_capacity_mw"]) / pcap
        avail.loc[(index >= e["outage_start"]) & (index < e["outage_end"])] -= share
    return avail.clip(lower=0.0)


def frame(derate: bool) -> pd.DataFrame:
    """Hourly ``gross``/``avail``/``tmax`` for the pooled downstate CT fleet."""
    npl = plant_nameplates()
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
        c = c[c["facilityId"].astype(int).isin(npl)].copy()
        c["ts"] = pd.to_datetime(c["date"]) + pd.to_timedelta(c["hour"], unit="h")
        gross_h = c.groupby("ts")["grossLoad"].sum()
        g = pd.DataFrame({"gross": gross_h})
        g["avail"] = (
            derated_capacity(npl, gross_h.index) if derate else float(sum(npl.values()))
        )
        g["date"] = g.index.normalize()
        g["hour"] = g.index.hour
        g["tmax"] = g["date"].map(dt)
        frames.append(g.dropna(subset=["tmax"]))
    return pd.concat(frames)


def limb(g: pd.DataFrame, stat: str) -> dict:
    """M1/M2/M3 for one CT knot under whichever denominator ``g`` carries."""
    q = 0.97 if stat == "cap" else 0.25
    ev = g[g["hour"].isin(EVENING)]
    d = ev.groupby("date").agg(gross=("gross", "sum"), avail=("avail", "sum"))
    daily = pd.DataFrame({"cf": (d["gross"] / d["avail"]).where(d["avail"] > 0)})
    daily["tmax"] = ev.groupby("date")["tmax"].first()
    daily = daily.dropna()
    h = ev[ev["avail"] > 0].copy()
    h["cf"] = h["gross"] / h["avail"]
    if stat != "cap":
        daily, h = daily[daily["tmax"] < T0_C], h[h["tmax"] < T0_C]
    m1, m2 = float(daily["cf"].quantile(q)), float(h["cf"].quantile(q))
    return {
        "M1_daily": round(m1, 5),
        "M2_hourly": round(m2, 5),
        "gap_abs": round(m2 - m1, 5),
        "gap_rel_pct": round(100.0 * (m2 - m1) / m1, 2),
    }


def main() -> None:
    """Run both denominators and apply addendum §A's declared decision thresholds."""
    out: dict = {
        "session": "nyiso-207",
        "addendum": "PREREG-nyiso207-floor-coeff-basis-census.md §A (POST-HOC)",
        "years": list(YEARS),
        "limbs": {},
    }
    plain, der = frame(derate=False), frame(derate=True)
    for stat, frozen in (("base", 0.1320), ("cap", 0.6790)):
        a, b = limb(plain, stat), limb(der, stat)
        verdict = (
            "WITHDRAWN_AS_CONFOUNDED"
            if abs(b["gap_rel_pct"]) < WITHDRAW_BELOW_PCT
            else (
                "SURVIVES"
                if abs(b["gap_rel_pct"]) >= SURVIVE_AT_PCT
                else "ATTENUATED_INCONCLUSIVE"
            )
        )
        out["limbs"][f"DS_CT_{stat}"] = {
            "frozen": frozen,
            "nameplate_denominator_as_shipped": a,
            "availability_derated_denominator": b,
            "gap_shrinkage_pct_points": round(
                abs(a["gap_rel_pct"]) - abs(b["gap_rel_pct"]), 2
            ),
            "addendum_A_verdict": verdict,
        }
    OUT.write_text(json.dumps(out, indent=2) + "\n")
    print(json.dumps(out, indent=2))
    print(f"\nwrote {OUT}")


if __name__ == "__main__":
    main()
