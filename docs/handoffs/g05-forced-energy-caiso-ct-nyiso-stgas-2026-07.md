# G-05 — rule-20 forced-energy determination: CAISO CT + NYISO ST_GAS

**Date:** 2026-07-07 · **Gap:** G-05 (gap-register-2026-07.md) · **Rules:** 1, 12, 15, 19, 20, 21

## The question

G-05 flags that the rule-20 forced-energy budget is breached by 4/6 keepers'
committed bundles, disclosed via the C8-hard NOT-YET verdict, while the rule's
*letter* says "a keeper fails". This memo adjudicates the two classes the
rubric still flags **materially** (≥ 2 % of ISO load): **CAISO CT_PEAKER** and
**NYISO ST_GAS**. (ERCOT/PJM CT are single-year and immaterial; MISO CT/ST are
owned separately under G-23.)

For each class the test is CLAUDE.md **rule 15**: is the forcing a legitimate
structural reliability-commitment mechanism (keep + disclose, the caiso-58
precedent), or an **over-broad floor binding in hours its own driver evidence
says the class is offline** (a bug — replace/reconcile with the real driver)?

The authoritative discriminator is **not** the D-2 forced *share* (a high share
alone is not a bug — caiso-58 established this by owner decision) but the
**D-4 off-window test read against the measured CAMPD hour-of-day capacity
factor**: does the floor bind only in the hours the class actually runs?

## Determination: BOTH LEGITIMATE (keep + disclose)

| class | mechanism | D-2 forced share | D-4 off-window | measured driver evidence | verdict |
|---|---|---|---|---|---|
| CAISO CT_PEAKER | `ct_netload_drag` [15,22) | 59.7 / 65.9 / 65.4 % | **0.0 %** all yrs | overnight CT CF ≈ 0.016 (h0-6); drag windowed to the evening ramp | **LEGIT** |
| NYISO ST_GAS | `reliability_floor` (persistent-24h base + evening ramp) | 60.8 / 69.8 / 59.7 % | 0 % (see note) | NYC/LI overnight CF 0.11–0.17, **online 100 % of year** — a genuine 24h base | **LEGIT** |
| NYISO CT_PEAKER *(2nd-order, immaterial)* | `reliability_floor` HB14-21 ramp | 76 / 70 / 39 % | 27 % → **0.0 %** after window fix | measured h14 CF 0.11–0.23 — ramp start_hour=14 is driver-supported | **LEGIT** |

### CAISO CT_PEAKER — legitimate (confirms caiso-58)

The `ct_netload_drag` is a CAMPD-net-load-regressed, ramp-windowed [15,22)
min-gen floor. Its committed D-4 off-window share is **0.0 % in all three
years** (`caiso58_v2_regate/legitimacy_diagnostics.json`): every floored MWh
falls inside the h15-21 evening ramp. The CAMPD derivation
(`docs/caiso-ct-netload-drag-2026-06.md`) measured overnight CT CF ≈ 0.016
(h0-6) vs ≈ 0.38 at the afternoon cooling peak — the drag correctly **excludes**
the hours the fleet is physically offline. High forced share, clean rule-15
test → disclosed-legit reliability commitment, exactly as the owner decided for
caiso-58 (rule 1 dominates the rule-20 letter). No change.

### NYISO ST_GAS — legitimate

The ST_GAS forcing is dominated by the NYC/LI **"persistent 24h base"**
reliability-floor limbs (`reliability_floor_coeffs_NYISO.csv`: NYC floor_pct
0.391, LI 0.289, threshold −50 °C ⇒ always flagged, no sub-daily window),
plus the HB14-21 evening ramps.

Measured CAMPD hour-of-day CF of the downstate steam fleet (of nameplate),
pooled per zone:

| zone | npl | 2023 overnight(h0-6) / min / online | 2024 | 2025 |
|---|---|---|---|---|
| **NYC** | 4319 MW | 0.118 / 0.113 / **100 %** | 0.122 / 0.115 / 100 % | 0.159 / 0.144 / 100 % |
| **Long_Island** | 2731 MW | 0.120 / 0.101 / **100 %** | 0.153 / 0.125 / 100 % | 0.170 / 0.143 / 100 % |
| Capital_Hudson | 3021 MW | 0.029 / 0.025 / 25 % | 0.039 / 33 % | 0.083 / 54 % |
| Upstate_West | 208 MW | 0.362 / 0.354 / 96 % | 0.388 / 97 % | (all limbs disabled) |

