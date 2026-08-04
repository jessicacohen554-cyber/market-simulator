"""miso-124 A/B scorer — dual_fuel_switching re-armed on the current keeper.

Scores the single-delta arm ``results/calibration/miso124_dualfuel_B``
(``dual_fuel_switching=true``) against the keeper it was replayed from,
``results/calibration/miso122_scopegate_B`` (``2026-08-04-miso-122b-scope-gate``).

NO LP IS SOLVED HERE — every number is read from the two committed bundles.

The mechanism's VERDICT is not re-adjudicated: miso-121 settled it (fully
identified, price-inert, cell ``I``). This session restores the arming on the
owner's rule 1 ``[R-STRUCT]`` call, so the gates below test one thing only —
**that nothing regresses**. The session brief's stop condition is explicit: if
any gate regresses against miso-122b, stop and report rather than promote,
because that would mean the flag interacts with the miso-122 scope gate.

Gates:

K1  flag fidelity      — the arm records ``dual_fuel_switching=true``, the
                         keeper ``false``, and both siblings are OFF in BOTH
                         (rule 19 [R-ONE-MECH]).
K2  single delta       — the two scenario blocks differ in exactly one key.
K3  year span          — both bundles ``[2023, 2024, 2025]`` (rules 16 / 22).
K4  liveness           — dispatch and price legs, reported at the grains that
                         are actually predictive. Per miso-122's DO-NOT-MISREAD
                         the max class-hour delta is NOT a magnitude at MISO (it
                         lands on the import class where one 912.5 MW seam band
                         flips), so per-class ENERGY deltas are reported
                         alongside it and are the magnitude of record.
K5  direction integrity— a ``min(gas, oil)`` cap can only LOWER a delivered
                         cost, so the system demand-weighted lambda must never
                         rise. Checked, not assumed.
K6  no gate regression — the arm's nine criterion statuses, determination and
                         ledgered-caveat budget against the keeper's, plus the
                         legitimacy-diagnostic verdicts (D-1 / D-2 / D-4 / D-5 /
                         D-9 / D-10). THIS is the gate the session turns on.

Rule 22 [R-HOLDOUT]: 2023-2025 only. Writes
``results/calibration/_miso124_dualfuel_rearm_ab.json``.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parent.parent.parent
KEEPER = REPO / "results/calibration/miso122_scopegate_B"
ARM = REPO / "results/calibration/miso124_dualfuel_B"
OUT = REPO / "results/calibration/_miso124_dualfuel_rearm_ab.json"
YEARS = (2023, 2024, 2025)
SIBLINGS = ("dual_fuel_oil_reattribution", "dual_fuel_oil_daily_parity")


def _scenario(bundle: Path) -> dict:
    return json.loads((bundle / "run_config.json").read_text())["scenario_config"]


def _classes(bundle: Path, year: int) -> pd.DataFrame:
    c = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    return (
        c[c["pass"] == "P1"]
        .pivot_table(index="hour", columns="klass", values="mw")
        .sort_index()
    )


def _system(bundle: Path, year: int) -> tuple[pd.DataFrame, pd.DataFrame]:
    s = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    s = s[s["pass"] == "P1"]
    return (
        s.pivot_table(index="hour", columns="zone", values="price").sort_index(),
        s.pivot_table(index="hour", columns="zone", values="demand").sort_index(),
    )


def _diagnostic_verdicts(bundle: Path) -> dict:
    """Every verdict string in a bundle's legitimacy diagnostics, keyed by row."""
    path = bundle / "legitimacy_diagnostics.json"
    if not path.exists():
        return {}
    diags = json.loads(path.read_text()).get("diagnostics", {})
    out: dict[str, str] = {}
    for block, payload in diags.items():
        rows = payload.get("rows", payload) if isinstance(payload, dict) else payload
        if not isinstance(rows, list):
            continue
        for row in rows:
            if not isinstance(row, dict) or "verdict" not in row:
                continue
            key = "|".join(
                str(row.get(f))
                for f in ("year", "klass", "class", "mechanism", "driver", "check")
                if f in row
            )
            out[f"{block}:{key}"] = str(row["verdict"])
    return out


