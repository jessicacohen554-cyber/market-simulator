# FINDING — neiso-82: NEISO frontier + `complete` re-assessment against the neiso-81 keeper

**Session:** neiso-82 · **Date:** 2026-08-04 · **ISO:** NEISO (rule 25 [R-ISO-SCOPE]: no other ISO's lane touched)
**Keeper assessed:** `2026-08-04-neiso81-chpheatrate` (bundle `results/calibration/neiso81_chpheatrate_B`)

## 0. Headline

**FRONTIER HOLDS, RE-VERIFIED ON THE NEW KEEPER. `complete` unchanged. `final` NOT proposed
(locked test SPENT). No new declaration. The neiso-81-flagged 2025 re-gate does NOT fire —
the EIA-923 vintage has not landed.** One stale carried-forward number was found and corrected.

**NO RUN WAS PRODUCED IN THIS SESSION** — no LP, no solve, no `run_calibration_full.py`
invocation, no bundle, no dashboard registration. Stated explicitly per rule 15 (the neiso-80
discipline): rule 15's registration duty is not implied-and-skipped here, it is **inapplicable**
because there is nothing to register. Every number below comes from **committed artifacts only**,
via `scripts/calibration_verdict.py --run-id` (which reproduces byte-for-byte), direct reads of
the keeper's committed `hourly/` sidecars, and a re-run of `scripts/audit_eia923_completeness.py`
(a no-LP data audit). Rule 22: no holdout year of either tier was solved, scored, or touched.

Rule 28b: **no mechanism was tested**, so no `mechanism-matrix.js` cell verdict moves and the
matrix is not stamped. Rule 28a honoured — no closed lever was re-opened to manufacture work
(no C3c lever, no CC_CHP host-steam floor, `chp_steam_floor_p25` stays unarmed,
`cc_steam_part_capacity` stays `I`, Kendall stays ADJUDICATED-ARTIFACT).

---

## 1. Q1 — Does the 2026-07-11 frontier declaration still hold on the new keeper?

### YES. Verified on this keeper's own sidecars, not inherited.

The declaration's load-bearing claim is that the in-LP ISO-NE RCPF reserve co-optimization is
**dormant** — reserve dual `$0.00` in every hour of all three years at the published static
requirements. Read from `hourly/reserve_family_<year>.parquet`, the **only** artifact in which a
locational reserve family's binding is observable (`system`'s `reserve_price` is the cross-family
SUM broadcast identically to every zone, so it cannot answer this question).

| Family | Requirement (MW) | Years | Passes | Hours | `dual` min…max | Hours dual≠0 | `shortfall_mw` max |
|---|---|---|---|---|---|---|---|
| `ne_30min_total` | 1,800 | 2023/24/25 | P0, P1 | 8,760 ea | −0.0 … −0.0 | **0** | 0.0 |
| `ne_10min_total` | 1,200 | 2023/24/25 | P0, P1 | 8,760 ea | −0.0 … −0.0 | **0** | 0.0 |
| `ne_10min_spin` | 600 | 2023/24/25 | P0, P1 | 8,760 ea | −0.0 … −0.0 | **0** | 0.0 |

**26,280 train hours × 3 families × 2 passes = 157,680 family-hours, zero exceptions.** The
requirements in the sidecar are exactly the published static 1,800 / 1,200 / 600 MW. **No hour
goes reserve-short, so the frontier basis has NOT moved.**

The attestation's own phrasing — "reserve dual $0.00 in all 26,280 train hours" — is confirmed
exactly (3 × 8,760 = 26,280).

### C3c is bit-unchanged between neiso-81's arms — verified, not inherited

neiso-81 *reported* this; it is now checked directly. Annual P1 maxima, keeper arm B vs the
same-HEAD zero-delta control arm A:

| Year | Control A max | Keeper B max | Identical |
|---|---|---|---|
| 2023 | $248.97 | $248.97 | ✓ |
| 2024 | $218.24 | $218.24 | ✓ |
| 2025 | $280.85 | $280.85 | ✓ |

So no C3c evidence moved in either direction, and the declaration carries forward on its own terms.

