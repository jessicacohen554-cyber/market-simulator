# FINDING — caiso-147 `measured_chp_heat_rates` for CAISO

**Lever:** mechanism-matrix §5.2 CAISO lever-queue **item 7**,
`measured_chp_heat_rates` (cells `UUUKUU`; `K` in MISO at miso-99, CAISO `U`).
**Pre-registration:** `PREREG-caiso147-chp-heat-rates-2026-07-31.md`, committed
and pushed at `b1b5e5f` **before either arm solved**.

**Base keeper:** `2026-07-31-caiso146-ct-heat-rates` (CALIBRATED-WITH-CAVEATS,
0 FAILs, 2 ledgered non-protective caveats, protective 0/1). CAISO holds **no**
rule-22 calibration-complete marker; this session solved **2023 2024 2025 only**
and wrote no marker.

Rule 25 `[R-ISO-SCOPE]`: MISO's `K` transfers nothing. Every number below is
measured on CAISO's own fleet from CAISO's own data.

---

## §A — the mechanism, and what it replaces **in CAISO specifically**

The measured rate is eGRID's own published CHP heat-input allocation added back
on the same net denominator:

```
heat_rate = (PLHTIAN + CHPCHTI) / PLNGENAN
```

`PLHTIAN` is heat input allocated to electricity — the incumbent
`PLHTRT = PLHTIAN / PLNGENAN` is exactly that over the same denominator — and
`CHPCHTI` is the useful-thermal allocation eGRID removed. `PLNGENAN` is already
**net** generation, so **no gross-to-net factor is involved**, which is why this
route works where the CEMS route was blocked (`FINDING-miso98` §6.1). Zero
fitted parameters (rule 24 `[R-REGISTRY]`).

**In CAISO the delta is not the one MISO measured.** CAISO is one of the two
ISOs in `fleet.arrays.CHP_STEAM_CREDIT_HR_CORRECTION_ISOS` (CAISO, PJM), so a
covered CAISO plant's incumbent is not eGRID's credited rate — it is that rate
times a **hand factor**: `x1.8` for a CT_CHP under 8.0 MMBtu/MWh,
`max(x1.15, 6.3)` for a CC_CHP under 6.0. The swap here is therefore **hand
factor → published measurement**, a rule-21/24 win (an off-registry hand number
retired for a citable one) on top of the rule-14 accuracy win.

Plants the measurement does not reach **keep the hand factor untouched**
(`apply_measured_chp_heat_rates` returns a `skip_ids` set that
`_correct_chp_steam_credit_hr` honours, rule 19 `[R-ONE-MECH]`). This mechanism
does not remove the hand factor from CAISO; it supersedes it only where a
published measurement covers.

---

## §B — the derive was blinded by the hand factor, and the fix (no LP)

**The shipped derive gave CAISO 14 `ok` rows / 1,117 MW, with
`basis_mismatch = 65`.** That is not a data wall — it is a gate misfiring, and
the diagnosis is `scripts/probes/_caiso147_chp_basis_gate.py`.

`_flag`'s `_BASIS_TOL` check asks *"is the incumbent rate this eGRID row, or a
boundary repair / `HEAT_RATE_BINS` fallback?"* and compared eGRID's **credited**
rate against the **shipped** model rate. In a hand-factor ISO the shipped rate
*is* the credited rate times 1.8 or 1.15, so **every hand-corrected plant reads
as a mismatch.** Measured ratio of shipped-to-credited across the excluded rows:

| class | n | median ratio | matches |
|---|---|---|---|
| CT_CHP | 56 | **1.800** | `CAISO_EOR_TOPPING_FACTOR` exactly |
| CC_CHP | 9 | **1.150** | `CAISO_CHP_CC_STEAM_CREDIT_FACTOR` exactly |

Loading the fleet twice — as shipped, and with the hand factor neutralised —
partitions the exclusions exactly:

