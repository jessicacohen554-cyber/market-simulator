# PREREG — ercot-150: resolve the gas-offer margin anchor PER ZONE at ERCOT (`--gas-offer-margin-zonal-anchor`)

**Written and pushed BEFORE either arm solves.** Everything below — the
admissibility analysis that shaped the lever, the applier-convention finding,
the construction gates, the REPORTED/KILL split, the declared expected effect
STRUCTURE, and the rule-1 scrutiny clause — is fixed in advance.

**Session:** ercot-150. **Scope item:** the cross-ISO transfer nyiso-109 §7
chartered (*"ERCOT, PJM and MISO also arm a zonal gas basis on their keepers,
so the same grain mismatch exists in their lanes; their matrix cells enter as
`U` — each needs its own derived table and its own A/B in its own lane
(rule 25)"*), taken up at ERCOT under this session's handoff. This is
**off the §5.1 queue and deliberately so**: the queue's top is closure work on
the availability lane and the un-chartered audit items, and this lever is not
addressed to any of them — it is a **structural-integrity correction to a
mechanism already armed on the keeper**, chartered by the nyiso-109
measurement and shaped by the pjm-144 convention lesson. PJM's `I` transfers
NOTHING (rule 25): it is a topology result (price-coupled zones absorb a
mean-zero redistribution), and ERCOT's West **decouples** under binding GTCs —
whether ERCOT prices what PJM absorbed is exactly the open question this A/B
measures. **Keeper under test:** `2026-08-01-ercot149-gas-event-cap` (bundle
`results/calibration/ercot149_gas_event_cap_arm`, owner-promoted 2026-08-01;
**NOT-YET**, C1 16/16 all-class / 12/12 free-class, 4 criterion-grain FAILs:
C3a price_mean [2023-only, −33.3 %], C3b price_shape [2023-only, 0.616], C3c
price_tail [all years], C7 shape [2023 COAL_LIGNITE cv-leg]).
**Frozen HEAD:** `f58339b` + this session's mechanism-registration commits.

---

## §1 — The no-LP admissibility check, and how it SHAPED the experiment

### 1.1 The grain error, restated at ERCOT

`apply_gas_offer_margin` adds `markup_hr × (anchor − fuel)` and states its own
identity: *at `fuel == anchor` the reformed offer reduces EXACTLY to the
registered band multiplier.* That is a statement about **a unit's own delivered
fuel**. `GAS_OFFER_MARGIN_ANCHOR_BY_ISO["ERCOT"] = 2.2494` is derived from
`data.fuel.trajectories._gas_series` on the registered ERCOT recipe (annual
Henry Hub + the flat `GAS_BASIS_DIFFERENTIAL["ERCOT"] = −0.50` scalar +
seasonality: year means 2.0394 / 1.6895 / 3.0192). The ercot149 keeper arms
`ercot_zonal_gas_basis=True` (via the `coal_prb_sigmoid_overrides` channel —
§1.2), which afterwards shifts every gas unit's `(n_gen, T)` fuel by its
zone's measured basis AND a flat measured level correction. So marked-up gas
tranches price their markup at a fuel level they do not pay — the identical
defect class nyiso-109 measured and closed on NYISO, present here in ERCOT's
own geometry.

### 1.2 The applier-convention finding that makes ERCOT's defect GEOMETRY different — measured, not assumed

The handoff named three facts that had to be established before writing this
prereg. All three are now measured on the keeper bundle's own record:

**(a) Which of the two zonal-gas forms the keeper arms.** The machinery exists
as a ScenarioConfig field (`ercot_zonal_gas_basis`) resolvable from the env
probe `ERCOT_ZONAL_GAS` inside `backcast_config` — the form
`replay_keeper._ENV_GATED_INERT` hard-errors on — AND as a generic
`prb_overrides` ScenarioConfig override. The ercot149 bundle's `meta.json`
records the env-gated top-level keys at their INERT values
(`ercot_zonal_gas_basis: false`, `ercot_west_netload_gas_shape: false`,
`ercot_west_gas_delivered_floor: null`) and carries the ACTUAL arming inside
`coal_prb_sigmoid_overrides` (`ercot_zonal_gas_basis: true`,
`ercot_west_netload_gas_shape: true`, `ercot_west_gas_delivered_floor: 0.4`),
which `replay_keeper.build_kwargs` maps onto the `prb_overrides` kwarg. **A
kwargs replay reproduces the keeper's arming with no env var and no hard
error**, and `--set` deltas ride the same channel. NOT armed anywhere:
`ercot_gas_contract_haircut`, `ercot_gas_delivered_floor_basis`,
`ercot_offer_hrmult_ep_rebasis` (so the marked-up-tranche census has **zero
band-scoped `margin_anchor_*` anchors** — under the lever, every marked-up gas
tranche resolves its zone anchor).

**(b) Which applier fires — and where the fuel path actually ENDS.**
`ZONAL_BASIS_APPLIERS["ERCOT"] = apply_ercot_zonal_gas_basis`
(`data/fuel/basis/ercot.py` — ERCOT's own module, not the shared `meanzero.py`
core, but the same capacity-weighted mean-zero family): each gas unit is
shifted by

    gen_offset = level_corr + (basis_zone − capw_mean(basis over gas rows))

where `level_corr = ercot_electric_power_gas_basis(year) − (−0.50)` — the
measured TX delivered-to-electric-power basis (EIA N3045TX3) replacing the
flat scalar (+0.5045 / +0.4142 / +0.0366 in 2023/24/25) — and the result is
floored at `_GAS_PRICE_FLOOR` per hour. **ERCOT's convention is therefore
NEITHER NYISO's (pure one-sided) NOR PJM's (pure mean-zero): it is a
TWO-SIDED capacity-weighted mean-zero spread ON TOP OF a ONE-SIDED measured
level correction.** The `_gas_series` the ISO anchor is derived from adds the
SAME EP level term when the flag is on (the coal-sigmoid reference path,
`trajectories.py` — its comment says the per-zone spread is deliberately left
out), but the REGISTERED anchor 2.2494 was derived on the registered recipe
with the flag off, so the anchor carries the −0.50 scalar level and none of
the EP correction: the keeper's fleet-centroid delivered gas sits ABOVE the
anchor by `level_corr` in every year, and zones spread two-sidedly around
that centroid.

**Measured mid-course correction, recorded rather than absorbed:** the first
derivation construction (the pjm-144 template applied literally — synthetic
ISO-anchor series + the zonal-basis applier alone) was OVERTURNED BY ITS OWN
FIRST RUN before anything was pushed. The keeper's fuel path does not end at
the zonal basis: `ercot_west_netload_gas_shape` (keeper-armed) replaces the
West/Panhandle series with a measured two-regime step whose burner-tip
delivered floor (0.4 $/MMBtu) lifts the realised West annual mean far above
the post-basis level — measured on the ercot149 reconstruction's own fuel
path: post-basis **1.62 / 0.21 / 0.65** → realised **1.99 / 1.15 / 2.74**
$/MMBtu (2023/24/25; the collapse is confined to the measured 3 / 42 / 11 %
of hours and the rest of the year prices at firm Waha). A West anchor at the
pre-shape level (window 0.79, −1.46 vs the ISO anchor) would price West
markups at a fuel level West units never pay — the same grain-error class
this lever exists to fix, reintroduced at one zone by ignoring a later
fuel-path stage. The zone anchors are therefore identified on **the
reconstruction's own resolved `fuel_prices`** — the exact `(n_gen, T)` array
`apply_gas_offer_margin` prices against
(`derive_gas_offer_margin_anchor.SOLVE_FUEL_ARRAY_ISOS`), byte-faithful to
every fuel-path stage — with a within-zone spread guard (median-row anchor,
hard-fail past 0.25 $/MMBtu) so a per-unit transform can never silently break
the zone grain. Under this definition the West correction is **−0.29**, not
−1.46: the netload shape already restores most of the West level, and the
pre-shape figure would have overstated the West leg ~5×. NYISO/PJM keep the
synthetic construction — their zonal basis IS the end of their unit-fuel
modification, so the two constructions coincide there.

**(c) What the lever does NOT touch.** `apply_cc_committed_offer_margin`
(ERCOT-139, armed on the keeper) prices the CC_REGULAR `_committed*` block at
`level − HR × anchor` reading the CONFIG-level `gas_offer_margin_anchor`
ONLY — its measured level (10.354 $/MWh) was identified ERCOT-wide at the
ISO anchor by its own derive, and the zonal lever leaves it byte-identical
(asserted by K1). The zonal anchor applies exactly where the mechanism's
as-built wiring puts it (`data/fleet/assembly.py`): the `markup_hr > 0`
tranches of `apply_gas_offer_margin`, band-scoped rebasis anchors keeping
precedence (none exist on this keeper).

Consequences for the experiment, each pre-registered here:

* **No K6 direction gate** — the handoff's condition ("NO one-sided K6 unless
  the applier convention is one-sided") resolves to DROP: the spread is
  two-sided and the level is one-sided; neither admits nyiso-109's gate. The
  per-zone direction table is REPORTED against the offer-side prediction
  `sign(anchor_z − 2.2494)`.
* **K3 liveness prices on the ZONAL grain** (the pjm-144 leg): the mean-zero
  spread can be live at ~zero net system effect, and ERCOT's West decouples
  under binding GTCs, so the zone grain is where a real price effect must
  show. West/Panhandle deltas are additionally broken out in the report — the
  decoupling question is the scientific point of this A/B. The system
  load-weighted delta is REPORTED with no threshold.
* **The derivation must carry the solve's own fleet weights** (`--weights-bundle`
  REQUIRED): the mean removed is capacity-weighted over the fleet's gas rows
  (`weights = fleet.pmax[gas_rows]`), so ERCOT joins
  `CAPWEIGHTED_ZONAL_ISOS`. pjm-144 measured the unweighted error at up to
  0.106 $/MMBtu — larger than the 0.1 inertness bar.
