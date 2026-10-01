"""NYISO-NEXT-21 gates G-2 / G-3 / G-5 and the reported block (ZERO LP).

``docs/PRECOMMIT-nyiso-next21-astoria-heat-rate-2026-10-01.md`` sec. 3, every value
anchored to the keeper (``nyisonext18_2021`` / ``nyisonext18_span``) or to CAMPD:

G-2: Astoria 8906 ST_GAS P1 energy LOWER than the keeper's, every year.
G-3: per year and zone, P1 demand equals the keeper's within 0.1 GWh; P1 load
     slack exceeds the keeper's by <= 1 GWh.
G-5: no D-4 failure row keyed (year, mechanism, plant) in the arm's COMPOSED
     ``legitimacy_diagnostics.json`` absent from the keeper's.
G-1 is ``nyisonext21_compose_span.py --check-only``; G-4 is the scorer's C6 / C8.

Plant energy is read, for BOTH arms, from the registered run payload's per-plant
hourly CF (% of EIA-860 nameplate, 1 % resolution) so the two sides share one
basis; CAMPD is the committed bench part. The keeper's per-plant dispatch parquet
is not on ``main`` (repo-wide ignore), so the payload is the only common basis.

Usage::

    python3 scripts/probes/nyisonext21_gates.py --arm-span <run id> --arm-2021 <run id> \\
        --out results/calibration/_nyisonext21_gates.json
"""

from __future__ import annotations

import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
for p in (REPO, REPO / "scripts", REPO / "scripts" / "probes"):
    sys.path.insert(0, str(p))

import nyisonext17_gates as g17  # noqa: E402
from nyisonext21_d4_conduct_phase0 import _payload, _u8  # noqa: E402

CAL = REPO / "results" / "calibration"
BENCH = REPO / "frontend" / "data" / "backcast" / "bench" / "NYISO"
KEEP = {2021: "nyisonext18_2021", **{y: "nyisonext18_span" for y in range(2022, 2026)}}
ARM = {2021: "nyisonext21_2021", **{y: "nyisonext21_span" for y in range(2022, 2026)}}
KEEP_RUN = {
    2021: "2026-09-30-nyisonext18-retiree-carry-2021",
    **{y: "2026-09-30-nyisonext18-retiree-carry-span" for y in range(2022, 2026)},
}
ZONES = g17.ZONES
g17.CAL = CAL
#: NYC steam (Astoria, Ravenswood, Arthur Kill) and the Long Island / Hudson
#: steam that phase 0 found under-dispatched.
PLANTS = {
    "8906": "Astoria",
    "2500": "Ravenswood",
    "2490": "Arthur Kill",
    "2516": "Northport",
    "2511": "E F Barrett",
    "2625": "Bowline",
}


def _plant_twh(pay: dict, bench: dict, y: int, code: str) -> tuple[float, float]:
    """(model, CAMPD) ST_GAS TWh for one plant from the payload / bench."""
    plants = pay["years"][str(y)]["plants"]
    key = code if code in plants else f"{code}:ST_GAS"
    npl = float(bench[key]["npl"])
    m = float(_u8(plants[key]["m"]).sum()) * npl / 100 / 1e6
    a = float(_u8(bench[key]["campd"]).sum()) * npl / 100 / 1e6
    return round(m, 3), round(a, 3)


def year(y: int, pay_arm: dict, pay_keep: dict) -> dict:
    """All gates and the reported block for one year."""
    sa, sk = g17._sys(ARM[y], y), g17._sys(KEEP[y], y)
    da = sa.groupby("zone").demand.sum() / 1e3
    dk = sk.groupby("zone").demand.sum() / 1e3
    dz = {z: round(float(da[z] - dk[z]), 4) for z in ZONES}
    slack_a, slack_k = float(sa.slack.sum()) / 1e3, float(sk.slack.sum()) / 1e3
    g3_pass = all(abs(v) <= 0.1 for v in dz.values()) and slack_a - slack_k <= 1.0

    bench = json.load(gzip.open(BENCH / f"{y}.json.gz"))["bench"]["plants"]
    steam = {}
    for code, name in PLANTS.items():
        ma, act = _plant_twh(pay_arm, bench, y, code)
        mk, _ = _plant_twh(pay_keep, bench, y, code)
        steam[name] = {"arm": ma, "keeper": mk, "campd": act}
    ast = steam["Astoria"]
    nyc = {
        k: round(sum(steam[n][k] for n in ("Astoria", "Ravenswood", "Arthur Kill")), 3)
        for k in ("arm", "keeper", "campd")
    }

    new_d4 = sorted(
        map(str, g17._d4_fail_keys(ARM[y], y) - g17._d4_fail_keys(KEEP[y], y))
    )
    gone_d4 = sorted(
        map(str, g17._d4_fail_keys(KEEP[y], y) - g17._d4_fail_keys(ARM[y], y))
    )
    return {
        "G2_astoria_twh": ast,
        "G2_pass": ast["arm"] < ast["keeper"],
        "G3_zone_demand_delta_gwh": dz,
        "G3_slack_gwh": {"arm": round(slack_a, 3), "keeper": round(slack_k, 3)},
        "G3_pass": bool(g3_pass),
        "G5_new_d4_failures": new_d4,
        "G5_pass": not new_d4,
        "reported": {
            "steam_twh": steam,
            "nyc_steam_twh": nyc,
            "d4_cleared": gone_d4,
            "zone_lw_price": {
                z: {"arm": g17._lw(sa, z), "keeper": g17._lw(sk, z)} for z in ZONES
            },
        },
    }


def main() -> None:
    """All years; write the record."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--arm-span", required=True)
    ap.add_argument("--arm-2021", required=True)
    ap.add_argument("--years", type=int, nargs="+", default=list(range(2021, 2026)))
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    arm_run = {2021: a.arm_2021, **{y: a.arm_span for y in range(2022, 2026)}}
    cache: dict[str, dict] = {}

    def pay(rid: str) -> dict:
        if rid not in cache:
            cache[rid] = _payload(rid)
        return cache[rid]

    out = {str(y): year(y, pay(arm_run[y]), pay(KEEP_RUN[y])) for y in a.years}
    Path(a.out).write_text(json.dumps(out, indent=1) + "\n")
    for y, d in out.items():
        print(y, {k: d[k] for k in d if k.endswith("_pass")})
        print(
            "   Astoria",
            d["G2_astoria_twh"],
            "NYC steam",
            d["reported"]["nyc_steam_twh"],
        )
        print(
            "   G5 new", d["G5_new_d4_failures"], "cleared", d["reported"]["d4_cleared"]
        )


if __name__ == "__main__":
    main()
