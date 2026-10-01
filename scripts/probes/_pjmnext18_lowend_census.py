"""PJM-NEXT-18 card 1: the keeper's low-end price-setters across 2019-2025, against the IMM.

Extends PJM-NEXT-14's 2020-only system-grain census (``_pjmnext14_lowend_lp_system.py``)
to every year of the keeper ``2026-09-30-pjm-next16-ovec``, read from the seven
year-isolated diagnostic replays' ``hourly/unit_hourly_<y>.parquet`` (rule 36).

Per year:
- **G-REPRO**: every class's P1 TWh in the replay vs the keeper's committed
  ``pjmnext16_A_span/hourly/class_hourly_<y>.parquet``.
- **Marginal set**: P1 unit-hours interior by > ``TOL_MW`` off both bounds with
  ``|red_cost| <= TOL_RC``, pooled per hour, weight ``1/n`` within the hour.
- ``all`` and ``low`` hours (actual RT < 6.5 x delivered gas, NEXT-12/14): the
  thermal-marginal hour share, class and class:kind shares, the share of weight whose
  offer is below 6.5 x delivered gas (P1), and median marginal offer vs median actual RT,
  both / delivered gas (P2/P3).
- **IMM comparison (P5)**: all-hours fuel-family shares of the thermal marginal weight
  (CC = CC_*, coal = COAL_*, CT = CT_*), renormalised over those three families, against
  the IMM's RT marginal-resource shares renormalised the same way
  (``data/raw/som-competitive-conduct``).

Run: ``python3 scripts/probes/_pjmnext18_lowend_census.py <year>=<replay_bundle> ...``
Writes ``results/phase0/pjm/_pjmnext18_lowend_census.json``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO / "scripts/probes"))
import _pjmnext14_lowend_lp as L  # noqa: E402
from scripts.data.derive_pjm_offer_surface import _pjm_fuel_daily  # noqa: E402

KEEPER_HOURLY = REPO / "results/calibration/pjmnext16_A_span/hourly"
OUT = REPO / "results/phase0/pjm/_pjmnext18_lowend_census.json"
T = 8760
#: IMM ``fleet_segment`` -> model fuel family.
IMM_FAMILY = {"gas_combined_cycle": "CC", "coal": "coal", "gas_simple_cycle": "CT"}


def _family(cls: str) -> str:
    """Fuel family of a model class."""
    if cls.startswith("CC_"):
        return "CC"
    if cls.startswith("COAL"):
        return "coal"
    if cls.startswith("CT_"):
        return "CT"
    return "other"


def _imm_shares(y: int) -> dict:
    """IMM RT marginal-resource shares for the year, raw and renormalised to CC/coal/CT."""
    d = pd.read_csv(L.SOM)
    d = d[(d.iso == "PJM") & (d.year == y) & (d.metric == "rt_marginal_resource_share")]
    raw = {str(r.fleet_segment): float(r.value) for r in d.itertuples()}
    fam = {IMM_FAMILY[k]: v for k, v in raw.items() if k in IMM_FAMILY}
    tot = sum(fam.values())
    return {
        "raw": raw,
        "renorm_cc_coal_ct": {k: round(v / tot, 3) for k, v in fam.items()}
        if tot
        else {},
    }


def _repro(bundle: Path, y: int) -> dict:
    """Per-class P1 TWh, replay minus keeper."""

    def twh(p: Path) -> pd.Series:
        c = pd.read_parquet(p)
        c = c[c["pass"].astype(str) == "P1"]
        return c.groupby(c.klass.astype(str)).mw.sum() / 1e6

    k = twh(KEEPER_HOURLY / f"class_hourly_{y}.parquet")
    r = twh(bundle / f"hourly/class_hourly_{y}.parquet")
    d = r.reindex(k.index.union(r.index)).fillna(0) - k.reindex(
        k.index.union(r.index)
    ).fillna(0)
    return {
        "max_abs_delta_twh": round(float(d.abs().max()), 6),
        "by_class_delta_twh": {a: round(float(v), 6) for a, v in d.items() if v != 0},
    }


def census(bundle: Path, y: int) -> dict:
    """One year's census."""
    cols = ["unit_id", "plant_group", "hour", "mw", "cap_mw", "mc", "red_cost", "pass"]
    u = pd.read_parquet(bundle / f"hourly/unit_hourly_{y}.parquet", columns=cols)
    u = u[(u["pass"].astype(str) == "P1") & (u.hour < T)].drop(columns="pass")
    m = u[
        (u.mw > L.TOL_MW)
        & (u.mw < u.cap_mw - L.TOL_MW)
        & (u.red_cost.abs() <= L.TOL_RC)
    ].copy()
    m["kind"] = m.unit_id.astype(str).map(L._kind)
    m["cls"] = m.plant_group.astype(str)
    m["fam"] = m.cls.map(_family)
    m["w"] = 1.0 / m.groupby("hour").unit_id.transform("size")
    act = pd.read_parquet(L.ACTUAL)
    rt = act[act.year == y].sort_values("hour").rt.to_numpy()[:T]
    days = pd.date_range(f"{y}-01-01", periods=T, freq="h").normalize()
    g = _pjm_fuel_daily().reindex(days).to_numpy(float)
    m["ratio"] = m.mc.to_numpy() / g[m.hour.to_numpy()]
    res: dict = {"year": y, "repro": _repro(bundle, y), "imm": _imm_shares(y)}
    masks = {"all": np.ones(T, bool), "low": rt < L.LOW_HR * g}
    for name, mask in masks.items():
        hs = np.where(mask)[0]
        mm, n = m[m.hour.isin(hs)], len(hs)
        fam = mm.groupby("fam").w.sum()
        th = fam.reindex(["CC", "coal", "CT"]).fillna(0)
        res[name] = {
            "hours": int(n),
            "hours_with_marginal_thermal": round(mm.hour.nunique() / n, 3),
            "by_class": {
                k: round(float(v), 3)
                for k, v in (mm.groupby("cls").w.sum() / n)
                .sort_values(ascending=False)
                .head(8)
                .items()
            },
            "by_class_kind": {
                f"{a}:{b}": round(float(v), 3)
                for (a, b), v in (mm.groupby(["cls", "kind"]).w.sum() / n)
                .sort_values(ascending=False)
                .head(10)
                .items()
            },
            "fam_renorm_cc_coal_ct": {
                k: round(float(v / th.sum()), 3) for k, v in th.items()
            }
            if th.sum()
            else {},
            "share_offer_below_6p5_delivered": round(
                float(mm.w[mm.ratio < L.LOW_HR].sum() / mm.w.sum()), 3
            ),
            "coal_bit_econ_share": round(
                float(mm.w[(mm.cls == "COAL_BIT") & (mm.kind == "econ")].sum() / n), 3
            ),
            "median_marginal_offer_over_gas": round(float(mm.ratio.median()), 2),
            "median_actual_rt_over_gas": round(float(np.median(rt[hs] / g[hs])), 2),
        }
        res[name]["gap_offer_minus_rt_over_gas"] = round(
            res[name]["median_marginal_offer_over_gas"]
            - res[name]["median_actual_rt_over_gas"],
            2,
        )
    return res


def main() -> None:
    """Census every year given on the command line; write the JSON artifact."""
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for spec in sys.argv[1:]:
        y, _, b = spec.partition("=")
        r = census(Path(b), int(y))
        out[y] = r
        lo = r["low"]
        print(
            y,
            "repro",
            r["repro"]["max_abs_delta_twh"],
            "| low thermal",
            lo["hours_with_marginal_thermal"],
            "below6.5",
            lo["share_offer_below_6p5_delivered"],
            "gap",
            lo["gap_offer_minus_rt_over_gas"],
            "coal econ",
            lo["coal_bit_econ_share"],
            "| all fam",
            r["all"]["fam_renorm_cc_coal_ct"],
            "IMM",
            r["imm"]["renorm_cc_coal_ct"],
        )
    OUT.write_text(json.dumps(out, indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
