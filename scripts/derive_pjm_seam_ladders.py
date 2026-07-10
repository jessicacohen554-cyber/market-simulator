#!/usr/bin/env python3
"""Derive PJM's per-seam measured band-price ladders (Q-Q duration coupling).

Fixes the PJM 2023 interchange duration miss (pjm-95 C1 root-cause lead: the
model imports in ~46% of hours where the measured record imports in ~2%,
hourly diurnal correlation −0.50 — the phantom imports displace CC_REGULAR
dispatch, the shared pjm-90-lineage C1 FAIL). The hurdle-gated
gas × heat-rate × load-shape reference seam clears on the hourly spot
spread, but the measured PJM interchange is direction-STRUCTURAL, not
spread-driven: PJM exports to MISO/NYISO in ~97-100% of ALL hours (2023
import hours: MISO 0.4%, NYISO 0.1%) while importing from the south
(Carolinas 85%, TVA 97%, LGEE 83% of hours) — firm PTP schedules, long-term
contracts and JOA entitlements whose willingness-to-flow is revealed only
statistically, exactly the flow structure a spot-spread seam deletes.

This is the same replacement MISO's G-23 import-starvation fix used
(``scripts/derive_miso_seam_ladders.py``, itself the NEISO audit-C-6
pattern): the seam's *revealed supply curve*, built by Q-Q duration coupling
of two measured series —

1. **Per-seam flows** — PJM's own settlement-grade tie-line interchange
   (``data/raw/iso-specific-transmission/PJM_{year}_import_export_act_sch_
   interchange.csv``, DataMiner ``act_sch_interchange``, ``actual_flow``
   import-positive, hour-beginning EPT), pooled onto the model's five priced
   seams by ``interchange_config.PJM_SEAM_TIE`` (MISO / NYISO / Carolinas /
   TVA / LGEE). This is the repo-canonical PJM boundary meter — the same
   file behind ``eia_loader.pjm_net_interchange`` and the
   ``pjm_seam_flow_limit`` deliverability envelopes — and it reconciles with
   the counterparty meters (PJM→MISO 2023: 35.3 TWh here vs 33.5 TWh in
   MISO's EIA-930 book), where PJM's EIA-930 submission (56.6 TWh) is the
   outlier (BOUNDARY NOTE below).
2. **Internal clearing price** — the measured PJM Day-Ahead system LMP
   (``data/raw/_validation-source/actual_lmp_hourly_PJM.parquet``, ``da``).
   External transactions schedule in the DA market, so DA is the price the
   seam supply curve is revealed against (same convention as MISO/NEISO).

Methodology — per-band Q-Q duration coupling
--------------------------------------------
Identical to the MISO derivation. The reference-price node splits each seam
into ``neighbor_price.SEAM_FLOW_TRANCHES`` (8) equal flow bands per
direction; band ``k`` clears fully whenever the internal price crosses its
offer. The measured counterpart of that offer is the DA price whose
exceedance duration equals the measured duration of the seam flowing deeper
than the band's midpoint depth:

    import band k:  pi_k    = Quantile_DA(1 - P[flow >  L_k])
    export band k:  sigma_k = Quantile_DA(    P[flow < -L_k])
    L_k = (k - 0.5) x interface_limit / 8   (the band's midpoint depth)

Band CAPACITIES are untouched — the 8 x interface_limit/8 grid and the
measured per-border (month x hour-of-day) deliverability envelopes
(``eia_loader.pjm_zonal_interchange_envelope`` via ``pjm_seam_flow_limit``)
keep carrying the measured capability; ONLY the price ladder is measured.

Why this is the right market structure (rule #1): the ladder encodes the
revealed willingness-to-flow as a rising supply curve the LP still clears
ECONOMICALLY hour by hour against its own internal price — nothing is
forced: at price extremes even the base band backs off, and flows respond
to changed model conditions. Under ``pjm_seam_measured_ladder`` it also
DISPLACES the firm scheduled-export floor
(``inject_reference_price_firm_export``) on ladder-covered years —
alternatives, never stacked (rule 19): the firm base the floor pinned is
exactly the deep-duration structure the ladder prices (a near-always-
clearing sigma_1), so stacking would double-count the same phenomenon.

Identification (CLAUDE.md rule 23): measured-behaviour, frozen formula —
the ladders re-derive ONLY when the source data updates (a new tie-line /
settlement year), never because a backcast residual moved. Zero fitted
parameters: every number is a quantile of a measured series at a
structurally fixed depth grid.

Boundary reconciliations (rule 14), documented here and in
``interchange_config.PJM_SEAM_LADDER_BY_YEAR``:

* **Which meter.** PJM's EIA-930 BA-to-BA submission
  (``data/raw/eia-930-interchange/PJM interchange hourly.parquet``)
  disagrees materially with the tie-line file on the MISO seam (2023:
  56.6 vs 35.3 TWh net export; the MISO-side EIA-930 book says 33.5 TWh —
  pseudo-tie / dynamic-schedule attribution differences between the two
  930 submissions). The tie-line file is chosen because (a) it is the
  boundary the model already uses everywhere (``pjm_net_interchange``,
  the zonal interchange attribution, the seam envelopes), and (b) it
  reconciles with the counterparty meters. The 930 parquet is retained as
  the cross-check this script prints.
* **Tie pooling.** Each tie maps to the neighbor BA it physically
  interconnects (``PJM_SEAM_TIE``): the NJ–NY merchant HVDC ties (NEPT /
  HUDS / LIND) pool into the NYISO seam; Duke Progress East/West pool with
  Duke Carolinas into the Carolinas seam; all MISO-member ties (incl. the
  MECS Michigan interface and the OVEC/LAGN dynamic schedules) pool into
  the MISO seam. The script hard-fails on an unmapped tie rather than
  silently misattributing it.
* Same-seam no-wash: each seam's export ladder must sit strictly below its
  import ladder at every band (a seam cannot deeply import and export at
  once); asserted per year, with a clamp note if it ever binds. CROSS-seam
  simultaneous counterflow (import TVA while exporting MISO) is real
  wheel-through the multi-link external node carries, bounded by the
  measured per-border envelopes.

Usage:
    python scripts/derive_pjm_seam_ladders.py            # all years + pooled
    python scripts/derive_pjm_seam_ladders.py --years 2025

Output is hand-rounded (prices to cents) into
``interchange_config.PJM_SEAM_LADDER_BY_YEAR``, with this script cited as
the derivation.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "src"))

RAW = REPO / "data" / "raw"
TIE_DIR = RAW / "iso-specific-transmission"
ACTUAL_LMP_PARQUET = RAW / "_validation-source" / "actual_lmp_hourly_PJM.parquet"
EIA930_PARQUET = RAW / "eia-930-interchange" / "PJM interchange hourly.parquet"

YEARS = (2023, 2024, 2025)

# No-wash ordering margin ($/MWh): a seam's export sinks sit at least this far
# below its cheapest import band (same-seam reconciliation, module docstring).
NO_WASH_EPS = 0.01

# Fixed non-leap calendar helpers (identical to derive_miso_seam_ladders).
_DAYS = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
_MONTH_START_HOUR = (np.cumsum([0, *_DAYS[:-1]]) * 24).tolist()
_HOURS_PER_YEAR = 8760

# EIA-930 DIBA → model seam, for the cross-check print only (the ladder is
# derived from the tie-line file; module docstring BOUNDARY NOTE).
_EIA930_DIBA_SEAM = {
    "MISO": "MISO",
    "NYIS": "NYISO",
    "DUK": "Carolinas",
    "CPLE": "Carolinas",
    "CPLW": "Carolinas",
    "TVA": "TVA",
    "LGEE": "LGEE",
}


def load_joined(years: tuple[int, ...]) -> pd.DataFrame:
    """Return the dense (year, hour) frame joining seam flows and the DA LMP.

    Columns: one import-positive MW series per seam in
    :data:`~market_sim.config.interchange_config.PJM_SEAM_TIE` (``MISO`` /
    ``NYISO`` / ``Carolinas`` / ``TVA`` / ``LGEE``), plus ``da``/``rt``
    ($/MWh PJM system). Hour-beginning EPT -> fixed non-leap hour-of-year
    (Feb 29 dropped), the LP's clock. Isolated gaps (DST) interpolated
    (limit=3). Hard-fails on a tie line missing from ``PJM_SEAM_TIE``.
    """
    from market_sim.config.interchange_config import PJM_SEAM_TIE

    tie_to_seam = {t: s for s, ties in PJM_SEAM_TIE.items() for t in ties}
    frames = []
    for year in years:
        path = TIE_DIR / f"PJM_{year}_import_export_act_sch_interchange.csv"
        df = pd.read_csv(
            path, usecols=["datetime_beginning_ept", "tie_line", "actual_flow"]
        )
        ts = pd.to_datetime(
            df["datetime_beginning_ept"], format="mixed", errors="coerce"
        )
        keep = ts.notna() & ~((ts.dt.month == 2) & (ts.dt.day == 29))
        df, ts = df[keep], ts[keep]
        unmapped = sorted(set(df["tie_line"].astype(str)) - set(tie_to_seam))
        if unmapped:
            sys.exit(
                f"{path.name}: tie lines {unmapped} missing from "
                "interchange_config.PJM_SEAM_TIE — map them to a seam "
                "(no silent misattribution)."
            )
        hoy = (
            np.array(_MONTH_START_HOUR)[ts.dt.month.to_numpy() - 1]
            + (ts.dt.day.to_numpy() - 1) * 24
            + ts.dt.hour.to_numpy()
        )
        frames.append(
            pd.DataFrame(
                {
                    "year": year,
                    "hour": hoy,
                    "seam": df["tie_line"].map(tie_to_seam).to_numpy(),
                    # actual_flow is already import-positive into PJM.
                    "mw": pd.to_numeric(df["actual_flow"], errors="coerce"),
                }
            )
        )
    work = pd.concat(frames, ignore_index=True)
    work = work[(work["hour"] >= 0) & (work["hour"] < _HOURS_PER_YEAR)]
    flows = work.pivot_table(
        index=["year", "hour"],
        columns="seam",
        values="mw",
        aggfunc="sum",
        observed=True,
    )
    lmp = pd.read_parquet(ACTUAL_LMP_PARQUET).set_index(["year", "hour"])
    full = pd.MultiIndex.from_product(
        [list(years), range(_HOURS_PER_YEAR)], names=["year", "hour"]
    )
    df = flows.reindex(full).join(lmp)
    return df.interpolate(limit=3)


def qq_import(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Import-band price: DA quantile matching the depth's exceedance duration."""
    exceed = float((flow > level).mean())
    return float(np.quantile(price, 1.0 - exceed))


