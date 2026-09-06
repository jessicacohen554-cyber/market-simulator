# FINDING — SCN-WS4a: data-centre siting currency (plan §7 "WS-4" items 2 and 5)

**Lane** SCN-WS4a · **Model** Opus (`claude-opus-5`) · **Date** 2026-09-05 ·
**Branch** `claude/scn-ws4a-datacenter-shares-yf7wvi` (the desk's issuance record names the stem
`claude/scn-ws4a-h3zc`; the session was provisioned on the branch above and the harness binds
pushes to it — noted here so the ledger's §5 stem row can be reconciled, no other difference) ·
**Base** `origin/main` at `4db660cb` (rebased mid-session from the desk pin `d01ab8b0`; SCN-WS1a
landed in between) · **Solves** none — this lane has no LP and no PRECOMMIT by charter.

**Scope executed:** plan §7 "WS-4" **item 2** (DC siting currency) and **item 5** (the D-4
constant-vs-published gap list). Items 1, 3 and 4 are SCN-WS4b/WS-4c's, wave 2; nothing in
`configs/scenario_campaign_matrix.yaml` or any other lane's region was touched.

---

## 1. Bottom line

| leg | outcome |
|---|---|
| **ERCOT zone shares** | **Already delivered, verified, no change needed.** ERCOT has carried a FULL published per-weather-zone decomposition since 2026-07-21 (2025 Adjusted LTLF `<zone>_contracts` + `<zone>_officer_letters`, ~73 % data centre per ERCOT Board Item 16.2). Shares sum to 1.0. The plan's §2.4 statement that zone shares exist "only for PJM" is **stale** (§5 below). |
| **MISO zone shares** | **POPULATED** from the 2026 LTLF's published regional DC decomposition + the published region→LRZ definition, with the one region-straddling model zone resolved on MISO's own per-LRZ LRR. Sums to 1.0. |
| **NEISO `{}`** | **RE-CONFIRMED** against the 2026 CELT, with the immateriality arithmetic written out from primary numbers (§3). `{}` holds; NEISO's absence from the zone-share table is moot, not a second gap. |
| **Item 5 gap list** | §4, written so card D-4 can be presented from it unedited. |
| **Routed, not executed** | one cache-epoch ledger entry (§6), owned by another lane's region this wave. |

---

## 2. MISO — how the shares were derived (item 2)

**The source.** MISO's **2026 Long-Term Load Forecast Results Summary** (LTLF Workshop
2026-04-13, `20260413 LTLF Workshop 2026 Long Term Load Forecast Summary_UPDATED`,
`cdn.misoenergy.org`) publishes the DC decomposition **by region**, which is the granularity this
table needs. Slide 21, *"Data Centers Net Energy, TWh; Current Trajectory"*, stacks DC net energy
into MISO North / Central / South and **defines those regions on the same slide**:

> North: LRZs 1, 3 · Central: LRZs 2, 4, 5, 6, 7 · South: LRZs 8, 9, 10

**The read and its validation.** The slide's series was read from the chart's own vector
coordinates in the published PDF (three filled paths, 21 annual vertices each, calibrated on the
y-axis tick text). It is **validated on the deck's own published totals**, which is why the read
is admissible rather than an estimate:

| check | read | published |
|---|---|---|
| system DC net energy, 2026 | **9.6 TWh** | "data centers expand from **9.6 TWh**…" |
| system DC net energy, 2046 | **266.3 TWh** | "…to **266 TWh**" |
| Central share of 2046 DC energy | **58.2 %** | independently reported as **~58 %** |

The regional split is **year-invariant** in the published series — Central / North / South =
`0.5822 / 0.2349 / 0.1829` at 2030 and `0.5824 / 0.2347 / 0.1829` at 2046 — so a single share
vector represents it exactly, which is what `DATACENTER_ZONE_SHARE` is.

