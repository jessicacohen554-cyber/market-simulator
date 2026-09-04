# PRE-DECLARATION — capx D45-R: the D45 close-out at HEAD (PJM L1 replay, NYISO L2/L3, PJM L4, the NEISO shipped-posture leg) plus D46 Stages 2 and 3 (NYISO / PJM / MISO T1-F)

**Lane:** capx D45-R — director r#33, owner rulings **Q33** (D45 is DEAD; this lane finishes
it AT HEAD) and **Q35** (D46 Stage 3 folded in at the re-measured price). Pack §D45-R.
Branch `claude/capx-d45r-close-jwq3bf` (the harness-assigned branch for the §D45-R
dispatch), FRESH off `origin/main` `a8464861`. **Pushed BEFORE any solve started.** Every
prediction below is graded at full magnitude in the D45 finding §7 (alongside D45's own
pre-declaration, which is graded there too), misses included; nothing here may be
re-narrated after a result is read.

**Governing discipline (rule 14, inherited from D28/D31/D37/D40/D45/D46):** faithful
positions and curves move capacity revenue UP and retirements HARDER; nothing is sized by
any residual; a worse-looking FC-3 after accurate inputs is the expected signature.
**NOTHING ARMS in this lane.** No `ScenarioConfig` field is added or moved (rule 28 not
triggered); no parameter value changes; no keeper / shard / marker; the backcast namespace
is untouched (rules 12, 13, 22, 25, 27, 28). Nothing is scored against measured H1-2026.

---

## 1. Posture, keys and baselines — resolved and verified before the solve

Every key below was computed at HEAD `a8464861` through the harness's own resolution path
(`run_capacity_hindcast.build_config` / `run_full_horizon.reference_config` →
`apply_iso_scenario_defaults` → `ScenarioConfig.cache_key()`), and **checked against all 165
cache keys committed under `results/` — none collides with any of them or with each other.**
The method is validated on a known answer: the same path reproduces D46's NEISO t1f key
`6690e4d6d66bc819` exactly. Every leg gets a fresh, verified-empty out-dir and the harness
redirects `CACHE_ROOT` into it, so no pre-existing bundle can be served.

**Posture, every leg:** `fossil_announced_exits_enabled=True` (Q30/D44, the post-D44
default — verified in each resolved config, not assumed), `hindcast_verified_announced_exits=True`
on the T1-H legs, `entry_screen_diagnostics=True` on the T1-H legs (diagnostics-on, the
D37/D45 pattern; output-only but cache-keyed), and the D41 CCS constants
(`ccs_retrofit_capex_kw=1521.4`, `fixed_om_gas_cc_ccs=65.0`) — inert in every T1-H leg by
construction (retrofits open 2028; the window solves {2021, 2023, 2024, 2025}), live in the
three t1f legs. **Keeper at HEAD, read from `frontend/data/backcast/keepers/<ISO>.json`:**
PJM `2026-08-15-pjm-162-inputclock`, NYISO `2026-09-04-nyiso-185-family-hr`, NEISO
`2026-08-17-neiso-99-joint-p1`, MISO `2026-09-03-miso-202-unitclip`.

### 1.1 The T1-H legs — `run_capacity_hindcast.py --start-year 2021 --end-year 2025 --vintage 2020 --fuel-variant realized --entry-screen-diagnostics`

