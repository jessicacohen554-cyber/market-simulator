# PRE-REGISTRATION — caiso-147 `measured_chp_heat_rates` for CAISO (single delta)

**Written and committed BEFORE either arm was solved.** No arm result existed
when this document was frozen. Gates below are final — a gate this document does
not contain cannot be quoted as a pass. Format mirrors
`PREREG-pjm137-measured-ct-heat-rates-2026-07-29.md`, not copied.

Lever: mechanism-matrix §5.2 CAISO queue **item 7**, `measured_chp_heat_rates`,
cells `UUUKUU` (`K` in MISO at miso-99; CAISO `U`). Rule 25 `[R-ISO-SCOPE]`: no
verdict transfers — CAISO derives its own artifact from its own market's data,
and this document scores CAISO on CAISO's evidence alone.

**Promotion is NOT pre-granted** and is not requested in advance by this
document. It remains a separate act, and (rule 22 `[R-HOLDOUT]`) a structural
mechanism change is scored leave-one-year-out within 2023–2025 before promotion.

Base keeper: `2026-07-31-caiso146-ct-heat-rates`, determination
CALIBRATED-WITH-CAVEATS, 0 FAILs, 2 ledgered non-protective caveats (C3a-2025,
C3c-2023/24) carried from the owner's caiso-145 disposition, 1 of 3 slots free,
protective 0/1. CAISO holds **no** rule-22 calibration-complete marker — this
session solves **2023 2024 2025 only** and writes no marker.

---

## §1 — the delta, exactly

`ScenarioConfig.measured_chp_heat_rates: False → True` for CAISO. **One existing
field, one flag, no new mechanism** (rule 19 `[R-ONE-MECH]`; nothing is
stacked). Both arms are replays of the caiso-146 keeper config at the same HEAD;
the control is a zero-delta replay solved in this session, **not** the keeper's
committed bytes (caiso-146 measured the caiso-139 keeper drifting up to 3.2 GW
on a class-hour at HEAD, so committed bytes are not a clean baseline).

The measured rate is eGRID's own published CHP heat-input allocation added back
on the same net denominator:

```
heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN
```

where `PLHTIAN` is heat input allocated to electricity (the incumbent
`PLHTRT = PLHTIAN / PLNGENAN` is exactly this over the same denominator) and
`CHPCHTI` is the useful-thermal allocation eGRID removed. `PLNGENAN` is already
**net** generation, so **no gross-to-net factor is involved** — the reason this
route works where the CEMS route was blocked (`FINDING-miso98` §6.1). Zero
fitted parameters (rule 24 `[R-REGISTRY]`).

**What it replaces in CAISO is NOT what it replaced in MISO, and that is the
point of this session.** CAISO is one of the two ISOs in
`fleet.arrays.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` (CAISO, PJM), so a covered
CAISO plant's incumbent is not eGRID's credited rate — it is that rate times a
**hand factor**: `x1.8` for a CT_CHP under 8.0 MMBtu/MWh, `max(x1.15, 6.3)` for
a CC_CHP under 6.0. The delta here is therefore **hand factor → published
measurement**, which makes this a rule-21/24 win (an off-registry hand number
retired in favour of a citable measurement) on top of the rule-14 accuracy win.
caiso-128 §3 measured that factor **over**-correcting CAISO CT_CHP by +40 %
while five ISOs sit 12–62 % under — a universal factor wrong in both directions
at once.

Plants the measurement does not reach **keep the hand factor untouched**
(`apply_measured_chp_heat_rates` returns a `skip_ids` set that
`_correct_chp_steam_credit_hr` honours). This mechanism does not remove the hand
factor from CAISO; it supersedes it only where a published measurement covers.

---

## §2 — the derive defect found and fixed BEFORE any solve

The shipped derive produced **14 `ok` rows / 1,117 MW** for CAISO, with
`basis_mismatch = 65`. Diagnosed by no-LP probe
(`scripts/probes/_caiso147_chp_basis_gate.py`), the cause is a gate blinded by
the hand factor, not a data wall:

`_flag`'s `_BASIS_TOL` check asks *"is the incumbent rate this eGRID row, or a
boundary repair / `HEAT_RATE_BINS` fallback?"* and compared eGRID's **credited**
rate against the **shipped** model rate. In a hand-factor ISO the shipped rate
is `credited x 1.8` (CT_CHP) or `x1.15` (CC_CHP), so **every hand-corrected
plant reads as a mismatch**. Measured ratio of shipped-to-credited on the
excluded rows: CT_CHP median **1.800**, CC_CHP median **1.150** — the hand
factors exactly. The gate was excluding precisely the population the mechanism
exists to fix, leaving only the 14 plants the hand factor never touched.

