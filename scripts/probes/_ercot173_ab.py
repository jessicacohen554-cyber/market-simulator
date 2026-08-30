"""ercot-173 A/B scorer (read-only): the inherited PRECOMMIT-ercot172 §5 gates.

Scores control (Run A) vs arm (Run B) on the gates PRECOMMIT-ercot173 §5
assigns — inherited verbatim from PRECOMMIT-ercot172 §5, G-BIT declared N/A
pre-solve (year-agnostic rule) and replaced by G-SPAN — plus the ercot-167
re-score definitions (RG-1/RG-2) and the owner's 2023 object reported first.

Conventions: the standard analyzer's demand-weighted P1 system price
(`_ercot89_span_check.py`), the committed actual RT parquet, spurious =
model >= $150 & actual < $150 (LIDLESS since the ercot-225 card's Option A,
owner-signed 2026-08-26 — the gate must not be escapable by overshooting
the band top; the [150,500]-band and >500-top split stays reported as
``spurious_band`` / ``spurious_top``), tail caught = model>200 & actual>200.

Read-only: consumes the two bundles' hourly sidecars; solves nothing.

Usage::

    python scripts/probes/_ercot173_ab.py \
        --base results/calibration/ercot173_control_A \
        --probe results/calibration/ercot173_reconc_B \
        [--out results/calibration/_ercot173_ab.json]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
ACTUAL_LMP = REPO / "data" / "raw" / "_validation-source" / "actual_lmp_hourly_ERCOT.parquet"
DEFAULT_OUT = REPO / "results" / "calibration" / "_ercot173_ab.json"
YEARS = (2023, 2024, 2025)
MID_BAND = (150.0, 500.0)

# The 2024 spike days (true calendar dates, ercot-172 correction) and the
# RG-2 named hour, on the model's fixed non-leap clock.
SPIKE_2024 = {"2024-04-28": range(2808, 2832), "2024-05-08": range(3048, 3072)}
RG2_HOUR_2025 = 7051  # 2025-10-21 19:00 CST
# G-C3c ledgered tail counts on the keeper (model total >$200 / actual >$200
# — the standing _ercot89_span_check basis, which reproduces the ledger's
# 61/25/3 on the committed keeper exactly; "degrade" = the model count moves
# AWAY from the actual count).
C3C_LEDGER = {2023: (61, 181), 2024: (25, 53), 2025: (3, 31)}


def lw_price(bundle: Path, year: int) -> np.ndarray:
    """Hourly demand-weighted system P1 price for ``year``."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    num = (df["price"] * df["demand"]).groupby(df["hour"]).sum()
    den = df.groupby("hour")["demand"].sum()
    return (num / den).reindex(range(8760)).to_numpy(float)


def shed_hours(bundle: Path, year: int) -> list[int]:
    """Hours with positive load shed (system slack > 1 MW)."""
    df = pd.read_parquet(bundle / "hourly" / f"system_{year}.parquet")
    df = df[(df["year"] == year) & (df["pass"] == "P1")]
    s = df.groupby("hour")["slack"].sum()
    return sorted(int(h) for h in s.index[s > 1.0])


def class_energy(bundle: Path, year: int) -> dict[str, float]:
    """Annual P1 energy (GWh) per scoring class."""
    df = pd.read_parquet(bundle / "hourly" / f"class_hourly_{year}.parquet")
    df = df[df["pass"] == "P1"]
    return {str(k): float(v) / 1e3 for k, v in df.groupby("klass")["mw"].sum().items()}


