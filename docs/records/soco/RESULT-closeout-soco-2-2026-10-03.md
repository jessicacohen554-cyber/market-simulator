# RESULT closeout-SOCO-2 — SOCO nuclear availability 2019–2022 at measured monthly CF

Lane `claude/closeout-soco-2`, 2026-10-03.

**Inputs:**
- PRECOMMIT: `PRECOMMIT-closeout-soco-2-2026-10-03.md`, with its pass/fail reading
  fixed before any LP.
- FINDING: `FINDING-closeout-soco-2-2026-10-03.md`, zero LP.

**Run:** `2026-10-03-closeout-soco-2-nuclear`, bundle
`results/calibration/closeout_soco_2_span`, 2019–2025. It is registered as a probe
(rule 15) and is not promoted.

## 1. What was solved

**Recipe.** The keeper `2026-10-02-w0-soco-fix2` (`w0_soco_span`) replayed with no
`--set`, at lane SHA `826333c41a896ab09e10292b8d580807fef2a015`. The only
solve-affecting difference is `NUCLEAR_MONTHLY_CF_BY_YEAR["SOCO"]` 2019–2022, taken
from the frozen derive. SolveEpoch `2026-10-03b` (stamped `2026-10-03a` in the legs, renamed at merge after NWPP took that id) re-keys backcast SOCO.

**Shards.** Seven, one year each (rule 36), all at the one SHA. Each was verified
before it was archived: 18 files per leg, with `dispatch/<Y>_P1.parquet` and
`hourly/unit_marginal_<Y>.parquet` present, and the bytes held locally.

**Compose.** `scripts/probes/_w0_compose_span.py`, the W0 composer carried onto this
lane. Its recipe check passed field by field against the keeper; it confirmed a
single SHA and a shared solve surface, and regenerated `legitimacy_diagnostics.json`
over the composite.

| Year | Shard branch @ commit (transport, rule 33) | LP P1 | Memory peak |
|---|---|---|---|
| 2019 | `claude/closeout-soco-2-2019` @ `cd0e2e1669a8081d61ad34741c15118702b4a250` | ~80 s | 13.4 GiB cgroup |
| 2020 | `claude/closeout-soco-2-2020` @ `d806bb4a07a2293ccb92444754e7cfde64edb215` | 79.7 s | 13.36 / 15.76 GiB rss+swap |
| 2021 | `claude/closeout-soco-2-2021` @ `74d16147ab08994e97a5ef875be9d4679e25f2f3` | 80.2 s | 13.36 / 15.69 |
| 2022 | `claude/closeout-soco-2-2022` @ `ad246d40ae97e32620c1846eee4451afc9759442` | ~80 s | — |
| 2023 | `claude/closeout-soco-2-2023` @ `06d7be56e58a4215d1dd0cf0ed7df0c5e8555507` | 80.7 s | 13.36 / 15.87 |
| 2024 | `claude/closeout-soco-2-2024` @ `d860fb854302dfc294bf53e5e84260b13540d9ab` | ~80 s | — |
| 2025 | `claude/closeout-soco-2-2025` @ `83ffe40f683159b395ff0d3ae0b4fddf70fd577e` | 84.1 s | — |

**Unserved energy** was 0 MWh in every year.

**Infrastructure stall, resolved in-lane.** Every shard first stopped on
`DegradedInputError` (SOCO `hydro_ror_split`). The cause was that
`scripts/data/curate_hydro_plant_modes.py` `DEFAULT_ISOS` omitted SOCO, so neither
`regenerate_clean` nor `--solve-profile SOCO` built SOCO's `hydro_plant_modes`
partition. The shards ran `curate_hydro_plant_modes.py --iso SOCO`, a data command
with no code edit. On the desk's ruling, SOCO is now registered in `DEFAULT_ISOS`,
with its own review line:
- 30/40 plants, 71.3 % of labelled MW;
- the errors are one-sided: 878.6 MW of EHA run-of-river plants called shapeable,
  and 0 MW the other way.

