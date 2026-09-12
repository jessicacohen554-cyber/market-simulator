"""caiso-278 phase 0: size the CAISO import-hub-price repair BEFORE any LP.

THE OBJECT, AND WHY IT IS ADMISSIBLE
------------------------------------
``IMPORT_TRANCHES["CAISO"]`` prices every import block at a STATIC hand value in
every month of every year — PNW_hydro_base $28, PNW_midC $36, DSW_solar_PV $48,
DSW_CCGT $68, DSW_CT $110, WECC_scarcity $180 — and
``inject_caiso_import_hub_prices``'s own docstring says what those numbers are:

    "the static ladder was re-fit against the model's own (too-high) solved
     price, so the import blocks that set the CAISO LMP in its cheaper hours sit
     ~$15-20 above the real delivered cost, and never go negative"

A value fitted to the model's own output is exactly what rules 1 ``[R-STRUCT]``
and 24 ``[R-REGISTRY]`` forbid today, and the measured replacement exists: the
WECC intertie scheduling-point nodal LMP (MALIN / PALOVRDE), committed at
``data/raw/_validation-source/wecc_intertie_lmp_hourly_CAISO.parquet``. Replacing
a fitted number with the measured delivered cost is rule 14 ``[R-ACCURATE]``, and
it regenerates for a forward year from forward hub curves (rule 13
``[R-MEASURED]``).

THE ARM THIS PROBE WAS WRITTEN FOR IS **KILLED** — AND NOT BY P-1
------------------------------------------------------------------
**READ THIS BEFORE THE RESULTS.** The probe was written on caiso-275 §4
disclosure 5's reading, that ``inject_caiso_import_hub_prices`` carries a live
matcher BUG: it matches rows with a RAW ``uid.startswith(f"{IMPORT_ZONE[iso]}_")``
— i.e. ``WECC_import_`` only — while its two siblings
(``inject_caiso_import_gas_coupling``, ``inject_caiso_import_solar_shape``) were
repaired to use the per-hub-aware ``_caiso_import_tranche_of``, so under the
keeper's armed ``caiso_per_hub_intertie`` (rows in ``WECC_PNW`` / ``WECC_DSW``)
it reprices zero rows.

**P-1 reproduces that row count exactly (0 raw vs 12 per-hub-aware) and the
reading is STILL WRONG.** The call site is
``scripts/run_calibration.py:5021``::

    if legacy_intertie and getattr(config, "caiso_import_hub_prices", False):

gated on ``legacy_intertie``, with the comment "Superseded by the per-hub node;
gated to the legacy pooled topology only." **The raw matcher is CONSISTENT WITH
ITS OWN GATE** — the function only ever runs on the legacy pooled topology,
where the rows really are ``WECC_import_*``. Under the per-hub topology the
whole branch is skipped and the matcher never executes. So there is nothing to
repair, and ``caiso_per_hub_intertie`` (armed) already prices each corridor at
its own measured hub — the successor the comment names.

caiso-275 §4.5's "a real code defect, recorded" is therefore **itself
mistaken**; its *conclusion* (do not arm the flag) was right, for a different
reason. P-2's measured-vs-ladder deltas below are consequently measured against
**the wrong baseline** — the static ladder is not what is live — and are kept
only as the record of how the arm died.

WHAT THIS PROBE ESTABLISHES, ZERO LP
------------------------------------
P-1  THE ROW COUNTS, raw matcher vs ``_caiso_import_tranche_of``, on the
     keeper's own fleet. Measured 0 and 12 — which is what the gated call site
     implies, NOT a live defect (see above).
P-2  THE PRE-SOLVE OFFER DELTA, per tranche per month per year: measured
     delivered hub price (+ wheel + border carbon, the injector's own
     arithmetic) minus the static ladder value. This is the magnitude any
     dispatch response must be bounded by, computed before a solve exists.
P-3  THE SCREEN YEAR, chosen on the MECHANISM'S OWN FOOTPRINT — the year whose
     measured |delta| x hours is largest on the tranches that actually carry
     marginal weight — and NEVER on the price residual (rule 29 ``[R-SCREEN]``
     step 1, rule 1 ``[R-STRUCT]``).
P-4  COVERAGE, stated before it can embarrass anyone: the 2023 series is
     incomplete (caiso-276 charter §5) and the injector silently keeps the
     static ladder in uncovered hours. Measure the gap per year.

It arms nothing and selects nothing on the residual.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

OUT = REPO / "results/calibration/_caiso278_hubprice_phase0.json"
YEARS = (2022, 2023, 2024, 2025)
T = 8760
_MD = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum((0,) + tuple(d * 24 for d in _MD))[:12]
#: Marginal load-weight each import tranche carried in the caiso-276 §5c census
#: (all-8760 window, CAISO 2022). Used ONLY to weight the footprint ranking
#: toward blocks that can actually set price — it is a measured property of the
#: mechanism's reach, not a residual.
MARGINAL_WEIGHT_2022 = {"PNW_midC": 0.1376, "DSW_solar_PV": 0.0574}


def main() -> None:
    from market_sim.config.interchange_config import (
        CAISO_IMPORT_DELIVERY_BASIS,
        IMPORT_TRANCHES,
        IMPORT_TRANCHE_EF,
    )
    from market_sim.config.constants import CARB_UNSPECIFIED_IMPORT_EF
    from market_sim.data.eia930.envelopes import measured_import_hub_prices
    from market_sim.model.interchange.caiso import (
        _caiso_import_tranche_of,
        wecc_border_carbon_adder,
    )
    from market_sim.config.interchange_config import IMPORT_ZONE

    out: dict = {
        "session": "caiso-278",
        "phase": 0,
        "object": "caiso_import_hub_prices matcher repair + arming",
    }
    ladder = {name: float(vom) for name, _cap, vom in IMPORT_TRANCHES["CAISO"]}
    out["static_ladder"] = ladder
    print("=== the static hand-fitted ladder (IMPORT_TRANCHES['CAISO']) ===")
    for k, v in ladder.items():
        print(f"  {k:<16s} ${v:>7.2f}/MWh   (every month of every year)")

    # ---------------- P-1: the matcher bug, on the keeper's own fleet ----------
    print("\n=== P-1  the matcher bug, measured on the keeper's own fleet ===")
    from scripts.lib.bundle_fleet import reconstruct_bundle_fleet

    bundle = REPO / "results/calibration/caiso275_B_gascoupling_2022"
    state, meta = reconstruct_bundle_fleet(
        bundle, 2022, required_flags=(), required_sequences=()
    )
    fa = state["fleet_arrays"]
    zone = IMPORT_ZONE.get("CAISO")
    uids = list(fa.unit_ids)
    raw = [u for u in uids if zone and str(u).startswith(f"{zone}_")]
    perhub = [u for u in uids if _caiso_import_tranche_of(str(u), zone) is not None]
    tranche_rows: dict[str, list[str]] = {}
    for u in perhub:
        t = _caiso_import_tranche_of(str(u), zone)
        tranche_rows.setdefault(str(t), []).append(str(u))
    out["P1_matcher"] = {
        "keeper_git_sha": meta.get("git_sha"),
        "import_zone_default": zone,
        "rows_matched_RAW_startswith": len(raw),
        "rows_matched_PERHUB_aware": len(perhub),
        "tranches_reachable": sorted(tranche_rows),
        "call_site": "scripts/run_calibration.py:5021, gated on `legacy_intertie`",
        "verdict": (
            "ROW COUNTS AS EXPECTED FOR A GATED CALL SITE — 0 raw / N per-hub. "
            "This is NOT a live defect: the call site is gated on "
            "`legacy_intertie` ('Superseded by the per-hub node; gated to the "
            "legacy pooled topology only'), so the raw matcher is consistent "
            "with its own gate and never runs under the armed per-hub topology. "
            "caiso-275 §4.5's 'real code defect' reading is refuted; the arm is "
            "KILLED and nothing is to be repaired."
            if not raw and perhub
            else "unexpected"
        ),
    }
    print(f"  keeper git_sha            {meta.get('git_sha')}")
    print(f"  IMPORT_ZONE['CAISO']      {zone}")
    print(f"  rows matched, RAW matcher (what the flag uses today)   {len(raw)}")
    print(f"  rows matched, per-hub-aware (the one-line repair)      {len(perhub)}")
    print(f"  tranches reachable after repair: {sorted(tranche_rows)}")
    print(f"  VERDICT: {out['P1_matcher']['verdict']}")

    # ---------------- P-2 / P-4: the pre-solve delta and coverage --------------
    border = wecc_border_carbon_adder(float(state["config"].carbon_price or 0.0))
    out["border_carbon_adder"] = round(border, 4)
    print(
        f"\n  (CARB border adder at the keeper's carbon price: "
        f"${border:.3f}/MWh at the unspecified EF)"
    )

    rows = []
    cov = []
    for year in YEARS:
        prices = measured_import_hub_prices("CAISO", year, T)
        if not prices:
            cov.append({"year": year, "status": "NO MEASURED SERIES"})
            print(
                f"\n  !! {year}: no measured hub series — the injector would "
                f"return False and keep the static ladder"
            )
            continue
        for tr, arr in sorted(prices.items()):
            a = np.asarray(arr, float)
            _loss, wheel = CAISO_IMPORT_DELIVERY_BASIS.get(tr, (0.0, 0.0))
            ef = IMPORT_TRANCHE_EF.get("CAISO", {}).get(tr, CARB_UNSPECIFIED_IMPORT_EF)
            delivered = a + wheel + border * (ef / CARB_UNSPECIFIED_IMPORT_EF)
            static = ladder.get(tr)
            if static is None:
                continue
            d = delivered - static
            fin = np.isfinite(d)
            cov.append(
                {
                    "year": year,
                    "tranche": tr,
                    "hours_finite": int(fin.sum()),
                    "coverage_pct": round(100 * float(fin.mean()), 2),
                    "wheel": wheel,
                    "ef_ratio": round(ef / CARB_UNSPECIFIED_IMPORT_EF, 3),
                }
            )
            midx = np.clip(np.searchsorted(_CUM, np.arange(T), side="right") - 1, 0, 11)
            for m in range(12):
                sel = (midx == m) & fin
                if not sel.any():
                    continue
                rows.append(
                    {
                        "year": year,
                        "tranche": tr,
                        "month": m + 1,
                        "measured_delivered": round(float(delivered[sel].mean()), 2),
                        "static": static,
                        "delta": round(float(d[sel].mean()), 2),
                        "hours": int(sel.sum()),
                        "hours_negative_measured": int((delivered[sel] < 0).sum()),
                    }
                )
    out["P4_coverage"] = cov
    out["P2_monthly_delta"] = rows
    df = pd.DataFrame(rows)

    print(
        "\n=== P-4  measured-series coverage (uncovered hours keep the static "
        "ladder, silently) ==="
    )
    print("  year  tranche           hours    cov%   wheel  efRatio")
    for c in cov:
        if "tranche" not in c:
            print(f"  {c['year']}  {c['status']}")
            continue
        print(
            f"  {c['year']}  {c['tranche']:<16s}{c['hours_finite']:>6d}"
            f"{c['coverage_pct']:>8.2f}{c['wheel']:>8.2f}{c['ef_ratio']:>9.3f}"
        )

    print("\n=== P-2  PRE-SOLVE OFFER DELTA, annual mean by tranche-year ===")
    print("  year  tranche          measured  static    DELTA   negHrs")
    ann = []
    for (y, tr), g in df.groupby(["year", "tranche"]):
        wsum = g["hours"].sum()
        dm = float((g["delta"] * g["hours"]).sum() / wsum)
        mm = float((g["measured_delivered"] * g["hours"]).sum() / wsum)
        neg = int(g["hours_negative_measured"].sum())
        ann.append(
            {
                "year": int(y),
                "tranche": tr,
                "measured": round(mm, 2),
                "static": ladder[tr],
                "delta": round(dm, 2),
                "hours": int(wsum),
                "neg_hours": neg,
                "abs_delta_hours": round(abs(dm) * int(wsum), 0),
            }
        )
        print(f"  {y}  {tr:<16s}{mm:>9.2f}{ladder[tr]:>8.2f}{dm:>+9.2f}{neg:>9d}")
    out["P2_annual"] = ann

    # ---------------- P-3: the screen year, on FOOTPRINT ----------------------
    # Footprint = sum over tranches of |annual delta| x covered hours x that
    # tranche's MEASURED marginal load-weight (caiso-276 §5c). Tranches with no
    # measured marginal weight contribute 0 — they cannot set price, so a large
    # delta on them is not a price footprint. NOTHING here reads C3a.
    print("\n=== P-3  SCREEN-YEAR SELECTION, on the mechanism's own footprint ===")
    print("  (footprint = SUM_tranche |delta| x covered hours x that tranche's")
    print("   MEASURED marginal load-weight from caiso-276 §5c; no residual read)")
    fp = {}
    for a in ann:
        w = MARGINAL_WEIGHT_2022.get(a["tranche"], 0.0)
        fp[a["year"]] = fp.get(a["year"], 0.0) + abs(a["delta"]) * a["hours"] * w
    print("  year   footprint (MWh-weighted $/MWh)   rank")
    order = sorted(fp, key=lambda y: -fp[y])
    for y in sorted(fp):
        print(f"  {y}   {fp[y]:>26,.0f}   {order.index(y) + 1}")
    out["P3_footprint"] = {str(k): round(v, 1) for k, v in fp.items()}
    out["P3_screen_year"] = order[0] if order else None
    out["P3_basis"] = (
        "largest measured |delta| x covered-hours x marginal-weight "
        "footprint; chosen before any solve and with no reference "
        "to the price residual (rules 1 / 29)"
    )
    print(
        f"\n  SCREEN YEAR = {out['P3_screen_year']}  "
        f"(the mechanism's own footprint is largest there)"
    )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
