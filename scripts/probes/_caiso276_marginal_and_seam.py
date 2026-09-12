"""caiso-276 phase 0 part 5: WHAT is marginal in the residual-carrying hours,
and is the model SEAM-CONSTRAINED there? ZERO LP.

Part 4 measured that 2022's residual is ONE object — a marginal-offer level
bias PROPORTIONAL TO THE GAS PRICE (implied-HR bias mean +1.024 MMBtu/MWh over
the 12 months, December +1.337 ranking 3 of 12 and only +0.51 sd above the
ex-December mean, so the +$49.51 December gap is just that ordinary bias times
$37.02 gas). A gas-proportional gap lives in the ``heat_rate x multiplier``
product of whatever tranche is marginal, NOT in a non-fuel adder (a VOM /
carbon term would DIVIDE by gas and shrink in December; the bias does not).

Part 4 also measured that only 647.7 MW of 22,354 MW of gas capacity is
idle-while-in-the-money in the residual window, so the model is not materially
failing to commit in-the-money capacity — which removes the commitment-reach
hypothesis the caiso-276 charter was pointed at.

Two possibilities remain for a gas-proportional bias, and they have opposite
successors:

  M-1  MERIT DEPTH. The model clears DEEPER into its own offer stack than the
       market did, so the marginal tranche's heat rate is genuinely higher than
       the market's marginal unit's. Identify the marginal tranche (the one
       whose own assembled offer sits closest to the clearing price) and report
       its class, band, heat rate and multiplier, load-weighted.
  M-2  SEAM BINDING. The model clears deeper because its IMPORT capability is
       exhausted in those hours while the real market's was not — a measured
       corridor-envelope object under rule 14 ``[R-ACCURATE]``, with a real
       footprint. Measure import tranche utilisation against the keeper's own
       assembled ``pmax x availability`` in the same windows.

Both are descriptions of the solved state. Neither reads whether a lever moves
C3a (rule 1 ``[R-STRUCT]``).
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from scripts.lib.bundle_fleet import reconstruct_bundle_fleet  # noqa: E402

BUNDLE = REPO / "results/calibration/caiso275_B_gascoupling_2022"
ACTUAL = REPO / "data/raw/_validation-source/actual_lmp_hourly_CAISO.parquet"
OUT = REPO / "results/calibration/_caiso276_marginal_and_seam.json"
YEAR = 2022
T = 8760
CA_ZONES = ("LA_BASIN", "NP15", "SDGE", "SP15_rest", "ZP26")
_MD = (31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_CUM = np.cumsum((0,) + tuple(d * 24 for d in _MD))[:12]
TOL = 0.25


def lw(v, w) -> float:
    return float((np.asarray(v, float) * np.asarray(w, float)).sum() / np.sum(w))


def band_of(uid: str) -> str:
    return str(uid).rsplit("_", 1)[-1]


def main() -> None:
    out: dict = {"session": "caiso-276", "year": YEAR, "phase": "0e"}
    sysdf = pd.read_parquet(BUNDLE / f"hourly/system_{YEAR}.parquet")
    sysdf = sysdf[sysdf["pass"] == "P1"]
    pr = sysdf.pivot(index="hour", columns="zone", values="price")
    dm = sysdf.pivot(index="hour", columns="zone", values="demand")
    zones = [z for z in CA_ZONES if z in pr.columns]
    P = pr[zones].to_numpy(float).T
    D = dm[zones].to_numpy(float).T
    lam = (P * D).sum(axis=0) / D.sum(axis=0)
    w = D.sum(axis=0)

    print("rebuilding the keeper's own 2022 offer surface (fleet_only)...")
    state, meta = reconstruct_bundle_fleet(
        BUNDLE, YEAR, required_flags=(), required_sequences=()
    )
    fa, fleet = state["fleet_arrays"], state["fleet"]
    mc = np.asarray(state["mc_base"], float)
    cap = np.asarray(fa.pmax, float)[:, None] * np.asarray(fa.availability, float)
    klass = np.array([str(getattr(g, "plant_group", "") or "") for g in fleet])
    fuel = np.array([str(getattr(g, "fuel_type", "") or "") for g in fleet])
    uids = list(fa.unit_ids)
    band = np.array([band_of(u) for u in uids])
    hrv = np.asarray(getattr(fa, "heat_rate", np.zeros(len(fleet))), float)
    out["keeper_git_sha"] = meta.get("git_sha")

    dd = pd.read_parquet(
        BUNDLE / f"dispatch/{YEAR}_P1.parquet", columns=["unit_id", "hour", "mw"]
    )
    dmat = (
        dd.pivot_table(index="unit_id", columns="hour", values="mw", aggfunc="sum")
        .reindex(index=uids, columns=range(T))
        .fillna(0.0)
        .to_numpy(float)
    )

    midx = np.clip(np.searchsorted(_CUM, np.arange(T), side="right") - 1, 0, 11)
    hod = np.arange(T) % 24
    windows = {
        "shoulder_hod_6_9_19_22_exDec": (
            np.isin(hod, [6, 7, 8, 9, 19, 20, 21, 22]) & (midx != 11)
        ),
        "belly_core_hod_10_16_exDec": np.isin(hod, range(10, 17)) & (midx != 11),
        "december_all": midx == 11,
        "all_8760": np.ones(T, bool),
    }

    # ---- M-1  marginal tranche identification ----
    # MARGINAL = partially loaded (strictly between 0 and its own bound) and
    # its offer within TOL of the clearing price. Load-weighted census over
    # each window; where nothing qualifies the hour is reported as "no
    # partially-loaded offer at lambda" (caiso-272's "lambda in a gap").
    live = cap > 1.0
    part = (
        live
        & (dmat > 0.01 * np.maximum(cap, 1e-9))
        & (dmat < 0.99 * np.maximum(cap, 1e-9))
    )
    m1 = {}
    for name, mask in windows.items():
        hrs = np.where(mask)[0]
        cnt: Counter = Counter()
        hr_num = hr_den = 0.0
        gapw = matchw = 0.0
        for j in hrs:
            ww = float(w[j])
            at = part[:, j] & (np.abs(mc[:, j] - lam[j]) <= TOL)
            if not at.any():
                gapw += ww
                continue
            matchw += ww
            # weight the census by each qualifying row's own partial MW
            mws = dmat[at, j]
            tot = float(mws.sum()) or 1.0
            for i, m_ in zip(np.where(at)[0], mws):
                key = f"{klass[i] or fuel[i]}:{band[i]}"
                cnt[key] += ww * float(m_) / tot
                if hrv[i] > 0:
                    hr_num += ww * float(m_) / tot * hrv[i]
                    hr_den += ww * float(m_) / tot
        tw = gapw + matchw
        m1[name] = {
            "hours": int(hrs.size),
            "matched_load_share": round(matchw / tw, 4) if tw else None,
            "lambda_in_gap_share": round(gapw / tw, 4) if tw else None,
            "marginal_hr_lw": round(hr_num / hr_den, 3) if hr_den else None,
            "top_marginal": [(k, round(v / matchw, 4)) for k, v in cnt.most_common(8)]
            if matchw
            else [],
        }
    out["M1_marginal_census"] = m1
    print("\n=== M-1  marginal tranche census (load-weighted) ===")
    for name, r in m1.items():
        print(f"\n  {name}   hours={r['hours']}")
        print(
            f"    matched {r['matched_load_share']}   lambda-in-a-gap"
            f" {r['lambda_in_gap_share']}   marginal HR (lw)"
            f" {r['marginal_hr_lw']}"
        )
        for k, v in r["top_marginal"]:
            print(f"      {k:<28s} {v:>7.4f}")

    # ---- M-2  seam binding ----
    isimp = (klass == "") & np.isin(
        np.array([str(getattr(g, "zone", "") or "") for g in fleet]),
        ["WECC_PNW", "WECC_DSW", "WECC_import"],
    )
    if not isimp.any():
        isimp = np.array(
            [str(getattr(g, "fuel_type", "") or "") == "import" for g in fleet]
        )
    out["import_rows"] = int(isimp.sum())
    m2 = {}
    for name, mask in windows.items():
        hrs = np.where(mask)[0]
        c = cap[np.ix_(isimp, hrs)]
        d = dmat[np.ix_(isimp, hrs)]
        util = d.sum(axis=0) / np.maximum(c.sum(axis=0), 1e-9)
        m2[name] = {
            "hours": int(hrs.size),
            "import_cap_mw": round(float(c.sum(axis=0).mean()), 0),
            "import_disp_mw": round(float(d.sum(axis=0).mean()), 0),
            "import_headroom_mw": round(
                float((c.sum(axis=0) - d.sum(axis=0)).mean()), 0
            ),
            "util_lw": round(lw(util, w[hrs]), 4),
            "hours_util_ge_99pct": int((util >= 0.99).sum()),
            "hours_util_ge_95pct": int((util >= 0.95).sum()),
            "frac_hours_util_ge_99pct": round(float((util >= 0.99).mean()), 4),
        }
    out["M2_seam_binding"] = m2
    print("\n=== M-2  import seam utilisation (keeper's own assembled cap) ===")
    print(
        "  window                              hours   impCap  impDisp"
        " headroom    util  h>=99%  frac>=99%"
    )
    for name, r in m2.items():
        print(
            f"  {name:<34s}{r['hours']:>6d}{r['import_cap_mw']:>9.0f}"
            f"{r['import_disp_mw']:>9.0f}{r['import_headroom_mw']:>9.0f}"
            f"{r['util_lw']:>8.4f}{r['hours_util_ge_99pct']:>8d}"
            f"{r['frac_hours_util_ge_99pct']:>11.4f}"
        )

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