| # | leg | run id | registers as | expected cache key | posture beyond the HEAD default | prior record → preserved at |
|---|---|---|---|---|---|---|
| L1 | PJM live-posture replay | `pjm-2021-2025-realized-t1h-d45r` | bare **`pjm-t1h`** | **`c6091bd5b62bbc3f`** | none (PJM ships curve-ON) | D45 L1 `pjm-2021-2025-realized-t1h-d45` (key `ea767a6254b8e4af`, pre-D44) → **`pjm-t1h-pre-d45r`** |
| L2 | NYISO live-posture, curve-OFF (flat $110) | `nyiso-2021-2025-realized-t1h-d45r` | bare **`nyiso-t1h`** | **`91686abe7a744a88`** | none (NYISO absent from `capacity_market_clearing_by_iso`) | the FFR-3A-2-vintage record (session FFR-3A-2, sha `8ba592814d92`; D45 never reached L2) → **`nyiso-t1h-pre-d45r`** |
| L3 | NYISO curve-ON probe | `nyiso-2021-2025-realized-t1h-d45r-curveon` | suffixed **`nyiso-t1h-d45r-curveon`** | **`cad77112c804881d`** | `--capacity-market-clearing` (`{NYISO: True}`) | — (probe; never the bare key) |
| L4 | PJM fixed-anchor control | `pjm-2021-2025-realized-t1h-d45r-fixed` | suffixed **`pjm-t1h-d45r-fixed`** | **`896da48960560a29`** | `--fixed-net-cone` (`capacity_market_clearing_by_iso=None`, flat $77.43/kW-yr) | — (probe) |
| L5 | NEISO SHIPPED posture (Net ICR lever OFF) | `neiso-2021-2025-realized-t1h-d45r` | bare **`neiso-t1h`** | **`d6c0137e37bf3200`** | none (`neiso_net_icr_requirement` ships `False`) | D46 `neiso-2021-2025-realized-t1h-d46` (key `da19b85495178949`, Q28-ARMED posture) → **`neiso-t1h-pre-d45r`** |

**Comparator provenance, per leg.** L1 vs `pjm-t1h-pre-d45r`: the resolved-config delta is
the D44 flip alone (the miso-202 `unit_outage_per_unit_clip` field keys neutral at its
`False` drop) — a clean single-axis comparison. L2 vs `nyiso-t1h-pre-d45r`: **CONFOUNDED**
by a month of HEAD (FFR-3A-2 epoch 2026-08-03 → D30/D36/D39-D43 gated/D41/D42-D44, the
entry-rate ladders, the S-123 package, the NYISO extcap intake, keeper 159→177→185); reported
as "the board row this replaces", never attributed. Within this lane the attribution is
**L2 vs L3** (one field) and **L1 vs L4** (one field) only. L5 vs `neiso-t1h-pre-d45r`: one
field (`neiso_net_icr_requirement` True→False), same keeper, dates ON on both — a clean
paired reading of D37's lever at the post-D44 posture; and L5 vs `neiso-t1h-d37-control`
(lever OFF, dates OFF, key `5925e67c572a910f`) isolates the dates flip at the shipped
posture.

### 1.2 The T1-F legs — `run_full_horizon.py --start-year 2026 --end-year 2030 --golden-posture` (D46 §1(a): the t1f TIER is 2026–2030, five solve years, no full-solve authorization needed or held)

| # | leg | run id (registrar-derived: `<iso>-2026-2030-<label>`, label `d45r-remeasure`) | registers as | expected cache key | prior record → preserved at |
|---|---|---|---|---|---|
| F1 | NYISO | `nyiso-2026-2030-d45r-remeasure` | bare **`nyiso-t1f`** | **`cc7d1050a8090c76`** | `nyiso-2026-2030-extcap-capxd2` (key `fdd84d51e31ffc82`, PROMOTE) → **`nyiso-t1f-pre-d45r`** |
| F2 | PJM | `pjm-2026-2030-d45r-remeasure` | bare **`pjm-t1f`** | **`321f04e9060787f0`** | `pjm-2026-2030-s6-ledger` (key `31a19d815fa319a7`, HOLD) → **`pjm-t1f-pre-d45r`** |
| F3 | MISO | `miso-2026-2030-d45r-remeasure` | bare **`miso-t1f`** | **`8d8bc63a0d4378a9`** | `miso-2026-2030-s123-verify` (key `587dc5b32ba71ceb`, HOLD) → **`miso-t1f-pre-d45r`** |

Scored `forecast_verdict.py --tier t1f --summary … --run-config … --dof-ledger …` with the
ledger built from the run's own `run_config.json` by `build_forecast_dof_ledger.py` (the D46
instrument-parity step, declared here so it is not an after-the-fact fix); the FC-5
corridor dispositions are **not** re-applied to a different trajectory (the D46 precedent:
FC-5 reads SKIPPED where the preserved record reads CAVEAT — report-only at t1f, gates
nothing). Registered `register_forecast_run.py --summary … --kind t1f --label d45r-remeasure`.