> **59 of the 65 `basis_mismatch` rows — 3,089 of 3,186 MW — were excluded by
> the hand factor alone.** The remaining **6 rows / 96.5 MW** are the genuine
> boundary-repair / bin-fallback mismatches the gate was built to catch (Fresno
> Cogen, SDSU, UC Santa Cruz, CSUF Trigeneration, Broadridge, Sierra Nevada
> Brewing).

So the gate was excluding **precisely the population the mechanism exists to
fix**, leaving only the 14 plants the hand factor never touched. The artifact
would have been a swap applied everywhere *except* where caiso-128 §3 says the
error is.

**The fix.** Compare the credited rate against the incumbent **at the seam where
the swap actually happens** — after the eGRID join and the boundary repairs,
before the hand factor. That is exactly what `apply_measured_chp_heat_rates`
overwrites, since it runs first and hands the hand factor its `skip_ids`.
Implemented as `basis_heat_rates()` in the derive plus a default-`True`
`apply_chp_steam_credit_correction` kwarg on `load_fleet_from_csv` (the model
always leaves it `True`; only the derive passes `False`, and the binned-fleet
side cache is left untouched in that mode so the committed cache always reflects
the fleet the model prices with).

**Governance of the fix:**

- **Zero fitted parameters.** It introduces no number. `_BASIS_TOL`,
  `_MAX_THERMAL_SHARE` and the physical bands are untouched.
- **Not rule-23 `[R-FROZEN-DERIVE]`.** This is CAISO's *first* derive; the
  defect was found by code inspection and a no-LP probe **before any solve
  existed**, so no residual was visible and none could have been fitted to.
- **Not rule-25 and not on the caiso-146 DO-NOT-REDO list.** It is ISO-generic
  (see through the hand factor wherever it exists), not a CAISO-scoped
  multiplier, band or exclusion.
- **The gate keeps its discriminating power** — the 6 genuine mismatches still
  fail it, and every physics gate still applies downstream. The exclusion count
  did not fall to zero; it moved to the gate that should own it
  (`not_unfired_topping` 1 → 44, because those rows previously short-circuited
  at `basis_mismatch` before the physics check could see them).
- **MISO verified untouched.** No hand factor there, so `basis == model` on
  every MISO row; the re-derived MISO artifact is identical on **every applied
  value** (only the deliberately-edited provenance string differs) and its
  applied population is still **6,732 MW**, exactly miso-99's committed figure.

**This is a latent defect in PJM too** — PJM is the other hand-factor ISO and
has never derived this artifact. Anyone taking `measured_chp_heat_rates` into
PJM gets the fixed gate automatically; that is noted, not acted on here
(rule 25).

---

## §C — the artifact (STEP 1, no LP)

`data/raw/_processed-legacy/chp_power_only_heat_rates_CAISO.csv`, eGRID2023
(`PLNT23` — the vintage the model's own `heat_rate` is joined from, so the delta
is "eGRID's CHP allocation, undone" with basis, source, vintage and denominator
all held fixed). 92 (plant, class) rows, 4,668.6 MW of CHP.

| flag | rows | MW | meaning |
|---|---|---|---|
| `ok` (applied) | **30** | **2,371.8** | measurement applies |
| `not_unfired_topping` | 44 | 1,914.4 | `thermal_share > 0.50` — boiler-first, excluded on physics |
| `basis_mismatch` | 6 | 96.5 | genuine boundary repair / bin fallback |
| `above_physical_band` | 3 | 251.1 | corrected rate outside the class band |
| `no_chp_credit` | 3 | 19.4 | eGRID applied no credit — nothing to add back |
| `no_egrid_row` | 6 | 15.4 | plant absent from the eGRID vintage |

**Coverage — energy reach is what matters, not capacity:**

