"""miso-245 S-3(b') — the repaired clean-A/B gate, declared before its numbers
existed in
``results/calibration/ADDENDUM-miso245-my-own-gate-S3b-failed-and-the-repair-is-the-strictest-satisfiable-form-2026-09-08.md``
§2.  ZERO LP, read-only, repairs nothing.

Every field on which the ARM's ``scenario_config`` differs from the KEEPER's
must fall into one of exactly TWO closed classes, each MEASURED:

  (P) PER-YEAR      — the arm's value is what the keeper's OWN recipe produces
                      for 2024 AND the keeper's recorded value is what that same
                      recipe produces for 2023, both via
                      ``pipeline.backcast_config.backcast_config``.
  (N) NEW-FIELD     — the field is ABSENT from the keeper's scenario_config, the
                      arm's value equals the ScenarioConfig dataclass DEFAULT,
                      and the field is one miso-244's G-DRIFT already measured
                      or classified INERT for MISO backcast.

Any differing field in neither class STOPS the arm.  The COUNT of differing
fields is not a bar and is never widened.
"""

from __future__ import annotations

import argparse
import dataclasses
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))
sys.path.insert(0, str(REPO))

KEEPER = REPO / "results/calibration/miso243_sppair_K"

#: Class (N) is CLOSED: only these two fields may be excused as new-field
#: defaults, and only at their dataclass default.  Each carries miso-244's own
#: measured/classified INERT finding as its citation.
_NEW_FIELD_INERT_CITATION = {
    "netload_drag_layup_window_mask": (
        "miso-244 G-DRIFT, MEASURED not classified from its gate: "
        "_resolve_drag_layup_shares(keeper_config, 'MISO', y, 8760) returns len 0 "
        "in 2023, 2024 and 2025"
    ),
    "pjm_thermal_accreditation_vintage": (
        "miso-244 G-DRIFT: capx D84 PJM thermal-ELCC accreditation, on the "
        "capacity-evolution path a mode='backcast' run never enters"
    ),
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--arm", required=True)
    ap.add_argument("--out", default="results/calibration/_miso245_s3b_prime.json")
    args = ap.parse_args()

    from market_sim.config.scenarios import ScenarioConfig
    from market_sim.pipeline.backcast_config import backcast_config
    from scripts.run_calibration import _henry_hub_actual, _load_reference

    kc = json.loads((KEEPER / "run_config.json").read_text())["scenario_config"]
    ac = json.loads((Path(args.arm) / "run_config.json").read_text())["scenario_config"]
    diff = sorted(k for k in set(kc) | set(ac) if kc.get(k) != ac.get(k))

    ref = _load_reference()
    hours = 8760
    per_year = {}
    for y in (2023, 2024):
        gp = _henry_hub_actual(ref, y)
        cfg = backcast_config(y, "MISO", hours, gp)
        per_year[y] = {"cfg": cfg, "henry_hub": float(gp)}

    defaults = {
        f.name: (f.default if f.default is not dataclasses.MISSING else None)
        for f in dataclasses.fields(ScenarioConfig)
    }

    rows = []
    unexplained = []
    for k in diff:
        kv, av = kc.get(k), ac.get(k)
        row = {"field": k, "keeper": kv, "arm": av, "class": None}
        # (P) per-year: the keeper's own recipe reproduces BOTH recorded values.
        p23 = getattr(per_year[2023]["cfg"], k, "<<missing>>")
        p24 = getattr(per_year[2024]["cfg"], k, "<<missing>>")
        if p23 != "<<missing>>" and p23 == kv and p24 == av:
            row["class"] = "P"
            row["evidence"] = (
                f"backcast_config(2023,'MISO')={p23!r} reproduces the keeper's "
                f"record; backcast_config(2024,'MISO')={p24!r} reproduces the arm's"
            )
        # (N) new-field default: absent from the keeper, arm == dataclass default,
        #     and the field is in the CLOSED inert list.
        elif k not in kc and k in _NEW_FIELD_INERT_CITATION and av == defaults.get(k):
            row["class"] = "N"
            row["dataclass_default"] = defaults.get(k)
            row["evidence"] = _NEW_FIELD_INERT_CITATION[k]
        else:
            row["backcast_config_2023"] = p23 if p23 != "<<missing>>" else None
            row["backcast_config_2024"] = p24 if p24 != "<<missing>>" else None
            row["dataclass_default"] = defaults.get(k)
            unexplained.append(k)
        rows.append(row)

    rep = {
        "probe": "miso-245 S-3(b') — the repaired clean-A/B gate (STRUCTURAL, STOP-only)",
        "addendum": (
            "results/calibration/ADDENDUM-miso245-my-own-gate-S3b-failed-"
            "and-the-repair-is-the-strictest-satisfiable-form-2026-09-08.md §2"
        ),
        "keeper": str(KEEPER),
        "arm": args.arm,
        "henry_hub_actual": {str(y): per_year[y]["henry_hub"] for y in per_year},
        "n_fields_keeper": len(kc),
        "n_fields_arm": len(ac),
        "n_differing": len(diff),
        "fields": rows,
        "unexplained": unexplained,
        "PASS": not unexplained,
    }
    Path(args.out).write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
