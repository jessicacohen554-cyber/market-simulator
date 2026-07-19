"""Derive the MISO per-zone monthly marginal delivery-factor (loss) surface.

The miso-76 M3 derive (frozen, CLAUDE.md rule 23 — re-derives ONLY on source
data updates; charter ``docs/handoffs/miso-nc-price-separation-design-2026-07.md``
§4). Reads the ``lmp-components`` clean partitions (MISO hub LMP/MCC/MLC,
2023-2025 train window) and emits the dimensionless per-zone (month)
marginal delivery-factor deviation surface consumed by the gated
``ScenarioConfig.miso_zonal_loss_surface`` LP mechanism:

    data/raw/iso-specific-transmission/MISO_loss_surface.csv
    columns: iso, zone, year, month, df_deviation, n_hours, interpolated

**The physics.** MISO's ex-post LMP decomposes as ``LMP_i = MEC + MCC_i +
MLC_i`` with ``MLC_i = MEC x (DF_i - 1)``, where ``DF_i`` is the node's
marginal delivery factor vs the system reference (MISO BPM-002, Energy and
Operating Reserve Markets: marginal loss component construction). The derive
target is the deviation ``dev_z,m = DF_z,m - 1``, estimated per zone-month
as the ratio of sums ``sum(MLC_z,t) / sum(MEC_t)`` over the month's hours —
the MEC-weighted estimator, chosen so the surface reproduces the measured
total MLC exactly when re-multiplied by the measured MEC series (the B1
transmission property). MEC_t is recovered per interval as the cross-hub
mean of ``LMP - MCC - MLC`` (identical across hubs up to 2-decimal
publication rounding; the curation's MEC-identity check guards this).

**Basis: day-ahead.** The DA market is an hourly, commitment-aware
full-network optimization — the closest real-world analogue of the model's
LP (charter §1a) — so the surface derives from the DA component record; RT
is reported alongside by the acceptance mode, never derived from.

**Per-year + pooled rows.** Backcast year Y consumes year-Y's own monthly
surface — a same-year measured *physical network property*, the same
admissibility class as same-year plant-specific CEMS emission rates
(CLAUDE.md rule 13 / backcast-overlay inventory). The additional pooled rows
(``year = 0``, all train years) are the forecast-mode forward analogue —
the stable multi-year network property that regenerates from rolling
history, mirroring the forecast emission-rate design — and are NOT used by
the backcast A/B.

**Zones.** Hub -> zone per the D6 crosswalk
(``scripts.data.derive_miso_hub_lmp.HUB_TO_ZONE``): West=MINN, Illinois=
ILLINOIS, Indiana=INDIANA, East=MICHIGAN, South=mean of the four South
hubs' deviations. MISO-Plains has NO trading hub: its surface is the mean
of the West and Illinois deviations — the two hubs bracketing the IA/MO
wheel-through corridor, the SAME documented neighbor proxy the D6 zonal
validation series uses (``build_miso_lmp_reference.py``); flagged
``interpolated=True``.

**Acceptance mode (charter §4, run BEFORE any solve):** ``--acceptance``
recomputes, per benchmarked pair-year (West/Illinois/East vs Indiana), the
separation the LP's dual ratios would imply at the typical flow pattern —
``sum_m h_m x MEC_m x ((1+dev_h,m)/(1+dev_I,m) - 1) / sum_m h_m`` — and
gates it against the B1 band [0.5x, 1.5x] of the measured mean dMLC for
that pair-year. This validates the derive -> loss-fraction -> dual-ratio
-> $ separation algebra chain offline; the LP A/B (charter §5) remains the
real B1 test (flow directions and congestion interactions are
LP-endogenous).

Usage:
    python scripts/data/derive_miso_loss_surface.py            # derive + write
    python scripts/data/derive_miso_loss_surface.py --acceptance
"""

from __future__ import annotations

import argparse
import logging
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import ISO_TRANSMISSION_DIR
from scripts.data.derive_miso_hub_lmp import HUB_TO_ZONE
from scripts.lib import clean_io

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("derive_miso_loss_surface")

OUT = ISO_TRANSMISSION_DIR / "MISO_loss_surface.csv"