* **The anchors are read from the reconstruction's own resolved
  `fuel_prices`** (`SOLVE_FUEL_ARRAY_ISOS`, the (b) correction): this both
  sidesteps the `_gas_series` EP double-count (the synthetic series with the
  flag armed would carry the level term twice) and captures the West
  net-load shape the keeper's fuel path applies after the zonal basis. Hard
  checks: the keeper must arm `ercot_zonal_gas_basis` AND
  `ercot_west_netload_gas_shape` (`ZONAL_KEEPER_REQUIRED_FLAGS` — a bundle
  without either would identify a different level), the bundle's per-year gas
  price must equal the training-window value the ISO anchor is identified on,
  and the within-zone spread guard (median-row anchor, hard-fail past
  0.25 $/MMBtu) rejects any per-unit transform — e.g. a future armed contract
  haircut — rather than silently averaging over it.

### 1.3 The derived table (the admissibility numbers)

`PYTHONPATH=.:src .venv/bin/python scripts/data/derive_gas_offer_margin_anchor.py
--iso ERCOT --by-zone --weights-bundle results/calibration/ercot149_gas_event_cap_arm`
reads each zone's gas rows from the reconstruction's own resolved
`fuel_prices` over the same 2023–2025 window, so the values are by
construction the levels the solve prices those zones' gas units at (every
fuel-path stage included — §1.2(b)). Raw measured basis (2023/24/25 vs HH,
`data/raw/ercot_zonal_gas_hub.csv`): West/Panhandle −0.72 / −2.19 / −2.38
(Waha), North/Northeast +0.13 / +0.21 / +0.43 (North/East-TX complex),
Houston −0.15 flat (HSC), South_Central +0.56 / +0.45 / −0.12, South
+1.23 / +0.63 / +0.59 (South-TX hubs) — a **2.580 $/MMBtu** window-mean
cross-zonal spread, the largest of the six ISOs. Measured EP level correction
(`ep_basis − (−0.50)`): **+0.5045 / +0.4142 / +0.0366**; per-year
gas-capacity-weighted means removed: **+0.2024 / +0.0824 / +0.0372** $/MMBtu
(vs unweighted +0.0657 / −0.4329 / −0.5114 — the weighting matters at 3–5×
the inertness bar); 1289 gas rows and **1132 / 1132 / 1135 marked-up
tranches with 0 band-scoped anchors** each year.

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 2.2494 |
|---|---|---|---|---|---|
| South | 3.5721 | 2.6518 | 3.6094 | **3.2778** | +1.0284 |
| South_Central | 2.9021 | 2.4718 | 2.8994 | **2.7578** | +0.5084 |
| North | 2.4721 | 2.2318 | 3.4494 | **2.7178** | +0.4684 |
| Northeast | 2.4721 | 2.2318 | 3.4494 | **2.7178** | +0.4684 |
| Houston | 2.1921 | 1.8718 | 2.8694 | **2.3111** | +0.0617 |
| West | 1.9866 | 1.1497 | 2.7396 | **1.9586** | −0.2908 |
| Panhandle | — | — | — | *(no gas capacity in any training year — omitted; zones absent from the map keep the window anchor)* | — |

