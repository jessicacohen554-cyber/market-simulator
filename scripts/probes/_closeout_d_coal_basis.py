"""Close-out D / owner card R-4 (ZERO LP): the dual-basis C1 table for every registered ISO-year.

Charter: docs/backcast-closeout-plan-2026-10.md §5.0 R-4 ("study across all nine ISOs first").
Record: docs/records/governance/closeout-2026-10/STUDY-r4-coal-basis-2026-10.md.

For every ISO-year a registered run scores (9 ISOs, read from the committed registry
sidecars, payloads and bench parts — never replayed), each C1 class is scored on TWO
benchmark bases with the scorer's own ``calibration_verdict.score_fuelmix``:

* **923** — the current scorer basis: the committed ``classFull`` (EIA-923 grid-delivered,
  the combined-fossil reconcile ``reconcile_vintage_classes`` applied). 2025 is rebuilt on
  the EIA-923 **Final 2025** release (PR #7015) by the bench builder's own frame
  (``run_calibration_full.build_benchmark_frames``) with the committed part's BTM shares and
  the unchanged reconcile, and is GATED (a complete vintage; the committed completeness
  part still marks it preliminary).
* **930a** — EIA-930-aligned, ONE construction for every ISO (no per-ISO branch, rule 25),
  built from the PRE-reconcile 923 classes (the uniform k undone):
    coal family  L_c = clamp(T_c, N_c, N_c + SS)
        T_c = EIA-930 coal cell; N_c = 923 net coal (grid); SS = station service of the
        CEMS-metered coal plants, Σ_p max(0, CEMS gross_p − 923 net_p) (CAMPD unit-level
        grossLoad × opTime of coal units, the SPP-87 construction). The BA's own metering
        decides where between the net and the gross basis the benchmark sits; it can never
        leave the two measured bounds.
    gas family   L_g = clamp(T_g, G − H, G)
        T_g = EIA-930 gas − geo/biomass fold-in (``gas_foldin_deflation``) + (930 oil − 923
        residual oil) when the BA reports an oil cell (the reconcile's own family rule);
        G = 923 grid gas (all gas classes); H = 923 grid CHP (CC_CHP + CT_CHP + ST_CHP).
        The SPP-88 metering-coverage correction: gas the BA's telemetry does not carry is
        removed from the benchmark, bounded by — and booked against — the host-served
        cogeneration block (the only fossil output that can sit outside BA metering;
        SPP-88 §2, PJM-NEXT-20 card 2 Hopewell). Never raises gas above 923.
    Within a family the level is split pro rata to the 923 classes (coal routing is
    verified clean, SPP-87 §1). Two variants isolate the legs:
    ``930c`` — the coal leg alone: 930a coal classes, every other class exactly the 923 basis
    (gas keeps the committed reconcile); ``930p`` — 930a with the gas correction booked pro
    rata across ALL gas classes instead of CHP-first (allocation sensitivity).

Also reported per ISO-year (diagnostic): hourly OLS of EIA-930 coal on the CEMS gross of the
ISO's 923 coal plants (coal units only, on the builder's hour-of-year clock).

Determinations: ``calibration_verdict.iso_determination`` per ISO with ``load_artifacts``
patched to substitute each basis's ``classFull`` (nothing written; rubric untouched).

Usage::

    uv run python scripts/probes/_closeout_d_coal_basis.py frames <SCRATCH> <ISO>   # one ISO, ~2-6 min
    uv run python scripts/probes/_closeout_d_coal_basis.py study  <SCRATCH> <OUT_DIR>

``frames`` caches the bench builder's EIA-923 / EIA-930 / CAMPD frames for 2019-2025 to
SCRATCH (run ISOs one at a time: MISO's build needs most of a container's memory).
``study`` writes ``<OUT_DIR>/STUDY-r4-coal-basis-2026-10.csv`` and a JSON beside it.
"""

from __future__ import annotations

import copy
import csv
import gzip
import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO / "src"))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import calibration_verdict as cv  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402

BENCH = REPO / "frontend/data/backcast/bench"
REG = REPO / "frontend/data/backcast/registry"
KEEP = REPO / "frontend/data/backcast/keepers"
ISOS = ("CAISO", "ERCOT", "MISO", "NEISO", "NWPP", "NYISO", "PJM", "SOCO", "SPP")
YEARS = tuple(range(2019, 2026))
FINAL_YEAR = 2025
COAL = tuple(bs.COAL_GROUPS)
GAS = tuple(bs.GAS_GROUPS)
OIL = tuple(bs.OIL_GROUPS)
CHP = ("CC_CHP", "CT_CHP", "ST_CHP")


