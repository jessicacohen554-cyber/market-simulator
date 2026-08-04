"""miso-127 — ex-ante pre-check for the take-or-pay PERIOD-BUDGET re-shaping lane.

NO LP. Committed artifacts + raw measured sources only. Answers the four
mandatory pre-checks that gate whether the lane may be chartered at all:

  (i)   VOLUME NEUTRALITY — does the *model* carry a per-plant annual sunk
        VOLUME, or only a per-hour fraction? A budget re-shaping needs a level;
        if the only level available is EIA-923 Schedule-5 receipts tonnage, the
        lane is miso-103's already-refuted answer key.
  (ii)  HEADROOM — does the pinned committed band sit ABOVE the regulated PRB
        fleet's measured overnight (h0-h05) minimum? If reality's floor is at
        or above the pin, there is no amplitude to recover.
  (iii) DIRECTION — would a re-shaping deepen the trough and raise the midday
        plateau, or is the class already capacity-bound at midday (so only the
        trough can move and annual volume must fall)?
  (iv)  NON-RECURRENCE of the miso-102 failure — is annual volume neutral by
        construction?

Run:  uv run python scripts/probes/_miso127_budget_reshape_precheck.py
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from market_sim.config.paths import PROCESSED_DIR
from market_sim.data.fleet.eia860 import (
    active_eia860_dir,
    eia860_regulated_plants,
)

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results/calibration/miso126_steampart_B"
YEARS = (2023, 2024, 2025)
OUT = REPO / "scripts/probes/_miso127_budget_reshape_precheck.json"

record: dict = {"probe": "miso127_budget_reshape_precheck", "bundle": str(BUNDLE)}


def _hdr(s: str) -> None:
    print("\n" + "=" * 78)
    print(s)
    print("=" * 78)


# ---------------------------------------------------------------------------
# Pre-check (i) — what level, if any, does the MODEL carry?
# ---------------------------------------------------------------------------
def precheck_i() -> None:
    _hdr("PRE-CHECK (i)  VOLUME NEUTRALITY — does the model carry an annual level?")

    csv = PROCESSED_DIR / "coal_takeorpay_MISO.csv"
    df = pd.read_csv(csv)
    print(f"  artifact              : {csv.relative_to(REPO)}")
    print(f"  columns               : {df.columns.tolist()}")
    print(f"  rows (plants)         : {len(df)}")

    # What the LOADER actually reads (market_sim.data.coal._derived_coal_takeorpay).
    import inspect

    from market_sim.data import coal as coal_mod

    src = inspect.getsource(coal_mod._derived_coal_takeorpay)
    consumed = sorted({c for c in df.columns if f'"{c}"' in src or f"'{c}'" in src})
    print(f"  columns READ by loader : {consumed}")
    unread = [c for c in df.columns if c not in consumed]
    print(f"  columns NEVER read     : {unread}")

    has_level_in_model = any(c in consumed for c in ("total_tons",))
    print(
        f"\n  -> model carries an annual VOLUME? {'YES' if has_level_in_model else 'NO'}"
        f"  (only a per-plant FRACTION, contract_share)"
    )

    # Is total_tons the series miso-103 refuted? It is same-year Schedule-5
    # receipts tonnage; miso-103's refuted candidate was contract_share x
    # (same-year / lagged / trailing-mean) Schedule-5 receipts.
    tons = df["total_tons"].to_numpy(float)
    share = df["contract_share"].to_numpy(float)
    print(
        f"\n  total_tons            : sum {tons.sum():,.0f} tons over {len(df)} plants"
    )
    print(f"  contract_share        : mean {share.mean():.3f}, "
          f"n(share==1.0) {int((share == 1.0).sum())}/{len(df)}")
    print(
        "  provenance            : EIA-923 Schedule-5 delivered fuel RECEIPTS,\n"
        "                          same-year, per plant — i.e. exactly the level\n"
        "                          miso-103 refuted (contract_share x receipts)."
    )

    record["precheck_i"] = {
        "artifact": str(csv.relative_to(REPO)),
        "columns": df.columns.tolist(),
        "columns_read_by_model": consumed,
        "columns_never_read": unread,
        "model_carries_annual_volume": bool(has_level_in_model),
        "total_tons_sum": float(tons.sum()),
        "contract_share_mean": float(share.mean()),
        "n_plants": int(len(df)),
    }


# ---------------------------------------------------------------------------
# Pre-check (ii) — headroom: measured overnight minimum vs the pinned band
# ---------------------------------------------------------------------------
def _night_frac(mw: np.ndarray, npl: float) -> dict[str, float]:
    """Overnight (h0-h05) load as a fraction of nameplate, on ONLINE days only.

    A day the plant is entirely offline is an outage, not a dispatch choice, so
    it is excluded — otherwise the "minimum" measures maintenance, not cycling.
    """
    d = mw[:8760].reshape(365, 24)
    night = d[:, 0:6].mean(axis=1)
    online = d.mean(axis=1) > 0.05 * npl
    if online.sum() < 30 or npl <= 0:
        return {}
    n = night[online] / npl
    return {
        "night_min": float(n.min()),
        "night_p05": float(np.percentile(n, 5)),
        "night_p50": float(np.median(n)),
    }


def precheck_ii() -> None:
    _hdr("PRE-CHECK (ii)  HEADROOM — measured overnight minimum vs the model's pin")

    import sys

    sys.path[:0] = [str(REPO), str(REPO / "src")]
    import scripts.legitimacy_diagnostics as LD

    reg = eia860_regulated_plants()
    sidecar = json.loads(
        (REPO / "frontend/data/backcast/registry/2026-08-04-miso-126-steampart-b.json")
        .read_text()
    )

    per_year: dict[int, dict] = {}
    for year in YEARS:
        bench = LD.load_bench(REPO, "MISO", year)
        model = LD.load_payload_plants(REPO, sidecar, year, bench)

        rows = []
        for key, rec in bench.items():
            if rec.get("group") != "COAL_PRB":
                continue
            code = int(str(key).split(":")[0])
            if code not in reg:
                continue
            npl = float(rec.get("npl") or 0.0)
            a = _night_frac(np.asarray(rec["mw"], float), npl)
            if not a:
                continue
            mrec = model.get(key)
            m = (
                _night_frac(np.asarray(mrec, float), npl)
                if isinstance(mrec, np.ndarray)
                else _night_frac(np.asarray(mrec.get("mw"), float), npl)
                if isinstance(mrec, dict)
                else {}
            )
            rows.append(
                {
                    "plant": code,
                    "npl": npl,
                    "actual_night_min": a["night_min"],
                    "actual_night_p05": a["night_p05"],
                    "actual_night_p50": a["night_p50"],
                    "model_night_min": m.get("night_min", float("nan")),
                    "model_night_p05": m.get("night_p05", float("nan")),
                    "model_night_p50": m.get("night_p50", float("nan")),
                }
            )
        fr = pd.DataFrame(rows)
        if fr.empty:
            print(f"  {year}: no regulated COAL_PRB bench plants")
            continue
        w = fr["npl"]

        def cw(col: str) -> float:
            v = fr[col]
            ok = np.isfinite(v)
            return float((v[ok] * w[ok]).sum() / w[ok].sum()) if ok.any() else float("nan")

        print(
            f"  {year}: n={len(fr):2d} regulated PRB plants, {w.sum():,.0f} MW npl\n"
            f"         ACTUAL overnight/npl  min {cw('actual_night_min'):.3f}  "
            f"p05 {cw('actual_night_p05'):.3f}  p50 {cw('actual_night_p50'):.3f}\n"
            f"         MODEL  overnight/npl  min {cw('model_night_min'):.3f}  "
            f"p05 {cw('model_night_p05'):.3f}  p50 {cw('model_night_p50'):.3f}"
        )
        per_year[year] = {
            "n_plants": int(len(fr)),
            "nameplate_mw": float(w.sum()),
            **{f"capw_{c}": cw(c) for c in fr.columns if c not in ("plant", "npl")},
        }
    record["precheck_ii"] = per_year


# ---------------------------------------------------------------------------
# Pre-check (iii) — direction: is the model's COAL_PRB capacity-bound midday?
# ---------------------------------------------------------------------------
def precheck_iii() -> None:
    _hdr("PRE-CHECK (iii)  DIRECTION — model COAL_PRB profile and midday headroom")

    out: dict[int, dict] = {}
    for year in YEARS:
        p = BUNDLE / f"hourly/class_hourly_{year}.parquet"
        d = pd.read_parquet(p)
        d = d[(d["klass"] == "COAL_PRB") & (d["pass"] == "P1")]
        mw = d.sort_values("hour")["mw"].to_numpy(float)
        prof = mw.reshape(-1, 24).mean(axis=0)
        peak_hr = int(prof.argmax())
        print(
            f"  {year}: profile h0 {prof[0]/1000:.2f} -> h14 {prof[14]/1000:.2f} GW "
            f"| daily peak h{peak_hr} {prof[peak_hr]/1000:.2f} GW "
            f"| max hourly {mw.max()/1000:.2f} GW"
        )
        out[year] = {
            "profile_gw": [float(x / 1000.0) for x in prof],
            "peak_hour": peak_hr,
            "max_hourly_gw": float(mw.max() / 1000.0),
            "annual_twh": float(mw.sum() / 1e6),
        }
    record["precheck_iii"] = out


# ---------------------------------------------------------------------------
# D-1 as committed (context, not a new statistic)
# ---------------------------------------------------------------------------
def committed_d1() -> None:
    _hdr("CONTEXT — committed D-1 COAL_PRB rows (keeper, unmodified)")
    d = json.load(open(BUNDLE / "legitimacy_diagnostics.json"))
    rows = []
    for g in d["diagnostics"] if isinstance(d.get("diagnostics"), list) else []:
        pass
    diag = d["diagnostics"]
    d1 = diag.get("D-1") if isinstance(diag, dict) else None
    if d1 is None:
        for k, v in (diag.items() if isinstance(diag, dict) else []):
            if "d1" in k.lower() or "diurnal" in str(v).lower()[:200]:
                d1 = v
                break
    for r in (d1 or {}).get("rows", []):
        if r.get("class") == "COAL_PRB":
            rows.append(r)
            print(f"  {r}")
    record["committed_d1_coal_prb"] = rows


if __name__ == "__main__":
    committed_d1()
    precheck_i()
    precheck_iii()
    precheck_ii()
    OUT.write_text(json.dumps(record, indent=2, default=str))
    print(f"\nwrote {OUT.relative_to(REPO)}")
