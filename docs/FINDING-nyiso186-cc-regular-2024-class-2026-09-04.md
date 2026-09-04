# FINDING — nyiso-186 (`cc-regular-2024-class` lane): the 2024 `CC_REGULAR` excess is CONCENTRATED at three combined cycles in every year, NO plant-level bar fires, the gas family is EXACT (the class is the within-family fill of the CT / steam holes), and ONE measured-data defect found on the inputs — Astoria Energy II priced at a class default because eGRID files both Astoria blocks under one ORISPL — is repaired by a generic identity rule and A/B-solved

**Session:** nyiso-186, `cc-regular-2024-class` lane
(`claude/nyiso-186-cc-regular-2024-b16yp7`), NYISO backcast-calibration track,
2026-09-04. **Solves run: TWO** — the same-HEAD control
(`results/calibration/nyiso186_control`, an INSTRUMENT: bit-identical to the
committed keeper in all three years, registers nothing) and the arm
(`results/calibration/nyiso186_astoria_identity`, §4).
**Keeper at entry: `2026-09-04-nyiso-185-family-hr`** — NOT-YET, target grade
5, fail set {C1-2024 `CC_REGULAR` +3.87 TWh / +3.18 pp, C3a-2025 −10.5 %
(owner-court, not touched), C3c}.
**Pre-registration:** `results/calibration/PREREG-nyiso186-cc-regular-2024-class.md`,
pushed at `3d9747aa` before the first per-plant measurement; its §7 addendum
(pushed at `d926bf48` before the artifact was re-derived) fixes the one A/B.
**Machine records:** `results/calibration/_nyiso186_cc_attribution.json`
(M1–M6, probe `scripts/probes/nyiso186_cc_attribution.py`); the arm bundle's
`calibration_attestation.json` (`scripts/gen_nyiso186_attestation.py`, every
premise computed), `metrics.json`, `legitimacy_diagnostics.json`.

---

## 1. The result in one paragraph

Attributed by plant on the keeper's own unit-hourly dispatch (the control
replay reproduces the committed keeper bit-identically — 0 of 52,560 hourly
zonal prices differ in every year — so its sidecars ARE the keeper's), the
`CC_REGULAR` excess is carried by **the same three plants in every year**:
Cricket Valley (57185, Capital-Hudson), Zeltmann / Poletti (56196, NYC) and
Astoria Energy II (57664, NYC) — **C3 = 0.875 / 0.745 / 0.853** of the
positive excess, CONCENTRATED on the pre-registered bar in all three. **None of
the plant-level hypotheses fires on its bar** at any of the three: their base
heat rates sit inside the class's rate-to-meter band, their phantom capacity
(where any) is not the energy being run, and their availability sits inside
the class's band. The bars were fixed before measurement and are reported as
read; §2.3 records why two of them are too loose to fire on anything. What the
measurement DOES establish is the mechanism: **the gas family is exact**
(model 67.80 TWh vs EIA-930 67.80 in 2024), so the class's +3.87 TWh is the
within-family fill of `CT_PEAKER` −1.66, `CT_CHP` −1.29 and `ST_GAS` −1.09 —
and it lands on the cheapest available NYC / Capital-Hudson combined cycles,
which the model loads harder when on (Zeltmann 0.96 vs a 0.68 meter) or keeps
on more hours (Cricket Valley 0.995 vs 0.878). That is the nyiso-175 CT-deficit
and nyiso-181 steam-deficit objects seen from the receiving end, not a CC
mechanism. Separately, M2 found on the INPUTS — never on a residual — that
**Astoria Energy II, a 650 MW NYC combined cycle, is priced at the `gas_cc`
f-class default 6.70** because eGRID files both Astoria Energy blocks under
ORISPL 55375 and 57664 has no eGRID row in any vintage, while eGRID's net
generation for 55375 equals EIA-923's (55375 + 57664) **to the MWh in all seven
vintages 2018–2024**. The committed identity derive's one-to-one predicate
cannot reach a two-into-one identity; it gains a MERGED-identity leg (same
tolerance, same overlap rule, same pooled rate rule, run over the whole
187-plant population — exactly one pair found), the artifact gains one row
(57664 → 7.3792), and the arm measures the consequence under the
pre-registered verdict rule (§4). License: rule 14, stated in PREREG §7.2
before the derive ran.

---

## 2. The attribution, as pre-registered and as measured (control = keeper)

### 2.1 M3 — concentration

