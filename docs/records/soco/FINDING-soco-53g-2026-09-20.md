# FINDING — SOCO-53g (2026-09-20): the $9.7/MWh defect that never reaches the LP, and a cell that was already adjudicated

**Lane** SOCO-53g · **Model** Opus 5 · **Date** 2026-09-20 ·
**Branch** `claude/soco-coal-prb-proxy-own-iso-4qln9o` · **Data profile** `soco` ·
**PRECOMMIT** `docs/handoffs/PRECOMMIT-soco-53g-2026-09-20.md`, pushed at
`da6c8d37fbdce04bf4225925914c6e994f6a1bcb` **before any solve**, and the SHA all three
shards pinned ·
**Incumbent keeper** `2026-09-20-soco53f-measured-coal-hr`, bundle
`results/calibration/soco53f_coal_hr` ·
**Run** `2026-09-20-soco53g-prb-own-iso`, bundle `results/calibration/soco53g_prb_own`
(committed) · **No control solved** — G-DRIFT found zero LIVE hunks, so rule 29(b) form 4
against the keeper is valid.

---

## 1. HEADLINE

**The arm moves nothing that is scored or reported, in any year — and phase 0 said so
before an LP was spent.**

`FINDING-soco-53f` §9 item 1 commissioned this lane on a measured claim: SOCO's three PRB
plants (6,361.5 MW, 55 % of its coal capacity) priced off the hand-curated **ERCOT-only**
reporter pool at 1.8228 / 1.7520 / 1.6147 $/MMBtu against their own 2.6711 / 2.4982 /
2.4610 — an under-pricing of **47–52 %, ≈ $9.7/MWh**, *"THREE TIMES SOCO-53f's lever, IN
THE OPPOSITE DIRECTION."*

**Both pooled numbers are correct and I reproduce them to four decimals. The inference
from them is wrong, for a structural reason: NEITHER POOL REACHES THE LP.**
`apply_coal_supply_pricing` writes the proxy onto SOCO's 15 PRB tranche rows and
`apply_plant_monthly_fuel_prices` **overwrites it three lines later** with each plant's
own filed EIA-923 monthly delivered cost. The model prices Miller at **2.1886**, Daniel at
**3.8505**, Scherer at **3.3945** (2023) — each plant's own receipts. Rule 14
`[R-ACCURATE]` was already being honoured at SOCO, one layer further down.

**The solve confirms the zero-LP prediction exactly, and then some:**

- **2023 and 2024 are BYTE-IDENTICAL to the keeper** — same `sha256` on `floors/`,
  `dispatch/<y>_P1.parquet`, `system.parquet` and `unit_hourly`, solved independently in
  separate containers at a *different* HEAD.
- **2025 differs in 4 of 657,000 class-hour cells**: a **2.2 MW degenerate tie swap**
  between a Georgia `CT_PEAKER` tranche and a 2.2 MW hydro unit at **identical** marginal
  costs, in hours **8098 and 8217** — December, not January — **netting to exactly
  0.0 MWh**.
- **Annual class generation: 0.000000 TWh apart on all 45 class-years.**
  `system.parquet` identical in all three years, so **prices and
  `marginal_emission_rate` do not move at all**.
- **All 21 C1 rows reproduce the keeper's exactly**, on **both** benches.

**Determination `NOT-YET` (rubric v3.8, PRICE UNSCORED), identical to the keeper on every
criterion, grade, caveat count and DOF entry.** Zero `ScenarioConfig` fields and zero free
parameters added.

**Three things are recorded against this lane and they lead §2, §3 and §6:** the
commissioning premise was false; **the matrix cell was already adjudicated `I` and this
lane read it only after launching its shards**; and prediction **P3 is falsified in
substance** for a reason that was measurable at zero LP and that I did not measure.

---

## 2. THE MECHANISM FIRES, AND IS THEN ERASED

Replaying `run_calibration.py:4484-4495`'s exact mutation sequence by hand on the keeper's
own rebuilt fleet, with the proxy OFF and ON, snapshotting after each step
(`scripts/probes/_soco53g_phase0.py decompose`):

| step | 2023 max \|OFF−ON\| | 2024 | 2025 |
|---|---|---|---|
| 1. `resolve_fuel_prices(apply_monthly=False)` | 0.000000000000 | 0.000000000000 | 0.000000000000 |
| 2. after `apply_coal_supply_pricing` | **0.958175366013** | **0.831525117241** | **1.053587942453** |
| 3. after `apply_plant_monthly_fuel_prices` | **0.000000000000** | **0.000000000000** | 0.649940697470 |