Five zones sit above the ISO anchor (the level correction), Houston sits
essentially on it, and West below — the two-sided-spread-on-one-sided-level
geometry §1.2(b) predicted, with the West side moderated by the net-load
shape's floor lift (West per-year values 1.99 / 1.15 / 2.74 are the realised
post-shape means; the pre-shape figures 1.62 / 0.21 / 0.65 appear only in
the derivation record's decomposition). The consistency stat is ERCOT's own,
NOT PJM's mean-zero invariant: capw(zone anchors) vs ISO anchor +
window-mean level correction (2.2494 + 0.321 = 2.570) carries a small
positive residual from the West floor lift weighted by West's ~5 % gas
capacity share plus the `_GAS_PRICE_FLOOR` hourly clip — the per-year
decomposition is committed in
`results/calibration/_ercot150_zonal_anchor_derivation.json`. **Zero fitted
parameters** (+1 derived DOF entry; `n_residual` unchanged).

**Inertness bar (pre-declared in the handoff): if every zone anchor were
within ~0.1 $/MMBtu of 2.2494 the arm would be recorded `I` ex-ante with no
solve spent.** Result: max |anchor − 2.2494| = **1.0284** $/MMBtu (South),
with 5 of 6 populated zones beyond the bar (Houston at +0.0617 is inside it —
its anchor still applies, being the same measurement, but Houston cannot be
what makes the arm live) — the arm is **LIVE on the offer side** and the A/B
proceeds.

