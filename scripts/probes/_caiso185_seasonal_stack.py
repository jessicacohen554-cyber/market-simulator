"""caiso-185 — the SEASONAL-STACK composition check (rule 19 ``[R-ONE-MECH]``).

**NOT PRE-REGISTERED.** PRECHECK-caiso185 §4 registered H-GUARD — the composition of the
reconcile with the ALWAYS-ON merchant-CC summer-capacity *clip* — and pre-registered that
the composition "must be measured, not asserted". It did **not** anticipate the composition
that the P0-2 provenance audit surfaced: the reconcile against the **seasonal summer
derate** of ``cc_nameplate_summer_derate``. This probe is reported as a hazard **discovered
during P0 and declared as not pre-registered**, not as a bar moved after the fact. Its
criterion is a *measured contradiction*, not a tuned threshold.

THE COMPOSITION. Under ``cc_nameplate_summer_derate`` (armed on the CAISO keeper) a CC
bin's LP capacity is raised to **full EIA-860 nameplate** in ``fleet_to_bins``, and
``arrays.py:739`` then multiplies the summer months (Jun-Sep) by the plant's published
``cc_summer_derate_ratio = net_summer / nameplate``. So today:

    summer capability  = nameplate x (net_summer / nameplate) = net_summer   (published)
    off-summer capabty = nameplate                                            (unpublished)

``_reconcile_cc_capacity`` acts on the **bin capacity**, i.e. on the left factor. Arming it
therefore rescales BOTH seasons:

    summer capability  = reconciled x ratio      <-- the derate is applied a SECOND time
    off-summer capabty = reconciled

The demonstrated peak is a **realized output**: it already embodies whatever ambient
derate the plant actually suffers. Multiplying it again by the published ambient ratio is
two mechanisms for one phenomenon.

THE TEST — a measured contradiction, with no free parameter:

* **S1** — armed summer capability vs the plant's **EIA-860 published summer capacity**.
  A model that asserts a plant cannot reach its own published summer rating contradicts
  a published measurement.
* **S2** — armed summer capability vs the plant's **CEMS-demonstrated peak WITHIN the
  summer months** (same p999 construction, same ``_CC_NET_OF_GROSS``, restricted to
  Jun-Sep). A model that asserts a plant cannot reach an output it is **recorded as having
  produced** contradicts the CEMS record directly. This is the decisive leg: it is the
  same measured authority the reconcile itself invokes.
* **S3** — the off-summer leg, for contrast: armed off-summer capability vs the
  non-summer demonstrated peak and vs EIA-860's published **winter** capacity.

Usage::

    python scripts/probes/_caiso185_seasonal_stack.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    EIA_860_DIR,
    cc_capacity_reconcile_path,
)
from market_sim.data import campd  # noqa: E402
from market_sim.data.fleet.arrays import _SUMMER_MONTHS  # noqa: E402
from market_sim.data.fleet.campd_bins import cc_summer_derate_ratio  # noqa: E402

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
OUT = REPO / "results" / "calibration" / "_caiso185_seasonal_stack.json"
# The deriver's own gross->net factor, so both sides of the comparison sit on
# the identical basis (derive_cc_capacity_reconcile._CC_NET_OF_GROSS).
CC_NET_OF_GROSS = 0.975


def _seasonal_peaks(codes: set[int]) -> dict[int, dict[str, float]]:
    """Per-plant p999 of CAMPD net MW, split summer (Jun-Sep) vs off-summer.

    Same construction as ``derive_cc_capacity_reconcile._campd_p999_and_annual``
    (99.9th percentile of net MW pooled across the backcast years) but split on
    the model's OWN summer mask :data:`_SUMMER_MONTHS`, so the comparison is
    against the months the derate actually touches.
    """
    states = campd.states_for_iso(ISO)
    summer: dict[int, list[np.ndarray]] = {}
    offsummer: dict[int, list[np.ndarray]] = {}
    for year in YEARS:
        df = campd.load_campd_hourly(states, [year])
        net = campd.plant_hourly_net(df, {pid: CC_NET_OF_GROSS for pid in codes}, year)
        clock = pd.date_range(f"{year}-01-01", periods=8760, freq="h")
        is_summer = np.isin(clock.month.to_numpy(), list(_SUMMER_MONTHS))
        for pid, arr in net.items():
            if pid not in codes:
                continue
            a = np.asarray(arr, dtype=float)
            n = min(len(a), len(is_summer))
            summer.setdefault(pid, []).append(a[:n][is_summer[:n]])
            offsummer.setdefault(pid, []).append(a[:n][~is_summer[:n]])
    out: dict[int, dict[str, float]] = {}
    for pid in codes:
        rec: dict[str, float] = {}
        for label, store in (("summer", summer), ("offsummer", offsummer)):
            arrs = store.get(pid)
            if not arrs:
                continue
            pooled = np.concatenate(arrs)
            if pooled.size == 0:
                continue
            rec[f"{label}_p999_mw"] = float(np.quantile(pooled, 0.999))
            rec[f"{label}_max_mw"] = float(pooled.max())
        out[pid] = rec
    return out


def main() -> None:
    """Measure S1 / S2 / S3 for every row of the committed CAISO table."""
    table = pd.read_csv(cc_capacity_reconcile_path(ISO))
    codes = {int(c) for c in table["plant_code"]}
    peaks = _seasonal_peaks(codes)

    e860 = pd.read_parquet(EIA_860_DIR / "eia860_generator_operable.parquet")
    e860 = e860[e860["Technology"] == "Natural Gas Fired Combined Cycle"].copy()
    e860["plant_code"] = pd.to_numeric(e860["Plant Code"], errors="coerce")
    for src, dst in (
        ("Nameplate Capacity (MW)", "np_mw"),
        ("Summer Capacity (MW)", "ns_mw"),
        ("Winter Capacity (MW)", "win_mw"),
    ):
        e860[dst] = pd.to_numeric(e860[src], errors="coerce")
    e860 = e860[e860["plant_code"].notna()]
    sums = e860.groupby(e860["plant_code"].astype(int))[
        ["np_mw", "ns_mw", "win_mw"]
    ].sum()

    rows: list[dict] = []
    for r in table.itertuples(index=False):
        code = int(r.plant_code)
        ratio = cc_summer_derate_ratio(code)
        cur, rec_mw = float(r.current_mw), float(r.reconciled_mw)
        p = peaks.get(code, {})
        s = sums.loc[code] if code in sums.index else None
        row = {
            "plant_code": code,
            "plant_name": str(r.plant_name),
            "mode": str(r.mode),
            "cc_summer_derate_ratio": None if ratio is None else round(ratio, 5),
            "bin_capacity_unarmed_mw": round(cur, 1),
            "bin_capacity_armed_mw": round(rec_mw, 1),
            "eia860_cc_nameplate_mw": None if s is None else round(float(s.np_mw), 1),
            "eia860_cc_summer_mw": None if s is None else round(float(s.ns_mw), 1),
            "eia860_cc_winter_mw": None if s is None else round(float(s.win_mw), 1),
            "cems_summer_p999_mw": round(p.get("summer_p999_mw", float("nan")), 1),
            "cems_summer_max_mw": round(p.get("summer_max_mw", float("nan")), 1),
            "cems_offsummer_p999_mw": round(p.get("offsummer_p999_mw", float("nan")), 1),
            "cems_offsummer_max_mw": round(p.get("offsummer_max_mw", float("nan")), 1),
        }
        rr = 1.0 if ratio is None else float(ratio)
        summer_unarmed = cur * rr
        summer_armed = rec_mw * rr
        row["summer_capability_unarmed_mw"] = round(summer_unarmed, 1)
        row["summer_capability_armed_mw"] = round(summer_armed, 1)
        # S1 — against the published summer rating.
        if s is not None and float(s.ns_mw) > 0.0:
            row["s1_armed_over_published_summer"] = round(
                summer_armed / float(s.ns_mw), 4
            )
            row["s1_contradiction"] = bool(summer_armed < float(s.ns_mw) * 0.99)
        # S2 — against the plant's OWN measured summer output (the decisive leg).
        sp = p.get("summer_p999_mw")
        if sp:
            row["s2_armed_over_cems_summer_p999"] = round(summer_armed / sp, 4)
            row["s2_contradiction"] = bool(summer_armed < sp * 0.99)
        sm = p.get("summer_max_mw")
        if sm:
            row["s2b_armed_over_cems_summer_max"] = round(summer_armed / sm, 4)
        # S3 — the off-summer leg, for contrast.
        op = p.get("offsummer_p999_mw")
        if op:
            row["s3_armed_over_cems_offsummer_p999"] = round(rec_mw / op, 4)
            row["s3_unarmed_over_cems_offsummer_p999"] = round(cur / op, 4)
        if s is not None and float(s.win_mw) > 0.0:
            row["s3_cems_offsummer_p999_over_published_winter"] = (
                None if not op else round(op / float(s.win_mw), 4)
            )
            row["s3_unarmed_over_published_winter"] = round(cur / float(s.win_mw), 4)
        rows.append(row)

    out = {
        "iso": ISO,
        "years": YEARS,
        "summer_months": sorted(_SUMMER_MONTHS),
        "cc_net_of_gross": CC_NET_OF_GROSS,
        "pre_registered": False,
        "rows": rows,
        "s1_contradictions": [
            r["plant_code"] for r in rows if r.get("s1_contradiction")
        ],
        "s2_contradictions": [
            r["plant_code"] for r in rows if r.get("s2_contradiction")
        ],
    }
    OUT.write_text(json.dumps(out, indent=1))
    print(json.dumps(out, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
