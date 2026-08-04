"""caiso-164 §0 — decompose the CAISO north-south basis miss, NO LP.

Reads committed artifacts only: the caiso-163 keeper's hourly ``system_<y>``
sidecars (model P1 zonal prices) and ``data/raw/lmp-data/CAISO/
CAISO_dam_hourly_<y>.csv`` (measured DAM hub LMPs, already decomposed by CAISO
into MCE / MCC / MCL).  Nothing here is applied to a solve — it is a
measurement, reported against, never fed back (rules 1 / 13).

The question caiso-163 §5 left open: the real Path 15 separates NP15 from ZP26
in ~100 % of hours at +5.7 to +8.6 $/MWh and the keeper manages 2.7-4.7 % of
hours at -0.08 to -0.11.  Is that a CONGESTION-FREQUENCY miss (right sign, too
few hours) or a MAGNITUDE miss (right hours, too small a spread)?  And in the
hours the real basis is widest, which way is Path 15 actually flowing?

Method notes that matter for reading the output:

* **CAISO publishes the answer to the congestion-vs-loss question directly.**
  A CAISO LMP is ``MCE + MCC + MCL`` (energy + congestion + loss).  MCE is the
  single system reference price, identical at every node, so any hub-to-hub
  basis is exactly ``dMCC + dMCL``.  The model's LP is **lossless**, so the
  only component it can possibly reproduce is dMCC.  Comparing the model's
  basis against the *total* measured basis therefore charges the model for a
  component it has no representation of; this probe scores it against dMCC and
  reports dMCL separately.
* **Binding direction is exact from prices here.**  The model's CAISO N-S
  corridor is radial (NP15 - ZP26 - SP15_rest, no parallel path), so on a
  lossless LP a nonzero price difference across a link happens if and only if
  that link is at a bound, and the sign of the difference gives the binding
  direction: power flows toward the higher price, so ``NP15 > ZP26`` means the
  binding flow is S->N and ``NP15 < ZP26`` means N->S.  The same reading
  applies to the measured dMCC (the congestion component is by construction the
  shadow-price projection).
* Hour alignment between the model's plain 8760 clock and the GMT-stamped DAM
  file is **measured, not assumed**: the lag maximising the correlation of the
  model's NP15 price against the measured NP15 price is found by search and
  printed, so the diurnal cut can be read honestly.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
DAM = REPO / "data/raw/lmp-data/CAISO"
KEEPER = REPO / "results/calibration/caiso163_asym_path_ratings"
YEARS = (2023, 2024, 2025)

# Measured DAM hub -> model zone.  SP15_rest is the caiso-163 convention (the
# SP15 gateway zone); the load-weighted SP15 composite over the three southern
# model zones is reported alongside it because SP15_rest carries only ~16 TWh
# of the ~112 TWh southern load and is not on its own a fair stand-in.
HUBS = {
    "NP15": "TH_NP15_GEN-APND",
    "ZP26": "TH_ZP26_GEN-APND",
    "SP15": "TH_SP15_GEN-APND",
}
SP15_COMPOSITE = ("SP15_rest", "LA_BASIN", "SDGE")
# A price difference below this is numerical noise, not a separated zone.
TOL = 0.01


def measured(year: int) -> pd.DataFrame:
    """Return the hourly measured hub frame for ``year``, GMT-indexed.

    Columns are ``<hub>_<component>`` for component in LMP / MCE / MCC / MCL,
    restricted to hours where all three hubs printed.
    """
    df = pd.read_csv(DAM / f"CAISO_dam_hourly_{year}.csv")
    df = df[df["node"].isin(HUBS.values())]
    wide = df.pivot_table(
        index="interval_start_gmt",
        columns="node",
        values=["LMP", "MCE", "MCC", "MCL"],
        aggfunc="mean",
    )
    inv = {v: k for k, v in HUBS.items()}
    wide.columns = [f"{inv[node]}_{comp}" for comp, node in wide.columns]
    wide = wide.dropna()
    wide.index = pd.to_datetime(wide.index)
    return wide.sort_index()


def model_prices(year: int, bundle: Path = KEEPER) -> pd.DataFrame:
    """Return the model's P1 hour x zone price frame for ``year``."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="price")


