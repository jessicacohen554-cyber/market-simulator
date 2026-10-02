"""Derive MISO gas VARIABLE transport with the print's reporting lag as a regressor.

miso-300 (owner ruling 2026-10-02, miso-299 decision card *"What should
miso-300 do?"*: **"Lag-aware pooled estimator (phase 0)"**).  An estimator
change on a frozen derive (rule 23 ``[R-FROZEN-DERIVE]`` admits source-data
updates alone), admissible under that ruling and under nothing else.  The
frozen table ``data/raw/reference/miso_gas_variable_transport.csv`` is NEVER
overwritten: this script writes the COMPANION
``data/raw/reference/miso_gas_variable_transport_lagaware.csv`` (+ ``.pool.csv``)
in the frozen table's exact format, so the unchanged consumer
(:func:`market_sim.data.fuel.basis.miso._load_miso_gas_variable_transport`)
reads either.

WHY A LAG TERM
--------------
The frozen derive measured the EIA-923 monthly print as a LAGGED AVERAGE of the
hub (month-over-month slope of the wedge on the hub -0.69 fleet-wide, -0.76
CC_REGULAR; a perfectly lagged average implies -1, a hub-tracking marginal cost
0).  Pooled over three years the lag averages out of the intercept; fitted on a
single year it does not (miso-299: the per-year intercept tracks the year's hub
trajectory, r = -0.54 to -0.85).  Making it a regressor lets ONE ``v`` per plant
be identified on all seven receipt years at once::

    wedge[p,m] = v[p] + F[p] / burn[p,m] + lambda * dhub[p,m]
    dhub[p,m]  = hub_m - hub_{m-1}   on the plant's own hub kind
                 (Chicago flow-day staircase monthly mean for Chicago / MidCon
                 zones, Henry Hub trade-day for MISO-South; January takes the
                 prior year's December from the prior year's staircase)

``lambda`` is ONE fleet-wide coefficient: the lag is a reporting convention of
the print, common to the fleet, not a plant or class attribute.  Per-class
values are reported as a diagnostic and used for nothing.  Never per plant.

TWO STEPS, both burn-weighted (a month's print is the volume-weighted mean of
its deliveries, so its variance scales as ``1/burn``):

1. ``lambda`` is estimated jointly with every plant's own ``v`` and ``F`` on the
   pooled 2019-2025 panel (plants with >= 3 admissible months; a plant with
   fewer is fitted exactly by its own two terms and carries no information).
2. The lag-cleaned wedge ``wedge - lambda * dhub`` is handed to the FROZEN
   derive's own machinery unchanged — :func:`derive_miso_gas_variable_transport._fit`
   (WLS on ``1/burn``, weight = burn), its own-rung bars ``MIN_MONTHS`` 12 and
   ``MIN_BURN_SPREAD`` 2.0, and its ladder own -> zone|group -> group ->
   MISO-wide.  ``v`` is therefore exactly the frozen estimator on a wedge with
   the lag term removed; nothing else changes.

THE OFFER IS STILL ``hub + v[p]``.  ``lambda`` never enters the offer; it only
cleans the identification.  Rule 13 ``[R-MEASURED]``: ``v`` stays a contractual
attribute of the plant's delivery path; the forward analogue is ``v`` carried
forward and re-identified by this same formula on each new EIA-923 vintage.

REGRESSION-FREE CROSS-CHECK (``v_topquartile_usd_mmbtu`` in the table): the
plant's burn-weighted RAW wedge over its top burn quartile restricted to
FLAT-HUB months (|dhub| at or below the median |dhub| of the whole pooled
panel — one threshold for every plant, fixed by the data).  In a flat-hub month
the lag term is ~0 by construction, so the check sees ``v`` plus the plant's
own residual fixed leg, exactly as the frozen derive's check did.

Pre-stated reading: ``docs/records/miso/FINDING-miso300-lagaware-transport-2026-10-02.md``
s0 (pinned before this script existed).  Nothing here is swept against any gate.

Usage (repo root)::

    uv run python scripts/data/derive_miso_gas_variable_transport_lagaware.py
    # -> data/raw/reference/miso_gas_variable_transport_lagaware.csv (+ .pool.csv)
    #    results/phase0/miso/_miso300_lagaware_table.json (the summary)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (str(ROOT), str(ROOT / "src")):
    if p not in sys.path:
        sys.path.insert(0, p)

from scripts.data import derive_miso_gas_variable_transport as frozen  # noqa: E402

OUT = ROOT / "data/raw/reference/miso_gas_variable_transport_lagaware.csv"
SUMMARY = ROOT / "results/phase0/miso/_miso300_lagaware_table.json"
#: Every receipt year the keeper carries (rule 16).  2018 enters only as the
#: prior December for January 2019's hub change; 2026 is partial and excluded.
YEARS: tuple[int, ...] = (2019, 2020, 2021, 2022, 2023, 2024, 2025)
#: A plant contributes to the fleet-wide ``lambda`` only with this many
#: admissible months (two are consumed by its own ``v`` and ``F``).
MIN_MONTHS_LAMBDA = 3
REPORT_GROUPS = ("CC_REGULAR", "CT_PEAKER", "ST_GAS")


def hub_month_changes(years: tuple[int, ...]) -> dict[tuple[str, int, int], float]:
    """Return ``{(hub_kind, year, month): hub_m - hub_{m-1}}`` ($/MMBtu).

    Monthly means come from :func:`frozen._hub_month_means` on the same daily
    staircases the applier prices from; January's prior month is the previous
    year's December (so the first year's prior year is included in the means).
    """
    means = frozen._hub_month_means(tuple(range(min(years) - 1, max(years) + 1)))
    out: dict[tuple[str, int, int], float] = {}
    for (kind, year, month), level in means.items():
        if year not in years:
            continue
        prev = (kind, year, month - 1) if month > 1 else (kind, year - 1, 12)
        if prev in means:
            out[(kind, year, month)] = level - means[prev]
    return out


def build_lag_panel(years: tuple[int, ...] = YEARS) -> pd.DataFrame:
    """Return the frozen wedge panel with a ``dhub_usd_mmbtu`` column attached."""
    panel = frozen.build_panel(years)
    changes = hub_month_changes(years)
    keys = list(zip(panel["hub_kind"], panel["year"], panel["month"]))
    panel["dhub_usd_mmbtu"] = [changes.get(k, np.nan) for k in keys]
    dropped = int(panel["dhub_usd_mmbtu"].isna().sum())
    panel = panel.dropna(subset=["dhub_usd_mmbtu"]).reset_index(drop=True)
    panel.attrs["rows_without_dhub"] = dropped
    return panel


def fit_lambda(panel: pd.DataFrame) -> tuple[float, float, int, int]:
    """Return ``(lambda, se, n_rows, n_plants)`` from the joint burn-weighted WLS.

    Design: one intercept and one ``1/burn`` column per plant (its ``v`` and
    ``F``) plus the single shared ``dhub`` column.  Weight ``sqrt(burn)`` on
    both sides.  The standard error is the classical WLS one.
    """
    counts = panel.groupby("plant_id")["month"].transform("size")
    sub = panel[counts >= MIN_MONTHS_LAMBDA].reset_index(drop=True)
    plants = sub["plant_id"].to_numpy()
    uniq, idx = np.unique(plants, return_inverse=True)
    n, k = len(sub), 2 * len(uniq) + 1
    design = np.zeros((n, k))
    rows = np.arange(n)
    design[rows, idx] = 1.0
    design[rows, len(uniq) + idx] = 1.0 / sub["burn_mmbtu"].to_numpy(float)
    design[:, -1] = sub["dhub_usd_mmbtu"].to_numpy(float)
    w = np.sqrt(sub["burn_mmbtu"].to_numpy(float))
    y = sub["wedge_usd_mmbtu"].to_numpy(float)
    xw, yw = design * w[:, None], y * w
    coef, *_ = np.linalg.lstsq(xw, yw, rcond=None)
    resid = yw - xw @ coef
    sigma2 = float((resid**2).sum() / max(n - k, 1))
    cov_last = float(np.linalg.pinv(xw.T @ xw)[-1, -1])
    return float(coef[-1]), float(np.sqrt(sigma2 * cov_last)), n, len(uniq)


def _flat_topquartile(wedge, burn, dhub, threshold: float) -> float:
    """The regression-free cross-check: top-burn-quartile wedge in flat-hub months."""
    flat = np.abs(dhub) <= threshold
    if flat.sum() == 0:
        return float("nan")
    return frozen._top_quartile(wedge[flat], burn[flat])


def derive_from_panel(panel: pd.DataFrame, lam: float) -> pd.DataFrame:
    """Frozen ladder on the lag-cleaned wedge; the frozen ``derive`` body otherwise.

    Mirrors :func:`derive_miso_gas_variable_transport.derive` line for line —
    pooled rungs first, then each plant's own rung or the first pooled rung it
    resolves to — with the fitted wedge ``wedge - lam * dhub``.  The
    ``v_topquartile_usd_mmbtu`` column carries the flat-hub cross-check on the
    RAW wedge; ``wedge_burn_weighted`` the raw burn-weighted wedge.
    """
    panel = panel.copy()
    panel["adj_wedge"] = panel["wedge_usd_mmbtu"] - lam * panel["dhub_usd_mmbtu"]
    flat_threshold = float(np.median(np.abs(panel["dhub_usd_mmbtu"].to_numpy(float))))

    pooled_zone_group: dict[tuple[str, str], float] = {}
    for key, grp in panel.groupby(["zone", "group"]):
        if len(grp) >= frozen.MIN_MONTHS:
            pooled_zone_group[key] = frozen._fit(
                grp["adj_wedge"].to_numpy(float), grp["burn_mmbtu"].to_numpy(float)
            )[0]
    pooled_group: dict[str, float] = {}
    for key, grp in panel.groupby("group"):
        if len(grp) >= frozen.MIN_MONTHS:
            pooled_group[str(key)] = frozen._fit(
                grp["adj_wedge"].to_numpy(float), grp["burn_mmbtu"].to_numpy(float)
            )[0]
    pooled_iso = frozen._fit(
        panel["adj_wedge"].to_numpy(float), panel["burn_mmbtu"].to_numpy(float)
    )[0]

    out: list[dict[str, object]] = []
    for plant_id, grp in panel.groupby("plant_id"):
        burn = grp["burn_mmbtu"].to_numpy(float)
        adj = grp["adj_wedge"].to_numpy(float)
        raw = grp["wedge_usd_mmbtu"].to_numpy(float)
        dhub = grp["dhub_usd_mmbtu"].to_numpy(float)
        spread = float(burn.max() / burn.min()) if burn.min() > 0 else float("inf")
        own = len(grp) >= frozen.MIN_MONTHS and spread >= frozen.MIN_BURN_SPREAD
        v_fit, fixed, r2 = frozen._fit(adj, burn)
        v_ols = frozen._fit(adj, burn, weighted=False)[0]
        key = (grp["zone"].iloc[0], grp["group"].iloc[0])
        if own:
            v, source = v_fit, "own"
        elif key in pooled_zone_group:
            v, source = pooled_zone_group[key], "zone_group_pool"
        elif key[1] in pooled_group:
            v, source = pooled_group[key[1]], "group_pool"
        else:
            v, source = pooled_iso, "miso_pool"
        out.append(
            {
                "plant_id": int(plant_id),
                "plant_name": grp["plant_name"].iloc[0],
                "group": key[1],
                "zone": key[0],
                "nameplate_mw": float(grp["nameplate_mw"].iloc[0]),
                "n_months": int(len(grp)),
                "burn_spread": round(spread, 3),
                "v_usd_mmbtu": round(v, 6),
                "v_source": source,
                "fixed_usd_month": round(fixed, 3),
                "r2": round(r2, 4),
                "v_ols_usd_mmbtu": round(v_ols, 6),
                "v_topquartile_usd_mmbtu": round(
                    _flat_topquartile(raw, burn, dhub, flat_threshold), 6
                ),
                "wedge_burn_weighted": round(float((raw * burn).sum() / burn.sum()), 6),
                "_v_own_fit": v_fit,
                "_topq_allmonths_raw": frozen._top_quartile(raw, burn),
                "_topq_allmonths_adj": frozen._top_quartile(adj, burn),
            }
        )
    frame = pd.DataFrame(out).sort_values("plant_id").reset_index(drop=True)
    frame.attrs["pooled_zone_group"] = {
        f"{k[0]}|{k[1]}": v for k, v in pooled_zone_group.items()
    }
    frame.attrs["pooled_group"] = dict(pooled_group)
    frame.attrs["pooled_iso"] = pooled_iso
    frame.attrs["flat_threshold"] = flat_threshold
    frame.attrs["lambda"] = lam
    return frame


def _cap_wtd(frame: pd.DataFrame, col: str, mask) -> float | None:
    """Nameplate-weighted mean of ``col`` over ``mask`` rows."""
    sub = frame[mask]
    sub = sub[np.isfinite(sub[col])]
    if sub.empty or sub["nameplate_mw"].sum() <= 0:
        return None
    return round(
        float((sub[col] * sub["nameplate_mw"]).sum() / sub["nameplate_mw"].sum()), 4
    )


def _write(frame: pd.DataFrame, out: Path) -> Path:
    """Write the table + ``.pool.csv`` in the frozen table's exact column set."""
    cols = [c for c in frame.columns if not c.startswith("_")]
    header = [
        "# MISO gas VARIABLE transport over the zone's traded hub ($/MMBtu), "
        "LAG-AWARE pooled estimator (miso-300 companion; the frozen table is untouched).",
        "# Derived by scripts/data/derive_miso_gas_variable_transport_lagaware.py from "
        f"EIA-923 receipts x the daily hub staircases, {YEARS[0]}-{YEARS[-1]} pooled: "
        "wedge = v + F/burn + lambda*dhub, burn-weighted WLS, ONE fleet-wide lambda = "
        f"{frame.attrs['lambda']:.4f}; v from the frozen estimator on wedge - lambda*dhub.",
        "# Owner ruling 2026-10-02 (miso-299 card 'Lag-aware pooled estimator (phase 0)'): "
        "the rule-23 ruling for this estimator change. The offer is hub + v; lambda never "
        "enters it.",
        "# v_topquartile_usd_mmbtu = regression-free cross-check: top-burn-quartile raw "
        f"wedge in flat-hub months (|dhub| <= {frame.attrs['flat_threshold']:.4f} $/MMBtu, "
        "the panel median).",
        "# Consumers resolve a plant absent from this table down the declared ladder "
        "own -> zone_group -> group -> miso, whose rungs are in the sibling .pool.csv.",
        f"# Pooled fallback rungs: MISO-wide v = {frame.attrs['pooled_iso']:.6f} $/MMBtu; "
        "per (zone|group) rungs in the sibling .pool.csv.",
    ]
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w") as handle:
        handle.write("\n".join(header) + "\n")
        frame[cols].to_csv(handle, index=False)
    pool = pd.DataFrame(
        [
            {"rung": "zone_group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_zone_group"].items())
        ]
        + [
            {"rung": "group", "key": k, "v_usd_mmbtu": round(v, 6)}
            for k, v in sorted(frame.attrs["pooled_group"].items())
        ]
        + [
            {
                "rung": "miso",
                "key": "__MISO__",
                "v_usd_mmbtu": round(frame.attrs["pooled_iso"], 6),
            }
        ]
    )
    pool.to_csv(out.with_suffix(".pool.csv"), index=False)
    return out.with_suffix(".pool.csv")


