# ADDENDUM 3 to PRECOMMIT-miso255-measured-sil — **the OWNER ordered the full span, before the
# screen was read. Recorded as an instruction, not a quiet widening.**

**Written and pushed while the shards solve, and before ANY of their numbers exist** (rule 29
`[R-SCREEN]`). No gate, gate value or direction check from PRECOMMIT §3 is renegotiated.

## 1. THE INSTRUCTION AND WHAT IT CHANGES

Owner, 2026-09-12, verbatim: **"Launch them all"** — following **"Keep working to get to a solve
and launch shards"** and the standing ruling **"If structural integrity improves but gates regress
that may still be a keeper."**

PRECOMMIT §2 ordered a **two-year screen (2021, 2022) first**, with the full span spent only if
the screen cleared its pre-registered gate. **That order is now inverted by instruction**: all five
years — 2021, 2022, 2023, 2024, 2025 — are launched at once, on the SAME pin
`d0fec486fa2218afc55dbd2eb377bc2570e61699`, one shard per year (rule 32 `[R-SHARD]`), each
differencing against its own committed control.

**Stated plainly because it is my job to state it, not to re-litigate it:** rule 29's screen-first
ordering exists to avoid spending a span on an arm a one-year screen would have killed. Spending
the span first forgoes that protection. The owner has weighed it and chosen throughput; this lane
proceeds and records the trade rather than burying it. **The gates themselves are untouched** — a
STOP that fires on 2021 or 2022 still kills the arm, it just costs three extra solves to learn it.

**What it does NOT change:** the screen years and their footprint basis (PRECOMMIT §2), every gate
in §3 and its pre-registered value, the direction check, the controls (rule 29(b) form 4 — still no
control solve), and the rule that no gate reads C1 `CC_REGULAR`, C3a or the gas volume.

## 2. WHAT THE FIVE SHARDS ARE

| year | control (committed) | out-dir | branch |
|---|---|---|---|
| 2021 | `miso251_tp2021` | `miso255_sil_2021` | `claude/miso255-sil-2021c` |
| 2022 | `miso251_screen2022` | `miso255_sil_2022` | `claude/miso255-sil-2022c` |
| 2023 | `miso_fuelvintage_A` | `miso255_sil_2023` | `claude/miso255-sil-2023c` |
| 2024 | `miso_fuelvintage_A` | `miso255_sil_2024` | `claude/miso255-sil-2024c` |
| 2025 | `miso_fuelvintage_A` | `miso255_sil_2025` | `claude/miso255-sil-2025c` |

**One pin for all five is deliberate.** A span bundle composed from per-year legs is only coherent
if every leg solved on the same code; mixing pins would make the composite un-attributable. 2023-25
are the keeper's own years, so their controls are the keeper bundle itself — which is why no
control solve is spent for them either.

**The pre-solve delta says the training years are NOT inert**: 2,141 / 1,928 / 1,619 hours over the
import envelope and 1.28 / 1.35 / 1.64 TWh of excess in 2023 / 2024 / 2025, against 8,479 h /
26.48 TWh (2021) and 6,436 h / 33.81 TWh (2022). So the span was always going to have to be
re-solved for a promotion (rule 16 `[R-ALLYEARS]`); the instruction brings that forward rather than
creating it.

## 3. THE KEEPER BAR THIS SETS UP, WRITTEN DOWN BEFORE THE NUMBERS

Recorded now so the recommendation cannot be reverse-engineered from the results:

* **A promotion needs the full span 2023-2025 in one registered bundle** (rule 16). Five per-year
  legs are NOT a keeper; the parent composes them, and the composite must carry
  `stamp_config_partition.py --check`.
* **G-4 is decisive on the CLAIM, not on the code.** If the LP merely relocates the rail from the
  8,700 MW scalar onto the new envelope (≥80 % of hours at ≥99 % of it), the rule-14
  `[R-ACCURATE]` provenance repair still stands on its own evidence — the scalar is still a
  PRA/LOLE accreditation construct falsified by the meter in both directions — but the arm does
  **not** resolve the 2021/2022 object, and the session will say exactly that rather than dress a
  level change as a mechanism.
* **The owner's standing rule is honoured as written**: structural-integrity gains (G-2/G-3 — the
  seam confined to a measured capability envelope, the unsourced rail gone) may outweigh gate
  regressions on C1/C3a/C4, which are REPORTED under G-6 and gate nothing in either direction. If
  that is the shape of the result, it will be named as such, at full magnitude, with the
  regressions quoted rather than minimised.
* **Rule 31 `[R-RETAIN]` stands:** the `miso255_sil_*` bundles are gitignored, live on ephemeral
  shard disk, and will not survive those containers. The promotion question goes to the owner
  explicitly before this session ends.