### 1.4 What the ISO-level identification misprices today

At the registered curve, `markup_hr × (2.2494 − fuel)` hands every marked-up
tranche in the five above-anchor zones a NEGATIVE average margin shift (their
delivered fuel runs above the anchor by +0.06…+1.03) — offers discounted
below the registered multipliers — and every West marked-up tranche a
POSITIVE one (fuel −0.29 below anchor on the realised, net-load-shaped
series) — offers uplifted above them. The zone anchor restores the
mechanism's identity in all six populated zones **at each zone's realised
annual level**; the within-year two-regime West variation is exactly what
the margin's own hour-by-hour `fuel[t]` tracking prices, which is the
mechanism working as designed, not a residual. Nothing else about the
mechanism moves: same markups, same bands, same ISO anchor recorded in both
arms, and the CC-committed measured level untouched (§1.2c).

---

## §2 — The lever: the mechanism's own identification point, at the right grain

`--set gas_offer_margin_zonal_anchor=true` on the keeper recipe
(`replay_keeper` routes it through BOTH the solve kwarg — which resolves
`constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["ERCOT"]` into
`gas_offer_margin_anchor_by_zone` so the bundle's run_config records the
values, rule 21 — and the `prb_overrides` config channel; the ERCOT-65/84
double-channel lesson is designed in). An ISO without a table hard-fails
(rule 24); the table is ERCOT's own, derived from ERCOT's own basis data and
ERCOT's own keeper fleet, and never transfers (rule 25). A band-scoped
rebasis anchor (`margin_anchor_*`) keeps precedence (rule 19) — the ercot149
curve carries none, so all marked-up gas tranches resolve their zone anchor.
Panhandle is absent from the table (no gas capacity in any training year) and
absent zones keep the window anchor by the as-built wiring — a no-op on an
empty zone.

