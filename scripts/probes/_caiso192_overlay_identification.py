"""caiso-192 — lane 1: is the CAISO CC outage overlay's mechanical-vs-economic split ALREADY MADE? **NO LP.**

Gates are fixed in ``GATESPEC-caiso192-overlay-identification-2026-08-11.md`` (authored by
caiso-191 before any lane-1 measurement existed) and restated unchanged in
``PRECHECK-caiso192-overlay-identification-2026-08-11.md``, committed before this script was
written. **Nothing here is a choice**: the shipped merit-order guard is used AS SHIPPED
(``MERIT_RCC_PCTL = 0.90``, ``MERIT_OOM_FRAC = 0.90``, ``REAL_RUN_CF``,
``MIN_REAL_RUN_HOURS``, ``MERIT_HR_MIN/MAX``), no new threshold or parameter is introduced,
and every quantity is either counted from a committed artifact or produced by a shipped
function.

**Exogenous instrument closure (GATESPEC §2).** CAMPD unit-level operation, delivered fuel
prices, EIA-860 fleet identity, EIA-930 net load. **No LMP / price series / model dual /
scored residual / benchmark is read anywhere in this module** — the only price series that
enters is the delivered fuel price the shipped panel builds for itself.

What this measures, in order:

* **§A REPRODUCTION.** Re-derives the CAISO extract from CAMPD twice — once WITHOUT the
  merit-order guard and once WITH it — and compares each to the committed
  ``data/raw/campd-unit-outages-CAISO.csv`` by sha256. This is the check the lane's premise
  turns on and it is run FIRST, before any rate is computed.
* **§B X_c, the caiso-187 §2 frozen formula**, through the SHIPPED loader
  ``outages.unit_outage_derate_factors`` — the G-RATE basis — measured on (i) the committed
  extract (the overlay the LP actually applies) and (ii) the counterfactual PRE-guard extract
  (committed ∪ the committed layup companion), so the guard's already-realised effect is
  quantified rather than assumed.
* **§C G-SEP** separation statistics between the reclassified (layup) and retained
  (mechanical) spans, using the shipped ``MeritOrderPanel.out_of_merit_share``.
* **§D** the gate tally.

The loader is reached through a temporarily patched path resolver so the counterfactual can
be measured; ``data/raw`` is never written. There is no solve.

Usage::

    uv run python scripts/probes/_caiso192_overlay_identification.py
"""

from __future__ import annotations

import contextlib
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))

ISO = "CAISO"
YEARS = [2023, 2024, 2025]
# The extract spans 2018-2026; the guard and the reproduction identity are properties of the
# whole file, so §A is measured over the full derived span. Every GATE statistic below is
# restricted to YEARS (rule 22 -- the gates are defined on the training window).
DERIVE_YEARS = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
HOURS = 8760
KEEPER = REPO / "results" / "calibration" / "caiso188_d1_micseam"
EXTRACT = REPO / "data" / "raw" / "campd-unit-outages-CAISO.csv"
LAYUP = REPO / "data" / "raw" / "campd-unit-outages-layup-CAISO.csv"
OUT = REPO / "results" / "calibration" / "_caiso192_overlay_identification.json"

# The two classes the lane is chartered over (GATESPEC §1).
SCOPE = ("CC_REGULAR", "CC_CHP")

# The gate bars, transcribed from GATESPEC §3. Declared as constants so the tally below
# cannot silently drift from the spec.
G_RATE_LO, G_RATE_HI = 0.07, 0.15
G_STAB_MAX_YOY_PP = 3.0
G_STAB_MAX_RATIO = 1.5
G_SEP_MIN_LAYUP_OOM = 0.80
G_SEP_MIN_SEPARATION_PP = 30.0