**15 rows move at step 2** — exactly the three PRB plants' five tranches each, 1.8227 →
2.6706 $/MMBtu in 2023 — and the plant-monthly overlay then writes **8,760 of 8,760
cells** on every one of them in 2023 and 2024.

**Rule 19 `[R-ONE-MECH]`, at two grains.** `fuel_prices` and `mc_base` from
`run_year(..., fleet_only=True)` rebuilds, resolved config verified `ctl=False` / `arm=True`
on every leg so a null result is the mechanism and not the plumbing:

| year | LP rows | `fuel_prices` rows moved | `mc_base` rows moved | max \|Δ mc_base\| |
|---|---|---|---|---|
| 2023 | 327 | **0** | **0** | **0.000000000000** |
| 2024 | ~327 | **0** | **0** | **0.000000000000** |
| 2025 | 290 | 5 | 4 | 7.7512 $/MWh, 744 h only |

Every non-COAL class sits at max \|Δ\| exactly **0.000000000000** in all three years —
`ST_GAS`, `CT_PEAKER`, `CC_REGULAR`, all three CHP classes, hydro — **including plant
6073's own 1,132 MW gas `CC_REGULAR` rows**, which share its ORIS code. The class gate does
not leak.

**Barry is outside the blast radius by construction.** `price_by_supply` carries exactly
two keys, `lignite` and `prb`; a `bituminous` row returns `None` and is skipped.
`coal_supply_by_iso("SOCO")` tags **3 Barry, 26 Gaston, 703 Bowen** bituminous. Barry's
rows are **not among the 15** in any year. Barry unit 4's real defect — a gas-fired boiler
paying a coal fuel price — is untouched and stays routed.

---

## 3. THE CELL WAS ALREADY ADJUDICATED `I`, AND I READ IT AFTER LAUNCHING

`docs/codebase-site/data/mechanism-matrix/SOCO.js` already carried
`coal_prb_proxy_own_iso` at **`I` (INERT)**, written by **NWPP-41 on 2026-09-17**:

> *"SOCO has 3 prb-ranked plants and ALL THREE file their own EIA-923 delivered cost in
> every year 2023-2025, so `apply_plant_monthly_fuel_prices` overwrites the proxy on every
> one of them and the pool never reaches a SOCO plant. **Nothing to arm unless a SOCO PRB
> plant stops reporting.**"*

**Rule 28 `[R-MECH-MATRIX]` (a) forbids re-testing an `I` cell without new evidence, and
the SessionStart hook says to check the cell BEFORE proposing a lever. I checked it after
launching three shards.** That is a process miss and it is recorded as one, not
explained away. `FINDING-soco-53f` §9 item 1 also routed this lane without checking the
cell — so the miss is two lanes deep, which is exactly the accumulation the DO-NOT-REDO
discipline exists to stop.

**What makes the work admissible rather than a redo is that it produced new evidence, and
that evidence corrects the cell.** NWPP-41 censused at the **plant-YEAR** grain. The grain
that matters is the **plant-MONTH**:

| | plant-years | fully silent | **missing plant-months** |
|---|---|---|---|
| SOCO PRB pool (6002, 6073, 6257) | 9 | **0** | **2** — `6073/2025:[1]`, `6257/2025:[10]` |

All three plants do file every year. **6073 Daniel still skips January 2025**, where the
overlay writes only **8,016 of 8,760** cells and the ERCOT-pool fallback survives in the
other 744. **The cell's closing sentence is falsified: a plant that keeps reporting but
misses one month is enough.**

And the plant-month count is itself an **upper bound**, not the footprint: Scherer also
missed a month (October 2025) and `nearby_fuel_price_fallback` **did** cover it
(8,760/8,760). Two missing plant-months yield **one** live one.

---

## 4. THE LIVE FOOTPRINT, PINNED EXACTLY — AND WHY NO MW FOLLOWS

**The offer moves.** 2,976 unit-hours — Daniel's `committed` / `econlo` / `econhi` / `peak`
coal tranches × 744 hours — carry **+7.7512 $/MWh**, *mean = min = max*, flat across
2025-01-01 00:00 .. 2025-01-31 23:00. Fuel +0.6500 $/MMBtu (1.7441 → 2.3941). Exactly what
phase 0 predicted, to four decimals.

**No MW follows.** Daniel's coal at an armed `mc` of **27.37 $/MWh** is still far
inframarginal against a January system price averaging **56.29** (p10 41.38, p90 72.84).
A $7.75 lift does not come near a merit-order boundary. Daniel's COAL energy in the window
is **0.2810 TWh** on both sides, to **+0.0 MWh**.

**The only MW difference in the entire three-year bundle:**