# Train window (CLAUDE.md rule 22) — the only years this derive may read.
TRAIN_YEARS: tuple[int, ...] = (2023, 2024, 2025)

# Derive basis (module docstring): the DA ex-post component record.
MARKET_BASIS = "da"

# Pooled-surface sentinel year (forecast-mode rows; module docstring).
POOLED_YEAR = 0

# The hub-less zone and its documented neighbor proxy (module docstring).
PLAINS_ZONE = "MISO-Plains"
PLAINS_PROXY_ZONES: tuple[str, ...] = ("MISO-West", "MISO-Illinois")

# B1 pre-registered band (charter §5): implied/measured per pair-year.
B1_BAND: tuple[float, float] = (0.5, 1.5)

# Benchmarked pairs vs Indiana (charter §5 B1), keyed by hub.
B1_PAIR_HUBS: tuple[str, ...] = ("MINN.HUB", "ILLINOIS.HUB", "MICHIGAN.HUB")
REFERENCE_HUB = "INDIANA.HUB"


def _hub_month_frame(year: int, market: str = MARKET_BASIS) -> pd.DataFrame:
    """Return one year's per-(hub, month, hour) component frame with MEC.

    Reads the clean ``lmp-components`` partition, recovers the per-interval
    MEC as the cross-hub mean of ``LMP - MCC - MLC``, and returns tidy rows
    ``hub, month, mlc, mec`` (one per hub-interval; intervals missing any
    component for a hub are dropped for that hub only).
    """
    df = clean_io.read_clean("lmp-components", iso="MISO", year=year, market=market)
    df = df[df["node"].isin(HUB_TO_ZONE)].copy()
    mec_rows = df["lmp_usd_per_mwh"] - df["mcc_usd_per_mwh"] - df["mlc_usd_per_mwh"]
    mec = (
        pd.DataFrame({"interval_start_utc": df["interval_start_utc"], "mec": mec_rows})
        .groupby("interval_start_utc")["mec"]
        .mean()
    )
    out = pd.DataFrame(
        {
            "hub": df["node"],
            # Month of the EST market day (the report's own clock).
            "month": pd.DatetimeIndex(df["interval_start_est"]).month,
            "mlc": df["mlc_usd_per_mwh"],
            "mec": df["interval_start_utc"].map(mec),
        }
    ).dropna(subset=["mlc", "mec"])
    return out


def _zone_month_dev(frames: list[pd.DataFrame]) -> pd.DataFrame:
    """Aggregate hub frames to the per-zone monthly deviation surface.

    Per (hub, month): ``dev = sum(mlc) / sum(mec)`` (ratio of sums — the
    MEC-weighted estimator, module docstring). Zones then average their
    member hubs' deviations (South = 4-hub mean); Plains is interpolated
    from its documented neighbor proxy. Returns tidy rows
    ``zone, month, df_deviation, n_hours, interpolated``.
    """
    df = pd.concat(frames, ignore_index=True)
    by_hub = df.groupby(["hub", "month"]).agg(
        mlc_sum=("mlc", "sum"), mec_sum=("mec", "sum"), n_hours=("mlc", "size")
    )
    by_hub["dev"] = by_hub["mlc_sum"] / by_hub["mec_sum"]
    by_hub = by_hub.reset_index()
    by_hub["zone"] = by_hub["hub"].map(HUB_TO_ZONE)
    zone = (
        by_hub.groupby(["zone", "month"])
        .agg(df_deviation=("dev", "mean"), n_hours=("n_hours", "sum"))
        .reset_index()
    )
    zone["interpolated"] = False
    proxy = (
        zone[zone["zone"].isin(PLAINS_PROXY_ZONES)]
        .groupby("month")
        .agg(df_deviation=("df_deviation", "mean"), n_hours=("n_hours", "min"))
        .reset_index()
    )
    proxy["zone"] = PLAINS_ZONE
    proxy["interpolated"] = True
    return pd.concat([zone, proxy], ignore_index=True)


