"""FFR-8B Phase-0: the pre-registered re-base reads on the invocation-1 bundle.

The FFR-8A §1.5 read set re-run verbatim on the POST-EPOCH repair arm
(``docs/handoffs/ffr-8b-rebase-dispersion-2026-08-09.md`` §1.1), single-arm:

* **(i) price side** — per-screen price distribution (mean/max/h>$100/h>$1000,
  adder mean) off the ``screen_signal_diag_*.npz`` dumps, plus the per-fuel
  pro-forma replica margins at the SAME flat mc/availability basis the
  pre-epoch §4.1 record resolved to (``ffr8a_ablation_chain._FALLBACK_FUEL_BASIS``
  — verified arithmetically against the committed §4.1 control rows), so every
  delta vs the pre-epoch record is basis-identical.
* **(ii) exit side** — the gas_st 2022-bridge wave (n/MW/bar decomposition),
  in-window executed/economic exits, the fleet-wide ``entry_capped`` census,
  the coal cohort's event sequence, and the per-year reserve margins (the
  §4.2.4 cap-interaction context), from the evolution ledgers.
* **(iii)** additions are read from the bundle's ``score.json`` (decision
  basis) when present — reported, never targeted.
* **dispersion context for Phase 1** — per-dump quantiles of r_online/r_full/
  installed headroom/sigma_r (the §5(c) numbers re-based).

Read-only; never solves. Usage::

    uv run python scripts/probes/ffr8b_rebase_reads.py \
        --bundle results/hindcast/ercot-2021-2025-t1ff-armr-ffr8b-base \
        --out docs/handoffs/ffr-8b/rebase-reads-2026-08-09.json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.results.evolution_ledger import load_ledgers_for_run  # noqa: E402

# The flat per-fuel mc/availability basis the pre-epoch §4.1 margins resolved
# to (ffr8a_ablation_chain._FALLBACK_FUEL_BASIS; the FFR-6A probe JSON's layout
# does not expose per-fuel rows to _fuel_basis_from_ffr6a, so the fallback was
# the operative basis — kept verbatim here for delta comparability).
FUEL_BASIS = {
    "coal": {"mc_mean": 24.41, "availability_mean": 0.790},
    "gas_cc": {"mc_mean": 16.5, "availability_mean": 0.87},
    "gas_ct": {"mc_mean": 22.0, "availability_mean": 0.90},
    "gas_st": {"mc_mean": 28.0, "availability_mean": 0.80},
    "nuclear": {"mc_mean": 10.0, "availability_mean": 0.93},
}

PIPELINE_EVENTS = ("decided", "re_confirmed", "reversed", "executed")
DECOMP_FIELDS = (
    "net_revenue_usd",
    "going_forward_cost_usd",
    "energy_margin_usd",
    "reserve_uplift_usd",
    "attribute_revenue_usd",
    "capacity_revenue_usd",
    "as_annual_credit_usd",
)
BASIS_FIELDS = (
    "screen_price_mean_usd_mwh",
    "screen_price_max_usd_mwh",
    "reserve_signal_mean_usd_mwh",
    "availability_mean",
    "mc_mean_usd_mwh",
)


def _resolve_cache_dir(out_dir: Path) -> Path:
    iso_dir = out_dir / "ERCOT"
    keys = sorted(d for d in iso_dir.iterdir() if d.is_dir())
    if len(keys) != 1:
        raise SystemExit(f"{iso_dir}: expected exactly one cache-key dir, found {keys}")
    return keys[0]


def _dist(p: np.ndarray) -> dict:
    return {
        "mean": round(float(np.mean(p)), 3),
        "max": round(float(np.max(p)), 1),
        "h_gt_100": int((p > 100.0).sum()),
        "h_gt_1000": int((p > 1000.0).sum()),
    }


def _margins(p: np.ndarray) -> dict:
    return {
        fuel: round(
            float(np.clip(p - b["mc_mean"], 0.0, None).sum())
            * b["availability_mean"]
            / 1000.0,
            2,
        )
        for fuel, b in FUEL_BASIS.items()
    }


def _q(x: np.ndarray) -> dict:
    x = np.asarray(x, dtype=float)
    return {
        "mean": round(float(x.mean()), 1),
        "p50": round(float(np.percentile(x, 50)), 1),
        "p25": round(float(np.percentile(x, 25)), 1),
        "p10": round(float(np.percentile(x, 10)), 1),
        "p5": round(float(np.percentile(x, 5)), 1),
        "p1": round(float(np.percentile(x, 1)), 1),
        "min": round(float(x.min()), 1),
    }


def _capw(rows: list[dict], field: str) -> float:
    mw = sum(float(r.get("mw", 0.0)) for r in rows)
    if mw <= 0.0:
        return 0.0
    return sum(float(r.get(field, 0.0)) for r in rows) / (mw * 1000.0)


def _capw_basis(rows: list[dict], field: str) -> float:
    mw = sum(float(r.get("mw", 0.0)) for r in rows)
    if mw <= 0.0:
        return 0.0
    return sum(float(r.get(field, 0.0)) * float(r.get("mw", 0.0)) for r in rows) / mw


def _mw_by_fuel(rows: list[dict]) -> dict[str, float]:
    acc: dict[str, float] = defaultdict(float)
    for r in rows:
        acc[r.get("fuel", "?")] += float(r.get("mw", 0.0))
    return {k: round(v, 1) for k, v in sorted(acc.items())}


def price_side(cache_dir: Path) -> dict:
    """(i): per-screen distributions + margins + dispersion context."""
    out: dict = {}
    for path in sorted(cache_dir.glob("screen_signal_diag_*_for_*.npz")):
        with np.load(path, allow_pickle=False) as z:
            d = {k: z[k] for k in z.files}
        entering = int(d["entering_year"])
        price = np.asarray(d["price_base_usd_mwh"], dtype=float) + np.asarray(
            d["adder_usd_mwh"], dtype=float
        )
        row = {
            **_dist(price),
            "adder_mean": round(float(np.mean(d["adder_usd_mwh"])), 3),
            "base_mean": round(float(np.mean(d["price_base_usd_mwh"])), 3),
            "margins": _margins(price),
            "net_load_system_mw": _q(-np.sort(-d["net_load_system_mw"])),
            "installed_headroom_mw": _q(d["installed_headroom_mw"]),
        }
        for key in ("r_online_mw", "r_full_mw", "sigma_r_mw", "as_hold_mw"):
            if key in d:
                row[key.replace("_mw", "_q_mw")] = _q(d[key])
        if "storage_as_mw" in d:
            row["storage_as_mw"] = round(float(d["storage_as_mw"]), 1)
        if "storage_power_mw" in d:
            row["storage_power_mw"] = round(float(d["storage_power_mw"]), 1)
        solve_year = int(path.stem.split("_")[3])
        out[f"solve_{solve_year}_entering_{entering}"] = row
    if not out:
        raise SystemExit(f"no screen_signal_diag dumps under {cache_dir}")
    return out


def exit_side(cache_dir: Path) -> dict:
    """(ii): the ledger reads, single-arm (adapted from ffr5d_paired_arm)."""
    ledgers = load_ledgers_for_run(cache_dir)
    if not ledgers:
        raise SystemExit(f"{cache_dir}: load_ledgers_for_run returned {{}}")
    out: dict = {"years": sorted(ledgers)}
    seq: dict = {}
    for year in sorted(ledgers):
        rows = ledgers[year].get("pipeline_events") or []
        for event in PIPELINE_EVENTS:
            ev_rows = [r for r in rows if r.get("event") == event]
            if not ev_rows:
                continue
            for label, grp in (
                ("all", ev_rows),
                ("coal", [r for r in ev_rows if r.get("fuel") == "coal"]),
                ("gas_st", [r for r in ev_rows if r.get("fuel") == "gas_st"]),
            ):
                if not grp:
                    continue
                entry = {
                    "n": len(grp),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in grp), 1),
                    "decided_years": sorted(
                        {r.get("decided_year") for r in grp if "decided_year" in r}
                    ),
                    "execute_years": sorted(
                        {r.get("execute_year") for r in grp if "execute_year" in r}
                    ),
                }
                if any(f in r for r in grp for f in DECOMP_FIELDS):
                    entry["bar_usd_per_kw_yr"] = {
                        f.replace("_usd", ""): round(_capw(grp, f), 2)
                        for f in DECOMP_FIELDS
                    }
                    entry["basis"] = {
                        f: round(_capw_basis(grp, f), 3)
                        for f in BASIS_FIELDS
                        if any(f in r for r in grp)
                    }
                seq.setdefault(str(year), {}).setdefault(event, {})[label] = entry
    out["pipeline_sequence"] = seq

    census: dict = {}
    for year in sorted(ledgers):
        rows = [
            r
            for r in (ledgers[year].get("pipeline_events") or [])
            if r.get("event") == "entry_capped"
        ]
        if not rows:
            continue
        by_fuel: dict[str, dict] = defaultdict(lambda: {"n": 0, "mw": 0.0})
        for r in rows:
            f = by_fuel[r.get("fuel", "?")]
            f["n"] += 1
            f["mw"] += float(r.get("mw", 0.0))
        census[str(year)] = {
            "total": {
                "n": len(rows),
                "mw": round(sum(float(r.get("mw", 0.0)) for r in rows), 1),
            },
            "by_fuel": {
                k: {"n": v["n"], "mw": round(v["mw"], 1)}
                for k, v in sorted(by_fuel.items())
            },
        }
    out["entry_capped"] = census

    exits: dict = {}
    for year in sorted(ledgers):
        led = ledgers[year]
        executed = [
            r for r in (led.get("pipeline_events") or []) if r.get("event") == "executed"
        ]
        econ = [r for r in (led.get("retirements") or []) if r.get("reason") == "economic"]
        if executed or econ:
            exits[str(year)] = {
                "pipeline_executed": {
                    "n": len(executed),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in executed), 1),
                    "by_fuel": _mw_by_fuel(executed),
                },
                "economic_retirements": {
                    "n": len(econ),
                    "mw": round(sum(float(r.get("mw", 0.0)) for r in econ), 1),
                    "by_fuel": _mw_by_fuel(econ),
                },
            }
    out["thermal_exits"] = exits
    out["reserve_margins"] = {
        str(y): ledgers[y].get("reserve_margin") for y in sorted(ledgers)
    }
    out["bridged_years"] = [y for y in sorted(ledgers) if ledgers[y].get("bridge")]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--bundle", required=True, help="run_capacity_hindcast out-dir")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    bundle = Path(args.bundle)
    cache_dir = _resolve_cache_dir(bundle)
    result: dict = {
        "probe": "ffr8b_rebase_reads phase 0",
        "cache_dir": str(cache_dir),
        "price_side": price_side(cache_dir),
        "exit_side": exit_side(cache_dir),
    }
    score_path = cache_dir / "score.json"
    if score_path.exists():
        score = json.loads(score_path.read_text())
        result["additions_decision_basis"] = score.get("additions")
        result["retirements_score"] = score.get("retirements")
    out_path = REPO / args.out
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n")
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
