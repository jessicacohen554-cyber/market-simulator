# FINDING — the 2019-2022 retiree window is **NOT** inert in 2023-2025: 720 MW of coal that retired in May 2020 is dispatchable in PJM's 2023

**Session:** `pjm-fuelvintage-1`, 2026-09-09. **ZERO LP** — six `run_year(fleet_only=True)`
rebuilds and two parquet reads.
**Status: a defect in commit `7934e92c`, found before any solve was spent. Reported and routed,
NOT unilaterally repaired — see §5.**
**Audience: ALL FIVE ISO LANES of the xiso-fuelvintage program, not just PJM.**

---

## 1. The claim that fails

Commit `7934e92c` moved `RETIREMENT_WINDOW_START` from 2023 to 2019 and rebuilt
`data/raw/eia-860/eia860_generator_retired_within_window.parquet` additively (477 → 1,094 units).
Every downstream document asserts the same thing:

> "**Zero effect on 2023-2025 by construction.**"
> — `docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md`, the landed-changes table;
> repeated in `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §2 and in every one of
> the five per-ISO prompts ("ZERO in 2023-2025", "Card A is inert here").

PJM's own prompt (CARD 2) says **"PROVE IT"** rather than assert it. Proved, it is false.

## 2. What was measured

The PJM 2023 fleet was built twice off the committed keeper recipe
(`results/calibration/pjm_debugb_inputclock_A/meta.json`), differing **only** in which retiree
parquet `paths.active_eia860_dir` serves: the committed 2019-2022 artifact, versus a copy filtered
to `planned_retirement_year >= 2023` — byte-equivalent to the pre-`7934e92c` artifact. Nothing
under `data/raw` was modified; the alternate vintage is a temp directory of symlinks.

| PJM 2023 | 2019-window (HEAD) | 2023-window (pre-`7934e92c`) |
|---|---|---|
| LP rows | **3,789** | **3,407** |
| rows present only at HEAD | **382** | — |
| rows lost | 0 | — |

**The 382 injected dead rows are themselves perfectly inert — that half of the claim holds
exactly:**

| the 382 extra rows | value |
|---|---|
| nameplate `pmax` sum | 12,213.775 MW |
| **effective MW-h (`pmax × availability`) over 8,760 h** | **0.0000000000** |
| max effective MW in any hour | **0.0000000000** |
| max availability | **0.0000000000** |

**But the 3,407 SHARED rows are not identical, and that is the defect:**

| shared rows (3,407) | max abs delta |
|---|---|
| `pmax` | **324.000 MW** |
| `availability` | **0.2958** |
| `mc_base` (the P0 offer the LP solves on) | **0.0927 $/MWh** |
| total effective MW-h | **1,296,024,581.10** (HEAD) vs **1,295,228,131.22** (pre) = **+796,449.88 MW-h**, **+0.0615 %** |

## 3. Root cause — ONE plant, and it is not subtle

Nine of the 3,407 shared rows move. They are all the same plant:

```
plant 2866  W H Sammis (OH, PJM_AEP_Ohio, coal)   9 rows   +720.0000 MW
```

W H Sammis's rows in the retiree parquet:

| units | capacity | retired |
|---|---|---|
| 1, 2, 3, 4 | 4 × 180 MW = **720 MW** net summer, coal (BIT) | **2020-05** |
| 5, 6, 7 + five oil units | 1,503 MW | 2023-06 |

Under the **2023** window only the 2023-06 rows were injected, and they dispatch through June
2023 — correct. Under the **2019** window units 1-4 are injected too. The COD ramp masks them
offline for all of 2023 (their effective MW-h is exactly 0, per §2) — **but the plant-level
binning has already folded their 720 MW into the plant's capacity total, and the tranche split
puts it back onto rows the COD ramp leaves AVAILABLE.** The dead units' capacity is not dropped;
it is *redistributed to their live siblings*.

So the model's PJM 2023 dispatches, as coal in AEP Ohio, **720 MW that stopped existing in May
2020** — and it does so *because* of a commit whose stated purpose was to represent retirements
more accurately. `+720.0 MW` is not a rounding artifact: it is exactly units 1-4.

The `availability` and `mc_base` deltas ride the same plant: `retiree_cems_cap` (keeper flag, ON)
is **plant-keyed** — `rcaps.get(int(gen.plant_code))`, `data/fleet/arrays.py:1500`, applied to
"every dispatch tranche of the (possibly binned) plant" — so widening the retiree set changes
which tranches get capped to a measured CEMS envelope, and the coal passthrough carries that into
the offer.

## 4. Cross-ISO exposure — this is not a PJM curiosity

A plant is exposed when it **gains pre-2023 retiree rows AND still has rows the solve year can
dispatch**. Measured over the committed parquet plus the operable vintage:

| ISO | pre-2023 retiree plants | **EXPOSED** | pre-2023 MW on the exposed plants | plants |
|---|---|---|---|---|
| CAISO | 50 | **1** | **480.0** | AES Redondo Beach |
| ERCOT | 13 | 0 | 0.0 | — |
| NEISO | 24 | **1** | **521.5** | **Mystic Generating Station** |
| MISO | 90 | **3** | **287.8** | Crawfordsville, Elk River, River Rouge |
| NYISO | 17 | **1** | 0.0 | Astoria Gas Turbines |
| **PJM** | 90 | **2** | **1,043.0** | **W H Sammis**, Yorktown |
| SPP | 19 | 0 | 0.0 | — |
| **ALL** | 303 | **8** | **2,332.3** | |

Two notes on how to read that table:

- **It is an upper bound, not the leak.** PJM's exposure is 1,043 MW and PJM's *measured* 2023
  leak is **720 MW** — Sammis only; Yorktown did not move. Each ISO must measure its own rather
  than assume the bound is realised.
- **The "still in the operable vintage" leg is EMPTY for every ISO**, so exposure reduces to
  plants carrying retiree rows on **both** sides of 2023. That is why the set is small: a plant
  in the retiree parquet has, by construction, already left the operable snapshot. **NEISO's
  exposed plant is Mystic** — the very plant the retiree-window machinery was built for
  (`fleet/models.py:147`) — so NEISO should check it first rather than last.

## 5. What this does NOT change, and what it does

**It does not stop the fuel arm.** `gas_electric_power_monthly_level` is a separate, flagged
mechanism; this session's screen and span proceed. But three things follow and all three are
stated rather than absorbed:

1. **No 2023-2025 replay at HEAD is a byte-faithful replay of any keeper solved before
   `7934e92c`.** For PJM that is an *independent* second reason G-CTRL form 4 is void, on top of
   the unresolvable-`git_sha` finding in `PRECOMMIT-pjm-fuelvintage-2026-09-09.md` §2 — and this
   one would have voided it even if every sha had resolved.
2. **The full-span run this lane produces carries TWO deltas against the committed keeper**, not
   one: the declared fuel seam, and this undeclared 720 MW. Any C1 / C2 coal number from it is
   joint until the defect is repaired, and this lane will report it that way.
3. **"Card A is inert in 2023-2025" must be struck from all five prompts** and from
   `FINDING-xiso-fuelvintage-monthly-gas-level-2026-09-09.md` §2. Four other lanes are solving
   right now against a claim that is false for at least three of them.

**Deliberately NOT repaired here, and the reason is not timidity.** The fix belongs in the shared
plant-binning path (`data/fleet/`), so it moves **every ISO's fleet in every year**, including
years no keeper has re-solved. Landing that mid-flight — with this lane's three shards and the
NYISO lane's four shards already solving against HEAD — would invalidate seven in-progress LPs and
silently re-key configs the holdout gates govern. It is an owner-level call about the whole
program's frozen recipe, not a lane's call about its own arm. **Routed to the owner with the
measurement in hand; see the promotion question in this session's final report.**

## 6. Reproduce

```
python3 scripts/probes/_pjm_fuelvintage_retiree_window_effective_mw.py 2023
      # row counts, the effective-MW proof for the 382 dead rows, and the shared-row deltas