---

## 2. Q2 — Is the ledgered C3c caveat still correctly sized and correctly worded?

### Sizing: CORRECT. Wording: correct on the actual side; **one model-side number was STALE**.

**Model side re-verified independently** (keeper `hourly/system_<year>.parquet`, P1 = the scored
pass), on **both** a load-weighted and an any-zone basis — both give the same answer:

| Year | Model hours > $300 | Annual max | Winter (J/F/D) max | Summer (J/J/A) max |
|---|---|---|---|---|
| 2023 | **0** | $248.97 | $233.04 | $81.44 |
| 2024 | **0** | $218.24 | $198.52 | $218.24 |
| 2025 | **0** | $280.85 | $229.76 | $280.85 |

The asserted **model 0h holds in all three years**. The scorer's own per-year rows confirm the
actual-side anatomy describes this run:

- **2023 — CAVEAT:** model 0h vs RT actual **15h**; 10 winter (Feb-3/4 arctic blast ×9 + Feb-26) /
  5 summer; **1 of 15 DA-visible**. ✓ matches the attestation verbatim.
- **2024 — PASS, not a caveat:** model 0h vs RT actual **8h**, small-count |Δ|≤10h. It is *not*
  a CAVEAT row in the verdict. **C3c does not fail in all three years** — the ledgered caveat is
  2023 + 2025 only.
- **2025 — CAVEAT:** model 0h vs RT actual **20h**; 7 winter / 11 summer / 2 shoulder; **6 of 20
  DA-visible**. ✓ matches verbatim.

Determination reproduces exactly: **CALIBRATED-WITH-CAVEATS · 0 FAILs · 1 ledgered caveat (C3c) ·
C1 all 12/12 · free 8/8 · C7 SKIPPED (unscored-protective)**.

### The stale number (miso-116 §7 basis discipline) — FOUND AND CORRECTED

The 2024 exception's `reason` carried **"the energy-only LP tops out at ~$204"**. This run tops
out at **$218.24** (+$14.24, +7.0%). The figure is not merely off for this keeper — it has been
stale for at least four keeper generations:

| Bundle | 2024 P1 max |
|---|---|
| `neiso70_ctheatrate_B` | $218.24 |
| `neiso71_nucavail_B` | $218.24 |
| `neiso72_hy_window_B` | $218.24 |
| `neiso_c156_meter_screen_B` | $218.24 |
| `neiso81_chpheatrate_B` (keeper) | $218.24 |

**Corrected in place** in the keeper's `calibration_attestation.json`, sourced from the keeper's
own `hourly/system_2024.parquet`, **no re-solve**. The edit is to editorial carried-forward
narrative only — `magnitude`, `magnitude_basis`, every scored value and the determination are
untouched, and `calibration_verdict.py --run-id` re-run after the edit returns the identical
determination and identical criterion set. Blast radius was contained: the text appears **only**
in bundle attestations — the dashboard registry sidecar and the ~570 KB run payload
(`runs/<id>.js`) do not carry it, so nothing user-facing was showing the wrong number.

### NOT stale — checked and left alone

**"caps the cold-hour price at dual-fuel oil-parity (~$258/MWh)"** is correct as written. `$258`
is the **oil-parity cap parameter** (it appears independently at
`scripts/run_calibration_full.py:9861`), not a realized maximum. Realized winter maxima ($233.04 /
$229.76) sitting *under* it is consistent — the cap is an upper bound, not an attractor.

Also noted, no action: exception[6] still ledgers the D-3 zero-forcing ablation twin. Rule 20
[R-DOF] was amended 2026-07-14 to no longer require one, and that amendment explicitly permits
already-registered twins to remain as historical artifacts. Correct as-is.

### NEW measured observation — sharpens the declaration, does not overturn it

**The model's closest approach to the $300 threshold is SUMMER, not winter.** Top model hours:

