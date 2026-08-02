"""ERCOT-149 Phase 0 (no LP): gas-side COP-vs-window collision quantification.

The ERCOT-148 named successor (diagnosis section 6.1; open owner ruling #7).
ERCOT-148 proved the DAM COP plant pin RESTORES availability over measured
CAMPD full-stop windows on the COAL fleet and capped it coal-scoped
(``ercot_dam_availability_coal_event_cap``, keeper
``2026-07-31-ercot148-dam-event-cap``). The SYMMETRIC gas question — committed
event-based CC/ST dead-stop windows vs the COP ``OFF``-at-full-HSL convention —
was left explicitly UNMEASURED, and the coal adjudication does NOT transfer:
gas is load-following (``OFF``-is-available is genuinely correct there) and the
gas windows passed a different (event-based) detector. This probe produces the
measurement Phase 1 adjudicates from, per gas plant x 2023-2025, with NO LP:

1. **Model dispatch above the measured-window ceiling** — the keeper's own
   hourly per-plant dispatch, decoded from the committed dashboard payload
   (``frontend/data/backcast/runs/<id>.js``: gzip+base64 JSON;
   ``plants[<code>].m`` is base64 uint8 of ``100 x MW / nameplate``, recovered
   in MW by rescaling the byte series so its annual sum equals the payload's
   own ``m_ann`` TWh — self-normalizing, no nameplate join). Decode + ceiling
   machinery is VERIFIED against the ERCOT-148 committed coal quantification:
   on the superseded ``2026-07-31-ercot145-gas-daily-shape`` payload it
   reproduces the 4.36/4.98/5.01 TWh coal phantom per plant to 0.01 TWh.
   The ceiling is the loader's own product exactly as the incumbent cap
   composes it (``arrays.py`` ERCOT-148 block): >= 5-day unit windows
   (:func:`market_sim.data.outages.unit_outage_derate_factors`) x ERCOT
   plant-grain partial plateaus (:func:`partial_outage_derate_factors`),
   on the bins-sheet plant capacity. Both layers are armed incumbents on gas
   in the keeper (``outage_source='historic'`` applies the unit windows to
   EVERY plant group, arrays.py:1026; the partial plateaus per plant code,
   arrays.py:1226) — the DAM overlay is applied after both and restores over
   them, exactly the coal seam.
2. **COP conduct during each committed window** — for DAM-crosswalked plants,
   the measured site live/rating fraction
   (:func:`ercot_thermal_dam_availability_plant_series`) averaged over the
   window: ~1 means the pin holds the plant near-fully available through the
   dead stop; ~0 means the pin agrees with the window (honest-OUT control).
3. **In-merit conduct during each committed window** — the merit-order
   guard's own instrument (``scripts.lib.outage_detect.build_merit_order_panel``
   / ``out_of_merit_share``, the same measured SRMC-vs-revealed-clearing-cost
   panel that routed provable economic layups to the layup companion when the
   extract was derived): the share of the window the unit's measured SRMC sat
   ABOVE the revealed marginal cost of the capacity that was running. ~0 means
   the unit was IN MERIT through the span yet produced nothing — the
   layup reading is untenable and the dead stop is mechanical.
4. **Channel attribution** — a crosswalked plant's restore is the plant PIN;
   an unmapped plant can only be restored by the DAM class-hour water-fill /
   residual redistribution (same overlay; the incumbent cap bounds either).
   For the mapped channel, ``MAPPED_SITE_STRUCTURE`` records the measured
   site-coverage anatomy (2024 disclosure resource inventory + crosswalk
   ``p98_rating/plant_nameplate``): full-coverage sites vs partial acceptance
   (crosswalk accepts a subset of the plant's DAM sites) vs config-collapse
   train-aliasing (``_site()`` folds two physical CC trains into one site, so
   live = max(train1, train2) can never see a single-train outage).
5. **No-overlay controls** — CC_CHP / CT_CHP carry windows but are excluded
   from the DAM overlay by the deriver's class scope, so their above-ceiling
   dispatch bounds the machinery's noise floor. Verified: the CHP "phantom"
   is a flat in-window offset equal to the dashboard render's CHP-only BTM
   adder (Pasadena 2024: 39.1 MW mean phantom = the flat adder; in deep
   windows the decoded series sits exactly at ceiling + adder), i.e. true CHP
   dispatch respects the windowed ceiling — nothing restores CHP, and the
   CC/ST payloads carry no BTM adder, so their phantom is real dispatch.
6. **Event-day exposure** — the windowed-out scoped-gas capacity (sum of
   cap x (1 - ceiling factor)) on each year's top window-envelope days and on
   the known in-sample scarcity event days, to size the precommit's C3c /
   spurious-tail risk before any arm.

Pure data reconciliation: no LP, no dispatch, no scoring, no solve.

Usage:
    python scripts/probes/ercot149_gas_outage_phase0.py \
        [--years 2023 2024 2025] [--no-oom] \
        [--payload frontend/data/backcast/runs/2026-07-31-ercot148-dam-event-cap.js] \
        [--compare-payload frontend/data/backcast/runs/2026-07-31-ercot145-gas-daily-shape.js] \
        [--json-out results/calibration/ercot149_gas_outage_phase0.json]
"""