def model_load(year: int, bundle: Path = KEEPER) -> pd.DataFrame:
    """Return the model's P1 hour x zone demand frame for ``year``."""
    d = pd.read_parquet(bundle / f"hourly/system_{year}.parquet")
    d = d[d["pass"] == "P1"]
    return d.pivot_table(index="hour", columns="zone", values="demand")


def best_lag(model_np15: np.ndarray, meas_np15: np.ndarray) -> tuple[int, float]:
    """Return the (lag, correlation) that best aligns model hours to GMT hours.

    ``lag`` is the number of hours the measured series is shifted back to line
    up with model hour 0, searched over the full plausible UTC-offset range.
    """
    n = min(len(model_np15), len(meas_np15))
    best = (0, -2.0)
    for lag in range(-12, 13):
        a = model_np15[max(0, lag) : n + min(0, lag)]
        b = meas_np15[max(0, -lag) : n + min(0, -lag)]
        m = min(len(a), len(b))
        if m < 1000:
            continue
        r = float(np.corrcoef(a[:m], b[:m])[0, 1])
        if r > best[1]:
            best = (lag, r)
    return best


def _split(diff: np.ndarray) -> dict:
    """Frequency / conditional-magnitude decomposition of a basis series.

    ``mean = separated_share * conditional_mean``, so the two factors are
    exactly the two ways a mean basis can be missed.
    """
    sep = np.abs(diff) > TOL
    n = len(diff)
    pos = sep & (diff > 0)
    neg = sep & (diff < 0)
    return {
        "hours": int(n),
        "sep_hours": int(sep.sum()),
        "sep_pct": round(100.0 * float(sep.mean()), 3),
        "mean": round(float(diff.mean()), 4),
        "cond_mean_when_sep": round(
            float(diff[sep].mean()) if sep.any() else 0.0, 4
        ),
        "cond_absmean_when_sep": round(
            float(np.abs(diff[sep]).mean()) if sep.any() else 0.0, 4
        ),
        "pos_hours": int(pos.sum()),
        "neg_hours": int(neg.sum()),
        "pos_pct_of_sep": round(
            100.0 * float(pos.sum()) / max(1, int(sep.sum())), 2
        ),
        "p95_abs": round(float(np.percentile(np.abs(diff), 95)), 4),
        "max_abs": round(float(np.abs(diff).max()), 4),
    }