| hour | unit | ctl → arm MW | `mc` ctl | `mc` arm |
|---|---|---|---|---|
| 8098 | `CT_PEAKER_SOCO_GA_p55061_econhi` | 119.541939 → 117.341942 | 60.390652 | 60.390652 |
| 8098 | `7191_hydro` | 0.000000 → 2.200000 | 1.400000 | 1.400000 |
| 8217 | `CT_PEAKER_SOCO_GA_p55061_econlo` | 267.695557 → 269.895569 | 60.390652 | 60.390652 |
| 8217 | `7191_hydro` | 2.200000 → 0.000000 | 1.400000 | 1.400000 |

**Identical marginal costs on both sides, and the two hours cancel exactly (Σ Δ = 0.0
MWh).** That is the degenerate-alternate-optimum signature: the same 2.2 MW moved from one
hour to another, annual totals unchanged. It is not caused by the arm's own repriced rows —
none of which moved — but by the basis reshuffling under a perturbed objective.

---

## 5. WHAT THE RUN DELIVERED

### 5.1 Dispatch — nothing moved

| | 2023 | 2024 | 2025 |
|---|---|---|---|
| `class_hourly` cells moved / total | **0 / 657,000** | **0 / 657,000** | 4 / 657,000 |
| `system` cells moved / total | **0 / 262,800** | **0 / 262,800** | **0 / 262,800** |
| `class_band_hourly` cells moved | **0 / 2,330,160** | **0 / 2,330,160** | 4 / 2,330,160 |
| `storage` cells moved | **0 / 140,160** | **0 / 140,160** | **0 / 140,160** |
| max \|Δ annual class TWh\| | **0.000000000** | **0.000000000** | **0.000000000** |
| file `sha256`: `floors/`, `dispatch/<y>_P1`, `system.parquet`, `unit_hourly` | **IDENTICAL** | **IDENTICAL** | — |

### 5.2 Gates

| | keeper | arm (committed bench) | arm (HEAD-rebuilt bench) |
|---|---|---|---|
| determination | `NOT-YET` (PRICE UNSCORED) | `NOT-YET` | `NOT-YET` |
| C1 | FAIL, 1 row (2023 `CT_PEAKER`) | **same** | **same** |
| C1 all · free | 13/14 · 9/10 | **13/14 · 9/10** | **13/14 · 9/10** |
| C2 / C4 / C6 / C8 | PASS | **PASS** | **PASS** |
| C3a / C3b / C3c | UNSCORABLE | UNSCORABLE | UNSCORABLE |
| `grade_summary` | scored 5, target 4, fails 1 | **identical** | **identical** |
| caveats | 0 ledgered, 0 protective | **0 / 0** | **0 / 0** |
| DOF | 3 entries / 1 residual | **3 / 1** | — |
| **C1 rows differing vs keeper** | — | **0 of 21** | **0 of 21** |

2023 `CT_PEAKER` stays the single FAIL at **+9.73 TWh / +4.0pp** (HEAD bench: +9.76 /
+4.1pp). **SOCO's headline defect is neither fixed nor worsened.**

### 5.3 Rule 17 `[R-FLOOR-WINDOW]` — re-measured, holds, and identical to the keeper

Re-measured on this bundle's own `floors/<year>_P1.npz` with
`scripts/probes/_soco53g_floor_shares.py`, **first validated by reproducing the keeper's
own table exactly — all fifteen cells, shares and median block lengths**. Binding share
against each plant's own measured `sync_share`:

| plant | 2023 | 2024 | 2025 | measured | Δ vs keeper |
|---|---|---|---|---|---|
| 3 Barry | 0.000 | 0.000 | 0.000 | 0.0632 | +0.000 |
| 10 Greene County | 0.309 | 0.295 | 0.496 | 0.7516 | +0.000 |
| 26 E C Gaston | 0.197 | 0.078 | 0.184 | 0.6392 | +0.000 |
| 728 Yates | 0.074 | 0.478 | 0.749 | 0.8429 | +0.000 |
| 2049 Jack Watson | 0.808 | 0.652 | 0.753 | 0.9202 | +0.000 |

**Zero exceedances; every cell identical to the keeper.** Barry keeps zero floored hours;
floored blocks keep a median of 64–342 h (campaigns, not gap fills).

### 5.4 Marginal emission rate — unchanged, to the cell

| year | lw-mean | p10 | median | p90 | zero-share | cells differing vs keeper |
|---|---|---|---|---|---|---|
| 2023 | 0.6255 | 0.4187 | 0.5905 | 0.8635 | 0.00 % | **0 / 26,280** |
| 2024 | 0.5921 | 0.3833 | 0.5810 | 0.7121 | 0.00 % | **0 / 26,280** |
| 2025 | 0.6161 | 0.3833 | 0.5848 | 1.0244 | 0.15 % | **0 / 26,280** |

