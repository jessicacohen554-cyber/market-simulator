# FINDING — ercot-219 (OPTION-B PHASE-1, the ercot-218b structural artificial-shortage mechanism, BUILT under B-1 and A/B'd full-span): the three stages are **REJECTED-AS-ARMED on four gates at full magnitude** (G-SPUR 9→273 / 11→671 / 1→1239 against a +5 bar; G-SHED 0/1/0 → 218/77/221 h; G-BAT-2024 ratio 0.41; G-OWNER blown out), and the cause is measured, not mysterious: **stage 1 reconciles the model's AVAILABLE capability envelope to a telemetered ONLINE aggregate — a dimensional category error at the aggregate grain**, which is the ERCOT-159/163 realized-commitment failure mode restated. The mechanism's own G-EXH signature is nonetheless **strongly correct and monotone** (exhaustion hours 1,557 → 336 → 63 across 2023→2024→2025), so the diagnosis is specific: stages 2–3 are sound in construction and stage 1's BASIS is wrong. **Keeper UNCHANGED; no promotion taken.**

**Session ercot-219, 2026-08-18, branch `claude/ercot-219-option-b-phase1-5cs9bf`.**
Keeper resolved fresh from `frontend/data/backcast/keepers/ERCOT.json` at
session start AND end: **`2026-08-17-ercot215-arm-decontam`** — UNCHANGED;
determination NOT-YET, fail set {C3a-2023 −40.1 %, C3b-2023 NRMSE 0.736}, C3c
the ledgered CAVEAT ×3 (68/181, 22/53, 1/31). RETENTION HOLD honoured:
`2026-08-16-ercot213-ctl-headbase` and `2026-08-15-ercot204-rule26-delete`
NOT pruned. Pre-registered in
`docs/PRECOMMIT-ercot219-option-b-phase1-2026-08-18.md` (+ Amendment 1),
pushed and blob-verified BEFORE any solve. This lane is **off-queue by the
owner dispatch of ERCOT-219 itself and the signed card** (the ERCOT §5.1
queue holds no live un-adjudicated in-model item — FINDING-ercot218 §0).

## 0. VERDICT

**REJECTED-AS-ARMED**, recorded unrewritten. Under the card-§4 direction-blind
table (reproduced verbatim in precommit §3), **four gates FAIL**:

| gate | control | arm | bar | verdict |
|---|---|---|---|---|
| **G-CAP** | 0 | **0** violations in all 26,280 h | 0 | **PASS** |
| **G-SPUR** | 9 / 11 / 1 | **273 / 671 / 1,239** | ≤ +5/yr vs 9/11/1 | **FAIL** (×53 the bar in 2023) |
| **G-SHED** | 0 / 1 / 0 h | **218 / 77 / 221 h** | no new shed hours | **FAIL** |
| **G-OWNER** | C3a-2024 +7.9 %, C3a-2025 +0.5 % | **+715.3 % / +1,278.4 %** | both retain PASS | **FAIL** |
| **G-BAT** | — | 2024 ratio **0.4075**; 2025 0.8972 | ±25 % | **FAIL** (2024) |
| **G-DOF** | 8 / 6 | **8 / 6** identical | ledger delta = B-1 series only, zero fitted scalars | **PASS** |
| **G-D2** | 15 D-4 rows | **15, byte-identical**; all three stage attribution rows present | no new D-4 rows | **PASS** |
| **G-REPRO** | — | control reproduces the keeper **12/12 sidecars sha256-identical** AND its determination + reasons exactly | must reproduce before the arm is read | **PASS** |
| **G-EXH** | — | 1,557 / 336 / 63 exhaustion hours (§4) | reported, not gated | reported |
| **LOYO** | — | structurally N/A, declared pre-solve | parameter-free rule | N/A |

**Official scorecard:** the arm's determination stays NOT-YET but its fail set
**WIDENS from {price_mean, price_shape} to {fuelmix, price_mean, price_shape,
dispatch_corr}** — the mechanism breaks two criteria the keeper passes (C1
fuelmix and dispatch correlation), on top of blowing out the price level.
Per the precommitted rule the verdict is REJECTED-AS-ARMED; **promotion is a
separate owner decision on this recorded verdict and was NOT taken in
session** (dispatch order).

## 1. WHAT WAS BUILT (and it is all still standing, behind default-off gates)

Three NEW `ScenarioConfig` booleans, default **False**, ERCOT-gated, **zero
fitted scalars** — the card §2 stages exactly as chartered:

1. **`ercot_capability_reconciliation`** — stage 1, the B-1 keystone: a single
   hourly tighten-only scalar on merchant-thermal availability, applied in
   `data/fleet/arrays.py::_apply_outage_overlays` after the DAM rescale and
   event caps and before min-gen composition.
