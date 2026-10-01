# RESULT — caiso-276: independent verification of the caiso-275 Arm A / Arm B adjudication, plus two findings that lane did not produce

**Session caiso-276, 2026-09-12. CAISO only (rule 25 `[R-ISO-SCOPE]`). ZERO LP SPENT.**

**READ THIS FIRST — SCOPE.** caiso-276 ran **concurrently with caiso-275**, not after it, and reached
the same two verdicts from the same committed sidecars **independently and without seeing that
lane's working**. caiso-275 owns the arms, the promotion and the registration; this document is
**corroboration plus two findings caiso-275 did not produce**, and it is deliberately NOT a competing
claim on the same objects. Where the two lanes agree the agreement is worth something precisely
because it was reached twice; where this document is unique it says so.

I verified caiso-275's promotion rather than assuming it:
`python3 scripts/calibration_verdict.py --run-id 2026-09-12-caiso-275-gascoupling` →
**CALIBRATED** on 2023–2025, C1/C2/C3a/C3b/C4/C6/C8 PASS, the single ledgered C3c caveat.
**The promotion is sound and I have nothing to add against it.**

---

## §1 — The handoff this session was given was STALE, and phase 0 found nothing to repair

The charter directed three zero-LP phase-0 steps on the premise that CAISO reads **NOT-YET** with
**C6 UNATTESTED** and **C8 SKIPPED**, and suggested an attestation regeneration might be "a
near-zero-LP fix". Measured against the then-designated keeper `2026-09-10-caiso-271-egrid-family`:

1. **C6 UNATTESTED?** No. `calibration_attestation.json` present, **C6 PASSES**.
2. **C8 SKIPPED?** No. `legitimacy_diagnostics.json` present, **C8 PASSES**. The `SKIPPED` lines
   under it are rule 20 `[R-FORCED-BUDGET]` per-class immateriality skips (COAL 0.0 %, CT_PEAKER
   2.0 %, ST_GAS 0.6 % of ISO load) working exactly as designed — not a missing artifact.
3. **Re-score:** **CALIBRATED**, C3c the single ledgered caveat — the disposition rule 23 `[R-C3C]`
   prescribes.

**No artifact was missing and nothing legitimately refused to attest, so there was no third case to
report and NOTHING WAS REGENERATED.** The charter was right that manufacturing a pass would violate
rule 1 `[R-STRUCT]`; the point was moot. The premise described `caiso-269`, superseded by
caiso-271/273 the day before.

## §2 — Arm A `caiso_import_solar_shape`: falsified on its own G-1. AGREES WITH caiso-275.

| year | hours > $0.50 | G-1 (≥1,000) | annual LW price ctrl → arm | G-2 leakage | belly imports |
|---|--:|:--|--:|--:|--:|
| 2023 | **339** | **FAIL** | 56.545 → 56.368 (−0.177) | 0.024 PASS | +73.8 MW |
| 2024 | **307** | **FAIL** | 37.651 → 37.507 (−0.143) | 0.049 PASS | +96.2 MW |
| 2025 | **518** | **FAIL** | 37.133 → 36.946 (−0.187) | 0.057 PASS | +117.8 MW |

Armed, live, directionally right, and **~100× too small**: against a −$36…−$46 offer collapse on
30 % of all hours the annual price moves −$0.14 to −$0.19. caiso-275 §3's own headroom note
(~440 MW actually marginal) predicted it.

**Recorded against my own convenience: arm A moves the rubric the RIGHT way every year**
(ΔC3a −0.33 / −0.41 / −0.53 pp; ΔC3b −0.0047 / −0.0035 / −0.0056). **That is not a reason to keep
it and was not used as one.** Reviving an arm past a failed ex-ante STOP gate *because the residual
improved* is the fitted-mechanism selection rules 1 `[R-STRUCT]` and 29 `[R-SCREEN]` exist to refuse.
**A-2022 was never spent**, per caiso-275 §7 G-1 ("a dead arm's remaining years are not re-read").

## §3 — Arm B `caiso_import_gas_coupling`: live where its driver is wide. AGREES WITH caiso-275.

| year | hours > $0.50 | G-1 | annual LW price ctrl → arm | ΔC3a | ΔC3b |
|---|--:|:--|--:|--:|--:|
| **2022** (screen) | **1,276** | **PASS** | 95.473 → 94.069 (−1.404) | **−1.68 pp** | **−0.0463** |
| 2023 | **1,478** | **PASS** | 56.545 → 55.891 (−0.653) | −1.20 pp | −0.0016 |
| 2024 | 580 | **FAIL** | 37.651 → 37.547 (−0.104) | −0.29 pp | −0.0014 |
| 2025 | 481 | **FAIL** | 37.133 → 37.066 (−0.067) | −0.19 pp | +0.0003 |

**Two independent corroborations of caiso-275's own corrections**, reached here before that lane's
commits were visible: its "Arm B FAILS its own G-1 and G-2 in 2024" correction (`66259c12`) matches
the 580 h measured here, and its "Arm B flips C3b-2022 FAIL to PASS" (`7c5b2f8c`) matches
**0.241 → 0.194** crossing the 0.20 NRMSE bar.

**The 2024/2025 G-1 failures are the MECHANISM WORKING, not a defect.** Arm B is a gas-**basis**
coupling and can only bite when the basis is wide: phase 0 sizes `hub − F923` at **−11.68 $/MMBtu**
for Dec-2022 against **−0.7 to −1.4** for a typical 2024/25 month. The response is
driver-proportional — Dec-2022 **−13.59 $/MWh** against ≤ −0.97 in every other month of that year,
and within 2024 the largest monthly move is **December (−0.70)**, that year's own widest-basis month.
A driver-proportional response is the signature of a real mechanism; an arm moving price equally in
a year when its driver was ten times smaller would be the suspicious result.