from __future__ import annotations

import argparse
import base64
import gzip
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import (  # noqa: E402
    CAMPD_BINS_CSV,
    RAW_DATA_DIR,
    REFERENCE_DIR,
)
from market_sim.data.fleet import load_campd_bins  # noqa: E402
from market_sim.data.outages import (  # noqa: E402
    UNIT_OUTAGE_MIN_DAYS,
    ercot_thermal_dam_availability_plant_series,
    partial_outage_derate_factors,
    unit_outage_derate_factors,
)

HOURS = 8760
# DAM-covered gas classes (the deriver's scope) vs the no-overlay CHP controls.
DAM_GAS_CLASSES = ("CC_REGULAR", "ST_GAS", "CT_PEAKER")
CONTROL_CLASSES = ("CC_CHP", "CT_CHP")
SCOPE = DAM_GAS_CLASSES + CONTROL_CLASSES

# Measured site-coverage anatomy of the accepted gas crosswalk rows (evidence:
# 2024 Gen_Resource disclosure resource inventory per collapsed site + the
# crosswalk's own p98_rating_mw / plant_nameplate_mw ratio; commands in
# docs/DIAGNOSIS-ercot149-gas-cop-window-2026-08-01.md section 3). "aliased" =
# the deriver's _site() config-collapse folds >= 2 physical CC train families
# (<PLANT>_CC1_*, <PLANT>_CC2_*) into ONE site whose live capability is the
# MAX across trains — a single-train outage is invisible to the pin even when
# the dead train's configs file OUT honestly. "partial" = the crosswalk
# accepts a subset of the plant's DAM sites (ratio well below 1), so the pin
# applies one unit's/train's fraction to the whole model plant bin. "covered" =
# accepted site(s) span the plant (ratio ~1); a high in-window fraction there
# is the QSE's own OFF-at-HSL filing through the dead stop (the coal-side
# Coleto/Limestone conduct signature).
MAPPED_SITE_STRUCTURE: dict[int, tuple[str, str]] = {
    55153: ("aliased", "GUADG_CC1+CC2 (559/558 MW) collapse to site GUADG; ratio 0.51"),
    55501: ("aliased", "KMCHI_CC1+CC2 (676/676 MW) collapse to site KMCHI; ratio 0.47"),
    55230: ("partial", "JACKCNTY covers train 1 only; train 2 is site JCKCNTY2 (not accepted); ratio 0.49"),
    3612: ("partial", "BRAUNIG_VHB3 only; VHB1/VHB2/VHB6CT5-8 not accepted; ratio 0.35"),
    3601: ("partial", "GIDEON_GIDEONG3 only; GIDEONG1/G2 not accepted; ratio 0.52"),
    3576: ("partial", "OLINGR_OLING_3 only (1 of 3 units); ratio 0.33"),
    7900: ("partial", "SANDHSYD (CC train, 300 MW) only; SH1-7 CTs not accepted; ratio 0.43"),
    6243: ("partial", "DANSBY_DANSBYG1 only; ratio 0.51"),
    3443: ("covered", "VICTORIA single train; ratio 0.76"),
    3441: ("covered", "NUECES_B single site; ratio 0.89"),
    55137: ("covered", "RIONOG single train; ratio 0.88"),
    55154: ("covered", "LOSTPI single train; ratio 0.89"),
    7512: ("covered", "BRAUNIG (Arthur Von Rosenberg) single train; ratio 0.90"),
    55545: ("covered", "DUKE (Hidalgo) single train; ratio 0.94"),
    4937: ("covered", "FERGCC single train; ratio 0.98"),
    55168: ("covered", "BASTEN single train; ratio 0.98"),
}