| year | class model / EIA-923 (unit sidecar, TWh) | E⁺ | top-3 (TWh over own EIA-923) | C3 | verdict |
|---|---|---|---|---|---|
| 2023 | 33.666 / 33.012 | 3.759 | 57185 +1.244 · 56196 +1.109 · 57664 +0.937 | **0.875** | CONCENTRATED |
| **2024** | 38.175 / 34.060 | 4.715 | 57185 +1.838 · 56196 +0.868 · 57664 +0.805 | **0.745** | CONCENTRATED |
| 2025 (prelim. 923) | 36.784 / 28.562 | 6.173 | 57664 +2.648 · 56196 +1.397 · 57185 +1.223 | 0.853 | CONCENTRATED |

The cancellation on the other side, 2024: Valley 56940 −0.281, Bethpage 50292
−0.186, Astoria Energy I 55375 −0.092; in 2023 **Bethlehem 2539 −2.275** (§5.2).

### 2.2 M4 / M5 at the top-3, 2024 (bars verbatim; peers = every other `CC_REGULAR` plant with CF ≥ 0.20 and a qualifying CAMPD record)

| plant | `r` = base HR ÷ CAMPD running HR | band | H-A | `pmax`/p99.9 | dispatch vs deliverable (TWh) | H-B1 | `a_p` = avail ÷ online share | band | H-B2 |
|---|---|---|---|---|---|---|---|---|---|
| 57185 Cricket Valley | 7.013 ÷ 6.801 = **1.031** | [0.707, 1.412] | no | 1.198 | 6.00 < 8.44 | no | 0.695 ÷ 0.880 = **0.790** | [0.532, 2.816] | no |
| 56196 Zeltmann | 6.977 ÷ 6.736 = **1.036** | " | no | 0.891 | 4.55 < 5.56 | no | 0.833 ÷ 0.907 = **0.918** | " | no |
| 57664 Astoria Energy II | 6.700 ÷ 7.053 (facility meter) = 0.950 | " | no | — | — | — | — | — | UNTESTABLE (no own CAMPD record), as pre-declared |

Zeltmann's H-B1 **does** fire in 2023 and 2025 (`pmax`/p99.9 1.098 / 1.110,
dispatch 4.50 > 4.39 and 4.03 > 4.01 deliverable) — not in the scored 2024 cell
(p99.9 700 MW that year). The registered, unarmed `cc_capacity_reconcile` (cell
`U`; its committed table caps Zeltmann 737 → 560, Cricket Valley 1,312.5 →
1,086.9, Athens 1,221.6 → 1,064.7) is the admissible form and is handed to the
queue (§7), not built here (one repair per session, PREREG §4 / F7).

### 2.3 Why the bars could not fire, stated as a defect of the bars

The M4 band's floor is Flynn 7314 (0.707: eGRID 8.70 against a CAMPD loaded
12.3) and Carr Street 50978 (0.816); the M5 band's ceiling is the same two
(1.968, 2.816) — plants whose eGRID annual rate and CAMPD loaded rate disagree
by 30–40 % and whose availability is class-generic against a 0.3–0.5 online
share. A `[min, max]` peer band that admits them admits everything. The bars
stand as pre-registered (F8); a successor should bound the peer set to plants
whose two rate bases agree within the class's own spread.

### 2.4 M6 — the class accounting, 2024 (class sidecar vs bench)

| class | model | actual | Δ |
|---|---|---|---|
| `CC_REGULAR` | 37.934 | 34.060 | **+3.874** |
| `CC_CHP` | 18.913 | 17.017 | +1.896 |
| `CT_PEAKER` | 0.251 | 1.911 | −1.660 |
| `CT_CHP` | 0.885 | 2.172 | −1.287 |
| `ST_GAS` | 8.821 | 9.913 | −1.092 |
| `ST_CHP` | 0.996 | 0.872 | +0.124 |
| **gas family** | **67.800** | **67.802** (EIA-930) | −0.002 |

The family total is pinned (C2); the CC classes' +5.77 is the CT classes'
−2.95 and the steam's −1.09 (plus `ST_CHP`). Any CC-side repair therefore moves
energy to OTHER combined cycles first, not out of the class.

### 2.5 The mechanism at the carriers — when-online loading, 2024