# --------------------------------------------------------------------------- frames
def build_frames(scratch: Path, iso: str) -> None:
    """Cache the bench builder's frames for ``iso`` (2019-2025) under ``scratch``."""
    import scripts.run_calibration_full as rcf

    sc = json.loads((KEEP / f"{iso}.json").read_text())
    side = json.loads((REG / f"{sc['keeper']}.json").read_text())
    bundle = REPO / side["bundle"]
    tmp = scratch / f"b_{iso}"
    tmp.mkdir(parents=True, exist_ok=True)
    meta = json.loads((bundle / "meta.json").read_text())
    meta["years"] = list(YEARS)
    (tmp / "meta.json").write_text(json.dumps(meta))
    if (bundle / "run_config.json").exists():
        shutil.copy(bundle / "run_config.json", tmp / "run_config.json")
    _, frames = rcf.build_benchmark_frames(tmp)
    for name, frame in frames.items():
        frame.to_parquet(scratch / f"fr_{iso}_{name}.parquet")
    print(iso, {k: v.shape for k, v in frames.items()})


# --------------------------------------------------------------------------- inputs
def load_part(iso: str, year: int) -> dict | None:
    """Committed bench part for (iso, year), or None."""
    p = BENCH / iso / f"{year}.json.gz"
    return json.load(gzip.open(p))["bench"] if p.exists() else None


def infer_k(b: dict) -> float:
    """The uniform reconcile factor the render applied (SCORER-COAL-1 construction)."""
    co2, cf = b.get("co2") or {}, b["classFull"]
    by, inten, btm = (
        co2.get("byClass", {}),
        co2.get("intensity", {}),
        co2.get("btmClass", {}),
    )
    ks = []
    for c, v in by.items():
        if c in btm or c not in cf or not inten.get(c) or c not in (*GAS, *COAL):
            continue
        full = v / inten[c]
        if full > 0.5:
            ks.append((full, cf[c] / full))
    if not ks:
        return 1.0
    k = max(ks)[1]
    return 1.0 if abs(k - 1.0) < 2e-4 else k


def family(e930: dict) -> tuple[str, ...]:
    """Reconcile family membership exactly as the render builds it."""
    return (*GAS, *COAL) if e930.get("oil") is None else (*GAS, *COAL, *OIL)


def pre_reconcile(b: dict) -> dict:
    """``classFull`` with the uniform reconcile factor undone (the raw 923 grid classes)."""
    k = infer_k(b)
    cf = dict(b["classFull"])
    for g in family(b["e930"]):
        if g in cf:
            cf[g] = cf[g] / k
    return cf


def frame_classes(e923: pd.DataFrame, year: int) -> dict[str, float]:
    """Full-plant 923 TWh per class from the builder frame, OTHER_FOSSIL re-bucketed as the render does."""
    from market_sim.data.fleet.eia860 import apply_other_fossil_scoring

    f = apply_other_fossil_scoring(e923[e923.year == year], year, plant_col="plant_id")
    return {
        str(k): float(v) / 1e6
        for k, v in f.groupby("klass")["annual_mwh"].sum().items()
    }


def rebuild_classfull(b: dict, full_new: dict[str, float]) -> dict:
    """classFull (pre-reconcile) on a rebuilt 923 frame, keeping the part's BTM shares.

    Fossil classes: full × (1 − committed BTM share). Nuclear / hydro / biomass / OTHER / oil
    take the frame value (no BTM). Wind / solar stay on EIA-930 (render routing).
    """
    pre = pre_reconcile(b)
    co2 = b.get("co2") or {}
    by, inten = co2.get("byClass", {}), co2.get("intensity", {})
    out = dict(pre)
    for c in pre:
        if c in ("wind", "solar"):
            continue
        if c in by and inten.get(c):
            full_old = by[c] / inten[c]
            share = (full_old - pre[c]) / full_old if full_old > 1e-9 else 0.0
            out[c] = round(full_new.get(c, 0.0) * (1.0 - share), 4)
        elif c in full_new:
            out[c] = round(full_new[c], 4)
    return out


