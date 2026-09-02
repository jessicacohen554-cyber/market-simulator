"""nyiso-176 phase-0 probe: attribute the NYISO input-artifact drift.

Zero solve. Answers the four measurement gates of
``results/calibration/PREREG-nyiso176-input-artifact-reproducibility.md``:

* **R1** — is the outage extract's committed-vs-HEAD ``-40 %`` an
  *invocation-span* artifact (committed spans 2018-2026; the deriver's
  ``--years`` default is 2023-2025) rather than drift?
* **R2** — per-plant / per-unit attribution of whatever R1 leaves.
* **R3** — channel ablation on the tranche artifact: the outage-derate
  overlay (A), parasitic factors (B), fleet nameplate (C), residual (D),
  scored on ``n_match`` = rows whose ``online_hours`` agrees with the
  committed artifact to within 24 h.
* **R4** — the S A Carlson (2682) forensic: does ablation A alone restore
  its ``ST_GAS`` row to the committed 3,913 online hours?

Writes ``results/calibration/_nyiso176_input_artifact_reproducibility.json``.
Reads nothing but committed bytes plus HEAD derivations into a scratch dir;
**no committed artifact is overwritten** and no ISO but NYISO is touched
(rule 25 ``[R-ISO-SCOPE]``).
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

COMMITTED_TRANCHES = ROOT / "data/raw/_processed-legacy/thermal_tranches_NYISO.csv"
COMMITTED_OUTAGES = ROOT / "data/raw/campd-unit-outages-NYISO.csv"
S0_CONTROL = ROOT / "results/calibration/_nyiso175b_tranches_NYISO_S0_control.csv"
OUT = ROOT / "results/calibration/_nyiso176_input_artifact_reproducibility.json"
SCRATCH = ROOT / "results/calibration/_nyiso176_scratch"

YEARS = [2023, 2024, 2025]
FULL_SPAN = [2018, 2019, 2020, 2021, 2022, 2023, 2024, 2025, 2026]
KEY = ["plant_code", "plant_group"]
MATCH_TOL_HOURS = 24


# ---------------------------------------------------------------- R1 / R2


def derive_outages(years: list[int], out_path: Path) -> pd.DataFrame:
    """Run the outage deriver at HEAD over ``years``, into ``out_path``."""
    cmd = [
        sys.executable,
        "scripts/data/derive_campd_unit_outages.py",
        "--iso",
        "NYISO",
        "--years",
        *[str(y) for y in years],
        "--out",
        str(out_path),
    ]
    if out_path.exists():
        return pd.read_csv(out_path)
    env = {"PYTHONPATH": f"{ROOT}:{ROOT / 'src'}"}
    import os

    e = dict(os.environ)
    e.update(env)
    subprocess.run(cmd, cwd=ROOT, check=True, env=e, capture_output=True)
    return pd.read_csv(out_path)


def year_counts(df: pd.DataFrame) -> dict[str, int]:
    y = pd.to_datetime(df["outage_start"]).dt.year
    return {str(int(k)): int(v) for k, v in y.value_counts().sort_index().items()}


def window_key(df: pd.DataFrame) -> set[tuple]:
    return set(
        zip(
            df["facility_id"].astype(int),
            df["unit_id"].astype(str),
            df["outage_start"].astype(str),
        )
    )


def run_r1_r2() -> dict:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    committed = pd.read_csv(COMMITTED_OUTAGES)
    span = derive_outages(FULL_SPAN, SCRATCH / "outages_fullspan.csv")
    narrow = derive_outages(YEARS, SCRATCH / "outages_2023_2025.csv")

    c_yr, s_yr = year_counts(committed), year_counts(span)
    within_5 = abs(len(span) - len(committed)) <= 0.05 * len(committed)
    per_year_ok = {
        y: (
            abs(s_yr.get(y, 0) - c_yr[y]) <= 0.10 * c_yr[y]
            if c_yr[y]
            else s_yr.get(y, 0) == 0
        )
        for y in c_yr
    }
    r1_pass = bool(within_5 and all(per_year_ok.values()))

    ck, sk = window_key(committed), window_key(span)
    only_committed, only_head = ck - sk, sk - ck

    def by_plant(keys: set[tuple], df: pd.DataFrame) -> dict:
        if not keys:
            return {}
        k = list(
            zip(
                df["facility_id"].astype(int),
                df["unit_id"].astype(str),
                df["outage_start"].astype(str),
            )
        )
        sel = df.loc[[i for i, key in enumerate(k) if key in keys]]
        g = sel.groupby(["facility_id", "facility_name"]).size()
        return {
            f"{int(a)} {b}": int(v)
            for (a, b), v in g.sort_values(ascending=False).items()
        }

    return {
        "committed_windows": int(len(committed)),
        "head_fullspan_windows": int(len(span)),
        "head_2023_2025_windows": int(len(narrow)),
        "committed_by_year": c_yr,
        "head_fullspan_by_year": s_yr,
        "head_2023_2025_by_year": year_counts(narrow),
        "committed_2023_2025_subset": int(
            sum(c_yr.get(str(y), 0) for y in YEARS)
        ),
        "R1_within_5pct_total": bool(within_5),
        "R1_per_year_within_10pct": per_year_ok,
        "R1_PASS": r1_pass,
        "R2_exact_window_matches": int(len(ck & sk)),
        "R2_only_in_committed": int(len(only_committed)),
        "R2_only_at_head": int(len(only_head)),
        "R2_only_in_committed_by_plant": by_plant(only_committed, committed),
        "R2_only_at_head_by_plant": by_plant(only_head, span),
    }


# ---------------------------------------------------------------- R3 / R4


def derive_tranches(out_path: Path, ablate: str | None) -> pd.DataFrame:
    """Run the tranche deriver at HEAD over 2023-2025 with a channel ablated.

    ``ablate`` is ``"A"`` (outage-derate overlay neutralised), ``"B"``
    (parasitic factors neutralised), or ``None`` (the S-0 control).
    Executed in a subprocess so each leg gets a clean module state and the
    ``lru_cache`` on ``unit_outage_derate_factors`` cannot leak across legs.
    """
    stub = SCRATCH / f"_run_tranche_{ablate or 'S0'}.py"
    patch = ""
    if ablate == "A":
        patch = "d.unit_outage_derate_factors = lambda *a, **k: {}\n"
    elif ablate == "B":
        patch = "d._parasitic_factor_map = lambda: {}\n"
    stub.write_text(
        "import sys\n"
        f"sys.path.insert(0, {str(ROOT)!r})\n"
        f"sys.path.insert(0, {str(ROOT / 'src')!r})\n"
        "import importlib\n"
        "d = importlib.import_module('scripts.data.derive_thermal_tranches')\n"
        + patch
        + "sys.argv = ['derive', '--iso', 'NYISO', '--years', '2023', '2024', "
        f"'2025', '--out', {str(out_path)!r}]\n"
        "d.main()\n"
    )
    if out_path.exists():
        return pd.read_csv(out_path)
    import os

    e = dict(os.environ)
    e["PYTHONPATH"] = f"{ROOT}:{ROOT / 'src'}"
    subprocess.run(
        [sys.executable, str(stub)], cwd=ROOT, check=True, env=e, capture_output=True
    )
    return pd.read_csv(out_path)


def n_match(cand: pd.DataFrame, committed: pd.DataFrame) -> tuple[int, int, list]:
    """Rows whose ``online_hours`` agrees with committed to within 24 h."""
    m = committed.merge(cand, on=KEY, how="inner", suffixes=("_c", "_x"))
    delta = (m["online_hours_x"] - m["online_hours_c"]).abs()
    ok = delta <= MATCH_TOL_HOURS
    worst = (
        m.loc[~ok, KEY + ["online_hours_c", "online_hours_x"]]
        .assign(delta=delta[~ok])
        .sort_values("delta", ascending=False)
        .head(12)
    )
    return int(ok.sum()), int(len(m)), worst.to_dict("records")


def run_r3_r4() -> dict:
    SCRATCH.mkdir(parents=True, exist_ok=True)
    committed = pd.read_csv(COMMITTED_TRANCHES)
    legs: dict[str, pd.DataFrame] = {}
    legs["S0"] = (
        pd.read_csv(S0_CONTROL)
        if S0_CONTROL.exists()
        else derive_tranches(SCRATCH / "tranches_S0.csv", None)
    )
    legs["A_no_derate"] = derive_tranches(SCRATCH / "tranches_A.csv", "A")
    legs["B_no_parasitic"] = derive_tranches(SCRATCH / "tranches_B.csv", "B")

    out: dict = {"n_committed_rows": int(len(committed)), "legs": {}}
    for name, df in legs.items():
        nm, ncommon, worst = n_match(df, committed)
        out["legs"][name] = {
            "rows": int(len(df)),
            "n_match_online_hours": nm,
            "n_common": ncommon,
            "worst_online_hours_rows": worst,
        }

    base = out["legs"]["S0"]["n_match_online_hours"]
    dominant = None
    for name in ("A_no_derate", "B_no_parasitic"):
        if out["legs"][name]["n_match_online_hours"] >= 60:
            dominant = name
    out["R3_S0_baseline_n_match"] = base
    out["R3_dominant_channel"] = dominant
    out["R3_verdict"] = (
        f"DOMINANT: {dominant}" if dominant else "MULTI-CHANNEL (no ablation >= 60)"
    )

    # Channel C — fleet nameplate reconciliation, measured directly.
    m = committed.merge(legs["S0"], on=KEY, how="inner", suffixes=("_c", "_x"))
    np_moved = m.loc[
        (m["nameplate_mw_x"] - m["nameplate_mw_c"]).abs() > 0.05,
        KEY + ["nameplate_mw_c", "nameplate_mw_x"],
    ]
    out["R3_channel_C_nameplate_rows"] = np_moved.to_dict("records")

    # R4 — S A Carlson (2682) ST_GAS.
    def carlson(df: pd.DataFrame) -> dict:
        r = df[(df["plant_code"] == 2682)]
        return {
            f"{row.plant_group}": {
                "online_hours": int(row.online_hours),
                "median_cf": (
                    None if pd.isna(row.median_cf) else float(row.median_cf)
                ),
                "nameplate_mw": float(row.nameplate_mw)
                if "nameplate_mw" in df.columns and not pd.isna(row.nameplate_mw)
                else None,
                "status": str(row.status) if "status" in df.columns else None,
            }
            for row in r.itertuples()
        }

    c_st = carlson(committed).get("ST_GAS", {})
    a_st = carlson(legs["A_no_derate"]).get("ST_GAS", {})
    ref = c_st.get("online_hours")
    got = a_st.get("online_hours")
    out["R4"] = {
        "committed": carlson(committed),
        "S0": carlson(legs["S0"]),
        "A_no_derate": carlson(legs["A_no_derate"]),
        "B_no_parasitic": carlson(legs["B_no_parasitic"]),
        "R4_PASS": bool(
            ref and got is not None and abs(got - ref) <= 0.10 * ref
        ),
    }
    return out


def main() -> None:
    res = {"prereg": "PREREG-nyiso176-input-artifact-reproducibility.md"}
    res["R1_R2_outage_extract"] = run_r1_r2()
    res["R3_R4_tranche_artifact"] = run_r3_r4()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, indent=2, sort_keys=True, default=str))
    print(f"wrote {OUT}")
    print(json.dumps(res["R1_R2_outage_extract"], indent=2, default=str)[:2000])
    print(json.dumps(res["R3_R4_tranche_artifact"], indent=2, default=str)[:3000])


if __name__ == "__main__":
    main()
