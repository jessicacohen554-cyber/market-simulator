# FINDING — capx D72: a pre-declared STOP fired on leg 1, the cause is bisected to a hunk and a digit, and four of the seven keys are settled at ZERO LP by a proof the STOP cannot touch

**Lane:** capx D72 — the PRE-HUNK RE-SOLVE CAMPAIGN routed by D60-R3
(`FINDING-capx-d60-2026-09-05.md` §8-blast-radius / §9). Pre-declaration
`PREDECL-capx-d72-prehunk-2026-09-06.md`, pushed at `3d2f4dbb` **before any solve**.
**Branch:** `claude/capx-d72-prehunk-resolves`, rebased to `origin/main` **`a663cf6f`**.

> **Name collision, recorded because it nearly cost a file.** A DIFFERENT lane also carries the
> label "capx D72" — `claude/capx-d72-carbon-floor-blast-radius`, whose
> `FINDING-capx-d72-2026-09-06.md` (448 lines, `6e5d7b88`) is the G-C1 carbon-nulling blast
> radius. This lane's documents are therefore suffixed `-prehunk-`. The collision was caught by
> a `git status` read before committing — the pre-existing file showed as `M`, not `??` — and
> the other lane's file was restored byte-identical (448 lines in, 448 out) before anything was
> staged. Rule 27 `[R-PUSH]` in its plainest form: check what is already there before you write.

---

## 0. Verdict (one paragraph)

