# CHARTER — miso-93 LANE A: re-audit the MISO keeper on the guard-corrected CAMPD envelope

**Status:** pre-registered 2026-07-26, BEFORE any result of this session was read.
**Lane:** A of the miso-93 handoff — the top-ranked ready item.
**Parent charter:** `docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §5
(blast radius) + §8 (owner verdict: *"ERCOT / PJM / MISO / CAISO / NYISO replay
their keepers in-sample (2023–2025, one bundle, rule 16) on the corrected
envelope, both arms registered (rule 15)"*).
**Predecessor:** miso-89 attempted this and was BLOCKED on container RAM
(OOM at 15.9 GB). miso-92 removed 35 % of the cross-year floor, making the
staged recipe viable.

## 1. What this lane is, and what it is NOT

This is a **replay, not a calibration change.** No mechanism is added, no
parameter is tuned, no offer curve is touched. The keeper recipe
(`results/calibration/miso88_egrid_hr/meta.json`) is replayed verbatim. The
question is a factual one:

> Does `2026-07-25-miso-88-egrid-hr` still earn its determination when solved
> against the availability envelope the repo actually carries today?

Because the guard-corrected extract is **committed and is the envelope MISO now
solves against**, the keeper's registered numbers currently describe a
**pre-adoption** envelope. Until this lane lands, they are not reproducible at
HEAD. That is a documented, expected state (miso-89 entry; re-confirmed and
quantified by miso-92 §7) — not a new defect.

**No tuning is licensed by any outcome of this lane.** The ledger budget is
**3/3, saturated**. A newly-failing gate is reported as a re-tune trigger for a
future chartered session; it is NOT closed here with an adder, a multiplier, or
a widened ledger entry (rules 1, 10, 24).

## 2. The A0 baseline — and why MISO's is clean where CAISO's was not

caiso-123 showed the CAISO re-audit verdict was measured against a **confounded
A0**: that ISO's extract had an independent content backfill land between the
keeper's solve and the guard, so the "guard effect" conflated two changes.

**MISO does not have that problem, and this was verified before solving:**

| revision | `data/raw/campd-unit-outages-MISO.csv` blob |
|---|---|
| `2f4cbc3` (2026-07-24, last pre-keeper change) | `f2b3ec8e4f2920bccf9d64200b1635cc42d223a9` |
| `3babe5f` (**the keeper's own `git_sha`**, 2026-07-25) | `f2b3ec8e4f2920bccf9d64200b1635cc42d223a9` |
| `6a8f285` (2026-07-26, the guard adoption) | `c298c6801d8f93c99a762749b01fabe829f92bc4` |
| `HEAD` (`4094bbe`) | `c298c6801d8f93c99a762749b01fabe829f92bc4` |

The keeper's sha is a descendant of `2f4cbc3` and an ancestor of `6a8f285`
(verified with `git merge-base --is-ancestor`), and the blob is **byte-identical
across the keeper's sha**, changing exactly once — at the guard commit — and not
since. So on the extract axis the MISO A0→A1 contrast is **single-delta by
construction**, and no A0 re-solve is needed on that axis (the guard is
byte-inert off; neiso-65 §2).

**But the code surface is NOT single-delta.** `git diff 3babe5f..HEAD` touches
`offer_surfaces.py` (+391), `renewables.py` (+342), `scenarios.py` (+220),
`runner.py` (+129), `dual_fuel.py`, `campd_bins.py`, `arrays.py`, `bounds.py`,
`retirements.py`, `reserves/spec.py` — other lanes' work, mostly gated
default-off but **not audited for MISO-inertness**. miso-92 attributed the
observed HEAD drift to CAMPD and called it "sufficient"; that is an
**attribution, not an isolation**, and caiso-123 is the precedent for why the
difference matters. §4 therefore adds a same-HEAD isolation arm.

## 3. A dependency this lane found before solving — record it

neiso-65 §2 published a table of clean partitions that must be regenerated
before replaying a keeper in a fresh container. **MISO is absent from every row
of that table**, because MISO never solved in that session (RAM-blocked).

That omission is wrong, and it silently contaminated this session's first
launch:

* `model/interchange/miso.py::_miso_cil_cel_groups` builds **per-zone seasonal
  CIL/CEL interface groups** from the curated `capacity-deliverability`
  partition (MISO LOLE Study Reports).
* When the partition is absent it returns `[]` and the caller **falls back to
  static PY2025-26 summer caps** — a documented graceful fallback, but a
  structurally different network.
* This happens **independently of the `capacity_deliverability_limits` flag**,
  which is `false` in the MISO keeper. Reading the flag is therefore *not*
  sufficient to conclude the partition is unneeded.

With the partition regenerated the solve log instead reports
`seasonal CIL/CEL interface caps on 5 zone group(s) … static summer fallbacks
replaced`. `ramp-capability` also carries a MISO partition (991 rows).

**Binding for this lane:** all clean partitions are regenerated before solving,
and every solve log is audited for missing-input warnings before its numbers are
quoted. The first (degraded) launch was killed and its bundle deleted; no number
from it is quoted anywhere.

## 4. Method — pre-registered

Three-year bundle, rule 16, via the staged one-year-per-process
`--reuse-solved` recipe (the 14.4 GB single-year peak is irreducible; miso-92).

* **Arm A1 (the deliverable):** keeper recipe, HEAD, corrected extract,
  `--years 2023 2024 2025` in ONE bundle → `results/calibration/miso93_meritguard_a1`.
  Registered on the dashboard whatever the verdict (rule 15).
* **Isolation probe (diagnostic, single-year, NEVER registered):** the same
  2023 solve at HEAD with the extract reverted to the keeper's blob
  `f2b3ec8`. Contrast against A1-2023 isolates **the extract's own effect at
  identical HEAD**, separating it from the code drift of §2. Rule 16 forbids
  registering a one-year bundle; it is deleted after its numbers are recorded in
  the finding.

## 5. Pre-registered pass/fail bar

Scored by `scripts/calibration_verdict.py` on the unmodified rubric. The keeper's
current standing is the reference:

| criterion | keeper standing | threshold |
|---|---|---|
| C1 per-class mix | PASS (free 12/12) | `min(2 % load, 8 TWh)` **and** 3 pp |
| C2 family volume | PASS | ±2.5 % |
| C3a mean LMP | 2023 −2.2 % / 2024 −8.0 % PASS; 2025 −16.6 % **ledgered** | ±10 % |
| C3b shape | 2025 NRMSE 0.208 **ledgered** | ≤0.20 |
| C3c tail | all years **ledgered** | — |
| C4 / C5a / C6 / C7 / C8 | PASS | C5a ±7 % |

**Verdict rule, fixed in advance:**

* **FIX-IN-PLACE** — determination stays `CALIBRATED-WITH-CAVEATS` with the
  same 3 ledgered caveats and no new failing gate. The keeper is re-audited in
  place; A1 becomes the reproducible bundle for its registered numbers.
* **RE-TUNE REQUIRED** — any currently-passing gate fails, or a 4th caveat
  would be needed. Reported as a trigger with its magnitude; **no tuning in this
  session** (3/3 saturated).

**Named exposure, declared before solving.** miso-92's measured 2023 drift
(mean LWP $31.224 → $30.770, −1.45 %) puts the pre-registered risk on
**C3a-2024**, which sits at −8.0 % against a −10 % veto: a drift of the same
sign and size lands it near −9.4 %, inside the band but with little margin. The
class shifts miso-92 measured (ST_GAS +2.05 TWh, CT_PEAKER −1.16, COAL_BIT
+1.10, COAL_PRB −1.08) largely cancel **within** the C2 gas and coal families
(net +0.89 / +0.02 TWh) and sit well inside the C1 8 TWh band, so C1/C2 are
expected to hold. Recording this now so neither outcome can be narrated as
predicted after the fact.

## 6. What this lane may NOT do

* Not tune anything (§1). Not widen a ledger entry. Not add a 4th.
* Not touch any year outside 2023–2025 — MISO has **no** calibration-complete
  marker and the holdout freeze is additionally `active=true` (rule 22,
  parent charter §6).
* Not register a single-year bundle (rule 16).
* Not re-derive `SUMMER_WEFOR_SHARE` or any measured-behaviour constant — this
  lane has no source-data change of that kind to cite (rule 23).
