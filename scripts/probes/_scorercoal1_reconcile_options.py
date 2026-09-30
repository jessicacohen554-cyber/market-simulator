"""SCORER-COAL-1 probe (ZERO LP): the C1 fossil reconcile's coal allocation, cross-ISO.

Measures, for every ISO and every bench year a registered keeper scores:
  * k — the uniform factor ``render_calibration_html.reconcile_vintage_classes``
    applied to every fossil class (1.0 when the combined total was in band);
  * 923 coal (grid, pre-reconcile) vs the EIA-930 coal cell vs ``coal_cems``;
  * how much of each C1 coal record's miss is the reconcile factor, i.e.
    ``coal_923 × (1 − k)``.

Then re-scores every registered run under three options, each defined BEFORE any
number was read (docs/handoffs/RESULT-scorer-coal1-reconcile-options-2026-09-29.md §2):
  (c) STATUS QUO — the committed classFull.
  (a) COAL-AT-923 — the combined-band TRIGGER is unchanged (same years reconcile),
      and the combined target is unchanged; coal is held at its own 923 grid level
      and the gas (+oil) family takes the whole correction:
      gas_target = combined_target − coal_923.
  (b) COAL-AT-CEMS — same trigger and combined target; coal is set to
      coal_cems × k_coal (k_coal = mean over the ISO's complete coal vintages of
      coal_923 ÷ coal_cems, both PRE-reconcile, so the anchor is not circular),
      scaled proportionally across coal classes; gas takes the remainder.

The pre-reconcile 923 classes are recovered from the bench part itself: the
render's ``co2.byClass`` is ``intensity × full-923 class TWh`` (pre-BTM,
pre-reconcile), so for a class with no BTM ``classFull / (byClass/intensity)``
is the applied factor k. Every family class is then un-scaled by k, and the
status-quo reconcile is re-applied to that recovered frame as a parity check —
a year that does not reproduce is reported, never silently scored. The options
themselves are applied as deltas on the COMMITTED classFull (conserving the
combined family total), so option (c) is the committed benchmark exactly.
Needs the repo venv (numpy/pandas via the render import).

Reads committed artifacts only (bench parts, registry sidecars, run payloads,
bundle attestations). Writes nothing outside the scratch path passed as argv[1].
"""

from __future__ import annotations

import copy
import gzip
import json
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

import scripts.calibration_verdict as cv  # noqa: E402
from scripts.lib import benchmark_semantics as bs  # noqa: E402
from scripts.render_calibration_html import reconcile_vintage_classes  # noqa: E402

BENCH = REPO / "frontend/data/backcast/bench"
REG = REPO / "frontend/data/backcast/registry"
COAL = tuple(bs.COAL_GROUPS)
GAS = tuple(bs.GAS_GROUPS)
OIL = tuple(bs.OIL_GROUPS)


def load_part(iso: str, year: int) -> dict:
    """Return the committed bench dict for (iso, year)."""
    return json.load(gzip.open(BENCH / iso / f"{year}.json.gz"))["bench"]


def family(e930: dict) -> tuple[str, ...]:
    """The reconcile family membership exactly as the render builds it."""
    return (*GAS, *COAL) if e930.get("oil") is None else (*GAS, *COAL, *OIL)


def infer_k(b: dict) -> tuple[float, str, float]:
    """Applied reconcile factor from the co2 block: (k, class used, spread)."""
    co2 = b.get("co2") or {}
    by, inten, btm = (
        co2.get("byClass", {}),
        co2.get("intensity", {}),
        co2.get("btmClass", {}),
    )
    cf = b["classFull"]
    ks = []
    for c, v in by.items():
        if c in btm or c not in cf or not inten.get(c):
            continue
        if c not in GAS and c not in COAL:
            continue
        full = v / inten[c]
        if full > 0.5:  # precision floor: byClass is 4 dp
            ks.append((full, cf[c] / full, c))
    if not ks:
        return 1.0, "none", 0.0
    ks.sort(reverse=True)
    k = ks[0][1]
    spread = max(abs(x[1] - k) for x in ks)
    return (1.0 if abs(k - 1.0) < 2e-4 else k), ks[0][2], spread