# Known in-sample scarcity event days (C3c context): the June/Sep-2023 RT tail
# clusters and Winter Storm Heather (Jan 2024).
EVENT_DAYS = {
    2023: ["2023-06-20", "2023-06-27", "2023-08-17", "2023-09-06", "2023-09-07"],
    2024: ["2024-01-15", "2024-01-16", "2024-01-17", "2024-05-08", "2024-08-20"],
    2025: ["2025-02-19", "2025-08-01"],
}


def load_payload(path: Path) -> dict:
    """Decode a dashboard run payload (gzip+base64 JSON in a JS wrapper)."""
    raw = Path(path).read_text()
    m = re.search(r'runGz\["[^"]+"\]="(.*)";?\s*$', raw, re.S)
    if m is None:
        raise SystemExit(f"no runGz payload found in {path}")
    return json.loads(gzip.decompress(base64.b64decode(m.group(1))))


def decode_plant_mw(entry: dict) -> np.ndarray | None:
    """Recover a plant's hourly model MW from its payload entry.

    ``m`` is base64 uint8 of ``100 x MW / nameplate`` (render_calibration_html
    ``_b64``); the byte series is rescaled so its annual sum equals the
    payload's own ``m_ann`` (TWh), which recovers MW without a nameplate join.
    Returns None for an all-zero series (scale undefined, dispatch is zero).
    """
    b = np.frombuffer(base64.b64decode(entry["m"]), dtype=np.uint8).astype(float)
    if b.shape[0] < HOURS:
        b = np.concatenate([b, np.zeros(HOURS - b.shape[0])])
    tot = float(b.sum())
    if tot <= 0.0:
        return None
    return b[:HOURS] * (float(entry["m_ann"]) * 1e6 / tot)


