# FINDING — ercot-150: the zone-resolved gas-offer margin anchor is a KEEPER at ERCOT — the LEVEL side prices, the spread side is topology-inert, and the honest identification cut its own West leg 5×

**Session:** ercot-150. **Frozen HEAD:** `37cc8e3` (= origin/main carrying this
session's mechanism-registration commits, merged mid-session).
**Outgoing keeper:** `2026-08-01-ercot149-gas-event-cap` (NOT-YET, 4 FAILs).
**NEW KEEPER:** `2026-08-02-ercot150b-zonal-anchor`
(bundle `results/calibration/ercot150_zonalanchor_B`), **NOT-YET with every
criterion status identical to the outgoing keeper** — promoted as the more
structurally faithful run (rule 1), not on any residual.
**Pre-registration:** `results/calibration/PREREG-ercot150-zonal-margin-anchor-2026-08-02.md`,
committed and pushed **before either arm solved**, including the derived
anchor table, the measured applier-convention analysis, the zonal K3
construction, and the kill set.
**Solves: 2** — one same-HEAD zero-delta control
(`2026-08-01-ercot150a-control-zerodelta`, bundle
`results/calibration/ercot150_control_A`), one single-delta arm, three years
each, sequential (15 GB box + 12 GB swap asserted at session start).
**Scorer artifact:** `results/calibration/_ercot150_zonal_anchor_ab.json`;
derivation record `_ercot150_zonal_anchor_derivation.json`; full verdicts
`_ercot150_verdict_{A,B}.json`.
**Owner instruction (in-session, before results):** *"Is this a recommended
keeper candidate? If so plz promote. If structural integrity improves but
gates regress that may still be a keeper."* — §6 executes it.

---

## §0 — Headline

nyiso-109 measured an identification-**grain** error in
`gas_offer_net_revenue_margin` — the anchor of `markup_hr × (anchor − fuel)`
is ISO-level while the solve prices each gas unit at its zone's basis — and
chartered per-ISO transfers. PJM adjudicated `I` (dispatch-live,
price-inert: its mean-zero convention on a price-coupled topology). ERCOT's
handoff posed the open question: its measured spread is the largest of the
six ISOs (2.580 $/MMBtu) and its West decouples under binding GTCs — does
ERCOT price what PJM absorbed?

**The answer splits exactly along ERCOT's measured convention difference,
and both halves were pre-registered.** ERCOT's applier is NEITHER NYISO's
one-sided table NOR PJM's pure mean-zero centroid: it is a capacity-weighted
mean-zero spread **plus a flat measured EP level correction** the ISO anchor
does not carry. The A/B shows:

* **The LEVEL side prices.** K3's zonal liveness gate passes in every year —
  max zone |Δλ| **0.356 / 0.304 / 0.319 $/MWh** against the 0.10 gate,
  system load-weighted **+0.446 / +0.329 / +0.339** — because the level
  correction moves every zone's marked-up offers in the same direction,
  which no coupled topology can cancel. This is why ERCOT's verdict is the
  opposite of PJM's on the same mechanism.
* **The SPREAD side is topology-inert, exactly as at PJM.** The model's West
  decouples from North in only **6 / 17 / 2 hours a year**; precisely in
  those hours the West delta shows the predicted discount (2024
  decoupled-hours mean **−0.05** vs +0.30 in coupled hours), and the annual
  West mean rides the ~8750 coupled hours up with the system (offer-side
  sign agreement 5/6; the one miss is West — a topology outcome, REPORTED
  as pre-registered, never gated).

Every construction gate passes, kills P1/P2/P3/P5 pass, and P4 fired on a
**template artifact** (§5). Under the prereg's escalation branch and the
owner's standing in-session instruction, the arm is **promoted**: it is the
correct identification of an armed mechanism's own anchor, at zero fitted
parameters, with every criterion status identical to the keeper it replaces.

---

## §1 — The admissibility work that shaped the experiment (no LP)

### 1.1 The keeper's convention, measured before anything was written

The three handoff facts, established from the ercot149 bundle's own record:

1. **Arming channel.** The zonal machinery rides the
   `coal_prb_sigmoid_overrides` (`prb_overrides`) channel
   (`ercot_zonal_gas_basis: true`, `ercot_west_netload_gas_shape: true`,
   `ercot_west_gas_delivered_floor: 0.4`); the env-gated top-level meta keys
   sit at their INERT values, so `replay_keeper._ENV_GATED_INERT` never
   fires and `--set` single-deltas work. NOT armed:
   `ercot_gas_contract_haircut`, `ercot_gas_delivered_floor_basis`,
   `ercot_offer_hrmult_ep_rebasis` (⇒ zero band-scoped anchors; under the
   lever every marked-up tranche — 1132/1132/1135 — resolves its zone).
2. **The applier.** `ZONAL_BASIS_APPLIERS["ERCOT"] =
   apply_ercot_zonal_gas_basis`: per-unit offset = `level_corr +
   (basis_zone − capw_mean)`, `level_corr = EP basis − (−0.50)` =
   **+0.5045 / +0.4142 / +0.0366 $/MMBtu** (2023/24/25), hourly-floored at
   `_GAS_PRICE_FLOOR`. The registered ISO anchor 2.2494 = HH − 0.50 with no
   EP term — the fleet centroid sits ABOVE the anchor by the level
   correction, and zones spread two-sidedly around the centroid.
3. **What the lever cannot touch.** `apply_cc_committed_offer_margin`
   (ERCOT-139) reads the CONFIG-level anchor only — K1 asserts the pair
   unchanged in both arms.

### 1.2 The derive's first run overturned its own template — the load-bearing correction

The pjm-144 construction (synthetic ISO-anchor series + the zonal-basis
applier alone) produced a West anchor of 0.79 (−1.46 vs the ISO anchor). But
the reconstruction's own fuel path showed the keeper's
`ercot_west_netload_gas_shape` lifting realized West gas **1.62 / 0.21 /
0.65 → 1.99 / 1.15 / 2.74 $/MMBtu** — its burner-tip delivered floor (0.4)
converts the deep-Waha years' mean-preservation into a large level lift. A
pre-shape West anchor would have priced West markups at a fuel level West
units never pay — **the same grain-error class this lever exists to fix,
reintroduced at one zone by ignoring a later fuel-path stage.**

The anchors were therefore identified on **the keeper reconstruction's own
resolved `fuel_prices`** — the exact `(n_gen, T)` array
`apply_gas_offer_margin` prices against
(`derive_gas_offer_margin_anchor.SOLVE_FUEL_ARRAY_ISOS`), with hard checks:
the keeper must arm both fuel-path stages, the bundle's gas prices must
equal the training-window values, and a within-zone spread guard
(median-row anchor, hard-fail past 0.25 $/MMBtu) rejects any per-unit
transform. Every zone was within-zone uniform. **The correction CUT the
West leg ~5× (−1.46 → −0.29)** — the direction a residual-hunting
construction would never move — and was committed in the prereg before any
arm solved.

### 1.3 The registered table

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 2.2494 |
|---|---|---|---|---|---|
| South | 3.5721 | 2.6518 | 3.6094 | **3.2778** | +1.0284 |
| South_Central | 2.9021 | 2.4718 | 2.8994 | **2.7578** | +0.5084 |
| North | 2.4721 | 2.2318 | 3.4494 | **2.7178** | +0.4684 |
| Northeast | 2.4721 | 2.2318 | 3.4494 | **2.7178** | +0.4684 |
| Houston | 2.1921 | 1.8718 | 2.8694 | **2.3111** | +0.0617 |
| West | 1.9866 | 1.1497 | 2.7396 | **1.9586** | −0.2908 |

Panhandle omitted (no gas capacity in any training year; absent zones keep
the window anchor — a no-op on an empty zone). Inertness bar: max |anchor −
2.2494| = 1.0284 ≫ 0.1 → LIVE ex ante, 5 of 6 zones beyond the bar
(Houston +0.0617 inside it). Zero fitted parameters (+1 derived DOF entry,
8 → 9; `n_residual` 6 unchanged); default `ScenarioConfig().cache_key()`
byte-identical to origin/main; zonal-anchor tests 16/16; the derive
re-reproduced **byte-identically** on the completed clean tree before the
solves. The derivation record carries the per-year decomposition
(post-basis vs realized West, capw means removed +0.2024/+0.0824/+0.0372,
capw invariant vs ISO+level with the West-lift residual +0.0598, and the
exact-reproduction check).

---

## §2 — Construction gates: five of five PASS

| gate | result |
|---|---|
| **K1** flag fidelity | **PASS** — arm `true` + resolved 6-zone map equal to the registry; control `false`/`null`; `gas_offer_net_revenue_margin` at 2.2494 and the ERCOT-139 CC-committed pair unchanged in **both** |
| **K2** control integrity | **PASS on the scorecard basis** — control reproduces the keeper's determination and every criterion status, C1 16/16 · 12/12. **The REPORTED strict-byte basis measured REAL same-HEAD drift** (§4) — the first zonal-anchor lane where the control falsified the drift-inertness expectation, exactly what the gate's two-basis design exists to catch |
| **K3** liveness | **PASS** — MW leg (max class-hour Δ 1073 / 1458 / 1432 MW) AND the zonal price leg (max zone \|Δλ\| 0.356 / 0.304 / 0.319 vs the 0.10 gate) in every year |
| **K4** single delta | **PASS** — the two scenario blocks differ in exactly the two zonal-anchor keys |
| **K5** year span | **PASS** — both bundles [2023, 2024, 2025]; holdout freeze ACTIVE and untouched |

*(No K6 — dropped ex ante: a two-sided spread on a one-sided level admits no
one-sided gate; direction REPORTED.)*

## §3 — Kill gates: P1/P2/P3/P5 pass; P4's trip is a template artifact

P1: arm C1 **16/16 all / 12/12 free**. P2 at BOTH grains: criterion-level
FAIL sets identical ({price_mean, price_shape, price_tail, shape}); across
all 73 per-(criterion, year, key) rows of the captured verdicts, **no row
that PASSES in the control FAILs in the arm** (the ERCOT-specific leg
guarding the 2023-only C3a/C3b). P3: governance + forced_share PASS. P5:
nothing swept — the anchors are the derive's output, untouched after the
result.

**P4 (slack and dump exactly 0.0) FIRED — on both arms' shared inheritance,
not on the delta.** The gate was transcribed from pjm-144, whose keeper
genuinely carries zero slack. The ercot149 keeper ITSELF carries slack
**3478.9 / 1114.6 / 0.0 MWh** (dump 0.0 everywhere); the control reproduces
those numbers **byte-identically**, so the gate as written cannot
distinguish the arms — it tests the keeper's standing state. The arm's true
delta is **+0.97 / +0.91 / 0.00 MWh (~+0.03 %)**: dearer marked-up offers
flip roughly one MWh-hour per year to slack at the scarcity edge — the
honest directional cost of the level side, reported, not hidden. The
prereg's pre-committed disposition for a fired kill with clean construction
is escalation to the owner with the numbers (§6).

## §4 — The K2 byte finding: real same-HEAD drift, shared by both arms

Control minus committed keeper: class-hour max **2201 / 3532 / 2983 MW**,
hourly zone |Δλ| up to $130 in 757 / 1443 / 2115 hours — with annual
load-weighted λ within **−0.007 / −0.068 / −0.054 $/MWh** and every
criterion status identical. This is input-level drift between the keeper's
HEAD-era clean tree and this session's regeneration at `37cc8e3` (~24 src
files moved on main; every ERCOT-live candidate is forecast-gated or
ISO-gated, so the drift is attributed to the regenerated derived inputs,
not a mechanism change). Both arms share the same tree and HEAD, so the
single-delta comparison is unconfounded — which is precisely why the prereg
scores kills against the CONTROL, never the committed keeper. Recorded as
its own finding; nothing absorbed.