**Energy share ≡ MW share, with no basis conversion.** MISO applies ONE footprint-wide DC load
factor (~93 %: 90 % hyperscale at ~95 %, 10 % enterprise at ~75 %; slide 21 key insights) and
publishes no regional LF differentiation, and our block is flat — so the energy split *is* the MW
split. This is the check rule 14 asks for before importing real data, and it passes.

**Region → model zone.** The model's six MISO zones are whole LRZ unions (`iso_configs`
`_miso_config`: West = LRZ 1, Plains = LRZ 3+5, Illinois = LRZ 4, Indiana = LRZ 6, East = LRZ 2+7,
South = LRZ 8+9+10), so the published regions map onto them directly:

- **MISO-South IS the published South region** — it takes `0.1829` with no reconciliation at all.
- **North** = MISO-West + the LRZ-3 half of MISO-Plains.
- **Central** = MISO-Illinois + MISO-Indiana + MISO-East + the LRZ-5 half of MISO-Plains.

**Within each region**, the memo §3.3 default (`load_share`) distributes — exactly the
one-published-anchor-plus-documented-default construction PJM already ships, here with three
anchors instead of one.

**The one straddle, resolved on published magnitudes.** MISO-Plains is the only model zone that
crosses a published region boundary (LRZ 3 is North, LRZ 5 is Central), and the model carries no
LRZ-3 vs LRZ-5 load split — EIA-930 reports them as the single sub-BA `0035`, which is *why* the
zone is a union. The straddle is therefore split on MISO's **own published per-LRZ magnitudes**:
the PY2025/2026 summer Local Reliability Requirement, **LRZ 3 = 13,574 MW** vs **LRZ 5 =
10,243 MW** → **0.5699 / 0.4301**, from `data/raw/capacity-deliverability/miso/miso.csv` (sourced
to the PY2025-26 LOLE Study Report). Rule 14's named exception applies exactly: real data defined
on a boundary our zones do not match, used in a *reconciled* form with the misalignment documented
— never a guess.

**The result.**

| model zone | DC share | `load_share` | ratio | region |
|---|---|---|---|---|
| MISO-West | 0.152557 | 0.1466 | 1.04 | North (LRZ 1) |
| MISO-Plains | 0.151060 | 0.1385 | 1.09 | North (LRZ 3) + Central (LRZ 5) |
| MISO-Illinois | 0.078214 | 0.0676 | 1.16 | Central (LRZ 4) |
| MISO-Indiana | 0.155040 | 0.1340 | 1.16 | Central (LRZ 6) |
| MISO-East | 0.280229 | 0.2422 | 1.16 | Central (LRZ 2+7) |
| MISO-South | 0.182900 | 0.2711 | **0.67** | South (LRZ 8+9+10) |

Sum = 1.0 (`datacenter_zone_shares` raises otherwise; the test now asserts it for every override
table).

**The material move is MISO-South, and it is the published narrative, not an artefact.** South is
MISO's second-largest load region but is **DC-light**: the Dec-2024 LTLF whitepaper (p. 13) has the
southern states growing "primarily from industrial drivers", with LRZ 9 (Louisiana / east Texas)
growing on oil-and-gas electrification and green hydrogen rather than data centres, while Central
grows on "abundant low-cost land and industrial-focused incentives that attract large hyperscale
campuses" (2026 LTLF slide 21). The `load_share` fallback had been putting **27 %** of MISO's DC
block into the zone the forecast singles out as *not* the DC region.

**Rule 13 regeneration.** The next LTLF vintage regenerates this table by re-reading the same
slide; the LRR straddle factor re-reads the next planning year's LOLE report. No residual was
consulted and none could be — this lane runs no solve.

**Documented limitation.** The published decomposition is **regional**, so the ordering *within*
Central and *within* North is the `load_share` default, not a published per-LRZ DC table. MISO's
driver-level per-LRZ forecast data would refine all six anchors; it is behind the 403-walled host
(§4, item G-D4-2).

