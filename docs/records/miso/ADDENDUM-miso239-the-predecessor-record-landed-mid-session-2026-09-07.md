# ADDENDUM miso-239 — miso-238's record LANDED ON `main` mid-session, so this session's §0a disclosure is SUPERSEDED; the two independent executions of the same repair agree EXACTLY

Extends `PREREG-miso239-which-property-of-g-2026-09-07.md` (pushed `c0e971ee`) and
`FINDING-miso239-the-pre-registered-ladder-reads-mixed-and-the-object-is-the-spread-2026-09-07.md`.
On the miso-233 / miso-235 / miso-236 / miso-237 / miso-238 addendum pattern.

**NO PRE-REGISTERED DECISION RULE IS TOUCHED AND NO miso-239 NUMBER CHANGES.** The channel
definitions (PREREG §2), the gating seam (PJM), the Q-A verdict ladder and its `≥ 0.50` bars, the
absolute floors (`|γ_MERIT| ≥ 200` MW/z, sub-verdict `≥ 100` MW/z), the Q-C bars
(`≥ 0.50` / `≤ 0.25`), the basis discipline (§0c) and every §5 restriction stand exactly as
pushed. Zero LP, as declared. Keeper unchanged at `2026-09-07-miso-233-spp-hourly` (CALIBRATED,
C3c the single ledgered caveat, DOF 41/2). **Q-A still reads MIXED and still closes nothing;
Q-C still reads SURVIVES.**

---

## 0 — The correction, stated plainly

`PREREG-miso239` §0a recorded — correctly, at `origin/main` = **`8377e878`**, which is what this
session read at start — that miso-238's **FINDING and phase-0 JSON had not landed**, that
`git log --all` returned exactly one commit for its probe, and that consequently *"no number
quoted in this session's handoff from miso-238 is reproducible from a committed artifact today."*
§0b recorded that the probe pushed at `6937a251` still carried the marginal-covariance estimator
its own committed `ADDENDUM` §2 had replaced.

**Both statements have since EXPIRED.** miso-238's own deliverables landed on `main` at
**`3cae3b15`** (PR #5488, branch `claude/miso-backcast-calibration-hd2rem`) **while this session
was running** — `FINDING-miso238-the-carrier-is-the-ladder-not-the-envelope-2026-09-07.md`,
`_miso238_pjm_seam_channel_attribution_phase0.json`, and the probe carrying the same ADDENDUM §2
repair. The predecessor's record is **complete**, and the §0a/§0b disclosure describes a state of
`main` that no longer exists. It was true when written and is superseded now; it is not withdrawn
as an error, and it is not restated as a live finding.

## 1 — What this session did about it

`PREREG-miso239` §0b had declared, before running anything, that this session would apply
miso-238 ADDENDUM §2's repair itself. It did, and pushed it. On discovering miso-238's own version
on `main`, **this session DROPPED its own repair commit entirely and rebuilt on the
predecessor's authoritative version.** miso-238's probe is the record of miso-238's instrument;
a successor's reconstruction of it is not, and does not belong on top of it.

## 2 — The corroboration this accidentally produced, which is stronger than either version alone

Two sessions independently applied the same declared repair to the same probe, from the same
committed ADDENDUM, without seeing each other's code. Comparing the two regenerated
`_miso238_pjm_seam_channel_attribution_phase0.json` files:

* **Every numeric value in the entire file is identical.**
* The **only** difference anywhere in the diff is one key *name* —
  `gamma_marginal_mw_per_z` → `gamma_marginal_model_mw_per_z`, the ADDENDUM §2 disclosure column,
  which no gate and no verdict reads.
* Re-running `_miso239_merit_ladder_property_attribution_phase0.py` against **miso-238's landed
  module** reproduces this session's JSON **byte-identically** — every gate leg, every channel,
  every share, every census row.
* **G-P4 therefore still passes at `0.0 × bar`**: miso-238's published PJM column, reproduced
  from scratch by an independent code path, on all nine quantities in all three years.

miso-238 ADDENDUM §2 argued its repair was admissible because the partial-OLS coefficient is
linear in the residual and so leaves the decomposition exact. That argument was verified twice,
independently, and the two verifications agree to the digit.

## 3 — What is corrected, and what is not

* **CORRECTED, in place:** §0c of this session's FINDING, which stated the missing-artifact
  premise, now carries the landing and points here. The FINDING's headline, verdicts, tables and
  every number are **untouched** — none depended on the premise.
* **NOT corrected:** `PREREG-miso239` §0a/§0b. A pre-registration is a record of what was known
  **before** the numbers, and rewriting one after the fact is exactly what pre-registration
  exists to prevent. It stands as pushed, and this addendum is its erratum.
* **NOT changed:** every adjudicating quantity, every verdict, the DOF ledger (41/2), the keeper,
  and every cell verdict. Nothing was re-run to reach a different answer; the re-run was a
  **check**, and it returned the same file.
* **NOT weakened:** the §0b withdrawal of this session's own `LINEAR → candidate (d)` mapping.
  That is a defect in miso-239's own instrument, has nothing to do with miso-238's record, and
  stands in full.

## 4 — What a successor should take from this

**Read `origin/main` at the moment you need it, not only at session start** — a parallel lane in
the same ISO can land its record mid-session, and a disclosure written against a start-of-session
snapshot can expire without anyone doing anything wrong. The cheap defence is the one this
session already carried and which cost nothing to keep: a provenance gate that reproduces the
predecessor's published quantity **from scratch, in the predecessor's own metric**, rather than a
citation to an artifact whose presence was assumed. G-P4 was written to survive the artifact being
missing, and it survived the artifact arriving.

## 5 — Governance

Rule 1 `[R-STRUCT]`: nothing judged by a residual, nothing proposed, nothing selected; no number
changed. Rule 12 `[R-PARALLEL]`: no LP; nothing on CI. Rule 13 `[R-MEASURED]`: measurement only.
Rule 14 `[R-ACCURATE]`: no input changed. Rule 15 `[R-DASHBOARD]`: no run produced, registered or
pruned. Rule 19 `[R-ONE-MECH]`: no mechanism added. Rule 21 `[R-DOF]`: 41/2, unchanged. Rule 22
`[R-HOLDOUT]`: 2023–2025 only. Rule 23 `[R-FROZEN-DERIVE]`: no derive re-run; the `δ_k` ladders
stay frozen and PREREG §5.2 binds unchanged. Rule 24 `[R-REGISTRY]`: no field created. Rule 25
`[R-ISO-SCOPE]`: MISO only. Rule 26 `[R-DELETE]`: this session's superseded repair commit is
**dropped, not zeroed or kept alongside** the predecessor's — git history is the record.
Rule 27 `[R-PUSH]`: blobs verified after push. Rule 28(b): evidence-append form only; no cell
verdict moves. Rule 29 `[R-SCREEN]`: clause 0, zero LP.