### 5.5 Legitimacy diagnostics — substantively identical

`gates` block identical. `D1`, `D4`, `D5`, `D10` **byte-identical**. `D2` differs only in a
newly-populated `load_share` field (every `forced_share`, `class_total_twh` and `verdict`
identical); `D9` differs only in the bundle-name string. The D-1 FAILs (2023 `COAL_BIT`,
2024 `COAL_PRB`, 2025 `CT_PEAKER`) are **inherited from the keeper**, and none gates — no
COAL class carries a forced mechanism row at all (`forced_share` 0.0 throughout).

---

## 6. THIS LANE'S OWN PREDICTIONS, SCORED HONESTLY

| # | prediction | outcome |
|---|---|---|
| **P1** | 2023 BIT-IDENTICAL to the keeper | **CONFIRMED, and exceeded** — byte-identical, not merely numerically identical |
| **P2** | 2024 BIT-IDENTICAL | **CONFIRMED, and exceeded** — byte-identical |
| **P3** | 2025 moves through Daniel's rows; `COAL_PRB` FALLS 0.000–0.141 TWh; displaced energy to `CC_REGULAR`/`CT_PEAKER`; bound 0.4108 TWh | **FALSIFIED IN SUBSTANCE.** `COAL_PRB` fell by **exactly 0.000000 TWh**; no class moved; the only movement was a 2.2 MW tie swap in **December**, not January, at identical marginal costs. The stated band's lower edge was 0.000, so the number is inside it — but the prediction's *content*, that the offer lift would displace coal energy, is wrong. See below. |
| **P4** | No scored C1 row changes value in any year | **CONFIRMED, and more strongly** — no class moves at all; all 21 C1 rows identical |
| **P5** | `NOT-YET`; C2/C4/C6/C8 PASS; 0 caveats; DOF 3/1; C1 13/14 · 9/10; zero fields, zero free parameters | **CONFIRMED in full**, on both benches |
| **P6** | Rule 17 holds in all twelve plant-years; 2023/2024 reproduce the keeper exactly; 2025 rises or holds, bounded +0.05 | **CONFIRMED** — all fifteen cells identical, so 2025 *held* |
| **P7** | MER unchanged 2023/2024; 2025 rises 0.0000–0.0050 | **CONFIRMED at the band's edge** — unchanged in all three years, 0 of 26,280 cells |
| **P8** | Parity CI-green for SOCO; E13 fires on registration; nothing new | **CONFIRMED** (§7) |

**Seven of eight hold; P3 is falsified and the reason matters more than the miss.** I
predicted that a +$7.75/MWh offer lift would displace coal energy **without checking where
Daniel's coal sat relative to the January price.** It sits **~$29/MWh below the mean**. That
check was available at **zero LP** — the keeper's own `unit_hourly` carries `mc` and
`system_2025.parquet` carries `price`, and I read both files for other purposes in the same
session. **This is the same class of error `FINDING-soco-53f` §6 P9 made**: reasoning about
a machine's cost without asking where the cost sits relative to the price that clears. Two
lanes running. The lesson is cheap and specific: **an offer-side lever's dispatch effect is
bounded by how close the repriced rows are to the margin, and that distance is one join
away in the committed bundle.**

---

## 7. GATES

| gate | state |
|---|---|
| `check_mechanism_matrix --base origin/main` | **PASS** — integrity, anchors (0 unresolvable), keeper stamps, §5.x prose headers, all three ratchets |
| `check_cache_key_registration` | **RED at HEAD, NOT THIS LANE'S** — `PPA_COST_RECOVERY_YR` and `REGIONAL_RENEWABLE_CF` have no `DECLARED` entry. Both were added by commit `3fc20b97` (the MAC-sidecar lane) and are consumed **only** by `scripts/build_mac_sidecar.py` and `scripts/data/derive_regional_renewable_cf.py`, neither on the solve path. This lane adds no field. **Routed, not patched.** |
| `check_bench_freshness` | **RED repo-wide**; SOCO's three parts STALE for nyiso-240's EIA-923 repair (`FINDING-soco-53f` §7, +2.616 TWh). **SOCO's bench was deliberately NOT rebuilt** — the auto-rebuild was reverted and `metrics.json` re-written on the committed bench. **Both verdicts reported and they agree** (§5.2). |
| `check_registry_payload_parity` | **CI-GREEN for SOCO** — the only committed SOCO path is the registered `soco53g_prb_own`. The LOCAL run lists this session's own gitignored leg dirs because the gate walks the filesystem (`:437`), exactly as rule 31's 2026-09-16 correction documents. **Nothing deleted.** |
| `audit_keepers --check --iso SOCO` | E13 fires on registration — **FIFTH** consecutive SOCO lane (§7.1); E11 lineage as declared in the PRECOMMIT |
| `ruff check` / `ruff format` | clean on every file this lane touched |