**Four of the seven PRE-hunk keys are PROVED INERT against capx D55's
`_floor_retention_merit` hunk at zero LP, and that proof is final. The remaining three cannot
be re-solved against the charter's reference, because the reference moved out from under the
campaign while it was being written.** Leg 1 (`neiso-t1f`) solved clean at HEAD — 5/5 years,
10.0 min, 0 FAIL / 0 WARN over 14 invariants, realized key `18515067bf4d2fbe` exactly as
pre-declared, HEAD guard OK — and its 2027 NEISO ledger landed on **neither** pre-declared
side. **Pre-declared STOP 3 fired.** It is not a second `_floor_retention_merit` hunk: a
code-vs-data probe (D65 §3c's own instrument) proves the drift is **CODE**, and a three-probe
bisect names the boundary as **`ad45b0e4` (PR #4970, SCN-LOAD)**, whose
`DEMAND_GROWTH_RATES["NEISO"]["low"]["near"]` re-derivation **0.007 → 0.004009** lowers the
forecast peak, lowers the adequacy requirement, and lets the reliability floor admit four more
retirements. **SCN-LOAD declared this staleness itself** (its §6 item 2) and routed the
cache-epoch entry it may not write; this lane is the first to *measure* it on a forecast
solve. Nothing was registered, and no keeper, shard, marker, freeze, default, parameter value
or matrix cell moved.

---

## 1. STOP 1 — every one of the seven keys held, twice

Resolved through the harness path (config construction only, no solve) at `c5786dfa`, and
again after the rebase to `a663cf6f` — a window carrying **91 commits** including
`scenarios.py` +244, `constants.py` +163 and a new `policy/voluntary_demand.py`:

| bare key | pin (D60 §R3.2) | at `8bc588a2` | at `a663cf6f` |
|---|---|---|---|
| `ercot-t1f` | `0c3e9cd5b5993bdf` | HIT | **HIT** |
| `neiso-t1f` | `18515067bf4d2fbe` | HIT | **HIT** |
| `ercot-t1h` | `82b27751be747552` | HIT | **HIT** |
| `caiso-t1h` | `7da58199acd362ee` | HIT | **HIT** |
| `miso-t1h`  | `687bd75f2828bea1` | HIT | **HIT** |
| `nyiso-t1h` | `6e70a637b3465542` | HIT | **HIT** |
| `neiso-t1h` | `f3988df3068020d1` | HIT | **HIT** |

**Seven of seven, both times.** This is worth stating plainly because it is the *reason* the
STOP below matters: **the cache key is not a staleness detector.** Every new field in that
91-commit window is cache-neutral at its default, and the change that actually moved the model
is a `constants.py` scalar, which the key never hashed in the first place.

---

## 2. The zero-LP inertness proof — four keys settled, and settled PERMANENTLY

Full construction, census and controls: `PREDECL-capx-d72-prehunk-2026-09-06.md` §2. In brief:
`_apply_reliability_floor` is a greedy loop over `sorted(eligible, key=_floor_retention_merit)`
that `break`s when the requirement clears, and the admission-cap site (`retirements.py:2656`)
emits `entry_capped` for each unit it un-retired and `decided` for each it did not. So the
retention **order** is observable in a year **only** if the loop broke mid-way — if it
un-retired nothing (`entry_capped == 0`) or everything (`decided == 0`), the outcome set is
identical under every order, and the fleet entering the next year is identical, so the
argument composes across the horizon by induction.

| key | per-year `capped`/`decided` (floor_retained = 0 throughout) | verdict |
|---|---|---|
| **`ercot-t1f`** | 26: 0/0 · 27: 377/0 · 28: 11/0 · 29: 1/0 · 30: 1/0 | **INERT** |
| `neiso-t1f` | 26: 0/0 · **27: 292/30** · 28–30: 0/0 | NOT inert |
| **`ercot-t1h`** | 21–25: 0/0 (no pipeline events at all) | **INERT** |
| **`caiso-t1h`** | 21–25: 0/0 | **INERT** |
| `miso-t1h` | 21: 0/0 · **22: 405/5** · 23: 385/0 · 24: 415/0 · 25: 0/0 | NOT inert |
| **`nyiso-t1h`** | 21–25: 0/0 | **INERT** |
| `neiso-t1h` | 21: 0/0 · 22: 0/22 · 23: 0/0 · **24: 187/52** · 25: 0/0 | NOT inert |

Three guards, all checked so the proof is not vacuous: `floor_retained` is a **live** field
(3 of 416 committed ledgers carry a non-empty one); **nothing else consumes the merit order**
(three references in live code — the sort, the log's *values*, and an unimported re-export);
and under `retirement_rule="pipeline"`, which **all seven** bundles use,
`apply_economic_retirements` returns early into `_apply_pipeline_retirements` (line 3619), so
the two `floor_retained` sink writes are **mutually exclusive** and neither can overwrite the
other. Validated on both controls: D55's own known-inert `miso-t1h-d46` reads retained-all
(1497/0, 948/0); the known-moving `neiso-t1f` is flagged at **2027 and only 2027** — exactly
where D65 measured the drift, with 2026 and 2028–2030 reading inert exactly where D65 measured
byte-identity.

> **Why this survives everything below.** The proof is computed from committed ledgers and
> HEAD source. It never solves, so it cannot be confounded by drift, and it does not need
> re-doing when HEAD moves again. **The D55 question is closed for these four keys, for good.**

### 2.1 A correction to the §8-blast-radius residue table, restated because it is now load-bearing

D60-R3 annotates `miso-t1h` **"(measured INERT by D55)"**. That citation is wrong.
D55 measured the **`…-t1h-d46`** bundle inert (`eff2c890746ec966`); the bare `miso-t1h` key
points at **`…-t1h-d53-sectorgate-d51ratio`** (`6ea92547eaa62559`), whose lineage D55 §2.3
measured as the case where the floor **does** release a suffix (477.4 MW committed, 278.6 MW
certain under the fixed key). The census above reproduces that shape (2022: 405/5). **The one
key the residue table said needed no work is one of the three that does.**

---

## 3. Leg 1 — solved clean, and STOP 3 FIRED

```
python3 scripts/run_full_horizon.py --iso NEISO --start-year 2026 --end-year 2030 \
    --golden-posture --out-dir results/ff-t1f-d72/neiso
```
5/5 years, 10.0 min, 3.28 GB peak, 14 invariants **0 FAIL / 0 WARN**, realized key
`18515067bf4d2fbe` (**pre-declared, HIT**), HEAD guard OK at `a663cf6f`.

| 2027 NEISO | rows | total MW | `reserve_margin` | `fleet_by_fuel_after.gas_cc` |
|---|---|---|---|---|
| PRE-hunk (committed `9e48ff6`) | 33 | 2,369.81 | 0.045867 | 10,713.80312 |
| POST-hunk (D65 HEAD ctl) | 40 | 2,244.89 | 0.050821 | 10,838.72120 |
| **D72 leg 1 (this HEAD)** | **44** | **2,758.32** | **0.047594** | **10,326.84583** |

Neither side. **STOP 3 fires exactly as pre-declared** — and the pre-declaration's own
expectation ("the 2027 ledger lands on the POST-hunk side, to the digit") is a **MISS, graded
against myself at full magnitude**. What the pre-declaration got right is that it named a
falsifier precise enough to catch this on the first leg instead of after three.

---

## 4. The diagnosis — CODE, not data; and the hunk named to the digit

### 4.1 Code vs data, settled first (D65 §3c's instrument)

I had regenerated `data/clean` in this session (§7 defect 3), and `cache_key` hashes config
only, **never data-file state** — so "my data differs" was the cheaper hypothesis and had to
die first. D65's basis tree (`git archive e5ac39f1b2a6 src scripts configs`) was solved for
NEISO 2026–2027 through `MARKET_SIM_DATA_ROOT` against **this session's regenerated data**:

| 2027 | rows | MW | rm | gas_cc |
|---|---|---|---|---|
| POST-hunk (D65 HEAD ctl, committed) | 40 | 2,244.89 | 0.050821 | 10,838.72120 |
| **PROBE — D65 source + THIS data** | **40** | **2,244.89** | **0.050821** | **10,838.72120** |

**Identical on every key.** The regenerated clean tree is faithful, and the entire divergence
is inside `src/` + `scripts/` + `configs/` — the only trees the archive replaces.

### 4.2 The bisect — three probes, 23 candidates

Same harness, source tree swapped, data held constant. Window `e5ac39f1b2a6..a663cf6f` carries
**23 first-parent merges touching `src/market_sim/`**.

| probe | commit | 2027 | side |
|---|---|---|---|
| 1 | `ad45b0e4` (idx 11, midpoint) | 44 / 2,758.32 / 0.047594 / 10,326.846 | **DRIFTED** |
| 2 | `bb2ae3d9` (idx 9, capx D62) | 40 / 2,244.89 / 0.050821 / 10,838.721 | **POST (good)** |
| 3 | `9249b507` (idx 10, SCN-WS1c carbon floor) | 40 / 2,244.89 / 0.050821 / 10,838.721 | **POST (good)** |

`9249b507` and `ad45b0e4` are **consecutive** first-parent commits touching `src/market_sim/`
(verified by `git log --first-parent 9249b507..ad45b0e4`, which returns exactly those two).
**The boundary is `ad45b0e4` — PR #4970, `scn-load-forecast-intake` (SCN-LOAD).**

*Recorded against myself: my named prime suspect going in was SCN-WS1c's carbon floor
(`max(RFF path, program trajectory)` on an RGGI ISO). Probe 3 refutes it. The hypothesis-led
probe was still the right call — it was also the interval's midpoint — but the reasoning that
picked it was wrong and is reported as wrong.*

**Probe 3 is independently corroborated by the other D72 lane, through a different
instrument.** `FINDING-capx-d72-2026-09-06.md` (the G-C1 carbon-nulling blast radius,
`6e5d7b88`) reaches the same verdict with **zero LP**: the pre-repair nulling predicate
exempted `carbon_price_path="zero"` by literal enumeration, **all 110 tracked
`run_config.json` files carry that value**, so `b1996141` changes the effective carbon price
by **$0.00 in every solved year of every committed bundle**. A content census and a 4.5-minute
solve, agreeing exactly: the carbon floor is inert on everything committed.

### 4.3 The hunk, in words and in digits

`ad45b0e4` touches exactly two files under `src/`: `config/constants.py` (+554/−263) and
`data/datacenter.py` (+82). Under owner ruling S4 / card D-4 it **re-derives
`DEMAND_GROWTH_RATES` from the newly curated `load-forecast` datatype** instead of transcribing
hand estimates. For the leg:

| `DEMAND_GROWTH_RATES["NEISO"]["low"]` | `near` | `long` |
|---|---|---|
| before (`9249b507`) | **0.007** | 0.007 |
| after (`ad45b0e4`) | **0.004009** | 0.007759 |

2027 is a `near` year (≤ `DEMAND_GROWTH_TRANSITION_YEAR` = 2030), so NEISO's near-term growth
**falls 0.700 %/yr → 0.4009 %/yr**. The causal chain, end to end, and every link is in the
measured direction:

> lower near-term growth → lower forecast peak → lower
> `peak × (1 + PLANNING_RESERVE_MARGIN)` adequacy requirement → the reliability floor needs to
> un-retire **fewer** units to clear it → **more** retirements admitted (40 → 44 rows,
> **+513.4 MW**) and a **lower** post-floor reserve margin (0.050821 → 0.047594), with
> **511.9 MW less gas_cc** surviving.

### 4.4 Blast radius — 6 of 6 ISOs, all three cases, both eras

| ISO | `low` near | `mid` near | `high` near |
|---|---|---|---|
| CAISO | 0.015 → 0.017371 | 0.028 → 0.032425 | 0.042 → 0.048638 |
| **ERCOT** | 0.05 → 0.019388 | 0.085 → 0.134813 | **0.115 → 0.206157** |
| MISO | 0.018 → 0.029732 | 0.031 → 0.054816 | 0.045 → 0.082546 |
| NEISO | 0.007 → 0.004009 | 0.013 → 0.007446 | 0.022 → 0.012601 |
| NYISO | −0.0024 → −0.001611 | 0.0122 → 0.011815 | 0.0263 → 0.025754 |
| PJM | 0.02 → 0.035914 | 0.036 → 0.064645 | 0.06 → 0.107742 |

Every ISO, every case, both `near` and `long`. **Every committed forecast bundle in the
repository is stale against HEAD at an unchanged cache key** — a staleness of exactly the class
D60-R3's §8-blast-radius was chartered to close for D55, arriving from a different mechanism
while that campaign was being executed.

### 4.5 This is DISCLOSED, INTENTIONAL and CORRECT — and this lane does not touch it

`FINDING-scn-load-2026-09-06.md` §6 item 2 declares it in terms this lane can only confirm:
*"every forecast-mode bundle in ERCOT, PJM, MISO, CAISO and NEISO solved before this commit is
stale at the same cache key … NYISO forecast bundles move only ~0.2 % but are not
byte-identical and should be treated as stale too. NO BACKCAST BUNDLE IN ANY ISO IS
AFFECTED"*, and it routes the owed `results/cache.py` epoch entry to SCN-DESK as another
lane's region. It is a **rule 14 `[R-ACCURATE]`** improvement — published CELT 2026 / LTLF /
Gold Book forecasts replacing flat transcribed estimates — and the same rule forbids reverting
it because a downstream comparison got harder. **Named, confirmed, measured, and not touched**,
exactly as this lane treats D55's hunk.

**What this lane adds to that disclosure:** SCN-LOAD declared the scope; it did not measure a
forecast bundle's ledger. Leg 1 is the **first measurement** — for NEISO 2027, +4 retirement
rows / +513.4 MW / −511.9 MW surviving gas_cc / −0.0032 reserve margin. The move is material,
so the epoch entry SCN-LOAD routed is owed on evidence, not merely on principle.

---

## 5. What this does to the charter — stated rather than worked around

The campaign's object was: *does a bundle solved before D55 reproduce at HEAD?* That question
is now **unanswerable by re-solving at HEAD**, because a re-solve confounds D55's ordering hunk
with SCN-LOAD's demand re-derivation, and the second effect is the larger one. Concretely:

- **The four inert keys are DONE and are immune** (§2). Their proof never solves.
- **The three remaining keys cannot be closed under this pre-declaration.** My §4 expectations
  are spent and one is already falsified; re-declaring them against the SCN-LOAD side inside
  the same session would be writing the pre-declaration after seeing the answer, which is the
  one thing a pre-declaration exists to prevent.
- **The four "inert" keys are still stale at HEAD** — for the SCN-LOAD reason, not the D55 one.
  §2.4 of the pre-declaration scoped the claim to D55 *before* any of this was known, and that
  scoping is what keeps it honest now: **INERT against D55 ≠ reproduces at HEAD**, and no
  RENAME-grade note in this lane says otherwise.

**Leg 1's bundle is deleted and not registered.** It is a correct bundle for `a663cf6f`, but
registering it would (a) publish a determination under a pre-declaration its own leg falsified
and (b) leave an unregistered-or-mis-registered bundle dir on `main`. Every number it produced
is in §3 and §4 — the doc is the record and git history is the record for the bytes, the same
discipline rules 15 `[R-DASHBOARD]` and 29(c) `[R-SCREEN]` state.

---

## 6. Routed

1. **The SCN-LOAD forecast blast radius, now measured.** The `results/cache.py` epoch entry
   SCN-LOAD §6 item 2 routed to SCN-DESK is owed, and this finding supplies the magnitude for
   at least one ISO. **Every registered forecast run on the board — t1f, t1h, t1x, t3 — is
   stale against HEAD.** This is a strictly larger blast radius than D55's and it subsumes it:
   §8-blast-radius's 28 PRE-hunk bundles are now **all 33** stale, on a different axis.
2. **capx D72's three remaining keys** (`neiso-t1f`, `miso-t1h`, `neiso-t1h`) need a **re-based
   charter** with a pre-declaration written against the SCN-LOAD side. Four of the original
   seven are permanently discharged (§2), so the re-charter is 3 legs, not 7.
3. **D65 §3d's floor-diagnostic gap is STILL OPEN at HEAD** and was re-confirmed here:
   `retirements.py:2656` calls `_apply_reliability_floor` with no assignment target while
   `:2704` and `:3666` assign it, so `floor_retained` is blind to the admission-cap pass. §2's
   census had to reconstruct that pass from `pipeline_events` for exactly this reason.
   Capturing the return would make the whole §2 proof a one-line ledger read.
4. **The cache key is not a staleness detector, and this is now twice-demonstrated** (D55's
   ordering hunk, SCN-LOAD's constants). Both moved every forecast bundle at an unchanged key;
   both were found only because a lane happened to re-solve. Whatever the epoch ledger becomes,
   the recurring cost is real.

---

## 7. Environment — THREE defects, one of them new

D60-R3 §R3.5 records two; a third cost this lane a failed leg.

1. **The scientific stack was ABSENT, not merely off-pin.** `pip install -r requirements.txt`
   aborts on a Debian-owned PyYAML (`Cannot uninstall PyYAML 6.0.1, RECORD file not found`) and
   leaves `import numpy` failing. Repaired with `pip3 install --ignore-installed PyYAML -r
   requirements.txt`; verified at the pins — python 3.11.15, highspy 1.14.0, numpy 2.4.6,
   scipy 1.17.1, pandas 3.0.3, pyarrow 24.0.0, pydantic 2.13.4, byte-for-byte the stack the
   committed controls record.
2. **The clone was SHALLOW** — deepened 666 → 3,522 first-parent commits.
3. **NEW: `data/clean` is derived + gitignored and absent on a fresh checkout**, so leg 1's
   first attempt died 50 s in (`confirmed-retirements: clean partition for NEISO is absent`).
   Regenerating it needs **`PYTHONPATH=.:src`** — with the repo root alone, as
   `regenerate_clean.py` sets internally, **45 of 56 curations fail** on
   `ModuleNotFoundError: market_sim`, silently, one per datatype, while the script still exits
   0. Worth a repair in the script itself: it already builds an env for its children and only
   needs `src` added to it.

**`uv run` is not usable here** — it builds an empty `.venv` (`--no-sync` → no numpy), so every
command ran under the system `python3` at the verified pins (D60-R3's pip-forced precedent).

---

## 8. Governance attestation

| gate | reading |
|---|---|
| rule 12 `[R-PARALLEL]` | one solve at a time; legs sequential; peak RSS 3.32 GB against 15 GB |
| rule 21 `[R-DOF]` | **no parameter value chosen anywhere in this lane** |
| rule 22 `[R-HOLDOUT]` | every solved year 2026–2027 / 2026–2030, `mode="forecast"`; no measured actual touched |
| rule 24 `[R-REGISTRY]` | no off-registry knob; no `ScenarioConfig` field added or changed |
| rule 25 `[R-ISO-SCOPE]` | no ISO's value identifies another's; nothing transferred |
| rule 27 `[R-PUSH]` | no existing ≥300-line source file rewritten; docs added, not regenerated |
| rule 28 `[R-MECH-MATRIX]` | **no cell moved — this lane tested no mechanism.** It re-measures existing recipes across hunks it names and does not touch |
| keeper / shard / marker / freeze / default | **none touched** |
| registration | **none.** Leg 1 hit a pre-declared STOP and was not registered |

**Both hunks this lane names — D55's `_floor_retention_merit` and SCN-LOAD's
`DEMAND_GROWTH_RATES` — are correct repairs of real defects, and both are left exactly as they
are.** Naming a hunk is not adjudicating it.

---

## 9. Every prediction, graded

| # | pre-declared | outcome |
|---|---|---|
| P1 | all seven keys resolve to their D60 §R3.2 pins | **HIT** — 7/7, twice (`8bc588a2`, `a663cf6f`) |
| P2 | four keys provably inert at zero LP | **HIT** — proof + two controls (§2) |
| P3 | leg 1 realizes key `18515067bf4d2fbe` | **HIT** |
| P4 | leg 1's 2027 lands on the POST-hunk side, to the digit | **MISS** — landed on a third side (§3) |
| P5 | leg 1 2026 byte-identical to the committed bundle | **NOT ASSESSED** — superseded by P4's STOP before it was read |
| P6 | determination stays PROMOTE | **NOT ASSESSED** — not scored under a fired STOP |
| P7 | STOP 3 catches a second hunk if one exists | **HIT — it caught drift on the first leg**, which is what the falsifier was for, even though the drift is not a second `_floor_retention_merit` hunk |
| P8 | `miso-t1h` is not inert despite the residue table's note | **HIT** (§2.1) |