| plant | model on-share / loading when on | meter on-share / loading when on | model − meter, TWh |
|---|---|---|---|
| 56196 Zeltmann | 0.899 / **0.960** | 0.907 / **0.682** | +0.87 |
| 55375 + 57664 Astoria (one facility) | 1.000 / 0.841 | 1.000 / 0.768 | +0.71 |
| 57185 Cricket Valley | **0.995** / 0.543 | **0.878** / 0.503 | +1.84 |
| 55405 Athens | 0.713 / 0.554 | 0.690 / 0.610 | +0.11 |
| 56940 Valley | 0.945 / 0.767 | 0.948 / 0.841 | −0.28 |
| 2539 Bethlehem | 0.909 / 0.558 | 0.916 / 0.754 | +0.19 |

Athens and Valley track their meters; the carriers are the NYC blocks the model
runs flat when on and the Capital-Hudson block it never turns off. Read with
§2.4, the class object is the price/merit position of the CT and steam classes
in those zones — the classes that should be taking those hours — not the CCs'
own bases.

---

## 3. The one data defect, found on the inputs (M2): the Astoria registry split

| registry | what it files |
|---|---|
| EIA-860 | 55375 Astoria Energy: CT1, CT2, ST1 (2006, 595 MW nameplate); **57664 Astoria Energy II: CT3, CT4, ST2 (2011, 650 MW)** |
| eGRID (2018–2024, every vintage) | ONE plant, 55375, 1,245 MW, generators CT1–CT4 / ST1 / ST2; **no row for 57664** |
| CAMPD | ONE facility, 55375, four CT units; no facility 57664 |
| EIA-923 | two plants; 2024 net 4.157 + 4.005 TWh |

**Identity:** eGRID `PLNGENAN(55375)` = EIA-923 netgen(55375) + netgen(57664) to
< 0.5 MWh in all seven vintages (6,341,472 / 5,989,392 / 5,447,419 / 5,899,776
/ 7,207,809 / 7,998,042 / 8,162,646 MWh). The committed identity derive
(`derive_egrid_identity_heat_rates.py`, nyiso-150) tests exactly this equality
one-to-one, with `MATCH_TOL_MWH` 0.5 and `MIN_OVERLAPS` 2, and its own
docstring names "the Astoria 55375↔57664 family" as the object class it was
written for; its predicate cannot reach a two-into-one merge. **Consequence in
the keeper:** the fleet parquet carries `heat_rate = NaN` for 57664 → the
`HEAT_RATE_BINS['gas_cc']['f_class']` default **6.70**, while the sibling block
carries eGRID's 7.258 and the facility meter reads 7.05 (running-hour, stack
duplicates merged). The model's cheapest large NYC combined cycle is an
estimate sitting 5 % under its own meter.

**The repair (generic, zero parameters):** the derive gains a MERGED-identity
leg — for a CAMPD-less EIA plant `p`, an eGRID plant `q ≠ p` of the same state
that is itself an EIA-923 plant, with `PLNGENAN(q) == netgen(p) + netgen(q)`
to the same tolerance in every overlapping vintage, ≥ the same overlap count —
takes `q`'s pooled `ΣPLHTIAN / ΣPLNGENAN` under the artifact's declared rate
rule. Run over the whole population it finds **one pair**: 57664 ↔ 55375,
pooled **7.3792**, per-vintage 7.2576–7.5436, LOYO [7.3552, 7.4041]. The
Allegany row is byte-identical; `--check` reproduces the artifact. No
`ScenarioConfig` field changes (the mechanism `egrid_identity_heat_rates` is
already armed, cell K); the delta is one artifact row. Rule 23: the
re-derivation cites its data change (eGRID's plant boundary at Astoria).

**The same split's availability half — NOT in this arm (F7), sized and handed
forward:** the `perunitmerit` outage extract routes all four CEMS units to EIA
plant 55375 (CT1 / CT2 at 297.5 MW, CT3 / CT4 at 313.0 MW, plant denominator
1,221 MW), so Astoria Energy II is never derated and Astoria Energy I is derated
for its sibling's outages; the tranche artifact reads 55375 at a 150 % median
CF. 2025 shows the cost: 57664's EIA-923 falls to 2.12 TWh on a long outage the
model cannot see (+2.65 TWh, the largest plant excess of any year). The repair
form is the `campd.CAMPD_UNIT_PLANT_REMAP` entry the caiso-196 El Segundo case
established for this defect class — but the outage derive reads the raw
parquets (`scripts/lib/outage_detect.py`), not `_normalize_campd`, so the
remap alone does not reach it; the outage-derive lane owns the routing and the
re-derivation of every CAMPD-fed NYISO artifact it changes.