### 7.1 E13 fires for the FIFTH consecutive SOCO lane, for the same structural reason

`2026-09-20-soco53g-prb-own-iso` is registered for SOCO but is neither the keeper nor
stamped to one. It is a **newly registered candidate whose promotion the owner has not
ruled on**, and E13 has no state for that. Each way to turn it green breaks a rule: pruning
deletes a result before the ruling (rule 31); stamping `holdout.keeper` would be factually
false (rule 30(a) is for the keeper's own recipe on a *held-out year*, and this is a
different config on the same years); promoting pre-empts the owner. `FINDING-soco-53`
§9.1, `53d` §9.1, `53e` §8.1 and `53f` §8.1 recorded the identical analysis. **Five lanes.
The routed fix is a `candidate: true` sidecar field, or an E13 exemption for a run
registered after the current keeper's date with no promotion recorded.**

### 7.2 The E11 recipe diff, declared before the solve

`coal_prb_proxy_own_iso` is a `ScenarioConfig` field but **not** a `solve_and_persist`
kwarg, so `replay_keeper --set` routes it through the generic `prb_overrides` channel alone
and `meta.json` records `coal_prb_sigmoid_overrides {} -> {'coal_prb_proxy_own_iso': true}`.
**Benign, and verified three ways**: the composer refuses any leg whose *resolved*
`coal_prb_sigmoid_overrides` is non-null, `gen_soco53g_attestation._verify` re-checks it,
and all three legs read `null` with `coal_prb_proxy_own_iso: true`. Nothing leaked into the
PRB sigmoid registry.

---

## 8. G-DRIFT (rule 29(b)) — ZERO LIVE HUNKS, AND THE SOLVE PROVED IT

`git diff 04f7f849 HEAD -- src/market_sim scripts/run_calibration*.py scripts/lib
scripts/replay_keeper.py data/raw/_validation-source data/raw/reference` → **309 insertions
over 5 files**, two commits, both classified **INERT** in the PRECOMMIT before the solve:
`aa4bb5b5` (caiso-288's `caiso_citygate_blackout_bridge`, new `bool = False`, CAISO-gated,
absent from the recipe) and `3fc20b97` (two constants consumed only by the MAC sidecar,
plus `new_entry.py` `cf_override`/`life_override` defaulting to `None` and byte-identical
there — and `new_entry.py` is capacity evolution, which a `mode="backcast"` run never
enters).

**The byte-identity of 2023 and 2024 is an independent confirmation of that audit.** The
legs solved at `da6c8d37`, the keeper at `04f7f849`, and the **solve-surface fingerprint
moved** (`f4d250dfebdf2c96` → `60895cac1f7c8879`) — yet the dispatch is byte-for-byte the
same. A fingerprint change with no dispatch change is precisely what "INERT" means, and it
is rarely this cleanly demonstrated.

---

## 9. ROUTED

1. **The cross-ISO census in `_prb_monthly_actuals`' own docstring is at the wrong grain,
   and understates the populations.** It records the ERCOT series as sticking to
   non-reporting PRB plants in *"MISO (12 plants), PJM (2) and SPP (3–5) as well as NWPP
   (5)"*. Re-censused at the **plant-month** grain over 2023–2025:

   | ISO | PRB plants | plant-years | fully silent | **missing plant-months** |
   |---|---|---|---|---|
   | MISO | **38** | 114 | 36 | **484** |
   | SPP | **29** | 87 | 11 | **216** |
   | NWPP | 9 | 27 | 15 | 180 |
   | ERCOT | 7 | 21 | 15 | 181 |
   | PJM | 2 | 6 | 6 | 72 |
   | SOCO | 3 | 9 | **0** | **2** |

   Two corrections, both **measurements routed to those ISOs' own lanes, never verdicts**
   (rules 25 `[R-ISO-SCOPE]` / 28(d)): the plant-count census **understates** the
   populations badly (MISO 38 not 12; SPP 29 not 3–5); and a missing receipt is an **upper
   bound** on the live footprint, because `nearby_fuel_price_fallback` covers some of them.
   **The only true measurement is the mutation-sequence decomposition**
   (`scripts/probes/_soco53g_phase0.py decompose`), and each lane should run it on its own
   fleet before spending a solve. **NWPP-41's own armed NWPP cell deserves the same
   re-measurement** — its case rested on Colstrip and Centralia filing nothing, which the
   plant-year grain does capture, but its *magnitude* has never been measured past the
   overlay.
