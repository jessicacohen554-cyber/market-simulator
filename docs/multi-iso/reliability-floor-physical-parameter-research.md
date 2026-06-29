# Temperature-Gated Reliability Floor — Physical Parameter Research & Alignment

**Status:** Research findings + alignment audit of the implemented mechanism on
`main` (@ `b28f00d`). Produced 2026-06-29 from a fan-out web-research pass
(105 agents, 23 primary sources, 20 adversarially-verified claims). Pairs with
`reliability-floor-rebuild-plan.md` (the structure) and
`reliability-floor-coefficients.md` (the derived numbers).

**One-line takeaway for the next session:** the rebuilt engine is *structurally
correct and well-aligned* with the physical literature, but the floor
**magnitude** is sourced from the wrong quantity — the offer-curve **must-run
tranche share** (`Pct_Must_Run`), which is **0** for merchant steam/CT/CC — so
the priority classes the mechanism exists for (gas steam, CT peakers) floor at
**0** and ship `enabled=False`. The fix is to drive the floor off the **physical
minimum-stable level of a *committed* unit** (Pmin/Pmax, a turbine property) that
the **temperature gate turns on**, not the must-run share. This is a decided
direction, not an open question (see §3).

---

## 1. Cited research findings (physical, forward-reproducible)

Every value below is flagged **PHYSICAL** (regenerates for a forward year from
weather forecasts / engineering specs / published advisory triggers — admissible
under CLAUDE.md #9/#11) or **FIT-RISK** (would amount to tuning to the backcast —
reject).

### 1.1 Minimum stable level — *min-run-if-committed* (% of nameplate) — PHYSICAL

Cleanest non-fitted source: **NREL WWSIS-2 / TEPPC** (NREL/TP-5500-55588, Table 7;
verified 3-0). These are the Pmin/Pmax a unit holds *once committed* — exactly the
floor the temperature gate should impose.

| Class | Min-stable % (committed) | Source range / corroboration |
|---|---|---|
| **Gas steam (ST_GAS)** — priority | **12%** (older units 12–20%) | WWSIS-2 12%; older subcritical sits high end |
| Simple-cycle CT (CT_PEAKER) | **38%** (older frame up to 50–60%) | WWSIS-2 38%; ScienceDirect turndown review: large frame GTs ~60%, OEM mods 40–50%, advanced 20–30% |
| Combined cycle (CC_REGULAR) | **52%** | WWSIS-2 52% (least-flexible fossil) |
| Coal (ST/COAL) | **40%** | WWSIS-2 40% |
| Oil / oil-steam | **≈12%** (use steam value) | same steam physics; taxonomy lumps oil into one class |

> Caveat (flagged): WWSIS values are c.2012 Western-Interconnection per-type
> *averages*, not "older"-unit-specific. Older steam may sit toward the high end.
> Using them as-is is PHYSICAL; nudging them to improve MAE is FIT-RISK.

### 1.2 Minimum run-hours & start timescales — PHYSICAL

Gas steam **drags online rather than cycles** because of soak-gated physics: water
must reach temperature/pressure/moisture thresholds before the turbine loads
(EIA id=45956, 3-0).

- **PJM soak defaults** (Manual 15, Rev 47, 3-0): Cold soak = **0.73 × MinRunTime**,
  Intermediate = 0.61×, Hot = 0.43×. "Hot" = after overnight shutdown; "cold" =
  after a **2–3 day** shutdown. **CTs, engines, intermittent, storage have NO soak.**
- **Coal** (EPA MATS TSD, 3-0): hot ≤24 h offline, warm 25–119 h, cold ≥120 h;
  cold start of a large coal unit 4–6 h.
- **Commitment lead by start class** (WWSIS, 2-1, modeling convention not tariff):
  coal/nuclear day-ahead; CC/oil/gas-steam ~4-h-ahead; CT/IC no lead (real-time).

→ **Already implemented correctly** in `constants.py`: `ST_GAS_COMMITMENT_PARAMS`
min-run raised to **24 h** (efficient) / **48 h** (older subcritical) so a committed
boiler bridges a multi-day event; `CT_COMMITMENT_PARAMS` held at **1 h** (fast-start,
full-day floor but no event bridging). Matches the research.

### 1.3 Documented temperature triggers — cold PHYSICAL, hot PERCENTILE-METHOD

