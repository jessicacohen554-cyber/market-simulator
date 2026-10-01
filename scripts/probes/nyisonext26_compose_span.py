"""NYISO-NEXT-26: G-1 leg acceptance and span composition for both arms.

The arms are the NEXT-21 keeper's recipe replayed at the pin with the PRECOMMIT's delta
(``docs/records/nyiso/PRECOMMIT-nyiso-next26-li-tsl-all-hours-2026-10-01.md``):

* arm A: ``nyiso_li_tsl_all_hours: true``;
* arm B: ``nyiso_gas_daily_print_level: true`` and ``nyiso_li_tsl_all_hours: true``.

Per leg it checks S0 (solved at the pin), S1 (scenario_config equals the keeper's plus the
arm's delta, keys born since at their default; offer-curve block identical), S2 (resolved
outage / tranche / hydro inputs identical) and S3/S4 (no firm-import D-2 row; 16 NE-AC nodes).
Adapted from ``nyisonext26_compose_span.py`` (PR #6987's branch).

Usage::

    python3 scripts/probes/nyisonext26_compose_span.py --arm A --check-only \\
        --legs results/calibration/nyisonext26_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext26_compose_span.py --arm A \\
        --legs results/calibration/nyisonext26_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext26_span
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.probes.nyiso238_compose_span import compose as _compose  # noqa: E402
from scripts.probes.rnyiso_compose_span import _offer_block  # noqa: E402

sys.path.insert(0, str(_REPO / "src"))

PIN = "SET_AT_MERGE"
CAL = _REPO / "results" / "calibration"
DELTAS: dict = {
    "A": {"nyiso_li_tsl_all_hours": (False, True)},
    "B": {
        "nyiso_gas_daily_print_level": (False, True),
        "nyiso_li_tsl_all_hours": (False, True),
    },
}
DELTA: dict = DELTAS["A"]
#: keys the replay path translates identically for control and arm (rule 26 deletions;
#: nyiso_firm_imports was deleted at f26384a7 -- recorded false in the keeper, hash-inert)
IGNORED = {"retiree_cems_cap", "nyiso_firm_imports", "cc_subfloor_eia923_heat_rates"}
#: year-keyed fields replay_keeper re-derives per solve year (the composite keeper
#: records its first leg's value); S1 checks weather_year == the leg's year instead
YEAR_KEYED = {"weather_year", "gas_price_override"}
#: resolved-input artifacts that must be byte-identical to the keeper's (sha256 / record)
INPUT_KEYS = ("campd_unit_outages", "thermal_tranches", "hydro_plant_modes")


def _new_field_default(key: str, value: object) -> bool:
    """True when ``key`` post-dates the keeper and the arm carries its default."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    fields = {f.name: f for f in dataclasses.fields(ScenarioConfig)}
    f = fields.get(key)
    return f is not None and f.default is not dataclasses.MISSING and f.default == value


def _field_default(key: str) -> object:
    """``ScenarioConfig``'s default for ``key`` (``None`` if it has none)."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    for f in dataclasses.fields(ScenarioConfig):
        if f.name == key and f.default is not dataclasses.MISSING:
            return f.default
    return None


def _keeper(year: int) -> Path:
    """The keeper bundle carrying ``year``."""
    return CAL / ("nyisonext21_2021" if year == 2021 else "nyisonext21_span")


def check_legs(legs: list[Path]) -> None:
    """Fail loud if any leg misses S0-S3."""
    bad: list[str] = []
    for leg in legs:
        y = int(leg.name.rsplit("_", 1)[-1])
        rc = json.loads((leg / "run_config.json").read_text())
        kc = json.loads((_keeper(y) / "run_config.json").read_text())
        errs: list[str] = []
        basis = (rc.get("git") or {}).get("basis_sha") or ""
        if basis != PIN:
            errs.append(f"S0 basis_sha {basis!r}")
        sa, sk = rc["scenario_config"], kc["scenario_config"]
        # a field that post-dates the keeper is read at its dataclass default
        # (the keeper solved without it, i.e. at the default)
        sk = {**{k: _field_default(k) for k in sa if k not in sk}, **sk}
        diff = {
            k: (sk.get(k), sa.get(k))
            for k in set(sa) | set(sk)
            if k not in IGNORED | YEAR_KEYED
            and sa.get(k) != sk.get(k)
            and not (k not in sk and _new_field_default(k, sa.get(k)))
        }
        if sa.get("weather_year") != y:
            errs.append(f"S1 weather_year {sa.get('weather_year')!r}")
        if diff != DELTA:
            errs.append(f"S1 scenario_config delta {diff}")
        if _offer_block(rc) != _offer_block(kc):
            errs.append("S1 offer-curve block differs from the keeper")
        ra, rk = rc.get("resolved_inputs") or {}, kc.get("resolved_inputs") or {}
        for key in INPUT_KEYS:
            if ra.get(key) != rk.get(key):
                errs.append(f"S2 resolved_inputs[{key}] differs from the keeper")
        ld = json.loads((leg / "legitimacy_diagnostics.json").read_text())
        rows = ld["diagnostics"]["D2"]["rows"]
        if any(r.get("mechanism") == "firm_import" for r in rows):
            errs.append("S3 D-2 firm_import row present")
        import pandas as pd

        dp = pd.read_parquet(leg / "dispatch" / f"{y}_P1.parquet")
        col = "unit_id" if "unit_id" in dp.columns else dp.columns[0]
        n_node = int(
            dp[col]
            .astype(str)
            .str.startswith("NYISO_NE_AC_")
            .pipe(lambda m: dp.loc[m, col].nunique())
        )
        if n_node != 16:
            errs.append(f"S4 {n_node} NYISO_NE_AC_* units in dispatch (want 16)")
        print(f"  {leg.name}: {'OK' if not errs else errs}")
        if errs:
            bad.append(leg.name)
    if bad:
        raise SystemExit(f"legs {bad} fail G-1; refusing to compose")


def main() -> None:
    """Check every leg, then compose the span bundle."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm", choices=sorted(DELTAS), required=True)
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    global DELTA
    DELTA = DELTAS[args.arm]
    legs = [Path(x) for x in args.legs]
    check_legs(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