2. **Only 2 of the 7 hand-curated `COAL_PLANT_SUPPLY` PRB plants file anything** in
   2023–2025 (6179, 7097, both TX). "The ERCOT pool" is a two-plant pool. That is ERCOT's
   lane's to look at, not this one's.
3. **`derive_parasitic_load.py` has never been run for SOCO** — unchanged from
   `FINDING-soco-53f` §2.4, re-routed with its numbers (SOCO coal meter 0.866–0.928 against
   the committed 0.93, so every SOCO coal heat rate is biased LOW by 1.5–5.9 %).
4. **SOCO-53b, the 2025 hydro input hole** — 0.327 TWh modelled against 6.012 measured.
   This lane touches it not at all (hydro is identical in all three years).
5. **Barry unit 4** (§2) — 362 MW the model prices as coal on a coal fuel price while CAMPD
   files it as gas. Proven outside this lever's reach; still routed.
6. **SOCO's committed bench does not carry nyiso-240's repair.** Rebuilding re-scores the
   keeper; the desk's call.
7. **E13's fifth consecutive SOCO firing** (§7.1).
8. **`check_cache_key_registration` is RED at HEAD** for another lane's two constants (§7).

---

## 10. COST, AND WHERE EVERY BYTE LIVES (rules 31 / 33 / 34)

- **Parent LP cost: ZERO.** The parent ran no LP of any length (rule 32(a)). Phase 0, the
  `fleet_only` rebuilds, the decomposition, composition, the floors re-measurement and all
  scoring are zero-LP.
- **Three shards, ONE YEAR EACH** (rule 36 `[R-YEAR-ISOLATION]` (a)), all pinned to
  `da6c8d37fbdce04bf4225925914c6e994f6a1bcb`, each pushing a **full 16-file bundle**
  including `dispatch/<year>_P1.parquet` and the bundle-root `system.parquet` (rule 34(a)).
  Solve wall-clock ≈ 115 s for 2023; all three well inside the 20-minute ceiling.
- **Retrievability verified before anything was archived** (rule 34(d)): `git ls-tree`
  returns **16 files** on each. **A promotion costs ZERO re-solves.** Recovery by IMMUTABLE
  SHA (rule 33(d)), also recorded in `.gitignore` — **the explicit `git fetch origin <sha>`
  is REQUIRED first**, the shard branches are auto-deleted:

  | leg | SHA |
  |---|---|
  | `soco53g_arm_2023` | `bce798aba680a79f1e06320ed8382575e07c63f3` |
  | `soco53g_arm_2024` | `050c7baddb73b52b46f9b15086027eeba2b7a69f` |
  | `soco53g_arm_2025` | `52e999c71b6eb44699fb833672479a1083a5966e` |

  Re-compose at zero LP with `scripts/probes/soco53g_compose_span.py --expect-proxy true`.
- **The keeper's own legs were verified to still resolve** and were recovered in this
  session — `0f061987…`, `34d7131e…`, `381ca2fc…`, 16 files each — with the same
  explicit-fetch caveat, which `PRECOMMIT-soco-53g` §8 records as a correction to the
  handoff's recovery instructions.
- **The composite is committed**; the three per-year legs are **gitignored, not deleted**
  (rule 31 `[R-RETAIN]`, discharging rule 29(c) via `.gitignore` rather than `rm`).
- **All three shard sessions archived** after fetch + checkout + verify (rule 33(a)/(e)).
  None left alive. **Nothing was deleted.**

---

## 11. THE PROMOTION QUESTION (rule 31 `[R-RETAIN]`) — AND MY RECOMMENDATION

**SOCO's keeper is unchanged at `2026-09-20-soco53f-measured-coal-hr`. Nothing has been
pruned.** The candidate is `2026-09-20-soco53g-prb-own-iso`.

**MY RECOMMENDATION: DO NOT PROMOTE THIS RUN AS IT STANDS. Arm the mechanism as a POSTURE
instead, if you want it — and that is a different act with a different deliverable.**

The owner's standing rule is *"if structural integrity improves but gates regress that may
still be a keeper."* **That rule does not reach this case, because neither half of it is
true here.** The gates do not regress — they are identical to the cell. And structural
integrity does not measurably improve: the arm is byte-identical in the two gated years and
changes nothing at all in the third. A keeper promotion re-keys the ISO's whole registered
set and prunes the outgoing keeper's bundle (rule 35), and here it would do that to install
a run whose dispatch is **the same bytes** in 2/3 years.