| Year | Top hours | Price | % of $300 |
|---|---|---|---|
| **2025** | **Jun-24 17:00 / 18:00 / 19:00** | **$280.85** | **93.6%** |
| 2025 | Jun-24 15:00, Jun-25 16:00 | $271.85 | 90.6% |
| 2025 | Jun-23 16:00–18:00 | $258.98 | 86.3% |
| 2023 | Sep-07 15:00–18:00 | $248.97 | 83.0% |
| 2023 | Feb-03 18:00–20:00 (arctic blast) | $233.04 | 77.7% |

**The model's entire 2025 top-8 hour set sits on the Jun-23/24/25 heat wave** — i.e. on the exact
DA-visible actual event the caveat names — and gets within **$19.15** of the threshold. This is
independent corroboration of the frontier note's own pointer that the remaining C3c distance is
**summer peak-load-margin offer formation** (its own charter), and it is consistent with Limb A
(measured dynamic requirements) engaging on precisely the 2025-06-24 18:00 hour to produce the
model's first structurally-formed >$300 price. The winter leg is *further* from the threshold than
the summer leg in both caveat years. **No lever was re-opened on the strength of this** (rule 28a);
it is recorded as evidence for whoever charters the summer-formation identification.

---

## 3. Q3a — Has the 2025 EIA-923 vintage landed? **NO. The flagged re-gate does NOT fire.**

