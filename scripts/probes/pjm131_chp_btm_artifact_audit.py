"""pjm-131 follow-on diagnostic — why ``chp-btm-share`` cannot supply a host share.

**Not a pre-registered test.** This probe was written *after*
``pjm131_chp_btm_precheck.py`` reported ``s_measured = 1.000`` for every covered
PJM plant, to localize that result. It carries no decision rule and decides no
verdict — it is descriptive measurement only. The session's pre-registered rules
live in ``docs/handoffs/pjm-131-gate1-arm-charter-2026-07.md`` §4, and gate 1 is
refuted there on Q3 independently of anything measured here.

What it establishes, from committed inputs only:

1. ``chp-btm-share`` is **globally degenerate** — ``btm_share == 1.0`` for every
   row of every ISO partition that curates (CAISO curates none). A share of 1.0
   means "no part of this plant's EIA-923 net generation reaches CAMPD", which
   is the signature of a CEMS-electrically-invisible plant, not a measured host
   share.

2. The cause is upstream, in ``plant_emission_rates_v2``: the curation's CHP
   signature is ``steam_load_klbh_sum > 0`` and it sums ``net_mwh`` over exactly
   those rows — but at CEMS the steam load and the electrical output are
   reported on *different units*, so those rows carry ``gross_mwh = net_mwh =
   0``. The denominator is therefore zero by construction.

3. A plant-level repair (identify the cogen at plant level, then sum ``net_mwh``
   over all the plant's units) is **not sufficient**: only a minority of cogen
   plants have any unit with ``net_mwh > 0`` at all. Repairing to that subset
   would sample only the CEMS-visible cogens — a biased basis for a fleet-wide
   capacity pull-out, and worse than the uniform sector estimate it would
   replace (CLAUDE.md rule 14's "misaligned to our representation" exception).

Consequence: ``runner.py`` resolves this artifact for **forecast** years, so a
forecast whose ISO has a curated partition pulls every covered CHP plant 100 %
behind the meter and gives it zero grid capacity. Latent rather than live —
``data/clean/`` is derived and gitignored, so it fires only once curated.

Usage:
    PYTHONPATH=. .venv/bin/python scripts/probes/pjm131_chp_btm_artifact_audit.py \
        --json-out results/calibration/pjm131_chp_btm_artifact_audit.json
"""

from __future__ import annotations

import argparse
import glob
import json
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[2]
V2 = REPO / "data" / "raw" / "_processed-legacy" / "plant_emission_rates_v2.parquet"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--json-out", default=None)
    args = ap.parse_args()

    out: dict = {}

    # ---- 1. the artifact, per ISO ----------------------------------------
    per_iso = {}
    for p in sorted(glob.glob(str(REPO / "data/clean/chp-btm-share/*/*.parquet"))):
        iso = Path(p).parent.name
        d = pd.read_parquet(p)
        per_iso[iso] = {
            "rows": int(len(d)),
            "campd_net_zero_rows": int((d["campd_net_mwh"] == 0).sum()),
            "btm_share_eq_1_rows": int((d["btm_share"] == 1.0).sum()),
            "groups": sorted(d["plant_group"].unique().tolist()),
            "eia923_net_twh": float(d["eia923_net_mwh"].sum() / 1e6),
        }
    out["artifact_by_iso"] = per_iso
    out["all_rows_degenerate"] = all(
        v["rows"] == v["btm_share_eq_1_rows"] for v in per_iso.values()
    )

    # ---- 2. the upstream cause -------------------------------------------
    v2 = pd.read_parquet(V2)
    steam = v2[v2["steam_load_klbh_sum"].astype(float) > 0.0]
    out["upstream"] = {
        "v2_rows": int(len(v2)),
        "steam_reporting_unit_years": int(len(steam)),
        "steam_reporting_with_zero_net_mwh": int((steam["net_mwh"] == 0).sum()),
        "steam_reporting_with_nonzero_net_mwh": int((steam["net_mwh"] != 0).sum()),
        "all_rows_zero_net_mwh": int((v2["net_mwh"] == 0).sum()),
    }

    # ---- 3. would a plant-level repair be enough? ------------------------
    steam_plants = set(steam["plant_id"])
    per_plant = (
        v2[v2["plant_id"].isin(steam_plants)]
        .groupby("plant_id")
        .agg(net_sum=("net_mwh", "sum"))
    )
    out["plant_level_repair"] = {
        "cogen_plants": int(len(per_plant)),
        "with_any_cems_mwh": int((per_plant["net_sum"] > 0).sum()),
        "still_zero": int((per_plant["net_sum"] == 0).sum()),
    }

    print(json.dumps(out, indent=2))
    if args.json_out:
        p = Path(args.json_out)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(out, indent=2))
        print(f"wrote {p}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
