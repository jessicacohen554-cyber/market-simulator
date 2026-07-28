"""Derive the PJM per-zone monthly marginal delivery-factor (loss) surface.

The pjm-136 M2 derive (frozen, CLAUDE.md rule 23 `[R-FROZEN-DERIVE]` — re-derives
ONLY when its source data updates; charter
`results/calibration/FINDING-pjm136-zonal-dual-structure-2026-07-28.md`). Reads
the pjm-136 zonal LMP-component intake (`data/raw/pjm-zonal-lmp/`, PJM DataMiner2
`da_hrl_lmps` `type = ZONE` rows, 2023-2025) and emits the dimensionless per-zone
(month) marginal delivery-factor deviation surface consumed by the gated
`ScenarioConfig.pjm_zonal_loss_surface` LP mechanism:

    data/raw/iso-specific-transmission/PJM_loss_surface.csv
    columns: iso, zone, year, month, df_deviation, n_hours, interpolated

**The physics.** PJM's ex-post LMP decomposes as `LMP_i = MEC + MCC_i + MLC_i`
(PJM Manual 11 §2 / OATT Attachment K), with the marginal loss component `MLC_i`
the value of losses incurred delivering a marginal MW to node `i` relative to the
system reference. The derive target is the dimensionless deviation
`dev_z,m = MLC_z,m / MEC_m`, estimated per zone-month as the ratio of sums
`sum(MLC_z,t) / sum(MEC_t)` over the month's hours — the MEC-weighted estimator
(identical to `derive_miso_loss_surface.py`), chosen so the surface reproduces
the measured total MLC exactly when re-multiplied by the measured MEC series.
Nothing here reads a model output, a residual, or a scoring target: this is a
measured physical network property that regenerates for any year from the same
published feed and responds to changed grid conditions (rule 13 `[R-MEASURED]`).

**Basis: day-ahead.** The DA market is an hourly, commitment-aware full-network
optimization — the closest real-world analogue of the model's LP — so the surface
derives from the DA component record; RT is reported by `--acceptance`, never
derived from.

**Zones — every model zone is real, none interpolated.** PJM publishes a
`type = ZONE` pnode per transmission zone, and the canonical
`eia930.zonal_shares._PJM_LOAD_ZONE_GROUPS` crosswalk maps all 21 of them onto
the eight model zones. A model zone that rolls up several transmission zones is
aggregated by that hour's metered load in each
(`data/raw/zone-specific-demand/PJM<year>_hrl_load_metered.csv`) — the definition
of a zonal price, and the same weighting the model's own zonal demand uses. This
is why the intake fetched zone pnodes rather than reusing the committed 12-hub
file: three model zones (`PJM_West_APS`, `PJM_Central_PA`, `PJM_SWMAAC`) have no
hub at all, and two of those are Dominion's other import paths (rule 14
`[R-ACCURATE]`). No zone carries `interpolated=True`.

**Per-year + pooled rows.** Backcast year Y consumes year-Y's own monthly
surface — a same-year measured *physical network property*, the same
admissibility class as same-year plant-specific CEMS emission rates. The
additional pooled rows (`year = 0`, all train years) are the forecast-mode
forward analogue — the stable multi-year network property that regenerates from
rolling history — and are NOT used by the backcast A/B.

**Acceptance mode (run BEFORE any solve).** `--acceptance` recomputes, per
benchmarked zone pair-year, the separation the LP's dual ratios would imply at
the typical flow pattern —
`sum_m h_m x MEC_m x ((1+dev_y,m)/(1+dev_x,m) - 1) / sum_m h_m` — and gates it
against the [0.5x, 1.5x] band of the measured mean dMLC for that pair-year (the
miso-76 B1 band, applied to PJM's own measured quantities). This validates the
derive -> loss-fraction -> dual-ratio -> $ separation algebra offline; the LP A/B
remains the real test, since flow directions and congestion interactions are
LP-endogenous.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/data/derive_pjm_loss_surface.py
    PYTHONPATH=. .venv/bin/python scripts/data/derive_pjm_loss_surface.py --acceptance
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import pandas as pd

from market_sim.config.paths import ISO_TRANSMISSION_DIR, RAW_DATA_DIR
from market_sim.data.eia930.zonal_shares import _PJM_LOAD_ZONE_GROUPS

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_pjm_loss_surface")

OUT = ISO_TRANSMISSION_DIR / "PJM_loss_surface.csv"
ZONAL_LMP_DIR = RAW_DATA_DIR / "pjm-zonal-lmp"

#: Train-window years the surface carries per-year rows for.
YEARS: tuple[int, ...] = (2023, 2024, 2025)

#: Sentinel year for the pooled (forecast-analogue) rows.
POOLED_YEAR = 0

#: PJM LMP `type = ZONE` pnode name -> the metered-load zone code the canonical
#: `_PJM_LOAD_ZONE_GROUPS` crosswalk is keyed on. Naming aliases only (the LMP
#: feed spells zones out where the metered-load feed abbreviates); no judgement
#: about zone membership is made here — that lives in the canonical crosswalk.
LMP_PNODE_TO_LOAD_ZONE: dict[str, str] = {
    "AECO": "AE",
    "AEP": "AEP",
    "APS": "AP",
    "ATSI": "ATSI",
    "BGE": "BC",
    "COMED": "CE",
    "DAY": "DAY",
    "DEOK": "DEOK",
    "DOM": "DOM",
    "DPL": "DPL",
    "DUQ": "DUQ",
    "EKPC": "EKPC",
    "JCPL": "JC",
    "METED": "ME",
    "OVEC": "OVEC",
    "PECO": "PE",
    "PENELEC": "PN",
    "PEPCO": "PEP",
    "PPL": "PL",
    "PSEG": "PS",
    "RECO": "RECO",
}

#: Rollup pnodes in the same feed that are not transmission zones.
NON_ZONE_PNODES = ("PJM-RTO", "MID-ATL/APS")

#: Acceptance-mode benchmark pairs: (near, far) model zones whose measured
#: delta-MLC the implied dual separation is gated against. Chosen as the
#: Dominion-facing boundaries the pjm-136 charter targets plus the west-east
#: gradient's two ends, so the gate covers both the small and the large
#: measured separations rather than only the favourable one.
ACCEPTANCE_PAIRS: tuple[tuple[str, str], ...] = (
    ("PJM_Dominion", "PJM_AEP_Ohio"),
    ("PJM_Dominion", "PJM_West_APS"),
    ("PJM_Dominion", "PJM_SWMAAC"),
    ("PJM_EMAAC", "PJM_ComEd"),
)

#: The miso-76 B1 acceptance band, applied to PJM's own measured quantities.
ACCEPT_BAND = (0.5, 1.5)

#: MEC is published per row and is identical across nodes per interval up to the
#: feed's 6-decimal rounding; above this the identity is broken and the derive
#: must fail rather than average an inconsistent reference.
MEC_IDENTITY_TOL = 1e-4


def _load_components(year: int, run: str = "da") -> pd.DataFrame:
    """Load one year of zonal LMP components, mapped onto model zones.

    Returns a long frame with columns ``utc``, ``month``, ``model_zone``,
    ``load_zone``, ``mlc``, ``mec``, ``mcc``, ``lmp``, ``mw`` (metered load).

    The interval key is ``datetime_beginning_utc``, NOT the EPT stamp: on the
    DST fall-back day both 01:00 EDT and 01:00 EST carry the same EPT label, so
    keying on EPT silently merges two different market intervals (it reads as a
    $3.84/MWh break in the MEC identity, which is how it was found).
    """
    feed = f"{run}_hrl_lmps"
    files = sorted(ZONAL_LMP_DIR.glob(f"{feed}_{year}_*.parquet"))
    if not files:
        raise SystemExit(
            f"no {feed} parquet for {year} in {ZONAL_LMP_DIR} — run "
            "scripts/data/fetch_pjm_zonal_lmp_components.py first"
        )
    raw = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    raw = raw[~raw["pnode_name"].isin(NON_ZONE_PNODES)].copy()
    raw["utc"] = pd.to_datetime(raw["datetime_beginning_utc"], format="mixed")
    ept = pd.to_datetime(raw["datetime_beginning_ept"], format="mixed")
    raw = raw[ept.dt.year == year].copy()
    raw["month"] = ept[ept.dt.year == year].dt.month

    raw["load_zone"] = raw["pnode_name"].map(LMP_PNODE_TO_LOAD_ZONE)
    missing = sorted(set(raw.loc[raw["load_zone"].isna(), "pnode_name"]))
    if missing:
        raise SystemExit(f"unmapped PJM LMP zone pnodes: {missing}")
    raw["model_zone"] = raw["load_zone"].map(_PJM_LOAD_ZONE_GROUPS)
    unmapped = sorted(set(raw.loc[raw["model_zone"].isna(), "load_zone"]))
    if unmapped:
        raise SystemExit(f"load zones absent from _PJM_LOAD_ZONE_GROUPS: {unmapped}")

    raw = raw.rename(
        columns={
            f"marginal_loss_price_{run}": "mlc",
            f"system_energy_price_{run}": "mec",
            f"congestion_price_{run}": "mcc",
            f"total_lmp_{run}": "lmp",
        }
    )
    # MEC identity guard: one system reference per interval (fail loud, never
    # average an inconsistent reference).
    spread = raw.groupby("utc")["mec"].agg(lambda s: s.max() - s.min())
    worst = float(spread.max())
    if worst > MEC_IDENTITY_TOL:
        raise SystemExit(
            f"{year} {run}: MEC differs across zones by up to {worst:.6f} $/MWh "
            f"(> {MEC_IDENTITY_TOL}) — the feed's system reference is not uniform"
        )

    raw = raw.merge(_metered_load(year), on=["utc", "load_zone"], how="left")
    n_missing = int(raw["mw"].isna().sum())
    if n_missing:
        # A transmission zone with no metered row that hour keeps its model
        # zone's average rather than dropping out of it.
        log.warning(
            "%d %s: %d zone-hours have no metered load row; equal-weighted there",
            year,
            run,
            n_missing,
        )
        raw["mw"] = raw["mw"].fillna(raw.groupby("load_zone")["mw"].transform("median"))
        raw["mw"] = raw["mw"].fillna(1.0)
    return raw


def _metered_load(year: int) -> pd.DataFrame:
    """Metered PJM zonal load (MW) per (UTC interval, transmission zone)."""
    path = RAW_DATA_DIR / "zone-specific-demand" / f"PJM{year}_hrl_load_metered.csv"
    frame = pd.read_csv(
        path, usecols=["datetime_beginning_utc", "datetime_beginning_ept", "zone", "mw"]
    )
    frame["utc"] = pd.to_datetime(frame["datetime_beginning_utc"], format="mixed")
    ept = pd.to_datetime(frame["datetime_beginning_ept"], format="mixed")
    frame = frame[ept.dt.year == year]
    frame = frame.rename(columns={"zone": "load_zone"})
    frame["mw"] = pd.to_numeric(frame["mw"], errors="coerce")
    return frame.groupby(["utc", "load_zone"], as_index=False)["mw"].mean()


def _zone_hourly_mlc(frame: pd.DataFrame) -> pd.DataFrame:
    """Load-weighted hourly MLC per (UTC interval, model zone), with month."""
    frame = frame.copy()
    frame["_w"] = frame["mlc"] * frame["mw"]
    num = frame.groupby(["utc", "month", "model_zone"], as_index=False)["_w"].sum()
    den = frame.groupby(["utc", "month", "model_zone"], as_index=False)["mw"].sum()
    out = num.merge(den, on=["utc", "month", "model_zone"])
    out["mlc"] = out["_w"] / out["mw"]
    return out.drop(columns=["_w", "mw"])


def _deviation_rows(frames: dict[int, pd.DataFrame], year_label: int) -> list[dict]:
    """`dev = sum(MLC_z) / sum(MEC)` per (model zone, month) over ``frames``."""
    mlc_parts, mec_parts = [], []
    for frame in frames.values():
        mlc_parts.append(_zone_hourly_mlc(frame))
        mec_parts.append(frame.groupby(["utc", "month"], as_index=False)["mec"].mean())
    mlc = pd.concat(mlc_parts, ignore_index=True)
    mec = pd.concat(mec_parts, ignore_index=True)

    mec_sum = mec.groupby("month")["mec"].sum()
    rows: list[dict] = []
    for (zone, month), block in mlc.groupby(["model_zone", "month"]):
        denom = float(mec_sum.loc[month])
        rows.append(
            {
                "iso": "PJM",
                "zone": zone,
                "year": year_label,
                "month": int(month),
                "df_deviation": round(float(block["mlc"].sum()) / denom, 8),
                "n_hours": int(block["utc"].nunique()),
                "interpolated": False,
            }
        )
    return rows


def _acceptance(frames: dict[int, pd.DataFrame], surface: pd.DataFrame) -> int:
    """Offline B1-analogue gate: implied $ separation vs measured mean dMLC."""
    print("=" * 82)
    print("pjm-136 derive acceptance — implied dual separation vs measured ΔMLC")
    print(f"band [{ACCEPT_BAND[0]}x, {ACCEPT_BAND[1]}x]")
    print("=" * 82)
    n_pass = n_total = 0
    for year, frame in frames.items():
        hourly = _zone_hourly_mlc(frame)
        wide = hourly.pivot(index="utc", columns="model_zone", values="mlc")
        mec = frame.groupby(["utc", "month"])["mec"].mean().reset_index()
        mec_m = mec.groupby("month")["mec"].mean()
        hours_m = mec.groupby("month")["mec"].size()
        sub = surface[surface["year"] == year]
        dev = sub.pivot(index="month", columns="zone", values="df_deviation")

        for near, far in ACCEPTANCE_PAIRS:
            measured = float((wide[near] - wide[far]).mean())
            ratio_m = (1.0 + dev[near]) / (1.0 + dev[far]) - 1.0
            implied = float((hours_m * mec_m * ratio_m).sum() / hours_m.sum())
            rel = implied / measured if abs(measured) > 1e-9 else float("nan")
            ok = ACCEPT_BAND[0] <= rel <= ACCEPT_BAND[1]
            n_total += 1
            n_pass += int(ok)
            print(
                f"  {year} {near.replace('PJM_', ''):>10s} vs "
                f"{far.replace('PJM_', ''):<10s} measured ΔMLC {measured:+7.3f}  "
                f"implied {implied:+7.3f}  ratio {rel:5.2f}x  "
                f"{'PASS' if ok else 'FAIL'}"
            )
    print(f"\nacceptance: {n_pass}/{n_total} pair-years in band")
    return 0 if n_pass == n_total else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--acceptance", action="store_true")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args(argv)

    frames = {year: _load_components(year, "da") for year in YEARS}

    rows: list[dict] = []
    for year in YEARS:
        rows.extend(_deviation_rows({year: frames[year]}, year))
    rows.extend(_deviation_rows(frames, POOLED_YEAR))
    surface = pd.DataFrame(rows).sort_values(["year", "zone", "month"])

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    surface.to_csv(out_path, index=False)
    log.info(
        "wrote %s (%d rows: %d zones x %d months x %d year labels)",
        out_path,
        len(surface),
        surface["zone"].nunique(),
        surface["month"].nunique(),
        surface["year"].nunique(),
    )

    annual = (
        surface[surface["year"] != POOLED_YEAR]
        .groupby(["year", "zone"])["df_deviation"]
        .mean()
        .unstack(0)
    )
    print("\nmean monthly df_deviation by zone-year (dimensionless):")
    print(annual.round(5).to_string())

    if args.acceptance:
        return _acceptance(frames, surface)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