def apply_option(
    opt: str, committed: dict, k: float, e930: dict, k_coal: float | None
) -> dict:
    """Return classFull under option ``opt``, as a delta on the COMMITTED classFull.

    ``k`` is the factor the render applied (1.0 = the combined total was in band,
    and every option leaves the year byte-identical). Otherwise the combined family
    total (the status-quo target, CAISO cap included) is conserved and only its
    coal/non-coal allocation moves.
    """
    cf = dict(committed)
    if opt == "c" or abs(k - 1.0) < 2e-4:
        return cf
    fam = [g for g in family(e930) if g in cf]
    coal = [g for g in fam if g in COAL]
    rest = [g for g in fam if g not in COAL]
    tgt = sum(cf[g] for g in fam)
    coal_cur = sum(cf[g] for g in coal)
    coal_raw = coal_cur / k
    if opt == "a":
        coal_tgt = coal_raw
    else:  # b
        cems = float(e930.get("coal_cems") or 0.0)
        coal_tgt = cems * k_coal if (cems > 0 and k_coal) else coal_raw
    if coal_cur > 0:
        for g in coal:
            cf[g] = round(cf[g] * coal_tgt / coal_cur, 4)
    rest_cur = sum(cf[g] for g in rest)
    s = (tgt - coal_tgt) / rest_cur
    for g in rest:
        cf[g] = round(cf[g] * s, 4)
    return cf


def main(out: Path) -> None:
    """Measure, re-score, and dump JSON to ``out``."""
    runs = defaultdict(list)
    for f in sorted(REG.glob("*.json")):
        s = json.loads(f.read_text())
        runs[s["iso"]].append(s["id"])
    measure, k_by, kcoal = [], {}, {}
    for iso in sorted(runs):
        years = sorted(int(p.name[:4]) for p in (BENCH / iso).glob("[0-9]*.json.gz"))
        for y in years:
            b = load_part(iso, y)
            e930, cf = b["e930"], b["classFull"]
            k, kc, spread = infer_k(b)
            raw = dict(cf)
            for g in family(e930):
                if g in raw:
                    raw[g] = raw[g] / k
            parity = max(
                abs(reconcile_vintage_classes(dict(raw), e930, iso)[g] - cf[g])
                for g in family(e930)
                if g in cf
            )
            coal923 = sum(raw.get(g, 0.0) for g in COAL)
            coalcf = sum(cf.get(g, 0.0) for g in COAL)
            k_by[(iso, y)] = k
            measure.append(
                {
                    "iso": iso,
                    "year": y,
                    "k": round(k, 4),
                    "k_class": kc,
                    "k_spread": round(spread, 4),
                    "parity_twh": round(parity, 4),
                    "coal923": round(coal923, 3),
                    "coal930": e930.get("coal"),
                    "coal_cems": e930.get("coal_cems"),
                    "coal_classFull": round(coalcf, 3),
                    "coal_k_effect": round(coalcf - coal923, 3),
                    "coal_complete": cv.family_is_complete(iso, "coal", y),
                }
            )
        rat = [
            m["coal923"] / m["coal_cems"]
            for m in measure
            if m["iso"] == iso and m["coal_complete"] and (m["coal_cems"] or 0) > 0
        ]
        kcoal[iso] = sum(rat) / len(rat) if rat else None

    results = {}
    for iso, ids in runs.items():
        for rid in ids:
            art = cv.load_artifacts(rid)
            base = copy.deepcopy(art["bench"])
            results[rid] = {"iso": iso}
            for opt in ("c", "a", "b"):
                a2 = dict(art)
                a2["bench"] = copy.deepcopy(base)
                for y, yb in a2["bench"].items():
                    k = k_by.get((iso, int(y)))
                    if k is not None:
                        yb["classFull"] = apply_option(
                            opt, yb["classFull"], k, yb["e930"], kcoal[iso]
                        )
                full = cv.determine_from_artifacts(rid, a2)
                span = [
                    y
                    for y in (2023, 2024, 2025)
                    if y in art["sidecar"].get("years", [])
                ]
                trn = cv.determine_from_artifacts(rid, a2, years=span) if span else None
                recs = [
                    {
                        k: r.get(k)
                        for k in (
                            "criterion",
                            "key",
                            "year",
                            "status",
                            "model",
                            "actual",
                            "magnitude",
                        )
                    }
                    for crit in full["criteria"].values()
                    for r in crit.get("records", [])
                    if r.get("criterion") in ("fuelmix", "sysvol", "forced_share")
                ]
                results[rid][opt] = {
                    "determination": full["determination"],
                    "train_determination": trn["determination"] if trn else None,
                    "records": recs,
                }
    out.write_text(
        json.dumps({"measure": measure, "k_coal": kcoal, "runs": results}, indent=1)
    )
    print(f"wrote {out}")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