The NYC and Long Island steamers — the two zones carrying the persistent-base
limbs and ~10 TWh/yr of the class — are **online 100 % of the year with an
overnight CF that never drops below ≈ 0.11**. They genuinely run a persistent
24h reliability base (downstate DARU/SRE local-reliability commitments + steam
boiler minimum-run blocks), the **opposite** of the CT overnight-offline
signature. The floor binds where the class actually operates — it is **not** a
rule-15 bug.

Corroborating evidence:
- **D-1 diurnal shape PASSES** for ST_GAS every year (profile r 0.947 / 0.942 /
  0.947; off-peak CV ratio 0.68–0.88) — the floored dispatch tracks the measured
  profile; it is not a caiso-42-style flat line.
- **Ablation twin** (`nyiso53_litsl_v2-ablation`): the floors buy ST_GAS
  +2.7/+3.8/+3.9 TWh, and **even with them the class still under-runs the
  measured actuals** (model 7.2/8.1/10.3 vs 8.7/11.1/16.0 TWh) — the forcing
  moves dispatch *toward* the measurement, never past it (rule-1 keeper test).

**Mechanism choice (rules 19/21 — one mechanism per phenomenon).** The
alternative was to switch ST_GAS onto the forward-native `gas_st_netload_drag`
(windowed [15,22), the drag coeffs are present but off). That would be **wrong
here**: the drag is the correct mechanism for a class that is *offline overnight*
(CTs), but downstate steam runs a genuine 24/7 base — a windowed [15,22) drag
would UNDER-commit the measured overnight base and make the model *less*
faithful. Steam base ≠ CT evening ramp: two different phenomena, two different
mechanisms. The reliability-floor persistent-24h base is the correct one, and it
already owns the class (the drag is off, so no double-floor / rule-19 stack).

### NYISO CT_PEAKER — legitimate (diagnostic-window fix)

