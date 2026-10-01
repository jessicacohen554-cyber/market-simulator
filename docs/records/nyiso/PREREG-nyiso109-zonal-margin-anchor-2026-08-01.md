# PREREG — nyiso-109: resolve the gas-offer margin anchor PER ZONE (`--gas-offer-margin-zonal-anchor`)

**Written and pushed BEFORE either arm solves.** Everything below — the
diagnosis that selected the lever, the construction gates, the REPORTED/KILL
split, the declared expected SIGN, and the rule-1 scrutiny clause that the
expected sign triggers — is fixed in advance.

**Session:** nyiso-109. **Scope item:** A (the named successor chartered by
nyiso-108 §7: *"the NYISO 2023 fossil over-pricing, now visible at +10.2 % — an
offer-stack / fuel-basis root cause"*). **Keeper under test:**
`2026-07-31-nyiso108-hydro-input-repair` (bundle
`results/calibration/nyiso108_hydrorepair_B`, **NOT-YET**, 1 FAIL (C3a 2023),
1 ledgered caveat (C3c)).
**Frozen HEAD:** `1aad56a` + this session's two commits (`df5c9e9` probe,
`e606439` mechanism). **Pre-solve evidence:**
`scripts/probes/_nyiso109_trough_offer_stack.py` →
`results/calibration/_nyiso109_trough_offer_stack.json`.

---

## §1 — The diagnosis that selected the lever, and the handoff premise it CORRECTS

Every number here is measured on committed artifacts with **no LP** — the
keeper's own `hourly/` sidecars, the committed clean `lmp/NYISO/RTM` hourly
actual, the committed bench payload, and `data/raw/NYISO/interface-flows/`.

### 1.1 The residual is not a level error — it is a COMPRESSED price distribution

On the hours whose hourly RT actual is committed in this checkout (2023: Jun +
Dec; 2024: Feb–Jun + Sep; 2025: Aug — coverage disclosed, never quoted as
full-year), the model's system load-weighted price against the actual, by
**actual-price decile**:

| | trough (d1) | d5 | peak (d10) |
|---|---|---|---|
| 2023 | **+10.85** | +7.24 | **−11.56** |
| 2024 | **+11.18** | +6.17 | **−21.30** |
| 2025 | **+9.28** | +8.55 | **−25.04** |

and by **load** decile the same shape: bottom-decile error **+8.81 / +4.92 /
+8.31**, top-decile **+0.14 / −2.02 / −13.68**. The model's within-load-decile
price dispersion is 1.9–5.0 against the actual's 3.4–16.1.

### 1.2 The handoff's "2023-specific" premise is FALSIFIED — and that is why 2023 alone fails

The trough→evening-peak amplitude, same covered hours:

| | model swing | actual swing | reproduced | trough err | peak err |
|---|---|---|---|---|---|
| 2023 | 9.37 | 13.62 | **69 %** | **+7.26** | **+3.01** |
| 2024 | 9.41 | 19.17 | **49 %** | **+5.50** | −4.26 |
| 2025 | 14.80 | 33.21 | **45 %** | **+8.65** | −9.75 |

The trough is over-priced by **+$5.5 to +$8.7/MWh in ALL THREE years**. What is
2023-specific is only that 2023 is the mild year whose peak error is also
**positive**, so nothing cancels the trough excess and the annual mean crosses
the ±10 % band. **A lever scoped to 2023 would be the wrong lever**, and the
handoff's instruction to prefer one is recorded here as corrected by
measurement rather than followed. This is the same defect PJM diagnosed at
pjm-141 (31/33/32 % of amplitude, sign-symmetric) — measured here independently
on NYISO's own data (rule 25); PJM's verdicts transfer nothing.

### 1.3 The interface/congestion route is REFUSED on NYISO's own measurement