def window_rows(win: pd.DataFrame, year: int) -> pd.DataFrame:
    """The committed >= 5-day rows overlapping ``year`` for the scoped classes."""
    return win[
        (win["plant_group"].isin(SCOPE))
        & (win["duration_days"] >= UNIT_OUTAGE_MIN_DAYS)
        & (win["outage_end"] >= f"{year}-01-01")
        & (win["outage_start"] <= f"{year}-12-31")
    ]


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument(
        "--payload",
        default=str(
            REPO
            / "frontend/data/backcast/runs/2026-07-31-ercot148-dam-event-cap.js"
        ),
        help="keeper run payload the phantom is measured on",
    )
    ap.add_argument(
        "--compare-payload",
        default=str(
            REPO
            / "frontend/data/backcast/runs/2026-07-31-ercot145-gas-daily-shape.js"
        ),
        help="prior-keeper payload (gas classes byte-identical at the seam; "
        "a matching phantom shows the collision is not an ERCOT-148 artifact)",
    )
    ap.add_argument(
        "--no-oom",
        action="store_true",
        help="skip the per-window merit-panel out-of-merit shares (faster)",
    )
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    bins = load_campd_bins(str(CAMPD_BINS_CSV))
    cap = {
        (int(c), str(g)): float(m)
        for c, g, m in zip(
            bins["Plant_Code"], bins["Plant_Group"], bins["capacity_mw"]
        )
        if m and m > 0
    }
    plant_name = {
        int(c): str(n)
        for c, n in zip(bins["Plant_Code"], bins.get("Plant_Name", bins["Plant_Code"]))
    }
    group_of: dict[int, list[str]] = {}
    for (c, g) in cap:
        group_of.setdefault(c, []).append(g)

    win = pd.read_csv(
        RAW_DATA_DIR / "campd-unit-outages.csv",
        parse_dates=["outage_start", "outage_end"],
    )
    xw = pd.read_csv(REFERENCE_DIR / "ercot-dam-plant-crosswalk.csv")
    mapped_codes = set(xw[xw["accepted"] == 1]["plant_code"].astype(int))

    payloads = [("keeper", load_payload(Path(args.payload)))]
    if args.compare_payload and Path(args.compare_payload).exists():
        payloads.append(("prior", load_payload(Path(args.compare_payload))))

    # CT_PEAKER carries no outage overlay by design — assert, don't assume.
    n_ct = len(win[win["plant_group"] == "CT_PEAKER"])
    if n_ct:
        print(f"WARNING: {n_ct} CT_PEAKER rows in the windows CSV (expected 0)")

    oom_panels: dict[int, object] = {}
    if not args.no_oom:
        from scripts.lib.outage_detect import build_merit_order_panel

        for year in args.years:
            oom_panels[year] = build_merit_order_panel("ERCOT", year, HOURS, ("TX",))

    plant_year: list[dict] = []
    spells: list[dict] = []
    class_year: dict[tuple[str, int, str], dict] = {}
    event_exposure: list[dict] = []

    for year in args.years:
        uf = unit_outage_derate_factors(year, HOURS, str(CAMPD_BINS_CSV), iso="ERCOT")
        pf = partial_outage_derate_factors(year, HOURS)
        dam = ercot_thermal_dam_availability_plant_series(year, HOURS)
        wy = window_rows(win, year)
        base = pd.Timestamp(f"{year}-01-01")

        # Plants in scope this year: any scoped class with a full-stop window
        # row or a plant-grain partial plateau on a scoped plant.
        codes = set(wy["facility_id"].astype(int))
        for c in pf:
            for g in group_of.get(int(c), []):
                if g in SCOPE:
                    codes.add(int(c))

        # Windowed-out scoped-gas capacity by hour (the DAM-covered classes
        # only — what a widened cap could actually bind on).
        removed_mw = np.zeros(HOURS)

        for code in sorted(codes):
            groups = [g for g in group_of.get(code, []) if g in SCOPE]
            for grp in groups:
                key = (code, grp)
                if key not in cap:
                    continue
                f = np.ones(HOURS)
                w = uf.get(key)
                if w is not None:
                    f = f * w[:HOURS]
                q = pf.get(code)
                if q is not None:
                    f = f * q[:HOURS]
                windowed = f < 0.999
                if not windowed.any():
                    continue
                ceil_mw = cap[key] * f
                if grp in DAM_GAS_CLASSES:
                    removed_mw += cap[key] * (1.0 - f)
                dam_frac = dam.get(code)
                mech = MAPPED_SITE_STRUCTURE.get(code, (None, None))
                row: dict = {
                    "year": year,
                    "plant": plant_name.get(code, str(code)),
                    "code": code,
                    "grp": grp,
                    "cap_mw": round(cap[key], 1),
                    "windowed_days": round(float(windowed.sum()) / 24.0, 1),
                    "mapped": code in mapped_codes,
                    "site_structure": mech[0] if code in mapped_codes else None,
                    "dam_frac_win": (
                        round(float(np.nanmean(dam_frac[windowed])), 3)
                        if dam_frac is not None
                        and np.isfinite(dam_frac[windowed]).any()
                        else None
                    ),
                }
                for lbl, pay in payloads:
                    pl = pay["years"][str(year)]["plants"]
                    entry = pl.get(str(code)) or pl.get(f"{code}:{grp}")
                    mw = decode_plant_mw(entry) if entry is not None else None
                    if mw is None:
                        row[f"phantom_twh_{lbl}"] = 0.0 if entry is not None else None
                        continue
                    ph = float(np.maximum(0.0, mw - ceil_mw)[windowed].sum()) / 1e6
                    row[f"phantom_twh_{lbl}"] = round(ph, 4)
                    if lbl == "keeper":
                        row["m_ann_twh"] = round(float(entry["m_ann"]), 3)
                        row["win_model_twh"] = round(float(mw[windowed].sum()) / 1e6, 4)
                        row["win_ceiling_twh"] = round(
                            float(ceil_mw[windowed].sum()) / 1e6, 4
                        )
                plant_year.append(row)

                ch = "mapped" if row["mapped"] else "unmapped"
                for bucket in ("all", ch):
                    agg = class_year.setdefault(
                        (grp, year, bucket),
                        {"phantom_keeper": 0.0, "phantom_prior": 0.0, "wdays": 0.0},
                    )
                    agg["phantom_keeper"] += row.get("phantom_twh_keeper") or 0.0
                    agg["phantom_prior"] += row.get("phantom_twh_prior") or 0.0
                    agg["wdays"] += row["windowed_days"]

        # Per committed window row: COP conduct + in-merit conduct.
        pl_keeper = payloads[0][1]["years"][str(year)]["plants"]
        panel = oom_panels.get(year)
        for r in wy.itertuples(index=False):
            code = int(r.facility_id)
            start = max(pd.Timestamp(r.outage_start), base)
            stop = min(
                pd.Timestamp(r.outage_end) + pd.Timedelta(days=1),
                pd.Timestamp(f"{year + 1}-01-01"),
            )
            lo = int((start - base).total_seconds() // 3600)
            hi = min(HOURS, int((stop - base).total_seconds() // 3600))
            if hi <= lo:
                continue
            dam_frac = dam.get(code)
            entry = pl_keeper.get(str(code))
            mw = decode_plant_mw(entry) if entry is not None else None
            grp = str(r.plant_group)
            pcap = cap.get((code, grp))
            oom = (
                panel.out_of_merit_share((code, str(r.unit_id)), lo, hi)
                if panel is not None
                else None
            )
            spells.append(
                {
                    "year": year,
                    "plant": str(r.facility_name),
                    "code": code,
                    "unit": str(r.unit_id),
                    "grp": grp,
                    "unit_mw": float(r.unit_capacity_mw),
                    "start": str(start.date()),
                    "end": str((stop - pd.Timedelta(hours=1)).date()),
                    "days": round((hi - lo) / 24.0, 1),
                    "mapped": code in mapped_codes,
                    "dam_frac": (
                        round(float(np.nanmean(dam_frac[lo:hi])), 3)
                        if dam_frac is not None and np.isfinite(dam_frac[lo:hi]).any()
                        else None
                    ),
                    "oom_share": None if oom is None else round(float(oom), 3),
                    "model_mean_mw": (
                        round(float(mw[lo:hi].mean()), 1) if mw is not None else None
                    ),
                    "plant_cap_mw": round(pcap, 1) if pcap else None,
                }
            )

        # Event-day exposure: windowed-out DAM-class gas MW on the known event
        # days + the year's top-5 window-envelope days.
        daily = removed_mw[: 365 * 24].reshape(365, 24).max(axis=1)
        clock = pd.date_range(f"{year}-01-01", periods=365, freq="D")
        top = np.argsort(daily)[::-1][:5]
        for d in top:
            event_exposure.append(
                {
                    "year": year,
                    "day": str(clock[d].date()),
                    "kind": "top-envelope",
                    "windowed_out_gas_mw": round(float(daily[d]), 0),
                }
            )
        for ds in EVENT_DAYS.get(year, []):
            d = (pd.Timestamp(ds) - base).days
            if 0 <= d < 365:
                event_exposure.append(
                    {
                        "year": year,
                        "day": ds,
                        "kind": "event-day",
                        "windowed_out_gas_mw": round(float(daily[d]), 0),
                    }
                )

    py = pd.DataFrame(plant_year).sort_values(
        ["year", "phantom_twh_keeper"], ascending=[True, False]
    )
    sp = pd.DataFrame(spells).sort_values(["year", "grp", "code", "start"])

    pd.set_option("display.width", 260)
    print(
        "\n=== ERCOT-149 Phase 0: gas dispatch above the measured-window "
        "ceiling (keeper payload; prior payload as robustness) ===\n"
    )
    print(py.to_string(index=False))

    print("\n=== class x year totals (TWh above windowed ceiling) ===\n")
    cy_rows = []
    for (grp, year, ch), v in sorted(class_year.items()):
        cy_rows.append(
            {
                "grp": grp,
                "year": year,
                "channel": ch,
                "phantom_twh_keeper": round(v["phantom_keeper"], 3),
                "phantom_twh_prior": round(v["phantom_prior"], 3),
                "windowed_plant_days": round(v["wdays"], 1),
            }
        )
    cy = pd.DataFrame(cy_rows)
    print(cy.to_string(index=False))

    print(
        "\n=== committed windows: COP conduct (dam_frac ~1 = pin holds the "
        "plant available through the dead stop; ~0 = pin agrees with the "
        "window) + in-merit conduct (oom_share ~0 = in merit through the "
        "span, layup untenable) ===\n"
    )
    print(sp.to_string(index=False))

    hot = sp[(sp["mapped"]) & (sp["dam_frac"].fillna(0) > 0.5)]
    print(
        "\n=== windows at PINNED plants with in-window COP fraction > 0.5 "
        "(the coal-side collision signature) ===\n"
    )
    print(hot.to_string(index=False) if len(hot) else "(none)")

    print("\n=== event-day / top-envelope windowed-out gas capacity ===\n")
    ee = pd.DataFrame(event_exposure)
    print(ee.to_string(index=False))

    if args.json_out:
        Path(args.json_out).write_text(
            json.dumps(
                {
                    "plant_years": py.to_dict(orient="records"),
                    "class_years": cy.to_dict(orient="records"),
                    "windows": sp.to_dict(orient="records"),
                    "event_exposure": ee.to_dict(orient="records"),
                    "mapped_site_structure": {
                        str(k): {"mechanism": v[0], "evidence": v[1]}
                        for k, v in MAPPED_SITE_STRUCTURE.items()
                    },
                },
                indent=1,
                default=str,
            )
        )
        print(f"\nwrote {args.json_out}")


if __name__ == "__main__":
    main()
