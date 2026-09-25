"""R-SOCO-B (ZERO LP): verify the seven per-year legs and compose them into one span bundle.

PRECOMMIT: ``docs/handoffs/r-soco/PRECOMMIT-r-soco-b-2026-09-25.md`` §6. Each leg is
the promoted SOCO keeper's recipe replayed on the repaired SOCO boundary, one shard per
year (rule 36). Three layers of checks run BEFORE anything is written:

1. :func:`scripts.probes.rsoco_compose_span.assert_lane` — the R-SOCO posture (F1/F2
   flags, the std outage extract, empty offer-curve overrides), reused not forked;
2. :func:`assert_repairs` — this lane's own posture, read from each leg's artifacts:
   the pinned git SHA; both new registry rows in ``solve_surface.moved``; the former
   Gulf Power plants absent from the solved fleet in every year; PowerSouth (``AEC``)
   units present in 2021 with zero dispatch before September; the 2019 served
   demand-with-interchange equal to the phase-0 census value (R1 live);
3. :func:`scripts.probes.soco55_compose_span.compose` — posture drift, band identity,
   dispatch present, MER live, identical solve-surface fingerprint and dependency set.

Usage::

    python3 scripts/probes/rsocob_compose_span.py --check-only --pinned-sha <sha> \\
        --legs results/calibration/rsocob_{2019,2020,2021,2022,2023,2024,2025}
    python3 scripts/probes/rsocob_compose_span.py --pinned-sha <sha> \\
        --legs results/calibration/rsocob_{2019,2020,2021,2022,2023,2024,2025} \\
        --out  results/calibration/rsocob_boundary_span
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.rsoco_compose_span import assert_lane  # noqa: E402
from scripts.probes.soco55_compose_span import ROOT, compose as _compose  # noqa: E402

#: The registry rows this lane adds (R-SOCO-B2 added ``ISO_BA_EXITS``); declared at
#: their inert SOCO values, so a leg solved on the repaired code carries them in
#: ``solve_surface.moved``.
NEW_SURFACE_ROWS = (
    "EIA930_INTERCHANGE_SIGN_INVERTED_WINDOWS_UTC",
    "ISO_BA_JOINS",
    "ISO_BA_EXITS",
)
#: R-SOCO-B2: the Gulf plants are SOCO members through 2022 and leave at LP row 4637
#: of 2022 (hour-ending UTC 2022-07-13 12:00; constants.ISO_BA_EXITS).
GULF_LAST_MEMBER_YEAR = 2022
GULF_EXIT_ROW_2022 = 4637
#: Gulf thermal plants carried by every vintage 2019-2022 (Crist, Lansing Smith).
GULF_CORE = {641, 643}
#: Former Gulf Power plants (current EIA-860 codes them FPL).
GULF = {641, 643, 7715, 50310, 55242, 57502, 63754, 64757, 65036}
#: PowerSouth thermal plants carried by vintage_2021 (McWilliams, McIntosh).
AEC_THERMAL = {533, 7063}
#: 2019 served demand-with-interchange, TWh (PRECOMMIT §3, the phase-0 census post side).
DEMAND_2019_TWH = 245.097
#: First hour of September on the model's non-leap clock (Jan..Aug = 243 days).
SEP_FIRST_HOUR = 243 * 24
_CODE = re.compile(r"(?:^|_p)(\d+)(?=_|$)")


def _plant_code(unit_id: str) -> int | None:
    """Parse the EIA plant code out of an LP unit id (``..._p533_econlo``, ``53_hydro``)."""
    m = _CODE.search(str(unit_id))
    return int(m.group(1)) if m else None


def _leg_year(leg: Path) -> int:
    years = json.loads((leg / "meta.json").read_text()).get("years") or []
    if len(years) != 1:
        raise SystemExit(f"{leg.name}: expected exactly one year, got {years}")
    return int(years[0])


def assert_repairs(legs: list[Path], pinned_sha: str) -> dict:
    """Fail loud unless every leg solved this lane's repaired boundary; return evidence."""
    evidence: dict = {}
    for leg in legs:
        year = _leg_year(leg)
        cfg = json.loads((leg / "run_config.json").read_text())
        git = cfg.get("git") or {}
        if git.get("basis_sha") != pinned_sha or git.get("dirty"):
            raise SystemExit(
                f"{leg.name}: git {git} is not the clean pinned {pinned_sha}"
            )
        moved = (cfg.get("solve_surface") or {}).get("moved") or {}
        missing = [n for n in NEW_SURFACE_ROWS if n not in moved]
        if missing:
            raise SystemExit(f"{leg.name}: solve_surface.moved lacks {missing}")
        fleet = pd.read_parquet(leg / "dispatch" / f"{year}_P1_fleet.parquet")
        codes = {c for c in (_plant_code(u) for u in fleet["unit_id"]) if c is not None}
        gulf = sorted(codes & GULF)
        ev = {"units": int(len(fleet)), "gulf_plants": gulf}
        if year > GULF_LAST_MEMBER_YEAR and gulf:
            raise SystemExit(
                f"{leg.name}: Gulf plants still in the solved fleet: {gulf}"
            )
        if year <= GULF_LAST_MEMBER_YEAR and not GULF_CORE <= set(gulf):
            raise SystemExit(
                f"{leg.name}: Gulf plants missing before the exit: {gulf}"
            )
        if year == GULF_LAST_MEMBER_YEAR:
            disp = pd.read_parquet(leg / "dispatch" / f"{year}_P1.parquet")
            ucol = "unit_id" if "unit_id" in disp.columns else disp.columns[0]
            mwcol = next(c for c in ("mw", "MW", "dispatch_mw") if c in disp.columns)
            hcol = next(c for c in ("hour", "t") if c in disp.columns)
            sub = disp[disp[ucol].map(_plant_code).isin(GULF)]
            pre = float(sub.loc[sub[hcol] < GULF_EXIT_ROW_2022, mwcol].sum())
            post = float(sub.loc[sub[hcol] >= GULF_EXIT_ROW_2022, mwcol].abs().sum())
            if post > 1e-6 or pre <= 0.0:
                raise SystemExit(
                    f"{leg.name}: Gulf dispatch before the exit {pre:.1f} MWh (want "
                    f"> 0), after {post:.3f} MWh (want 0)"
                )
            ev.update(gulf_pre_exit_gwh=round(pre / 1e3, 1), gulf_post_exit_mwh=post)
        aec = codes & AEC_THERMAL
        if year < 2021 and aec:
            raise SystemExit(
                f"{leg.name}: PowerSouth plants {sorted(aec)} before the join"
            )
        if year == 2021:
            if aec != AEC_THERMAL:
                raise SystemExit(
                    f"{leg.name}: PowerSouth thermal plants missing: {aec}"
                )
            disp = pd.read_parquet(leg / "dispatch" / f"{year}_P1.parquet")
            ucol = "unit_id" if "unit_id" in disp.columns else disp.columns[0]
            mwcol = next(c for c in ("mw", "MW", "dispatch_mw") if c in disp.columns)
            hcol = next(c for c in ("hour", "t") if c in disp.columns)
            sel = disp[ucol].map(_plant_code).isin(AEC_THERMAL)
            sub = disp[sel]
            pre = float(sub.loc[sub[hcol] < SEP_FIRST_HOUR, mwcol].abs().sum())
            post = float(sub.loc[sub[hcol] >= SEP_FIRST_HOUR, mwcol].sum())
            if pre > 1e-6 or post <= 0.0:
                raise SystemExit(
                    f"{leg.name}: PowerSouth dispatch Jan-Aug {pre:.3f} MWh (want 0), "
                    f"Sep-Dec {post:.1f} MWh (want > 0)"
                )
            ev.update(aec_jan_aug_mwh=pre, aec_sep_dec_gwh=round(post / 1e3, 1))
        sysf = pd.read_parquet(leg / "hourly" / f"system_{year}.parquet")
        dem = float(sysf.loc[sysf["pass"] == "P1", "demand"].sum()) / 1e6
        ev["demand_twh"] = round(dem, 4)
        if year == 2019 and abs(dem - DEMAND_2019_TWH) > 0.01:
            raise SystemExit(
                f"{leg.name}: 2019 demand-with-interchange {dem:.4f} TWh, expected "
                f"{DEMAND_2019_TWH} (R1 not live?)"
            )
        evidence[year] = ev
        print(f"  {leg.name}: repairs OK {ev}")
    return evidence


def main() -> None:
    """CLI entry."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--pinned-sha", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true", help="assert, do not compose")
    a = ap.parse_args()
    legs = [ROOT / p if not Path(p).is_absolute() else Path(p) for p in a.legs]
    assert_lane(legs)
    assert_repairs(legs, a.pinned_sha)
    if a.check_only:
        return
    if not a.out:
        raise SystemExit("--out is required unless --check-only")
    out = ROOT / a.out if not Path(a.out).is_absolute() else Path(a.out)
    _compose(legs, out, True)


if __name__ == "__main__":
    main()
