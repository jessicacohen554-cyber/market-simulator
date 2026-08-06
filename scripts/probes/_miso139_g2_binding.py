"""miso-139 — G-2 binding, measured on the keeper's OWN committed sidecars.

PREREG ``PREREG-miso139-ambient-derate-class-scope-2026-08-06.md`` @ ``6263f43d``,
§5.  No LP is solved: class dispatch comes from the committed
``hourly/class_hourly_<year>.parquet`` (P1) and class capability from the model's
own availability matrix, rebuilt with the keeper config exactly as in
``_miso139_derate_gates.py``.

The licensing question is NOT "does the derate remove MW" — it always does.  It
is whether the removal exceeds the class's OWN unloaded headroom in the hour, so
the class is actually forced DOWN and the marginal unit can change.  A derate
that only eats slack changes nothing (miso-134: BINDING IS NOT LICENSING).

Reported per convention, for the miso-137 windows summer h12-17 AND summer
h00-05 (PREREG §6 Trap 3: the night is reported beside the afternoon, always).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

from market_sim.config.iso_configs import get_iso_config  # noqa: E402
from market_sim.data.fleet import (  # noqa: E402
    generators_to_fleet_arrays,
    load_fleet_from_csv,
)

sys.path.insert(0, str(REPO / "scripts" / "probes"))
from _miso139_derate_gates import (  # noqa: E402
    SUMMER_MONTHS,
    W_AFT,
    W_NIGHT,
    _hour_month,
    _hour_of_day,
    keeper_config,
    with_scope,
)

ISO = "MISO"
YEARS = (2023, 2024, 2025)
KEEPER = REPO / "results/calibration/miso132_ccmin_B"
GATES = REPO / "results/calibration/_miso139_derate_gates.json"
OUT = REPO / "results/calibration/_miso139_g2_binding.json"

ARMED = ("CT_PEAKER", "CC_REGULAR")
COMMITTED_SCOPE = ("CT_CHP", "ST_CHP")


def class_capability(year: int, cfg) -> dict[str, np.ndarray]:
    """Hourly class capability (MW) = sum over units of pmax * availability."""
    gens = load_fleet_from_csv(
        ISO,
        get_iso_config(ISO),
        year=year,
        measured_ct_heat_rates=bool(getattr(cfg, "measured_ct_heat_rates", False)),
        measured_chp_heat_rates=bool(getattr(cfg, "measured_chp_heat_rates", False)),
        cc_steam_part_capacity=bool(getattr(cfg, "cc_steam_part_capacity", False)),
        cc_steam_part_reclass=bool(getattr(cfg, "cc_steam_part_reclass", False)),
    )
    zones = [z.name for z in get_iso_config(ISO).zones]
    fa = generators_to_fleet_arrays(gens, zones, 8760, iso=ISO, config=cfg, year=year)
    groups = np.array([g.plant_group for g in gens])
    cap = fa.pmax[:, None] * fa.availability
    return {c: cap[groups == c].sum(axis=0) for c in set(groups) if c}


def main() -> None:
    slopes = json.loads(GATES.read_text())["g1_miso_own_slopes"]
    hod, mon = _hour_of_day(8760), _hour_month(8760)
    summer = np.isin(mon, SUMMER_MONTHS)
    windows = {
        "summer_aft": summer & np.isin(hod, W_AFT),
        "summer_night": summer & np.isin(hod, W_NIGHT),
        "summer_all": summer,
    }
    out: dict = {
        "prereg": "PREREG-miso139-... @ 6263f43d, §5",
        "keeper": "2026-08-05-miso-132b-cc-committed",
        "note": (
            "binding := derate removal exceeds the class's own unloaded headroom "
            "in that hour, so the class is forced DOWN. A removal inside headroom "
            "eats slack and cannot change the marginal unit."
        ),
        "years": {},
    }
    for y in YEARS:
        base = keeper_config(y)
        ctrl = class_capability(y, base)
        convs = {
            "A_misoslope": with_scope(
                base, COMMITTED_SCOPE + ARMED, True, {c: slopes[c] for c in ARMED}
            ),
            "B_misoslope": with_scope(
                base, COMMITTED_SCOPE + ARMED, False, {c: slopes[c] for c in ARMED}
            ),
        }
        ch = pd.read_parquet(KEEPER / f"hourly/class_hourly_{y}.parquet")
        ch = ch[ch["pass"] == "P1"]
        disp = {
            str(k): g.sort_values("hour")["mw"].to_numpy()[:8760]
            for k, g in ch.groupby("klass", observed=True)
        }
        yrec: dict = {"classes": {}}
        for cname, cfg_v in convs.items():
            arm = class_capability(y, cfg_v)
            for cls in ARMED:
                d = disp.get(cls)
                if d is None or len(d) < 8760:
                    continue
                head = ctrl[cls] - d
                rem = ctrl[cls] - arm[cls]
                rec = yrec["classes"].setdefault(cls, {})
                for wname, m in windows.items():
                    binding = rem[m] > head[m]
                    rec[f"{cname}|{wname}"] = {
                        "hours": int(m.sum()),
                        "mean_capability_mw": float(ctrl[cls][m].mean()),
                        "mean_dispatch_mw": float(d[m].mean()),
                        "mean_headroom_mw": float(head[m].mean()),
                        "p10_headroom_mw": float(np.percentile(head[m], 10)),
                        "min_headroom_mw": float(head[m].min()),
                        "mean_removal_mw": float(rem[m].mean()),
                        "binding_hours": int(binding.sum()),
                        "binding_share": float(binding.mean()),
                        "forced_down_mwh": float(
                            np.maximum(rem[m] - head[m], 0.0).sum()
                        ),
                    }
        # cheaper-than-peaker cushion: unloaded coal + CC capability in the window
        coal_cap = sum(ctrl.get(c, 0.0) for c in ("COAL",))
        coal_disp = sum(
            disp.get(c, np.zeros(8760))
            for c in ("COAL_PRB", "COAL_BIT", "COAL_LIGNITE")
        )
        cc_head = ctrl["CC_REGULAR"] - disp.get("CC_REGULAR", np.zeros(8760))
        yrec["cushion"] = {
            w: {
                "coal_unloaded_mw_mean": float((coal_cap - coal_disp)[m].mean()),
                "cc_unloaded_mw_mean": float(cc_head[m].mean()),
            }
            for w, m in windows.items()
        }
        out["years"][str(y)] = yrec
    OUT.write_text(json.dumps(out, indent=2, default=str))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