python3 scripts/probes/_pjm_fuelvintage_retiree_window_attribution.py 2023
      # the per-plant attribution that names W H Sammis
python3 scripts/probes/_pjm_fuelvintage_ep_level_census.py 2023
      # the companion fuel-seam census (PRECOMMIT SS6/SS6a), same two-build method
```
Each builds the PJM 2023 fleet twice through `run_calibration.run_year(fleet_only=True)` on the
keeper's own recipe, swapping only the retiree parquet via a symlinked temp EIA-860 vintage. No
LP, no write under `data/raw`.

---

## 7. INDEPENDENT CORROBORATION — the CAISO lane found the same defect class, separately

While this was being measured, `caiso-fuelvintage-1` (session `012aNt8CFETU5cCW3EiWzmXf`)
stopped and escalated to the owner with:

> "2019-2022 retiree window: 16 scoring failures remain; **plant-356 COD defect blocks 5 parallel
> lanes**" — needs_action: "choose repair approach: **(a) exclude retiree rows before plant
> latest, (b) per-unit dates on Generator, or (c) bin by (plant, vintage)**"

Two lanes, different ISOs, different symptoms, **same root cause**: the per-plant binning collapses
units that share a plant code but not a retirement date, so a unit's COD cannot be honoured
per-unit. This session reached it through a capacity A/B on W H Sammis; CAISO reached it through
scoring failures on plant 356. Neither knew of the other.

That convergence matters for the repair decision: CAISO's option **(c) bin by (plant, vintage)**
and option **(b) per-unit dates** would both fix the Sammis redistribution, because both stop a
2020 retiree and a 2023 retiree from sharing one binned tranche. Option **(a) exclude retiree rows
before the plant's latest** would also fix Sammis — but by *discarding* the 2019-2022 rows for any
plant with a later exit, which is the opposite of what commit `7934e92c` set out to do and would
silently re-empty part of the window it added. Whichever is chosen, **the fix is one shared repair
serving both lanes, not two.**

## 8. Environment note — PJM cannot be solved in a default container, and why that matters here

Measured in this session while validating the control leg: a PJM per-plant year peaks at
**13.92 GiB anon RSS**, against a `claude-code-bash` cgroup RSS cap of **14,327,676,928 bytes
(13.34 GiB)**. The solve is OOM-killed a few minutes in, leaving an **empty `dispatch/` directory
and a misleading exit code 0** (the code observed is the tail pipeline's, not python's).
Allocator tuning is not the answer — `MALLOC_ARENA_MAX=2` plus single-threaded BLAS moved the peak
by **3 MB** (13.920 → 13.917 GiB), i.e. the peak is real data, not fragmentation.

`memory.memsw.limit_in_bytes` on that cgroup is **unlimited**, so swap counts as headroom and the
container simply ships with none. Adding 3 GB (`fallocate` / `mkswap` / `swapon`) lets the solve
run; it draws ~1.8 GB. This restores the configuration the previous PJM lane solved under —
`PRECOMMIT-pjm177-…-2026-09-09.md` §4 records "13.34 GiB cgroup **+ swap**".

Recorded here because it is a **silent** failure: a lane that trusts the exit code will register a
bundle that was never solved.
