"""nyiso-245 — DIAGNOSTIC: is the 2022 winter object a LEVEL object or a SHAPE object?

ZERO LP (rule 32 ``[R-SHARD]`` (a)). **Descriptive. Not a gate, and nothing is
selected on it.** The PRECOMMIT's six gates are already decided before this runs;
this measurement cannot and does not flip any of them (rule 1 ``[R-STRUCT]``). It
exists because the refusal is only useful to a successor if it says WHERE the
object is, and that is answerable from the same corpus at no extra cost.

**The question.** nyiso-245's G3a refused a within-unit SHAPE transfer: NYISO's
measured Δ ladder is non-monotone in 12 of 12 populated cells and its largest
value anywhere is $7.28/MWh. But nyiso-244 §6.1 measured the real market
withdrawing **6,202.5 MW** from below $200 when the event arrives. If the
within-unit *shape* barely moves, that withdrawal has to come from somewhere
else. Two candidates, and they are distinguishable:

* **LEVEL** — the same unit's whole curve shifts up in the event hours. A
  shape-only form cancels this **by construction**, so it would be blind to the
  object by design rather than by accident.
* **COMPOSITION** — different units offer in the two windows. Neither a shape nor
  a level transfer reaches this; it is an availability/commitment object, and
  nyiso-242/-243 already refuted the availability route on two instruments.

**The estimator, and why it is cohort-free AND composition-free.** Every statistic
is a **within-unit difference between the two windows**, taken only over masked
gens present in BOTH, then aggregated as a capacity-weighted median. A unit that
appears in only one window contributes nothing, so the ~9.4 GW fleet-scope gap and
any change in who is offering both cancel exactly — the same discipline nyiso-243
Leg 2 and nyiso-244 §6.1 imposed on themselves.

Two legs:

* **Leg A — the market.** Per masked gen: the bottom of its own curve
  (``price_1``), the top of its own curve (its highest priced block), and the rise
  between them, each a median over the window's hours; then the within-unit
  difference missed − ordinary.
* **Leg B — the model, on the same two windows.** The same three quantities on the
  keeper's own assembled offer array, per model plant.

**Leg C — reported for the successor only**: the Δ ladder rebuilt with
single-block price-takers excluded. The PRECOMMIT fixed in advance that they are
KEPT (the family's own population rules) and that excluding them "is a DIFFERENT
mechanism and needs its own PRECOMMIT". This leg is therefore **evidence for a
successor's precommit, never a rescue of this one** — the G3a verdict stands on
the artifact that was actually derived.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/nyiso245_level_vs_shape.py
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
BUNDLE = REPO / "results" / "calibration" / "nyiso241_ctcommitted_span"
CACHE = REPO / "results" / "calibration" / "_nyiso245_cache"
OUT = REPO / "results" / "calibration" / "_nyiso245_level_vs_shape.json"

HOURS = 8760
_MW_COLS = [f"Dispatch MW{i}" for i in range(1, 13)]
_PX_COLS = [f"Dispatch $/MW{i}" for i in range(1, 13)]


def _windows(year: int) -> dict[str, np.ndarray]:
    """The two winter windows the object is defined on (nyiso-242's own mask)."""
    from scripts.probes.nyiso242_tail_reachability import missed_mask

    missed, month = missed_mask(year)
    idx = np.arange(len(missed))
    win = {
        "missed": idx[missed & np.isin(month, (1, 2, 12))],
        "ordinary": idx[~missed & np.isin(month, (1, 2, 12))],
    }
    return {k: v[v < HOURS] for k, v in win.items()}


def leg_a_market(year: int, win: dict[str, np.ndarray]) -> dict:
    """Within-unit curve bottom / top / rise, missed vs ordinary, from P-27 DAM."""
    from scripts.data.derive_nyiso_offer_surface import read_month

    keep = {k: set(int(h) for h in v) for k, v in win.items()}
    acc: list[pd.DataFrame] = []
    for month in (1, 2, 12):
        raw = read_month(year, month, "DAM")
        if raw is None:
            continue
        from scripts.data.derive_nyiso_offer_surface import _std_hour

        ts = pd.to_datetime(
            raw["Date Time"].astype(str).str.strip(), format="%d%b%Y:%H:%M:%S"
        )
        hour = _std_hour(pd.DatetimeIndex(ts).tz_localize("UTC"), year)
        px = raw[_PX_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        mw = raw[_MW_COLS].apply(pd.to_numeric, errors="coerce").to_numpy(float)
        uol = pd.to_numeric(raw["Upper Oper Limit"], errors="coerce").to_numpy(float)
        nblocks = np.isfinite(px).sum(axis=1)
        ok = np.isfinite(px).any(axis=1) & (uol > 0) & (hour >= 0)
        lab = np.where(
            [h in keep["missed"] for h in hour],
            "missed",
            np.where([h in keep["ordinary"] for h in hour], "ordinary", ""),
        )
        ok &= lab != ""
        if not ok.any():
            continue
        acc.append(
            pd.DataFrame(
                {
                    "gen": raw["Masked Gen ID"].to_numpy()[ok],
                    "win": lab[ok],
                    "uol": uol[ok],
                    "bottom": px[ok, 0],
                    "top": np.nanmax(np.where(np.isfinite(px[ok]), px[ok], -np.inf), axis=1),
                    "nblocks": nblocks[ok],
                }
            )
        )
        del px, mw
    df = pd.concat(acc, ignore_index=True)
    df = df[np.isfinite(df["top"])]
    df["rise"] = df["top"] - df["bottom"]

    # G3c's contamination, answered fairly rather than asserted: a single-block
    # price taker's RISE is 0 in BOTH windows, so its within-unit rise CHANGE is
    # identically 0 and it drags the pooled median toward 0 by construction. A
    # unit is called multi-block if it submitted >1 priced block in the MEDIAN
    # hour of either window. Splitting on it is the only way to tell "the market
    # does not steepen" from "price takers hid the steepening".
    nb = df.groupby("gen")["nblocks"].median()
    multi = set(nb[nb > 1].index)

    per = df.groupby(["gen", "win"])[["bottom", "top", "rise", "uol"]].median().unstack("win")
    both = per["bottom"]["missed"].notna() & per["bottom"]["ordinary"].notna()
    per = per[both]
    w = per["uol"]["missed"].to_numpy(float)
    out = {"n_gens_in_both_windows": int(both.sum()), "capacity_mw": round(float(w.sum()), 1)}
    for q in ("bottom", "top", "rise"):
        d = (per[q]["missed"] - per[q]["ordinary"]).to_numpy(float)
        out[f"within_unit_delta_{q}_usd_per_mwh"] = {
            "cap_weighted_median": round(_wmed(d, w), 3),
            "p25": round(float(np.nanpercentile(d, 25)), 3),
            "p75": round(float(np.nanpercentile(d, 75)), 3),
        }
        out[f"level_{q}_usd_per_mwh"] = {
            "ordinary_cap_weighted_median": round(
                _wmed(per[q]["ordinary"].to_numpy(float), w), 3
            ),
            "missed_cap_weighted_median": round(
                _wmed(per[q]["missed"].to_numpy(float), w), 3
            ),
        }

    sub = np.array([g in multi for g in per.index], dtype=bool)
    out["multi_block_only"] = {
        "n_gens": int(sub.sum()),
        "capacity_mw": round(float(w[sub].sum()), 1),
        **{
            f"within_unit_delta_{q}_usd_per_mwh": {
                "cap_weighted_median": round(
                    _wmed((per[q]["missed"] - per[q]["ordinary"]).to_numpy(float)[sub], w[sub]), 3
                ),
                "p75": round(
                    float(
                        np.nanpercentile(
                            (per[q]["missed"] - per[q]["ordinary"]).to_numpy(float)[sub], 75
                        )
                    ),
                    3,
                ),
                "p90": round(
                    float(
                        np.nanpercentile(
                            (per[q]["missed"] - per[q]["ordinary"]).to_numpy(float)[sub], 90
                        )
                    ),
                    3,
                ),
            }
            for q in ("bottom", "top", "rise")
        },
    }
    return out


def leg_b_model(year: int, win: dict[str, np.ndarray]) -> dict:
    """The same three quantities on the keeper's own assembled offer array."""
    d = np.load(CACHE / f"{year}.npz", allow_pickle=True)
    uid = np.array([str(u) for u in d["unit_ids"]])
    pmax = d["pmax"].astype(float)
    mc = d["mc_base"].astype(float)
    pc = np.array([str(x) for x in d["gen_plant_code"]])
    pg = np.array([str(x) for x in d["plant_group"]])

    internal = np.ones(len(uid), dtype=bool)
    for pre in ("NYISO_external", "NYISO_DR"):
        internal &= ~np.char.startswith(uid, pre)

    groups: dict[tuple[str, str], list[int]] = {}
    for i in np.nonzero(internal)[0]:
        if not pc[i] or pc[i] == "None":
            continue
        groups.setdefault((pc[i], pg[i]), []).append(int(i))

    rec = {"bottom": [], "top": [], "rise": [], "w": []}
    for idx in groups.values():
        rows = np.asarray(idx, dtype=int)
        vals = {}
        for lab, sel in win.items():
            block = mc[np.ix_(rows, sel)]
            vals[lab] = (
                float(np.median(block.min(axis=0))),
                float(np.median(block.max(axis=0))),
            )
        rec["bottom"].append(vals["missed"][0] - vals["ordinary"][0])
        rec["top"].append(vals["missed"][1] - vals["ordinary"][1])
        rec["rise"].append(
            (vals["missed"][1] - vals["missed"][0])
            - (vals["ordinary"][1] - vals["ordinary"][0])
        )
        rec["w"].append(float(pmax[rows].sum()))

    w = np.asarray(rec["w"], dtype=float)
    return {
        "n_plants": len(w),
        "capacity_mw": round(float(w.sum()), 1),
        **{
            f"within_unit_delta_{q}_usd_per_mwh": {
                "cap_weighted_median": round(_wmed(np.asarray(rec[q], float), w), 3),
                "p25": round(float(np.nanpercentile(rec[q], 25)), 3),
                "p75": round(float(np.nanpercentile(rec[q], 75)), 3),
            }
            for q in ("bottom", "top", "rise")
        },
    }


def _wmed(v: np.ndarray, w: np.ndarray) -> float:
    """Weighted median of ``v`` with weights ``w``, NaNs dropped."""
    ok = np.isfinite(v) & np.isfinite(w) & (w > 0)
    if not ok.any():
        return float("nan")
    v, w = v[ok], w[ok]
    order = np.argsort(v)
    v, w = v[order], w[order]
    cum = np.cumsum(w)
    return float(v[int(np.searchsorted(cum, 0.5 * cum[-1], side="left"))])


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--year", type=int, default=2022)
    ap.add_argument("--out", type=Path, default=OUT)
    args = ap.parse_args()

    win = _windows(args.year)
    res = {
        "year": args.year,
        "note": (
            "DESCRIPTIVE. Not a gate; the PRECOMMIT's six gates were decided "
            "before this ran and nothing here flips one (rule 1 [R-STRUCT]). "
            "Every statistic is a WITHIN-UNIT difference over gens present in "
            "BOTH windows, so fleet scope and composition cancel exactly."
        ),
        "hours": {k: int(len(v)) for k, v in win.items()},
        "leg_a_market_p27": leg_a_market(args.year, win),
        "leg_b_model_keeper": leg_b_model(args.year, win),
    }

    print(f"=== windows: missed {res['hours']['missed']} h, ordinary {res['hours']['ordinary']} h")
    for leg, lab in (("leg_a_market_p27", "MARKET (P-27)"), ("leg_b_model_keeper", "MODEL (keeper)")):
        r = res[leg]
        print(f"\n--- {lab}: within-unit change, missed - ordinary ($/MWh, cap-weighted median)")
        for q in ("bottom", "top", "rise"):
            k = f"within_unit_delta_{q}_usd_per_mwh"
            print(f"    {q:<7s} {r[k]['cap_weighted_median']:+10.2f}   "
                  f"[p25 {r[k]['p25']:+.2f}, p75 {r[k]['p75']:+.2f}]")
    a = res["leg_a_market_p27"]
    b = res["leg_b_model_keeper"]
    m = res["leg_a_market_p27"]["multi_block_only"]
    print(f"\n--- MARKET, MULTI-BLOCK UNITS ONLY ({m['n_gens']} gens, {m['capacity_mw']:.0f} MW)")
    for q in ("bottom", "top", "rise"):
        k = m[f"within_unit_delta_{q}_usd_per_mwh"]
        print(f"    {q:<7s} {k['cap_weighted_median']:+10.2f}   [p75 {k['p75']:+.2f}, p90 {k['p90']:+.2f}]")
    print("\n=== THE DECOMPOSITION")
    print(f"    market moves its curve BOTTOM by {a['within_unit_delta_bottom_usd_per_mwh']['cap_weighted_median']:+.2f} "
          f"and its within-unit RISE by {a['within_unit_delta_rise_usd_per_mwh']['cap_weighted_median']:+.2f}")
    print(f"    model  moves its curve BOTTOM by {b['within_unit_delta_bottom_usd_per_mwh']['cap_weighted_median']:+.2f} "
          f"and its within-unit RISE by {b['within_unit_delta_rise_usd_per_mwh']['cap_weighted_median']:+.2f}")

    args.out.write_text(json.dumps(res, indent=2) + "\n")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":  # pragma: no cover - CLI
    main()
