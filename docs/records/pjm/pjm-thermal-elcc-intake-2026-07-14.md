# PJM thermal ELCC class-rating intake (N-4 / R3) — 2026-07-14

**Session.** N-4 of the forecast-driver capacity-revenue audit lane. Executes
**R3** of the accreditation-basis adjudication memo
(`docs/handoffs/accreditation-basis-memo-2026-07-12.md` §4.3): intake the PJM
**thermal** ELCC class ratings that the on-disk P-0B `capacity-market-elcc`
datatype was missing (it held only intermittent/storage/DR rows — 135 rows,
thermal absent). Data intake only — **no LP solves, no model wiring, no
`ScenarioConfig` flag**. The supply-basis extension itself (step 3 of the
memo's migration path) is N-5's job; this session gives it real numbers.

**Rule 13 status.** These are **published market-design inputs** (PJM's own
Accredited-UCAP class ratings, filed under FERC Docket ER24-99 / the 2025/26
CIFP reform), entering as a per-class accreditation factor that regenerates
for any forward delivery year and responds to modeled fleet/penetration
conditions. They are **never fit targets** — the intake adds no adder, haircut,
or residual-tuned value.

---

## 1. What was intaken

79 PJM thermal rows appended to `data/raw/capacity-market/elcc/pjm/pjm.csv`
(same schema, same file, same three vintage tranches as the existing
renewable/storage/DR rows). PJM does **not** publish a separate thermal ELCC
study — thermal is rated in the *same* already-cited class-ratings documents,
so no new source URL was introduced.

### Tranche 1 — Official / final **2026/2027** BRA (binding)

Source: `2026-27-bra-elcc-class-ratings.pdf` p.1 (rating); installed MW from
the 2025 RRS Table 5 (p.16-17).

| Class (canonical bucket) | ELCC % | Installed MW |
|---|---|---|
| Nuclear (`nuclear`) | 95 | 32,144 |
| Coal (`coal`) | 83 | 35,779 |
| Gas Combined Cycle (`gas_cc`) | 74 | *null — see note* |
| Gas Combustion Turbine (`gas_ct`) | 60 | 11,030 |
| Gas Combustion Turbine Dual Fuel (`gas_ct_dual_fuel`) | 78 | 13,158 |
| Diesel Utility (`diesel`) | 91 | 329 |
| Steam (`steam`) | 73 | 10,004 |

### Tranche 2 — Official / final **2027/2028** BRA (binding)

Source: 2025 RRS Table 24 (p.42-43, rating) & Table 5 (p.16-17, installed MW).

| Class | ELCC % | Installed MW |
|---|---|---|
| Nuclear | 95 | 32,181 |
| Coal | 83 | 35,964 |
| Gas Combined Cycle | 74 | *null — see note* |
| Gas Combustion Turbine | 61 | 10,970 |
| Gas Combustion Turbine Dual Fuel | 77 | 13,249 |
| Diesel Utility | 92 | 334 |
| Steam | 72 | 9,283 |
| Waste to Energy Steam (`waste_to_energy`) | 83 | 719 |
| Oil-Fired Combustion Turbine (`oil_ct`) | 80 | 2,852 |

### Tranche 3 — Preliminary **2026/27 → 2034/35** (ER24-99, non-binding, indicative)

Source: `preliminary-elcc-class-ratings-for-period-2026-2027-through-2034-2035.ashx`
p.1. `elcc_type = marginal`, `penetration_pct` null (delivery-year-indexed, not
a raw penetration %). This is the forward-regenerable trajectory (rule 13
forward story): 9 rows per class × 7 thermal classes = 63 rows.

| Class | 26/27 | 27/28 | 28/29 | 29/30 | 30/31 | 31/32 | 32/33 | 33/34 | 34/35 |
|---|---|---|---|---|---|---|---|---|---|
| Nuclear | 95 | 95 | 95 | 96 | 95 | 96 | 96 | 94 | 93 |
| Coal | 84 | 84 | 84 | 85 | 85 | 86 | 86 | 83 | 79 |
| Gas Combined Cycle | 79 | 80 | 81 | 83 | 83 | 85 | 85 | 84 | 82 |
| Gas Combustion Turbine | 61 | 63 | 66 | 68 | 70 | 71 | 74 | 76 | 78 |
| Gas Combustion Turbine Dual Fuel | 79 | 79 | 80 | 80 | 81 | 82 | 83 | 83 | 83 |
| Diesel Utility | 92 | 92 | 92 | 92 | 92 | 93 | 93 | 93 | 92 |
| Steam | 74 | 73 | 74 | 75 | 74 | 75 | 76 | 74 | 73 |

**Note — Gas Combined Cycle installed MW left null (never guessed, rule 13).**
RRS Table 5's Gas Combined Cycle row reports installed MW as *Single + Dual
Fuel combined* (57,664 MW for 2026/27), but PJM rates Single-Fuel CC and
Dual-Fuel CC separately and, for 2026/27, declined to issue a class rating for
Dual-Fuel CC at all (too few members post-attestation → resource-specific ELCC,
per the final ratings doc p.1 footnote). There is therefore no published
single-fuel-only CC installed-MW figure to pair with the 74% single-fuel-CC
rating, so `penetration_pct`/`penetration_unit` stay null for `gas_cc` in both
official tranches. The rating itself (74%) is published and is intaken.

**Note — Dec-2021 tranche has NO thermal rows (a real gap, not a miss).** The
existing renewable/storage rows include a third tranche from the superseded
December-2021 ELCC Report. That report **predates** the reform that extended
ELCC class ratings to thermal — reading the full document confirms it rates
only variable/storage/hydro/landfill classes, never nuclear/coal/gas. So the
thermal intake correctly has two tranches, not three.

---

## 2. MANUAL DOWNLOADS NEEDED

**None.** All three already-cited PJM source documents resolved through the
agent proxy on 2026-07-14 (HTTP 200, `application/pdf`), and every intaken value
was transcribed directly from them — no rating was guessed or interpolated:

| Document | URL | Result |
|---|---|---|
| 2026/27 BRA final class ratings | `https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/2026-27-bra-elcc-class-ratings.pdf` | 200, 128,730 B |
| 2025 PJM ELCC/RRS (Tables 5, 23, 24) | `https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/2025-pjm-elcc-rrs.pdf` | 200, 3,650,580 B |
| Preliminary ER24-99 ratings 26/27–34/35 | `https://www.pjm.com/-/media/DotCom/planning/res-adeq/elcc/preliminary-elcc-class-ratings-for-period-2026-2027-through-2034-2035.ashx` | 200, 92,063 B |

---

## 3. Restated memo §3.1 decomposition — real numbers, not indicative

The memo's §3.1 supply-side decomposition used **indicative** thermal ratings
because the rows were not yet intaken. Restating it against the **actual
intaken official/final 2026/2027 BRA class ratings** (the first binding
reform-era set), on the memo's own model ledger
(`evolution_2025.json`, thermal nameplate 182.9 GW: coal 46.4, gas-CC 63.5,
gas-CT 27.8, gas-ST 10.4, nuclear 28.6, oil 4.2, biomass 2.0):

| Restatement basis | Thermal accredited | Fleet avg | B2/ELCC overstate | Restated firm | Restated position |
|---|---|---|---|---|---|
| **Model B2** `pmax×(1−EFORd)` (reference) | 172.1 GW | 0.941 | — | 188.7 GW | **1.296** (measured) |
| **Official/final 26/27, plain CT 60%** | 142.2 GW | 0.778 | ×1.210 | 158.8 GW | **1.091** |
| **Official/final 26/27, CT single/dual blend 70%** | 144.9 GW | 0.792 | ×1.187 | 161.5 GW | **1.110** |
| *(memo's indicative, for reference)* | *145.2 GW* | *0.794* | *×1.185* | *161.8 GW* | *~1.11* |
| *Auction actual 2025/26* | — | — | — | — | **1.007** |

(Non-thermal firm 16.6 GW and implied 2025 requirement 145.6 GW held from the
memo; position = firm ÷ requirement.)

**The memo's conclusion holds with real numbers, and slightly strengthens.**
Restated thermal accredits **142–145 GW (avg 0.78–0.79)** vs the model's B2
172.1 GW (0.941) — an overstatement of **×1.19–1.21** (the memo said ×1.185).
Restated position lands **≈1.09–1.11** vs measured 1.296 and auction-actual
1.007, so the memo's split — **≈2/3 of the position excess is basis mismatch,
≈1/3 is real fleet/retirement error** — is confirmed against the published
ratings, not indicative ones.

### Two findings N-5 must carry forward

1. **The memo's indicative values were the *preliminary* numbers, not the
   binding ones.** The memo's §2/§3.1 indicative set (coal ~84, gas-CC ~79,
   gas-CT ~62) matches the **preliminary ER24-99** 2026/27 column, **not** the
   official/final ratings (coal 83, **gas-CC 74**, gas-CT 60). Gas-CC is the
   big mover: the binding rating is **74%, five points below** the indicative
   79%. N-5 step 3 should accredit binding delivery years off the
   **official/final** tranche and reserve the ER24-99 tranche for the forward
   trajectory (post-2027/28), never blend the two for the same year.

2. **The model's undifferentiated `gas_ct` class straddles PJM's single/dual
   CT split — a mapping decision, not a lookup.** PJM rates Gas Combustion
   Turbine at 60% and Gas Combustion Turbine Dual Fuel at 78%, and its CT fleet
   is **majority dual-fuel** (13.2 GW dual vs 11.0 GW single installed). The
   model's single `gas_ct` class (27.8 GW) has no dual-fuel flag, so N-5 must
   choose how it resolves: plain-CT 60% (conservative, memo-comparable → pos
   1.09) or an installed-MW-weighted single/dual blend ≈70% (fleet-
   representative → pos 1.11). The datatype carries **both** ratings as
   distinct rows (`gas_ct`, `gas_ct_dual_fuel`) so either mapping is available
   without re-intake; the choice belongs in the step-3 resolver, with the model
   fleet's own dual-fuel share if it can be recovered, else the PJM installed
   split as the documented default.

Neither finding changes the intake — both ratings and both tranches are on
disk. They scope the resolver N-5 writes.

---

## 4. Files changed (this session)

- `data/raw/capacity-market/elcc/pjm/pjm.csv` — +79 thermal rows.
- `data/raw/capacity-market/elcc/pjm/README.md`,
  `data/raw/capacity-market/elcc/README.md` — status + vocab updated for thermal.
- `data/dictionary/schema/capacity-market-elcc.schema.yaml` — `resource_class`
  vocab + description extended with the thermal buckets.
- `scripts/lib/capacity_market_elcc/__init__.py` — `RESOURCE_CLASSES` grows the
  thermal buckets; module docstring.
- `scripts/lib/capacity_market_elcc/pjm.py` — thermal native-label aliases.
- `scripts/render_data_dictionary.py` + `data/dictionary/data-dictionary.md` —
  narrative + rendered section refreshed (hermetic per-column render).
- `tests/test_curate_capacity_market_elcc.py` — `TestPjmThermalElccIntake`
  (loader-resolvability + schema round-trip against the real on-disk CSV,
  tmp `CLEAN_DIR`).

No model code, no `ScenarioConfig`, no solve, no dashboard artifact touched
(intake-only; the datatype is forecast-mode machinery not yet wired).

## 5. Handoff to N-5 (supply-basis extension, memo step 3)

- Grow `THERMAL_ACCREDITATION_BASIS_BY_ISO` with an `"elcc_class_rating"`
  basis for PJM; resolve per fuel class from `read_clean("capacity-market-elcc",
  iso="PJM")`, preferring the **official/final** tranche for binding years and
  the ER24-99 tranche for the forward path.
- Decide the `gas_ct` single/dual-fuel mapping (finding 2) in the resolver.
- Keep it one accreditation resolver for both the ledger and the payment seam
  (memo step 4, rule 19) — no second derate.
- Score any resulting verdict flip leave-one-year-out within 2023–2025 before
  promotion; the intake itself is forecast-only and touches no keeper.