def cems_gross(year: int, ids: set[int]) -> tuple[pd.Series, pd.DataFrame]:
    """CEMS gross (grossLoad × opTime) of COAL units at plants ``ids``.

    Returns (annual TWh per plant, hourly MWh per (plant, hour) on the bench builder's
    hour-of-year clock, ``campd._hour_index_8760``). The SPP-87 construction, every state.
    """
    from market_sim.data.campd import CAMPD_UNIT_PLANT_REMAP, _hour_index_8760

    parts = []
    for f in sorted((REPO / "data/raw/campd-unit-level").glob(f"*_{year}.parquet")):
        d = pd.read_parquet(
            f,
            columns=[
                "facilityId",
                "unitId",
                "date",
                "hour",
                "opTime",
                "grossLoad",
                "primaryFuelInfo",
            ],
        )
        d = d[d.primaryFuelInfo.astype(str).str.startswith("Coal")]
        if d.empty:
            continue
        fid = pd.to_numeric(d.facilityId, errors="coerce")
        pid = [
            CAMPD_UNIT_PLANT_REMAP.get((int(a), str(u)), int(a)) if pd.notna(a) else -1
            for a, u in zip(fid, d.unitId)
        ]
        dt = pd.to_datetime(d["date"])
        d = pd.DataFrame(
            {
                "pid": pid,
                "hoy": _hour_index_8760(dt.dt.month, dt.dt.day, d["hour"]),
                "mwh": (d.grossLoad.fillna(0.0) * d.opTime.fillna(0.0)).to_numpy(),
            }
        )
        d = d[d.pid.isin(ids) & (d.hoy >= 0)]
        parts.append(d.groupby(["pid", "hoy"]).mwh.sum())
    if not parts:
        return pd.Series(dtype=float), pd.DataFrame(columns=["pid", "hoy", "mwh"])
    h = pd.concat(parts).groupby(level=[0, 1]).sum().reset_index()
    return h.groupby("pid").mwh.sum() / 1e6, h


def hourly_fit(
    e930: pd.DataFrame, hourly: pd.DataFrame, ids: set[int], year: int
) -> dict:
    """OLS of hourly EIA-930 coal on hourly CEMS gross of the ISO's 923 coal plants (diagnostic).

    Slope ≈ 1 ⇒ the BA books coal near gross; ≈ net/gross (0.89-0.93) ⇒ net (SPP-87 §1).
    """
    y930 = e930[(e930.year == year) & (e930.series == "coal")].set_index("hour").mw
    g = hourly[hourly.pid.isin(ids)].groupby("hoy").mwh.sum()
    if y930.empty or g.empty or y930.abs().sum() <= 0:
        return {}
    j = pd.concat({"g": g, "e": y930}, axis=1).dropna()
    j = j[j.g > 0]
    if len(j) < 1000:
        return {}
    a, b0 = np.linalg.lstsq(np.vstack([j.g, np.ones(len(j))]).T, j.e, rcond=None)[0]
    return {
        "n": int(len(j)),
        "slope": round(float(a), 3),
        "intercept_mw": round(float(b0), 0),
        "corr": round(float(j.g.corr(j.e)), 3),
    }


# --------------------------------------------------------------------------- bases
def aligned(
    pre: dict, e930: dict, iso: str, ss: float, gas_mode: str
) -> tuple[dict, dict]:
    """The EIA-930-aligned classFull from the pre-reconcile 923 classes (module docstring)."""
    cf = dict(pre)
    coal = [g for g in COAL if g in cf]
    gas = [g for g in GAS if g in cf]
    n_c = sum(cf[g] for g in coal)
    t_c = float(e930.get("coal") or 0.0)
    l_c = min(max(t_c, n_c), n_c + ss) if n_c > 0 else 0.0
    if n_c > 0:
        for g in coal:
            cf[g] = round(cf[g] * l_c / n_c, 4)
    g_tot = sum(cf[g] for g in gas)
    h = sum(cf.get(g, 0.0) for g in CHP if g in gas)
    t_g = float(e930.get("gas") or 0.0) - bs.gas_foldin_deflation(pre, e930, iso)
    if e930.get("oil") is not None:
        t_g += float(e930["oil"]) - sum(pre.get(g, 0.0) for g in OIL)
    l_g = min(max(t_g, g_tot - h), g_tot)
    cut = g_tot - l_g
    if cut > 0:
        pool = [g for g in CHP if g in gas] if gas_mode == "chp" else gas
        p_tot = sum(cf[g] for g in pool)
        for g in pool:
            cf[g] = round(cf[g] * (1.0 - cut / p_tot), 4)
    info = {
        "coal_net923": round(n_c, 3),
        "coal_ss": round(ss, 3),
        "coal_gross_bound": round(n_c + ss, 3),
        "coal_930": round(t_c, 3),
        "coal_aligned": round(l_c, 3),
        "coal_side": "net"
        if l_c <= n_c + 1e-9
        else ("gross" if l_c >= n_c + ss - 1e-9 else "930"),
        "gas_923": round(g_tot, 3),
        "gas_chp": round(h, 3),
        "gas_930_equiv": round(t_g, 3),
        "gas_aligned": round(l_g, 3),
        "gas_coverage_cut": round(cut, 3),
    }
    return cf, info