**What was deliberately NOT done.** The Dec-2024 whitepaper's one per-LRZ magnitude — "LRZ 1 is
expected to see an additional 4 GW of demand throughout the forecast period, mainly from a
burgeoning data center market" — was **rejected as an anchor**: it is all-driver rather than
DC-only, on the 2024 vintage rather than the 2026 one the block's trajectory uses, and reconciling
4 GW/2044 against the block's 33.5 GW/2046 yields an LRZ-1 share *below* `load_share`, contradicting
MISO's own naming of LRZ 1 as a top-DC zone. That is the basis mismatch rule 14 warns about, and
using it would have been worse than the fallback it replaced.

---

## 3. NEISO — the immateriality arithmetic (item 2, third leg)

The `{}` in `DATACENTER_ADDITIONS_MW["NEISO"]` is **re-confirmed against the 2026 CELT**, now with
the arithmetic carried out from primary numbers instead of a remembered ratio. Sources: ISO-NE
**Final Draft 2026 Large Load Forecast** (Load Forecast Committee, 2026-03-27,
`fx2026_large_loads.pdf`) and the **2026 CELT Report** (2026-05-01).

1. **The population is two projects, one of them a data centre** (deck slide 14): a **NEMA data
   centre, 200 MW** reported nameplate (thru 2027) and a **CT general-electrification** project,
   85 MW (thru 2040). Only the first can populate a DC block. None is under construction, so both
   are excluded from summer 2026/2027 and winter 2026/27 entirely.
2. **ISO-NE's own derates** (slide 9): milestone factor **60 %** for a project that has entered a
   study agreement × a **70 %** data-centre capacity-utilization factor →
   **200 × 0.60 × 0.70 = 84 MW** effective nameplate.
3. **ISO-NE's own hourly profile** (slide 11): a mixed-use data centre peaks at **85 %** of
   nameplate mid-day and holds **80 %** in all other hours, weekends 10 % lower. So
   **peak = 84 × 0.85 = 71.4 MW**, and annual energy
   = 84 MW × 8,760 h × [(8 × 0.85 + 16 × 0.80)/24 weekdays, ×0.9 weekends] = 84 × 0.793 × 8,760
   ≈ **584 GWh/yr**.
4. **Against the 2026 CELT's own denominators** — summer 50/50 peak 25,228 MW (2026) → 26,849 MW
   (2035); winter 50/50 20,483 MW (2026/27) → 26,411 MW (2035/36); net annual energy
   116,679 GWh (2026) → 127,660 GWh (2035):

   | quantity | DC project | share |
   |---|---|---|
   | 2035 summer 50/50 peak | 71.4 MW | **0.27 %** |
   | 2035/36 winter 50/50 peak | 71.4 MW | **0.27 %** |
   | 2035 net annual energy | 584 GWh | **0.46 %** |

   The **whole** large-load forecast (both projects) contributes ~110 MW of peak in the 2030s
   rising to ~130 MW in the 2040s — **0.41 % / 0.49 %** of that winter peak.

Every figure is an order of magnitude under the ~1 % materiality bar the earlier deferral used,
and ISO-NE still states New England "has not witnessed the scale of data center proposals" seen
elsewhere (slide 3). **`{}` holds** — DC stays implicit in the NEISO near-era
`DEMAND_GROWTH_RATES`. Because the block resolves to 0 MW, **NEISO's absence from
`DATACENTER_ZONE_SHARE` is moot**: there is nothing to allocate, so it is not a second open gap.
No number was taken from a neighbouring ISO's basis (rule 25).

---

## 4. Item 5 — the constant-vs-published gap list for owner card D-4

*This section is written to be presented as-is with card D-4. It names each hand-transcribed
load-forecast constant, the published series behind it, what is on disk, and what a curated
`load-forecast` datatype would actually change. **It opens no intake and fetches no data into the
repo** — that is the owner's call.*

**The shape of the gap in one line.** Every load-forecast number in the model is a **hand-read
figure with a citation comment**; **not one** of the six published forecast documents they come
from is a tracked file in `data/raw/`, and only one (the NYISO Gold Book) is even a recorded,
re-fetchable corpus payload. Nothing *depends* on this — the constants carry their citations and
the scenario runs on them — but no number is machine-verifiable against its source, and no vintage
refresh can be automated.

