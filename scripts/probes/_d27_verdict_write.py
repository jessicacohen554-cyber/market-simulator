"""One-shot records helper for capx D27: preserve `miso-t1h`, write the HEAD re-measure.

NOT a standing tool — it is the auditable record of the single ff-verdicts.json
edit this lane makes (preserve-then-overwrite, the NEISO-RC-R pattern). It
refuses to touch any key other than `miso-t1h` / `miso-t1h-pre-d27`, so a
cross-lane write is impossible by construction (rule 28 / D27 kill K-c).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
VERDICTS = REPO / "frontend" / "data" / "forecast" / "ff-verdicts.json"
LIVE_KEY = "miso-t1h"
PRESERVED_KEY = "miso-t1h-pre-d27"


def _sorted_deep(obj):
    """Return ``obj`` with every dict key sorted, matching the board's style."""
    if isinstance(obj, dict):
        return {k: _sorted_deep(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        return [_sorted_deep(v) for v in obj]
    return obj


def main(sidecar_path: str) -> int:
    board = json.loads(VERDICTS.read_text())
    before = set(board)
    file_order = list(board)

    if PRESERVED_KEY in board:
        raise SystemExit(f"{PRESERVED_KEY} already exists — refusing to overwrite")
    if LIVE_KEY not in board:
        raise SystemExit(f"{LIVE_KEY} absent — nothing to preserve")

    # 1. Preserve the FFR-3A-2-vintage record verbatim, with a marker note.
    preserved = json.loads(json.dumps(board[LIVE_KEY]))
    prov = preserved.setdefault("provenance", {})
    prov["preserved_note"] = (
        "PRESERVED BASELINE — the FFR-3A-2-vintage measurement that occupied the "
        "bare `miso-t1h` key until capx lane D27 (2026-09-01) re-measured the MISO "
        "T1-H leg at HEAD and took the bare key under the LIVE-vintage convention. "
        "NEVER quote this record as MISO's current T1-H state; read `miso-t1h`. "
        "It remains valid at the sha it records."
    )
    board[PRESERVED_KEY] = preserved

    # 2. Write the HEAD re-measure to the bare key.
    new = json.loads(Path(sidecar_path).read_text())
    new.setdefault("provenance", {})
    new["provenance"].update(
        {
            # `scored_at_sha` / `scored_at_date` / `cache_epoch` are the
            # scorer's OWN forecast-provenance/v1 stamp and are never
            # overwritten here — only the session label and the note are added.
            "session": "capx-D27",
            "note": (
                "HEAD re-measure of the MISO T1-H leg (capx lane D27, executing "
                "D17-R's routed PRIMARY R1), run "
                "`miso-2021-2025-realized-t1h-d27`, bare invocation at HEAD with "
                "every solve-affecting flag omitted. Scored against the CURRENT "
                "committed capacity_actuals_miso.csv; the prior bare-key record "
                "(FFR-3A-2 vintage) is preserved at `miso-t1h-pre-d27`. NOT an "
                "S-123-isolating A/B — five MISO-relevant defaults moved after the "
                "FFR-3A-3 baseline and no control arm was in budget; see "
                "docs/handoffs/FINDING-capx-d27-miso-t1h-remeasure-2026-09-01.md."
            ),
        }
    )
    board[LIVE_KEY] = _sorted_deep(new)
    board[PRESERVED_KEY] = _sorted_deep(board[PRESERVED_KEY])

    # `miso-t1h-pre-d27` goes immediately after `miso-t1h`, so the preserved
    # baseline reads next to the live record in the file.
    order_out = []
    for k in file_order:
        order_out.append(k)
        if k == LIVE_KEY:
            order_out.append(PRESERVED_KEY)

    added = set(board) - before
    assert added == {PRESERVED_KEY}, f"unexpected key additions: {added}"

    # Write with the file's EXISTING top-level key order preserved and only
    # this lane's two entries re-sorted internally. The board's stored order is
    # not fully sorted (one hand-edited pair from another lane), and a global
    # sort_keys=True dump would reorder that lane's lines for zero content
    # change — a needless conflict against a lane in flight (kill K-c).
    ordered = {k: board[k] for k in order_out}
    VERDICTS.write_text(json.dumps(ordered, indent=1, default=str) + "\n")
    print(f"wrote {LIVE_KEY} (determination {new['determination']}), "
          f"preserved -> {PRESERVED_KEY}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