Measured: **59 of 65 `basis_mismatch` rows — 3,089 of 3,186 MW — were excluded
by the hand factor alone.** The remaining 6 rows / 96.5 MW are the genuine
repair / bin-fallback mismatches the gate was built to catch (Fresno Cogen,
SDSU, UC Santa Cruz, CSUF, Broadridge, Sierra Nevada Brewing).

**The fix** (`basis_heat_rates()` in the derive, plus a default-`True`
`apply_chp_steam_credit_correction` kwarg on `load_fleet_from_csv`): compare the
credited rate against the incumbent **at the seam where the swap actually
happens** — after the eGRID join and the boundary repairs, before the hand
factor. That is exactly what `apply_measured_chp_heat_rates` overwrites, since
it runs first and hands the hand factor its `skip_ids`.

Governance of the fix:

- **Zero fitted parameters.** It introduces no number. `_BASIS_TOL`,
  `_MAX_THERMAL_SHARE` and the physical bands are untouched.
- **Not a rule-23 `[R-FROZEN-DERIVE]` violation.** This is CAISO's *first*
  derive; the defect was found by code inspection and a no-LP probe **before any
  solve existed**, so no residual was visible and none could have been fitted to.
- **Not a rule-25 `[R-ISO-SCOPE]` violation and not on the DO-NOT-REDO list.**
  It is ISO-generic (see through the hand factor wherever it exists), not a
  CAISO-scoped multiplier, band or exclusion.
- **The gate keeps its full discriminating power** — the 6 genuine mismatches
  still fail it, and every physics gate still applies downstream.
- **MISO is untouched, verified.** MISO carries no hand factor, so
  `basis == model` on every MISO row; the re-derived MISO artifact is identical
  on **every applied value** (only the provenance `source` string, deliberately
  edited, differs), and its applied population is still 5,755 + 977 =
  **6,732 MW** — exactly miso-99's committed figure.

---

## §3 — the artifact, as derived (STEP 1 result, pre-solve)