def derive(years: tuple[int, ...] = TRAIN_YEARS) -> pd.DataFrame:
    """Build the full surface: one per-year block per train year + pooled rows.

    Returns the deterministic tidy frame written to :data:`OUT` (sorted by
    ``year, zone, month``; ``year = 0`` marks the pooled forecast rows).
    ``years`` exists for fixture tests only — the frozen default is the
    train window.
    """
    frames_by_year = {y: _hub_month_frame(y) for y in years}
    parts: list[pd.DataFrame] = []
    for year, frame in frames_by_year.items():
        z = _zone_month_dev([frame])
        z.insert(0, "year", year)
        parts.append(z)
    pooled = _zone_month_dev(list(frames_by_year.values()))
    pooled.insert(0, "year", POOLED_YEAR)
    parts.append(pooled)
    out = pd.concat(parts, ignore_index=True)
    out.insert(0, "iso", "MISO")
    out = out.sort_values(["year", "zone", "month"], ignore_index=True)
    return out[
        ["iso", "zone", "year", "month", "df_deviation", "n_hours", "interpolated"]
    ]


def write(df: pd.DataFrame) -> Path:
    """Write the surface CSV deterministically (fixed float format)."""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT, index=False, float_format="%.6f")
    log.info("wrote %s (%d rows)", OUT, len(df))
    return OUT


def acceptance(df: pd.DataFrame, years: tuple[int, ...] = TRAIN_YEARS) -> bool:
    """Offline B1 acceptance (charter §4): implied dual-ratio separation vs measured.

    For each benchmarked pair-year, the implied annual-mean separation at the
    typical flow pattern is the month-hours-weighted mean of
    ``MEC_m x ((1+dev_h,m)/(1+dev_ref,m) - 1)``, using the pair-year's own
    monthly surface and measured monthly mean MEC. Gate: within
    :data:`B1_BAND` of the measured mean dMLC for that pair-year (DA basis —
    the derive source; RT is printed alongside as context, never gated).

    Returns True iff every benchmarked pair-year lands in band. ``years``
    exists for fixture tests only — the frozen default is the train window.
    """
    ok = True
    print(
        f"{'pair':<22}{'year':<6}{'measured':>10}{'implied':>10}{'ratio':>8}  band "
        f"[{B1_BAND[0]}x, {B1_BAND[1]}x]  (DA basis)"
    )
    for year in years:
        hubs = _hub_month_frame(year)
        # Measured monthly mean MEC + per-hub monthly mean MLC (plain means —
        # the B1 quantity is the plain annual mean dMLC).
        mec_m = hubs.groupby("month")["mec"].mean()
        hours_m = hubs[hubs["hub"] == REFERENCE_HUB].groupby("month")["mlc"].size()
        mlc_m = hubs.pivot_table(index="month", columns="hub", values="mlc")
        surf = df[(df["year"] == year)].set_index(["zone", "month"])["df_deviation"]
        ref_zone = HUB_TO_ZONE[REFERENCE_HUB]
        for hub in B1_PAIR_HUBS:
            zone = HUB_TO_ZONE[hub]
            dev_h = surf.loc[zone].reindex(mec_m.index)
            dev_r = surf.loc[ref_zone].reindex(mec_m.index)
            implied_m = mec_m * ((1.0 + dev_h) / (1.0 + dev_r) - 1.0)
            implied = float(np.average(implied_m, weights=hours_m))
            measured = float(
                np.average(
                    mlc_m[hub] - mlc_m[REFERENCE_HUB],
                    weights=hours_m.reindex(mlc_m.index),
                )
            )
            ratio = implied / measured if measured != 0.0 else np.inf
            in_band = B1_BAND[0] <= ratio <= B1_BAND[1]
            ok &= in_band
            print(
                f"{zone + ' - ' + ref_zone:<22}{year:<6}{measured:>10.3f}"
                f"{implied:>10.3f}{ratio:>8.2f}  {'PASS' if in_band else 'FAIL'}"
            )
    print(f"\nacceptance: {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> None:
    """CLI: derive + write, or run the offline acceptance gate."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument(
        "--acceptance",
        action="store_true",
        help="run the offline B1 acceptance gate (charter §4) after deriving",
    )
    args = ap.parse_args()
    df = derive()
    write(df)
    if args.acceptance and not acceptance(df):
        raise SystemExit("offline acceptance FAILED — do not solve (charter §4)")


if __name__ == "__main__":
    main()
