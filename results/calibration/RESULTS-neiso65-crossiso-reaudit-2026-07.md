# RESULTS — cross-ISO keeper re-audits on the corrected envelope + the CAISO crosswalk (neiso-65, 2026-07-26)

The execution session for the charter verdict recorded in
`docs/handoffs/campd-economic-layup-fix-charter-2026-07.md` §8:
**ADOPTED-AS-IMPROVEMENT, freeze HELD** (owner, 2026-07-26). This document
records (1) the adoption landing, (2) the keeper re-audits on the corrected
envelope for the five ISOs the neiso-64 session did not cover, and (3) the
STEP-D CAMPD↔CAISO resource crosswalk — the charter's highest-value follow-up.

## 1. Adoption landed

- The merit-order guard patches are applied and pushed (still default-off:
  `MERIT_ORDER_GUARD_ENABLED = False`; the committed extracts are guard-ON
  derivations, the code path stays gated).
- All six `campd-unit-outages[-<ISO>].csv` re-derived guard-on and committed,
  with `campd-unit-outages-layup[-<ISO>].csv` companions (no loader reads them).
  2023–2025 reclassification reproduced the neiso-64 numbers exactly where
  published: NEISO 444 windows / 1,083 GW-days, PJM 903 / 4,624,
  MISO 755 / 3,630; and ERCOT 1,352 / 3,986, NYISO 1,146 / 2,868,
  CAISO 355 / 692.
- Guard-off byte-inertness re-verified in this container: a no-flag CAISO
  re-derive reproduced the pre-adoption blob `3dc01fae` exactly.
- The holdout freeze **stays active** (`holdout-freeze.json` history entry
  2026-07-26): the residual over-count (§4 below) is unexplained, so
  out-of-training years stay preserved.
- The `2026-07-25-neiso-64-meritguard-a1` bundle was regenerated
  deterministically (replay of the keeper recipe on the now-committed
  corrected envelope) and its dashboard payload `runs/<id>.js`, `meta.json`,
  `run_config.json` and `legitimacy_diagnostics.json` landed — the API-only
  push path of the prior session could not carry them; this session's git-push
  path can. Reproduction check: registry sidecar byte-identical, every scored
  criterion value identical; the only metrics delta is the grade tally (7→8
  scored) because C8 now scores against the bundle's own D-2 diagnostics
  instead of SKIPPED.

## 2. Method — and a reproduction lesson

Each ISO's **keeper recipe replayed verbatim** (`--replay-bundle`, years
2023 2024 2025, one bundle, rule 16) against the corrected envelope. The A0
arm is the keeper itself: the guard is byte-inert off, so an A0 re-solve is
the keeper by construction (no solve burned on it). Both arms are on the
dashboard whatever the verdict (rule 15).

**Reproduction lesson (cost: two contaminated solves, both caught and
re-run).** `data/clean/` is derived and disposable — a fresh container does
not have it, and several keeper recipes hard-require or silently prefer clean
partitions. Replaying a keeper in a fresh container requires regenerating,
BEFORE solving:

| partition | curate script | recipes that need it |
|---|---|---|
| `transfer-interface-limits` | `curate_transfer_interface_limits.py` | PJM (`pjm_measured_interface_limits`, hard-fails) |
| `ramp-capability` | `curate_ramp_capability.py` | PJM (`measured_ramp_capability`) |
| `capacity-deliverability` | `curate_capacity_deliverability.py` | NYISO (`nyiso_li_lcr_tsl`, hard-fails), CAISO (`capacity_deliverability_limits`, **degrades silently**) |
| `gtc-limits` | `curate_gtc_limits.py` | ERCOT (`ercot_gtc_limits_measured`, **degrades silently** to static TTC) |
| PJM DA virtuals (gitignored raw) | `fetch_pjm_da_virtuals.py` | PJM (`pjm_da_virtual_bids`, hard-fails) |