2. **`ercot_exhaustion_expectation`** — stage 2:
   `P_exhaust(t) = max over [t..end-of-day] LOLP(H(h))`, `H` = post-stage-1
   capability − load − the armed `*_withheld` AS families' own LP requirement
   rows, `LOLP` the registered `ordc_lolp_*` curve through
   `results/scarcity.resolve_lolp_params` + `lolp` (an EXPECTATION input;
   ercot-206 B0 untouched — no price channel changed). Window helper
   `scarcity.within_day_forward_max` (vectorized, rule 2).
3. **`ercot_storage_reservation_offer`** — stage 3, **P1-only** through a new
   `pipeline/solve.py::run_energy_solve(p1_storage_discharge_cost=…)` seam:
   `offer[s,t] = max(vom_base[s], P_exhaust(t) × ordc_voll)`, raise-only.
   The thermal `mc_bid_adjust` seam **cannot** carry this (measured at build
   time: that `(n_gen, T)` array reaches only the thermal P-block columns,
   `lp/costs.py:97`, while storage discharge carries its own objective
   input) — so the card's named seam was implemented as its **storage
   analogue at the same P0→P1 boundary**, with `build_cost_vector`'s
   `storage_discharge_cost` widened to accept `(n_storage, T)`. **P0 is
   untouched by construction and by seam proof.**

Audit trail written per solve-year: `hourly/exhaustion_<year>.parquet`
(`h_margin_mw`, `as_sequestered_mw`, `lolp`, `p_exhaust`).

**Amendment 1 (pre-solve, appended to the precommit before any A/B member
ran)** — the SP-1b liveness falsifier caught a real input defect: the stage-1
scalar clipped to **s = 0** in exactly two hours, 2023 h2461 (T_tel −1.7 GW)
and 2024 h7345 — both single-hour **wind/solar-HSL telemetry spikes** (2023
h2461 wind HSL 15.2 → **32.0** → 25.0 GW; 2024 h7345 33.2 → **43.3** → 22.0
GW, above installed wind). Unguarded they would manufacture a load-shed out
of a data artifact. The degenerate branch `T_tel ≤ N` is now
reconciliation-inert like a NaN hour — zero scalars, the mechanism's own
degenerate point.

## 2. SEAM PROOFS — ALL ASSERTIONS PASS (`results/calibration/ercot219_seamproof.json`)

| proof | result |
|---|---|
| **SP-1** gate-off byte-identity ×3 years vs the PRE-EDIT tree (a worktree at the precommit commit dumped the baseline) | **True** — availability / pmax / min_gen / storage-vom fingerprints identical for 2023, 2024, 2025 |
| **SP-1b** stage-1 liveness + tighten-only | live in every year (14.2 M / 15.7 M / 14.5 M row-hours tightened) and **max delta ≤ 0 in all three** — never loosens, never resurrects an outaged unit |
| **SP-2** cross-ISO byte-identity with all three booleans **ARMED** | **byte-identical in all five non-ERCOT ISOs** (CAISO `caiso200_h1_memberpanel`, PJM `pjm158_novirt_B`, NYISO `nyiso140_control`, NEISO `neiso99_basis_A`, MISO `miso160_wefor_A`) — rule 25 proven at the assembly grain, not asserted |
| **SP-3** no-price-input audit | the stage-1 loader's parquet reads are **column-scoped in source** to `rtolhsl` and `wind_hsl_mw`/`solar_hsl_mw`; READ and REFUSED sets written into the proof (`system_lambda`, `rtorpa`, `rtoffpa`, `rtordpa`, `prc`, `rtolcap`, `rtoffcap`, every LMP/RTSPP/DA series, every model price output — refused) |
| **SP-4** cache-key discipline | pinned default key **`603c2498bf71d21d` UNMOVED**; armed ERCOT backcast key `7bf65b6e5aa95144` distinct |

**G-REPRO in its strongest form:** the control replay reproduces the ercot-215
keeper **12/12 hourly sidecars sha256-IDENTICAL** and its official
determination + reasons exactly (`NOT-YET`, `price_mean, price_shape`), so
the A/B delta is the mechanism alone and nothing else.

## 3. WHY IT FAILS — the measured root cause, and it is a DIMENSIONAL error, not a licensing one

**`RTOLHSL` is an ONLINE quantity; the model's `pmax × availability` is an
AVAILABLE envelope. The reconciliation forces the second onto the first.**

Measured on 2023, all from committed artifacts:

| object | mean MW |
|---|---:|
| model merchant-thermal **AVAILABLE** envelope (what stage 1 rescaled) | **≈ 68,000** (seam log; 1,880 rows) |
| `T_tel` = `rtolhsl − wind_hsl − solar_hsl − storage_capability` (telemetered **ONLINE** all-thermal) | **37,345** |
| SCED-corpus **ONLINE** all-thermal HSL truth (ERCOT-155 taxonomy) | 41,284 |
| model merchant-thermal **DISPATCH** in the CONTROL (its own online level) | **26,429** (p95 **48,244**) |

The model's *online* level already sits in the telemetered *online* regime.
Stage 1 instead pushed the model's *available* envelope down to it — scalar
mean **0.63–0.74**, i.e. ~30 % of merchant thermal capability removed in
**every** hour, including the 8,039 telemetered hours of 2023 where all were
tightened. The LP consequently loses the headroom it must have to commit at
peak (control p95 dispatch 48.2 GW against a reconciled envelope near 32 GW +
nuclear/hydro), so it **sheds load in 218 hours of 2023** and prices those
hours at VOLL — which is the entire G-SPUR/G-SHED/G-OWNER blow-out.

**This is ERCOT-159/163 restated, and the record predicted its shape:** "the
per-hour telemetered capability cap (aggregate or per-unit) pins the backcast
to realized commitment — rule-13 forbidden" (RESEARCH-ercot218b §5). B-1
scoped an exception to that *licensing* objection at the aggregate grain, and
the exception is honoured here in full — but the objection has a second,
**dimensional** half that no signature can waive: an ONLINE aggregate and an
AVAILABLE envelope are different physical objects, and equating them does not
tighten a fat envelope, it **deletes the commitment freedom the LP needs**.
ERCOT-159's own verdict — *"the defect is PRECISION, not physics"* — is
reproduced here at the aggregate grain a third time.

**The Phase-0 closure measurement was correct and was read one step too far.**
`ercot219_basis_phase0.json` measured `T_tel` against the SCED **online**
truth at corr 0.9957 with a stable −4.05 GW offset, and the precommit §1.1
read that as validating the basis. It validated `T_tel` **as an online
object** — which is exactly what it is. The error is the application, not the
measurement, and the precommit's own pinned arithmetic is what made it
falsifiable in one A/B. Recorded so no successor repeats it.

## 4. G-EXH — the mechanism's own signature, and it is RIGHT (reported, not gated)

The card asked for the exhaustion-hour calendar as the mechanism's own
2023-vs-2024/25 contrast. From the arm's committed
`hourly/exhaustion_<year>.parquet`:

| | 2023 | 2024 | 2025 |
|---|---:|---:|---:|
| exhaustion-regime hours (`LOLP(H) ≥ 0.5`) | **1,557** | **336** | **63** |
| hours with `P_exhaust × VOLL ≥ $1,000` | 5,780 | 4,270 | 2,270 |
| `H` margin p5 (MW) | **1,750** | 3,991 | 6,180 |
| storage offer raised above base (h of 8,760) | 7,231 | 6,931 | 5,239 |

**Monotone by a factor of 25 across the span, in the predicted direction, from
carried inputs alone** — no regime parameter, no year keying (the ercot-217
lane stays closed). 2023's exhaustion population is 4.6× 2024's and 25× 2025's;
`H` p5 rises 1.75 → 3.99 → 6.18 GW as the ECRS release reform (Aug 2024) and
RTC+B (Dec 2025) retire the sequestration and the fleet grows. **The
expectation layer reproduces the real mechanism's own decay curve.** Its
monthly calendar concentrates 2023 in Jun–Sep (184/207/240/180 h) — the
artificial-shortage summer — exactly where the IMM located it.

That is the honest split this session establishes: **stages 2–3 behave as
chartered; stage 1's basis is the defect.** The failure is not that the
architecture cannot express the phenomenon — it is that the only aggregate
capability series the record can license is the wrong dimensional object.

## 5. SIDE-EFFECT REPORTING AT FULL MAGNITUDE (Q-B FINAL / R-A — never a basis, never a gate)

The card-§4 table contains no 2023 price criterion by design; every number
here is side-effect reporting, was never targeted, and no decision rule
consulted it. Probe basis (demand-weighted P1 settled price vs actual RT):

| year | C3a control → arm | C3b NRMSE control → arm | model tail > $200 control → arm (actual) |
|---|---|---|---|
| 2023 | −30.4 % → **+1,092.3 %** | 3.45 → 25.16 | 67 → **2,370** (181) |
| 2024 | +7.9 % → **+715.3 %** | 2.34 → 24.63 | 22 → **1,243** (53) |
| 2025 | +0.5 % → **+1,278.4 %** | 0.94 → 35.65 | 1 → **2,076** (31) |

The arm over-prices by an order of magnitude in every year. Reported at full
magnitude; nothing is minimised and no improvement is claimed anywhere.