def qq_export(price: np.ndarray, flow: np.ndarray, level: float) -> float:
    """Export-band price: DA quantile matching the export-depth duration."""
    depth = float((flow < -level).mean())
    return float(np.quantile(price, depth))


def derive(g: pd.DataFrame) -> tuple[dict, list[str]]:
    """Derive ``{seam: {"import": [...], "export": [...]}}`` from sample ``g``.

    ``g`` is one year of :func:`load_joined` (or the pooled multi-year frame
    for the static forward ladder). Prices are per band 1..SEAM_FLOW_TRANCHES
    at the midpoint-depth grid of each seam's interface limit. ``notes``
    carries no-wash clamp diagnostics.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    g = g.dropna(subset=["da"] + [n.name for n in INTERFACE_NEIGHBORS["PJM"]])
    da = g["da"].to_numpy(dtype=float)
    out: dict[str, dict[str, list[float]]] = {}
    notes: list[str] = []
    for spec in INTERFACE_NEIGHBORS["PJM"]:
        flow = g[spec.name].to_numpy(dtype=float)
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        mids = (np.arange(SEAM_FLOW_TRANCHES) + 0.5) * step
        imp = [qq_import(da, flow, m) for m in mids]
        exp = [qq_export(da, flow, m) for m in mids]
        # Same-seam no-wash: every export band strictly below the cheapest
        # import band (rule 14 single-seam reconciliation).
        lim = min(imp) - NO_WASH_EPS
        for k, s in enumerate(exp):
            if s > lim:
                notes.append(
                    f"{spec.name} export band {k + 1}: sink ${s:.2f} clamped "
                    f"to ${lim:.2f} (same-seam no-wash vs cheapest import band)"
                )
                exp[k] = lim
        out[spec.name] = {
            "import": [round(p, 2) for p in imp],
            "export": [round(p, 2) for p in exp],
        }
    return out, notes


def offline_score(g: pd.DataFrame, ladders: dict) -> dict[str, dict[str, float]]:
    """Score each seam's ladder against its measured flow, driven by actual DA.

    The offline analogue of the MISO derivation's P9 diagnostic: simulate the
    band clearing ``sum(step x 1[DA > pi_k]) - sum(step x 1[DA < sigma_k])``
    on the measured DA price and compare to the measured seam net flow
    (volume, duration RMSE, import-hour share, hourly correlation). The live
    LP additionally applies the measured per-border deliverability envelopes
    and its own internal price, so this is the derivation sanity check, not
    the calibration score.
    """
    from market_sim.config.interchange_config import INTERFACE_NEIGHBORS
    from market_sim.data.neighbor_price import SEAM_FLOW_TRANCHES

    g = g.dropna(subset=["da"] + list(ladders))
    da = g["da"].to_numpy(dtype=float)
    scores: dict[str, dict[str, float]] = {}
    for spec in INTERFACE_NEIGHBORS["PJM"]:
        lad = ladders[spec.name]
        step = spec.interface_limit_mw / SEAM_FLOW_TRANCHES
        act = g[spec.name].to_numpy(dtype=float)
        sim = sum(step * (da > p) for p in lad["import"]) - sum(
            step * (da < p) for p in lad["export"]
        )
        scores[spec.name] = {
            "sim_twh": sim.sum() / 1e6,
            "act_twh": act.sum() / 1e6,
            "dur_rmse": float(np.sqrt(np.mean((np.sort(sim) - np.sort(act)) ** 2))),
            "imp_hrs_sim": 100.0 * float((sim > 0).mean()),
            "imp_hrs_act": 100.0 * float((act > 0).mean()),
            "hourly_corr": float(np.corrcoef(sim, act)[0, 1]),
        }
    return scores


def eia930_crosscheck(years: tuple[int, ...]) -> None:
    """Print the per-seam annual TWh from BOTH meters (rule 14 boundary note)."""
    if not EIA930_PARQUET.exists():
        print("  (EIA-930 PJM parquet absent — cross-check skipped)")
        return
    ix = pd.read_parquet(EIA930_PARQUET)
    t = pd.to_datetime(ix["local_time"]) - pd.Timedelta(hours=1)
    ix = ix.assign(year=t.dt.year.to_numpy())
    ix = ix.assign(seam=ix["diba"].astype(str).map(_EIA930_DIBA_SEAM))
    # EIA sign: + = PJM exports to the DIBA → import-positive is −mw.
    per = (
        -ix.dropna(subset=["seam"])
        .groupby(["year", "seam"], observed=True)["mw"]
        .sum()
        .div(1e6)
        .unstack()
    )
    print("\n=== EIA-930 cross-check (import-positive TWh; ladder uses the")
    print("    tie-line meter — see module docstring BOUNDARY NOTE) ===")
    print(per.loc[list(years)].round(1).to_string())


def _print_ladder(label: str, g: pd.DataFrame) -> None:
    """Derive, score and print one sample's ladders + anchor diagnostics."""
    ladders, notes = derive(g)
    gg = g.dropna(subset=["da"])
    da_mean = float(gg["da"].mean())
    print(f"\n=== {label} ===")
    print(f"  anchor: PJM system DA mean ${da_mean:.2f}")
    for seam, lad in ladders.items():
        print(f'    "{seam}": {{')
        print(f'        "import": {tuple(lad["import"])},')
        print(f'        "export": {tuple(lad["export"])},')
        print("    },")
    for n in notes:
        print(f"  note: {n}")
    for seam, s in offline_score(g, ladders).items():
        print(
            f"  offline P9 {seam}: {s['sim_twh']:+.2f} TWh vs {s['act_twh']:+.2f} "
            f"actual; duration RMSE {s['dur_rmse']:.0f} MW; import hours "
            f"{s['imp_hrs_sim']:.0f}% vs {s['imp_hrs_act']:.0f}%; "
            f"hourly corr {s['hourly_corr']:+.2f}"
        )


def main() -> None:
    """CLI entry point: derive per-year ladders and the pooled forward ladder."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--years", nargs="+", type=int, default=list(YEARS))
    args = ap.parse_args()

    years = tuple(sorted(args.years))
    df = load_joined(years)
    for year in years:
        _print_ladder(str(year), df.loc[year])
    if len(years) > 1:
        pooled = df.loc[years[0] : years[-1]]
        _print_ladder(f"pooled {years[0]}-{years[-1]} (static forward ladder)", pooled)
    eia930_crosscheck(years)


if __name__ == "__main__":
    main()