def year_stats(m: np.ndarray, a: np.ndarray) -> dict:
    """Level / spurious / tail stats on the shared conventions."""
    ok = np.isfinite(m) & np.isfinite(a)
    m, a = m[ok], a[ok]
    # Gated count LIDLESS (ercot-225 Option A, owner-signed 2026-08-26);
    # the band/top split is the kept report decomposition.
    lo = a < MID_BAND[0]
    spur = (m >= MID_BAND[0]) & lo
    spur_band = (m >= MID_BAND[0]) & (m <= MID_BAND[1]) & lo
    hi = a > 200.0
    return {
        "c3a_hub_pct": round(float((m.mean() - a.mean()) / a.mean() * 100.0), 2),
        "nrmse": round(float(np.sqrt(np.mean((m - a) ** 2)) / a.mean()), 4),
        "spurious": int(spur.sum()),
        "spurious_band": int(spur_band.sum()),
        "spurious_top": int(((m > MID_BAND[1]) & lo).sum()),
        "tail_model": int((m > 200.0).sum()),
        "tail_caught": int((hi & (m > 200.0)).sum()),
        "tail_actual": int(hi.sum()),
        "model_mean": round(float(m.mean()), 3),
        "actual_mean": round(float(a.mean()), 3),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", type=Path, required=True)
    ap.add_argument("--probe", type=Path, required=True)
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    act = pd.read_parquet(ACTUAL_LMP)
    out: dict = {
        "_provenance": {
            "scorer": "scripts/probes/_ercot173_ab.py",
            "base": str(args.base),
            "probe": str(args.probe),
            "gates": "PRECOMMIT-ercot172 §5 inherited verbatim per PRECOMMIT-ercot173 §5",
        },
        "years": {},
        "gates": {},
        "rg_ercot167": {},
        "owner_object_2023": {},
    }

    stats = {}
    for yr in YEARS:
        a = act[act.year == yr].set_index("hour")["rt"].reindex(range(8760)).to_numpy()
        mb, mp = lw_price(args.base, yr), lw_price(args.probe, yr)
        sb, sp = year_stats(mb, a), year_stats(mp, a)
        shed_b, shed_p = shed_hours(args.base, yr), shed_hours(args.probe, yr)
        eb, ep = class_energy(args.base, yr), class_energy(args.probe, yr)
        edelta = {
            k: {
                "base_gwh": round(eb[k], 1),
                "probe_gwh": round(ep.get(k, 0.0), 1),
                "pct": round(100.0 * (ep.get(k, 0.0) - eb[k]) / max(eb[k], 1e-9), 3),
            }
            for k in sorted(eb)
            if eb[k] > 100.0  # ignore trivial classes for the report
        }
        stats[yr] = {
            "base": sb, "probe": sp,
            "shed_base": shed_b, "shed_probe": shed_p,
            "class_energy_delta": edelta,
            "model_a": mb, "model_p": mp, "actual": a,
        }
        out["years"][str(yr)] = {
            "base": sb, "probe": sp,
            "shed_hours_base": shed_b, "shed_hours_probe": shed_p,
            "class_energy_delta_pct": {k: v["pct"] for k, v in edelta.items()},
        }

    # --- G-SHED: 2024 shed count must FALL; no year's may rise.
    g_shed = (
        len(stats[2024]["shed_probe"]) < len(stats[2024]["shed_base"])
        and all(
            len(stats[y]["shed_probe"]) <= len(stats[y]["shed_base"]) for y in YEARS
        )
    )
    # --- G-SPUR: spurious count must not increase in any year.
    g_spur = all(
        stats[y]["probe"]["spurious"] <= stats[y]["base"]["spurious"] for y in YEARS
    )
    # --- G-C3c: the ledgered tail counts must not degrade (standing basis:
    #     the model's total >$200 count must not move AWAY from the actual).
    g_c3c = all(
        abs(stats[y]["probe"]["tail_model"] - C3C_LEDGER[y][1])
        <= abs(stats[y]["base"]["tail_model"] - C3C_LEDGER[y][1])
        for y in YEARS
    )
    # --- G-SPAN (G-BIT N/A, declared pre-solve): 2023+2025 class energy ≤0.5 %,
    #     shed not increased, C3c tails not degraded (the latter two above).
    span_viol = {
        str(y): {
            k: v["pct"]
            for k, v in stats[y]["class_energy_delta"].items()
            if abs(v["pct"]) > 0.5
        }
        for y in (2023, 2025)
    }
    g_span = (
        not any(span_viol.values())
        and all(
            len(stats[y]["shed_probe"]) <= len(stats[y]["shed_base"])
            for y in (2023, 2025)
        )
        and all(
            abs(stats[y]["probe"]["tail_model"] - C3C_LEDGER[y][1])
            <= abs(stats[y]["base"]["tail_model"] - C3C_LEDGER[y][1])
            for y in (2023, 2025)
        )
    )
    out["gates"] = {
        "G-BIT": "N/A (declared pre-solve: year-agnostic rule; replaced by G-SPAN)",
        "G-SPAN": {"pass": bool(g_span), "class_energy_violations_pct": span_viol},
        "G-SHED": {
            "pass": bool(g_shed),
            "shed_2024": [len(stats[2024]["shed_base"]), len(stats[2024]["shed_probe"])],
        },
        "G-SPUR": {
            "pass": bool(g_spur),
            "by_year": {
                str(y): [stats[y]["base"]["spurious"], stats[y]["probe"]["spurious"]]
                for y in YEARS
            },
        },
        "G-C3c": {
            "pass": bool(g_c3c),
            "by_year": {
                str(y): {
                    "ledger": C3C_LEDGER[y],
                    "base": stats[y]["base"]["tail_model"],
                    "probe": stats[y]["probe"]["tail_model"],
                }
                for y in YEARS
            },
        },
        "G-DOF": "structural: zero new fitted scalars (the flag is boolean; reviewed in the FINDING)",
        "G-COAL148": "scored separately post-registration (ercot149 payload machinery vs the incumbent product ceiling)",
        "G-D2": "scored from the arm bundle's legitimacy_diagnostics.json",
        "LOYO": "N/A (parameter-free rule; nothing identified on any year — per-year deltas reported instead)",
    }

    # --- RG-1 / RG-2 (the ercot-167 re-score, PRECOMMIT-ercot173 §7).
    a24 = stats[2024]["actual"]
    spikes = {}
    for day, hrs in SPIKE_2024.items():
        h = np.array(list(hrs))
        spikes[day] = {
            "base_daymean_abs_err": round(
                float(np.nanmean(np.abs(stats[2024]["model_a"][h] - a24[h]))), 2
            ),
            "probe_daymean_abs_err": round(
                float(np.nanmean(np.abs(stats[2024]["model_p"][h] - a24[h]))), 2
            ),
        }
    c3a24_delta = stats[2024]["probe"]["c3a_hub_pct"] - stats[2024]["base"]["c3a_hub_pct"]
    rg1 = (
        all(s["probe_daymean_abs_err"] < s["base_daymean_abs_err"] for s in spikes.values())
        and c3a24_delta <= 1.0
        and g_shed
    )
    m25b, m25p = stats[2025]["model_a"], stats[2025]["model_p"]
    a25 = stats[2025]["actual"]
    rg2_hour = {
        "hour": RG2_HOUR_2025,
        "base_model": round(float(m25b[RG2_HOUR_2025]), 2),
        "probe_model": round(float(m25p[RG2_HOUR_2025]), 2),
        "actual": round(float(a25[RG2_HOUR_2025]), 2),
        "spurious_in_probe": bool(
            MID_BAND[0] <= m25p[RG2_HOUR_2025] <= MID_BAND[1]
            and a25[RG2_HOUR_2025] < MID_BAND[0]
        ),
    }
    out["rg_ercot167"] = {
        "RG-1_g4_2024": {
            "clears": bool(rg1),
            "spike_days": spikes,
            "c3a_2024_delta_pp": round(float(c3a24_delta), 2),
        },
        "RG-2_g3_2025": {
            "spurious_2025": [stats[2025]["base"]["spurious"], stats[2025]["probe"]["spurious"]],
            "named_hour": rg2_hour,
        },
    }

    # --- The owner's object: C3a-2023, reported FIRST in the write-up.
    a23 = stats[2023]["actual"]
    m23b, m23p = stats[2023]["model_a"], stats[2023]["model_p"]
    missed = np.where((a23 > 200.0) & (m23b <= 200.0))[0]
    out["owner_object_2023"] = {
        "c3a_hub_base_pct": stats[2023]["base"]["c3a_hub_pct"],
        "c3a_hub_probe_pct": stats[2023]["probe"]["c3a_hub_pct"],
        "delta_pp": round(
            float(stats[2023]["probe"]["c3a_hub_pct"] - stats[2023]["base"]["c3a_hub_pct"]), 2
        ),
        "missed_set_n": int(missed.size),
        "missed_model_mean": [
            round(float(np.nanmean(m23b[missed])), 2),
            round(float(np.nanmean(m23p[missed])), 2),
        ],
        "missed_model_max": [
            round(float(np.nanmax(m23b[missed])), 2),
            round(float(np.nanmax(m23p[missed])), 2),
        ],
        "missed_flipped_gt200": int((m23p[missed] > 200.0).sum()),
    }

    for y in YEARS:
        for k in ("model_a", "model_p", "actual"):
            stats[y].pop(k, None)
    args.out.write_text(json.dumps(out, indent=1))
    print(json.dumps({k: out[k] for k in ("gates", "rg_ercot167", "owner_object_2023")}, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