### 1.3 Order, concurrency and price (rule 12)

L1 (PJM, solo, ~16–21 min / 8.8 GB) → L2 ∥ L3 (NYISO, ~7–13 min each, ~3 GB) → L4 (PJM,
solo) → L5 ∥ F1 (NEISO T1-H ~7 min; NYISO t1f ~13 min / 2.9 GB measured on the extcap leg)
→ F2 (PJM t1f, solo; the S-6 leg measured **20.9 min / 8.8 GB**) → F3 (MISO t1f, solo; the
S-123-V leg measured **24.2 min / 9.9 GB**). **STOP RULE (charter):** if F2 or F3 exceeds
2 h wall it is killed, the measured time recorded, and the key left stale with a dated note.
On the measured factor both are priced at 20–40 min; the 2 h bar is 3–6× that.

### 1.4 The registration plan (frozen)

Preserve-then-overwrite (the D27/D37/D45/D46 pattern): each bare key's current entry is
copied VERBATIM to `<key>-pre-d45r` (its own provenance untouched), then the new record
takes the bare key. `VERDICT_MAP`: (i) new rows for the eight run ids above; (ii) the three
D45 rows that point at bundles that never existed —
`nyiso-2021-2025-realized-t1h-d45`, `nyiso-2021-2025-realized-t1h-d45-curveon`,
`pjm-2021-2025-realized-t1h-d45-fixed` — are **RE-POINTED IN PLACE to this lane's run ids**
(the D46 re-pointing precedent, disclosed in the finding); (iii)
`pjm-2021-2025-realized-t1h-d45` → `pjm-t1h-pre-d45r` and
`neiso-2021-2025-realized-t1h-d46` → `neiso-t1h-pre-d45r` (the `-pre-d31/-pre-d33/-pre-d46`
chain). Zero duplicate keys, verified by AST. The existing `<iso>-2026-2030-ff-t1-gate` rows
and the sidecar-level `verdict_key` overrides on the superseded t1f sidecars are left as D46
left theirs (recorded, not repaired — a records item for the director if it wants them
re-pointed). Each new bundle commits its slim set (meta, `run_config.json`, `score.json` /
`full_horizon_summary.json`, `forecast_verdict.json`, the `evolution_<year>.json` ledgers,
the diagnostics `.npz`) under a per-lane `.gitignore` block on the D46 template.

**STOP conditions (binding):** any cache-key collision with a committed bundle; any realized
key ≠ its pre-declared value (reported, and the leg is registered only after the difference
is explained from the resolved config); anything beyond the six bare keys, the two probe keys,
their `-pre-d45r` preserves and the four ISOs' board blocks moving; `check_gate_a_provenance.py`
failing before the records commit (→ STOP and route; the director holds the re-key duty).

### 1.5 What the dates channel actually holds per ISO — READ BEFORE THE SOLVE (the D46 §7 lesson)

Queried from the committed EIA-860 vintages through `disposition_table` (verified posture for
the 2020 vintage, reversal registry applied where its clean partition exists — `data/clean`
was still rebuilding at query time, so the T1-H counts are an upper bound on what the solve
will load):

| ISO | T1-H window (vintage 2020, verified), live rows in 2021–2025 | T1-F window (default vintage), live rows in 2026–2030 |
|---|---|---|
| PJM | **28 rows / 7,824 MW** — coal 6,619, gas_st 996, gas_cc 142, oil 68; by year 2021: 1,242 · 2022: 3,917 · 2023: 1,935 · 2024: 285 · 2025: 446 (Chalk Point, Waukegan, Will County, Morgantown, Avon Lake, Cheswick, Chesterfield, Yorktown ≥300 MW) | 16 rows / 8,201 MW — coal 5,939 (Kincaid 2027, Cardinal + Rockport 2028, Brandon Shores 2029), gas_st 1,257, oil 792, gas_ct 212 |
| NYISO | **16 rows / 512 MW** — gas_ct 507 (2023), oil 5 | 2 rows / 22 MW |
| NEISO | 15 rows / 2,964 MW — gas_cc 1,884, oil 660, coal 400, gas_ct 21 (D46 measured this set) | 5 rows / 144 MW |
| MISO | 55 rows / 11,075 MW — coal 9,514 (D42 measured this set) | **52 rows / 17,536 MW** — coal 13,119, gas_st 3,305, gas_ct 951 (J H Campbell, Schahfer, Sherburne, Baldwin, South Oak Creek …) |