def _sha256(path: Path) -> str:
    """Hex sha256 of a file's bytes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _derive(out_path: Path, guard: bool) -> None:
    """Run the shipped deriver into ``out_path``; ``guard`` toggles --merit-order-guard.

    Invoked as a subprocess through the same CLI a re-derivation would use, so the
    reproduction check exercises the shipped path end to end rather than an in-process
    reimplementation of it.
    """
    cmd = [
        sys.executable,
        str(REPO / "scripts" / "data" / "derive_campd_unit_outages.py"),
        "--iso",
        ISO,
        "--years",
        *[str(y) for y in DERIVE_YEARS],
        "--hour-grain",
        "--out",
        str(out_path),
    ]
    if guard:
        cmd.append("--merit-order-guard")
    subprocess.run(cmd, check=True, cwd=str(REPO), capture_output=True)


def _keeper_config():
    """The designated keeper's ScenarioConfig, from its own committed run_config."""
    import dataclasses

    from market_sim.config.scenarios import ScenarioConfig

    sc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    fields = {f.name for f in dataclasses.fields(ScenarioConfig)}
    return ScenarioConfig(**{k: v for k, v in sc.items() if k in fields})


def _fleet_by_class(cfg):
    """``{class: [(plant_code, pmax_mw, online_year)]}`` for the CAISO LP fleet.

    Built through the shipped path so the population is exactly the LP's bins (the caiso-187
    §2 construction, reproduced verbatim).
    """
    from market_sim.config.iso_configs import get_iso_config
    from market_sim.data.fleet.assembly import bins_to_fleet, load_or_synthesize_bins

    iso_cfg = get_iso_config(ISO)
    bins = load_or_synthesize_bins(cfg, ISO, iso_cfg, [])
    gens, _ = bins_to_fleet(bins, [z.name for z in iso_cfg.zones], cfg)
    out: dict[str, list[tuple[int, float, int]]] = {}
    for g in gens:
        out.setdefault(str(g.plant_group), []).append(
            (int(g.plant_code), float(g.pmax_mw), int(g.online_year))
        )
    return out


@contextlib.contextmanager
def _extract_at(path: Path):
    """Point the SHIPPED loader's CAISO path resolver at ``path`` for the block.

    Measurement device only: it lets ``unit_outage_derate_factors`` -- the loader the LP
    itself uses -- be evaluated on the counterfactual PRE-guard extract without writing a
    byte into ``data/raw``. Restored unconditionally on exit.

    ``unit_outage_derate_factors`` is ``@lru_cache``d on its arguments, and the path is NOT
    one of them, so the cache is cleared on both entry and exit -- without that the
    counterfactual silently returns the previously-measured committed-extract result.
    """
    from market_sim.data import outages as _out

    original = _out.unit_outage_csv_for_iso
    try:
        _out.unit_outage_csv_for_iso = lambda iso: path  # noqa: ARG005
        _out.unit_outage_derate_factors.cache_clear()
        yield
    finally:
        _out.unit_outage_csv_for_iso = original
        _out.unit_outage_derate_factors.cache_clear()


def _x_class(cfg, units_by_class, year: int) -> dict[str, dict[str, float]]:
    """``X_c`` per class -- the overlay's measured removal, through the SHIPPED loader.

    Verbatim the caiso-187 §2 construction: ``unit_outage_derate_factors`` returns the
    per-(plant, group) hourly availability MULTIPLIER the LP applies, and the class's measured
    removal is one minus its capacity-weighted, hour-averaged multiplier. Plants absent from
    the overlay contribute 1.0, so the figure is the class's fleet-wide removal.
    """
    from market_sim.data.outages import unit_outage_derate_factors

    factors = unit_outage_derate_factors(
        year,
        HOURS,
        iso=ISO,
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
        cc_nameplate_basis=bool(getattr(cfg, "unit_outage_lp_capacity_basis", False)),
    )
    out: dict[str, dict[str, float]] = {}
    for klass, units in units_by_class.items():
        cap: dict[int, float] = {}
        for code, pmax, _online in units:
            cap[code] = cap.get(code, 0.0) + pmax
        num = den = 0.0
        covered = 0.0
        for code, pmax in cap.items():
            arr = factors.get((code, klass))
            mult = 1.0 if arr is None else float(np.mean(arr))
            if arr is not None and mult < 1.0 - 1e-12:
                covered += pmax
            num += mult * pmax
            den += pmax
        if den <= 0:
            continue
        out[klass] = {
            "class_capacity_mw": round(den, 1),
            "overlay_covered_capacity_mw": round(covered, 1),
            "mean_availability_multiplier": round(num / den, 6),
            "X_measured_removal": round(1.0 - num / den, 6),
        }
    return out