The model's Upstate_West→Capital_Hudson link separates in **0.0 %** of hours in
all three years while the real market separates in **60.3 / 54.8 / 38.2 %**. But
the measured MIS P-32 flows show the real **CENTRAL EAST - VC** interface sits
within 50 MW of its own posted limit in only **0.8 / 0.1 / 0.2 %** of hours
(TOTAL EAST, UPNY CONED and SPR/DUN-SOUTH: **0.0 %** in every year), and the
model's monthly TTC envelope already tracks the measured monthly mean limit
(2023 model 1950…2725 vs measured 1918…2699). So the observed separation is
**not produced by the posted interface limit binding** — it is marginal losses
(zone means $−0.7…+2.0/MWh) plus sub-interface nodal constraints, neither
representable at five-zone grain. Placing a tighter limit on the model's link to
manufacture the spread would be a fitted constraint, not a measured one
(rules 5 / 14's named misalignment clause). **`measured_interface_limits` is
therefore adjudicated for NYISO ex ante, no solve** — recorded in this
session's matrix update, not tested here.

### 1.4 What the trough residual points at, arithmetically

Regressing the monthly Capital_Hudson trough (p10) on the month's measured
delivered gas (Henry Hub monthly + the committed NYISO hub basis) over the same
covered months: the model's bottom-of-stack offer is **slope 3.74 MMBtu/MWh,
intercept $16.95/MWh**; the actual's is **slope 2.24, intercept $13.19**. The
model's trough carries a materially larger **fuel-invariant adder** — the
signature of `gas_offer_net_revenue_margin`'s fixed $/MWh margin, whose implied
per-band margins at NYISO's registered curve are `CC_REGULAR` econ_low
**$5.03**, `ST_GAS` econ_low **$10.36** / econ_high **$12.52**, `CT_PEAKER`
committed **$23.65** (`derive_gas_offer_margin_anchor.py --net-revenue-check`).

---

## §2 — The lever: the mechanism's own identification point, evaluated at the grain its definition requires

`apply_gas_offer_margin` adds `markup_hr × (anchor − fuel)` and states its own
identity: *"At `fuel == anchor` the reformed offer reduces EXACTLY to the
registered band multiplier, so the anchor is an identification constant, not a
tunable."* That is a statement about **a unit's own delivered fuel**.

`GAS_OFFER_MARGIN_ANCHOR_BY_ISO` is derived from
`data.fuel.trajectories._gas_series`, which is **ISO-level**: it carries the hub
overlay but **not** the per-zone basis, which the solve applies afterwards on
the `(n_gen, T)` array (`apply_nyiso_zonal_gas_basis`, which runs *before*
`apply_dual_fuel_pricing` and therefore before the margin). On an ISO with no
zonal basis the two are the same series and the single anchor is identified
everywhere. **On NYISO they are not**: the zonal basis is anchored so the
**reference** zone (`Capital_Hudson`, Iroquois Z2) is unchanged and every other
zone shifts strictly **down** to its own measured pipeline hub. Measured offsets
(`nyiso_zonal_gas_offsets`, from the committed SOM Figure A-6 table):

| zone | hub | 2023 | 2024 | 2025 |
|---|---|---|---|---|
| Capital_Hudson / Lower_Hudson / Long_Island | Iroquois Z2 | 0.00 | 0.00 | 0.00 |
| NYC | Transco Z6 NY | −1.34 | −0.71 | −1.38 |
| Upstate_West | Tenn Z4 200L | −1.46 | −1.07 | −3.08 |

So a NYC or Upstate_West gas tranche prices its markup at a fuel level it
**never pays**, and the further below the anchor it sits the larger the uplift
its band multiplier never contained. `derive_gas_offer_margin_anchor.py
--by-zone` (new; applies the **runtime** transform to the same series over the
same 2023–2025 window, so the values are by construction the levels the solve
prices those zones at):

| zone | 2023 | 2024 | 2025 | **anchor** | vs ISO 3.9046 |
|---|---|---|---|---|---|
| Capital_Hudson / Lower_Hudson / Long_Island | 3.3566 | 2.7969 | 5.5602 | **3.9046** | **0.0000** |
| NYC | 2.0166 | 2.0869 | 4.1802 | **2.7612** | −1.1433 |
| Upstate_West | 1.8966 | 1.7269 | 2.4802 | **2.0346** | −1.8700 |

**Zero fitted parameters.** This is the *same* measurement as the ISO anchor
evaluated per zone, rule-23 frozen against residuals (it re-derives only when
the gas source data or the per-zone hub table changes). It adds no new
identification constant, no new mechanism, and no second channel: a band-scoped
rebasis anchor (ERCOT-118/119 `margin_anchor_*`) keeps precedence, so the two
never stack (rule 19 `[R-ONE-MECH]`). It is rule-25 safe by construction —
`GAS_OFFER_MARGIN_ANCHOR_BY_ZONE` carries **NYISO only**, derived from NYISO's
own basis table, and an ISO without a table hard-fails rather than borrowing.

**Cross-ISO exposure is REPORTED, never acted on here:** ERCOT, PJM and MISO
also arm a zonal gas basis on their keepers, so the same grain mismatch exists
in their lanes. Their cells enter as `U`; measuring their exposure is not this
session's scope and no other ISO's keeper is touched.

---

## §3 — Declarations fixed IN ADVANCE

### 3.1 The expected SIGN, and why it is grounds for EXTRA scrutiny

Every zonal anchor is **≤** the ISO anchor and every markup is ≥ 0, so
`markup_hr × (anchor_z − fuel) ≤ markup_hr × (anchor_ISO − fuel)` for every
marked-up tranche: **offers can only fall or stay equal, never rise.** In the
three reference-hub zones nothing moves at all. So the arm's price effect is
**weakly downward**, which is the direction the failing C3a 2023 (+10.2 %)
wants.

**That is pre-registered as grounds for scrutiny, not encouragement**
(rule 1 `[R-STRUCT]`, both directions; the nyiso-101 posture). The lever is
defended on the arithmetic of §2 — the mechanism's own stated identity is false
in two of five NYISO zones today — and it would be the correct change **even if
C3a moved the wrong way or not at all**. Conversely a C3a improvement is **not**
evidence the lever is right; the construction gates in §4 and the
non-degradation gates in §5 are what decide.

### 3.2 What is NOT claimed, declared before the solve

* **No C3c claim.** C3c is out of scope (owner-closed queue, re-open condition
  is a Capital_Hudson F/G topology split under its own charter). A C3c movement
  in either direction is REPORTED and never banked.
* **No amplitude claim beyond the trough half.** The measured defect is
  sign-symmetric; this lever touches only the trough side. The peak half
  (−$4.3 / −$9.8 in 2024 / 2025) is untouched and stays open.
* **No hydro claim.** The nyiso-108 hydro input repair is not re-litigated,
  re-tuned or reverted (rule 14; explicitly out of scope).
* **The hydro VOLUME statistic stays declared plumbing** (nyiso-108 §6) and is
  never quoted here.
* **The barred statistics stay barred**: NYISO 2025 `solar` (+437.2 %),
  2025 `OTHER` (+11.4 %), 2025 `ST_CHP` (+85.0 %), and `hydro` in every year.

### 3.3 Holdout

Both arms solve **[2023, 2024, 2025]** and nothing else (rules 16 / 22). The
holdout spend freeze is ACTIVE; NYISO holds `complete`, is absent from `final`,
and no out-of-training year is touched by any solve, score or probe in this
session.

---

## §4 — Construction gates (these, and ONLY these, can invalidate the experiment)

* **K1 flag fidelity.** Arm B's `meta.json` / `run_config` records
  `gas_offer_margin_zonal_anchor == true` **and**
  `gas_offer_margin_anchor_by_zone` equal to
  `constants.GAS_OFFER_MARGIN_ANCHOR_BY_ZONE["NYISO"]`; the control records
  `false` / `null`. Both record `gas_offer_net_revenue_margin == true` and
  `gas_offer_margin_anchor == 3.9046`.
* **K2 control integrity — TWO BASES, only the first is a gate.** The
  **scorecard** basis (the control reproduces the committed keeper's
  determination and every per-criterion status) is the pre-registered gate. The
  stricter **byte** basis (class-hour for class-hour, < 1e-6 MW) is computed and
  **REPORTED**; a byte miss is same-HEAD drift and is its own finding, not a
  failed gate. Drift is expected to be possible here in a way it was not at
  nyiso-108: HEAD has moved 4 solve-path commits since the keeper's `e1a4bc6`
  (`data/hydro.py`, `data/fleet/arrays.py`, `model/reserves/spec.py`). NYISO is
  in neither `EIA930_PS_FOLDED_INTO_WAT` nor `EIA930_PS_SPLIT_COMPLETE_FROM`, so
  the hydro change is expected inert for NYISO — **that expectation is recorded
  so the control can falsify it.**
* **K3 mechanism is LIVE.** `max |Δ class MW|` on a class-hour **> 50 MW** in
  **every** year, and the arm's system load-weighted mean price differs from the
  control by **> $0.10/MWh** in every year. Failing K3 is verdict `I` (inert),
  not `R`.
* **K4 single delta.** The two arms' `run_config` scenario blocks differ in
  **exactly** the two zonal-anchor keys and nothing else.
* **K5 year span.** Both bundles `[2023, 2024, 2025]`.
* **K6 direction integrity.** The arm's zonal price change is **≤ 0 in
  Capital_Hudson / Lower_Hudson / Long_Island to < 1e-6 $/MWh of zero** (the
  reference-hub zones carry an unchanged anchor, so any movement there is a
  second-order re-dispatch effect and must be disclosed, not silently absorbed).
  A *rise* anywhere is a construction error, not a result.

---

## §5 — What can KILL the arm (pre-registered non-degradation gates)

Scored from `scripts/calibration_verdict.py` on the arm vs the **control**, never
against the committed keeper.

* **P1 — C1 free-class must not regress.** The control's `free` pass count is
  10/10; the arm must be **≥ 10/10 free** and **≥ 14/14 all-class**. A single
  free-class cell dropping out of band KILLS the arm. (The knife-edge cell is
  2023 `CC_REGULAR` at −2.80 of ±2.94 — ~0.14 TWh of budget.)
* **P2 — no NEW load-bearing FAIL.** The arm's FAIL set must be a **subset** of
  the control's `{C3a}`. A C3b price-shape FAIL — the plausible failure mode,
  since cheapening only the trough half of a compressed distribution can flatten
  it further — KILLS the arm.
* **P3 — protective gates hold.** C6 / C7 / C8 must each stay PASS. C8's
  fragile cell is 2024 `ST_GAS` (30.6 % forced, a grounded above-budget pass);
  losing its grounding KILLS the arm.
* **P4 — slack and dump stay 0.0** in every year of both arms.
* **P5 — no fitted follow-up.** If the arm lands the 2023 C3a inside the band,
  no further parameter may be moved in this session to "finish" it, and if it
  does not, the anchor values may **not** be re-derived to close the gap
  (rule 23). The anchors are what the derive script printed; they are not swept.

**Promotion rule, pre-committed:** the arm is promoted only if **every gate in
§4 passes and no gate in §5 kills it**. A C3a 2023 that returns inside ±10 %
additionally moves NYISO **NOT-YET → CALIBRATED-WITH-CAVEATS** and requires the
keeper shard's `frontier.amendment_note` to say so. A C3a that stays outside the
band while §4/§5 hold is **still a legitimate promotion candidate on rule-1
structural grounds** (the nyiso-108 precedent, owner standing instruction) — but
that call is put to the owner and recorded as such, never taken silently.

---

## §6 — Solves

Two, three years each, one invocation apiece (rule 16), years sequential inside
an invocation, at most two invocations concurrent (rule 12):

```
scripts/replay_keeper.py results/calibration/nyiso108_hydrorepair_B \
  --out-dir results/calibration/nyiso109_control_A \
  --note "nyiso-109 same-HEAD zero-delta control"

scripts/replay_keeper.py results/calibration/nyiso108_hydrorepair_B \
  --out-dir results/calibration/nyiso109_zonalanchor_B \
  --set gas_offer_margin_zonal_anchor=true \
  --note "nyiso-109 single delta: gas_offer_margin_zonal_anchor=true on the nyiso-108 keeper"
```

Both bundles are registered on the dashboard whatever the verdict (rule 15).