Two consequences stated now: **at NYISO the channel is nearly empty** (0.5 GW of 2023 CTs),
so the dates flip cannot be what moves NYISO's rows; **at PJM it is large and coal-heavy
and lands inside the 2022 decision cohort**, so the L1 replay is NOT a re-run of D45's L1 —
it is the first PJM measurement of the channel (the "OPEN HERE" the PJM matrix cell asks
for).

---

## 2. PREDICTIONS (graded at full magnitude in the finding §7)

### 2.1 The D45 predictions, re-affirmed or amended at the HEAD posture

**P1′ — L1 (PJM live): the curve still pays $0 in the 2023 and 2024 screens and its cap in
2025.** AMENDED from D45 P1 (which said $0 in *every* screen year and was already partly
wrong on 2025). The dated exits (~6.6 GW coal, mostly 2021–2023) leave the fleet BEFORE the
screen, so the entering positions come in **lower than D45's 1.171 / 1.137 — predicted
1.11–1.15 (2023) and 1.07–1.12 (2024)** — still above the vintage zero-crosses
(1.065 / 1.064), so `capacity_revenue_usd` is 0.0 for every candidate in both years; 2025
enters SHORT (≤ 0.96) and pays the 2025/26 cap. Falsifier: a strictly positive capacity leg
in 2023 or 2024, or a 2023 entering position ≥ 1.16.

**P2′ — L1 retirements: the over-fire GROWS and the non-coal classes open, because the
dates channel ADDS exits on top of a cap-bound economic cohort it does not displace.**
AMENDED from D45 P2. Mechanism: the exit-rate cap budgets the ECONOMIC screen only
(`exit_rate_cap_mw` is an argument of the screen; dated exits ride step 0's machinery and
bypass it), and the screen still fails essentially the whole fossil fleet at a $0 leg, so
the cap re-fills its ~18 GW coal cohort from the undated coal that remains. Predictions:
`retire.total_gw` **20–28 GW, central 24** (vs 15.062 actual, FAIL, sign +); coal **18–26 GW**;
`gas_st` **0.7–1.2 GW** (Yorktown-class dated steam, off exactly zero), `gas_cc` 0.1–0.2,
`oil` ~0.07, `gas_ct` 0.0; `unit_recall_gt300` **≥ 0.80, plausibly 0.85–1.00** (the dated
set carries the large true exits — a HIT here is the channel working, not the screen);
`false_retire` **FAIL and LARGER than 7.839 GW**. Rule-14 reading, stated now: this is the
expected signature of a faithful exogenous input over an unfaithful $0 clearing half — the
repair is §2.3 of the finding (basis devintage + the clearing half), not the channel.
Falsifier: total < 18 GW, or recall < 0.70, or `gas_st` still exactly 0.000.

**P3′ — L1 vs L4 (the one-field PJM A/B): the fixed leg retires LESS; the recall need not
fall.** RE-AFFIRMED on the total, AMENDED on recall. At $77.43/kW-yr × ~0.83 accredited coal
kW ≈ $64/kW-yr the leg clears the coal cohort's median $14.8/kW-yr gap, so L4's ECONOMIC coal
collapses to **0–5 GW** while its dated exits are identical (exogenous): L4 total **8–13 GW**
(the dated 7.8 GW plus a small economic residual), i.e. **lower than L1 by 10–18 GW**. D45 P3
predicted L4's recall would fall below 0.70; at HEAD the dated channel carries the ≥300 MW
targets in both legs, so L4's recall is predicted to **stay ≥ 0.70** — the amendment's
reason is the channel, stated before the solve. Falsifier: L4 total ≥ L1 total.