| class | rows | capacity | **metered CAMPD energy (2023)** |
|---|---|---|---|
| CC_CHP | 11/21 | 1,819/2,707 MW (67.2 %) | **7.490/7.490 TWh — 100.0 %** |
| CT_CHP | 19/71 | 553/1,962 MW (28.2 %) | 0.146/0.413 TWh — 35.4 % |

CC_CHP — the material class at 3.7–4.3 % of generation — is covered on
**100.0 %** of its own metered energy; the uncovered plants sit below the
Part-75 boundary and meter nothing.

**Validation.** `PLHTIAN + CHPCHTI` reproduces independently metered CAMPD
annual heat input within 1 % on **13 of 13** covered plants, median ratio
**1.00000**. MISO's was 19/22. **CAISO's validation is better**, so the charter's
stop-condition (validation materially worse than miso-99's) was not triggered.

**Direction — two-sided, and opposite between the classes** (cap-weighted,
shipped → measured):

| class | shipped | measured | delta | cheaper | dearer |
|---|---|---|---|---|---|
| CC_CHP | 6.779 | 8.108 | **+1.330 (+19.6 %)** | 1 row / 525 MW | 10 rows / 1,294 MW |
| CT_CHP | 11.935 | 10.196 | **−1.739 (−14.6 %)** | 10 rows / 389 MW | 9 rows / 164 MW |

CC_CHP was **under**-costed and CT_CHP **over**-costed. This is caiso-128 §3's
"a universal hand factor is wrong in both directions at once" measured directly
on CAISO's own fleet, and it is the substantive case for a published per-plant
measurement over a single ISO-keyed factor. 28 of 30 rows move > 0.5 MMBtu/MWh.

**Stated limitations (pre-registered, not discovered after the fact):**

- **CT_CHP coverage is thin and adversely selected** — 35.4 % of metered energy,
  and the covered plants are the *less* steam-credited ones (cap-weighted
  credited 7.167 covered vs 6.377 excluded; thermal share 0.288 vs 0.526).
  CT_CHP is 0.72–0.74 % of model generation so this is immaterial to the
  determination either way, but it is **not** a clean identification and is not
  claimed as one.
- **The `not_unfired_topping` exclusion is large and correct** — 44 rows /
  1,914 MW (41 % of CHP capacity), median `thermal_share` 0.598 against the 0.50
  EPA-envelope ceiling, and the power-only rate those plants would otherwise
  take has median 14.52 and max **58.4** MMBtu/MWh: nonsense for an offer rate,
  exactly the boiler-first case the gate exists to reject. They keep the
  existing eGRID → hand-factor chain.

---

## §D — the gate framing, corrected against the scorer's source

The session charter stated that CC_CHP, being ~4 % of load and so above the 2 %
materiality floor, "IS gated" by C7/C8 unlike caiso-146's CT_PEAKER. **That is
not what the scorer implements**, and the correction matters for how this run is
read:

- **C7 / D-1:** `legitimacy_diagnostics.D1_GATED_CLASSES` =
  `CT_PEAKER, ST_GAS, COAL*`. CHP is absent; the keeper's own rows read
  `"gated": false`.
- **C8 / D-2:** `D2_EXEMPT_CLASSES = ("CC_CHP", "CT_CHP", "ST_CHP", "nuclear")`.

Both carry the same rationale in source: *"host-steam-pinned duty."* The
exemption is **by explicit class list, not by materiality** — so CC_CHP's
0.44–0.47 `chp_steam` forced share is not gated by C8 no matter how large the
class is, and the materiality floor never comes into it.

Consequently this finding **reports CHP's D-1/D-2 numbers as diagnostics and
never quotes them as a passed gate**, and places the binding protective gates on
the classes that absorb the displaced energy — CT_PEAKER (C7-gated, C8
peaker-capped at 0.15), ST_GAS and COAL.

*(Noted for a future session, not acted on here: CT_CHP's 2025 `profile_r` is
**0.393** in the incumbent keeper — far below the 0.80 threshold — and is
ungated. A latent shape limitation this session inherits and does not create.)*
