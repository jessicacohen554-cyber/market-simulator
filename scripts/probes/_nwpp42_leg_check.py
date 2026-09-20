"""nwpp-42: signature-check and summarise one per-year leg against the keeper.

Rule 36 ``[R-YEAR-ISOLATION]`` solves each backcast year in its own container,
so every leg is a SINGLE-YEAR bundle while the incumbent keeper
(``results/calibration/nwpp41_span_A``) is a THREE-YEAR span. A naive
``scenario_config`` diff against that span therefore reports differences that
are not mechanism changes at all, and the first run of this lane's check nearly
condemned a clean leg on them. This probe classifies every delta instead of
counting them, into exactly three buckets:

``YEAR``
    The span's ``run_config.json`` snapshots its FIRST year (2023), so a 2024 or
    2025 leg legitimately carries that year's own ``gas_price_override`` and
    ``weather_year``. The value is verified against the keeper's own
    ``meta.json`` ``gas_prices`` map rather than trusted, so a genuinely wrong
    fuel price is still caught.

``NEW-FIELD-AT-DEFAULT``
    A ``ScenarioConfig`` field that did not exist when the keeper solved reads
    ``None`` in its config and its default in the leg's. Admitted ONLY when the
    leg's value equals the current dataclass default AND the field is
    registered in ``_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS`` at that same value —
    i.e. the repo itself declares it cannot move a solve. Anything else is LIVE.

``LIVE``
    A real mechanism delta. The arm legs must show exactly one,
    ``measured_coal_heat_rates None -> True``; the control legs must show none.

Run: ``python3 scripts/probes/_nwpp42_leg_check.py <bundle-dir> <year> arm|ctl``

NOTE (2026-09-20, after the NWPP-42 promotion): ``KEEPER`` below still points at
``results/calibration/nwpp41_span_A``, which was PRUNED from the working tree at
that promotion under rule 15's keeper-only retention (git history is the record;
recover with ``git checkout 1fb4b6b5c680ca5ae0ef9375eb11b7cbbb08d64d --
results/calibration/nwpp41_span_A``). The probe is kept as this lane's record of
how each leg was checked, not as standing tooling; a successor re-points
``KEEPER`` at its own control before running it.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

KEEPER = Path("results/calibration/nwpp41_span_A")
#: Fields the span config snapshots for its first year only (see module docstring).
_YEAR_CARRIED = ("gas_price_override", "weather_year")


def _scenario(path: Path) -> dict:
    d = json.loads(path.read_text())
    return d.get("scenario_config", d)


def classify(bundle: Path, year: int) -> tuple[list, list, list]:
    """Return ``(live, year_carried, new_at_default)`` deltas vs the keeper."""
    from market_sim.config.scenarios import (  # noqa: PLC0415
        _CACHE_KEY_OPTIONAL_FIELD_DEFAULTS as DROPS,
    )
    from market_sim.config.scenarios import ScenarioConfig  # noqa: PLC0415

    arm = _scenario(bundle / "run_config.json")
    keep = _scenario(KEEPER / "run_config.json")
    keeper_gas = json.loads((KEEPER / "meta.json").read_text()).get("gas_prices", {})

    live, year_carried, new_default = [], [], []
    for k in sorted(set(arm) | set(keep)):
        a, b = arm.get(k), keep.get(k)
        if a == b:
            continue
        row = (k, b, a)
        if k == "gas_price_override":
            # Must equal the price the KEEPER itself used for this year.
            expected = keeper_gas.get(str(year))
            (year_carried if expected is not None and a == expected else live).append(row)
        elif k == "weather_year":
            (year_carried if a == year else live).append(row)
        elif b is None and a == getattr(ScenarioConfig(), k, object()) and DROPS.get(k) == repr(a).strip("'"):
            new_default.append(row)
        elif b is None and a == getattr(ScenarioConfig(), k, object()) and str(DROPS.get(k)) == str(a):
            new_default.append(row)
        else:
            live.append(row)
    return live, year_carried, new_default


def main() -> int:
    bundle, year, kind = Path(sys.argv[1]), int(sys.argv[2]), sys.argv[3].lower()
    live, yr, nd = classify(bundle, year)
    meta = json.loads((bundle / "meta.json").read_text())

    print(f"=== {bundle.name} ({year}, {kind}) ===")
    for lab, rows in (("YEAR-CARRIED", yr), ("NEW-FIELD-AT-DEFAULT", nd), ("LIVE", live)):
        print(f"  {lab}: {len(rows)}")
        for k, b, a in rows:
            print(f"      {k}: {b!r} -> {a!r}")

    print(f"  meta hydro_backfill_year: {meta.get('hydro_backfill_year')}")
    print(f"  meta prb_overrides:       {meta.get('coal_prb_sigmoid_overrides')}")
    print(f"  meta years:               {meta.get('years')}")

    want = {("measured_coal_heat_rates", None, True)} if kind == "arm" else set()
    ok = set(live) == want
    ok &= meta.get("hydro_backfill_year") == 2024
    ok &= bool((meta.get("coal_prb_sigmoid_overrides") or {}).get("hydro_cascade_coupling"))
    ok &= meta.get("years") == [year]
    for f in (f"dispatch/{year}_P1.parquet", "system.parquet",
              f"hourly/hydro_cascade_{year}.parquet", f"hourly/system_{year}.parquet"):
        present = (bundle / f).exists()
        ok &= present
        if not present:
            print(f"  MISSING ARTIFACT: {f}")
    print(f"  VERDICT: {'PASS' if ok else 'FAIL'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
