# DECISION CARD — nyiso-189: which instrument form repairs the eGRID steam-generator filing artifact (Bethlehem 2539 and its population), and which vintages it may reach

**Session:** nyiso-189, NYISO backcast-calibration lane, 2026-09-04. **Zero
solves.** Keeper `2026-09-04-nyiso-188-combined` (CALIBRATED, grade 7, fails
0, C3c ledgered) is untouched. **Pre-registration:**
`results/calibration/PREREG-nyiso189-bethlehem-gen-collapse-census.md`,
pushed at `65dc4094` before the census ran. **Record:**
`results/calibration/_nyiso189_gen_collapse_census/` (probe
`scripts/probes/nyiso189_gen_collapse_census.py`).

## 1. The population fact (Step 0, as pre-registered — T1 is a zero test, T2–T4 are records)

38 NYISO combined cycles file a steam (`CA`) generator in eGRID. **T1 — the
steam generator reports exactly zero net generation in a vintage its CTs
run — fires at five:**

| plant | T1 fires in | ST/CT range (all vintages) | T1-clean median ST/CT | nameplate CA/CT | heat per CT-MWh | applied HR (eGRID 2023) | 2023 block HR at own share / at nameplate share |
|---|---|---|---|---|---|---|---|
| Bethlehem 2539 | **2024 only** | 0.000–0.519 | 0.495 | 0.532 | 10.26–12.55 | **9.665** | **6.89 / 6.72** |
| World Generation X 54131 | **2023 only** (the applied vintage) | 0.000–0.418 | 0.402 | 0.349 | 9.73–12.33 | **9.807** | **7.00 / 7.27** |
| Richard M Flynn 7314 | 2019–2024 (chronic) | 0.000–0.531 | 0.531 (one clean vintage) | 0.545 | 8.34–12.74 | 8.704 | 5.69 / 5.63 |
| Ravenswood 2500 | 2019–2024 (chronic) | −0.002–0.000 | — | 0.483 | 10.86–24.31 (mixed-family plant; `PLHTIAN` spans its steam boilers) | 9.500 (family rate) | not meaningful |
| Lederle 10521 | 2019–2024 (chronic; a 12 MW cogen) | 0.043–0.091 | 0.043 | 0.410 | 5.98–6.25 | 5.759 | 5.91 / 4.37 |

Everywhere else the steam share is stable across vintages (e.g. Athens
0.528–0.541, Zeltmann 0.543–0.625, Astoria Energy 0.581–0.635, Sithe
0.569–0.590) and the applied 2023 `PLHTRT` sits within 0.1 of the block HR
at the plant's own share — the CT-heat identity reproduces eGRID's own
plant rate where the filing is intact, which is the identity's validation.
The cogens with structurally small steam shares (CH Resources 10617 /
10621, Cornell, NYU, Kennedy) are steam-to-host plants, not artifacts.

**Bethlehem's 2023 vintage is the one that matters and T1 does not reach
it** (CA = 267,718 MWh, ST/CT 0.065 against its own 0.49–0.52 record). The
zero test reaches, in the applied vintage: World Generation X (50 MW; applied
9.807 against ≈ 7.0–7.3) and the three chronic reporters, of which Flynn
(applied 8.704 against an implausible 5.6–5.7 from a single clean vintage)
and Ravenswood (mixed-family) are not safely repairable by the identity as
written. So a threshold-free form fixes a 50 MW cogen and misses the 750 MW
plant that motivated the object.

## 2. The decision (verbatim options from FINDING-nyiso188 §4.2; nothing is built until one is chosen)

| form | what it is | reaches Bethlehem 2023? | footprint | admissibility |
|---|---|---|---|---|
| **A — pooled-vintage eGRID basis** | the identity derive's rule (ΣPLHTIAN / ΣPLNGENAN over all vintages, LOYO recorded) as a registered mechanism for every CAMPD-covered plant | yes, by dilution: 2539 → 7.85, LOYO [7.51, 8.05] | every NYISO plant's base heat rate moves (fleet-wide basis change, one A/B) | (a)–(d) in form; knowingly contaminated at 2539; the strongest LOYO spreads flag the artifact plants |
| **B1 — CT-heat identity, T1-admitted** | `PLHTIAN / Σ GENNTAN(CT) / (1 + ST/CT)` for plant-vintages T1 flags, share = the plant's T1-clean median (measured record) or the EIA-860 nameplate ratio (published field) | **no** | World Generation X 2023 (+ chronic reporters, with Flynn / Ravenswood exclusions needing their own rule) | threshold-free, source-internal |
| **B2 — CT-heat identity, record-admitted** | as B1, but a vintage is inadmissible when its ST/CT lies BELOW the plant's own minimum over its T1-clean vintages (a plant-history bound, no external constant) | **yes**: Bethlehem 2023 (0.065 < 0.49), 2024 (0.000); World Generation X 2023 | the same plants; the rule is relative, not a global threshold | needs the owner to authorize the plant-history bound as the admissibility test (it is a rule choice, not a fitted number) |

**Session recommendation:** **B2 with the plant's own T1-clean median share**
(2539 → 6.89; World Generation X → 7.00), NOT A. Grounds: A moves every
plant on a pooled basis to reach one plant, and still leaves that plant at
7.85 against a block three independent bases put at 6.9–7.0; B2 reaches
exactly the plant-vintages whose filed steam share departs from the plant's
own record, with every constant a published field or the plant's own
measured history. The bound is the owner's to authorize; once chosen, the
lane pre-registers its own A/B (one `ScenarioConfig` field + matrix row;
control = same-HEAD replay; rejected iff C2 / C3a / C3b / C8 flip PASS → FAIL)
and solves.

**Expected footprint if B2 is chosen (stated, not measured):** Bethlehem's
variable cost falls ≈ $7.5/MWh (2.8 MMBtu/MWh × 2024 delivered gas), which
moves it INTO merit in Capital-Hudson; the class total is pinned by the gas
family, so the energy comes from other CCs (Athens, Cricket Valley) and
`ST_GAS`; C3a moves DOWN in every year (the keeper is +7.9 / +3.8 / −6.9 %,
so 2023 / 2024 improve and 2025 worsens toward the band edge). This is why
the choice is the owner's: it is a structural correction with a known price
direction, not a fit.

## 3. What the owner needs to say

1. **A or B2** (or B1, accepting that it does not reach Bethlehem 2023).
2. For B: **which steam share** — the plant's own T1-clean median (measured,
   varies by plant) or the EIA-860 nameplate ratio (published, 2539: 0.532).
3. For B2: **authorize the plant-history bound** ("a vintage below the plant's
   own T1-clean minimum steam share is inadmissible") as the admissibility
   rule.

Nothing else is open on this object. The `complete`-marker question raised
by a CALIBRATED keeper is separate and remains the owner's.