**P4′ — the PJM clearing-half reading** stands as the finding §2 already wrote it (a basis
artifact; 2–4 points past the cleared position on the auction's own UCAP basis). New at
HEAD: the restated positions fall by the dated exits' UCAP (~5–6 GW ⇒ 3–4 points), so the
2022/2023 entering screens on the restated basis land **1.04–1.07 — AT or within one point
of the market's CLEARED position (1.051–1.055)** — which would make the $0 reading a
pure-basis artifact in those years (on the restated basis the curve would pay $15–25). This
is the one prediction that could CHANGE §2.2's reading; if it holds it is appended as a
dated correction, not edited in. Falsifier: restated entering positions still ≥ 1.075.

**P5′ — L2 (NYISO live, flat $110): zero economic exits; the dated CTs put `retire.total_gw`
IN BAND for the first time.** AMENDED from D45 P5. The flat $110/kW-yr pays every candidate
through, so economic retirement events are **exactly zero in every year**; the announced
nuclear exit (1.036 GW) plus the channel's 507 MW of 2023 gas_ct give **1.45–1.60 GW,
central 1.54** against 1.488 actual — **PASS on the ±10 % total band** (D45 predicted FAIL
at −30 %, which was true of the pre-D44 posture). `gas_ct` 0.45–0.55 GW vs 0.398 actual;
`unit_recall_gt300` 1/1 PASS; `false_retire` ≤ 0.15 PASS. Stated now so it cannot be
claimed as skill afterwards: **a PASS here is the exogenous channel landing on a small
target, not the screen — the screen decided nothing.** Additions: storage **exactly
0.000 GW** (the D37-class shut channel, predicted to recur); solar / gas_ct / shares band
FAILs persist (over-build, bounded by the entry-rate ladders now). Falsifier: any economic
retirement event, or storage entry > 0, or total outside 1.3–1.7 GW.

**P6′ — L3 (NYISO curve-ON at HEAD): the latent flip arms again, gas_st-led.** RE-AFFIRMED.
With the published curve consulted at the model's own census position (**1.12–1.35** in
2023–2025, past the 1.12 zero-cross in at least two of the three scored screen years), the
capacity leg collapses to ≤ $10/kW-yr there and downstate steam fails its bar:
`retire.total_gw` **2.0–4.5 GW, central 3.0**, **`gas_st` ≥ 1.5 GW** of it, `false_retire`
FAIL (≥ 0.5). Falsifier: L3 within 0.3 GW of L2 (the curve inert), or the excess led by any
class other than gas_st / oil.