**The case FOR promoting.** It is a genuine rule 14 `[R-ACCURATE]` / rule 25
`[R-ISO-SCOPE]` input repair with **zero free parameters and zero `ScenarioConfig`
fields**. For 744 hours where SOCO has no measured price of its own, the model currently
charges **Texas rail economics**, and SOCO's own market's receipts are the right input. The
pool that replaces it is **deeper** than the default (3 reporters vs 2), **nothing is
gap-filled** (0 NaN-filled months either side), there is **no circularity** (the
leave-one-out value excluding Daniel is identical, because Daniel files nothing that month),
and it **moves toward truth without overshooting** (2.3941 against Daniel's own February
3.4190 — about 39 % of the gap closed). Rule 1 says a structurally-correct mechanism is not
judged by the residual.

**The case AGAINST.** Its value *today* is 744 hours of one plant in a year whose C1 rows
are SKIPPED, and it does not change a single scored or reported number anywhere. The
determination does not move. SOCO's headline defect — 2023 `CT_PEAKER` at +9.73 TWh — is
untouched, and its diagnosis across four lanes is absent commitment physics, which no
fuel-price lever reaches. The matrix cell already said `I`, and the honest reading of this
lane's result is that **the cell was right**.

**THE BETTER FORM, if you want the mechanism.** Arm SOCO in
`src/market_sim/pipeline/backcast_config.py:1799` beside NWPP —
`coal_prb_proxy_own_iso=(iso.upper() in ("NWPP", "SOCO"))` — so it is a **declared posture**
that regenerates for every future SOCO solve and every future gap-month, rather than a
recipe detail carried by one run. I verified the two arming routes are equivalent at the
solve (both resolve the same config and move the cache key the same way:
`63cf200dd91f6ad9` → `6e9a1c9f088e1f23`). **That is a source change, so it needs its own
PR**, and this run is already its complete A/B evidence — three years, byte-identical where
it should be, no gate movement anywhere. **A posture armed in source but not carried by the
registered keeper would be the drift rule 24 `[R-REGISTRY]` forbids**, so if you take that
route the keeper should be re-solved on it at the ISO's next natural cadence rather than
promoted now for this alone.

**If you promote anyway** (your call, and it is a defensible one on rule 14 grounds): rule
35 `[R-PROMOTE]` binds, the year union is already enumerated **before** any prune (rule
35(b)) — SOCO's registered years are exactly **{2023, 2024, 2025}** over the keeper plus
this candidate, no folded touchpoints, no dangling `holdout.keeper`, and this run covers all
three, so **the promotion shrinks nothing**. Order: capture the lineage diff while both
bundles are on disk, write the id into `frontend/data/backcast/keepers/SOCO.json` (declaring
the E11 `prb_overrides` recipe diff in the promotion prose, §7.2), run `audit_keepers
--check --iso SOCO`, rebuild `build_status.py --iso SOCO`, re-stamp the SOCO matrix shard
and its §5.8 prose header, and **only then** `scripts/prune_iso_runs.py --iso SOCO
--force-uncite`. `calibration-complete.json` needs no change — SOCO has never had an entry.

**Three questions beyond the promotion:**

1. **May SOCO's bench be rebuilt?** It does not carry nyiso-240's repair (+2.616 TWh).
   Rebuilding re-scores the keeper. Not a lane's call.
2. **E13 has now fired on FIVE consecutive SOCO candidates** (§7.1). Is a `candidate: true`
   sidecar field worth adding?
3. **Should `coal_prb_proxy_own_iso` be reconsidered as a shared default rather than a
   per-ISO arm?** There is no ISO for which "price my non-reporting PRB plant on Texas rail
   economics" is the right input. Rules 25 / 28(d) make each arm its ISO's own lane's, which
   is why this lane does not propose it — but the measurement in §9 item 1 suggests the
   question belongs to the desk, with MISO (484 missing plant-months) and SPP (216) as the
   places it would actually bite.

---

## Log entry

## soco-53g — 2026-09-20 — the $9.7/MWh defect that never reaches the LP, and a cell that was already adjudicated

FINDING-soco-53f §9 item 1 commissioned this lane on a measured claim: SOCO's three PRB plants, 6,361.5 MW and 55 % of its coal capacity, priced off the hand-curated ERCOT-only reporter pool at 1.8228/1.7520/1.6147 $/MMBtu against their own 2.6711/2.4982/2.4610 — an under-pricing of 47–52 %, about $9.7/MWh, "three times SOCO-53f's lever, in the opposite direction". Both pooled numbers are correct and reproduce to four decimals. The inference from them is wrong, and for a structural reason: neither pool reaches the LP. In the calibration path apply_coal_supply_pricing writes the proxy onto SOCO's 15 PRB tranche rows and apply_plant_monthly_fuel_prices overwrites it three lines later with each plant's own filed EIA-923 monthly delivered cost, 8,760 of 8,760 cells on every one of those rows in 2023 and 2024. The model prices Miller at 2.1886, Daniel at 3.8505 and Scherer at 3.3945. Rule 14 was already being honoured at SOCO, one layer further down. The mutation-sequence decomposition is exact: step 2 moves 15 rows by 0.958/0.832/1.054 $/MMBtu, step 3 returns 0.000000000000, 0.000000000000 and 0.649940697470.