| Trigger | Value | Source | Vote |
|---|---|---|---|
| PJM Cold Weather Alert (RTO/zone) | forecast/actual **tmin ≤ 10 °F (−12.2 °C)** | PJM Manual 13 Rev 97 | 3-0 ✓ |
| PJM extra CT mobilization layer | predicted **tmin ≤ −5 °F (−20.5 °C)** | PJM Manual 13 | 3-0 ✓ |
| ISO-NE Cold Weather Watch/Warning/Event | escalating, keyed to **forecast capacity margin** under cold — *not* a fixed °F | ISO-NE Cold Weather Alerts | 3-0 ✓ |
| ISO-NE Firm Oil Storage Requirement | 40 h = **90th-pct cold-snap (4 days)** × 10 h/day | NYISO ICAPWG 2023 | 3-0 ✓ |
| PJM Hot Weather Alert ">90 °F" | ❌ **REFUTED 0-3** — no verified ISO tmax number exists | — | killed |
| "HDD > 55 = gas-constrained day" | ❌ **REFUTED 0-3** — do not hardcode | — | killed |

**Cold side** has hard operational anchors (PJM −12 °C / −20.5 °C). **Hot side** has
*no* ISO-published number → must be set by a per-zone **design-day / weather
percentile** (95th–99th-pct tmax or TMY design cooling day), symmetric with how
ISO-NE sizes cold readiness. Choosing the hot tmax because it improves the fit
would convert it into a FIT-RISK parameter.

### 1.4 Cold-season gas-electric coordination — PHYSICAL (mechanism, inventory-capped)

Most gas units lack firm pipeline transport, so on cold-threshold days stored-fuel
(oil/coal/nuclear) and **dual-fuel oil-switching** units carry reliability and are
priced into merit (ISO-NE OFSA 2018, 3-0; FERC/NERC Jan-2025, 3-0). Forward-
reproducible gated on **cold + fuel inventory**, not year-round. ⚠️ Do *not*
hardcode firm-vs-interruptible as a clean per-unit on/off switch (REFUTED 1-2) —
treat as a correlate. This is the basis for the ISO-NE/MISO-South winter deviations.

### 1.5 Single defensible cross-ISO rule

`tmax > hot-percentile(zone) OR tmin < cold-threshold(zone) → hold in-scope class
at floor for the full day; gas steam bridges to adjacent flagged days (min_event_
hours); LP dispatches economically above the floor.` Physically-justified
deviations: ERCOT summer-scarcity (hot binds), ISO-NE & MISO-South winter gas
constraint (cold + oil into merit), CAISO net-load-driven CT (evening ramp, no temp
gate). All of these are **already represented** in the rebuilt registry's `driver`
field.

---

## 2. Alignment with the implemented mechanism (`main` @ `b28f00d`)

### 2.1 What the rebuild got RIGHT (strong alignment — keep)

| Research expectation | Implementation | Verdict |
|---|---|---|
| Full-day hold, no hour-of-day windows | step-gate, 24 h on flagged days | ✅ |
| Per-(zone × class) independently toggleable | `ReliabilityFloorSpec` + `reliability_floor_overrides` keyed `ZONE:CLASS:limb` | ✅ |
| One engine, hot/cold/net-load via a `driver` field | `driver ∈ {tmax, tmin, netload}` | ✅ |
| Gas steam longer min-run; CT fast-start | `ST_GAS` 24/48 h, `CT` 1 h in `constants.py` | ✅ |
| Steam event-bridging across a multi-day event | `min_event_hours` (≥24) on ST_GAS/ST_CHP | ✅ |
| No outcome pinning; weak limbs ship OFF | p97-CF ceiling removed; enable gate ρ≥0.3, n≥30, floor>baseline | ✅ |
| Oil/oil-steam covered | floored as one `oil` class (split documented as absent) | ✅ |
| Backcast + forecast compatible; toggle off | weather-year pin regenerates series; `reliability_floor` flag arms engine; no-op when no pinned weather | ✅ |

The **structure is exactly what the research recommends.** Nothing structural needs
to change.

### 2.2 The one substantive divergence — floor MAGNITUDE source

`scripts/derive_reliability_coeffs.py` computes (lines ~346, 360):

```
min_stable_pct = grp["must_run_pct"].mean() / 100.0      # = bin Pct_Must_Run
floor_pct      = commit_frac * min_stable_pct
```

`Pct_Must_Run` is the **offer-curve must-run tranche share** — the slice of a
plant's capacity that bids as always-on in the CAMPD binning. For **merchant**
thermal it is **0** (no market must-run obligation). Result, from
`reliability-floor-coefficients.md`:

- **Only 3 of 143 limbs ship `enabled=True`** — all three are **CHP** (CC_CHP,
  ST_CHP), which survive *only* because cogeneration carries a thermal-host must-run
  tranche (Pct_Must_Run ≈ 0.4–0.9).
- **Zero ST_GAS, zero CT_PEAKER, zero COAL limbs are enabled in any ISO** — i.e.
  the entire priority fleet the mechanism was built for floors at **0**, even where
  the temperature response is unambiguously real (e.g. NYC ST_GAS ρ=0.63 n=343
  commit_frac=0.97; Long Island ST_GAS ρ=0.66; many ERCOT/MISO ST_GAS ρ 0.4–0.68).