def summarize(frame: pd.DataFrame, panel: pd.DataFrame, lam_fit: tuple) -> dict:
    """Coverage, ``v`` by class, lambda (fleet + per-class diagnostic), cross-checks."""
    lam, se, n_rows, n_plants = lam_fit
    own = frame["v_source"] == "own"
    out: dict = {
        "_rule": {
            "ruling": "owner 2026-10-02, miso-299 card 'Lag-aware pooled estimator (phase 0)'",
            "estimator": "wedge = v[p] + F[p]/burn + lambda*dhub; burn-weighted WLS; "
            "lambda fleet-wide (step 1), v via frozen _fit/ladder on wedge - lambda*dhub (step 2)",
            "years": list(YEARS),
            "bars": {
                "MIN_MONTHS": frozen.MIN_MONTHS,
                "MIN_BURN_SPREAD": frozen.MIN_BURN_SPREAD,
                "MIN_MONTHS_LAMBDA": MIN_MONTHS_LAMBDA,
            },
            "source": str(frozen.F923.relative_to(ROOT)),
            "pre_stated_reading": "FINDING-miso300-lagaware-transport-2026-10-02.md s0",
        },
        "panel": {
            "plant_months": int(len(panel)),
            "plants": int(panel["plant_id"].nunique()),
            "rows_without_dhub": int(panel.attrs.get("rows_without_dhub", 0)),
            "flat_threshold_abs_dhub": round(float(frame.attrs["flat_threshold"]), 4),
            "months_flat_share": round(
                float(
                    (
                        np.abs(panel["dhub_usd_mmbtu"]) <= frame.attrs["flat_threshold"]
                    ).mean()
                ),
                3,
            ),
        },
        "lambda": {
            "fleet": round(lam, 4),
            "se": round(se, 4),
            "n_rows": n_rows,
            "n_plants": n_plants,
            "per_class_diagnostic": {},
        },
        "table": {
            "plants": int(len(frame)),
            "plants_own": int(own.sum()),
            "own_cap_share_of_table": round(
                float(
                    frame.loc[own, "nameplate_mw"].sum() / frame["nameplate_mw"].sum()
                ),
                4,
            ),
            "sources": {k: int(v) for k, v in frame["v_source"].value_counts().items()},
            "pooled_iso": round(float(frame.attrs["pooled_iso"]), 6),
            "pooled_group": {
                k: round(float(v), 6) for k, v in frame.attrs["pooled_group"].items()
            },
            "v_cap_wtd": {},
            "v_own_cap_wtd": {},
            "v_topquartile_flat_own_cap_wtd": {},
            "wedge_burn_wtd": {},
        },
        "cross_check": {},
    }
    for g in list(REPORT_GROUPS) + ["__ALL_GAS__"]:
        pm = np.ones(len(panel), bool) if g == "__ALL_GAS__" else (panel["group"] == g)
        if pm.sum() >= 3 * MIN_MONTHS_LAMBDA:
            lg = fit_lambda(panel[pm].reset_index(drop=True))
            out["lambda"]["per_class_diagnostic"][g] = {
                "lambda": round(lg[0], 4),
                "se": round(lg[1], 4),
                "n_rows": lg[2],
            }
        fm = np.ones(len(frame), bool) if g == "__ALL_GAS__" else (frame["group"] == g)
        out["table"]["v_cap_wtd"][g] = _cap_wtd(frame, "v_usd_mmbtu", fm)
        out["table"]["v_own_cap_wtd"][g] = _cap_wtd(frame, "v_usd_mmbtu", fm & own)
        out["table"]["v_topquartile_flat_own_cap_wtd"][g] = _cap_wtd(
            frame, "v_topquartile_usd_mmbtu", fm & own
        )
        sub = panel[pm]
        out["table"]["wedge_burn_wtd"][g] = round(
            float(
                (sub["wedge_usd_mmbtu"] * sub["burn_mmbtu"]).sum()
                / sub["burn_mmbtu"].sum()
            ),
            4,
        )
    o = frame[own & np.isfinite(frame["v_topquartile_usd_mmbtu"])]
    out["cross_check"] = {
        "n_own_plants": int(len(o)),
        "r_v_vs_topquartile_flat_raw": round(
            float(np.corrcoef(o["v_usd_mmbtu"], o["v_topquartile_usd_mmbtu"])[0, 1]), 4
        ),
        "r_v_vs_topquartile_allmonths_raw": round(
            float(np.corrcoef(o["v_usd_mmbtu"], o["_topq_allmonths_raw"])[0, 1]), 4
        ),
        "r_v_vs_topquartile_allmonths_adj": round(
            float(np.corrcoef(o["v_usd_mmbtu"], o["_topq_allmonths_adj"])[0, 1]), 4
        ),
        "topquartile_flat_minus_v_cap_wtd_own": _cap_wtd(
            o.assign(d=o["v_topquartile_usd_mmbtu"] - o["v_usd_mmbtu"]),
            "d",
            np.ones(len(o), bool),
        ),
    }
    return out


