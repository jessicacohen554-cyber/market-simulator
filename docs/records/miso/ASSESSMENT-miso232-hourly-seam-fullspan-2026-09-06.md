# ASSESSMENT miso-232 — the HOURLY neighbour-anchored PJM seam ladder, full span, is PROMOTED. **DETERMINATION CALIBRATED**, C3c the single ledgered caveat.

**KEEPER → `2026-09-06-miso-232-hourly-seam`** (bundle `miso232_hourlyseam_K`), promoted from
`2026-09-06-miso-230-ctdrag-seam`. Rule 22: 2023–2025. DOF ledger **unchanged at 41/2**.
Pre-registration: `PRECOMMIT-miso232-hourly-seam-fullspan-2026-09-06.md` (pushed at `451e6109`
while the LP ran, before any year's bundle was opened).

---

## 0. Provenance, stated first: THE SCREEN DID NOT CLEAR ITS GATE

The miso-231 2024 screen was **KILLED on G-1 by 0.0183** — the pre-registered bar required
`corr(imports, own model hub price)` to fall ≥ 0.30 from the keeper's own 2024 +0.4461 and it
fell 0.2817 (`FINDING-miso231-hourly-seam-screen-2026-09-06.md`, `_miso231_screen_gates.json`).
The bar was not moved and the lane did not spend the remaining years.

**The full span was authorized by OWNER RE-CHARTER** under the 2026-09-06 standing steer (*"if
structural integrity improves but gates regress that may still be a keeper"*) — rule 29(2)'s
owner step, and the escalation route the miso-231 PRECOMMIT §5 pre-registered for this outcome.
The grant was to solve the span; it was not a finding that the gate passed and it did not lower
the bar. This run is a keeper because the span **scored CALIBRATED under the miso-227 promotion
rule** (promote on CALIBRATED / CALIBRATED-WITH-CAVEATS; escalate a load-bearing NOT-YET), not
because the screen passed.

## 1. The determination

| criterion | tier | verdict |
|---|---|---|
| C1 fuel mix | LOAD | **PASS — 16/16 all-class, 12/12 free-class** |
| C2 system volume | LOAD | PASS |
| C3a mean LMP | LOAD | PASS (+6.2 / +3.2 / −5.5 %) |
| C3b price duration/shape | LOAD | PASS (NRMSE 0.101 / 0.107 / 0.131) |
| C3c price tail / scarcity | SUPP | **CAVEAT (ledgered, non-downgrading — rubric v3.3)** — 3/7/11 vs 30/37/88 h, unchanged |
| C4 dispatch correlation | SUPP | PASS (gas r 0.960/0.960/0.968; coal 0.910/0.894/0.902) |
| C6 governance | PROT | PASS |
| C8 forced-energy share | PROT | **PASS — CT_PEAKER grounded above budget, all three years** |

2025 C1 and C2 are **SKIPPED** on the preliminary EIA-923 vintage and are not read as evidence.

## 2. The single delta

`miso_seam_neighbour_hourly_ladder=true` on the miso-230 recipe, via `replay_keeper --set`. Band
`k`'s import offer becomes `pi_k(t) = pjm_border(t) + delta_k`, the measured hourly PJM
western-border DA plus a frozen offset that is a quantile of the DA-minus-border spread at the
ladder's fixed depth grid (`derive_pjm_neighbour_hourly`). Zero fitted parameters; the derive is
frozen under rule 23 and was not re-run. It displaces the annual neighbour overlay on the seams it
covers (rule 19); SPP / South / Manitoba keep the incumbent anchor for want of a measured price
series (rule 14's misalignment clause, disclosed in the miso-231 PRECOMMIT §2).

**G-DRIFT** `284722a04..HEAD`: all hunks INERT (PRECOMMIT §2 — main's four post-Addendum-B hunks
are an ERCOT-gated helper revert, a PJM constant import, a PJM ISOConfig override and a cache
docstring; MISO `surface_stamp` reads `moved: {}`). The keeper's committed bundle was the control
(form 4). **No control solve was spent.**

## 3. What the mechanism did — the full span reproduces the screen in every year

2024 reproduces the screen byte-for-byte (imports 29.751 TWh, corr +0.1644, cheap-hour 3,321.6 MW).
All numbers from the committed `hourly/` sidecars; "measured" is the MISO-Indiana hub RT price and
the EIA-930 seam record the miso-225/226 comparators use.

| year | statistic | keeper | **arm** | MEASURED |
|---|---|---:|---:|---:|
| 2023 | corr(imports, own model price) — the G-1 basis | +0.7036 | **+0.1754** (fall 0.528) | (−0.101 ref) |
| | corr(imports, measured price) | +0.3247 | **−0.0823** | −0.136 |
| | decile slope d1−d10, measured price | −3,073 MW | **+139 MW** | +1,303 MW |
| | cheap-hour (<$20, n=1,230) imports | 3,594.8 MW | **4,892.6** (+1,298) | — |
| | gross imports | 48.305 TWh | **44.763** (−3.54) | — |
| 2024 | corr, own price | +0.4461 | **+0.1644** (fall 0.282) | |
| | corr, measured price | +0.3211 | **−0.0636** | −0.039 |
| | decile slope, measured price | −3,322 MW | **+111 MW** | +1,384 MW |
| | cheap-hour (n=2,111) imports | 2,129.3 MW | **3,321.6** (+1,192) | — |
| | gross imports | 31.294 TWh | **29.751** (−1.54) | — |
| 2025 | corr, own price | +0.7951 | **+0.0368** (fall 0.758) | |
| | corr, measured price | +0.3455 | **−0.0852** | −0.059 |
| | decile slope, measured price | −3,063 MW | **+681 MW** | +948 MW |
| | cheap-hour (n=395) imports | 928.0 MW | **2,606.3** (+1,678) | — |
| | gross imports | 24.239 TWh | **21.504** (−2.74) | — |

- **The seam's price response changes SIGN in every year.** On the published comparator basis the
  correlation crosses zero and lands within 0.05 of the measured value in all three years. No
  prior arm on record had flipped the slope.
- **The 0.30 own-price bar is cleared in 2023 (0.528) and 2025 (0.758) and missed in 2024 (0.282)
  exactly as the screen measured.** This is reported, not used: the screen year was 2024, it
  failed, and the span exists by re-charter.
- **G-3 confinement holds:** slack 0 / 0.0196 / 0 TWh and dump 0 in every year, unchanged from the
  keeper (the 2024 slack is the keeper's pre-existing 0.0196).
- **The mechanism REDISTRIBUTES import energy; it does not add it.** Gross imports fall 1.5–3.5
  TWh per year while imports in the hours the measured seam flows most rise 1.2–1.7 GW.

## 4. Collateral — G-4 scored for the first time, and the pre-named CT_PEAKER risk did not materialise

`scripts/screen_collateral_gate.py` (this session's fix for the miso-231 hole, §7) runs the real
scorer in memory on the unregistered bundle against the committed bench parts: **ZERO
PASS→FAIL flips.** Of the 16 scored C1 cells **13 move toward actual and 3 away**:

| C1 cell (TWh, model − actual) | keeper | arm | move |
|---|---:|---:|---|
| **CT_PEAKER 2023** (the miso-227 cell; band ±8.00) | −4.39 | **−3.29** | toward |
| **CT_PEAKER 2024** | −3.37 | **−2.28** | toward |
| COAL_PRB 2023 / 2024 | −3.35 / −4.77 | −2.00 / −3.66 | toward |
| COAL_BIT 2023 / 2024 | −3.66 / −4.31 | −3.06 / −3.68 | toward |
| ST_GAS 2023 / 2024 | −0.54 / −5.59 | +0.29 / −5.16 | toward |
| CC_REGULAR 2024 | +5.43 | +4.09 | toward |
| **CC_REGULAR 2023** | −5.92 | **−6.31** | **away** |
| **CC_CHP 2024** | −0.51 | **−0.73** | **away** |
| **ST_CHP 2024** | −2.74 | −2.76 | away (0.02) |

Reported at full magnitude against the candidate: **C3a moves away in 2023 (+4.6 → +6.2 %) and
2024 (+1.7 → +3.2 %)** and toward in 2025 (−8.7 → −5.5 %), all inside ±10 %; C3b and C4 improve in
every year. **CT_PEAKER forced share falls** 49.2 / 31.2 / 34.0 → 42.2 / 27.2 / 25.1 %, still above
the 15 % cap, so C8 passes only through rule 18's grounded route (D-4 off-window PASS; class D-1
profile r 0.977/0.984/0.982, cv ratio 1.76/1.57/1.65), as it did for the keeper. **Coal D-1**
(non-gating, attributed and closed by miso-231 — not re-opened): the keeper's four fails shrink to
one — COAL_PRB cv ratio 0.488/0.492/0.389 → 0.535/0.548/**0.460 (still FAIL)**, COAL_BIT-2024 0.387
→ 0.514. Reported, not claimed.

## 5. Pre-committed NON-CLAIMS, carried onto the determination basis

1. **The decile slope is repaired in SIGN, not in MAGNITUDE** — +139 / +111 / +681 MW against
   measured +1,303 / +1,384 / +948, i.e. 11 / 8 / 72 % of the measured value. A partial repair.
2. **C3c is UNTOUCHED** (3/7/11 tail hours vs 30/37/88, byte-identical to the keeper). No scarcity
   claim of any kind; C3c stays the designated frontier (2026-07-20).
3. **G-2 annual volume was WITHDRAWN as a gate, not passed.** Gross imports fall 3.54 / 1.54 / 2.74
   TWh; the model's gross reference-node import class is not comparable to the measured net seam
   total (miso-231 Addendum A.2), so no volume claim is made in either direction.
4. **The screen failed G-1 by 0.0183.** The span exists by owner re-charter.

## 6. Rule 15 — keeper-only retention

MISO now carries exactly one registered run. `2026-09-05-miso-217-intermphys`,
`2026-09-05-miso-220-nonsteam-lift` and `2026-09-06-miso-230-ctdrag-seam` were pruned via
`scripts/prune_iso_runs.py --iso MISO --force-uncite` (sidecar, payload and bundle together). The
keeper shard's superseded/promotion notes and the matrix shard now cite runs no longer on the site,
by design (`audit_keepers` treats narrative citations as out of scope); nothing is retracted and
git history is the record. The keeper's `hourly/` sidecars (`class_hourly`, `class_band_hourly`,
`system`, `reserve_family`, `storage`) are committed.

## 7. Fixed in passing — the G-4 hole in every MISO screen

`scripts/screen_collateral_gate.py` + `tests/scoring/test_screen_collateral_gate.py`. The scorer
resolves only a registered run and rule 29(2) forbids registering a screen bundle, so miso-231
could score only three of five gates. The tool assembles the payload exactly as registration
would, round-trips it through the `runs/<id>.js` codec, holds the bench fixed at the committed
parts, and compares record-by-record with the keeper's committed verdict. STOP-only; exit 1 on a
flip; nothing it prints is a determination. Documented in `scripts/README.md`.

## 8. Governance

Rule 1 `[R-STRUCT]`: the screen bar was not moved and the span is an owner step, stated in place
on every surface (attestation, sidecar, keeper shard, matrix, this doc). Rule 12: years
sequential, solved in-session (~45 min, 13 GB + swap). Rule 13: the hourly border price is a
purchased-input price with a forward analogue in the code. Rule 15: registered and pruned in this
session. Rule 16: one invocation, one bundle. Rule 19: displaces, never stacks. Rule 21: 41/2.
Rule 22: 2023–2025; MISO holds no `complete` marker and no holdout year was touched. Rule 23: no
derive re-run. Rule 28(b): `seam_neighbour_hourly_ladder` O → K, keeper and gates re-stamped in
`mechanism-matrix/MISO.js`, §5.4 header re-stamped; `check_mechanism_matrix.py --base origin/main`
clean. Rule 29: phase 0, screen, G-DRIFT all precede this; keeper as control; the screen bundle was
deleted by miso-231 before its merge. Rule 27: every pushed blob verified against local.

**Open after this promotion, named and not started:** the slope's magnitude gap (the remaining
~90 % in 2023/2024); the CC_REGULAR-2023 give-back; the SPP / South seams' unmeasured price
series; and C3c, which needs its own charter.