def main() -> int:
    """Print the caiso-164 §0 decomposition; always returns 0 (diagnostic)."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--json", default=None, help="also write the report here")
    args = ap.parse_args()

    report: dict = {"measured": {}, "model": {}, "split": {}, "align": {}}

    print("=" * 79)
    print("A. MEASURED CAISO N-S BASIS, DECOMPOSED (CAISO's own LMP components)")
    print("   basis = dMCE + dMCC + dMCL ; dMCE == 0 (single reference bus)")
    print("=" * 79)
    print(
        f"{'yr':>5} {'pair':>10} {'mean tot':>9} {'dMCE':>8} {'dMCC':>9} "
        f"{'dMCL':>8} {'cong%':>7} {'loss%':>7}"
    )
    meas = {}
    for year in YEARS:
        m = measured(year)
        meas[year] = m
        for a, b in (("NP15", "ZP26"), ("NP15", "SP15")):
            tot = (m[f"{a}_LMP"] - m[f"{b}_LMP"]).to_numpy()
            dmce = (m[f"{a}_MCE"] - m[f"{b}_MCE"]).to_numpy()
            dmcc = (m[f"{a}_MCC"] - m[f"{b}_MCC"]).to_numpy()
            dmcl = (m[f"{a}_MCL"] - m[f"{b}_MCL"]).to_numpy()
            share = lambda x: 100.0 * float(x.mean()) / float(tot.mean())  # noqa: E731
            print(
                f"{year:>5} {a + '-' + b:>10} {tot.mean():>9.3f} "
                f"{dmce.mean():>8.4f} {dmcc.mean():>9.3f} {dmcl.mean():>8.3f} "
                f"{share(dmcc):>6.1f}% {share(dmcl):>6.1f}%"
            )
            report["measured"][f"{year}_{a}_{b}"] = {
                "mean_total": round(float(tot.mean()), 4),
                "mean_dMCE": round(float(dmce.mean()), 6),
                "mean_dMCC": round(float(dmcc.mean()), 4),
                "mean_dMCL": round(float(dmcl.mean()), 4),
                "congestion_share_pct": round(share(dmcc), 2),
                "loss_share_pct": round(share(dmcl), 2),
                "total": _split(tot),
                "dMCC": _split(dmcc),
                "dMCL": _split(dmcl),
            }

    print()
    print("=" * 79)
    print("B. MEASURED CONGESTION ONLY (dMCC) — frequency, magnitude, DIRECTION")
    print("   sign convention: dMCC>0 => NP15 dearer => binding flow is S->N")
    print("=" * 79)
    print(
        f"{'yr':>5} {'pair':>10} {'sep h':>7} {'sep %':>7} {'mean':>8} "
        f"{'|mean| when sep':>16} {'S->N h':>8} {'N->S h':>8} {'S->N %':>8}"
    )
    for year in YEARS:
        for a, b in (("NP15", "ZP26"), ("NP15", "SP15")):
            s = report["measured"][f"{year}_{a}_{b}"]["dMCC"]
            print(
                f"{year:>5} {a + '-' + b:>10} {s['sep_hours']:>7} "
                f"{s['sep_pct']:>6.2f}% {s['mean']:>8.3f} "
                f"{s['cond_absmean_when_sep']:>16.3f} {s['pos_hours']:>8} "
                f"{s['neg_hours']:>8} {s['pos_pct_of_sep']:>7.1f}%"
            )

    print()
    print("=" * 79)
    print("C. HOUR ALIGNMENT — measured, not assumed")
    print("=" * 79)
    lags = {}
    for year in YEARS:
        mp = model_prices(year)
        lag, r = best_lag(
            mp["NP15"].to_numpy(), meas[year]["NP15_LMP"].to_numpy()
        )
        lags[year] = lag
        report["align"][str(year)] = {"lag_hours": lag, "corr": round(r, 4)}
        print(f"{year}: best lag {lag:+d} h, corr(model NP15, measured NP15) = {r:.4f}")

    print()
    print("=" * 79)
    print("D. MODEL BASIS (keeper 2026-08-03-caiso163-asym-path-ratings, P1)")
    print("   lossless LP + radial N-S corridor => price gap <=> link at bound")
    print("=" * 79)
    print(
        f"{'yr':>5} {'pair':>16} {'sep h':>7} {'sep %':>7} {'mean':>8} "
        f"{'|mean| when sep':>16} {'S->N h':>8} {'N->S h':>8} {'S->N %':>8}"
    )
    for year in YEARS:
        mp = model_prices(year)
        ml = model_load(year)
        sp15_w = sum(mp[z] * ml[z] for z in SP15_COMPOSITE) / sum(
            ml[z] for z in SP15_COMPOSITE
        )
        pairs = {
            "NP15-ZP26": (mp["NP15"] - mp["ZP26"]).to_numpy(),
            "NP15-SP15_rest": (mp["NP15"] - mp["SP15_rest"]).to_numpy(),
            "NP15-SP15(lw)": (mp["NP15"] - sp15_w).to_numpy(),
        }
        for label, diff in pairs.items():
            s = _split(diff)
            report["model"][f"{year}_{label}"] = s
            print(
                f"{year:>5} {label:>16} {s['sep_hours']:>7} "
                f"{s['sep_pct']:>6.2f}% {s['mean']:>8.3f} "
                f"{s['cond_absmean_when_sep']:>16.3f} {s['pos_hours']:>8} "
                f"{s['neg_hours']:>8} {s['pos_pct_of_sep']:>7.1f}%"
            )

    print()
    print("=" * 79)
    print("E. THE SPLIT — frequency miss vs magnitude miss, on dMCC (like-for-like)")
    print("   mean = sep_share x conditional_mean, so the two ratios multiply")
    print("=" * 79)
    print(
        f"{'yr':>5} {'meas sep%':>10} {'mdl sep%':>9} {'FREQ x':>8} "
        f"{'meas |cond|':>12} {'mdl |cond|':>11} {'MAG x':>7} {'net x':>7}"
    )
    for year in YEARS:
        mm = report["measured"][f"{year}_NP15_ZP26"]["dMCC"]
        md = report["model"][f"{year}_NP15-ZP26"]
        freq = md["sep_pct"] / mm["sep_pct"] if mm["sep_pct"] else float("nan")
        mag = (
            md["cond_absmean_when_sep"] / mm["cond_absmean_when_sep"]
            if mm["cond_absmean_when_sep"]
            else float("nan")
        )
        report["split"][str(year)] = {
            "measured_sep_pct": mm["sep_pct"],
            "model_sep_pct": md["sep_pct"],
            "freq_ratio": round(freq, 4),
            "measured_cond_absmean": mm["cond_absmean_when_sep"],
            "model_cond_absmean": md["cond_absmean_when_sep"],
            "magnitude_ratio": round(mag, 4),
            "net_ratio": round(freq * mag, 4),
        }
        print(
            f"{year:>5} {mm['sep_pct']:>9.2f}% {md['sep_pct']:>8.2f}% "
            f"{freq:>8.3f} {mm['cond_absmean_when_sep']:>12.3f} "
            f"{md['cond_absmean_when_sep']:>11.3f} {mag:>7.3f} "
            f"{freq * mag:>7.4f}"
        )

    print()
    print("=" * 79)
    print("F. THE WIDEST HOURS — where the real basis is largest, what does the")
    print("   model do THERE?  (top decile of measured |NP15-ZP26 dMCC|)")
    print("=" * 79)
    for year in YEARS:
        m = meas[year]
        dmcc = (m["NP15_MCC"] - m["ZP26_MCC"]).to_numpy()
        thresh = float(np.percentile(np.abs(dmcc), 90))
        top = np.abs(dmcc) >= thresh
        mp = model_prices(year)
        mdiff = (mp["NP15"] - mp["ZP26"]).to_numpy()
        # Align the model series onto the measured GMT index by the measured lag.
        lag = lags[year]
        n = min(len(mdiff), len(dmcc))
        idx = np.arange(n)
        midx = np.clip(idx + lag, 0, len(mdiff) - 1)
        maligned = mdiff[midx]
        topn = top[:n]
        hod = pd.DatetimeIndex(m.index[:n]).hour.to_numpy()
        sn = dmcc[:n][topn] > 0
        both = topn & (np.abs(maligned) > TOL)
        agree = both & (np.sign(maligned) == np.sign(dmcc[:n]))
        row = {
            "top_decile_threshold": round(thresh, 3),
            "top_decile_hours": int(topn.sum()),
            "measured_mean_in_top": round(float(dmcc[:n][topn].mean()), 3),
            "measured_SN_share_pct": round(100.0 * float(sn.mean()), 2),
            "model_separated_in_top_hours": int(both.sum()),
            "model_sep_rate_in_top_pct": round(
                100.0 * float(both.sum()) / max(1, int(topn.sum())), 2
            ),
            "model_mean_in_top": round(float(maligned[topn].mean()), 4),
            "sign_agreement_hours": int(agree.sum()),
            "modal_gmt_hour_of_top": int(np.bincount(hod[topn]).argmax()),
        }
        report.setdefault("widest", {})[str(year)] = row
        print(
            f"{year}: top-decile |dMCC| >= {thresh:.2f}, {int(topn.sum())} h, "
            f"measured mean {dmcc[:n][topn].mean():+.2f} $/MWh, "
            f"{row['measured_SN_share_pct']:.1f}% of them S->N"
        )
        print(
            f"      model separated in {int(both.sum())} of those "
            f"({row['model_sep_rate_in_top_pct']:.2f} %), model mean there "
            f"{maligned[topn].mean():+.4f}, sign agrees in "
            f"{int(agree.sum())} h"
        )

    print()
    print("  lag robustness — model separation in the same top-decile hours,")
    print("  swept over the whole plausible alignment range:")
    for year in YEARS:
        m = meas[year]
        dmcc = (m["NP15_MCC"] - m["ZP26_MCC"]).to_numpy()
        thresh = float(np.percentile(np.abs(dmcc), 90))
        top = np.abs(dmcc) >= thresh
        mdiff = (model_prices(year)["NP15"] - model_prices(year)["ZP26"]).to_numpy()
        n = min(len(mdiff), len(dmcc))
        counts = []
        for lg in range(-3, 4):
            midx = np.clip(np.arange(n) + lg, 0, len(mdiff) - 1)
            counts.append(int((top[:n] & (np.abs(mdiff[midx]) > TOL)).sum()))
        report.setdefault("lag_robustness", {})[str(year)] = counts
        print(
            f"  {year}: lags -3..+3 -> separated hours "
            + " ".join(str(c) for c in counts)
            + f"  (of {int(top[:n].sum())})"
        )

    print()
    print("=" * 79)
    print("G. DIURNAL SHAPE, Pacific local hour — measured NP15-ZP26 dMCC")
    print("=" * 79)
    for year in YEARS:
        m = meas[year]
        loc = pd.DatetimeIndex(m.index).tz_convert("America/Los_Angeles")
        dmcc = pd.Series((m["NP15_MCC"] - m["ZP26_MCC"]).to_numpy(), index=loc)
        by = dmcc.groupby(loc.hour).mean()
        report.setdefault("diurnal_measured_dMCC", {})[str(year)] = {
            int(h): round(float(v), 3) for h, v in by.items()
        }
        print(f"{year}: " + " ".join(f"{h:02d}:{v:+.1f}" for h, v in by.items()))

    print()
    print("=" * 79)
    print("H. WHY THE NORTH NEVER GETS DEAR — model vs measured zonal price by")
    print("   Pacific local hour.  Measured NP15 rises over ZP26 midday; does")
    print("   the model's NP15 rise at all?")
    print("=" * 79)
    for year in YEARS:
        m = meas[year]
        loc = pd.DatetimeIndex(m.index).tz_convert("America/Los_Angeles")
        mp = model_prices(year)
        # Model hour index is a plain local 8760/8784 clock from Jan 1 00:00,
        # the same origin the measured file starts on (its first stamp is local
        # midnight), so hour % 24 is the local hour without further alignment.
        mh = np.arange(len(mp)) % 24
        rows = []
        for h in range(24):
            mm = loc.hour == h
            md = mh == h
            rows.append(
                (
                    h,
                    float(m["NP15_LMP"].to_numpy()[mm].mean()),
                    float(m["ZP26_LMP"].to_numpy()[mm].mean()),
                    float(mp["NP15"].to_numpy()[md].mean()),
                    float(mp["ZP26"].to_numpy()[md].mean()),
                )
            )
        report.setdefault("diurnal_levels", {})[str(year)] = [
            {
                "hour": h,
                "meas_NP15": round(a, 2),
                "meas_ZP26": round(b, 2),
                "model_NP15": round(c, 2),
                "model_ZP26": round(d, 2),
            }
            for h, a, b, c, d in rows
        ]
        sp15m = m["SP15_LMP"].to_numpy()
        sp15d = mp["SP15_rest"].to_numpy()
        print(f"-- {year}")
        print(
            f"{'h':>3} {'meas NP15':>10} {'meas ZP26':>10} {'meas SP15':>10} "
            f"{'meas d':>8} | {'mdl NP15':>9} {'mdl ZP26':>9} {'mdl SP15':>9} "
            f"{'mdl d':>7}"
        )
        for h, a, b, c, d in rows:
            print(
                f"{h:>3} {a:>10.2f} {b:>10.2f} "
                f"{sp15m[loc.hour == h].mean():>10.2f} {a - b:>8.2f} | "
                f"{c:>9.2f} {d:>9.2f} {sp15d[mh == h].mean():>9.2f} "
                f"{c - d:>7.2f}"
            )

    print()
    print("=" * 79)
    print("J. THE SOUTHERN PRICE FLOOR — how often does each zone go cheap?")
    print("   Real CAISO's south collapses on the solar glut; the model's does")
    print("   not, and a zone that never collapses cannot decouple downward.")
    print("=" * 79)
    for year in YEARS:
        m = meas[year]
        mp = model_prices(year)
        print(f"-- {year}")
        print(
            f"{'series':>18} {'min':>9} {'p01':>8} {'p05':>8} "
            f"{'h < $5':>8} {'h < $0':>8} {'midday p05':>11}"
        )
        loc = pd.DatetimeIndex(m.index).tz_convert("America/Los_Angeles")
        mh = np.arange(len(mp)) % 24
        series = [
            (f"meas {k}", m[f"{k}_LMP"].to_numpy(), (loc.hour >= 9) & (loc.hour <= 16))
            for k in ("NP15", "ZP26", "SP15")
        ] + [
            (f"model {z}", mp[z].to_numpy(), (mh >= 9) & (mh <= 16))
            for z in ("NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE")
        ]
        for label, arr, belly in series:
            rec = {
                "min": round(float(arr.min()), 2),
                "p01": round(float(np.percentile(arr, 1)), 2),
                "p05": round(float(np.percentile(arr, 5)), 2),
                "hours_below_5": int((arr < 5.0).sum()),
                "hours_below_0": int((arr < 0.0).sum()),
                "midday_p05": round(float(np.percentile(arr[belly], 5)), 2),
            }
            report.setdefault("price_floor", {}).setdefault(str(year), {})[
                label
            ] = rec
            print(
                f"{label:>18} {rec['min']:>9.2f} {rec['p01']:>8.2f} "
                f"{rec['p05']:>8.2f} {rec['hours_below_5']:>8} "
                f"{rec['hours_below_0']:>8} {rec['midday_p05']:>11.2f}"
            )

    print()
    print("=" * 79)
    print("I. SPILL / SHORTFALL BY ZONE (P1 dump and slack, MWh) — is the model's")
    print("   north oversupplied in exactly the hours reality says it is short?")
    print("=" * 79)
    for year in YEARS:
        d = pd.read_parquet(KEEPER / f"hourly/system_{year}.parquet")
        d = d[d["pass"] == "P1"]
        dump = d.pivot_table(index="hour", columns="zone", values="dump")
        slack = d.pivot_table(index="hour", columns="zone", values="slack")
        mh = np.arange(len(dump)) % 24
        # The measured congestion window, read off section G: local 09-16 is
        # where dMCC is largest (solar belly + ramp).
        belly = (mh >= 9) & (mh <= 16)
        row = {}
        for z in ("NP15", "ZP26", "SP15_rest", "LA_BASIN", "SDGE"):
            row[z] = {
                "dump_total_MWh": round(float(dump[z].sum()), 1),
                "dump_belly_MWh": round(float(dump[z].to_numpy()[belly].sum()), 1),
                "dump_belly_hours": int((dump[z].to_numpy()[belly] > 1e-6).sum()),
                "slack_total_MWh": round(float(slack[z].sum()), 1),
            }
        report.setdefault("spill", {})[str(year)] = row
        print(f"-- {year}   (belly = local hours 09-16)")
        print(
            f"{'zone':>10} {'dump MWh':>14} {'dump belly MWh':>16} "
            f"{'belly h':>9} {'slack MWh':>12}"
        )
        for z, v in row.items():
            print(
                f"{z:>10} {v['dump_total_MWh']:>14,.0f} "
                f"{v['dump_belly_MWh']:>16,.0f} {v['dump_belly_hours']:>9} "
                f"{v['slack_total_MWh']:>12,.0f}"
            )

    if args.json:
        Path(args.json).write_text(json.dumps(report, indent=2))
        print(f"\nwrote {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
