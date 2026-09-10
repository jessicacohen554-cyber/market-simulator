#!/usr/bin/env python3
"""Re-base the NEISO T3 FC-5 disposition table onto another committed bundle.

capx D92 measurement helper (companion to ``corridor_model_values.py``, which
is VALIDATED at 54/54 against the table's own declared bundle). This module does
the MECHANICAL half only:

* recompute every row's ``model_value`` from the new summary,
* recompute ``divergence_pct`` against the row's UNCHANGED ``anchor_value``
  (rule 13 ``[R-MEASURED]``: nothing moves toward an anchor, and no anchor moves),
* classify each row against the FC-5 convention (>15 % or opposite sign needs a
  written explanation) and report which rows need one AUTHORED.

It never invents an explanation and never changes a verdict on its own: a row
whose class changes is emitted with ``verdict: "NEEDS AUTHORING"`` so it cannot
slip through as an EXPLAINED DIVERGENCE nobody explained.

Not standing tooling: the measurement record for
``docs/handoffs/FINDING-capx-d92-2026-09-10.md``.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from corridor_model_values import model_values  # noqa: E402

#: The FC-5 convention imported whole by rubric section FC-5
#: (``cross-model-corridor-2026-07-13.md`` section 1): a divergence above this,
#: or an opposite sign/direction, requires a written ours-vs-theirs explanation.
DIVERGENCE_PCT_THRESHOLD = 15.0


def classify(rows: list[dict], summary: dict, ps_residual_gw: float) -> list[dict]:
    """One record per row: old value, new value, old/new divergence, action."""
    cache: dict[int, dict[str, float]] = {}
    out: list[dict] = []
    for r in rows:
        year = int(r["target_year"])
        if year not in cache:
            cache[year] = model_values(summary, year, ps_residual_gw)
        new = cache[year][r["quantity"]]
        anchor = r["anchor_value"]
        old_div = r["divergence_pct"]
        new_div = None
        if anchor not in (None, 0):
            new_div = round((new - float(anchor)) / float(anchor) * 100.0, 1)
        was_div = r["verdict"] == "EXPLAINED DIVERGENCE"
        now_div = new_div is not None and abs(new_div) > DIVERGENCE_PCT_THRESHOLD
        if not was_div and now_div:
            action = "AUTHOR — became divergent"
        elif was_div and not now_div:
            action = "AUTHOR — became IN CORRIDOR (retire the explanation)"
        elif (
            was_div
            and now_div
            and old_div is not None
            and (float(old_div) > 0) != (new_div > 0)
        ):
            action = "AUTHOR — sign flipped (existing explanation falsified)"
        else:
            action = "carry"
        out.append(
            {
                "quantity": r["quantity"],
                "target_year": year,
                "anchor_value": anchor,
                "old_model_value": r["model_value"],
                "new_model_value": round(new, 4),
                "old_divergence_pct": old_div,
                "new_divergence_pct": new_div,
                "old_verdict": r["verdict"],
                "action": action,
            }
        )
    return out


def main(argv: list[str]) -> int:
    disp = json.loads(Path(argv[1]).read_text())
    summ = json.loads(Path(argv[2]).read_text())
    ps = float(disp["model_source"].get("storage_ps_residual_gw") or 0.0)
    recs = classify(disp["rows"], summ, ps)
    need = [r for r in recs if r["action"] != "carry"]
    print(f"{len(recs)} rows; {len(need)} need authoring")
    for r in need:
        print(
            f"  {r['quantity']:30} @{r['target_year']}  "
            f"{r['old_model_value']:>10} -> {r['new_model_value']:<10} "
            f"div {r['old_divergence_pct']} -> {r['new_divergence_pct']}   {r['action']}"
        )
    if len(argv) > 3:
        Path(argv[3]).write_text(json.dumps(recs, indent=1) + "\n")
        print(f"wrote {argv[3]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