Second-order (immaterial, ~1.5–2.1 % of load) but on the same mechanism, so
resolved here. The enabled NYC/LI CT reliability limbs are the HB14-21 evening
ramps (`NYC_CT_ev` / `LI_CT_ev`, start_hour=14); the unwindowed 24h hot step is
already R1-disabled. Measured downstate CT CF at **h14 is 0.11–0.23** (CAMPD
2023-25 pooled) — squarely inside the class's active ramp. The D-4 justified
window was inherited from the `ct_netload_drag` [15,22) and mislabeled that
legitimate h14 binding as off-window (~27 %). Correcting the
`reliability_floor × CT_PEAKER` window to the driver-derived **[14,22)**
(`scripts/legitimacy_diagnostics.py` `D4_WINDOWS`) drops the off-window share to
**0.0 %** — the floor binds *entirely* within its measured-active window. Not a
bug; a diagnostic-window artifact. The change affects only NYISO (the sole ISO
whose CT ramp starts at h14; MISO's is [15,21], ERCOT/PJM are 24h hot-day) and
can only *lower* an off-window share, so it never newly-fails an ISO.

## Why no faithful model change applies (rule 1)

The measured downstate steam and CT fleets genuinely dispatch 60 %+ of their
energy as out-of-merit reliability commitment. Any change that pushed the D-2
forced share under the 30 %/15 % caps would have to **delete real market
structure** to hit a number — forbidden by rule 1 ("never reach the right number
through a mechanism that isn't real … a real market behaviour stays in even if
it makes the fit worse"). The floors already move dispatch *toward* (never past)
the measurement, and both classes pass the rule-15 D-4 test. The correct
resolution is therefore **keep + disclose**, identical to the owner's caiso-58
decision — the rule-20 budget is a disclosure/NOT-YET flag for these classes,
not a hard blocker.

## Deliverable

**No new keeper, no model change.** The NYISO keeper recipe was re-solved at HEAD
purely to test for drift; it reproduced **byte-identically** (0/12 metrics differ,
per-plant dispatch matches nyiso-53 exactly), so nyiso-53 is already HEAD-faithful.
A byte-identical duplicate is not a keeper (rule 1), so the throwaway re-solve was
discarded and the two real deliverables were applied to **nyiso-53 in place**:

- Diagnostic reconciliation: `D4_WINDOWS[(reliability_floor, CT_PEAKER)]` →
  [14,22) (and CT_CHP), driver-derived, blast-radius NYISO-only. nyiso-53's
  committed `legitimacy_diagnostics.json` regenerated (payload path — the
  CI-reproducible convention): D-4 now PASSES (CT off-window 0.0% all years).
- G-05 determination recorded in nyiso-53's `calibration_attestation.json`
  governance note; its existing zero-forcing ablation twin + DOF ledger stand.
  Determination stays NOT-YET (disclosed hard breach, rule-1 faithfulness).
- CAISO unchanged (caiso-58 already the disclosed-legit keeper; this memo
  confirms it).
- G-05 struck to CLOSED with this evidence.

### Note on committed forced-share numbers (payload vs parquet)

The committed `legitimacy_diagnostics.json` D-2 shares (ST_GAS 60.8/69.8/59.7%,
CT 76.2/70.1/39.4%) come from the **dashboard payload** path — a curated ~100-of-
276-plant CAMPD-benchmarked subset — which is what CI's G-06 gate reproduces and
what every keeper's committed artifact uses. The full-fleet parquet share is
higher (ST_GAS ~65/76/61%, CT ~95/84/46%) but is not committed (parquets are
gitignored) or CI-checked. Both breach the caps and both pass the rule-15 D-4
test, so the determination is identical either way; the committed convention is
the payload path.

## Addendum 2026-07-09 — ST_GAS grounded under rubric v2.2 (drag re-adjudicated, rejected again)

Two things changed after this memo was written: (a) rubric v2.2 added the
grounded-above-budget C8 escalation (above-cap passes iff every binding
mechanism clears a **declared** D-4 window and D-1 shape clears), under which
the nyiso-56 keeper's ST_GAS scored "above cap, NOT grounded — **no declared
D-4 window: reliability_floor**" (a provenance gap, not a shape miss — D-1
passes r 0.95-0.96 / cv_ratio 0.69-0.90 every year); and (b) the
`gas_st_netload_drag` this memo rejected on its **windowed [15,22)** premise
became ALL-HOURS (`ramp_window=None`, the ERCOT-46 / PJM-94 keeper mechanism),
making that premise stale and the drag worth re-testing as an all-hours base
whose level flexes with net-load.

**Re-adjudication result: the drag is rejected again, now on measurement.**
`scripts/derive_nyiso_st_gas_netload_drag.py` (new, PJM-construction-faithful:
EIA-930 NYIS net-load, CAMPD overnight CF, hinge fit) fails its own
pre-registered honesty gates: overnight Spearman rho 0.32/0.39/0.72
(class-wide) and 0.30/0.28/0.57 (NYC+LI-only) — not year-stable; the binned
overnight CF is FLAT vs net-load below ~15 GW (a base, not a hinge) with the
base level drifting up across years at equal net-load (11 GW: 0.087 → 0.140 →
0.136); and the pooled hinge overshoots the 2023 measured class energy
(142 %). The downstate commitment is an **unconditional** local-reliability
base (DARU/SRE + boiler min-run blocks), not net-load-hinged — so this memo's
mechanism choice stands: the persistent-24h `reliability_floor` remains the
class's single grounded mechanism (rule 19), for a measured reason that no
longer depends on the stale window premise.

**Deliverable (same pattern as the CT_PEAKER window fix above):**
`D4_WINDOWS[(reliability_floor, ST_GAS)]` → (0, 24), citing this memo's
measured table (NYC/LI online 100 % of year, overnight CF 0.11-0.20 — no hour
the driver evidence says the class is offline) plus the drag-rejection
derivation; nyiso-56's committed `legitimacy_diagnostics.json` regenerated
(payload path) so the D-4 row exists; status rebuilt. Under rubric v2.2 the
C8 ST_GAS protective caveat escalates to **GROUNDED ABOVE BUDGET — a clean
PASS surfaced as a report note**. Blast radius NYISO-only (PJM's enabled
ST_GAS limbs are drag-owned in its keeper and dropped; every other ISO's are
disabled). Scorer-only: no re-solve, no mechanism change, keeper stays
nyiso-56.