The solve confirmed the zero-LP prediction and exceeded it. 2023 and 2024 are byte-identical to the keeper — the same sha256 on floors/, dispatch/<y>_P1.parquet, system.parquet and unit_hourly, solved independently in separate containers at a different HEAD whose solve-surface fingerprint had moved, which is itself the cleanest confirmation of the G-DRIFT audit this lane could have produced. 2025 differs in 4 of 657,000 class-hour cells: a 2.2 MW degenerate tie swap between a Georgia CT_PEAKER tranche and a 2.2 MW hydro unit at identical marginal costs, in hours 8098 and 8217 — December, not January — netting to exactly 0.0 MWh. Annual class generation is 0.000000 TWh apart on all 45 class-years, system.parquet is identical in all three years so prices and marginal_emission_rate (0.6255/0.5921/0.6161) do not move at all, and all 21 C1 rows reproduce the keeper's exactly on both the committed and the HEAD-rebuilt bench. Determination NOT-YET (rubric v3.8, PRICE UNSCORED), identical to the keeper on every criterion, grade, caveat count and DOF entry: C1 FAIL on one row of fourteen (2023 CT_PEAKER +9.73 TWh / +4.0pp), C2/C4/C6/C8 PASS, C1 all 13/14 · free 9/10, 0 ledgered and 0 protective caveats, DOF 3/1, zero ScenarioConfig fields and zero free parameters. Rule 17 re-measured on this bundle's own floors npz with a tool first validated against the keeper's fifteen cells: holds in all twelve plant-years, every cell identical, Barry still zero floored hours.

The offer does move and no MW follows. 2,976 unit-hours of Victor J Daniel Jr's four coal tranches carry +7.7512 $/MWh — mean equal to min equal to max — across all 744 January-2025 hours, the one plant-month where SOCO has no measured price of its own, because Daniel filed no January receipt and the nearby-plant fallback did not reach it. Daniel's armed mc of 27.37 $/MWh is still about 29 below the January mean system price of 56.29, so it stays deeply inframarginal. Prediction P3 is falsified in substance: I predicted the lift would displace 0.000–0.141 TWh of COAL_PRB and it displaced exactly 0.000000, because I never checked where those rows sat relative to the price. That check was one join away in the committed bundle and I read both files in the same session for other purposes. It is the same class of error 53f's P9 made — reasoning about a machine's cost without asking where the cost sits relative to the price that clears — and it is now two lanes running. Seven of eight predictions held, including byte-identity in both gated years.

Recorded against the lane, and it leads the write-up: the matrix cell was ALREADY adjudicated I by NWPP-41 on 2026-09-17, and this lane read it only after launching its shards, which rule 28(a) and the SessionStart hook both forbid. 53f routed the lane without checking it either, so the miss is two lanes deep. What makes the work admissible rather than a redo is that it produced new evidence and that evidence corrects the cell: NWPP-41 censused at the plant-YEAR grain and concluded "nothing to arm unless a SOCO PRB plant stops reporting", and that sentence is falsified — all three SOCO plants do file every year, and Daniel still skips one month. The grain that matters is the plant-MONTH, and even that is an upper bound, since Scherer also missed a month and the nearby fallback covered it. Re-censused cross-ISO at the plant-month grain and routed, never adjudicated (rules 25/28(d)): MISO 38 PRB plants and 484 missing plant-months, SPP 29 and 216, NWPP 9 and 180, ERCOT 7 and 181, PJM 2 and 72, SOCO 3 and 2 — so the docstring's "MISO (12), PJM (2), SPP (3–5)" understates the populations badly, and only 2 of the 7 hand-curated COAL_PLANT_SUPPLY plants file anything at all. The recommendation to the owner is NOT to promote this run, on the ground that the standing "structure improves, gates regress" rule does not reach it — the gates do not regress and structural integrity does not measurably improve — but to arm the mechanism as a declared posture in backcast_config.py beside NWPP if it is wanted, for which this run is already the complete three-year A/B evidence. Three per-year shards under rule 36, each pushing a full 16-file bundle, composed at zero LP with no re-solves; every leg recoverable by immutable SHA and recorded in .gitignore, so a promotion costs nothing. All three shards archived. Record: `docs/handoffs/FINDING-soco-53g-2026-09-20.md`.