**Zero fitted parameters** (+1 DOF entry, +0 residual-identified). Rule 23:
the table re-derives only when the gas source data, the per-zone hub table,
the EP series, or the keeper fleet recipe the weights are read from changes —
never because a residual moved. The anchors are what the derive script
printed; they are not swept, in any direction, whatever the gates do (§5 P5).

---

## §3 — Declarations fixed IN ADVANCE

### 3.1 The expected effect STRUCTURE, and the rule-1 posture

**ERCOT is NOT-YET with four standing FAILs, so — unlike pjm-144 — residuals
exist that this lever could move.** The nyiso-109 §3.1 posture therefore
applies with EXTRA force, pre-registered:

* **The declared direction from the applier's arithmetic**: marked-up gas
  offers RISE in the five above-anchor zones (by `markup_hr × (+0.06…+1.03)`)
  and FALL modestly in West (by `markup_hr × 0.29`). The rise side carries
  ~95 % of ERCOT's gas capacity, so the net offer-stack level rises — **the
  direction the failing C3a-2023 (−33.3 %, model under-prices) wants.** That
  alignment is pre-registered as grounds for EXTRA scrutiny, never as
  encouragement: an improvement on C3a (or any criterion) is NOT evidence the
  lever is right, and the lever is defended on the arithmetic of the
  mechanism's stated identity alone — the anchors were derived with zero
  reference to any residual, before either arm solved. (The mid-course
  correction in §1.2(b) CUT the West leg from −1.46 to −0.29 — the honest
  identification made the lever SMALLER, which is the direction a
  residual-hunting construction would never move.)
* A regression on any criterion is likewise not by itself grounds to reject a
  structurally correct identification — the §5 escalation path applies, never
  a silent revert.
* **Declared expected structure** (not a gate; deviations are findings to
  report): the dominant action is now the LEVEL side — most zones' marked-up
  offers rise and their λ with them in the hours those tranches are
  marginal; West/Panhandle λ falls only modestly (the −0.29 leg) and only in
  the hours the West decouples (binding W→E GTC transfers). The SYSTEM
  load-weighted λ delta is expected positive (the level side carries ~95 %
  of gas capacity) but is sign-unconstrained. Whether the decoupled-West
  effect survives to zonal annual means — what PJM's coupled topology
  erased — remains the K3-report interest, now at a smaller stake than the
  handoff anticipated: the measured moderation of the West leg is itself a
  finding. **No magnitude band is declared** — there is no measured basis
  for one.

### 3.2 What is NOT claimed, declared before the solve

* **No C3c claim.** ERCOT's C3c FAILs in all three years (the RT
  scarcity-formation attribution, ercot-144's ledger evidence). A cross-zonal
  offer re-anchoring can move tail counts either way; movement is REPORTED.
  C3c cannot flip to a kill by itself unless it appears as a NEW per-year
  PASS→FAIL flip (P2 row grain) — there is no C3c PASS year to lose.
* **No C7 claim.** The 2023 COAL_LIGNITE cv-leg is attributed OUTSIDE the
  offer surface (ercot-142/143, closed); this gas-side lever is not addressed
  to it. C7's class-year rows are policed by P2's row grain.