| # | constant | published series it was transcribed from | on disk? | what a curated datatype would change |
|---|---|---|---|---|
| **G-D4-1** | `DEMAND_GROWTH_RATES` (6 ISOs × 3 paths × near/long = 36 numbers) | ERCOT 2025 LTLF3; CEC CED 2025-2045 (2025 IEPR); PJM 2026 LTLF (2026-01-14); NYISO 2026 Gold Book Table I-1a; ISO-NE 2026 CELT; MISO Sept-2025 LTLF | **No.** No LTLF, CELT, IEPR or PJM load-forecast file is tracked anywhere under `data/raw/`. The 2026 Gold Book is a **gitignored corpus payload** (`.gitignore:1039`) with a verified re-fetch URL in `data/raw/NYISO/README.md`; it is the only one with a recorded recovery route | The rates become derived, not typed: each path's CAGR recomputed from the edition's own published series (the NYISO row already does this arithmetic **by hand** — see its comment block, which spells out six CAGRs from Table I-1a). Edition bumps stop being a per-lane transcription errand (rule 23 re-derives on source change) |
| **G-D4-2** | `DATACENTER_ADDITIONS_MW` (5 populated ISOs) | ERCOT LFL/LTLF queue; PJM 2025 LTLF DC component; CEC 24-IEPR DC forecast; NYISO 2025 Gold Book large-load; MISO 2025/2026 LTLF | **No** | Would close three *named* limitations already in the comments: CAISO `high := mid` because the IEPR high-DC MW table was never read; PJM and NYISO `low := 0` because the signed-subset MW is not separately published in what was read; MISO `high` extrapolated past 2030 on the published 2030 high/mid ratio |
| **G-D4-3** | `DATACENTER_ZONE_SHARE` (PJM, ERCOT, MISO — this commit) | PJM 2025 LTLF Table B-9b (unread; DOM anchored from a secondary ~20 GW figure); ERCOT 2025 Adjusted LTLF `ErcotAdjustedForecast.xlsb`; MISO 2026 LTLF slide 21 + PY2025-26 LOLE per-LRZ LRR | **Partly.** The MISO **LRR** leg is on disk and cited (`data/raw/capacity-deliverability/miso/miso.csv`). The ERCOT `.xlsb` is **not** in `data/raw` in any form. PJM Table B-9b has never been read. MISO's own **driver-level per-LRZ forecast data** — which the 2026 LTLF says it published (slide 6, "published driver-level forecast data") — is behind the 403-walled `www.misoenergy.org` host (§5) | PJM's 7 residual zones and MISO's within-region ordering both stop being `load_share` defaults; ERCOT's 52,306 MW aggregation becomes reproducible rather than a transcribed result |
| **G-D4-4** | `ELECTRIFICATION_LAYERS` | per-ISO published end-use adoption anchors (FF-G4 Option B) | **No** | The plan's own §2.4 records this as populated in **exactly one cell** (NEISO `heat_pump` mid) with `ev` empty in every ISO. This is the constant the intake would move most: the layers exist and are wired, and have no numbers to run on |
| **G-D4-5** | `DEMAND_GROWTH_TRANSITION_YEAR = 2030` | **none** — its comment says "engineering judgment" | n/a | Nothing. Flagged because it is the one load-shape constant in the family with **no published source at all**, so a provenance upgrade elsewhere leaves it standing alone |

**Two observations the desk should carry with the card.**

- **The gap is provenance, not capability.** Every one of these constants carries a citation and a
  derivation; the campaign runs today. What is missing is (a) machine-verifiability, (b) automated
  vintage refresh, and (c) the *unread tables* in G-D4-2/3/4, which are gaps the intake would
  actually close rather than merely re-file.
- **The intake's real prize is G-D4-4, not G-D4-1.** The growth rates are transcribed but complete;
  the electrification layers are wired and **empty**. If the owner funds a narrow slice rather than
  the whole datatype, the per-ISO end-use adoption tables buy the most.