**G-5 does not fire for either arm**: level and shape improve together in **6 of 7** arm-years, flat
in the seventh. No arm buys level by wrecking shape.

**BASIS CAVEAT, AGAINST MY OWN NUMBERS.** The C3a/C3b levels here are a **screen metric, not the
rubric's**. The model side reproduces the scorer exactly (56.545 / 37.651 / 37.133 vs 56.54 / 37.65 /
37.13) but the actual side is reconstructed from `actual_lmp_hourly_CAISO.parquet` and does **not**
reproduce the committed bench actual (scorer 2023 actual 54.17 → C3a +4.4 %; mine 54.63 → +2.45 %).
**The Δ columns are load-bearing; the levels are not the rubric's and must not be quoted as such.**

## §4 — FINDING 1 (UNIQUE): both arms move the structural object the WRONG way

**Measured, not assumed — and caiso-275 did not produce this table.** Its own §1 object is that in
the belly the real CAISO runs **7–9 GW of its own gas and is a net EXPORTER**, while the model runs
~1.5 GW of gas and **imports** ~2 GW. Both arms act on the import *offer*, so both close price by
importing **more** and running **less** domestic gas. Over the same bottom-2,628-net-load-hour belly,
control → arm, mean MW:

| year | arm | belly gas | belly imports |
|---|---|--:|--:|
| 2022 | B | 3,305.4 → 3,265.3 (**−40.2**) | 4,686.5 → 4,718.5 (**+32.0**) |
| 2023 | B | 2,722.8 → 2,644.2 (**−78.6**) | 2,929.2 → 3,037.3 (**+108.1**) |
| 2024 | B | 2,254.0 → 2,231.5 (−22.5) | 3,585.2 → 3,609.4 (+24.2) |
| 2025 | B | 2,213.5 → 2,208.5 (−4.9) | 3,357.4 → 3,360.9 (+3.5) |
| 2023 | A | 2,722.8 → 2,694.2 (−28.6) | 2,929.2 → 3,003.0 (+73.8) |
| 2024 | A | 2,254.0 → 2,233.7 (−20.3) | 3,585.2 → 3,681.4 (**+96.2**) |
| 2025 | A | 2,213.5 → 2,195.9 (−17.6) | 3,357.4 → 3,475.2 (**+117.8**) |

**Every cell moves gas down and imports up.** The magnitudes are small (~1–3 % of belly gas) and arm
B's mechanism is legitimate in itself — pricing desert-SW gas imports against the **measured** basis
is a rule 14 `[R-ACCURATE]` input, and imports genuinely *were* cheaper in Dec-2022.

**This is NOT offered as an argument against the promotion, which is sound.** It is offered as the
statement of what the promotion did and did not buy: **arm B improves the price residual while
slightly WIDENING the belly gas deficit that residual is a symptom of.** The deficit remains the
larger open CAISO object and neither arm touches it. Recorded so a later lane does not read the
C3b-2022 flip as evidence the belly is solved.

## §5 — FINDING 2 (UNIQUE): the parity gate is NOT git-aware, and rule 31's stated reason is false

CLAUDE.md rule 31 `[R-RETAIN]` justifies the gitignore route by asserting that *"the parity gate
(`check_registry_payload_parity.py`) only ever sees committed dirs, so an ignored bundle can sit on
local disk indefinitely without turning anything red."*

**That reason is factually wrong about this script.** It enumerates bundles with a pure filesystem
walk — `for path in sorted(p for p in calib_root.iterdir() if p.is_dir())` (line 437) — with **no git
awareness of any kind**. An ignored, untracked bundle on local disk still turns the gate RED locally.
Reproduced at this commit: the sweep names `results/calibration/caiso275_*` while
`git ls-tree -r HEAD` shows **zero** tracked files under those paths and `git check-ignore` resolves
every one.

**The rule's MECHANISM is nonetheless correct; only its stated REASON is not.** A fresh CI checkout
does not contain the directories at all, so the gate is **green in CI** and the bundles are genuinely
out of `main` — the whole of what rule 29(c) requires.

**Why this matters: the next session that runs the gate locally, sees RED, and `rm`s the bundles to
"clear it" will have reproduced the ercot-255 incident rule 31 was written to prevent.** The correct
reading is: *untracked + ignored IS the discharge; a local RED on an ignored dir is expected and must
not be cleared with `rm`.*

**Recommendation for the owner** (not self-authorized — CLAUDE.md is a rule 27 `[R-PUSH]` core file
and owner-governed): either correct rule 31's parenthetical, or teach the gate to skip
`git check-ignore`d directories. The second is the better fix, since it makes the local and CI
verdicts agree.

## §6 — Disclosures against interest

1. **This session was largely redundant.** caiso-275 was alive and working the same arms the whole
   time; I did not know that until I refreshed `main` at the end. The corroboration has value, the
   duplicated effort did not.
2. **I launched a B-2024 re-solve shard on a false premise.** I believed the year unsolved; it was
   solved, pushed and merely unmerged on `claude/caiso275-b-2024-retry` (`7c40b050`). **I stopped and
   archived the shard before it spent a single LP** and recovered the year with `git checkout`, so
   the cost was zero LP and one wasted container — but the correct move was to check the remote
   branches *before* launching, and I did not.
3. **G-4 was never discharged by me.** I did not measure C1/C2/C4 on either arm and make no claim
   about them; caiso-275's registered composite is what carries that.
4. **My §2/§3 levels are a screen metric**, per the §3 caveat — only the deltas are load-bearing.
5. **My earlier re-stamp of the §5.2 matrix header and my matrix cell append were superseded**
   by caiso-275's own rule-28(b) updates and are not re-applied here (rule 25: one lane, one edit).