* **No amplitude claim.** The xiso-1 diurnal-amplitude defect is systemic and
  its ERCOT cell is `U`; this arm's spread is per-zone and per-year, constant
  across the hours of a day (the West netload shape belongs to the OTHER
  mechanism), so within-day offer σ is untouched by construction. Any
  amplitude movement via re-dispatch is REPORTED, never banked.
* **No trough/spread-lane reopen.** The ercot-138 §J inert band
  (`gas_offer_net_revenue_margin` inert on the CC committed band — markup 0),
  the offer-surface variants (R/inert), and the West/Panhandle topology split
  (CLOSED) are all untouched; this lever changes no multiplier and no
  topology, only the anchor the EXISTING markups are priced at.
* **No forecast-lane result**, no re-litigation of any armed mechanism; both
  arms carry the keeper recipe exactly, ± the single delta.

### 3.3 Holdout

Both arms solve **[2023, 2024, 2025]** and nothing else (rules 16 / 22). The
holdout spend freeze is ACTIVE; ERCOT holds neither `complete` nor `final`,
and no out-of-training year is touched by any solve, score or probe in this
session.

---

## §4 — Construction gates (these, and ONLY these, can invalidate the experiment)

* **K1 flag fidelity.** Arm B's run_config records
  `gas_offer_margin_zonal_anchor == true` **and**
  `gas_offer_margin_anchor_by_zone` equal to
  `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["ERCOT"]` (all six populated
  zones); the control records `false`/absent and `null`. Both record
  `gas_offer_net_revenue_margin == true`, `gas_offer_margin_anchor == 2.2494`,
  **and** the ERCOT-139 pair unchanged (`cc_committed_offer_margin == true`,
  equal `cc_committed_offer_level`) — the shared-anchor mechanism this lever
  must NOT touch (§1.2c).
* **K2 control integrity — TWO BASES, only the first is a gate.** The
  **scorecard** basis (the control reproduces the committed keeper's
  determination and every per-criterion status) is the pre-registered gate.
  The stricter **byte** basis (class-hour for class-hour, < 1e-6 MW) is
  computed and **REPORTED**; a byte miss is same-HEAD drift and is its own
  finding, not a failed gate. Drift is possible: HEAD has moved from the
  keeper's `73e237a` to `f58339b` (~24 src files: FFR-1D/W1X forecast-mode
  config guards — including the `ercot_dam_availability_gas_event_cap`
  backcast-only-overlay guard entry, forecast-gated by construction —
  miso-113's MISO-gated night floor, pjm-144's PJM-keyed tables, FH-1/FH-2
  forecast-vintage mechanisms with a `is_full_forward_hindcast`-gated
  trajectories guard, the Wave-1 cache-epoch bump, and
  runner/pipeline/commitment refactors intended behavior-preserving). Every
  one is ISO-gated, mode-gated, or intended inert for an ERCOT backcast —
  **that expectation is recorded so the control can falsify it.**
* **K3 mechanism is LIVE — zonal price leg** (§1.2). `max |Δ class MW|` on a
  class-hour **> 50 MW** in **every** year, AND
  `max over zones |Δ zonal mean λ|` **> $0.10/MWh** in **every** year. The
  system load-weighted λ delta and the West/Panhandle deltas are REPORTED
  with no threshold. Failing K3 is verdict `I` (inert), not `R`.
* **K4 single delta.** The two arms' recorded scenario blocks differ in
  **exactly** the two zonal-anchor keys and nothing else.
* **K5 year span.** Both bundles `[2023, 2024, 2025]`.
* *(No K6 — dropped per §1.2; the spread is two-sided on a one-sided level,
  and direction is REPORTED.)*

A construction-gate failure invalidates the experiment (fix and re-solve);
it never adjudicates the mechanism.

---

## §5 — What can KILL the arm (pre-registered non-degradation gates)