That one tuple is also what `scripts/lib/clean_profiles.py` reads, so this
**closes the W0 RESULT §7 follow-up** ("SOCO solve-profile `hydro_plant_modes`").
The 2023 leg reproduces the keeper's class totals exactly, which proves the
partition is the one the keeper solved on.

## 2. The numbers (keeper → this run)

Model nuclear against EIA-923:

| Year | Keeper TWh | This run TWh | EIA-923 TWh | Miss now |
|---|---|---|---|---|
| 2019 | 45.25 | 47.21 | 47.73 | −1.09 % |
| 2020 | 45.40 | 47.24 | 47.60 | −0.77 % |
| 2021 | 45.56 | 48.69 | 48.93 | −0.50 % |
| 2022 | 45.56 | 47.09 | 47.06 | +0.06 % |

**2023–2025 are byte-identical to the keeper.** The maximum class |Δ| is
0.0000 TWh, so the EIA-923 2025 drift the PRECOMMIT expected did not move the 2025
leg.

**Where the extra nuclear went (class Δ TWh).** The solved result matches the
zero-LP greedy (FINDING §b′):

| Year | ΔNuc | ΔCC | ΔCT | ΔPRB | ΔBIT | ΔST_GAS | Greedy ΔCC |
|---|---|---|---|---|---|---|---|
| 2019 | +1.96 | −0.52 | −0.64 | −0.41 | −0.16 | −0.18 | −0.57 |
| 2020 | +1.84 | −0.65 | −0.71 | −0.28 | −0.03 | −0.13 | −0.65 |
| 2021 | +3.13 | −2.03 | −0.58 | −0.29 | −0.14 | −0.10 | −1.92 |
| 2022 | +1.53 | −0.95 | −0.43 | 0.00 | −0.02 | −0.13 | −1.01 |

## 3. Scored against the bar (fixed in the PRECOMMIT)

Scoring is `calibration_verdict.py` on the registered payload, rubric v3.17.

**Why the scorer shows extra CAVEAT → FAIL statuses.** This bundle has no governance
attestation yet; `promote_keeper.py` writes it. Without it, the keeper's ledgered
exceptions do not carry. The overall determination therefore reads NOT-YET
(UNATTESTED), and every ledgered CAVEAT row prints as FAIL: COAL_BIT 2019, C3a
2019/20/22, C3b 2022. **These are not regressions.** Their magnitudes are listed
below and every one is equal or better.

### The desk's bar

| Gate | Bar | Pre-fixed reading | Solved | Verdict |
|---|---|---|---|---|
| B1 | 2019 CC_REGULAR inside C1 | FAIL (3.41 pp) | **3.4 pp** (+4.43 TWh) | **FAIL**, as predicted |
| B2 | 2021 CC_REGULAR inside C1 | PASS (2.78 pp) | **2.7 pp** (+4.24 TWh) | **PASS**: FAIL → PASS |
| B3 | No passing (year, criterion) leaves its band | PASS | No C1, C2, C3a, C3b or C8 row moves PASS → FAIL | **PASS** |
| B4 | C3a no worse by > 1 pp | FAIL (2021, 2.2 pp) | 2019 +11.9 → +10.9 %; 2020 +12.0 → +11.0 %; **2021 −4.3 → −5.8 %** (1.5 pp worse, still PASS); 2022 −14.3 → −14.8 % (0.5 pp worse); 2023–25 unchanged | **FAIL** (2021, 1.5 pp), as predicted |

### The PRECOMMIT's structural gates

| Gate | Condition | Solved | Verdict |
|---|---|---|---|
| S1 | Nuclear 2019–22 within ±2.0 % of EIA-923 | −1.09 / −0.77 / −0.50 / +0.06 % | **PASS** |
| S2 | 2023/2024 class totals within 0.05 TWh of the keeper | 0.0000 (2025 also 0.0000) | **PASS** |
| S3 | No C1/C2/C3a PASS → FAIL; C8 forced shares move ≤ 2 pp | none; ST_GAS forced +1.1 to +1.5 pp (2019–22), all still GROUNDED | **PASS** |
| S4 | CC 2021 share falls ≥ 0.5 pp; CC 2019 falls ≥ 0.1 pp | −0.9 pp; −0.2 pp | **PASS** |