## §5 — What the arm moves, reported in full

Class-energy deltas (arm − control, TWh): 2023/2024 are the level side's
clean signature — CC_REGULAR −0.302 / −0.270 and CC_CHP −0.116 / −0.132
give way to COAL_PRB +0.350 / +0.375 (the dearer marked-up CC margin
crossing coal, the ercot-138 crossing band moving the honest direction)
with CT_PEAKER +0.030 / +0.052; 2025 is mixed — CT_PEAKER **−0.197**,
CC_REGULAR **+0.130**, COAL_PRB +0.115, ST_GAS +0.086 — the near-zero 2025
level correction (+0.037) leaves the SPREAD as the dominant term, and the
South/SC premium anchors push their CTs off while cheaper-anchored CC
econ energy backfills (full table in the A/B JSON). Zonal λ:
all zones rise (+0.20..+0.36 annual mean; Northeast lowest, the big-gas
zones clustered at the top), West included (§0 — the decoupled-hours
discount is real but sub-annual). Per-year price rows, all
statuses held (margins reported, pre-declared NON-EVIDENCE): C3a
−33.3→−32.6 % (2023 FAIL), +0.6→+1.6 % (2024 PASS), −9.2→−8.3 % (2025
PASS, **away** from the band edge); C3b 0.616→0.607; C3c 2023 model tail
54→58 h of actual 181; C7 lignite r 0.886→0.888, cv-leg still the sole
shape FAIL.