The two silent degradations (ERCOT static-TTC fallback, CAISO "returning no
limits") produced structurally unfaithful first solves of the ercot-113 and
caiso-120 arms; both were re-solved with the partitions present and only the
faithful solves are registered/quoted. Every log was then audited for
missing-input warnings. NEISO's "zonal load file not found" is NOT a
degradation: `data/raw/zone-specific-demand/` has never carried a NEISO
subdirectory, so the keeper itself solved on the identical fallback (and the
a1 metrics reproduce exactly).

## 3. Per-ISO verdicts

| ISO | arm | mean-LMP move | verdict |
|---|---|---|---|
| NEISO | `2026-07-25-neiso-64-meritguard-a1` | −1.0 to −1.7 % | **FIX-IN-PLACE** (neiso-64: C3a and C3b improve in all 3 years, nothing regresses) |
| ERCOT | `2026-07-26-ercot113-meritguard-a1` | ≤0.2 $/MWh | **FIX-IN-PLACE (insensitive)** |
| CAISO | `2026-07-26-caiso120-meritguard-a1` | +0.3 to +0.5 $/MWh | **RE-TUNE REQUIRED** (2025 C3a PASS→FAIL) |
| NYISO | `2026-07-26-nyiso73-meritguard-a1` | −4.0 to −6.1 $/MWh | **RE-TUNE REQUIRED** (largest sensitivity; 2023 flips to PASS across the board, 2024–25 over-relieved) |
| PJM | — | — | **BLOCKED — container RAM** (see §3e) |
| MISO | — | — | **BLOCKED — container RAM** (see §3e) |

No keeper was changed. The two RE-TUNE verdicts are keeper-lane work items,
not this charter's scope; until re-tuned, those keepers' registered numbers
describe solves against the pre-adoption envelope and no longer reproduce at
HEAD.

### 3a. ERCOT (`ercot113_meritguard_a1`) — insensitive, and why

| criterion | 2023 A0→A1 | 2024 A0→A1 | 2025 A0→A1 |
|---|---|---|---|
| C3a mean LMP | −27.1 → −27.4 % (FAIL both) | −8.5 → −8.6 % (PASS) | −8.3 → −8.3 % (PASS) |
| C3b NRMSE | 0.531 → 0.530 (FAIL both) | 0.142 → 0.144 (PASS) | 0.106 → 0.106 (PASS) |
| C3c h>$200 | 70 → 68 (FAIL both) | 12 → 12 (FAIL) | 0 → 0 (FAIL) |

Every status unchanged. ERCOT had the largest reclassification share of any
ISO (28 % of window GW-days) yet the keeper barely moves, because the
keeper's availability envelope is owned by the **measured thermal DAM
availability overlay** (`ercot-thermal-dam-availability.csv` class-target
redistribution); the CAMPD extract only shapes the plant-grain distribution
beneath those class targets. The corrected extract is still the right input
(rule 14) — it just isn't load-bearing for ERCOT's class-level envelope.
LOYO: trivially satisfied (no year moves).

### 3b. CAISO (`caiso120_meritguard_a1`) — re-tune required

| criterion | 2023 A0→A1 | 2024 A0→A1 | 2025 A0→A1 |
|---|---|---|---|
| C3a mean LMP | +3.5 → +3.6 % (PASS) | +8.4 → +9.2 % (PASS) | +10.0 → **+11.1 % (PASS→FAIL)** |
| C3b NRMSE | 0.072 → 0.072 (PASS) | 0.136 → 0.140 (PASS) | 0.141 → 0.149 (PASS) |
| C3c h>$200 | 0/47 (FAIL both) | 0/35 (FAIL both) | 0/8 small-count (PASS both) |

Direction: restoring laid-up capacity *raises* CAISO model prices slightly —
the envelope interacts with the RA must-offer commitment bridge
(`caiso_ra_mustoffer`, default-on) rather than with a scarcity margin — and
2025's C3a crosses the +10 % line. Uniform-direction drift, no year traded
(LOYO clean); but a threshold flip on a load-bearing criterion is exactly the
charter-§5 rule-11 condition: the keeper's offer calibration was leaning on
the inflated outage envelope. Re-tune in the CAISO lane.

### 3c. NYISO (`nyiso73_meritguard_a1`) — re-tune required, largest sensitivity

| criterion | 2023 A0→A1 | 2024 A0→A1 | 2025 A0→A1 |
|---|---|---|---|
| C3a mean LMP | +18.3 % FAIL → **−0.4 % PASS** | +1.8 → −8.8 % (PASS) | −2.4 → −11.2 % (PASS→FAIL) |
| C3b NRMSE | 0.223 FAIL → **0.120 PASS** | 0.176 → 0.195 (PASS) | 0.152 → 0.195 (PASS) |
| C3c h>$300 | 21/10 FAIL → **5/10 PASS** | 10/12 → 3/12 (PASS→FAIL) | 27/42 → 13/42 (PASS→FAIL) |

NYISO booked **46 %** of its CC capacity-year as outage — the worst
over-count of the six (neiso-63) — and shows the largest correction: mean LMP
−10 to −16 %. The keeper's worst year (2023, its only C3a/C3b FAILs) flips to
PASS on all three price criteria: the 2023 over-pricing WAS the phantom
outage envelope. 2024–25 over-relieve (under-priced tails), i.e. the keeper's
offer margins were calibrated against the inflated envelope throughout
(rule 11). Re-tune in the NYISO lane. Caveat stands: NYISO has **no published
outage instrument**, so its corrected extract itself remains UNVERIFIED — the
re-audit measures keeper sensitivity, not extract correctness.

### 3d. NEISO — done in neiso-64 (fix-in-place); nothing new this session.

### 3e. PJM and MISO — RAM-blocked, not skipped

Both keeper recipes exceed this container's 15 GB during a single year's LP:

- MISO (`miso88_egrid_hr` recipe, per-asset reserve columns, 2,550 members):
  OOM-killed at 15.9 GB RSS / 31 GB VM — twice, including running **alone**.
- PJM (attempted on the then-keeper `pjm119_overlay_restore` recipe, per-gen
  reserve co-opt, 2,403 members): completed 2023 solo, OOM-killed at 15.9 GB
  in 2024's build.

Per CLAUDE.md (GitHub-Actions section): the session reports the limit rather
than offloading to CI. The two replays need a ≥24 GB environment; the
commands are one-liners (`--replay-bundle results/calibration/miso88_egrid_hr
--year 2023 2024 2025 --out-dir results/calibration/miso89_meritguard_a1`,
same shape for PJM into `pjm122_meritguard_a1`), with the §2 clean partitions
regenerated first. PJM's completed-2023 partial bundle was NOT registered
(rule 16 — no partial-year bundles), no numbers from it are quoted, and the
partial dirs were deleted rather than committed — the future replay
regenerates them whole.

**PJM keeper superseded mid-session (2026-07-26, parallel lane):** while this
session ran, the owner promoted `2026-07-25-pjm-121-cc-belt` (10/10 PASS,
one config delta vs pjm-119: `pjm_offer_midcurve_segments` gains `CC_LIKE`)
and pruned the pjm-116…119 netrev lineage including the
`pjm119_overlay_restore` bundle this session attempted to replay. The future
PJM re-audit therefore targets `--replay-bundle
results/calibration/pjm121_ccbelt` (same RAM class — the delta is an offer
surface, not the LP size). pjm-121 was solved 2026-07-25, i.e. on the
pre-adoption envelope, so it carries exactly the A0 semantics this method
requires.

## 4. STEP D — the CAMPD↔CAISO resource crosswalk

CAISO's Curtailed and Non-Operational Generator (CNOG) report is
per-resource; neiso-64 could only use it through a resource-NAME heuristic
(honest null, 0/3 placebo, extract at ~⅓ of a scope-mismatched whole-fleet
total). This session turned it into per-plant ground truth:

- **Crosswalk review** (`data/raw/reference/caiso-resource-eia-crosswalk.csv`):
  34 accepted rows / 29 plants → **58 rows / 44 of 55 thermal plants,
  ~20.9 GW** of resource capacity. 13 candidate acceptances (Ormond Beach 1–2,
  Moss Landing blocks 1–2, Mountainview PSP3–4, Delta, Elk Hills CC, Sunrise,
  Los Esteros, Glenarm 5, Gilroy cogen, Huntington Beach steam 2); 3
  wrong-plant remaps — the new-CC-at-old-steam-site trap the builder's
  docstring warns about (Alamitos Energy Center → 62115, Huntington Beach
  Energy → 62116) plus Harbor Cogen → 50541; 8 rows the generator missed
  (Alamitos steam 3/4/5 → 315, Redondo 5/6/8 → 356, El Segundo EC 5/6 + 7/8
  → 57901). Refinery/campus CHP resources stay unaccepted for precision — the
  crosswalk also feeds the solve overlay (`caiso_dam_outages`), so a wrong
  pairing would enter dispatch, not just scoring.
- **Scorer**: `scripts/probes/_neiso65_caiso_crosswalk_score.py` — CNOG
  deduplicated to one row per outage `mrid` (the raw parquet repeats each
  outage on every trade date it was reported: 794,103 rows over 151,758
  mrids = **5.23×**, and 64.7 % of multi-segment mrids carry time-overlapping
  segments, so raw summing over-counts exactly as the charter warned), ambient
  capability derates excluded, both sides restricted to the crosswalked
  plants.

**Result (2023 / 2024 / 2025), crosswalked scope:**

| | level | monthly r |
|---|---|---|
| baseline | 1.38× / 0.84× / 1.00× | +0.55 / +0.81 / +0.82 |
| guard on | 1.13× / 0.77× / 0.93× | +0.55 / +0.78 / +0.84 |
| placebo p95 | | +0.60 / +0.84 / +0.85 → all "inside" |

**Active-plant scope** — excluding the ten crosswalked plants whose CAMPD
extract has no windows at all. Those are the long-term non-operational units
(Ormond Beach: 1,194 MW published mean; Alamitos steam: 927 MW; Huntington
Beach steam, Desert Star, El Segundo, Watson, Crockett): CNOG books
mothball/seasonal-RMR states as non-operational capacity, which the model
owns through fleet status, not the outage overlay. On the 34 plants where
the CEMS detector has signal:

| | level | monthly r |
|---|---|---|
| baseline | **1.85× / 2.19× / 2.28×** | +0.69 / +0.79 / +0.81 |
| guard on | **1.52× / 2.02× / 2.13×** | +0.69 / +0.77 / +0.83 |

**What this changes.** The scope excuse is gone for CAISO: on a per-resource,
same-plant comparison the CAMPD detector still books **1.5–2.3×** the
published outage MW after the guard. The residual over-count the charter's
verdict held the freeze for is now measured at TWO ISOs with clean
instruments (NEISO 1.29–1.36× whole-fleet; CAISO ~2× per-resource,
active-plant scope), and it is NOT explained by whole-fleet-vs-thermal scope.
The shape axis stays an honest null (placebo "inside" all years — CAISO's
correlation was already decent and the guard's GW-days are small here), and
the vetoed windows sit at 0.07–0.25× of published outage level, i.e. the
guard is not deleting published-outage mass. Direction of the remaining
error: either the detector books short economic cycling below the guard's
90 % out-of-merit threshold as outage, or CNOG (a DAM prior-trade-date
snapshot) under-reports intraday forced outages — both directions stated;
neither is resolved here.

## 5. Follow-ups this session leaves open

1. **PJM + MISO re-audits** in a ≥24 GB environment (§3e — commands ready).
2. **CAISO + NYISO keeper re-tunes** on the corrected envelope (their lanes).
3. **The residual over-count root-cause** (NEISO level + CAISO per-resource
   level agree it survives the guard) — the freeze's lift condition.

(A fourth item — the `pjm-121-cc-belt` payload gap — was resolved in
parallel by the 2026-07-26 payload-backfill session while this one ran.)
