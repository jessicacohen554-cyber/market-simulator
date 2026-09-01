"""Derive the per-plant must-run floor LEVEL over the plant's OUT-OF-MERIT hours.

``scripts/data/derive_thermal_tranche_p25_level_mw.py`` publishes the measured
p25 of a plant's net-MW sample over **every hour it was online** — a low
percentile of the plant's OPERATING RANGE. The phenomenon the per-plant
must-run floor exists to represent is narrower: MISO's VLR / self-committed
gas steamers **hold load in the hours merit says shut down**. The statistic
that measures THAT takes the same percentile of the same net-MW sample over
the same pooled window, conditioned on the hours in which the class's economic
signal says OFF.

**The conditioning set is inherited verbatim, not invented here.** It is the
miso-197 W3b construction (``FINDING-miso197-cc-overdispatch-anatomy-2026-09-01.md``
§4): the hours in which the measured CC_REGULAR fleet aggregate ran below
``0.90`` of its own ``99.5``th-percentile demonstrated output that year — i.e.
cheaper combined-cycle capability was demonstrably available and idle, so a
strict-merit stack says the 10-HR steamer should be off. Purely measured: no
model dispatch, no price, no residual enters it.

Everything else is the frozen deriver's own, imported rather than restated
(rule 23 ``[R-FROZEN-DERIVE]``: the frozen deriver is NOT touched and its
artifacts are NOT regenerated — this is an additive side artifact on the same
pooled window, and the only thing a consumer sees change is the SAMPLE):

    online   = net_MW > _ONLINE_FRAC x (nameplate x avail_mult)   # 5 % available
    oom      = online AND cc_fleet < 0.90 x p99.5(cc_fleet)
    level    = percentile(net_MW[oom], _OOM_PCTILE)               # clamped at nameplate

Rule 13 ``[R-MEASURED]``: a pooled multi-year percentile of measured operation
conditioned on a measured system state — the same admissible family as
``p25_cf`` itself, with the identical forward story. It re-derives from each new
CAMPD vintage exactly like the pooled deriver, and it responds to changed
conditions through BOTH the plant's own conduct AND how much combined-cycle
headroom the fleet carries, so a future year with a different CC fleet produces
a different conditioning set and a different level. No outcome pinning: the
output is a commitment LEVEL, not a price or volume target, and dispatch above
the floor stays free.

Rule 21 ``[R-DOF]``: ZERO free parameters. ``_OOM_PCTILE`` is the frozen
family's own p25 (``derive_thermal_tranche_p25_level_mw``'s percentile,
unchanged); the two conditioning constants are miso-197's already-published
W3b lines, inherited verbatim.

The percentile was FIXED by the miso-198 frozen selection criterion
(``scripts/probes/_miso198_level_selection.py``, pushed and blob-verified
before any candidate's number was computed), which admitted a candidate only if
it was conduct-grounded (S-i), non-pinning (S-ii: level <= the plant's own
median over its conditioning set) and no worse than the incumbent on
over-assertion (S-iii: the D-4 conduct direction, ``O / raw_assertion`` <=
1.25 x the incumbent's share every year). Of the four candidates only the p25
over out-of-merit hours was admissible; the p50 variants recover ~4 TWh/yr more
but assert ~2 TWh/yr in hours the plants' own meters say they did not operate
(1.7-2.1 x the incumbent's over-assertion share), which rule 17
``[R-FLOOR-WINDOW]`` makes a bug by definition. Record:
``results/calibration/_miso198_level_selection.json``.

Usage:
    python3 scripts/data/derive_thermal_tranche_oom_level_mw.py \
        --iso MISO --years 2023 2024 2025 [--compare] [--out PATH]

Output: ``data/raw/_processed-legacy/thermal_tranches_oom_level_mw_<ISO>.csv``
with columns ``plant_code, plant_group, nameplate_mw, oom_hours, oom_level_mw``.
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

# Groups the per-plant must-run floor levels — the same set the measured-MW
# deriver publishes. COAL is excluded (its floor level is a different
# mechanism, rule 19).
_LEVEL_GROUPS: frozenset[str] = frozenset({"CC_REGULAR", "CT_PEAKER", "ST_GAS"})

# The frozen percentile family's own p25 — UNCHANGED from
# derive_thermal_tranche_p25_level_mw. Only the sample is re-conditioned.
_OOM_PCTILE: int = 25

# The miso-197 W3b conditioning lines, inherited verbatim (FINDING-miso197 §4).
_CC_HEADROOM_FRAC: float = 0.90
_CC_REF_PCTILE: float = 99.5

# The class whose idle capability defines "the economic signal says off".
_MERIT_REFERENCE_GROUP: str = "CC_REGULAR"


def _cc_headroom_mask(
    net: dict[int, np.ndarray],
    primary: dict[int, str],
    hours: int,
) -> np.ndarray:
    """The W3b out-of-merit hour set for one year.

    Hours in which the measured ``CC_REGULAR`` fleet aggregate ran below
    ``_CC_HEADROOM_FRAC`` of its own ``_CC_REF_PCTILE`` demonstrated output —
    cheaper combined-cycle capability demonstrably idle.
    """
    agg = np.zeros(hours, dtype=float)
    for code, series in net.items():
        if primary.get(int(code)) == _MERIT_REFERENCE_GROUP:
            agg += series
    ref = float(np.percentile(agg, _CC_REF_PCTILE))
    return agg < _CC_HEADROOM_FRAC * ref


def oom_level_mw(iso: str, years: list[int]) -> pd.DataFrame:
    """Return the measured p25-of-out-of-merit-online dispatch level in MW."""
    cap, primary = dtt._fleet_nameplate_and_group(iso)
    factors = dtt._parasitic_factor_map()
    states = campd.states_for_iso(iso)
    if not states:
        raise SystemExit(f"no CAMPD states registered for ISO {iso!r}")

    oom_mw: dict[tuple[int, str], list[np.ndarray]] = {}
    for year in years:
        df = campd.load_campd_hourly(states, [year])
        if df.empty:
            print(f"  (no CAMPD for {iso} {year})")
            continue
        net = campd.plant_hourly_net(df, factors, year)
        hours = len(next(iter(net.values()))) if net else 0
        if not hours:
            continue
        derate = unit_outage_derate_factors(year, iso=iso)
        oom = _cc_headroom_mask(net, primary, hours)
        print(
            f"  {year}: {int(oom.sum())} out-of-merit hour(s) of {hours} "
            f"({_MERIT_REFERENCE_GROUP} below "
            f"{_CC_HEADROOM_FRAC:.2f} x p{_CC_REF_PCTILE})"
        )
        for (code, group), nameplate in cap.items():
            if group not in _LEVEL_GROUPS or nameplate <= 0:
                continue
            if primary.get(code) != group:
                continue
            series = net.get(code)
            if series is None:
                continue
            # THE FROZEN ONLINE MASK, imported: 5 % of AVAILABLE capacity.
            avail_mult = derate.get((code, group), np.ones(len(series)))
            avail_cap = nameplate * avail_mult
            finite = np.isfinite(series) & (avail_cap > 0.0)
            online = finite & (series > dtt._ONLINE_FRAC * avail_cap)
            sel = online & oom
            if sel.any():
                oom_mw.setdefault((code, group), []).append(series[sel])

    rows: list[dict] = []
    for (code, group), chunks in sorted(oom_mw.items()):
        sample = np.concatenate(chunks)
        if sample.size < dtt._MIN_ONLINE_HOURS:
            continue
        nameplate = float(cap[(code, group)])
        level = float(np.percentile(sample, _OOM_PCTILE))
        rows.append(
            {
                "plant_code": int(code),
                "plant_group": str(group),
                "nameplate_mw": round(nameplate, 1),
                "oom_hours": int(sample.size),
                # Clamp at nameplate for the same physical-admissibility reason
                # the frozen deriver's _P25_CAP exists: a floor above the
                # plant's registered capacity is impossible, whatever CEMS
                # gross reports.
                "oom_level_mw": round(min(level, nameplate), 2),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--iso", default="MISO")
    ap.add_argument("--years", nargs="+", type=int, default=[2023, 2024, 2025])
    ap.add_argument("--out", default=None)
    ap.add_argument(
        "--compare",
        action="store_true",
        help="print the out-of-merit level beside the incumbent all-online p25 "
        "level the runtime uses today, largest relative move first",
    )
    args = ap.parse_args()

    iso = args.iso.upper()
    print(f"Deriving out-of-merit level (MW) for {iso}, years {args.years}")
    df = oom_level_mw(iso, sorted(args.years))
    if df.empty:
        raise SystemExit("no rows derived")

    out = Path(args.out) if args.out else (
        PROCESSED_DIR / f"thermal_tranches_oom_level_mw_{iso}.csv"
    )
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    print(f"wrote {out} ({len(df)} rows)")

    if args.compare:
        inc_path = PROCESSED_DIR / f"thermal_tranches_p25_level_mw_{iso}.csv"
        if not inc_path.exists():
            print(f"(no incumbent artifact at {inc_path})")
            return
        inc = pd.read_csv(inc_path)
        m = df.merge(
            inc[["plant_code", "plant_group", "p25_level_mw"]],
            on=["plant_code", "plant_group"],
            how="left",
        )
        m["rel_move"] = (m["oom_level_mw"] - m["p25_level_mw"]) / m["p25_level_mw"]
        print("\nplant  group        npl     incumbent   out-of-merit   move")
        for r in m.sort_values("rel_move").itertuples(index=False):
            inc_v = getattr(r, "p25_level_mw")
            mv = getattr(r, "rel_move")
            print(
                f"{r.plant_code:6d} {r.plant_group:12s} {r.nameplate_mw:7.1f} "
                f"{inc_v if inc_v == inc_v else float('nan'):11.2f} "
                f"{r.oom_level_mw:13.2f} "
                f"{(f'{mv:+.1%}' if mv == mv else 'n/a'):>8s}"
            )


if __name__ == "__main__":
    main()
