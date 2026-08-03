# PRE-REGISTRATION — miso-121: `dual_fuel_switching` at MISO (matrix §5.4 item 5, cell `U`)

**Session:** miso-121, branch `claude/miso-121-dual-fuel-switching-bxpjo2`, off
`origin/main` at `f0b8c02`. **Keeper under test and expected UNCHANGED:**
`2026-08-03-miso-117b-ct-heat` (`results/calibration/miso117_ctheatrate_B`,
determination NOT-YET, sole FAIL C7 `COAL_PRB` ×3y, ledgered caveats 2/3
`{C3a, C3c}`).

**Written, committed and pushed BEFORE any measurement in this session and
BEFORE any arm solves.** Every band, kill and disposition below is fixed here in
advance. Nothing in §5 may be re-designed after a number exists.

**Contamination declared up front (as miso-119/120 did).** This session is not
blind. Before writing this document it read: the miso-119/120 finding, the MISO
lever queue (`docs/mechanism-testing-matrix.md` §5.4), the matrix row, the
mechanism's own source (`data/fuel/dual_fuel.py`, `data/fleet/eia860.py`,
`data/fuel/plant_prices.py`, `data/fuel/resolve.py`) and the keeper's own armed
`run_config.json`. Those are **construction facts** — what the mechanism does and
what the keeper arms — not outcomes. **No quantity that any band below is scored
against has been computed.** What protects the result is that the decision rule
is fixed before the measured quantities exist and is then applied verbatim.

---

## 1 — The mechanism, exactly as implemented

`dual_fuel_switching` (`scenarios.py:9320`, default off) is an **objective-only
elementwise cap** on the delivered fuel-price array, applied in
`data/fuel/resolve.py:224` *after* the zonal-basis transform:

```
for each gas generator g whose (plant_code, plant_group) is in the EIA-860
  Multifuel capable set:            fuel_prices[g, :] = min(fuel_prices[g, :], oil_hourly[:])
```

* **Capability** (`data.fleet.eia860.dual_fuel_plant_groups`) — operable
  EIA-860 units with `Energy Source 1 == NG` and
  `Switch Between Oil and Natural Gas? == Y`, classed through the same
  `classify_plant` the fleet loaders use so the `(plant_code, plant_group)` keys
  line up with the per-plant tranche fleet. Oil-primary switchers are excluded
  (already modelled as oil units).
* **Switch price** (`data.fuel.dual_fuel.dual_fuel_oil_price_series`) — the
  measured ISO-month EIA-923 (F923) Schedule 5 **Petroleum** receipt cost
  (`iso_monthly_oil_prices`), volume-weighted across the ISO's plants, expanded
  to hours; NaN months fall back in **backcast mode** to the flat national
  constant `constants.OIL_PRICE_PER_MMBTU`.
* **No LP structural change.** Heat rate and emission rate stay on the gas
  characterization. The mechanism can only ever **lower** a capable unit's fuel
  price, never raise it.

**The decisive arithmetic property, stated in advance:** `min(a, b) == a`
whenever `a ≤ b`. If no capable generator-hour in the keeper's own resolved
fuel-price array has `gas_price > oil_price`, then arming the flag leaves the LP
input array **byte-identical** and the arm is inert *as an identity*, not as an
estimate. This is the miso-109 `hydro_budget_nameplate_aware` adjudication
shape (`L1 = 0.000` → `I`, no solve), and it is the reason a zero-solve verdict
is reachable here.