- The CAISO review notes already document this and frame `min_stable_pct = 0` as
  "the correct #9/#11 outcome (no must-run tranche → no floor)."

**Why that framing is the wrong call here.** It conflates two distinct physical
quantities:

| Concept | What it is | Value for merchant steam/CT |
|---|---|---|
| **`Pct_Must_Run`** (what code uses) | offer-curve tranche that bids always-on *economically* | **0** (merchant ≠ must-offer) |
| **Min-stable-if-committed** (Pmin/Pmax) | turbine floor once a unit is *physically turned on* | **~12% steam / ~38% CT / ~52% CC** |

The whole point of the temperature gate is that on an extreme day the ISO
**reliability-commits** these merchant units (RUC / Cold-Weather-Alert CT
mobilization — §1.3, §1.4), *despite* their having no market must-run obligation.
Once committed they sit at their **physical Pmin**, not at 0. Sourcing the floor
from `Pct_Must_Run` therefore floors *only the units that were already must-run
anyway* (CHP) and adds nothing for the classes that are idle on mild days and
reliability-committed on extreme days — precisely where the mechanism is supposed
to bite.

Note coal: it carries a real take-or-pay must-run tranche, so its `min_stable_pct`
is non-zero (~0.25–0.35) — but its floor still ships OFF because the floor sits
*below* coal's mild-day baseline CF (~0.5–0.6); coal is already always-on, so the
floor doesn't bind. That is fine. The binding value of the mechanism is for the
**peaking/intermediate classes**, which is exactly what the `Pct_Must_Run` sourcing
zeroes out.

### 2.3 Threshold divergences (secondary)

- Thresholds ship as **flat priors** — `hot_tmax = 25 °C (77 °F)`, `cold_tmin =
  0 °C (32 °F)` — uniform across every zone, not derived per-zone.
- Cold `0 °C (32 °F)` is **much warmer** than PJM's documented Cold-Weather-Alert
  anchor of **10 °F (−12 °C)** / extreme **−5 °F (−20.5 °C)** — so the cold gate, if
  it ever floored anything, would trigger on far more days than the operational
  trigger justifies. For the PJM footprint, −12 °C is the citable value.
- Hot `25 °C` is a reasonable prior but is **not** the per-zone design-day /
  percentile the research recommends (and which is the only defensible route since
  no ISO hot number exists). Acceptable as a placeholder; upgrade to a per-zone
  95th–99th-pct tmax for a defensible forward rule.

---

## 3. Decided fix — floor off *min-run-if-committed*, gated on by temperature

**Decision (user, 2026-06-29):** the floor that the temperature gate turns on must
be the **min-run-if-committed floor (physical Pmin/Pmax), not the must-run-tranche
floor.**

```
floor_pct(zone, class) = commit_frac(zone, class)  ×  min_stable_pct_PHYSICAL(class)
```

- **`min_stable_pct_PHYSICAL(class)`** — NEW: a per-class physical constant from
  §1.1 (ST_GAS 0.12, CT_PEAKER 0.38, CC_REGULAR 0.52, COAL 0.40, oil 0.12), cited to
  NREL WWSIS-2 Table 7 in `constants.py`. **Replaces** `Pct_Must_Run/100` as the
  magnitude source. PHYSICAL / forward-reproducible.
- **`commit_frac`** — KEEP as is: the structural share of class capacity *online on
  flagged days* (CAMPD `grossLoad > 0` count, not an energy/CF ceiling). It
  regenerates for a forward year and responds to weather — admissible #9/#11. This
  is what makes the floor a *commitment* response to temperature.
- **Temperature gate** — KEEP: `tmax > hot_tmax_c` / `tmin < cold_tmin_c` does the
  committing (RUC analogue). Upgrade thresholds per §2.3 when convenient.

Both factors stay forward-reproducible, so this **does not** violate #9/#11 — it
*improves* physical fidelity (it models "reliability-commit, then enforce P ≥ Pmin,"
which is how real UC behaves). It is not a backcast fit: neither `commit_frac` nor
the NREL Pmin is tuned to the price/volume residual.

### 3.1 Watch-item: re-validate the enable gate under the corrected magnitude

The gate is `enabled ⇔ ρ≥0.3 AND n≥30 AND floor_pct > baseline`, where `baseline`
= mild-day CF. With the corrected magnitude, some real-signal steam limbs may still
fail `floor_pct > baseline` because it compares an **instantaneous floor** (Pmin ×
commit_frac) against a **daily energy average** (mild-day CF) — not a like-for-like
test. The next session should decide whether the third gate clause should instead
compare the flagged-day `commit_frac` against the **mild-day commit/online share**
(like-for-like commitment), and enable a limb where the *commitment* (not the CF)
rises with temperature. Keep the ρ/n significance gates; ship genuinely weak limbs
OFF (never invent a limb to plug a residual).

