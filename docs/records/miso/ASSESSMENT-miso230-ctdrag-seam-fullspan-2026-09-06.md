# ASSESSMENT miso-230 — the CT_PEAKER root cause is FIXED and the seam pair is PROMOTED. **DETERMINATION CALIBRATED**, C3c the single ledgered caveat.

**KEEPER → `2026-09-06-miso-230-ctdrag-seam`** (bundle `miso230_ctdrag_seam_K`), promoted from
`2026-09-05-miso-220-nonsteam-lift`. Rule 22: 2023–2025. DOF ledger **unchanged at 41/2**.

Executes the owner's standing decision of 2026-09-06 — *"fix CT_PEAKER, then promote the seam
pair"* — and the same day's restated bar. **The regression clause was not needed: no gate
regressed.**

---

## 1. The determination

| criterion | tier | verdict |
|---|---|---|
| C1 fuel mix | LOAD | **PASS — 16/16 all-class, 12/12 free-class** |
| C2 system volume | LOAD | PASS |
| C3a mean LMP | LOAD | PASS |
| C3b price duration/shape | LOAD | PASS |
| C3c price tail / scarcity | SUPP | **CAVEAT (ledgered, non-downgrading — rubric v3.3)** |
| C4 dispatch correlation | SUPP | PASS |
| C6 governance | PROT | PASS |
| C8 forced-energy share | PROT | **PASS — grounded above budget, all three years** |

## 2. What it fixes, and why the cell was never the seam's fault

miso-227 solved the seam full-span and scored **NOT-YET on one load-bearing cell**:
CT_PEAKER-2023 at −8.29 TWh against ±8.00. The predecessor missed that class by **5.4–8.0 TWh in
every year** and sat **0.015 TWh** inside the band — MISO's CALIBRATED status hinged on 0.19 % of a
band on a cell wrong by eight — and the seam added 0.30 TWh to a 7.99 TWh pre-existing miss.

| C1 cell | keeper gap | pair gap | move |
|---|---:|---:|---:|
| **CT_PEAKER 2023** | **−7.98** | **−4.32** | **+3.66** |
| **CT_PEAKER 2024** | **−6.11** | **−3.31** | **+2.80** |
| CC_REGULAR 2023 | −4.17 | −6.05 | −1.87 |
| CC_REGULAR 2024 | +6.10 | +5.39 | −0.71 |
| ST_GAS 2023 | +0.54 | −0.62 | −1.16 |
| ST_GAS 2024 | −5.04 | −5.64 | −0.60 |

Zero PASS→FAIL flips. 2025 C1 is SKIPPED on the preliminary EIA-923 vintage, as for the predecessor.

## 3. The two deltas

**(1) `ct_netload_drag=true`** on MISO's own derived curve and window:
`clip(0.01303·netGW − 0.8108, 0, 0.4394)` over **`[10, 21)` CST**.

**(2) `miso_seam_neighbour_anchored_ladder=true`** — the miso-227 arm, byte-unchanged.

They are not two mechanisms for one phenomenon (rule 19): the drag is CT_PEAKER *commitment*, the
seam is import *band pricing*. They are paired because the owner's decision names the pair.

## 4. Rule 25 `[R-ISO-SCOPE]` on both axes — why this is MISO's mechanism, not a transfer

PJM's **estimator** is carried (pure-play plant selection, CF denominator, 2-GW binning,
exact-grid-search hinge; no `scipy.optimize`). **None of its numbers, and not ERCOT's `[15, 22)`
window**, which is justified by a solar-collapse evening ramp MISO does not have — miso-229
measured MISO's midday block as strongly driven as its evening (ρ 0.743/0.691/0.734 vs
0.706/0.636/0.743).

**The window was DERIVED with zero free parameters**: the maximal contiguous run of local-standard
hours whose pooled mean CF is at or above **the fleet's own 24-hour mean CF (0.0850)** — the data's
own daily average, not a chosen level — with positive ρ(CF, net load). Result **`[10, 21)`**;
re-derived independently per year by the identical rule it reads `[9,21)` / `[10,21)` / `[11,22)`,
**stable to ±1 h**.

Frozen derive `scripts/data/derive_miso_ct_netload_drag.py` → `data/raw/reference/miso_ct_netload_drag.json`
(ISO-stamped, rule 23 `[R-FROZEN-DERIVE]`). **DOF ledger unchanged at 41/2** — every coefficient is
a statistic of measured CAMPD + EIA-930 data under a pre-specified estimator, none identified
against a residual.

**It is NOT the actuals pin.** `ct_mustrun_per_plant` floors each plant at its *observed EIA-923 net
generation* (rule 13's named forbidden case, D-9 QUARANTINED, machine-asserted `False`). It was
refused at miso-228/229 and is not revived. The drag's floor sits at **~half** the measured class
energy (8.406/7.311/7.469 vs 15.037/13.791/14.804 TWh) — the property that separates a minimum from
a pin.

## 5. Rule 19 `[R-ONE-MECH]` — replace, not stack, measured BEFORE the solve

MISO's `reliability_floor` already carried net-load-driven CT_PEAKER limbs in all six zones, and
the predecessor's D-2 attributed **100 %** of CT forcing to them.
`drop_drag_owned_reliability_specs` removes exactly those limbs. The zero-LP phase 0 measured it:

```
MISO 2023: reliability floor — dropped 18 drag-owned limb(s) (rule 19)
  keeper reliability_floor × CT_PEAKER : 2.6231 TWh -> ARM 0.0000 TWh
  ARM    ct_netload_drag               : 8.8578 TWh, zero outside [10, 21)
```

The keeper's own D-2 confirms `ct_netload_drag` is the **sole** CT_PEAKER forcing mechanism in all
three years.

## 6. Rule 29 `[R-SCREEN]` — the sequencing, and no control solve

1. **Zero-LP phase 0** measured the replacement and predicted a **+3.6544 TWh** lift.
2. **Screened alone on 2023** — one LP, the year named on the mechanism's own **footprint** (largest
   floor energy, 8.406 TWh) before the solve, never on a residual. **All five pre-registered
   STOP-only gates PASS**; realized lift **+3.948 TWh = 1.08× the prediction**.