Scored from `scripts/calibration_verdict.py`'s own outputs on the arm vs the
**control**, never against the committed keeper, by
`scripts/probes/_ercot150_zonal_anchor_ab.py` (no criterion re-derived; the
full per-(criterion, year, key) verdicts are captured to
`results/calibration/_ercot150_verdict_{A,B}.json` for the row-grain leg).

* **P1 — C1 must not regress.** The control's expectation is 16/16 all-class,
  12/12 free-class; the arm must hold **12/12 free** and **16/16 all**.
* **P2 — no NEW FAIL, at BOTH grains.** (1) Criterion grain: the arm's FAIL
  set must be a **subset** of the control's — expected
  {price_mean, price_shape, price_tail, shape}, so any NEW criterion FAIL
  kills. (2) **Row grain** (the ERCOT-specific leg, because C3a/C3b fail in
  2023 ONLY): comparing the captured full verdicts, every
  (criterion, year, key) row that PASSES in the control must not FAIL in the
  arm — a C3a-2024/2025 or C3b-2024/2025 PASS→FAIL flip kills even though
  the criterion status cannot regress further. The named fragile rows:
  price_mean 2024 (+0.8 % of ±10 % at the keeper) and price_mean 2025.
* **P3 — protective gates hold.** C6 `governance` and C8 `forced_share` stay
  PASS. C7 `shape` is a control FAIL (2023 lignite cv-leg) and is excluded
  here — its class-year rows are policed by P2's row grain.
* **P4 — slack and dump stay exactly 0.0** in every year of both arms.
* **P5 — no fitted follow-up.** Whatever the gates do, no parameter moves in
  this session to "finish" the result, and the anchor table is **not**
  re-derived against it (rule 23). The anchors are what the derive script
  printed.

**Promotion rule, pre-committed:**

* Every §4 gate passes AND no §5 kill fires → the arm is **promoted to
  keeper**: it is the structurally-correct identification grain of a
  mechanism the keeper already arms, at zero fitted parameters (rule 1: the
  most structurally faithful run is the keeper — improvement on the standing
  FAILs is neither required nor evidence).
* K3 fails → the arm is **`I` (inert)** on the matrix; registered; keeper
  unchanged.
* Any §5 kill fires (with §4 clean) → the arm is **registered, not promoted
  in-session**; the matrix cell records **`O`** with the evidence, and the
  decision is **put to the owner with the numbers in hand** (rule 1 both
  directions; the owner's standing structural-integrity instruction — the
  ercot149 precedent — quoted in the escalation). It is not recorded `R` — a
  fit regression under a correct identification is an escalation, not a
  refutation.

Both arms are registered on the dashboard whatever the verdict (rule 15).

---

## §6 — Solves

Two, three years each, one invocation apiece (rule 16), years sequential
inside an invocation (rule 12). **Arms run SEQUENTIALLY, not concurrently**:
ERCOT per-plant three-year solves are multi-GB; this container is 15 GB + a
12 GB swapfile asserted at session start (`swapon --show` re-checked before
each arm).

```
PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
  results/calibration/ercot149_gas_event_cap_arm \
  --out-dir results/calibration/ercot150_control_A \
  --note "ercot-150 same-HEAD zero-delta control"

PYTHONPATH=.:src .venv/bin/python scripts/replay_keeper.py \
  results/calibration/ercot149_gas_event_cap_arm \
  --out-dir results/calibration/ercot150_zonalanchor_B \
  --set gas_offer_margin_zonal_anchor=true \
  --note "ercot-150 single delta: gas_offer_margin_zonal_anchor=true on the ercot149 keeper"
```

Post-solve, per arm: `legitimacy_diagnostics.py` (else C7/C8 score SKIPPED),
dashboard registration, `calibration_verdict.py --write-metrics` plus the
full-verdict capture, then the A/B scorer and an attestation generated from
the committed JSON (the `gen_pjm144_attestation.py` pattern — nothing
hand-transcribed).