def main() -> None:
    ka, aa = _scenario(KEEPER), _scenario(ARM)
    diff = {k: (ka.get(k), aa.get(k)) for k in set(ka) | set(aa) if ka.get(k) != aa.get(k)}
    km = json.loads((KEEPER / "meta.json").read_text())
    am = json.loads((ARM / "meta.json").read_text())

    res: dict = {
        "session": "miso-124",
        "keeper": {"bundle": KEEPER.name, "run_id": "2026-08-04-miso-122b-scope-gate"},
        "arm": {"bundle": ARM.name, "run_id": "2026-08-04-miso-124-dualfuel-rearm"},
        "K1_flag_fidelity": {
            "keeper_dual_fuel_switching": ka.get("dual_fuel_switching"),
            "arm_dual_fuel_switching": aa.get("dual_fuel_switching"),
            "siblings_off_both": {
                s: [ka.get(s), aa.get(s)] for s in SIBLINGS
            },
            "verdict": "PASS"
            if ka.get("dual_fuel_switching") is False
            and aa.get("dual_fuel_switching") is True
            and all(not ka.get(s) and not aa.get(s) for s in SIBLINGS)
            else "FAIL",
        },
        "K2_single_delta": {
            "n_differing_keys": len(diff),
            "keys": {k: list(v) for k, v in diff.items()},
            "verdict": "PASS" if list(diff) == ["dual_fuel_switching"] else "FAIL",
        },
        "K3_year_span": {
            "keeper_years": km.get("years"),
            "arm_years": am.get("years"),
            "verdict": "PASS"
            if km.get("years") == am.get("years") == [2023, 2024, 2025]
            else "FAIL",
        },
    }

    max_dmw, max_dlmp, d_sys, energy, price_hours = {}, {}, {}, {}, {}
    for year in YEARS:
        ck, cA = _classes(KEEPER, year), _classes(ARM, year)
        cA = cA.reindex(columns=ck.columns, fill_value=0.0)
        d = cA - ck
        pk, dem = _system(KEEPER, year)
        pa, _ = _system(ARM, year)
        zc = [c for c in pk.columns if c.startswith("MISO-")]
        dl = (pa[zc] - pk[zc]).to_numpy()

        max_dmw[str(year)] = float(np.abs(d.to_numpy()).max())
        max_dlmp[str(year)] = float(np.abs(dl).max())
        wk = (pk[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        wa = (pa[zc] * dem[zc]).sum(axis=1) / dem[zc].sum(axis=1)
        d_sys[str(year)] = float((wa - wk).mean())
        # miso-122 DO-NOT-MISREAD: per-class ENERGY is the magnitude of record.
        energy[str(year)] = {
            k: round(float(v) / 1e3, 6)
            for k, v in d.sum().items()
            if abs(v) > 1e-6  # GWh
        }
        price_hours[str(year)] = {
            "hours_with_any_zonal_delta": int((np.abs(dl).max(axis=1) > 1e-9).sum()),
            "zone_hours_price_rose": int((dl > 1e-9).sum()),
            "zone_hours_price_fell": int((dl < -1e-9).sum()),
        }

    res["K4_liveness"] = {
        "max_abs_class_hour_mw": max_dmw,
        "max_abs_class_hour_mw_note": (
            "NOT a mechanism magnitude at MISO (miso-122 DO-NOT-MISREAD): it "
            "lands on the import class where a single 912.5 MW seam band flips. "
            "Read class_energy_delta_gwh instead."
        ),
        "max_zonal_abs_dlmp": max_dlmp,
        "class_energy_delta_gwh": energy,
        "price_delta_hours": price_hours,
    }
    res["max_zonal_abs_dlmp"] = max_dlmp  # consumed by the attestation generator
    res["K5_direction_integrity"] = {
        "d_system_demand_weighted_lambda": d_sys,
        "rule": "a min(gas, oil) cap can only lower a delivered cost; system lambda must never rise",
        "verdict": "PASS" if all(v <= 1e-9 for v in d_sys.values()) else "FAIL",
    }

    # ---- K6: the gate that decides whether this arm may be promoted --------
    km_metrics = KEEPER / "metrics.json"
    am_metrics = ARM / "metrics.json"
    crit = {}
    if km_metrics.exists() and am_metrics.exists():
        mk = json.loads(km_metrics.read_text())
        ma = json.loads(am_metrics.read_text())
        ck_ = mk.get("criteria", {})
        ca_ = ma.get("criteria", {})
        for name in sorted(set(ck_) | set(ca_)):
            sk = (ck_.get(name) or {}).get("status")
            sa = (ca_.get(name) or {}).get("status")
            crit[name] = {"keeper": sk, "arm": sa, "changed": sk != sa}
        det = {
            "keeper": mk.get("determination"),
            "arm": ma.get("determination"),
        }
        cav = {
            "keeper": sorted(mk.get("caveats") or []),
            "arm": sorted(ma.get("caveats") or []),
        }
    else:
        det = {"keeper": None, "arm": None}
        cav = {"keeper": None, "arm": None}

    vk, va = _diagnostic_verdicts(KEEPER), _diagnostic_verdicts(ARM)
    diag_changes = {
        k: [vk.get(k), va.get(k)] for k in sorted(set(vk) | set(va)) if vk.get(k) != va.get(k)
    }
    regressed = [n for n, v in crit.items() if v["changed"]]
    res["K6_no_gate_regression"] = {
        "determination": det,
        "ledgered_caveats": cav,
        "criteria": crit,
        "criteria_changed": regressed,
        "diagnostic_verdict_changes": diag_changes,
        "n_diagnostic_rows_compared": len(set(vk) | set(va)),
        "verdict": "PASS"
        if not regressed
        and not diag_changes
        and det["keeper"] == det["arm"]
        and det["arm"] is not None
        and cav["keeper"] == cav["arm"]
        else "FAIL",
    }

    gates = {k: v["verdict"] for k, v in res.items() if isinstance(v, dict) and "verdict" in v}
    res["gates"] = gates
    res["all_pass"] = all(v == "PASS" for v in gates.values())

    OUT.write_text(json.dumps(res, indent=1) + "\n")
    print(f"wrote {OUT.relative_to(REPO)}")
    for k, v in gates.items():
        print(f"  {k:>26}: {v}")
    print(f"  {'ALL':>26}: {'PASS' if res['all_pass'] else 'FAIL'}")
    print("\n  max zonal |dLMP| $/MWh:", max_dlmp)
    print("  d system demand-wtd lambda:", d_sys)
    print("  determination:", det)
    print("  ledgered caveats:", cav)
    if diag_changes:
        print("  DIAGNOSTIC VERDICT CHANGES:", diag_changes)


if __name__ == "__main__":
    main()