3. **Full span** only then, one invocation, one bundle (rule 16).

**Control = the predecessor's committed bundle** (rule 29(b) form 4). G-DRIFT `4545300d..HEAD`
classified **every** backcast-path hunk INERT (PRECOMMIT §5), extended over main's later 52 commits
which are forecast-path or a no-op cache-key fingerprint. **No control solve was spent.** The screen
bundle was **deleted before merge** (rule 29(c)); `PRECOMMIT-miso230-ct-netload-drag-2026-09-06.md`
and `_miso230_screen_gates.json` carry every number.

## 7. A scoring-path change, declared

`D4_WINDOWS` declared `ct_netload_drag` at ERCOT's `(15, 22)` **globally**. Scoring MISO's derived
`[10, 21)` against it would have counted h10–h14 — carrying 1,744–2,359 MW, the largest part of the
footprint — as **off-window binding**, i.e. failed the drag for binding in exactly the hours MISO's
own driver evidence says it should.

`D4_WINDOWS_BY_ISO` + `resolve_d4_windows` now declare MISO `[10, 21)` with the measured evidence
cited in place. **Pushed before the solve**, so it could not be re-chosen after seeing a gate.
No-op for every other ISO (ERCOT still reads `(15,22)`) and for every registered run; 117 tests
pass. Like every windowed row it is a rule-12/17 **declaration**, not an escalation path — the drag
is zero outside its configured window by construction.

## 8. REPORTED AGAINST THIS KEEPER, at full magnitude

- **(a) D-1 diurnal shape REGRESSES ON COAL.** The predecessor carried **one** D-1 FAIL (COAL_PRB
  2025, cv_ratio 0.388); this keeper carries **four** — COAL_PRB 0.488 / 0.492 / 0.389 across
  2023–2025 and COAL_BIT-2024 at 0.387 — from coal displaced by the CT floor. They do **not** gate
  (rule 18's shape leg binds only above the forced cap, COAL sits at ~0.3 % forced against a 30 %
  cap, and standalone C7 was retired at rubric v3.1), but **three are new** and two sit within
  0.012 of the line. This is the clearest cost of the arm.
- **(b) CT_PEAKER forced share rises steeply**: 26.5 / 18.3 / 15.3 % → **49.2 / 31.2 / 34.0 %**, so
  C8 passes **only** through rule 18's grounded conditional route. That route is earned and
  measured — D-4 off-window **0.0000** in all three years against MISO's own declared window, and
  the class's own D-1 **improves** (profile_r 0.935/0.962/0.982 → 0.975/0.984/0.983; cv_ratio
  1.335/1.119/1.395 → 1.792/1.566/1.738) — but this arm makes the fleet's largest forced share
  substantially larger.
- **(c) C3a-2025 moves AWAY** from actual (−7.0 % → −8.4 %, inside ±10 %) while 2023/2024 move
  toward it (+7.2 → +5.0, +3.4 → +2.0 %).
- **(d) CC_REGULAR-2023 moves 1.87 TWh further out** (−4.17 → −6.05) — the energy-balance
  counterpart of the CT lift, inside band.
- **(e) C3c is UNCHANGED, not improved** — tail hours **3 / 7 / 0 in both bundles, byte-identical**.
  The ledgered caveat is carried forward untouched and this run makes **no** scarcity-pricing claim.
- **(f) 2024 slack 0.0196 TWh is PRE-EXISTING** in the predecessor, not introduced, though spread
  over 9 zone-hours rather than 7.
- **(g) The seam's pre-committed NON-CLAIM stands unchanged** and is not quietly dropped on
  promotion: it repairs the ladder's **level**, not its **responsiveness** — corr(imports, own
  price) +0.750 → +0.725 against a measured −0.101, 3 % of the distance. The named successor is an
  **hourly** neighbour anchor reading the hourly PJM western-border DA the incumbent derive already
  loads; unbuilt, and the only construction on the board that can move the correlation.

## 9. Governance

Rule 13: both trigger and magnitude regenerate for a forward year and respond to changed
conditions. Rule 15: registered on the dashboard, non-keeper MISO runs pruned to keeper-only
(miso-227 pruned; its FINDING/ASSESSMENT docs retained, git history is the record). Rule 16: all
three years, one invocation, one bundle. Rule 17: driver, window and forward story stated. Rule 21:
no free parameter added. Rule 22: 2023–2025 only; **MISO holds no `complete` marker**, so D-5(b)
re-keying is not owed. Rule 27: edited locally, pushed as on-disk bytes, blobs verified. Rule 28(b):
`netload_drag_floors` **U → K** and `seam_neighbour_anchored_ladder` **O → K** in MISO's shard, same
session; `ct_drag_ramp_start/_end` additionally registered **literally** in the base row because the
window is now per-ISO derived rather than a shared constant (CI's shared ratchet caught this and it
is fixed, not baselined).

**Reported against the charter**: its instruction to mint a `ct_netload_drag` base row rested on a
false premise — the field was already registered in the `netload_drag_floors` row. Duty 28(c) did
not fire (no new `ScenarioConfig` field); duty 28(b) is discharged on the existing cells. The field
with no row in any shard is `ct_mustrun_per_plant`, which this lane refuses on rule-13 grounds.
