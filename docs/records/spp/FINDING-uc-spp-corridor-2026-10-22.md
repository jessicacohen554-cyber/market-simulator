# FINDING — UC-SPP-CORRIDOR: is a measured, per-year N→S limit identifiable for 2019–2025?

**Lane:** UC-SPP-CORRIDOR · **Date:** 2026-10-22 · **Branch:** `claude/uc-spp-corridor` · **Base:** `main` `3215209d`.
**Charter:** UC-DESK (`session_01WX9W5tgYMre3Z134LZoGF6`), owner ruling R30 ("Intake SPP data first").
**LP in this session:** zero. **Solve-path change:** none. **Data profile:** `spp`.
**Tables behind every number:** `docs/records/spp/uc-corridor/` (scripts + CSVs, reproducible from the committed raw).

## 0. Headline

| years | measured N→S limit identifiable? | value (SPP-53 construction, in-year limits) |
|---|---|---|
| 2019, 2020, 2021, 2022-01-01 → 04-13 | **No.** SPP serves no effective-limit series before 2022-04-14 | — (3,400 stays a carried value; misalignment stated) |
| 2022 (from 04-14) | Yes, limits measured | **3,395 MW** |
| 2023 | Yes | **3,358 MW** |
| 2024 | Yes | **3,321 MW** |
| 2025 | Yes | **3,358 MW** |

1. **New data.** SPP publishes effective limits as a separate portal product, `effective-limits` (`RTBM-EFFLIMIT-YYYYMMDD.csv`), from **2022-04-14**. Earlier lanes searched only `rtbm-binding-constraints`, which gained limit columns on 2026-03-17. Intaken here: 1,358 day files, the clean datatype `flowgate-limits-at-bind`.
2. **The in-window limits reproduce 3,400 MW within 2.4 % in every measured year.** Rule-14 misalignment (i) of SPP-53 (2026 limits on a 2019–25 solve) is **closed for 2022-04 → 2025**. The limit vintage was not why the model link is short.
3. **But the number is one transformer, not an interface.** Every year's weighted median lands on the **Franklin 161/69 kV transformer** (L ≈ 100 MW, ψ = 0.030). Remove it and the same construction gives 4,924–9,181 MW. Its ψ 95 % interval alone spans **2,380–5,680 MW**. A per-year number is identifiable; a *defensible interface capability* is not. The uncertainty sits in ψ (the price-based sensitivity), which this data does not touch.
4. **Per-season is not defensible.** Season medians swing from 174 to 5,033 MW as the median hops between elements (§3).
5. **2019–2021 lack more than measured limits.** The element that sets 3,400 MW did not bind in RTBM in 2019 or 2020, and bound only 38 h in 2021. That element is Franklin, whose first temporary flowgate SPP created on 2021-02-26. So for 2019–2021 the 3,400 MW figure rests on a constituent that was not part of that system's congestion pattern (§2b).
6. **Direct test at the UC-arm slack hours.** On 2023-08-10, 13:00–16:00 CDT, the hours where implied real N→S was 4.6–6.2 GW, **no N→S corridor element bound in SPP's RTBM**. The real system moved that much without the corridor binding. The model's 3,400 MW link was binding there. So in those hours the corridor is not what limited reality. Either real capability exceeded 3,400 MW for that flow pattern, or the implied flow is overstated by the model's South wind share. **This data cannot separate the two** (§4).

**Proposed treatment:** keep 3,400 MW; no solve-path change. Detail and the owner decisions are in §5.

## 1. Data intake

| item | value |
|---|---|
| source | `portal.spp.org` file-browser, `fsName=effective-limits`, anonymous HTTPS. Found via `GET /api/menu/` (slug `effective-limits`) |
| columns | the 10 binding-constraint columns + `Source Limit` (FAC-011 SOL), `Realtime Effective Limit` (enforced, TOP-001), `Initial Effective Limit` |
| coverage | 2022-04-14 → present. 2022: 262 files · 2023: 365 · 2024: 366 · 2025: 365 |
| raw | `data/raw/spp-effective-limits/`. Day files gitignored (~3 GB), `SHA256SUMS.txt` committed. `rtbm_efflimit_bound_<y>.csv.gz` committed (BINDING + BREACHED lines verbatim, 5.5–7.0 MB/yr) |
| fetch | `scripts/data/fetch_spp_effective_limits.py` (`--reduce` rebuilds the committed form) |
| clean | `flowgate-limits-at-bind` (schema-first; `scripts/lib/flowgate_limits_at_bind/{__init__,spp}.py`; `scripts/data/curate_flowgate_limits_at_bind.py`; registered in `regenerate_clean.py`; `tests/test_curate_flowgate_limits_at_bind.py`) |
| completeness | 2023: 363,730 BINDING / 101,070 BREACHED rows vs the RTBM-BC yearly roll-up's 339,620 / 100,555. EFFLIMIT is a superset. 4,903 exact repeated lines (1.1 %) are counted once on curation |

Other portal products checked, with their limits:

- `archive-temporary-flowgates` (`Temp_Flowgate_Archive.csv`, static Norm/Emer ratings with create/remove times).
- `permanent-flowgates` (seasonal ratings).
- `congestion-by-constraint` (DA monthly Σ flow × shadow price, 2016+).
- `ttc-updates` (WEIS paths only).
- `historical-tie-flow` (per-counterparty tie flows, monthly, 2014+; relevant to the scarcity finding's P3).

**None of these is an effective limit for 2019–2021.** A rating is not an enforced limit: 2023–25 corridor rows sit at a median **0.91–0.92 × source limit**, and **99.7–100 %** are derated. Carrying 2022+ limits back would be an estimate (hard stop).

## 2. Per-year construction

Method: SPP-53's construction, unchanged. Same 12 identified constituents, same pooled 2023–25 ψ, same binding-hours-weighted median of T* = L/ψ. **One input changed:** L is the median RTBM effective limit over the constituent's own binding hours in that year. Weights are that year's binding hours. Using SPP-53's pooled hours as weights gives the same values (`ttc_by_year.csv`).

| year | constituents bound | TTC (weighted median) | weighted p25 / p75 | without Franklin | unweighted median | Franklin share of hours |
|---|---|---|---|---|---|---|
| 2022* | 9 / 12 | **3,395** | 3,395 / 9,378 | 6,689 | 5,141 | 43 % |
| 2023 | 11 / 12 | **3,358** | 3,358 / 4,924 | 4,924 | 4,924 | 54 % |
| 2024 | 12 / 12 | **3,321** | 3,321 / 9,378 | 4,924 | 4,751 | 30 % |
| 2025 | 12 / 12 | **3,358** | 3,358 / 14,795 | 9,181 | 4,856 | 41 % |

\* 2022-04-14 → 12-31 only.

What the in-window limits changed, by constituent (`constituent_limits_by_year.csv`):

| constituent | SPP-53 L (source) | in-window L, 2022–25 | T* SPP-53 → in-window |
|---|---|---|---|
| Franklin 161/69 kV xfmr | 100 (registry) | 99.0–101.2 | 3,355 → 3,321–3,395 |
| Cooper–St Joe 345 kV | 1,087 (2026 archive) | **301–386** | 6,437 → **1,781–2,286** |
| LEC–LAWH | 160 (registry) | 131–143 | 3,487 → 2,862–3,131 |
| Hawthorn xfmr | 650 (registry) | 495–523 | 18,564 → 14,137–14,923 |
| Sibley xfmrs | 400 (registry) | 400–418 | 4,574–4,919 → 4,578–5,141 |
| Nashua, Edwards, First Creek, Mullergren–Ellsworth, Marshall–Knob, Seward–St John | as SPP-53 | within −14 % / +12 % of SPP-53 | small moves |

- Seven of SPP-53's twelve limits were registry ratings (no 2026 bind). All twelve are now measured in-window.
- Cooper–St Joe ran at about a third of its 2026 limit in 2022–25.
- The large moves sit away from the median, so the aggregate does not move.

## 2b. 2019–2021: the dominant constituent was not there

`element_binding_hours_2019_2025.csv`: hours in which each SPP-53 element carried a BINDING/BREACHED RTBM interval, from SPP's 10-column roll-ups. These carry no limits.

| element | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | first temp flowgate (archive) |
|---|---|---|---|---|---|---|---|---|
| **Franklin xfmr** | **0** | **0** | **38** | 1,088 | 1,405 | 1,005 | 1,688 | 2021-02-26 |
| Cooper–St Joe | 175 | 28 | 291 | 405 | 525 | 190 | 325 | 2015 |
| Hawthorn xfmr | 110 | 67 | 107 | 179 | 44 | 55 | 372 | 2016 |
| Marshall–Knob | 22 | 32 | 329 | 0 | 0 | 170 | 476 | 2019 |
| Edwards xfmr | 64 | 49 | 112 | 285 | 44 | 277 | 723 | 2016 |
| others (6) | 0–44 | 0–63 | 0–134 | 0–244 | 3–524 | 187–537 | 37–338 | |

- In 2019–2021 the identified set bound far less: 9 of 11 elements bound under 70 h in 2019. Its weight sat on Cooper–St Joe, Hawthorn and Edwards, whose in-window T* run from 1,800 to 20,000 MW.
- A 2019–2021 value would need both limits (not served) and a ψ identified on those years' prices (not done; SPP-53's ψ is 2023–25).
- Carrying 2022+ limits back would be an estimate. That is a hard stop, so no number is given.

## 3. Why one number per year is not an interface capability

- **The median is Franklin.** Franklin carries 30–54 % of the weight and sits at the 25th–50th weighted percentile, so p25 = median in every year. Each year's TTC is Franklin's effective limit (stable at ≈ 100 MW) ÷ ψ = 0.0298.
- **ψ is the weak leg.** Franklin's ψ has t = 4.8. Its 95 % interval alone maps to **2,380–5,680 MW**. SPP-53's leave-one-year-out re-fits gave 2,645 / 3,681 / 11,121 MW. A 161/69 kV transformer with a 3 % hub-to-hub sensitivity is a local element, not a cut-set.
- **Seasons do not stabilise it** (`ttc_by_year_season.csv`, own-year limits and hours):

