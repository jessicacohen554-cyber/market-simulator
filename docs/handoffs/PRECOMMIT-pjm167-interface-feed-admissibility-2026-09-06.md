# PRECOMMIT — pjm-167 F2: a published transfer limit is enforced only if its own flows respect it

**Session:** pjm-167 · **Date:** 2026-09-06 · **HEAD at writing:** `beb74f0f5`
**Branch:** `claude/pjm-price-cc-regular-review-al60pj`
**Evidence:** `results/calibration/FINDING-pjm167-input-clock-2021-2022-2026-09-06.md` §2
**Keeper (control):** `2026-08-15-pjm-162-inputclock` / `pjm_debugb_inputclock_A`

Written **before any LP is solved**, per rule 29 `[R-SCREEN]`. Every threshold and gate below is
fixed here and is not revisable after a result is seen.

---

## 1. The defect and the change

`pjm_east_interface_cut` caps Flow(Central_PA→EMAAC) + Flow(SWMAAC→EMAAC) at PJM's published
hourly "Average Eastern" limit, and `pjm_measured_interface_limits` applies the same series to
Central_PA→EMAAC per-link. Both are armed in the PJM keeper. **The feed changes basis across the
2023 boundary** (FINDING §2.2): pre-2023 it posts a near-static seasonal limit-set value — **one**
distinct value across all of 2020, 85 across 2021 — and from 2024 the hourly-averaged TLC the
mechanism's docstring describes (8,767 distinct values). Enforced verbatim, the early vintage is a
hard LP bound **below flows PJM actually carried**: the measured flow exceeds the posted limit in
**27.9 %** of 2021 hours by up to **5,242 MW**, against **0.0 %** in 2024 and 2025.

**The change.** `ScenarioConfig.pjm_interface_feed_admissibility_gate` (bool, default False). When
armed, each series is judged against its own measured flows by
`transfer_interface_limits.interface_series_admissibility`; a series that fails is not enforced
that year — the joint cut returns all-`+inf` (non-binding) and the per-link overlay drops the
series from that link's stack, so the links keep their static per-link TTCs. That is **the posture
a forecast year already takes**, not a new number.

- **Zero fitted scalars.** The test reads the clean datatype's own `transfer_mw` against its
  `limit_mw`. The schema reserves that column for exactly this — *"carried ONLY for crosswalk
  sanity checks (binding frequency / flow direction), never as a dispatch target"*.
- **Rule 14 `[R-ACCURATE]`'s NAMED EXCEPTION**, not a licence to drop measured data: the two
  vintages are "a different time/area aggregation" under one series name.
- **Loud, never silent.** The fall-through logs at WARNING with its full arithmetic. This is the
  distinction pjm-119 draws: a *recorded* degradation under a declared gate, not an overlay that
  silently no-ops while the attestation still claims it.

## 2. The bar, declared ex ante

`PJM_INTERFACE_FEED_MAX_EXCEEDANCE_FRAC = 0.05`. **Never swept** (rule 29 clause (c)). 5 % is the
conventional materiality bar; **the partition it produces is identical for any threshold in
(2.1 %, 17.5 %)** — an eightfold range — so no result selects it.

## 3. Measured footprint, all ten series × seven years (zero LP, before any solve)

Exceedance = share of covered hours where the measured flow exceeds the posted limit.
**`*` = inadmissible at the declared bar.** The six series the model actually consumes
(`constants.PJM_INTERFACE_LINK_MAP`) are in **bold**.

| series | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 |
|---|---|---|---|---|---|---|---|
| **Average Eastern** | 1.6 | **18.7\*** | **27.9\*** | **17.5\*** | 2.1 | 0.0 | 0.0 |
| **Average Western** | 1.0 | **6.2\*** | **6.7\*** | **9.7\*** | 0.5 | 0.0 | 0.0 |
| **Average Central** | 0.5 | 1.0 | 1.2 | 2.5 | 0.0 | 0.0 | 0.0 |
| **AP-South Pre-Contingency** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| **AP-South Post-Contingency** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| **Bedington-BlackOak Pre** | 0.0 | 0.0 | 0.9 | 0.0 | 0.5 | 1.0 | 0.2 |
| **Bedington-BlackOak Post** | 0.0 | 0.0 | 0.6 | 0.0 | 0.0 | 0.0 | 0.0 |
| **AEP/DOM Post-Contingency** | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| 50045005 Post-Contingency | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |
| Cleveland | 0.1 | 0.0 | 5.1\* | 1.9 | 0.4 | 0.0 | 0.0 |