# --------------------------------------------------------------------------- study
def registered() -> dict[str, list[tuple[str, list[int]]]]:
    """{iso: [(run_id, years)]} from the committed registry sidecars."""
    out = defaultdict(list)
    for f in sorted(REG.glob("*.json")):
        s = json.loads(f.read_text())
        out[s["iso"]].append((s["id"], [int(y) for y in s["years"]]))
    return out


def study(scratch: Path, out_dir: Path) -> None:
    """Build both bases, score C1 on each, compute determinations, write CSV + JSON."""

    runs = registered()
    bases: dict[str, dict[tuple[str, int], dict]] = {
        "923": {},
        "930a": {},
        "930p": {},
        "930c": {},
    }
    info, parity, final_delta, fits = {}, {}, {}, {}
    coal_ids_by_year: dict[int, set[int]] = defaultdict(set)
    frames = {}
    for iso in ISOS:
        e923 = pd.read_parquet(scratch / f"fr_{iso}_eia923.parquet")
        frames[iso] = e923
        for y in YEARS:
            coal_ids_by_year[y] |= set(
                e923[(e923.year == y) & e923.klass.isin(COAL)].plant_id.astype(int)
            )
    cems = {y: cems_gross(y, ids) for y, ids in coal_ids_by_year.items()}

    for iso in ISOS:
        e923 = frames[iso]
        e930f = pd.read_parquet(scratch / f"fr_{iso}_eia930.parquet")
        years = sorted({y for _, ys in runs[iso] for y in ys})
        for y in years:
            b = load_part(iso, y)
            if b is None:
                continue
            e930 = b["e930"]
            if y == FINAL_YEAR:
                full_new = frame_classes(e923, y)
                pre = rebuild_classfull(b, full_new)
                old_pre = pre_reconcile(b)
                final_delta[f"{iso}|{y}"] = {
                    c: round(pre[c] - old_pre.get(c, 0.0), 3)
                    for c in (*COAL, *GAS)
                    if c in pre and abs(pre[c] - old_pre.get(c, 0.0)) >= 0.005
                }
            else:
                pre = pre_reconcile(b)
                # Parity of the rebuild construction on a complete committed vintage.
                if y == FINAL_YEAR - 1:
                    rb = rebuild_classfull(b, frame_classes(e923, y))
                    parity[iso] = {
                        c: round(rb[c] - pre[c], 3)
                        for c in (*COAL, *GAS)
                        if c in pre and abs(rb[c] - pre[c]) >= 0.05
                    }
            from scripts.render_calibration_html import reconcile_vintage_classes

            cf923 = reconcile_vintage_classes(dict(pre), e930, iso)
            bases["923"][(iso, y)] = cf923
            fy = e923[(e923.year == y) & e923.klass.isin(COAL)]
            net_p = fy.groupby("plant_id").annual_mwh.sum() / 1e6
            g = cems[y][0].reindex(net_p.index.astype(int)).fillna(0.0).to_numpy()
            n = net_p.to_numpy()
            metered = g > 0
            ss = float(np.clip(g[metered] - n[metered], 0.0, None).sum())
            cfa, inf = aligned(pre, e930, iso, ss, "chp")
            cfp, _ = aligned(pre, e930, iso, ss, "all")
            inf["coal_cems_metered_share"] = (
                round(float(n[metered].sum() / n.sum()), 3) if n.sum() > 0 else None
            )
            inf["k"] = round(infer_k(b), 4)
            bases["930a"][(iso, y)] = cfa
            bases["930p"][(iso, y)] = cfp
            bases["930c"][(iso, y)] = {**cf923, **{g: cfa[g] for g in COAL if g in cfa}}
            info[f"{iso}|{y}"] = inf
            fits[f"{iso}|{y}"] = hourly_fit(
                e930f, cems[y][1], set(net_p.index.astype(int)), y
            )

    # ---- C1 table (the scorer's own score_fuelmix; FINAL_YEAR gated as a complete vintage)
    cv._completeness_map()
    cmap_committed = dict(cv._COMPLETENESS_CACHE)
    cmap_final = {k: v for k, v in cmap_committed.items() if k != FINAL_YEAR}
    rows = []
    for iso in ISOS:
        for rid, ys in runs[iso]:
            art = cv.load_artifacts(rid)
            pay = art["payload"]["years"]
            for y in ys:
                if (iso, y) not in bases["923"]:
                    continue
                recs = {}
                for basis in ("923", "930a", "930p", "930c"):
                    yb = copy.deepcopy(art["bench"][y])
                    yb["classFull"] = bases[basis][(iso, y)]
                    cv._COMPLETENESS_CACHE = cmap_final
                    recs[basis] = {
                        r["key"]: r
                        for r in cv.score_fuelmix(y, pay[str(y)], yb, iso=iso)
                    }
                cv._COMPLETENESS_CACHE = cmap_committed
                committed = {
                    r["key"]: r
                    for r in cv.score_fuelmix(y, pay[str(y)], art["bench"][y], iso=iso)
                }
                for c, r9 in recs["923"].items():
                    ra, rp, rc = recs["930a"][c], recs["930p"][c], recs["930c"][c]
                    rows.append(
                        {
                            "iso": iso,
                            "year": y,
                            "run_id": rid,
                            "class": c,
                            "family": "coal" if c in COAL else "gas",
                            "model_twh": r9["model"],
                            "bench_923_twh": r9["actual"],
                            "bench_930a_twh": ra["actual"],
                            "delta_923_twh": round(r9["model"] - r9["actual"], 3),
                            "delta_930a_twh": round(ra["model"] - ra["actual"], 3),
                            "share_pp_923": r9.get("share_pp"),
                            "share_pp_930a": ra.get("share_pp"),
                            "status_923": r9["status"],
                            "status_930a": ra["status"],
                            "flip": r9["status"] != ra["status"],
                            "bench_930c_twh": rc["actual"],
                            "delta_930c_twh": round(rc["model"] - rc["actual"], 3),
                            "share_pp_930c": rc.get("share_pp"),
                            "status_930c": rc["status"],
                            "bench_930p_twh": rp["actual"],
                            "status_930p": rp["status"],
                            "status_committed": committed.get(c, {}).get("status"),
                        }
                    )

    # ---- determinations: load_artifacts patched per basis
    real_load = cv.load_artifacts
    dets = {}
    for label, basis, cmap in (
        ("committed", None, cmap_committed),
        ("923final", "923", cmap_final),
        ("930a", "930a", cmap_final),
        ("930p", "930p", cmap_final),
        ("930c", "930c", cmap_final),
    ):

        def patched(run_id, _b=basis):
            a = real_load(run_id)
            if _b is None:
                return a
            a = copy.deepcopy(a)
            iso = a["sidecar"]["iso"]
            for y in list(a["bench"]):
                if a["bench"][y] and (iso, int(y)) in bases[_b]:
                    a["bench"][y]["classFull"] = bases[_b][(iso, int(y))]
            return a

        cv.load_artifacts = patched
        cv._COMPLETENESS_CACHE = cmap
        dets[label] = {}
        for iso in ISOS:
            sh = json.loads((KEEP / f"{iso}.json").read_text())
            d = cv.iso_determination(iso, sh["keeper"], sh.get("config_partition"))
            dets[label][iso] = {
                "determination": d["determination"],
                "scopes": [
                    {
                        "run": s.get("run_id"),
                        "role": s.get("role"),
                        "failing": s.get("failing"),
                        "years": s.get("years"),
                        "determination": s.get("determination"),
                    }
                    for s in d.get("scopes", [])
                ],
            }
    cv.load_artifacts = real_load
    cv._COMPLETENESS_CACHE = cmap_committed

    out_dir.mkdir(parents=True, exist_ok=True)
    csv_path = out_dir / "STUDY-r4-coal-basis-2026-10.csv"
    with csv_path.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    (out_dir / "STUDY-r4-coal-basis-2026-10.json").write_text(
        json.dumps(
            {
                "family_info": info,
                "hourly_fit": fits,
                "rebuild_parity_2024": parity,
                "final2025_minus_prelim_pre_reconcile": final_delta,
                "determinations": dets,
            },
            indent=1,
        )
    )
    print(f"wrote {csv_path} ({len(rows)} rows)")


if __name__ == "__main__":
    if sys.argv[1] == "frames":
        build_frames(Path(sys.argv[2]), sys.argv[3])
    else:
        study(Path(sys.argv[2]), Path(sys.argv[3]))
