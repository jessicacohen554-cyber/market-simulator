"""ERCOT-163 Phase 0 addendum — the ERCOT-151 DAM offline-CC block, config-collapsed.

NO LP, no solve, keeper UNCHANGED.

ERCOT-151 §0.2/§0.4 measured, on the **60-Day DAM Gen Resource** disclosure at
the 91 missed 2023 >$300 tail hours, ``10.3 GW of startable-but-OFF CC (8.2 GW
of it <= $200)`` and made that block the object ERCOT-152/158 were pointed at.
The RT-telemetry census (``ercot163_cc_commitment_state_census.py``) measures
**0.018 GW** of offline-startable CC at the top-100 gap hours — a 500x
discrepancy that cannot be a sampling difference. This probe resolves it on the
same DAM rows ERCOT-151 read.

**The mechanism of the discrepancy.** A combined-cycle train submits one DAM row
per **configuration** (``<TRAIN>_<config>``: ``BASTEN_CC1_1``, ``BASTEN_CC1_2``,
...). Exactly one configuration can be the operating point, so every OTHER
configuration of an operating train carries ``Resource Status = OFF`` with its
own full configuration HSL. Summing OFF-status HSL at resource-name grain
therefore counts the *alternative configurations of trains that are themselves
running* as idle startable capacity. The physically startable increment of an ON
train is only ``max_config_HSL - HSL(operating config)`` — the cost of moving up
a configuration, not a whole extra plant.

This probe reports, at the same hour keys, both grains:

* ``name_grain``   — ERCOT-151's construction, verbatim (sum HSL of OFF rows).
* ``train_grain``  — trains collapsed on the ``_<config>`` suffix. A train with
  any ON/ONRUC/... configuration is ON; its startable increment is its own
  ``max config HSL - ON config HSL``. Only trains with NO online configuration
  contribute their full HSL to the offline block.

Usage::

    PYTHONPATH=.:src python3 scripts/probes/ercot163_dam_config_collapse.py
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
for _p in (REPO, REPO / "src", REPO / "scripts", REPO / "scripts" / "data"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

DAM_GLOB = "60_DAY_DAM_DISCLOSURE_60d_DAM_Gen_Resource_Data_2023_*.parquet"
PHASE0_JSON = REPO / "results/calibration/_ercot161_wall_phase0.json"
DEFAULT_OUT = REPO / "results/calibration/_ercot163_dam_config_collapse.json"
YEAR = 2023

GAS_TYPES = {
    "CCGT90": "CC",
    "CCLE90": "CC",
    "SCGT90": "CT",
    "SCLE90": "CT",
    "GSREH": "ST",
    "GSNONR": "ST",
    "GSSUP": "ST",
}

#: ERCOT-151's own status partition, kept verbatim so the name-grain leg
#: reproduces its number rather than a re-specified one.
ON_STATUSES = ("ON", "ONREG", "ONDSR", "ONRUC", "ONRR", "ONOS", "ONEMR")
OFF_STARTABLE = ("OFF", "OFFQS", "OFFNS")
OUT_STATUSES = ("OUT", "OUTL", "EMR", "EMRSWGR")

#: A combined-cycle DAM resource name is ``<TRAIN>_<configuration index>``; the
#: train is the name with that trailing numeric segment removed. Simple-cycle
#: and steam names have no configuration segment and are their own train.
_CONFIG_SUFFIX = re.compile(r"_(\d+)$")

_MW_COLS = [f"QSE submitted Curve-MW{i}" for i in range(1, 11)]
_PR_COLS = [f"QSE submitted Curve-Price{i}" for i in range(1, 11)]


def _train(name: str) -> str:
    """``BASTEN_CC1_2`` -> ``BASTEN_CC1``; names without a config index unchanged."""
    return _CONFIG_SUFFIX.sub("", str(name))


def _keys(hours: np.ndarray) -> set[tuple[str, int]]:
    """Model hours-of-year -> the DAM ``(delivery date, hour ending)`` keys."""
    idx = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")
    return {(idx[h].strftime("%Y-%m-%d"), idx[h].hour + 1) for h in hours}


def _load(keys: set[tuple[str, int]]) -> pd.DataFrame:
    """Gas DAM Gen Resource rows at ``keys``, numerics coerced."""
    frames = []
    for path in sorted((REPO / "data/raw/ercot").glob(DAM_GLOB)):
        f = pd.read_parquet(path)
        f["he"] = pd.to_numeric(
            f["Hour Ending"].astype(str).str.split(":").str[0], errors="coerce"
        )
        f["date"] = pd.to_datetime(f["Delivery Date"], errors="coerce")
        f["key"] = list(zip(f["date"].dt.strftime("%Y-%m-%d"), f["he"]))
        f = f[f["key"].isin(keys) & f["Resource Type"].isin(GAS_TYPES)]
        if not f.empty:
            frames.append(f)
    df = pd.concat(frames, ignore_index=True)
    for c in ["HSL", "LSL"] + _MW_COLS + _PR_COLS:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")
    df["cls"] = df["Resource Type"].map(GAS_TYPES)
    df["status"] = df["Resource Status"].astype(str).str.strip().str.upper()
    df["train"] = df["Resource Name"].map(_train)
    return df


def _mw_le(df: pd.DataFrame, thresh: float) -> np.ndarray:
    """Submitted DAM curve MW offered at or below ``thresh`` (last such step)."""
    MW = df[_MW_COLS].to_numpy(float)
    PR = df[_PR_COLS].to_numpy(float)
    ok = np.isfinite(MW) & np.isfinite(PR) & (PR <= thresh)
    return np.where(ok, MW, 0.0).max(axis=1)


def _census(df: pd.DataFrame, n_keys: int) -> dict:
    """Both grains of the offline/online split, per class, mean GW per hour key."""
    is_on = df["status"].isin(ON_STATUSES)
    is_off = df["status"].isin(OFF_STARTABLE)
    is_out = df["status"].isin(OUT_STATUSES)

    name_grain = {}
    for cls, d in df.groupby("cls"):
        m_on, m_off, m_out = is_on[d.index], is_off[d.index], is_out[d.index]
        name_grain[str(cls)] = {
            "on_gw": round(float(d.loc[m_on, "HSL"].sum()) / n_keys / 1e3, 3),
            "off_startable_gw": round(
                float(d.loc[m_off, "HSL"].sum()) / n_keys / 1e3, 3
            ),
            "off_startable_le200_gw": round(
                float(_mw_le(d.loc[m_off], 200.0).sum()) / n_keys / 1e3, 3
            ),
            "out_gw": round(float(d.loc[m_out, "HSL"].sum()) / n_keys / 1e3, 3),
            "n_rows_per_key": round(len(d) / n_keys, 1),
        }

    # Train grain: collapse configurations within (key, train).
    df = df.assign(
        _on=is_on,
        _off=is_off,
        _out=is_out,
        _hsl_on=np.where(is_on, df["HSL"].to_numpy(float), 0.0),
    )
    tr = (
        df.groupby(["key", "cls", "train"], sort=False)
        .agg(
            hsl_max=("HSL", "max"),
            hsl_on=("_hsl_on", "max"),
            any_on=("_on", "any"),
            all_out=("_out", "all"),
            n_cfg=("HSL", "size"),
        )
        .reset_index()
    )
    # Offline-startable capability at train grain:
    #   * train with an ON configuration -> only its config-uprate headroom
    #   * train fully offline (and not all-OUT) -> its full max-config HSL
    tr["startable_gw"] = np.where(
        tr["any_on"],
        np.maximum(tr["hsl_max"] - tr["hsl_on"], 0.0),
        np.where(tr["all_out"], 0.0, tr["hsl_max"]),
    )
    train_grain = {}
    for cls, d in tr.groupby("cls"):
        on = d.loc[d["any_on"], "hsl_on"].sum()
        train_grain[str(cls)] = {
            "on_gw": round(float(on) / n_keys / 1e3, 3),
            "off_startable_gw": round(float(d["startable_gw"].sum()) / n_keys / 1e3, 3),
            "of_which_config_uprate_of_running_train_gw": round(
                float(d.loc[d["any_on"], "startable_gw"].sum()) / n_keys / 1e3, 3
            ),
            "of_which_wholly_offline_train_gw": round(
                float(d.loc[~d["any_on"], "startable_gw"].sum()) / n_keys / 1e3, 3
            ),
            "n_trains_per_key": round(len(d) / n_keys, 1),
            "mean_configs_per_train": round(float(d["n_cfg"].mean()), 2),
        }
    return {"name_grain": name_grain, "train_grain": train_grain}


def _sced_train_states(hours: np.ndarray) -> pd.DataFrame:
    """Per (hour-of-year, train) RT telemetered CC state from the SCED corpus.

    The SCED and DAM disclosures share the resource-name namespace
    (``BASTEN_CC1_2``), so stripping the configuration segment from both sides
    yields a joinable train key. SCED publishes only the OPERATING
    configuration of a train, so a train's RT capability is the telemetered
    HSL of whatever row is present.
    """
    from derive_ercot_dam_cleared_share import _MONTH_START_HOUR
    from derive_ercot_sced_offer_wall import _delivery_year_rows, _sced_source_files

    keep = set(int(h) for h in hours)
    cols = [
        "SCED Time Stamp",
        "Resource Name",
        "Resource Type",
        "Telemetered Resource Status",
        "HSL",
        "Base Point",
    ]
    frames = []
    for path in _sced_source_files(YEAR):
        f = pd.read_parquet(path, columns=cols)
        f = _delivery_year_rows(f, YEAR)
        f = f[f["Resource Type"].isin(("CCGT90", "CCLE90"))].copy()
        if f.empty:
            continue
        ts = pd.to_datetime(f["SCED Time Stamp"])
        cst = ts.dt.tz_localize(
            "America/Chicago", ambiguous=True, nonexistent="shift_forward"
        ).dt.tz_convert("Etc/GMT+6")
        f["hoy"] = (
            _MONTH_START_HOUR[cst.dt.month.to_numpy() - 1]
            + (cst.dt.day.to_numpy() - 1) * 24
            + cst.dt.hour.to_numpy()
        )
        f = f[f["hoy"].isin(keep)]
        if f.empty:
            continue
        for c in ("HSL", "Base Point"):
            f[c] = pd.to_numeric(f[c], errors="coerce").fillna(0.0)
        f["train"] = f["Resource Name"].map(_train)
        f["rt_status"] = (
            f["Telemetered Resource Status"].astype(str).str.strip().str.upper()
        )
        frames.append(f[["hoy", "train", "rt_status", "HSL", "Base Point"]])
    sced = pd.concat(frames, ignore_index=True)
    # One row per (hour, train): the hour's mean over its 5-minute intervals,
    # with the modal telemetered status.
    g = sced.groupby(["hoy", "train"], sort=False)
    out = g.agg(rt_hsl=("HSL", "mean"), rt_bp=("Base Point", "mean")).reset_index()
    out["rt_status"] = g["rt_status"].agg(lambda s: s.mode().iloc[0]).to_numpy()
    out["rt_state"] = np.select(
        [
            out["rt_status"].str.startswith("ONTEST"),
            out["rt_status"].str.startswith("ON"),
            out["rt_status"].isin(("OFFQS", "OFFNS")),
            out["rt_status"].str.startswith("OFF"),
            out["rt_status"].str.startswith("OUT"),
        ],
        ["ONTEST", "ONLINE", "OFFLINE_STARTABLE", "OFFLINE_OTHER", "OUT"],
        default="OTHER",
    )
    return out


def _dam_vs_rt(df: pd.DataFrame, hours: np.ndarray, n_keys: int) -> dict:
    """Cross-tab the DAM-declared CC train state against its RT telemetered state.

    Answers the ERCOT-163 question directly: of the CC capability the 60-Day DAM
    disclosure shows as ``OFF`` at these hours — the block ERCOT-151 handed
    forward as the model's phantom cheap depth — how much was, in real time,
    already ONLINE and dispatched rather than idle and startable?
    """
    idx = pd.date_range(f"{YEAR}-01-01", periods=8760, freq="h")
    key_to_hoy = {(idx[h].strftime("%Y-%m-%d"), idx[h].hour + 1): int(h) for h in hours}
    cc = df[df["cls"] == "CC"].assign(
        _on=df["status"].isin(ON_STATUSES),
        _out=df["status"].isin(OUT_STATUSES),
    )
    cc = cc.assign(_hsl_on=np.where(cc["_on"], cc["HSL"].to_numpy(float), 0.0))
    tr = (
        cc.groupby(["key", "train"], sort=False)
        .agg(
            hsl_max=("HSL", "max"),
            hsl_on=("_hsl_on", "max"),
            any_on=("_on", "any"),
            all_out=("_out", "all"),
        )
        .reset_index()
    )
    tr["hoy"] = tr["key"].map(key_to_hoy)
    tr = tr.dropna(subset=["hoy"])
    tr["hoy"] = tr["hoy"].astype(int)
    tr["dam_state"] = np.where(
        tr["any_on"], "DAM_ON", np.where(tr["all_out"], "DAM_OUT", "DAM_OFF")
    )
    # The DAM-declared capability the block is credited with: a DAM_ON train
    # contributes only its config-uprate headroom, a DAM_OFF train its full
    # max-config HSL (the ERCOT-151 crediting, corrected to train grain).
    tr["dam_offline_gw"] = np.where(
        tr["any_on"],
        np.maximum(tr["hsl_max"] - tr["hsl_on"], 0.0),
        np.where(tr["all_out"], 0.0, tr["hsl_max"]),
    )

    rt = _sced_train_states(hours)
    j = tr.merge(rt, on=["hoy", "train"], how="left")
    j["rt_state"] = j["rt_state"].fillna("RT_ABSENT")
    j[["rt_hsl", "rt_bp"]] = j[["rt_hsl", "rt_bp"]].fillna(0.0)

    cross: dict = {}
    for (d, r), g in j.groupby(["dam_state", "rt_state"]):
        cross.setdefault(d, {})[r] = {
            "dam_declared_offline_gw": round(
                float(g["dam_offline_gw"].sum()) / n_keys / 1e3, 4
            ),
            "rt_telemetered_hsl_gw": round(float(g["rt_hsl"].sum()) / n_keys / 1e3, 4),
            "rt_dispatched_gw": round(float(g["rt_bp"].sum()) / n_keys / 1e3, 4),
            "n_train_hours": int(len(g)),
        }
    off = j[j["dam_state"] == "DAM_OFF"]
    off_gw = float(off["dam_offline_gw"].sum()) / n_keys / 1e3
    online = off[off["rt_state"].isin(("ONLINE", "ONTEST"))]
    return {
        "crosstab": cross,
        "dam_off_cc_block_gw": round(off_gw, 4),
        "of_which_rt_online_gw_dam_basis": round(
            float(online["dam_offline_gw"].sum()) / n_keys / 1e3, 4
        ),
        "of_which_rt_online_share": round(
            float(online["dam_offline_gw"].sum())
            / max(float(off["dam_offline_gw"].sum()), 1e-9),
            4,
        ),
        "rt_dispatch_of_the_dam_off_block_gw": round(
            float(off["rt_bp"].sum()) / n_keys / 1e3, 4
        ),
        "rt_genuinely_idle_gw": round(
            float(
                off.loc[
                    off["rt_state"].isin(
                        ("OFFLINE_STARTABLE", "OFFLINE_OTHER", "RT_ABSENT")
                    ),
                    "dam_offline_gw",
                ].sum()
            )
            / n_keys
            / 1e3,
            4,
        ),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = ap.parse_args()

    phase0 = json.loads(PHASE0_JSON.read_text())
    gap = np.array(sorted(int(h) for h in phase0["hour_set"]["hours"]))

    # ERCOT-151's own hour set: actual RT > $300 with the ercot150b keeper's
    # load-weighted model price < $200. Reproduced from committed artifacts so
    # the name-grain leg is scored on the SAME hours ERCOT-151 reported.
    sysf = pd.read_parquet(
        REPO / "results/calibration/ercot150_zonalanchor_B/hourly/system_2023.parquet"
    )
    if sysf["pass"].nunique() > 1:
        sysf = sysf[sysf["pass"] == sysf["pass"].max()]
    mp = (
        sysf.groupby("hour")
        .apply(
            lambda x: float(
                np.average(x["price"], weights=x["demand"].clip(lower=1e-9))
            ),
            include_groups=False,
        )
        .reindex(range(8760))
        .to_numpy(float)
    )
    act = pd.read_parquet(
        REPO / "data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet"
    )
    a23 = (
        act[act["year"] == YEAR]
        .set_index("hour")["rt"]
        .reindex(range(8760))
        .to_numpy(float)
    )
    tail = np.flatnonzero(a23 > 300.0)
    missed = np.array([h for h in tail if mp[h] < 200.0])

    out = {
        "_provenance": {
            "probe": "scripts/probes/ercot163_dam_config_collapse.py",
            "session": "ercot-163 Phase 0 addendum (no LP, no solve)",
            "source": "60-Day DAM Gen Resource disclosure, delivery-2023",
            "reproduces": "results/calibration/ercot151_offline_phase0.json",
            "train_rule": "resource name with a trailing _<config> segment removed",
            "year": YEAR,
        },
        "hour_sets": {
            "ercot151_missed_tail": int(len(missed)),
            "ercot163_gap_top100": int(len(gap)),
        },
    }
    for label, hours in (
        ("ercot151_missed_tail", missed),
        ("ercot163_gap_top100", gap),
    ):
        keys = _keys(hours)
        df = _load(keys)
        out[label] = _census(df, len(keys))
        out[label]["dam_vs_rt"] = _dam_vs_rt(df, hours, len(keys))
        cc_n = out[label]["name_grain"].get("CC", {})
        cc_t = out[label]["train_grain"].get("CC", {})
        dv = out[label]["dam_vs_rt"]
        print(
            f"{label}: CC off-startable  name-grain {cc_n.get('off_startable_gw')} GW"
            f"  ->  train-grain {cc_t.get('off_startable_gw')} GW"
            f"  (uprate {cc_t.get('of_which_config_uprate_of_running_train_gw')} /"
            f" wholly-offline {cc_t.get('of_which_wholly_offline_train_gw')};"
            f" {cc_t.get('mean_configs_per_train')} configs/train)"
        )
        print(
            f"    DAM_OFF CC block {dv['dam_off_cc_block_gw']} GW -> RT ONLINE"
            f" {dv['of_which_rt_online_gw_dam_basis']} GW"
            f" ({dv['of_which_rt_online_share']:.1%}), RT dispatch of that block"
            f" {dv['rt_dispatch_of_the_dam_off_block_gw']} GW, genuinely idle"
            f" {dv['rt_genuinely_idle_gw']} GW"
        )

    args.out.write_text(json.dumps(out, indent=1))
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