**This is the case for the gate being a real test rather than a blunt "distrust old data" rule.**
Every *named flowgate* clears in every year, 2019–2022 included; only the three **"Average"
regional envelopes** — precisely the aggregate one would expect to be posted as a seasonal
limit-set rather than an hourly TLC — fail, and Central never does. `Cleveland` is the one
borderline call (5.1 % in 2021) and **it is consumed by no link**, so no armed mechanism depends
on where the bar sits relative to it.

**Consequence, fixed here before the solve:** under the gate exactly **two** consumed series fall
through, in exactly **three** years (2020–2022) — Average Eastern and Average Western. Nothing
changes in **2019 or 2023–2025**, on any link. **Every committed backcast keeper is byte-identical
under this gate**, which is why the in-sample protective re-solve F1 needs is not needed here.

## 4. Pre-registered STOP gates — structural only

Arm-vs-control on the same HEAD, **2021**. Screen year 2021 is chosen on **footprint** (the
largest exceedance, 27.9 %), not on residual. The screen may **kill** the arm; it may never
promote one, and it is never gated on the target residual.

| # | gate | pass condition | why it is structural |
|---|---|---|---|
| **H1** | the identity it asserts | arm's Average Eastern + Average Western caps are `+inf` / static for all 8,760 h; every other mapped series byte-identical to control | the mechanism must drop exactly the two series it names and no others |
| **H2** | the artifact is gone | arm EMAAC slack **= 0 MWh** (control 99,100 over 74 h) | the claim is that the VOLL is the cut's artifact; if slack survives, it is not |
| **H3** | direction | arm EMAAC−rest annual price wedge **< +$10/MWh** (control +$34.50; actual −$5.43) | the sign, not the level, is the claim |
| **H4** | footprint confined | zones other than EMAAC/West_APS/Central_PA move < 2 % in annual energy; `nuclear`/`wind`/`solar`/`hydro` < 1 % | the gate touches two links |
| **H5** | no non-target load-bearing flip | C1, C2 and C4 do not go PASS → FAIL on 2021 | protective; **C3a/C3b are the TARGETS and are NOT gated** |
| **H6** | in-sample inertness | a 2023 arm is **bit-identical** to the keeper's committed 2023 `hourly/` sidecars | §3 says no consumed series fails in 2023; this proves it in the solve path rather than asserting it |

**Kill rule.** Any of H1–H6 failing ⇒ the arm is dead and that is the session's result.

## 5. Ordering — F2 is screened AFTER F1

F1 (the fleet vintage) and F2 act on the **same pocket**: F1 restores ~10 GW of coal registry and
the MAAC-area units, F2 releases the EMAAC import bound. Screened together they confound. The
order is F1 first, then F2 on top of whatever F1 leaves.

## 6. BLOCKER — the screens cannot be run in this container

**No PJM per-plant LP fits.** Three attempts, all OOM-killed by the kernel:

| attempt | configuration | outcome |
|---|---|---|
| 1 | arm + control concurrently (rule 12's "~2 simultaneous") | both killed, at 7.7 GB and 13.9 GB anon-rss |
| 2 | control alone | killed at ~14 GB |
| 3 | control alone + `MALLOC_ARENA_MAX=2`, single-threaded BLAS/OMP, caches dropped | **killed at 13.96 GB** |

The container has **16.0 GB total / ~15.4 GB available**, and PJM 2021 (≈3,300 per-plant units ×
8,760 h, plus the DA-virtual pseudo-units) peaks above it. **This is an environment limit, not a
model defect**, and per CLAUDE.md's GitHub-Actions rule the correct response is to say so and ask
the owner, never to move the solve onto a billed runner. **Rule 12's "cap at ~2 simultaneous for
per-plant multi-zone LPs" does not hold here: the cap on this box is zero.**

Everything in §3 and in FINDING §§2–3 is zero-LP and stands regardless. What is blocked is
exactly the arm/control screens for F1 and F2 — i.e. the gates above and in
`PRECOMMIT-pjm167-fleet-vintage-screen-2026-09-06.md` §4. Both mechanisms therefore stay
**default-OFF and unarmed**, which is where they must stay until a screen clears them.

**To resume:** a box with ≥24 GB for PJM, then F1's screen, then F1's in-sample protective
re-solve of 2023–2025, then F2's screen on top. The 2021 DA-virtuals corpus this session
re-fetched (`data/raw/pjm-da-virtuals/hrl_da_incs_decs_2021_*.parquet`, gitignored) must be
re-fetched there too — `scripts/data/fetch_pjm_da_virtuals.py --years 2021`, ~4 min.
