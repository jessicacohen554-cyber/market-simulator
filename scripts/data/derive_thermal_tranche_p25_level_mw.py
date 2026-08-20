"""Derive the per-plant must-run floor LEVEL as measured MW, not a reconstructed CF.

``scripts/data/derive_thermal_tranches.py`` publishes ``p25_cf`` — the 25th
percentile of the plant's **available-capacity** factor over its online hours::

    acf      = net_MW / (nameplate x avail_mult)      # avail_mult is HOURLY
    p25_cf   = percentile(acf[online], 25)

and ``campd_bins.thermal_tranche_p25_level`` reconstructs a floor LEVEL from it as
``p25_cf x nameplate`` — i.e. **dropping the very ``avail_mult`` the statistic was
divided by**. On a plant with a deep availability derate the two bases differ by
``1 / avail_mult``, so the reconstructed floor lands far above the level actually
measured. The live case is MISO plant 1122 (Ames): ``p25_cf`` 0.674 against a
measured p25-of-online of 33 MW = 0.304 of its 108.7 MW nameplate; 0.674 x its
~49 MW available-capacity base = 33.0 MW exactly — the basis-mismatch signature.
The runtime then runs the plant +65-93 % over its own meter, ~90 % floor-forced.

This script publishes the SAME percentile of the SAME online sample **in MW**, so
no reconstruction is needed and no basis can be dropped (rule 14
``[R-ACCURATE]``: prefer the measured quantity over an estimate of it). The
online mask, the parasitic-factor net, the derate source, the fleet nameplate/
primary-group attribution and the pooled window are the frozen deriver's own,
imported rather than restated:

    online   = net_MW > _ONLINE_FRAC x (nameplate x avail_mult)   # 5 % of available
    p25_mw   = percentile(net_MW[online], 25)

Rule 23 ``[R-FROZEN-DERIVE]``: the frozen deriver is **NOT TOUCHED** and its
pooled artifact is **NOT regenerated** — this is an additive side artifact on the
same pooled window (2023-2025 for MISO), so the ONLY change a consumer sees is
the basis. Nothing here responds to a price or volume residual; the trigger is a
measured level/basis mismatch against the plant's own meter.

``--verify-basis`` reports, per plant, the measured MW level beside the
``p25_cf x nameplate`` the runtime uses today and the implied available-capacity
base, so the mismatch is visible in the artifact's own build log.

Usage:
    python3 scripts/data/derive_thermal_tranche_p25_level_mw.py \
        --iso MISO --years 2023 2024 2025 [--verify-basis] [--out PATH]

Output: ``data/raw/_processed-legacy/thermal_tranches_p25_level_mw_<ISO>.csv``
with columns ``plant_code, plant_group, nameplate_mw, online_hours, p25_level_mw,
p50_level_mw, p25_cf_pct, implied_avail_base_mw``.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

from market_sim.config.paths import PROCESSED_DIR  # noqa: E402
from market_sim.data import campd  # noqa: E402
from market_sim.data.outages import unit_outage_derate_factors  # noqa: E402

# Package import, not a spec_from_file_location file-load (refactor plan §6-E).
from scripts.data import derive_thermal_tranches as dtt  # noqa: E402

# Groups the per-plant must-run floor levels: the merchant gas committed groups
# the runtime's p25-level block can reach. COAL is excluded — its floor level is
# `coal_sync_pmin_mw` / `mustrun_online_pct`, a different mechanism (rule 19).
_LEVEL_GROUPS: frozenset[str] = frozenset({"CC_REGULAR", "CT_PEAKER", "ST_GAS"})


def p25_level_mw(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the measured p25/p50-of-online dispatch level in MW per plant."""
    cap, primary = dtt._fleet_nameplate_and_group(iso)
    factors = dtt._parasitic_factor_map()
    states = campd.states_for_iso(iso)
    if not states:
        raise SystemExit(f"no CAMPD states registered for ISO {iso!r}")

    online_mw: dict[tuple[int, str], list[np.ndarray]] = {}
    for year in years:
        df = campd.load_campd_hourly(states, [year])
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue
        net = campd.plant_hourly_net(df, factors, year)
        derate = unit_outage_derate_factors(year, iso=iso)
        for (code, group), nameplate in cap.items():
            if group not in _LEVEL_GROUPS or nameplate <= 0:
                continue
            if primary.get(code) != group:
                continue
            series = net.get(code)
            if series is None:
                continue
            # THE FROZEN ONLINE MASK, imported: 5 % of AVAILABLE capacity, so a
            # deeply-backed-down but still-synchronized unit counts and a
            # sensor-noise hour does not. Identical to the pooled deriver's.
            avail_mult = derate.get((code, group), np.ones(len(series)))
            avail_cap = nameplate * avail_mult
            finite = np.isfinite(series) & (avail_cap > 0.0)
            online = finite & (series > dtt._ONLINE_FRAC * avail_cap)
            if online.any():
                online_mw.setdefault((code, group), []).append(series[online])

    pooled_path = PROCESSED_DIR / f"thermal_tranches_{iso.upper()}.csv"
    p25_cf: dict[tuple[int, str], float] = {}
    if pooled_path.exists():
        pdf = pd.read_csv(pooled_path)
        if "p25_cf" in pdf.columns:
            for r in pdf.itertuples(index=False):
                try:
                    v = float(getattr(r, "p25_cf"))
                except (TypeError, ValueError):
                    continue
                if v == v:
                    p25_cf[(int(r.plant_code), str(r.plant_group))] = v

    rows: list[dict] = []
    for (code, group), chunks in sorted(online_mw.items()):
        sample = np.concatenate(chunks)
        if sample.size < dtt._MIN_ONLINE_HOURS:
            continue
        nameplate = float(cap[(code, group)])
        p25 = float(np.percentile(sample, 25))
        cf_pct = p25_cf.get((code, group))
        rows.append(
            {
                "plant_code": int(code),
                "plant_group": str(group),
                "nameplate_mw": round(nameplate, 1),
                "online_hours": int(sample.size),
                # Clamp at nameplate for the same physical-admissibility reason
                # _P25_CAP exists: a floor above the plant's registered capacity
                # is impossible, whatever CEMS gross reports.
                "p25_level_mw": round(min(p25, nameplate), 2),
                "p50_level_mw": round(
                    min(float(np.percentile(sample, 50)), nameplate), 2
                ),
                "p25_cf_pct": cf_pct if cf_pct is not None else "",
                # What the runtime's p25_cf x nameplate level implies the
                # measurement's available-capacity base was: p25_mw / p25_cf.
                "implied_avail_base_mw": round(p25 / (cf_pct / 100.0), 1)
                if cf_pct
                else "",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--verify-basis",
        action="store_true",
        help="print the measured MW level beside the p25_cf x nameplate level "
        "the runtime uses today, worst mismatch first",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    print(f"Deriving measured p25 level (MW) for {iso}, years {args.years}")
    df = p25_level_mw(iso, sorted(args.years))
    if df.empty:
        raise SystemExit("no rows derived")

    if args.verify_basis:
        v = df[df.p25_cf_pct != ""].copy()
        v["runtime_level_mw"] = (
            pd.to_numeric(v.p25_cf_pct) / 100.0 * v.nameplate_mw
        ).round(2)
        v["ratio"] = (v.runtime_level_mw / v.p25_level_mw.clip(lower=1e-9)).round(2)
        print("\n  measured MW level vs the runtime's p25_cf x nameplate:")
        print(
            v.sort_values("ratio", ascending=False)[
                [
                    "plant_code",
                    "plant_group",
                    "nameplate_mw",
                    "p25_level_mw",
                    "runtime_level_mw",
                    "ratio",
                    "implied_avail_base_mw",
                ]
            ]
            .head(25)
            .to_string(index=False)
        )

    out = (
        Path(args.out)
        if args.out
        else (PROCESSED_DIR / f"thermal_tranches_p25_level_mw_{iso}.csv")
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    df.sort_values(["plant_code", "plant_group"]).to_csv(out, index=False)
    print(f"\nWrote {out} — {len(df)} rows")


if __name__ == "__main__":
    main()