## 6. WHAT THIS DOES AND DOES NOT CLOSE

**Closed by measurement:** the **aggregate** capability-reconciliation route
of card §2 stage 1, on the only series the record can license (`rtolhsl`) —
it is an online-commitment envelope, so reconciling the model's available
capability to it is dimensionally wrong and it fails four gates. Do **not**
re-run it on `rtolcap` either: that column is thinner still (a ramp-limited
reserve headroom) and is already the armed reserve-supply-cap input (rule 19).

**NOT closed, and explicitly left standing:**
* **Stages 2–3.** Built, wired, seam-proven, and measured to behave as
  chartered (§4). They are inert without stage 1 by their own gating and stay
  default-off. A successor that supplies a *dimensionally correct* capability
  object inherits them at zero build cost.
* **The B-1 signature itself.** It was executed exactly as written; what the
  A/B refutes is the aggregate basis, not the owner's authorization. Whether
  B-1 should be re-scoped (or spent differently) is the owner's call, on this
  record.
* **Door D (2026 SOM RTC+B-era anchors, ~mid-2027)** remains the floor for
  the 2023 price object (ercot-218 §5), untouched by this session.

**The successor this finding names, if the owner wants one:** the object stage
1 actually needs is the model's **committed/online** capability compared to
`T_tel` — i.e. a *commitment*-side reconciliation, not an *availability*-side
one. That is the ercot-163-refuted commitment-state route at aggregate grain,
so it is **not** proposed here and no arm is named; it would need its own card
and its own licence. Recorded as the diagnosis, not as a charter.

## 7. GOVERNANCE

Owner dispatch executed as the lane's charter; B-1 appended verbatim at the
foot of `docs/DECISION-CARD-ercot218b-artificial-shortage-structural-2026-08-18.md`
(commit `ecbad28`) before any build step, per the card's closing clause and
the X-1/X-2 precedent. Precommit pushed and blob-verified (`fe1596ed`, 437
lines) BEFORE any solve; Amendment 1 appended pre-solve. **Rule 15:** both
A/B members registered on the backcast registry with payloads
(`2026-08-18-ercot219-ctl-headbase`, `2026-08-18-ercot219-arm-optionb`),
bundle slim files + sidecars + payloads + bench committed and pushed the same
session; ERCOT roster 5 → 7 runs, under top-15, no eviction, RETENTION HOLD
honoured. **Rule 16:** all three available years in one bundle per member.
**Rule 22:** {2023, 2024, 2025} only — no out-of-training year solved, scored
or registered; no marker sought (ERCOT holds neither `complete` nor `final`,
so no `calibration-complete.json` re-key applies). **Rule 25:** ERCOT only —
SP-2 proves the armed cross-ISO no-op in all five other ISOs. **Rules
5/23/24:** three registered `ScenarioConfig` fields recorded in `meta.json`
and `run_config.json.scenario_config`, cache-key + tier + backcast-only +
forecast-parity registrations landed in the same commit as the fields; no
env-var knob, no off-registry channel, nothing derived from a residual.
**Rule 27:** every file edited locally, exact on-disk bytes pushed, ≥300-line
files blob-verified. **Rule 28:** (b) the cell verdict is minted in
`docs/codebase-site/data/mechanism-matrix/ERCOT.js` this session (**O → R**,
with evidence); (c) the new mechanism family row
`ercot_artificial_shortage_pricing` landed in
`docs/codebase-site/data/mechanism-matrix.js` **plus a cell line in every ISO
shard** in the build commit; `check_mechanism_matrix.py` exit 0. **DO-NOT-REDO
honoured in full:** Door A conduct fitting not re-run (nothing is fitted to
any residual); `ercot_storage_rt_offer_surface` (R) not re-opened (the stage-3
offer is computed from the model's own state, no measured surface is fed);
item 11 per-unit crosswalk (Q-B FINAL) untouched — B-1 was the aggregate route
precisely because the per-unit one is closed; the mid-band spill lane (CLOSED,
ercot-215) and the regime lane (CLOSED, ercot-217) not re-opened — no regime
parameter exists in any stage; ercot-206 B0 held (the `ordc_lolp_*` constants
enter as an expectation input, explicitly distinguished in precommit §1.2, and
no price channel changed). **Q-B FINAL / R-A honoured:** every 2023 price
number above is side-effect reporting at full magnitude, never a basis, never
a gate. C6 attestations authored for both members; the arm's is marked
`capability_reconciled: true` and names the B-1 signature, per B-1's own
condition. No new workflows, no cron, no CI job, no PR (push-and-stop on the
designated branch).

**Session consumed the ercot-219 shorthand. Next shorthand: ercot-220**
(ercot-199 remains unclaimed).