This was the session's most important item: neiso-81 disclosed *in advance* that its arm would
look worse on the currently-SKIPPED 2025 C1 rows (CC_CHP 0.013 → 0.640; CC_REGULAR 2.028 → 2.707
against a 2.066 band, i.e. out of band where the control's is barely in).

`scripts/audit_eia923_completeness.py --year 2025` re-run against **current on-disk raw data**
reproduces NEISO's committed block **byte-identically** (`committed['isos']['NEISO'] ==
regenerated['isos']['NEISO']` → `True`):

| Class | Status | `gate` | Plants reporting | Retention |
|---|---|---|---|---|
| CC_CHP | incomplete | **False** | 4/7 (3 missing, 57%) | 0.934 |
| CC_REGULAR | incomplete | **False** | 17/30 (13 missing, 57%) | 0.872 |
| CT_CHP | incomplete | **False** | 9/24 (15 missing, 38%) | 0.276 |
| CT_PEAKER / ST_GAS / ST_CHP / COAL_BIT | immaterial | **False** | — | — |

**No NEISO class is gate-eligible for 2025.** The vintage is still filling in — `last_month` is 12
and the plant-*month* fraction is ~1.0 for plants that reported, but ~43% of prior-year plants have
not reported at all. The scorer's own C1 rows confirm the consequence: 2025 CC_REGULAR and CC_CHP
are `SKIPPED — preliminary EIA-923 vintage`, covered by the C2 family grid reconcile.

**Therefore: no re-score is warranted, the determination does not move, and there is no rule 22
D-5(b) owner escalation.** Per instruction, the vintage has not landed, so nothing is estimated.
The disclosure stands as a live flag for the session that finds `gate: true`.

> **Cross-lane note, deliberately NOT actioned (rule 25).** Regenerating the completeness map also
> rewrote **MISO** figures and **dropped SPP entirely** (committed has 7 ISOs, regeneration
> produces 6). NEISO's block is unaffected. The regenerated file was **reverted** and is not part
> of this session's diff. Flagged for the MISO/SPP lanes; this session does not touch it.

---

## 4. Q3b — Should the CC_CHP undershoot be named in the frontier note?

### RECOMMENDATION: **No.** Leave it where it is — a disclosed keeper residual, not a frontier object.

The residual is real and confirmed from the A/B record — the class flipped from over to under:

| Year | Actual (TWh) | Control A | Keeper B | A error | B error |
|---|---|---|---|---|---|
| 2023 | 1.0717 | 1.3274 (over) | **0.7408 (under)** | +0.2557 | +0.3309 |
| 2024 | 1.1240 | 1.2926 (over) | **0.9523 (under)** | +0.1686 | +0.1717 |

Three reasons not to name it in the declaration:

1. **It is not in the frontier's family.** The 2026-07-11 declaration is scoped to the C3c/C5b
   *scarcity-price-formation* family. CC_CHP volume attribution is a different object; folding it
   in would blur what the declaration actually asserts.
2. **It is unresolvable at C1's grain — provably, in both directions.** The C1 per-class volume
   band is ±1.955 / 2.103 / 2.066 TWh while CC_CHP's *entire annual actual* is 1.072 / 1.124 /
   1.194 TWh — **0.548× / 0.534× / 0.578× its own band**. No CC_CHP outcome can be discriminated
   by its C1 row, so naming it as an open frontier object would advertise an actionable residual
   the gate cannot adjudicate. It is additionally D-10 pinned / `excluded_from_free`, and its 2025
   row is SKIPPED on the preliminary vintage (§3).
3. **Its only named route is closed with evidence.** neiso-71 established that NEISO's merchant
   CC_CHP genuinely carries no host-steam obligation (non-Kendall CC_CHP floor totals 15.0 MW
   across all seven plants; a Kendall-based floor would be a FITTED parameter, rules 21/24).

It is already correctly disclosed as item (iii) of the keeper's `disposition_note` — "a real,
ungated and currently unclosable residual". That is the right altitude. **Recommend, do not
rewrite** — per the session charter this is left as a recommendation to the owner, and the
declaration text was not unilaterally changed to add it.

---

## 5. Governance status — nothing re-declared

| Item | Status |
|---|---|
| **Frontier** (declared 2026-07-11) | **HOLDS.** Carried forward through `2026-08-04-neiso81-chpheatrate`; a `reverified` stamp recording this session's measured basis was added to `keepers/NEISO.json .frontier`. Not re-declared. |
| **`complete`** (validation tier, held since 2026-07-07) | **UNCHANGED.** Already re-keyed to this keeper at neiso-81 with a D-5(b) determination re-verification. No promotion occurred here, so no re-key and no re-verification is due; `determination` re-runs identical anyway. |
| **`final`** (locked tier) | **NOT PROPOSED.** The entry's own `locked_test` note reads *"SPENT, NOT RE-GRANTABLE"* — the 2019 + H1-2026 one-shot was scored once on 2026-07-07 with the frozen neiso-53 config and stands. NEISO's absence from `final` is deliberate and was **not** read as a pending grant. `locked_test_scored_on` is not re-keyed. |
| **Holdout spend** | **NOTHING SPENT.** No solve of any kind; the active holdout spend freeze was never approached. |

## 6. Recommended next lane

**Charter the NEISO `6081_CA1` classification question.** It sits in the LP as a 96.0 MW `oil`
generator with an empty `plant_group` while its three CC1-block CT siblings are
`CC_REGULAR`/`gas_cc`, and CAMPD meters the block on Pipeline Natural Gas at units 001/002/003
with no CAMPD unit for CA1 at all. At 73–91 GWh/yr gross this is a **correctness** question before
a magnitude one. It needs its own charter and its own measured identification — it was **not**
opened here, and `cc_steam_part_capacity` was **not** stamped for it.

Secondary, lower priority: the summer peak-load-margin offer-formation identification that §2's
93.6%-of-threshold observation points at — the one route the frontier note itself leaves open,
and which needs a NEW measured identification rather than any existing lever.

## 7. Files changed

| File | Change |
|---|---|
| `results/calibration/neiso81_chpheatrate_B/calibration_attestation.json` | Corrected stale `~$204` → `~$218` ($218.24) in the 2024 C3c exception `reason`. Editorial text only; determination re-verified identical after the edit. |
| `frontend/data/backcast/keepers/NEISO.json` | Added `frontier.reverified`. Only key added; `keeper`, `note`, `prior_keeper_note`, `disposition_note` and `frontier.declared` / `.note` / `.carried_forward_through` verified byte-identical. |
| `frontend/data/backcast/status/NEISO.js` | Regenerated via `scripts/build_status.py --iso NEISO` (NEISO shard only). |
| `results/calibration/FINDING-neiso82-frontier-reassessment-2026-08-04.md` | This document. |

No bundle was created. `manifest.js` / `benchmark.js` untouched (the Pages deploy is their single
writer). No other ISO's lane touched.