**Recommendation (unchanged from the plan's own): defer.** Nothing in this lane's work was blocked
by the gap — MISO's shares came from a published document read in-session, and the one thing that
*was* blocked (the per-LRZ refinement) is blocked by a **403 host wall**, which an intake decision
does not lift.

---

## 5. Things found stale or blocked (for the desk, not fixed here beyond the noted lines)

1. **Plan §2.4 is stale on zone shares.** It reads "zone shares only for PJM
   (`DATACENTER_ZONE_SHARE`, Dominion 0.55 anchor), NEISO `{}`" — but **ERCOT has been populated
   since 2026-07-21**, verified in this lane at the plan's own pin `4d4dc6ce`. Corrected in place
   (one clause) since it describes the exact table this lane owns; flagged here because the §2.4
   text is the plan's, not this lane's file region.
2. **Plan §2.4 G-L2 is stale on the Gold Book.** It reads "the 2026 Gold Book the NYISO row cites
   is absent (only 2018–2022 on disk)". Substantively right — it is not in the repo — but the
   *cause* is a deliberate BLOAT corpus conversion (`.gitignore:1039`), and its re-fetch URL is
   recorded and was verified 2026-08-15. Left as-is; the gap list above states it precisely.
3. **`www.misoenergy.org` is bot-walled for this environment, `cdn.misoenergy.org` is not.**
   Reproduced today, matching the 2026-08-03 measurement in
   `ffr-sc-transmission-ab-2026-08-03.md` §8: `https://www.misoenergy.org/planning/…/large-load-additions/`
   → **403**, and the guessed CDN filename that session tried
   (`…/2026 MISO Long Term Load Forecast Results Summary.pdf`) → **403**. But the **real** CDN
   filename returns **200**:
   `https://cdn.misoenergy.org/20260413%20LTLF%20Workshop%202026%20Long%20Term%20Load%20Forecast%20Summary_UPDATED750524.pdf`.
   **The MISO 2026 LTLF is therefore NOT unreachable** — that session's "blocked, handed forward"
   conclusion held only for the filename it guessed. The Dec-2024 whitepaper
   (`…/MISO Long-Term Load Forecast Whitepaper_December 2024667166.pdf`) and the Sept-2025 pilot
   deck (`…/092425 - Load Data Request for Stakeholders719704.pdf`) likewise return 200. What stays
   walled is the **www** host, i.e. the workshop event pages that link the driver-level datasets —
   which is why G-D4-3's per-LRZ refinement is blocked and the regional slide is what this lane
   used. *Successor note for whoever refreshes the MISO growth rates: the 2026 LTLF is readable
   today by exact CDN URL; `DEMAND_GROWTH_RATES["MISO"]` still cites the Sept-2025 vintage.*
4. **NEISO `DEMAND_GROWTH_RATES` labels 116,679 GWh as 2025**; the 2026 CELT's own release puts
   that figure at **2026** (127,660 GWh at 2035). A one-year label slip in a comment, not in a
   value — the rate is a 10-year CAGR either way. Not this lane's region to edit; noted for the
   next lane in that block.

---

## 6. Routed to SCN-DESK (not executed — outside this lane's file regions)

**A cache-epoch ledger entry is owed and this lane may not write it.** Populating
`DATACENTER_ZONE_SHARE["MISO"]` changes MISO **forecast-mode** results at the **same cache key**:
the block MW is unchanged, its zonal allocation is not. Scope, stated precisely:

> **MISO forecast-mode bundles** solved before this commit with `datacenter_load_path != "off"`
> (the default is `"mid"` since FF-1F) are **stale**. **No backcast bundle in any ISO** is affected
> — the DC block is forecast-only and coerced off in backcast mode by
> `validate_datacenter_config`. **No other ISO** is affected: ERCOT and PJM already carried
> overrides and are byte-identical; CAISO, NYISO and NEISO are untouched (and NEISO's block is
> 0 MW regardless). System-level energy is unchanged in MISO too — only the zonal split moves, so
> zonal dispatch, flows and prices change while the ISO total block does not.

`src/market_sim/results/cache.py` is **SCN-WS1a's region** in the wave-1 collision register (one
epoch entry). WS-1a has since merged (`4db660cb`), so the desk should assign this entry to the
next lane holding that file, or grant it as a one-line follow-up. The text above is ready to paste
as the ledger entry body.

