"""nwpp-44: verify the three arm legs BEFORE composing them (ZERO LP).

Wave 1 of this lane produced a bundle that looked entirely plausible — a clean
`scenario_config` diff, a full file set, and a coal total landing on the EIA
actual to 0.01 TWh — and was nonetheless worthless, because the shard CLI had
omitted ``--hydro-backfill-year 2024`` and 255 of NWPP's 280 hydro plants
carried no energy budget. See
``docs/handoffs/ADDENDUM-nwpp-44-hydro-backfill-2026-09-20.md``.

The lesson that generalises: **a keeper's recipe is not fully described by its
``ScenarioConfig``.** Loader-level kwargs live only in ``meta.json``, so a diff
of the config surface alone cannot see them. This script therefore checks the
three surfaces that together pin a leg — ``meta.json``, ``scenario_config``, and
the SOLVED OUTPUT — and refuses a leg that fails any of them.

It is deliberately paranoid about the output checks: a missing input shows up in
the dispatch long before it shows up anywhere a config diff can reach, and the
cheapest reliable tell is that **adding cheap supply to a feasible LP can never
create unserved energy** (rule: slack must not blow up).

Run: ``python3 scripts/probes/_nwpp44_verify_legs.py``
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
CAL = REPO / "results" / "calibration"
KEEPER = CAL / "nwpp42_coalhr_span"

#: Per-year expectations, taken from the KEEPER's own committed sidecars.
#: hydro/slack are the wave-1 tripwires; the tolerances are loose because the
#: arm legitimately moves dispatch — what they catch is a MISSING INPUT, which
#: is an order of magnitude larger than any offer-side effect.
EXPECT = {
    2023: {"hydro_twh": 106.872, "slack_mwh": 4_221.665, "gas": 2.54},
    2024: {"hydro_twh": 107.879, "slack_mwh": 8_818.021, "gas": 2.19},
    2025: {"hydro_twh": 113.077, "slack_mwh": 0.0, "gas": 3.52},
}

#: The two fields this lane arms, and the one the owner's Option B ruling
#: deliberately leaves off (PRECOMMIT-nwpp-44 §1).
ARMED = ("coal_takeorpay_from_data", "coal_committed_takeorpay_regulated")
REFUSED = (
    "coal_prb_committed_dispatchable",
    "coal_committed_takeorpay_sunk_fixed",
    "coal_bit_committed_takeorpay",
    "coal_committed_takeorpay_all",
)

#: meta.json keys a single-year leg may legitimately differ from the keeper on.
META_OK_TO_DIFFER = {
    "basis_sha",
    "git_sha",
    "years",
    "timestamp",
    "composed_from",
    "gas_prices",
    "environment",
    "shared_inputs",
    "highspy_version",
}

HYDRO_TOL_TWH = 5.0  # generous: the wave-1 failure was 38 TWh
SLACK_CEILING = 100_000  # generous: the wave-1 failure was 1,330,909 MWh


def check(year: int, bundle: Path) -> list[str]:
    """Return a list of failure strings for one leg ([] means the leg is sound)."""
    bad: list[str] = []
    exp = EXPECT[year]

    if not bundle.is_dir():
        return [f"bundle {bundle} does not exist"]

    meta = json.loads((bundle / "meta.json").read_text())
    cfg = json.loads((bundle / "run_config.json").read_text())
    sc = cfg["scenario_config"]

    # --- surface 1: meta.json, where the wave-1 defect lived --------------
    if meta.get("hydro_backfill_year") != 2024:
        bad.append(
            f"meta.hydro_backfill_year = {meta.get('hydro_backfill_year')!r}, want 2024"
        )
    kmeta = json.loads((KEEPER / "meta.json").read_text())
    for k in sorted(set(kmeta) | set(meta)):
        if k in META_OK_TO_DIFFER:
            continue
        a, b = kmeta.get(k, "<absent>"), meta.get(k, "<absent>")
        if isinstance(a, list) and isinstance(b, list):
            a, b = tuple(a), tuple(b)
        if a != b:
            bad.append(f"meta.{k}: keeper={a!r} leg={b!r}")

    # --- surface 2: the armed/refused config -----------------------------
    for f in ARMED:
        if sc.get(f) is not True:
            bad.append(f"{f} = {sc.get(f)!r}, want True")
    for f in REFUSED:
        if sc.get(f) is not False:
            bad.append(f"{f} = {sc.get(f)!r}, want False (owner Option B)")
    if sc.get("weather_year") != year:
        bad.append(f"weather_year = {sc.get('weather_year')!r}, want {year}")
    if sc.get("gas_price_override") != exp["gas"]:
        bad.append(
            f"gas_price_override = {sc.get('gas_price_override')!r}, want {exp['gas']}"
        )

    # --- surface 3: the SOLVED OUTPUT (what a config diff cannot see) -----
    cls = bundle / "hourly" / f"class_hourly_{year}.parquet"
    sysf = bundle / "hourly" / f"system_{year}.parquet"
    disp = bundle / "dispatch" / f"{year}_P1.parquet"
    if not disp.is_file():
        bad.append(f"dispatch/{year}_P1.parquet MISSING — registration would fail")
    if cls.is_file():
        d = pd.read_parquet(cls)
        hyd = d[d["klass"] == "hydro"]["mw"].sum() / 1e6
        if abs(hyd - exp["hydro_twh"]) > HYDRO_TOL_TWH:
            bad.append(
                f"hydro {hyd:.3f} TWh vs keeper {exp['hydro_twh']:.3f} "
                f"(|Δ| > {HYDRO_TOL_TWH}) — the wave-1 backfill failure signature"
            )
    else:
        bad.append(f"{cls.name} MISSING")
    if sysf.is_file():
        s = pd.read_parquet(sysf)
        slack = float(s["slack"].sum())
        if slack > SLACK_CEILING:
            bad.append(
                f"slack {slack:,.0f} MWh > {SLACK_CEILING:,} — an arm that only makes "
                "supply CHEAPER cannot create unserved energy, so an input is missing"
            )
    else:
        bad.append(f"{sysf.name} MISSING")
    return bad


def main() -> int:
    print(f"verifying nwpp-44 arm legs against keeper {KEEPER.name}\n")
    worst = 0
    for year in sorted(EXPECT):
        bundle = CAL / f"nwpp44_takeorpay_{year}"
        bad = check(year, bundle)
        if bad:
            worst = 1
            print(f"[FAIL] {year}  {bundle.name}")
            for b in bad:
                print(f"         - {b}")
        else:
            d = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
            s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
            bit = d[d["klass"] == "COAL_BIT"]["mw"].sum() / 1e6
            prb = d[d["klass"] == "COAL_PRB"]["mw"].sum() / 1e6
            print(
                f"[ OK ] {year}  hydro {d[d.klass == 'hydro'].mw.sum() / 1e6:7.3f} TWh · "
                f"slack {float(s['slack'].sum()):10,.0f} MWh · "
                f"COAL_BIT {bit:7.3f} · COAL_PRB {prb:7.3f} TWh"
            )
    print(
        "\n"
        + (
            "SOME LEGS FAILED — do NOT compose or register."
            if worst
            else "all legs sound — safe to compose."
        )
    )
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