**Two sibling cells are NOT under test and stay OFF** (rule 19 `[R-ONE-MECH]`):
`dual_fuel_oil_reattribution` (a reporting relabel that requires this
mechanism) and `dual_fuel_oil_daily_parity` (a granularity re-grain of this
mechanism's cap that requires it). Each is its own cell and its own charter.

---

## 2 — What the keeper arms on the gas side (construction fact, read before writing)

| key | keeper value |
|---|---|
| `gas_price_override` | 2.54 / 2.19 / 3.52 $/MMBtu (measured annual HH pin, by year) |
| `gas_hub_basis_overlay` | **False** |
| `gas_hub_basis_daily` | **False** |
| `miso_zonal_gas_basis` | True (mean-zero core; miso-119 measured max \|anchor_z − ISO\| = 0.1799 $/MMBtu) |
| `miso_pjm_border_anchor` | True |
| `dual_fuel_switching` | **False** (the cell under test) |

This is recorded **as a construction fact, not as a prediction**, and §5's bands
are scored on the *measured* array, not on this table. It is stated here so that
a reader can see the session knew the keeper's gas path carries no daily/hourly
hub overlay when it wrote the bands — the honest position, given that the
NYISO/NEISO lanes where this mechanism is `K` are precisely the lanes whose
winter gas *does* carry an AGT/Transco daily hub spike.

---

## 3 — The Phase-0 question (this is a MEASURED IDENTIFICATION, not a solve)

**Does MISO's own data identify all three legs the mechanism needs?**

* **(a) CAPABILITY** — which MISO units are dual-fuel, per-plant, from EIA-860
  primary/secondary fuel + the Multifuel switch flag, intersected with the
  keeper's own fleet. Not assumed, not transferred from PJM.
* **(b) SWITCH PRICE** — the delivered oil price at which switching becomes
  economic, from MISO's own F923 Petroleum receipts. Must satisfy rule 13
  `[R-MEASURED]`: a formulaic input that would **regenerate for a forward year
  from forward drivers** and respond to changed conditions.
* **(c) EVENT WINDOWS** — do MISO's **own** winter events show the switch in
  CAMPD unit fuel-type reporting? If the windows are not observable in MISO's
  own data, the row is adjudicated **on that**, and said so.

**Rule 22 `[R-HOLDOUT]` scope bar, binding on every leg including (c):** MISO
holds **no** `calibration-complete` marker. The window is **2023–2025 only**.
Winter Storm **Elliott (Dec 2022) is OUT OF SCOPE** and will not be solved,
scored, or read as an outcome — the in-window winter events are Jan-2024
(Gerri/Heather) and Jan-2025. "Elliott-class" in the queue prose names the
*phenomenon*, not a scoreable window here.

---

## 4 — Phase-0 construction (fixed here; no re-design later)

All four legs are **no-LP**. The model side is reconstructed from the keeper's
own `results/calibration/miso117_ctheatrate_B/run_config.json`, dropping **only**
`scenarios._CACHE_KEY_RETIRED_FIELDS` keys and **hard-failing on any other
unknown key** (the standing probe duty). Years 2023, 2024, 2025.

* **Leg A — capability census.** Build the keeper's MISO fleet at HEAD; intersect
  `(plant_code, plant_group)` with `dual_fuel_plant_groups()`. Report capable
  tranche count, capable MW, capable share of MISO gas MW, and the per-plant
  roster.
* **Leg B — switch price.** `iso_monthly_oil_prices(config, y)` for each year.
  Report months carrying a measured MISO receipt vs NaN (fallback) months, and
  the delivered level.
* **Leg C — arithmetic binding.** Resolve the keeper's own `(n_gen, T)`
  fuel-price array at HEAD **pre-`min`**, and compute over capable gen-hours
  `Δ_fuel = gas_price − oil_price` (exactly `dual_fuel_switch_mask`'s
  comparison). Report `max Δ_fuel`, the count of binding gen-hours, and — for
  binding hours only — `Δ_offer = Δ_fuel × heat_rate`.
* **Leg D — event-window observability.** For the capable roster's CAMPD units,
  tabulate reported fuel type across the **in-window** winters (Jan/Feb/Dec 2023,
  2024, 2025), and report oil-reporting unit-hours and the MW behind them.

---

## 5 — Pre-declared routes, bands and the disposition rule (BINDING)

### 5.1 Inertness routes — any one firing yields `U` → `I` with **ZERO solves**

| route | fires when | meaning |
|---|---|---|
| **I-A** CAPABILITY-ABSENT | capable capacity `< 500 MW` **or** `< 1.0 %` of MISO gas MW | too little capacity to move an ISO-level scored criterion; the mechanism has no MISO fleet to act on |
| **I-B** SWITCH-PRICE-UNIDENTIFIED | `< 50 %` of the 36 ISO-months carry a measured MISO F923 Petroleum receipt | the parity price is mostly the flat **national** `OIL_PRICE_PER_MMBTU` constant, so leg (b) is not identified from MISO's own data and fails rule 13's forward-regeneration test |
| **I-C** BYTE-IDENTITY | `max Δ_fuel ≤ 1e-9 $/MMBtu` over all capable gen-hours, all 3 years | **the `min()` is the identity map**; armed and disarmed LP inputs are byte-identical; inert as an *identity*, not an estimate |
| **I-D** UNOBSERVABLE-WINDOWS | zero oil-reporting unit-hours for the capable roster across all in-window winters, **or** MISO's CAMPD extract carries no fuel-type field able to distinguish oil burn | MISO's own data does not observe the phenomenon, so the mechanism has no MISO validation target — the queue's own leg-(c) adjudication route |
| **I-E** PRICE-INERT-EX-ANTE | L1–L4 all pass but the **marginal-tranche** statistic in §5.2 falls below its bar | the sharper screen miso-119's DO-NOT-REDO asked for |

### 5.2 The LIVE bars (all five must pass to authorize Phase 1)

* **L1** capable MW `≥ 500` **and** `≥ 1.0 %` of MISO gas MW.
* **L2** `≥ 50 %` of 36 ISO-months carry a measured MISO F923 Petroleum receipt.
* **L3** `≥ 100` capable gen-hours with `Δ_fuel > 0`, in at least one year.
* **L4** `≥ 1` oil-reporting capable unit-hour observable in MISO's own in-window
  CAMPD data.
* **L5 (marginality — the miso-119 lesson, binding).** Restrict the binding
  gen-hours to tranches the keeper's **own committed P1** leaves *partially
  loaded* (`0 < P < pmax × availability`, i.e. genuinely price-setting), and
  require the **capacity-weighted p50** of `Δ_offer` over those marginal binding
  gen-hours `≥ 0.10 $/MWh`.

**DO-NOT-REDO carried in verbatim from miso-119/120 and binding on this row
too:** `max |Δ_offer|` is an **UPPER bound only**. It may **not** be used as a
price-side *lower* bound or as a liveness argument. L5 is deliberately written on
the **p50 over marginal tranches**, because miso-119 measured that the capacity
census max over-bounded the realized price effect by two orders of magnitude
while capw p50/p95 were the predictive statistics.

### 5.3 Disposition rule (pre-committed, applied verbatim)

* **Any of I-A…I-E fires** → cell `dual_fuel_switching` × MISO **`U` → `I`**;
  **keeper UNCHANGED**; **no solve, no arm, no run registered**. Rule 15 is
  satisfied by *explicitly stating in the finding that this phase produced no
  LP run*, not by registering one. The matrix cell + §5.4 queue prose are
  stamped in this same session (rule 28b) and a finding doc is pushed.
* **All of L1–L5 pass** → Phase 1 is authorized: a same-HEAD two-arm A/B via
  `scripts/replay_keeper.py` on `miso117_ctheatrate_B`, both arms
  `--year 2023 2024 2025` in one chain, **arms sequential**, per-arm post-solve
  order: `dashboard_add_run.py` (top-15 retention) → `legitimacy_diagnostics` →
  `gen_miso121_attestation.py` + `build_dof_ledger` → `calibration_verdict
  --write-metrics` → the A/B scorer. Phase-1 gates would then be K1 flag
  fidelity / K2 control integrity / K3 liveness / K4 single delta / K5 year span,
  written to this document *before* Phase 1 runs.

### 5.4 Named-successor clause (fixed in advance, so it cannot be invented later)

**If I-C fires (byte identity) BUT leg D shows real, observed MISO oil
switching in-window**, then the `I` is on the mechanism **as armed**, and the
finding must name the missing **prerequisite** — a MISO gas *time-shape*
overlay capable of reaching oil parity — as a **separately-chartered
successor**, together with the specific new evidence that would re-open this
row. In that case the finding states plainly that the model does not reproduce
an observed MISO behaviour, and does **not** dress the inertness up as a
clean bill of health. Conversely, if I-C and I-D both fire, the row closes as a
phenomenon MISO's own data does not exhibit at scoreable scale.

**No successor may be chartered in this session** — naming is not chartering
(the miso-118 §5 Dearborn precedent).

---

## 6 — Kills (any firing stops the session; none may be waived after the fact)

* **P1 — no tuning (rules 5 / 23 `[R-FROZEN-DERIVE]`).** Nothing in Phase 0 is
  fitted, swept, or re-derived. The capable set, the F923 oil series and the
  keeper's anchors are **read**. If any leg's answer tempts a re-derive against a
  residual, the session stops and reports instead.
* **P2 — rule 22 `[R-HOLDOUT]`.** 2023–2025 only, in every leg. No out-of-training
  year is solved, scored, or read as an outcome; Elliott (Dec 2022) is out of
  scope by construction (§3).
* **P3 — rule 25 `[R-ISO-SCOPE]`.** PJM's / NYISO's / NEISO's `K` on this row
  **predicts nothing** for MISO and no parameter crosses the boundary. MISO's
  capability set, oil series and fleet weights come from MISO's own data. A
  verdict reached here likewise does not fill any other ISO's cell.
* **P4 — rule 19 `[R-ONE-MECH]`.** Nothing stacks: `dual_fuel_oil_reattribution`
  and `dual_fuel_oil_daily_parity` stay OFF; neither is adjudicated here.
* **P5 — standing MISO bars, all untouched.** The h14-21 `CT_PEAKER` floor limb
  is not relaxed and `min_stable_pct` is not re-derived (rules 1/14/23/25);
  `CC_CHP` volume/heat-rate closed (miso-116/118); trough quantity closed
  (miso-115/116); `CT_CHP`/`ST_CHP` ratios VOID; `miso_cc_coal_rebalance`,
  `miso_firm_import_floor`, `miso_pjm_lmp_import_pricing` refused; seam hod
  mis-shape unchartered; miso-89 ledgered; regulated-PRB family SPENT;
  `gas_offer_margin_zonal_anchor` CLOSED `I`.
* **P6 — no C7 claim.** `C7 COAL_PRB` is **data-blocked** and this lever is not a
  C7 instrument. No C7 result may be claimed in either direction, and the C7
  residual stays routed to the blocked miso-78/79 congestion + sub-hourly-RT
  lane.

---

## 7 — Governance duties this session owes regardless of outcome

* **Rule 15** — every arm registered in-session, **or** an explicit statement
  that a no-LP phase produced no run.
* **Rule 16** — any arm covers `2023 2024 2025` in one bundle.
* **Rule 26 `[R-REGISTRY]`** — arming visible in `run_config.json`; no off-registry
  channel.
* **Rule 28b** — the matrix cell is stamped in **this** session, inert verdicts
  included, alongside the §5.4 queue prose.
* **Rule 27 `[R-PUSH]`** — exact on-disk bytes; blob-verify line count + hash after
  any push touching a ≥300-line file.
* **Rule 21 `[R-DOF]`** — any arm carries a DOF ledger; this mechanism adds
  **zero free parameters** (the capable set and the oil series are measured
  registries, not tunables).

**Artifacts this session will produce:** this pre-registration,
`scripts/probes/_miso121_dual_fuel_screen.py`, its JSON + text output, and
`results/calibration/FINDING-miso121-dual-fuel-switching-2026-08-03.md`.