---

## 7. Duties and deliverables

- **Matrix duty (rule 28).** **No `ScenarioConfig` field added**, so CI duty (c) does not fire.
  Duty (b) does not fire either: no mechanism was *tested* — `datacenter_load_block` is armed and
  adjudicated exactly as before, and no cell's verdict, evidence or posture changes because a
  constant's zonal allocation was refined. **No shard was stamped, deliberately.** (Had the shard
  carried a MISO `datacenter_load_block` evidence line naming the `load_share` fallback, it would
  have been stamped; it does not.)
- **Scorecard.** Plan §5.1 / ledger §3 **Load-HI row 1** updated to record the siting half only —
  the named case is SCN-WS4b's and is **not** claimed here.
- **Byte-identity.** Every backcast keeper in every ISO is byte-identical (forecast-only mechanism,
  §6). ERCOT/PJM/CAISO/NYISO/NEISO forecast runs are byte-identical too; only MISO forecast moves.
- **Tests.** `tests/unit/data/test_datacenter.py` — 40 passed. The sum-to-1.0 parametrization now
  covers MISO; a new invariant test asserts **every** override table keys on the model
  `zone_names`, sums to 1.0 and carries no negative share; the MISO test gates the *published
  facts* (South is the published region exactly and is DC-light; every Central-region zone is
  DC-heavy), never the arithmetic that produced them. Three pre-existing failures in
  `tests/unit/config/test_reserve_config.py::TestErcotMultiProduct` are unrelated and reproduce on
  a clean tree.
- **Rule 27.** `constants.py` was edited in place with `Edit`-equivalent local edits and pushed as
  the exact on-disk bytes; the diff touches only lines 2946–3137 (the
  `DATACENTER_ADDITIONS_MW` / `DATACENTER_ZONE_SHARE` region this lane owns), and the pushed blob
  is verified by fetch-back against the local line count and hash.

---

## 8. Sources cited by this lane

- MISO **2026 Long-Term Load Forecast Results Summary**, LTLF Workshop 2026-04-13
  (`cdn.misoenergy.org/20260413 LTLF Workshop 2026 Long Term Load Forecast Summary_UPDATED750524.pdf`)
  — slide 21 (DC net energy by region + the region→LRZ definition + the ~93 % load factor),
  slide 26 (regional CAGR / share of MISO), slide 6 (published driver-level forecast data).
- MISO **December 2024 Long-Term Load Forecast Whitepaper**
  (`cdn.misoenergy.org/MISO Long-Term Load Forecast Whitepaper_December 2024667166.pdf`) p. 13 —
  the per-LRZ growth narrative, incl. the southern-states industrial-driver statement.
- MISO **2025 LTLF Stakeholder Load Data Pilot Survey** (2025-09-25) — establishes that granular
  large-load siting data was still being *collected* at that vintage.
- MISO **PY2025-26 LOLE Study Report** per-LRZ LRR, via `data/raw/capacity-deliverability/miso/miso.csv`.
- ISO-NE **Final Draft 2026 Large Load Forecast**, Load Forecast Committee 2026-03-27
  (`iso-ne.com/static-assets/documents/100033/fx2026_large_loads.pdf`) — slides 3, 9, 11, 14.
- ISO-NE **2026 CELT Report** (2026-05-01) peak and energy figures.
- ERCOT **2025 Adjusted Long-Term Load Forecast** and **Board System Planning update Item 16.2**
  (Dec 2025) — the pre-existing ERCOT basis, verified not re-derived.
