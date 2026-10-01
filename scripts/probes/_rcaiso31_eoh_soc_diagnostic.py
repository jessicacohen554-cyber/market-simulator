"""R-CAISO-31 (link 13) — report-only diagnostic over the intaken RTM EOH SOC bounds.

ZERO LP. Reads the committed extract ``data/raw/caiso-rtm-eoh-soc/`` and the
keeper's committed storage sidecars (``results/calibration/rcaiso20_A_span/
hourly/storage_<year>.parquet``). Nothing here feeds a solve (rule 13: the
bound is a conduct parameter with no forward driver; R-CAISO-28 FINDING §1).

Measures, per year 2023-25:

1. Coverage by month: S1 storage resources and EOH submitters per day, and the
   submitters' share of S1 injection MW (``en_max_mw``).
2. Hour-of-day (Pacific prevailing) envelope of the submitters' bounds,
   normalised per resource by its year ceiling (max of ``max_eoh_soc_mwh``,
   which tracks energy capacity, R-CAISO-28 §1): sum(min)/sum(ceiling) and
   sum(max)/sum(ceiling) over the resource-hours that carry a bound, plus the
   share of resource-hours "pinned" (max - min <= PIN_FRAC x ceiling).
3. The keeper's li-ion fleet SOC / energy capacity by the same hour of day.
   Qualitative comparator only: the submitters are a self-selected subset.

Usage::

    python3 scripts/probes/_rcaiso31_eoh_soc_diagnostic.py

Output (committed with the FINDING): docs/records/caiso/r-caiso-31/eoh_soc_diagnostic.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.paths import RAW_DATA_DIR  # noqa: E402

RAW = RAW_DATA_DIR / "caiso-rtm-eoh-soc"
KEEPER = REPO / "results" / "calibration" / "rcaiso20_A_span" / "hourly"
OUT = REPO / "docs" / "records" / "caiso" / "r-caiso-31" / "eoh_soc_diagnostic.json"
YEARS = (2023, 2024, 2025)
TZ = "America/Los_Angeles"
#: A bound whose window is narrower than 10 % of the resource's ceiling is
#: reported as "pinned" (descriptive threshold for the report, not a parameter).
PIN_FRAC = 0.10


def coverage(year: int) -> dict:
    """Monthly coverage of the EOH submitters against the S1 storage universe."""
    uni = pd.read_parquet(RAW / f"caiso_rtm_storage_universe_{year}.parquet")
    uni["month"] = uni["trade_date"].dt.month
    s1 = uni[uni["is_storage_s1"]]
    daily = s1.groupby("trade_date").agg(
        month=("month", "first"),
        n_s1=("resourcebid_seq", "size"),
        mw_s1=("en_max_mw", "sum"),
    )
    sub = (
        s1[s1["submits_eoh"]]
        .groupby("trade_date")
        .agg(n_sub=("resourcebid_seq", "size"), mw_sub=("en_max_mw", "sum"))
    )
    daily = daily.join(sub).fillna({"n_sub": 0, "mw_sub": 0.0})
    m = daily.groupby("month").agg(
        n_s1=("n_s1", "mean"),
        n_sub=("n_sub", "mean"),
        mw_s1=("mw_s1", "mean"),
        mw_sub=("mw_sub", "mean"),
    )
    m["mw_share"] = m["mw_sub"] / m["mw_s1"]
    non_s1 = int(uni.loc[~uni["is_storage_s1"], "resourcebid_seq"].nunique())
    return {
        "by_month": {
            int(k): {c: round(float(v), 4) for c, v in r.items()}
            for k, r in m.iterrows()
        },
        "year_mean_mw_share": round(
            float(daily["mw_sub"].sum() / daily["mw_s1"].sum()), 4
        ),
        "distinct_submitters": int(
            uni.loc[uni["submits_eoh"], "resourcebid_seq"].nunique()
        ),
        "submitters_failing_s1": non_s1,
    }


def envelope(year: int) -> dict:
    """Hour-of-day normalised bound envelope of the submitters."""
    e = pd.read_parquet(RAW / f"caiso_rtm_eoh_soc_{year}.parquet")
    cap = e.groupby("resourcebid_seq")["max_eoh_soc_mwh"].transform("max")
    e = e[cap > 0].assign(cap=cap[cap > 0])
    local = pd.to_datetime(e["interval_start_utc"], utc=True).dt.tz_convert(TZ)
    e = e.assign(
        hod=local.dt.hour,
        summer=local.dt.month.between(6, 9),
        pinned=(e["max_eoh_soc_mwh"] - e["min_eoh_soc_mwh"]) <= PIN_FRAC * e["cap"],
    )

    def prof(df: pd.DataFrame) -> dict:
        g = df.groupby("hod")
        return {
            int(h): {
                "min_frac": round(float(r["min_eoh_soc_mwh"] / r["cap"]), 4),
                "max_frac": round(float(r["max_eoh_soc_mwh"] / r["cap"]), 4),
                "pinned_share": round(float(r["pinned"]), 4),
                "resource_hours": int(r["n"]),
            }
            for h, r in g.agg(
                min_eoh_soc_mwh=("min_eoh_soc_mwh", "sum"),
                max_eoh_soc_mwh=("max_eoh_soc_mwh", "sum"),
                cap=("cap", "sum"),
                pinned=("pinned", "mean"),
                n=("cap", "size"),
            ).iterrows()
        }

    return {
        "all": prof(e),
        "summer_jun_sep": prof(e[e["summer"]]),
        "resource_hours": int(len(e)),
        "pinned_share": round(float(e["pinned"].mean()), 4),
    }


def keeper_soc(year: int) -> dict | None:
    """Keeper li-ion fleet SOC / energy capacity by Pacific hour of day (P1)."""
    p = KEEPER / f"storage_{year}.parquet"
    if not p.exists():
        return None
    s = pd.read_parquet(p)
    s = s[(s["pass"] == "P1") & (s["tech"] == "li_ion")]
    s = s.assign(hod=s["hour"] % 24)
    g = s.groupby("hod")[["soc_mwh", "energy_cap_mwh"]].sum()
    return {
        int(h): round(float(r["soc_mwh"] / r["energy_cap_mwh"]), 4)
        for h, r in g.iterrows()
    }


def chart(out: dict) -> Path:
    """Render the envelope-vs-keeper and coverage panels next to the JSON."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.ticker import PercentFormatter

    blue, orange, ink, mute = "#2a78d6", "#eb6834", "#1a1a19", "#6b6a63"
    fig, ax = plt.subplots(
        1, 4, figsize=(15, 3.8), gridspec_kw={"width_ratios": [1, 1, 1, 1.1]}
    )
    hours = list(range(24))
    for i, y in enumerate(str(y) for y in YEARS):
        a, e, k = ax[i], out[y]["envelope"]["all"], out[y]["keeper_soc_frac"]
        lo = [e[str(h)]["min_frac"] for h in hours]
        hi = [e[str(h)]["max_frac"] for h in hours]
        a.fill_between(
            hours,
            lo,
            hi,
            color=blue,
            alpha=0.18,
            lw=0,
            label="Submitters' bound (min-max)",
        )
        a.plot(hours, lo, color=blue, lw=2)
        a.plot(hours, hi, color=blue, lw=2)
        if k:
            a.plot(
                hours,
                [k[str(h)] for h in hours],
                color=orange,
                lw=2,
                label="Keeper fleet SOC",
            )
        share = out[y]["coverage"]["year_mean_mw_share"]
        a.set_title(
            f"{y} · {share:.0%} of storage MW submit",
            fontsize=10,
            color=ink,
            loc="left",
        )
        a.set_xlim(0, 23)
        a.set_ylim(0, 1.02)
        a.set_xticks([0, 6, 12, 18, 23])
        a.set_xlabel("Hour of day (Pacific)", color=mute, fontsize=9)
        if i == 0:
            a.set_ylabel("Share of energy capacity", color=mute, fontsize=9)
            a.legend(fontsize=8, frameon=False, loc="center left")
    a, months = ax[3], list(range(1, 13))
    for y, col in zip((str(y) for y in YEARS), ("#9ec5f4", "#5598e7", "#184f95")):
        bm = out[y]["coverage"]["by_month"]
        a.plot(
            months,
            [bm[str(m)]["mw_share"] for m in months],
            color=col,
            lw=2,
            marker="o",
            ms=4,
        )
        a.annotate(
            y,
            (12, bm["12"]["mw_share"]),
            xytext=(4, 0),
            textcoords="offset points",
            fontsize=8,
            color=ink,
            va="center",
        )
    a.set_title(
        "Submitters' share of storage MW, by month", fontsize=10, color=ink, loc="left"
    )
    a.set_xlim(1, 13)
    a.set_ylim(0, 0.3)
    a.yaxis.set_major_formatter(PercentFormatter(1.0))
    a.set_xticks([1, 4, 7, 10])
    a.set_xticklabels(["Jan", "Apr", "Jul", "Oct"])
    for a in ax:
        a.grid(axis="y", color="#e6e5df", lw=0.8)
        a.set_axisbelow(True)
        for side in ("top", "right"):
            a.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            a.spines[side].set_color("#c3c2b7")
        a.tick_params(colors=mute, labelsize=8)
    fig.suptitle(
        "CAISO RTM end-of-hour SOC bounds (participant-submitted, self-selected subset) vs keeper fleet SOC — report-only",
        fontsize=11,
        color=ink,
        x=0.01,
        ha="left",
    )
    fig.tight_layout()
    png = OUT.with_name("eoh_soc_envelope.png")
    fig.savefig(png, dpi=130, facecolor="white")
    return png


def main() -> int:
    """Compute and write the diagnostic record."""
    out = {
        str(y): {
            "coverage": coverage(y),
            "envelope": envelope(y),
            "keeper_soc_frac": keeper_soc(y),
        }
        for y in YEARS
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, indent=1))
    for y in YEARS:
        c, e = out[str(y)]["coverage"], out[str(y)]["envelope"]
        print(
            y,
            "MW share",
            c["year_mean_mw_share"],
            "submitters",
            c["distinct_submitters"],
            "pinned",
            e["pinned_share"],
            "min_frac h13/h17/h20",
            [e["all"].get(h, {}).get("min_frac") for h in (13, 17, 20)],
        )
    print(
        "wrote",
        OUT.relative_to(REPO),
        chart(json.loads(json.dumps(out))).relative_to(REPO),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