## §6 — The keeper question, answered directly

**Yes — recommended, and promoted.** The prereg pre-committed: kill fires
with clean construction → registered, cell `O`, owner decides with the
numbers. The owner's standing in-session instruction (quoted in the
header) pre-delegated that decision to the session's recommendation. The
recommendation is YES on the pre-registered grounds: (a) the arm is the
structurally-correct identification grain of a mechanism the keeper already
arms, at zero fitted parameters (rule 1: the most structurally faithful run
is the keeper); (b) every criterion status, C1 score, and per-year PASS row
held; (c) P4's trip is control-shared (the gate mis-transcribed PJM's
zero-slack world into a lane whose keeper carries standing slack) and the
true delta is ~+0.03 %; (d) no improvement is credited — the C3a moves were
pre-declared non-evidence. Matrix cell **`K`**; keeper shard, status page
and `audit_keepers --iso ERCOT` all updated/PASS in-session. Supersedes
`2026-08-01-ercot149-gas-event-cap` (kept on the dashboard as the
immediate-prior comparison).

## §7 — Cross-ISO: what transfers and what does not

Nothing transfers (rule 25) — but the three-ISO pattern is now complete and
worth stating for MISO's lane: NYISO's one-sided convention priced a level
and was K; PJM's pure mean-zero spread on a coupled topology was
price-inert and I; ERCOT's spread-plus-level split the difference — the
level priced (K), the spread stayed topology-inert. **The mechanism's price
effect at every ISO so far equals its LEVEL component; no coupled topology
has priced the mean-zero spread.** MISO arms the pure mean-zero core
(spread 0.332, the smallest) on a coupled topology — its inertness prior is
now strengthened three ways, and its cell can plausibly be adjudicated `I`
ex ante by the no-LP bar with zero solves, in its own lane.

## §8 — Test baseline at this HEAD

Re-measured on the completed clean tree (never inherited): **10 known-red /
4596 passed** — chp 7, consume_lmp 1, outages 1, ff_readiness marker-state
1. The pjm-144 baseline's three stale cache-key pins are FIXED on main
(Wave-1 epoch bump; default key `603c2498bf71d21d`, worktree ==
origin/main); the transient egrid/export/ff_readiness reds measured
mid-regeneration pass on the settled tree. The 4 new zonal-anchor registry
tests are green post-registration.

**Not claimed:** no amplitude claim (within-day offer σ untouched by
construction — the xiso-1 defect's ERCOT cell stays `U`); no C3c claim; no
C7 claim; no trough/spread-lane reopen (ercot-138 §J band untouched); no
forecast-lane result; no out-of-training year touched (2023–2025 only,
freeze ACTIVE).
