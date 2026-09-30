"""NYISO-NEXT-13 G-1 leg acceptance + span composition (zero LP).

The arm is the NEXT-12 keeper's recipe replayed at the pin with ONE delta,
``nyiso_ne_ac_recon_detach: true`` (``docs/PRECOMMIT-nyiso-next13-ne-ac-recon-detach-2026-09-29.md``
sec. 5 G-1). Per leg:

* S0 -- solved at the pin (``git.basis_sha``);
* S1 -- ``scenario_config`` equals the keeper bundle's except exactly
  ``nyiso_ne_ac_recon_detach`` False -> True (``nyiso_firm_imports``, rule-26 retired, and
  ``retiree_cems_cap`` are ignored); offer-curve block equal;
* S2 -- ``resolved_inputs`` byte-identical to the keeper bundle's;
* S3 -- no D-2 ``firm_import`` row in the leg's ``legitimacy_diagnostics.json``;
* S4 -- ``dispatch/<y>_P1.parquet`` carries exactly 16 ``NYISO_NE_AC_*`` units.

Usage::

    python3 scripts/probes/nyisonext12_compose_span.py --check-only \\
        --legs results/calibration/nyisonext13_{2021,2022,2023,2024,2025}
    python3 scripts/probes/nyisonext12_compose_span.py \\
        --legs results/calibration/nyisonext13_{2022,2023,2024,2025} \\
        --out results/calibration/nyisonext13_span
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

PIN = "3145578d94c73b6042ecabf1ff6723c70af3c742"
CAL = _REPO / "results" / "calibration"
DELTA = {"nyiso_ne_ac_recon_detach": (False, True)}
#: keys the replay path translates identically for control and arm (rule 26 deletions;
#: nyiso_firm_imports was deleted at f26384a7 -- recorded false in the keeper, hash-inert)
IGNORED = {"retiree_cems_cap", "nyiso_firm_imports"}
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
    return CAL / ("nyisonext12_2021" if year == 2021 else "nyisonext12_span")


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
    ap.add_argument("--legs", nargs="+", required=True)
    ap.add_argument("--out")
    ap.add_argument("--check-only", action="store_true")
    args = ap.parse_args()
    legs = [Path(x) for x in args.legs]
    check_legs(legs)
    if args.check_only:
        return
    if not args.out:
        ap.error("--out is required unless --check-only")
    _compose(legs, Path(args.out))


if __name__ == "__main__":
    main()
