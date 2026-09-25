"""COAL-SUB byte-identity proof: diff two sets of fleet snapshots row by row (zero LP).

Owner instruction 2026-09-25 (verbatim): *"we need to completely eliminate the
class Coal From the model altogether all coal should be sorted into its
subclass"*. The change is correct only if every coal unit that was ALREADY
subclass-resolved dispatches byte-identically, and the only movers are the
units the census lists in the former generic ``COAL`` bucket. This compares a
BEFORE and an AFTER directory of :mod:`coal_subclass_snapshot` outputs.

Per ISO-year it checks:

* the generator population and order (``unit_ids``; the coal unit-id token is
  unchanged by design, so ids must match exactly);
* every per-generator array (``pmax``, ``pmin``, ``heat_rate``, ``vom``,
  emission rates, ``zone_idx``, ``availability`` row hashes, ``min_gen`` row
  hashes, ``ramp10``, the assembled ``mc_base`` offer row hashes, …) —
  **exact** equality, no tolerance;
* the class labels (``plant_group``, ``efficiency_bin``): the only permitted
  change is ``COAL`` -> a coal subclass.

A row that differs in any numeric array is a MOVER; each mover is checked
against the BEFORE census's unresolved (generic-bucket) plant list, and a
mover outside that list is a FAILURE of the byte-identity claim.

Usage::

    python scripts/probes/coal_subclass_compare.py --before <dir> --after <dir> \
        --out <file.json>
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np

LABEL_FIELDS = ("plant_group", "efficiency_bin")
COAL_SUBCLASSES = {"COAL_LIGNITE", "COAL_PRB", "COAL_BIT", "COAL_WC"}
_PLANT_RE = re.compile(r"_p(\d+)")


def _plant(uid: str) -> int:
    m = _PLANT_RE.search(uid)
    return int(m.group(1)) if m else -1


def compare_one(before: Path, after: Path) -> dict:
    """Compare one ISO-year's BEFORE/AFTER snapshot pair."""
    b = np.load(before)
    a = np.load(after)
    bj = json.loads(before.with_suffix(".json").read_text())
    unresolved = {
        int(u["plant_code"]) for u in bj["coal_units"] if not u["resolved_subclass"]
    }
    out: dict = {"n_gen_before": int(b["unit_ids"].size), "n_gen_after": int(a["unit_ids"].size)}
    if not np.array_equal(b["unit_ids"], a["unit_ids"]):
        bs, as_ = set(b["unit_ids"].tolist()), set(a["unit_ids"].tolist())
        out["unit_id_mismatch"] = {
            "only_before": sorted(bs - as_)[:50],
            "only_after": sorted(as_ - bs)[:50],
            "same_set_different_order": bs == as_,
        }
        return out
    uids = b["unit_ids"].tolist()
    movers: dict[str, list[str]] = {}
    label_changes: dict[str, int] = {}
    bad_labels: list[str] = []
    missing_fields = sorted(set(b.files) ^ set(a.files))
    for f in sorted(set(b.files) & set(a.files)):
        if f == "unit_ids":
            continue
        x, y = b[f], a[f]
        if x.shape != y.shape:
            out.setdefault("shape_mismatch", {})[f] = [list(x.shape), list(y.shape)]
            continue
        if x.dtype.kind in "fc":
            diff = ~((x == y) | (np.isnan(x) & np.isnan(y)))
        else:
            diff = x != y
        if diff.ndim > 1:
            diff = diff.reshape(diff.shape[0], -1).any(axis=1)
        idx = np.flatnonzero(diff)
        if f in LABEL_FIELDS:
            for i in idx:
                pair = f"{x[i]}->{y[i]}"
                label_changes[f"{f}:{pair}"] = label_changes.get(f"{f}:{pair}", 0) + 1
                if not (str(x[i]) == "COAL" and str(y[i]) in COAL_SUBCLASSES):
                    bad_labels.append(f"{uids[i]} {f} {pair}")
            continue
        for i in idx:
            movers.setdefault(uids[i], []).append(f)
    mover_plants = {_plant(u) for u in movers}
    out.update(
        {
            "missing_fields": missing_fields,
            "label_changes": label_changes,
            "bad_label_changes": bad_labels,
            "n_movers": len(movers),
            "mover_plants": sorted(mover_plants),
            "movers_outside_generic_bucket": sorted(
                u for u in movers if _plant(u) not in unresolved
            ),
            "movers": {u: fs for u, fs in sorted(movers.items())},
            "generic_bucket_plants": sorted(unresolved),
        }
    )
    return out


def main() -> None:
    """Compare every ISO-year present in both directories."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--before", required=True, type=Path)
    ap.add_argument("--after", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    a = ap.parse_args()
    res = {}
    for bf in sorted(a.before.glob("*.npz")):
        af = a.after / bf.name
        if not af.exists():
            res[bf.stem] = {"error": "no AFTER snapshot"}
            continue
        res[bf.stem] = compare_one(bf, af)
    a.out.write_text(json.dumps(res, indent=1, default=str))
    ok = True
    for k, r in res.items():
        verdict = "IDENTICAL"
        if "error" in r or "unit_id_mismatch" in r or r.get("shape_mismatch") or r.get("missing_fields"):
            verdict, ok = "STRUCTURE-MISMATCH", False
        elif r["movers_outside_generic_bucket"] or r["bad_label_changes"]:
            verdict, ok = "FAIL", False
        elif r["n_movers"]:
            verdict = f"MOVERS-ONLY-GENERIC ({r['n_movers']} rows, plants {r['mover_plants']})"
        print(f"{k:12s} {verdict}  labels={r.get('label_changes', {})}")
    print("OVERALL", "PASS" if ok else "FAIL")


if __name__ == "__main__":
    main()