### Other rows

- **C1 COAL_BIT 2019:** −11.11 → −11.27 TWh (still the ledgered row).
- **COAL_PRB:** within 0.4 TWh in every year.
- **C3b (NRMSE):**
  - 2019: 0.142 → 0.137;
  - 2020: 0.149 → 0.140;
  - 2021: 0.119 → 0.125;
  - 2022: 0.282 → 0.281.
- **C2 sysvol:** PASS in every year. The 2021 gas family's C1 flag clears.
- **C4 dispatch_corr:** PASS.
- **C8 forced share:** PASS.

## 4. Determination on promotion (expected)

The ledger carries forward under rule 35 (the outgoing keeper's exceptions). The
only change to the failing set is that **C1 CC_REGULAR 2021 leaves it**.

SOCO stays **NOT-YET** on C1 CC_REGULAR 2019 at +3.4 pp share. The FINDING
attributes about half of that to the model-versus-bench total-generation gap, and
the rest to the 2019 night self-commitment of coal BIT, which is the mirror of the
ledgered C1 COAL_BIT 2019 row. Every route to that residual is adjudicated G/R:
- take-or-pay: G;
- take floor: G;
- coal campaign floor: refused at soco-73;
- startup amortization: G;
- replacement-cost coal: spot ≥ blended.

## 5. Recommendation to the desk

**Promote `2026-10-03-closeout-soco-2-nuclear` on structure (rules 1 and 14).**
- The PRECOMMIT's ex-ante decision rule is met: S1–S4 all PASS.
- The change replaces a forecast-fallback estimate with the measured EIA-923
  monthly CF the 2023–25 legs already read. Nuclear moves from 3–7 % short to
  within 1.1 % of EIA-923.
- It is zero DOF and adds no new field.

**The cost is on the desk's bar.**
- B1: 2019 CC stays FAIL (3.4 pp).
- B4: C3a 2021 moves 1.5 pp further from λ, staying inside ±10 %.

**What it buys:**
- 2021 CC_REGULAR flips FAIL → PASS.
- 2019 and 2020 C3a each move 1.0 pp toward λ.
- C3b improves in three of four changed years.

**Card options for the owner:**
- **(A) Promote on structure.** Recommended.
- **(B) Hold**, with the keeper unchanged. This leaves 2019–22 on a known estimate,
  which is a rule-14 defect.

**Optional follow-up (desk's call).** Route C1 CC_REGULAR 2019 to the existing 2019
self-commitment ledger row as its mirror. That is a ledger-scope question, not part
of this promotion.

**Promotion cost:**
- one `promote_keeper.py` run on the desk's slot;
- prune of `w0_soco_span`;
- the bundle above is already registered.

**Bundle bytes:**
- The keeper-format bundle (hourly sidecars, `unit_marginal` every year, metrics,
  configs, diagnostics) is committed on the lane branch under
  `results/calibration/closeout_soco_2_span`.
- The dispatch parquets live on the seven shard commits above, and in this
  container until it is reclaimed.
- Nothing has been deleted (rule 31).

## 6. Matrix and records

- **SOCO shard (`docs/codebase-site/data/mechanism-matrix/SOCO.js`):**
  `nuclear_unit_availability` stays U (the NRC overlay is untested), with its note
  updated to the solved result. `coal_fuel_inventory` stays U (FINDING §c/§e census).
- **No new matrix row:** a `constants.py` table is not a `ScenarioConfig` field.
- **Cross-ISO:** the PJM/NWPP/SPP nuclear rows go to lane closeout-nuclear-rows
  (owner ruling R-35). This PR stays SOCO-only.