| | winter | shoulder | summer |
|---|---|---|---|
| 2023 | 3,358 | 3,358 | 3,506 |
| 2024 | 4,578 | 3,321 | 3,395 |
| 2025 | 5,033 | 3,321 | **174** (Marshall–Knob 115 kV, ψ 0.365, takes the median) |

- SPP publishes no N↔S interface flowgate (SPP-53 §1, re-confirmed: no portal product carries one). TTC updates exist only for WEIS paths.

## 4. The slack hours: what the real corridor did

`slack_hour_corridor_binding.csv`. Corridor = SPP-14's fixed `n_s_corridor` rules, applied unchanged. Model hour → local wall clock (America/Chicago, non-leap).

| hours (local) | implied real N→S (scarcity finding) | N→S corridor elements binding in RTBM |
|---|---|---|
| **2023-08-10 13:00–16:00** | **4,763–6,205 MW** | **none.** Only `other` / Oklahoma elements bound, e.g. Win115–WPRISN, SW Station–Ellsworth, Conway–Kirby, Midwest–Franklin 138 kV (OKGE) |
| 2023-08-10 17:00 | 4,585–5,658 | Shays–Mullergren, Holcomb xfmr (low shadow) |
| 2023-09-25 14:00–16:00 | 2,303–4,219 | Cooper–St Joe (L 420–538, T* via ψ 0.169 ≈ 2.5–3.2 GW) |
| 2022-10-15 14:00–15:00 | 2,654–4,502 | 6–8 elements (LaCygne–N345, Kell xfmr, Shays–Mullergren, Gordon–Maize …) |
| 2022-05-14, 2023-10-09 | 3,061–5,129 / 2,735–3,433 | none |

- The ±1 h check on 2023-08-10 is the same: no corridor element bound 11:00–16:00 CDT.
- So on the day that drives about 30 % of the UC-arm unserved energy (2,161 MWh), the real corridor did not bind. The model's link did.
- That is consistent with two readings, as the scarcity finding §4 already said:
  - (a) real N→S capability in that flow pattern exceeded the implied 4.6–6.2 GW, so a static 3,400 MW is too tight there;
  - (b) the implied flow is overstated because the model's South wind share (22 % vs ~50 % annual) is low.
- Effective limits cannot separate (a) from (b). Only a measured zonal wind or flow series can.
- The Franklin element itself bound at ≈ 100 MW in 1,490–2,002 h/yr. If Franklin's T* were the interface, real N→S should sit near 3.4 GW whenever it binds. That check needs a measured hourly N→S flow, which SPP does not publish.

## 5. Proposed treatment (owner/desk decisions; nothing solve-affecting lands here)

**T1 — Keep `_ns_corridor_ttc = 3,400` (recommended).**
- 2022-04 → 2025: the in-window measurement reproduces it (3,321–3,395). Moving to per-year values would change the link by ≤ 2.4 %. That is not worth a solve-surface change or a ScenarioConfig field.
- 2019 → 2022-04-13: no measured limit exists, and the constituent that sets the value did not bind in 2019–2020 (§2b). Keep the value, state the misalignment, and add that the 2019–2021 congestion pattern differs.
- Optional, owner's call because it touches `src/`: amend the link's citation comment to cite this FINDING as the in-window confirmation for 2022-04 → 2025. The comment change is inert; the cache key does not move.

**T2 — Do not raise the limit to close the Aug-2023 unserved energy.** The data show the real corridor unbound in those hours. They do not give a measured capability above 3,400. Any higher value would be fit to the residual (rules 1 / 13). The defensible next step is the scarcity finding's **P2 data question**: a zone-resolved wind or flow series (per-plant hourly wind, or SPP's per-counterparty tie flows to place the seam legs) to separate (a) from (b).

**T3 — Matrix.** No cell moves; nothing was solved.
- `measured_interface_limits` stays **O**: the construction is confirmed on in-window limits, and the interface-vs-element question stays open.
- `internal_congestion_split` stays **U**. The Aug-2023 binding set (Oklahoma / western-Kansas elements, not the corridor) is evidence for that lever and for SPP-F1, not a verdict.

**T4 — SPP-F1 re-open source now exists.**
- SPP-F1's named re-open source ("RTBM binding-constraint files 2023-2024 with the effective-limit columns") is available: `flowgate-limits-at-bind` covers the Oklahoma-pocket elements (Cimarron, Osage–Webb Tap, Russett–South Brown, Division–Mustang) for 2023–2024.
- This is a desk routing item; the keeper shard is not edited here.

## 6. Limits of this reading

1. ψ is SPP-53's (pooled 2023–25 hub-spread OLS) and was **not re-fit**. Per-year ψ would mix two changes in one table.
2. The hour mapping assumes the model clock is local prevailing time. The ±1 h check gives the same result on 2023-08-10.
3. Implied N→S is the scarcity finding's balance. It carries the model's South wind/solar and the seam-leg ambiguity.
4. The corridor membership is SPP-14's contingency-token rule. An element outside it that limits N→S would be missed, and so would a corridor element mislabelled `other`.