def main() -> None:
    """Derive the lag-aware table, write it beside the frozen one, and summarize."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=OUT)
    parser.add_argument("--summary", type=Path, default=SUMMARY)
    args = parser.parse_args()
    if args.out.resolve() == frozen.OUT.resolve():
        raise SystemExit("refusing to overwrite the frozen table (rule 23)")

    panel = build_lag_panel(YEARS)
    if panel.empty:
        raise ValueError("MISO gas lag panel is empty — check the F923 and hub inputs")
    lam_fit = fit_lambda(panel)
    frame = derive_from_panel(panel, lam_fit[0])
    pool = _write(frame, args.out)
    summary = summarize(frame, panel, lam_fit)

    # Plant-level agreement with the frozen table, where both carry an own rung.
    frozen_tab = pd.read_csv(frozen.OUT, comment="#")
    both = frame.merge(
        frozen_tab[["plant_id", "v_usd_mmbtu", "v_source"]],
        on="plant_id",
        suffixes=("", "_frozen"),
    )
    own_both = both[(both["v_source"] == "own") & (both["v_source_frozen"] == "own")]
    summary["vs_frozen"] = {
        "frozen_plants": int(len(frozen_tab)),
        "frozen_plants_own": int((frozen_tab["v_source"] == "own").sum()),
        "frozen_v_cap_wtd": {
            g: _cap_wtd(
                frozen_tab,
                "v_usd_mmbtu",
                np.ones(len(frozen_tab), bool)
                if g == "__ALL_GAS__"
                else (frozen_tab["group"] == g),
            )
            for g in list(REPORT_GROUPS) + ["__ALL_GAS__"]
        },
        "own_both_n": int(len(own_both)),
        "own_both_corr": round(
            float(
                np.corrcoef(own_both["v_usd_mmbtu"], own_both["v_usd_mmbtu_frozen"])[
                    0, 1
                ]
            ),
            3,
        )
        if len(own_both) > 2
        else None,
        "own_both_mean_diff_cap_wtd": _cap_wtd(
            own_both.assign(d=own_both["v_usd_mmbtu"] - own_both["v_usd_mmbtu_frozen"]),
            "d",
            np.ones(len(own_both), bool),
        ),
    }
    summary["files"] = [str(args.out.relative_to(ROOT)), str(pool.relative_to(ROOT))]
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    args.summary.write_text(json.dumps(summary, indent=1))

    lam, se, n_rows, n_plants = lam_fit
    t = summary["table"]
    print(
        f"panel {summary['panel']['plant_months']} plant-months / {summary['panel']['plants']} plants; "
        f"lambda {lam:+.4f} (se {se:.4f}, {n_rows} rows, {n_plants} plants); "
        f"per class {summary['lambda']['per_class_diagnostic']}"
    )
    print(
        f"table {t['plants']} plants, own {t['plants_own']} (cap share {t['own_cap_share_of_table']:.2f}); "
        f"v cap-wtd {t['v_cap_wtd']}; frozen {summary['vs_frozen']['frozen_v_cap_wtd']}"
    )
    print(f"cross-check {summary['cross_check']}")
    print(
        f"vs frozen own-both {summary['vs_frozen']['own_both_n']} r {summary['vs_frozen']['own_both_corr']}"
    )
    print(f"wrote {args.out}\nwrote {pool}\nwrote {args.summary}")


if __name__ == "__main__":
    main()
