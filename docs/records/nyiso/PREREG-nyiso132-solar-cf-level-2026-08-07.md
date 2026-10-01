# PREREG nyiso-132 — the NYISO solar CF LEVEL: the four ex-ante items, SETTLED

**Registered 2026-08-07, session nyiso-132.** The arming pre-registration for
lever-queue item 2, discharging §4 of
`PREREG-nyiso130-solar-cf-level-2026-08-06.md` ("What must be pre-registered
BEFORE it is armed"), which was handed forward deliberately unfinished.

**NO SOLVE IS SPENT IN THIS DOCUMENT.** Everything below is measured from the
committed registry, the committed Gold Book extraction and the model's own
loader path at HEAD, before any arm exists. Rule 13 `[R-MEASURED]`: the price
residual is not consulted at any point in §1–§4.

**Session numbering.** `nyiso-131` is consumed by the run id
`2026-08-07-nyiso-131-taxgs-arm` (the D-27 promotion). This session is
**nyiso-132**.

**Baseline correction, material to the A/B.** The nyiso-130 prereg and the
session charter both name the keeper as `2026-08-06-nyiso-128-solar-basis`.
That is **stale**: owner decision D-27 (sitting Addendum AA.4) promoted
**`2026-08-07-nyiso-131-taxgs-arm`** on 2026-08-07, and it is the keeper on
`main`. The recipe is unchanged (693/693 shared `scenario_config` fields
identical, the 5 arm-only fields all default `False`) and C3a is unmoved, so
the identification below is unaffected — but **the control arm must be taken at
`nyiso-131-taxgs-arm`, not at `nyiso-128-solar-basis`.**

---

## 1. Item 1 — WHICH QUANTITY MOVES. Population identity, SHOWN not assumed

The prereg required proof that `RENEWABLE_AVG_CF["NYISO"]["solar"]` (an
**ISO-wide** normalization) and the **registered market fleet** (on which
0.1955 was measured) are the same population once
`nyiso_solar_market_generator_basis` is armed. Traced through the real loader
path, `data/renewables.py::load_renewable_profiles`:

1. **The capacity basis is swapped to the registry.** For
   `fuel == "solar" and iso == "NYISO"` with the flag set, `monthly` is
   replaced by `load_market_solar_monthly(...)` — NYISO's own Table III-2a
   registry. Everything downstream (`installed_mw`, the zone split, the vintage
   ramp) follows that array.
2. **The CF normalization is applied to that same array.** For NYISO solar the
   measured-profile branch does **not** fire:
   `_eia_hourly_cf_profile` returns `None` because EIA-930 NYIS reports SUN as
   identically zero — its own docstring names the case
   (*"all-zero signals a BA reporting gap ... e.g., EIA-930 NYIS does not
   separately report solar"*) — and NYISO is **not** in
   `_UNCURTAILED_FALLBACK_ISOS` (`{ERCOT, CAISO, MISO}`). So control falls
   through to `_eia930_cf("solar")`, whose last line is
   `derive_cf_profile(values, RENEWABLE_AVG_CF[iso][fuel])`.

**Therefore the constant is LIVE on the NYISO backcast solar path** (the lever
is not inert), and it normalizes **the registered fleet's own capacity array**.
The two populations are the same object. This is precisely why the lever only
became well-posed after the basis arm landed, as nyiso-130 anticipated.

Measured capacity, registered basis (`load_market_solar_monthly`, system total):

| year | first month | year-end | mean monthly | mean / year-end |
|---|---:|---:|---:|---:|
| 2023 | 114.4 MW | 174.4 MW | 161.1 MW | 0.9235 |
| 2024 | 174.4 MW | 573.4 MW | 389.9 MW | 0.6800 |
| **2025** | **573.4 MW** | **573.4 MW** | **573.4 MW** | **1.0000** |

2025 is flat — the 15 units of the 2026 Gold Book, no PV market generator added
— which matters in §2 and §3.

## 2. Item 2 — THE 0.15 → 0.133 GAP. Its stated cause is FALSIFIED; it is a reporting artifact, not a defect

The nyiso-130 prereg asserted *"clipping and the donor profile eat ~11 % before
any re-level"* and required the gap be enumerated under rule 19
`[R-ONE-MECH]` before choosing between re-levelling the constant and repairing
the realization. **Enumerated, and the stated cause does not survive
measurement.** Running the exact path of §1 at HEAD:

| year | shape source | `values.sum()` | **hourly MEAN cf** | hours clipped at 1.0 |
|---|---|---:|---:|---:|
| 2023 | DONOR-repaired (NEISO) | 1.000000 | **0.150000** | **0** |
| 2024 | DONOR-repaired (NEISO) | 1.000000 | **0.150000** | **0** |
| 2025 | DONOR-repaired (NEISO) | 1.000000 | **0.150000** | **0** |

- **Clipping is not a cause: ZERO hours clip in any year.**
- **The donor profile is not a level cause.** The nyiso-75 NEISO donor repair
  does supply the *shape* (NYIS SUN being identically zero), but
  `derive_cf_profile` renormalizes to the target, so the level is `0.150000`
  exactly. The distribution is proper (`values.sum() = 1.000000`).
- `renewable_cf_adjustment` is `1.0` (dataclass default, unset in the keeper).

**The whole gap is the DENOMINATOR CONVENTION.** Energy accrues against the
*monthly* capacity ramp while `installed_mw` is *year-end* capacity
(`monthly[:, -1].sum()`), so any statistic of the form
`energy / (year-end capacity × 8760)` under-reads a growing fleet:

| year | basis | realized CF vs **YEAR-END** | realized CF vs **MEAN-monthly** |
|---|---|---:|---:|
| 2023 | EIA-860 | 0.1345 | 0.1493 |
| 2024 | EIA-860 | 0.1176 | 0.1495 |
| 2025 | EIA-860 | 0.1385 | 0.1496 |
| 2023 | REGISTERED | 0.1398 | 0.1514 |
| 2024 | REGISTERED | 0.1026 | 0.1509 |
| **2025** | **REGISTERED** | **0.1500** | **0.1500** |

The EIA-860 year-end column averages **0.1302** — that is the "realized ~0.133"
of the record. Against the mean-monthly denominator every year reads **0.149–0.150**,
i.e. the constant, as designed. And on the **registered** basis in the
**flat** year the two denominators coincide and the model realizes **0.1500
exactly**.

**Conclusion (rule 19).** There is **no second defect and nothing to repair in
the realization**. The model's solar level is exactly what the constant says it
is; the "gap" is an artifact of the denominator used to *report* it, and it
vanishes identically in the mature-fleet year on the basis this keeper already
arms. So the choice the nyiso-130 prereg posed — *re-level the constant* vs
*repair the realization* — resolves to the first, and there is exactly **one**
mechanism in play.

**This is the trap the item existed to catch, and it is quantified.** The lever
must be sized **off the constant (0.15)**, never off the reported 0.133:

| sizing basis | factor | 2025 energy delivered | vs published 981.8 GWh |
|---|---:|---:|---:|
| **constant 0.15 → 0.1955 (correct)** | **1.3033** | **977.5 GWh** | **−0.4 %** |
| "realized 0.133" → 0.1955 (the trap) | 1.4699 | 1,102.4 GWh | **+12.3 %** |

(2025 armed-keeper delivery of 0.75 TWh is the nyiso-130 prereg §1 figure.)
Sizing off 0.133 would over-shoot the fleet's own published output by 12 %.

## 3. Item 3 — MATURE-FLEET YEAR ONLY. 2025, and the exclusion is the identification

Measured fleet CF is **0.1629 / 0.1468 / 0.1955** (nyiso-130 §3) — a 33 % swing,
not a stable number. 2023 and 2024 are **excluded as
commissioning-contaminated, and that exclusion is the identification, not a
preference**: the monthly step counts a plant as fully present from its
in-service month while a commissioning plant is not yet at full output, and
2024 is the heavy build year (registered capacity 174.4 → 573.4 MW, mean/year-end
**0.6800** in §1) which reads the *lowest* CF. **They are not averaged in.**

**2025 added no PV market generator at all** (the 2026 Gold Book carries the
same 15 units; §1 shows the capacity array flat at 573.4 MW in every month), so
it is the only clean read of a mature fleet: **0.1955**.

Independent identity check, computed here and not taken from the record:
`573.4 MW × 8,760 h × 0.1955 = 982.0 GWh` against the published **981.8 GWh** —
agreement to **0.02 %**. The target CF is the registry's own published energy
over its own published capacity; it carries **zero free parameters**, it
regenerates from each Gold Book vintage, and it responds to changed conditions
(fleet mix, new entries). Rule 13 `[R-MEASURED]` admissible as an INPUT.

## 4. Item 4 — DIRECTION, ADVERSE CASE AND INTERACTION, stated before the solve

**Direction.** Raising the constant adds zero-marginal-cost afternoon energy:
**C3a moves DOWN and the C3c tail moves DOWN.** Both are the same direction as
the nyiso-130 Priority-1 arm that was rejected on kill gate K6.

**Magnitude bound, ex ante.** The re-level is +30.3 % on a fleet the keeper
currently runs at 0.75 TWh in 2025 — i.e. **+0.23 TWh of 2025 solar**, against
NYISO annual load of ~150 TWh. That is ~0.15 % of energy, so the *level* effect
is small; the risk is concentrated in the afternoon hours where it displaces the
marginal unit.

**Adverse case, pre-registered (these are the numbers that decide it):**

- **C3a** is `+8.8 / +0.8 / −3.2 %` against a ±10 % band. 2024 and 2025 move
  toward the **−10 %** edge. **Adverse case: C3a-2025 crosses −10 %.** 2023 has
  the most headroom and should improve.
- **C3c** already **over**-produces in 2023 (22 h vs a measured 10 h) so a fall
  there is *favourable*; but 2025 sits only **3 h above its band floor of 21**.
  **Adverse case: C3c-2025 falls through its floor**, converting a passing year
  into a miss in the opposite direction. **A falling tail is NOT automatically
  good** and will not be reported as such.
- **C1/C2** solar volume should move *toward* the published figure (§2 table,
  −0.4 %); a move away from it falsifies the construction.

**Interaction — the two levers are NOT independent and will not be scored as if
they were.** The Zone-K joint reconciliation (the chartered successor to the
rejected `nyiso_li_tsl_n11_security`) pushes the same gate the same way. It is
**not** armed here and must not be co-armed on these arms: rule 19
`[R-ONE-MECH]`, and nyiso-130 §5's reasoning applies unchanged.

**Rule 25 `[R-ISO-SCOPE]`.** NEISO carries the identical Tier-3 `0.15` with the
identical `needs-citation` (`constants.py`). It is **NOT** covered by this
identification and must derive its own from its own market's data. No NEISO file
is touched.

## 5. The lever, as it will be armed

`RENEWABLE_AVG_CF["NYISO"]["solar"]: 0.15 → 0.1955`, replacing a self-declared
**Tier-3 approximation** carrying *"needs-citation: verify against EIA-923 ISO
totals before quoting a forecast"* with the registered fleet's own measured
mature-year CF. **Zero free parameters** — registry energy ÷ registry capacity
is an identity, not a chosen value. Expected DOF ledger effect: an entry moves
from *approximation* to *measured*, `n_residual` unchanged.

Open construction question to settle in the arming commit, flagged now rather
than after seeing a number: whether the change lands as a bare constant edit
(which also moves NYISO **forecast** runs, since `RENEWABLE_AVG_CF` is the
forecast normalization) or behind its own gate. It is a rule-14 accuracy repair,
so the default posture is that it should move both lanes — but the forecast
blast radius is stated before it is chosen, not discovered afterwards.

## 6. Status

**IDENTIFIED, SETTLED EX ANTE, NOT ARMED.** No `constants.py` edit, no solve, no
registration, no matrix cell moved by this document. 2023–2025 only; the holdout
spend freeze is ACTIVE and untouched.

Reproduced from: `data/renewables.py` at HEAD (`_eia_hourly_cf_profile`,
`_eia930_cf`, `derive_cf_profile`, `_eia860_monthly_capacity`,
`load_market_solar_monthly`), `results/calibration/_nyiso130_solar_gwh_reconciliation.json`,
`PREREG-nyiso130-solar-cf-level-2026-08-06.md`.
