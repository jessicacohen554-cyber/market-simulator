"""miso-138 addendum — WHY the pre-committed REFUTED verdict fired.

Diagnostic only. It changes no pre-registered threshold and re-cuts no
decision (PREREG K4); it measures the mechanism behind the verdict already
returned by ``_miso138_da_co_class_bridge.py``:

* the **feature-basis** comparison -- the unconditional distribution of the two
  shape features in the corpus against the same quantities in EIA-860, by TRUE
  class on the EIA-860 side. Unconditional on both sides, so nothing here is
  contaminated by the classifier's own output.
* the **G-1 confusion matrix** on ground truth in the held-out non-MISO
  population -- which classes the three features cannot tell apart even when
  the answer is known.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _miso138_da_co_class_bridge import (  # noqa: E402
    ALL_CLASSES,
    apply_screens,
    corpus_unit_features,
    eia860_at_grain,
    gnb_fit,
    gnb_predict,
    load_eia860,
)
from _miso138_fetch_da_co import SAMPLE_DAYS  # noqa: E402

FLAT = 0.01  # |derate| below this is an exactly-flat seasonal declaration


def quantiles(values: np.ndarray) -> dict:
    """p10/p50/p90 plus the flat-declaration share, on finite values only."""
    v = values[np.isfinite(values)]
    if not len(v):
        return {"n": 0}
    return {
        "n": int(len(v)),
        "p10": float(np.percentile(v, 10)),
        "p50": float(np.percentile(v, 50)),
        "p90": float(np.percentile(v, 90)),
        "share_flat": float((np.abs(v) < FLAT).mean()),
    }


def main() -> int:
    """Measure the feature-basis gap and the ground-truth confusion."""
    repo = Path(__file__).resolve().parents[2]
    scratch = Path(sys.argv[1])
    raw860 = load_eia860(repo)
    fleet = eia860_at_grain(raw860, "generator")

    out: dict = {"note": "diagnostic addendum to _miso138_da_co_class_bridge.json"}

    # --- (1) feature basis: corpus (unconditional) vs EIA-860 MISO (by TRUE class)
    miso860 = fleet[fleet["is_miso"] & fleet["klass"].isin(ALL_CLASSES)]
    out["eia860_miso_by_true_class"] = {
        k: {
            "derate": quantiles(miso860.loc[miso860["klass"] == k, "derate"].to_numpy(float)),
            "minfrac": quantiles(miso860.loc[miso860["klass"] == k, "minfrac"].to_numpy(float)),
        }
        for k in ALL_CLASSES
    }
    out["eia860_miso_all"] = {
        "derate": quantiles(miso860["derate"].to_numpy(float)),
        "minfrac": quantiles(miso860["minfrac"].to_numpy(float)),
    }

    corpus_years = {}
    for year, days in SAMPLE_DAYS.items():
        units = corpus_unit_features(scratch, year, days)
        kept, _ = apply_screens(units)
        corpus_years[str(year)] = {
            "derate": quantiles(kept["derate"].to_numpy(float)),
            "minfrac": quantiles(kept["minfrac"].to_numpy(float)),
            # A capability that never moves within a day either: the ambient
            # signal a real thermal unit carries hour to hour.
            "within_day_cv": quantiles(kept["cv"].to_numpy(float)),
        }
    out["corpus_unconditional"] = corpus_years

    # --- (2) G-1 confusion on ground truth, held-out non-MISO population
    train = fleet[(~fleet["is_miso"]) & fleet["klass"].isin(ALL_CLASSES)].dropna(
        subset=["logcap", "derate", "minfrac"]
    )
    x = train[["logcap", "derate", "minfrac"]].to_numpy(float)
    y = train["klass"].to_numpy()
    model = gnb_fit(x, y, ALL_CLASSES, uniform_prior=False)
    pred = gnb_predict(model, x)
    out["g1_confusion_nonmiso"] = {
        truth: {
            p: int(((y == truth) & (pred == p)).sum()) for p in ALL_CLASSES
        }
        for truth in ALL_CLASSES
    }
    # Same three features, but with the seasonal-derate leg removed: how much of
    # the identification was ever carried by size and min-load alone?
    for subset in (["logcap"], ["logcap", "minfrac"], ["logcap", "derate"]):
        xs = train[subset].to_numpy(float)
        m = gnb_fit(xs, y, ALL_CLASSES, uniform_prior=False)
        p = gnb_predict(m, xs)
        recalls = [float((p[y == k] == k).mean()) for k in ALL_CLASSES]
        out.setdefault("g1_feature_ablation", {})["+".join(subset)] = {
            "balanced_accuracy_insample": float(np.mean(recalls)),
            "per_class_recall": dict(zip(ALL_CLASSES, recalls, strict=False)),
        }

    dest = repo / "results/calibration/_miso138_bridge_diagnostics.json"
    dest.write_text(json.dumps(out, indent=1, default=float))
    print(f"wrote {dest}")
    print(json.dumps(out["corpus_unconditional"], indent=1, default=float))
    print(json.dumps(out["eia860_miso_by_true_class"], indent=1, default=float))
    print(json.dumps(out["g1_confusion_nonmiso"], indent=1))
    print(json.dumps(out["g1_feature_ablation"], indent=1, default=float))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
