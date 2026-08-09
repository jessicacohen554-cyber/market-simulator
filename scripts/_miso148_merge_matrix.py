"""miso-148 merge helper: re-apply this lane's matrix edits onto origin/main's file.

The merge produced 92 conflicts in ``mechanism-matrix.js``, EVERY one of them a
line-anchor DIGIT difference (both sides ran ``check_mechanism_matrix.py
--fix-anchors`` against a different ``scenarios.py`` line count). Resolving them
by hand would risk transcription drift across 92 hunks of dense prose, so the
file is taken from ``origin/main`` wholesale and this lane's THREE substantive
edits are re-applied programmatically:

1. the new ``summer_derate_basis_aware`` row (rule 28(c), inserted immediately
   before its sibling ``coal_nameplate_summer_derate``, where it was authored);
2. the MISO keeper stamp in the ``keepers:`` header (rule 28 promoting-session
   duty);
3. nothing else — every other byte is origin/main's.

Anchors are then repaired by the repo's own ``--fix-anchors`` against the MERGED
``scenarios.py``, which is the only line count that is correct after the merge.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
MATRIX = REPO / "docs" / "codebase-site" / "data" / "mechanism-matrix.js"
ROW_FILE = Path(sys.argv[1])
ANCHOR = '    { id: "coal_nameplate_summer_derate", cat: "outage",'
OLD_KEEPER = '    MISO: "2026-08-05-miso-132b-cc-committed",'
NEW_KEEPER = '    MISO: "2026-08-09-miso-148-basis-aware",'


def main() -> None:
    text = MATRIX.read_text()
    row = ROW_FILE.read_text().rstrip("\n")

    if '"summer_derate_basis_aware"' in text:
        raise SystemExit("row already present — refusing to duplicate")
    if text.count(ANCHOR) != 1:
        raise SystemExit(f"expected exactly 1 anchor, found {text.count(ANCHOR)}")
    if text.count(OLD_KEEPER) != 1:
        raise SystemExit(
            f"expected exactly 1 MISO keeper stamp, found {text.count(OLD_KEEPER)}"
        )

    text = text.replace(ANCHOR, row + "\n\n" + ANCHOR, 1)
    text = text.replace(OLD_KEEPER, NEW_KEEPER, 1)
    MATRIX.write_text(text)
    print("re-applied: summer_derate_basis_aware row + MISO keeper stamp")


if __name__ == "__main__":
    main()