---

## 4. Fix prompt-pack (for the next session)

Self-contained, toggleable, backcast+forecast compatible. Each prompt is one
session-sized unit; run in order.

### Prompt A — Physical min-stable constants

```
In src/market_sim/config/constants.py add a cited per-class physical
minimum-stable-level table (Pmin/Pmax of a COMMITTED unit), NREL WWSIS-2
(NREL/TP-5500-55588) Table 7:

  MIN_STABLE_PCT_PHYSICAL = {
    "ST_GAS": 0.12, "ST_CHP": 0.12,        # gas steam (older units high end)
    "CT_PEAKER": 0.38, "CT_CHP": 0.38,     # simple-cycle CT
    "CC_REGULAR": 0.52, "CC_CHP": 0.52,    # combined cycle (least flexible)
    "COAL": 0.40,                          # subcritical/supercritical steam
    "oil": 0.12,                           # oil/oil-steam (steam physics)
  }  # source: NREL WWSIS-2 Table 7; PHYSICAL, forward-reproducible, NOT backcast-fit

Add a citation comment in house style (see HEAT_RATE_BINS). Do not tune these.
```

### Prompt B — Re-point the derivation at the physical floor

```
In scripts/derive_reliability_coeffs.py replace the min_stable_pct source:
  - was: min_stable_pct = grp["must_run_pct"].mean()/100   # offer-curve must-run share
  - now: min_stable_pct = MIN_STABLE_PCT_PHYSICAL[plant_class]  # physical Pmin/Pmax
Keep commit_frac exactly as is (CAMPD online-share on flagged days — structural).
Keep floor_pct = commit_frac * min_stable_pct.
Re-run `python scripts/derive_reliability_coeffs.py --iso ALL`; regenerate
reliability_floor_coeffs_<ISO>.csv and docs/multi-iso/reliability-floor-coefficients.md.
Confirm ST_GAS / CT_PEAKER limbs now carry non-zero floor_pct where commit_frac is high.
```

### Prompt C — Re-validate the enable gate (see §3.1)

```
Review the enable rule (rho>=0.3, n>=30, floor_pct>baseline). The third clause
compares an instantaneous floor to mild-day CF (not like-for-like). Change it to
gate on whether flagged-day commit_frac exceeds mild-day online/commit share, OR
justify keeping the CF comparison. Keep rho/n significance gates. Weak limbs ship
enabled=False and stay visible in the report. Report how many ST_GAS/CT limbs flip
to enabled and why each one is physically justified.
```

### Prompt D — Thresholds (physical anchors, not flat priors)

```
Upgrade thresholds from the flat 25C/0C priors:
  - COLD: anchor PJM zones to the Cold Weather Alert -12C (10F), extreme -20.5C
    (-5F) for the CT mobilization tier (PJM Manual 13). Non-PJM zones: per-zone
    1st-percentile tmin / design heating day from the zone weather series.
  - HOT: per-zone 95th-99th-percentile tmax (or TMY design cooling day). There is
    NO ISO-published hot trigger; do NOT pick the hot tmax to improve MAE.
Write thresholds into reliability_floor_coeffs_<ISO>.csv with a comment citing the
operational criterion per limb. Document the per-zone percentile method.
```

### Prompt E — Re-solve, dashboard, docs

```
Re-solve ALL backcast years in one bundle per ISO (CAISO/PJM/NEISO/NYISO/MISO
--year 2023 2024 2025; ERCOT full span), independent invocations concurrently
(cap ~2 for per-plant ISOs). Register each on the dashboard via calibration-report
+ build_manifest, commit per-run bundles same session (CLAUDE.md #12/#13). Track
MAE before/after but do NOT revert a structurally-correct floor because the residual
worsened (#1/#11) — fix the real root cause. Then /sync-docs.
```

---

## 5. Verified source list

PJM Manual 13 (Rev 97) & Manual 15 (Rev 47); NREL WWSIS-2 (TP-5500-55588 / 56217,
Table 7); EPA MATS Startup TSD; EIA Today-in-Energy id=45956; ISO-NE Operational
Fuel-Security Analysis (2018), Cold Weather Alerts, CELT 2026 methodology, Winter
Energy Security Initiatives; NYISO Natural Gas Constraints (ICAPWG 2023); NERC
gas-electric coordination guideline & EOP-012; FERC/NERC Jan-2025 arctic & Winter
Storm Elliott / Feb-2021 reports.

**Refuted / do-not-use:** PJM ">90 °F Hot Weather Alert" number (0-3); "HDD > 55 =
gas-constrained day" (0-3); firm/interruptible as a clean per-unit availability
switch (1-2); 48-h cold-start generalized to all CTs (1-2).