`data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv`, eGRID2023
(`PLNT23`, the vintage the model's own `heat_rate` is joined from). 92
(plant, class) rows, 4,668.6 MW of CHP.

| flag | rows | MW | meaning |
|---|---|---|---|
| `ok` (applied) | **30** | **2,371.8** | measurement applies |
| `not_unfired_topping` | 44 | 1,914.4 | `thermal_share > 0.50` — boiler-first, excluded on physics |
| `basis_mismatch` | 6 | 96.5 | genuine boundary repair / bin fallback |
| `above_physical_band` | 3 | 251.1 | corrected rate outside the class band |
| `no_chp_credit` | 3 | 19.4 | eGRID applied no credit — nothing to add back |
| `no_egrid_row` | 6 | 15.4 | plant absent from the eGRID vintage |

Coverage, and **energy reach is what matters, not capacity**:

| class | rows | capacity | **metered CAMPD energy (2023)** |
|---|---|---|---|
| CC_CHP | 11/21 | 1,819/2,707 MW (67.2 %) | **7.490/7.490 TWh — 100.0 %** |
| CT_CHP | 19/71 | 553/1,962 MW (28.2 %) | 0.146/0.413 TWh — 35.4 % |

**Validation.** `PLHTIAN + CHPCHTI` reproduces independently metered CAMPD
annual heat input within 1 % on **13 of 13** covered plants, median ratio
**1.00000**. MISO's was 19/22. CAISO's validation is **better**, so the
stop-condition on a materially worse validation is not triggered.

**Direction — two-sided in both classes** (cap-weighted, shipped → measured):

| class | shipped | measured | delta | cheaper | dearer |
|---|---|---|---|---|---|
| CC_CHP | 6.779 | 8.108 | **+1.330 (+19.6 %)** | 1 row / 525 MW | 10 rows / 1,294 MW |
| CT_CHP | 11.935 | 10.196 | **−1.739 (−14.6 %)** | 10 rows / 389 MW | 9 rows / 164 MW |

The two classes move in **opposite directions** — CC_CHP was under-costed, CT_CHP
over-costed. This is caiso-128 §3's "wrong in both directions at once" measured
directly on CAISO's own fleet, and it is the substantive reason a published
per-plant measurement beats a single ISO-keyed factor. 28 of 30 rows move
> 0.5 MMBtu/MWh.

**Known limitations, stated before the solve:**

- **CT_CHP coverage is thin and adversely selected.** 35.4 % of metered energy,
  and the covered plants are the *less* steam-credited ones (cap-weighted
  credited rate 7.167 covered vs 6.377 excluded; thermal share 0.288 vs 0.526).
  CT_CHP is 0.72–0.74 % of model generation, so this is immaterial to the
  determination either way — but it is not a clean identification and is not
  claimed as one.
- **The `not_unfired_topping` exclusion is large** (44 rows / 1,914 MW = 41 % of
  CHP capacity) and is **correct**: median `thermal_share` 0.598 against the
  0.50 EPA-envelope ceiling, and the power-only rate those plants would
  otherwise have taken has median 14.52 and max **58.4** MMBtu/MWh — nonsense
  for an offer rate, exactly the boiler-first case the gate exists to reject.
  Those plants keep the existing eGRID → hand-factor chain.

---

## §4 — predictions (pre-registered, directional AND magnitude)

Baseline (caiso-146 keeper P1, model / actual, % of actual):

| class | 2023 | 2024 | 2025 |
|---|---|---|---|
| CC_CHP | 9.025 / 7.710 = **117 %** | 8.126 / 6.778 = **120 %** | 7.754 / 7.199 = **108 %** |
| CT_CHP | 1.549 / 2.120 = 73 % | 1.535 / 2.008 = 76 % | 1.523 / 1.328 = 115 % |
| CT_PEAKER | 1.726 / 4.128 = 42 % | 0.634 / 4.326 = 15 % | 0.455 / 2.374 = 19 % |
| CC_REGULAR | 48.429 / 51.837 = 93 % | 42.905 / 45.992 = 93 % | 36.376 / 40.590 = 90 % |

**P1 — CC_CHP falls.** It is priced +19.6 % dearer and its D-2 `chp_steam`
forced share is **0.435 / 0.470 / 0.461**, so 53–56 % of its energy is economic
and free to respond. Predicted direction: **down**, from 117/120/108 % toward
actual. Predicted magnitude **0.3–1.5 TWh/yr** (the economic fraction of a
~9 TWh class facing a ~20 % cost increase, bounded below by the floor).

**P2 — CT_CHP barely moves, despite getting 14.6 % cheaper.** Its forced share
is **0.950 / 0.961 / 0.971** — 95–97 % of the class is already pinned at the
`chp_steam` floor, so there is almost no economic headroom for a price cut to
act on. Predicted |Δ| **< 0.15 TWh/yr**. *This prediction is the one most likely
to be wrong, and it is the interesting one: a large CT_CHP move would mean the
floor attribution is not what D-2 says it is.*

**P3 — the displaced energy goes to CC_REGULAR and/or `import`.** Both are
under-produced (CC_REGULAR 93/93/90 %), so a CC_CHP fall should move them toward
actual. The displaced class **will be reported whatever it is**, including if it
is a class this moves the wrong way.

**P4 — CT_PEAKER is the protective exposure, not CHP.** It is C7-gated and C8
peaker-capped; CHP is not (see §5).

---

## §5 — protective checks, with the gate framing corrected

**Correction to the session charter, verified in the scorer's own source.**
`CC_CHP` and `CT_CHP` are exempt from **both** protective gates **by explicit
class list**, not by materiality:

- C7 / D-1: `legitimacy_diagnostics.D1_GATED_CLASSES` = `CT_PEAKER, ST_GAS,
  COAL*` — CHP is absent, and the keeper's own rows read `"gated": false`.
- C8 / D-2: `D2_EXEMPT_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")`.

Both carry the same stated rationale in source: *"host-steam-pinned duty"*. So
although CC_CHP is 3.7–4.3 % of generation — genuinely above the 2 %
`PROTECTIVE_MIN_LOAD_FRAC` line — **the materiality floor is not what governs
it**, and its 0.44–0.47 `chp_steam` forced share is **not** gated by C8. The
charter's premise that CC_CHP "IS gated" because it clears 2 % does not match
what the scorer implements.

Accordingly:

- **CHP D-1 / D-2 numbers are REPORTED as diagnostics, never quoted as a passed
  gate.** Pre-registered baselines: CC_CHP `profile_r` 0.968/0.969/0.988,
  `cv_ratio` 0.374/0.213/0.279, forced share 0.435/0.470/0.461. CT_CHP
  `profile_r` 0.817/0.801/**0.393**, `cv_ratio` 0.006/0.000/0.000, forced share
  0.950/0.961/0.971. *(CT_CHP-2025 `profile_r` 0.393 is already far below the
  0.80 threshold in the incumbent keeper and is ungated — a latent shape
  limitation this session inherits and does not create. It will be reported
  both arms.)*
- **The real protective gates are on the classes that ABSORB the displaced
  energy.** Binding pre-registration: **CT_PEAKER C7 `profile_r` ≥ 0.80 and
  `cv_ratio` ≥ 0.50, and C8 forced share ≤ 0.15**, all three years, in the armed
  arm. The caiso-146 keeper sits at `profile_r` 0.885/0.936/0.864 and forced
  share 0.0016/0.0055/0.0007 — 2025's 0.864 carries only 0.064 of headroom, so
  this is a live risk, not a formality. **ST_GAS and COAL C7 likewise.**
- `legitimacy_diagnostics.json` is generated explicitly for **both** arms
  (`--json-out <bundle>/legitimacy_diagnostics.json`) or C7/C8 score SKIPPED.

---

## §6 — what makes this a REJECT

Judged against the **same-HEAD zero-delta control**, not committed keeper bytes.

**REJECT if any of:**

1. **Any criterion verdict regresses** (PASS → CAVEAT/FAIL) on any load-bearing
   criterion in any year.
2. **A protective gate breaks**: CT_PEAKER (or ST_GAS / COAL) C7 `profile_r`
   < 0.80 or `cv_ratio` < 0.50, or C8 forced share above its cap, in any year
   where the control passed.
3. **The protective caveat budget is spent** — CAISO is at protective 0/1;
   arming must not open a protective caveat.
4. **The mechanism is inert**: max |Δ| on any CHP class-hour < 50 MW in all
   three years. Then the cell is `I`, not `K` — verified live *first*, the
   nyiso-89 §4a check, before any scorecard is read.
5. **A ledgered caveat worsens materially** — see §7.

**NOT a reject, per rule 1 `[R-STRUCT]` and rule 14 `[R-ACCURATE]`:** the
backcast getting worse on C1 or C3a. eGRID's own published CHP allocation is
more accurate than a steam-credited rate that the model then multiplies by a
hand factor. If the fit degrades, that is a **discovered bug** — the accurate
input stays and the root cause is opened as a named successor question. A
degraded fit is reported in full and blocks *promotion*, not the *input*.

---

## §7 — the two ledgered caveats

C3a-2025 (caiso-141 A2 water wall) and C3c-2023/24 (caiso-131 A4) are the
owner's caiso-145 disposition. They **do not forbid this work and do not forbid
it moving them**; they forbid reaching for a mechanism *because* it targets
them. This lever was selected off the §5.2 queue as an accuracy correction and
targets neither.

**Materiality trigger, pre-registered: 1.0 pp on C3a** (the caiso-146
threshold). If C3a moves ≥ 1.0 pp in any year, the mechanism is scored
**leave-one-year-out within 2023–2025** before any promotion is proposed.

Movement in either caveat will be **reported and never tuned toward**, and a
favourable move will **not** be cited as justification. If promotion follows,
the ledger is carried forward as the **owner's caiso-145 act** with provenance
stamped and magnitudes re-measured — **no new disposition is created** (owner
commit `82bd346` precedent).

---

## §8 — mechanics

Both arms replay the caiso-146 keeper at this HEAD, years **2023 2024 2025 in
one invocation** (rule 16 `[R-ALLYEARS]`), the two invocations concurrent
(rule 12 `[R-PARALLEL]`; ~5.5–6.5 GB peak RSS each, fall back to sequential
under ~3 GB available):

```
.venv/bin/python scripts/replay_keeper.py results/calibration/caiso146_ctheatrate_B \
    --out-dir results/calibration/caiso147_control_A --note "..."
.venv/bin/python scripts/replay_keeper.py results/calibration/caiso146_ctheatrate_B \
    --out-dir results/calibration/caiso147_chp_B \
    --set measured_chp_heat_rates=true --note "..."
```

A zero-delta replay restores the source keeper's date into `meta.json`; the
control's timestamp is corrected to the session date **before**
`dashboard_add_run`, so it does not mint a stale run id.

**Deliverables regardless of outcome:** both arms registered on the backcast
dashboard (rule 15), the `measured_chp_heat_rates` CAISO matrix cell updated
with its evidence citation in this session (rule 28b) **including if `R` or
`I`**, and a caiso-147 entry with its own DO-NOT-REDO section in
`docs/calibration-log/caiso.md`. No rule-22 calibration-complete marker is
written for CAISO.