**P7′ — the NYISO position reading.** RE-AFFIRMED with a wider band. L2's entering
positions exceed the published NYCA positions (1.043–1.083) by **+5 to +25 points** in
2023–2025 (the extcap intake added ~2.75 GW UCAP since the 2026-07-14 ledgers D45 projected
from), decomposing into a REQUIREMENT half (HEAD's single-vintage 1.0797 × weather-year
peak vs the published 33.4–34.6 GW UCAP requirement: the model's bar is **1.5–4 GW LOW**)
and a SUPPLY half whose sign is NOT pre-committed. The 2021 base-year position is predicted
**BELOW the published 1.049 (0.95–1.05)** — the base fleet is under-accredited (hydro, SCRs)
before the entry over-build pushes the later years long. Falsifier: any 2023–2025 entering
position below the published one.

**P8′ — verdict rows.** All five T1-H keys read **HOLD** before and after (FC-3 FAIL on
every leg — P5′'s total-band PASS does not clear the additions bands). `nyiso-t1h` FC-7
moves FAIL → CAVEAT as an INSTRUMENT change (the harness now writes `run_config.json`), never
a model improvement; the other four FC-7 stay CAVEAT (DOF ledger). NYISO t1f: **PROMOTE
holds** (FC-1/FC-2 PASS both; FC-7 PASS via the built ledger; FC-5 SKIPPED by the D46
precedent). PJM t1f: **HOLD holds**, I7 and I12 still FAIL. MISO t1f: **HOLD holds**, I3
still FAIL. Determinations: no flip on any key.

**P9′ — the two arming questions, on conditions fixed NOW (re-affirmed verbatim from D45
P9, with one addition).**
- **NYISO — consult the published curve at default?** Recommend ARM only if ALL of: (a)
  L3's `retire.total_gw` in the ±10 % band; (b) L3's `false_retire` in band; (c) L3's
  entering positions within ±3 points of the published NYCA positions in every scored year.
  **Any two of three is not enough.** Prediction: none of the three is met; the honest
  reading is "position artifact first, curve second" — the FF-3D flip stays withheld and the
  identified repairs are routed. ADDED condition (d), because P5′ makes it necessary: the
  L2 total-band PASS, if it lands, is NOT evidence for the curve-OFF posture either — it is
  the exogenous channel; the curve-OFF recommendation rests on the position reading alone.
- **PJM — does the curve-ON over-fire survive the corrected position?** D45's zero-solve
  re-screen (finding §3(a)) already answered "no, not at the market's price"; L4 is the
  one-field control that answers it on the live stack. Pre-stated reading: **L4 retires less
  and its recall holds (P3′)** ⇒ the D6 object is confirmed as the clearing half + basis,
  not a curve shape; **no PJM default moves either way** (the curve is the published design
  and the 2028/29+ floor makes $0-at-long impossible forward, D28 §4).

### 2.2 The NEISO shipped-posture leg (L5)

**P10 — L5 retires MORE than the armed D46 leg, gas_cc-led, and reads WORSE on every
gated row.** The Net ICR lever moved the armed positions onto the real FCA 14/15/16 to
±3.3 points where the control read +21 points long in the first scored year (D37); the
shipped posture is therefore the LONGER one, and a longer position pays less and retires
more. Predictions vs `neiso-t1h-pre-d45r` (4.447 GW): `retire.total_gw` **6–9 GW, central
7.5** (the d37-control read 7.566 with dates OFF; dates ON re-routes ~0.8 GW of coal out of
the economic channel and adds the 0.66 GW oil / 0.5 GW gas_cc derates), band FAIL flipping
sign from −11 % UNDER to **+20…+80 % OVER**; `gas_cc` **≥ 4 GW** (the control's 5.335);
coal economic **0.0** (D46's reading at the same posture: the dated set exempts none of the
in-window coal, yet the re-ranking took the coal exits away — predicted to hold under the
shipped lever too); `unit_recall_gt300` 3–4/6 FAIL; `false_retire` **≥ 0.5 FAIL** (the
control's 0.583). Additions byte-identical to D46's except where the longer position
starves the entry screen. Falsifier: L5 total ≤ 4.447 GW, or gas_cc < 2.5 GW.

**P11 — the L5 vs `neiso-t1h-d37-control` pair (lever OFF both, dates OFF → ON) reproduces
D46's re-routing sign:** coal economic 0.791 → **0.0**, gas_cc economic UP, oil off zero
(0.5–0.7 GW), total DOWN from 7.566. Falsifier: coal economic > 0.3 GW in L5.

### 2.3 The T1-F legs (F1–F3)

**P12 — NYISO t1f: PROMOTE holds; nothing the dates channel can move (22 MW in-window).**
All 14 invariants PASS; I7 margin stays ≥ +2 GW in every year; FC-2 backstop share ≤ 10 %
(predicted 0 %). CCS (RGGI carbon): retrofits **may** clear on the corrected constants —
NO direction predicted (NYISO's host economics were never dispositioned by D41, and D46
showed the per-ISO result does not transfer); read, not graded. Wall 8–20 min, ~3 GB.

**P13 — PJM t1f: HOLD holds and the I7 misses WIDEN.** The channel removes ~8.2 GW in
2026–2030 (coal 5.9: Kincaid 2027, Cardinal + Rockport 2028, Brandon Shores 2029) from a
leg that already misses I7 by 3.3 / 4.8 / 5.7 GW in 2028 / 2029 / 2030 and whose only
response channel (the gas_ct backstop ladder) is cap-bound at ~0.8–1.7 GW/yr. Predictions:
I7 FAIL in **≥ 3 years, plausibly 4 (2027 joins)**, 2030 miss **≥ 8 GW**; I12 FAIL persists
and deepens; backstop share **rises above 25.3 %** (may cross the 30 % FAIL bar — 50/50, not
committed); FC-8 CAVEAT (≥ 8 GB); determination HOLD. CCS at carbon = 0: **zero
conversions** (D41 §4.3's own PJM reading, re-tested here at the corrected constants —
D46's ERCOT miss on the same claim is noted, so confidence MED not HIGH). Wall 15–40 min,
~9 GB. Rule-14: every one of these is the expected signature of removing real dated
capacity from a leg whose entry side is under-built (D39), not a regression.

**P14 — MISO t1f: HOLD holds; the dates channel is the largest single input the leg has
ever received (17.5 GW in-window, 13.1 GW coal) and the invariants read WORSE.** I3 slack
FAIL persists and grows (2029/2030 slack > 0.03 % of load; 2028 may join); **I7 joins the
FAIL list in at least one year** (MED); I12 leaves its band in ≥ 1 year (MED); backstop
share rises off 0.0 % (may cross 10 % → CAVEAT). CCS at carbon = 0: zero conversions (MED,
same caveat as P13). Wall 20–45 min, ~10 GB. Determination HOLD.

**P15 — cost.** No leg exceeds 2× its measured-factor price; neither F2 nor F3 approaches
the 2 h STOP. Every realized cache key matches its pre-declared value (8/8).

### 2.4 Cross-lane safety

Nothing outside `pjm-t1h`, `nyiso-t1h`, `neiso-t1h`, `nyiso-t1f`, `pjm-t1f`, `miso-t1f`,
their `-pre-d45r` preserves and the two probe keys moves in `ff-verdicts.json`; the board
edit touches the PJM / NYISO / NEISO / MISO blocks only, FC legs + gate (b)/(c) only where a
record moved, gate (a) never; `check_gate_a_provenance.py` reads OK before and after (it
reads OK at `a8464861`: 6 rows). Matrix (rule 28): no verdict letter moves; PJM and NYISO
receive their own measured `fossil_announced_exits` evidence (rule 25) exactly as D46 §6
stamped the other four; NEISO's and MISO's cells gain the L5 / F3 citations only.
`caiso-t1h` / `caiso-t1f` are deliberately NOT touched (the CAISO lane is promoting again).

## 3. Kills

- **K-a — solve budget.** Any leg that OOMs or exceeds 2× its price is reported and NOT
  registered; years are never trimmed. The 2 h STOP on F2/F3 is absolute.
- **K-b — no parameter moves, no field added.** A miss that "wants" a tuned constant is an
  open root-cause item routed onward (rule 21). `capacity_market_clearing_by_iso` ships
  unchanged; NYISO stays absent from it; `neiso_net_icr_requirement` ships `False`.
- **K-c — rule 22.** T1-H solve years {2021, 2023, 2024, 2025}, 2022 bridged and never
  scored; scoring bounded to 2023–2025; T1-F 2026–2030 on forward drivers only; the holdout
  freeze untouched; nothing scored against measured H1-2026.
- **K-d — rules 13/14.** The published NYCA / RPM quantities and the SOM margins are
  VALIDATION observables; nothing in any leg targets them.
- **K-e — rule 27.** Local edits, exact on-disk bytes pushed; every pushed file ≥ 300 lines
  (`register_forecast_run.py`, `ff-verdicts.json`, `program-status.json`, the matrix shards,
  the D45 finding, every `run_config.json`) is blob-verified against the remote before the
  next commit.
- **K-f — rule 25.** Four ISOs, four separate readings; no parameter or verdict transfers
  between them.
- **K-g — the preserved baselines.** `*-pre-d45`, `*-pre-d46`, `*-pre-d37`, `*-d42-*`,
  `*-d37-control` and every other suffixed record are never written; on any collision the
  lane STOPS and routes.