def _window_hours(df: pd.DataFrame, year: int) -> pd.DataFrame:
    """Add year-clock ``[h0, h1)`` hour indices to an event frame, clipped to ``year``.

    Uses the SHIPPED reconstruction :func:`outages.unit_outage_event_window`, so the window a
    span is scored over is the same window the loader derates over.
    """
    from market_sim.data.outages import _has_hour_grain, unit_outage_event_window

    grain = _has_hour_grain(df)
    y0 = pd.Timestamp(f"{year}-01-01")
    y1 = pd.Timestamp(f"{year + 1}-01-01")
    rows = []
    for r in df.itertuples(index=False):
        start, stop = unit_outage_event_window(r, grain)
        if stop <= y0 or start >= y1:
            continue
        s = max(start, y0)
        e = min(stop, y1)
        rows.append(
            {
                "facility_id": int(r.facility_id),
                "unit_id": str(r.unit_id),
                "plant_group": str(r.plant_group),
                "unit_capacity_mw": float(r.unit_capacity_mw),
                "h0": int((s - y0).total_seconds() // 3600),
                "h1": int((e - y0).total_seconds() // 3600),
            }
        )
    return pd.DataFrame(rows)


def _sep_stats(retained: pd.DataFrame, layup: pd.DataFrame, year: int) -> dict:
    """G-SEP statistics for one year, over the lane's scope classes.

    Out-of-merit share per span comes from the SHIPPED
    :meth:`MeritOrderPanel.out_of_merit_share`; the panel is the SHIPPED
    :func:`build_merit_order_panel` at its shipped percentile. Means are weighted by
    ``unit_capacity_mw x span_hours`` (capacity-weighted over span-hours, GATESPEC §3
    G-SEP(a)). Spans whose unit the panel cannot identify carry no share and are counted
    separately -- they are the fail-safe population that STAYS MECHANICAL (GATESPEC §4.1).
    """
    from lib.outage_detect import MERIT_RCC_PCTL, build_merit_order_panel

    panel = build_merit_order_panel(ISO, year, HOURS, ("CA",), MERIT_RCC_PCTL)
    if panel is None:
        return {"panel": None}

    def _agg(df: pd.DataFrame) -> dict:
        num = den = 0.0
        n_scored = n_unidentified = 0
        mar_may_w = tot_w = 0.0
        for r in df.itertuples(index=False):
            hours = max(0, r.h1 - r.h0)
            w = float(r.unit_capacity_mw) * hours
            tot_w += w
            # Mar-May share of span-hours (GATESPEC §3 G-SEP(c), the spring signature).
            mar0 = int(
                (
                    pd.Timestamp(f"{year}-03-01") - pd.Timestamp(f"{year}-01-01")
                ).total_seconds()
                // 3600
            )
            jun0 = int(
                (
                    pd.Timestamp(f"{year}-06-01") - pd.Timestamp(f"{year}-01-01")
                ).total_seconds()
                // 3600
            )
            overlap = max(0, min(r.h1, jun0) - max(r.h0, mar0))
            mar_may_w += float(r.unit_capacity_mw) * overlap
            share = panel.out_of_merit_share((r.facility_id, r.unit_id), r.h0, r.h1)
            if share is None:
                n_unidentified += 1
                continue
            n_scored += 1
            num += share * w
            den += w
        return {
            "spans": int(len(df)),
            "spans_scored": n_scored,
            "spans_unidentified_failsafe": n_unidentified,
            "cap_weighted_mean_oom_share": (round(num / den, 6) if den > 0 else None),
            "mar_may_share_of_span_hours": (
                round(mar_may_w / tot_w, 6) if tot_w > 0 else None
            ),
        }

    ret = _agg(retained)
    lay = _agg(layup)
    sep = None
    if (
        ret["cap_weighted_mean_oom_share"] is not None
        and lay["cap_weighted_mean_oom_share"] is not None
    ):
        sep = round(
            100.0
            * (lay["cap_weighted_mean_oom_share"] - ret["cap_weighted_mean_oom_share"]),
            4,
        )
    return {
        "panel_priced_units": len(panel.srmc),
        "retained_mechanical": ret,
        "reclassified_layup": lay,
        "separation_pp": sep,
    }


def main() -> None:
    """Measure the lane and write the identification record. No LP, no solve."""
    record: dict = {
        "session": "caiso-192",
        "lane": 1,
        "iso": ISO,
        "gate_years": YEARS,
        "keeper": KEEPER.name,
        "gatespec": "GATESPEC-caiso192-overlay-identification-2026-08-11.md",
        "precheck": "PRECHECK-caiso192-overlay-identification-2026-08-11.md",
        "constants_as_shipped": True,
        "new_thresholds_introduced": [],
        "price_series_read": "NONE (GATESPEC §2 closure honoured)",
    }

    # ---- §A REPRODUCTION -------------------------------------------------
    committed_sha = _sha256(EXTRACT)
    with tempfile.TemporaryDirectory() as td:
        unguarded = Path(td) / "unguarded.csv"
        guarded = Path(td) / "guarded.csv"
        _derive(unguarded, guard=False)
        _derive(guarded, guard=True)
        un_sha, g_sha = _sha256(unguarded), _sha256(guarded)
        a = pd.read_csv(unguarded)
        c = pd.read_csv(EXTRACT)
        lay_all = pd.read_csv(LAYUP)
        key = ["facility_id", "unit_id", "outage_start", "outage_end"]
        ak = a[key].astype(str).agg("|".join, axis=1)
        ck = c[key].astype(str).agg("|".join, axis=1)
        lk = lay_all[key].astype(str).agg("|".join, axis=1)
        record["A_reproduction"] = {
            "committed_extract_sha256": committed_sha,
            "rederived_WITHOUT_guard_sha256": un_sha,
            "rederived_WITH_guard_sha256": g_sha,
            "GUARD_ALREADY_APPLIED": g_sha == committed_sha,
            "unguarded_reproduces_committed": un_sha == committed_sha,
            "rows_unguarded": int(len(a)),
            "rows_committed": int(len(c)),
            "rows_layup_companion": int(len(lay_all)),
            "rows_only_in_unguarded": int((~ak.isin(set(ck))).sum()),
            "rows_only_in_committed": int((~ck.isin(set(ak))).sum()),
            "unguarded_minus_committed_equals_layup": bool(
                set(ak) - set(ck) == set(lk)
            ),
            "derive_years": DERIVE_YEARS,
        }

    # ---- §B X_c through the SHIPPED loader --------------------------------
    cfg = _keeper_config()
    units_by_class = _fleet_by_class(cfg)

    # Counterfactual PRE-guard extract = committed UNION the committed layup companion.
    # Written to a temp path only; data/raw is never touched.
    pre = pd.concat([c, lay_all], ignore_index=True)
    with tempfile.TemporaryDirectory() as td:
        pre_path = Path(td) / "campd-unit-outages-CAISO-preguard.csv"
        pre.to_csv(pre_path, index=False)
        per_year: dict[str, dict] = {}
        for year in YEARS:
            post = _x_class(cfg, units_by_class, year)
            with _extract_at(pre_path):
                pre_x = _x_class(cfg, units_by_class, year)
            per_year[str(year)] = {
                klass: {
                    "POST_guard_X": post.get(klass, {}).get("X_measured_removal"),
                    "PRE_guard_X": pre_x.get(klass, {}).get("X_measured_removal"),
                    "guard_already_removes_pp": (
                        round(
                            100.0
                            * (
                                pre_x.get(klass, {}).get("X_measured_removal", 0.0)
                                - post.get(klass, {}).get("X_measured_removal", 0.0)
                            ),
                            4,
                        )
                    ),
                    "class_capacity_mw": post.get(klass, {}).get("class_capacity_mw"),
                }
                for klass in SCOPE
                if klass in post
            }
    record["B_removal_rates"] = per_year

    # ---- §C G-SEP ---------------------------------------------------------
    c_scope = c[c.plant_group.isin(SCOPE)]
    l_scope = lay_all[lay_all.plant_group.isin(SCOPE)]
    sep: dict[str, dict] = {}
    for year in YEARS:
        sep[str(year)] = _sep_stats(
            _window_hours(c_scope, year), _window_hours(l_scope, year), year
        )
    record["C_separation"] = sep

    # ---- §D GATE TALLY ----------------------------------------------------
    rates = {
        y: record["B_removal_rates"][str(y)]["CC_REGULAR"]["POST_guard_X"]
        for y in YEARS
    }
    g_rate_per_year = {
        str(y): {"rate": rates[y], "in_band": bool(G_RATE_LO <= rates[y] <= G_RATE_HI)}
        for y in YEARS
    }
    yoy = {
        f"{YEARS[i]}->{YEARS[i + 1]}": round(
            100.0 * (rates[YEARS[i + 1]] - rates[YEARS[i]]), 4
        )
        for i in range(len(YEARS) - 1)
    }
    ratio = round(rates[2025] / rates[2023], 6) if rates[2023] else None
    g_stab = {
        "yoy_change_pp": yoy,
        "yoy_within_3pp": all(abs(v) <= G_STAB_MAX_YOY_PP for v in yoy.values()),
        "ratio_2025_over_2023": ratio,
        "ratio_within_1.5x": bool(ratio is not None and ratio <= G_STAB_MAX_RATIO),
    }
    g_stab["pass"] = bool(g_stab["yoy_within_3pp"] and g_stab["ratio_within_1.5x"])

    sep_pass = {}
    for y in YEARS:
        s = sep[str(y)]
        lay_oom = s.get("reclassified_layup", {}).get("cap_weighted_mean_oom_share")
        sep_pp = s.get("separation_pp")
        lay_mm = s.get("reclassified_layup", {}).get("mar_may_share_of_span_hours")
        ret_mm = s.get("retained_mechanical", {}).get("mar_may_share_of_span_hours")
        sep_pass[str(y)] = {
            "a_layup_oom_ge_0.80": bool(
                lay_oom is not None and lay_oom >= G_SEP_MIN_LAYUP_OOM
            ),
            "b_separation_ge_30pp": bool(
                sep_pp is not None and sep_pp >= G_SEP_MIN_SEPARATION_PP
            ),
            "c_spring_signature": bool(
                lay_mm is not None and ret_mm is not None and lay_mm > ret_mm
            ),
        }

    record["D_gate_tally"] = {
        "G_RATE": {
            "band": [G_RATE_LO, G_RATE_HI],
            "per_year": g_rate_per_year,
            "pass": all(v["in_band"] for v in g_rate_per_year.values()),
        },
        "G_STAB": g_stab,
        "G_SEP": {
            "per_year": sep_pass,
            "pass": all(all(v.values()) for v in sep_pass.values()),
        },
        "G_LOYO": {
            "new_thresholds": [],
            "pass": True,
            "basis": "vacuous - no new threshold or parameter introduced; shipped "
            "constants used AS SHIPPED (GATESPEC §3 G-LOYO, PRECHECK §3 declaration)",
        },
    }
    record["D_gate_tally"]["ALL_GATES_PASS"] = all(
        record["D_gate_tally"][g]["pass"]
        for g in ("G_RATE", "G_STAB", "G_SEP", "G_LOYO")
    )
    record["ADOPTED"] = record["D_gate_tally"]["ALL_GATES_PASS"]

    # ---- §E cross-checks against INDEPENDENT committed figures -------------
    # Neither is used to decide anything; both are corroboration that this session's
    # instruments reproduce figures published by earlier sessions from other code paths.
    lay_all["_y"] = pd.to_datetime(lay_all.outage_start).dt.year
    record["E_cross_checks"] = {
        "caiso183_published_extract_sha256": "25360e90",
        "measured_extract_sha256_prefix": committed_sha[:8],
        "sha_matches_caiso183": committed_sha.startswith("25360e90"),
        "caiso183_published_recipe": (
            "derive_campd_unit_outages.py --iso CAISO --years 2018 … 2026 "
            "--merit-order-guard --hour-grain"
        ),
        "caiso180_published_layup_counts_2023_2024_2025": [93, 164, 98],
        "measured_layup_counts_2023_2024_2025": [
            int((lay_all._y == y).sum()) for y in YEARS
        ],
        "caiso187_published_X_CC_REGULAR": [0.2157, 0.2621, 0.3186],
        "measured_X_CC_REGULAR": [
            record["B_removal_rates"][str(y)]["CC_REGULAR"]["POST_guard_X"]
            for y in YEARS
        ],
    }

    OUT.write_text(json.dumps(record, indent=1))
    print(json.dumps(record, indent=1))
    print(f"\nwrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
