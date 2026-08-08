# FFR-8A — Diagnose and repair the forward price object's missing scarcity content

**Session.** FFR Wave 8, DIAGNOSIS + REPAIR lane (owner decision D-21(a), DEFERRED at sitting
Addendum V.6, RE-OPENED by the owner at Addendum AC.1, 2026-08-07). Branch
`claude/forward-price-scarcity-repair-3ak5b9`, off `origin/main` `82edc344`. Model: Fable
(rule 27 — runner/model core).

**Charter.** FFR-6A verdict row 1 (`docs/handoffs/ffr-6a-margin-gap-decomposition-2026-08-05.md`
§5): the repaired unified lookahead's pro-forma scarcity is ZERO on a 21.9–31.8 % RM fleet
(p_mean $9.54–10.49, p_max $24.4–46.2, zero hours > $100, reserve signal 0.000 at the
2024/2025 screens) while the measured 2024/2025 market priced 161/217 h > $100 and the energy
price-level/tail term is 96–100 % of the per-fuel margin gap. Diagnose from published market
design only, then repair with zero fitted parameters. The bars and reserve legs are EXONERATED
(FFR-6A §3.2, re-verified FFR-7C §3 row 2) and are not revisited. **The validation instrument
is price-side** (FFR-7C §5): this window can only FALSIFY a screen via exits — a correct
object must produce ≈ 0 economic exits AND approach the measured scarcity-hour content.

**Rule-1 posture.** Nothing here is tuned toward 1.534 GW (or the corrected 2.294 GW), toward
the measured price curve, or toward any residual. Every repair input is a published market
design constant, a published-methodology quantity model, or the model's own outage machinery;
the repaired level is a MEASUREMENT and is reported as-is. No lift recommendation — the
FH-4/FH-5 determination is the manager's (Addendum I.1, V.3 as sharpened by FFR-7C).

---

## 1. PRE-REGISTRATION

*Everything in §1 was written and committed BEFORE any probe was run, any arm solved, or any
repair measured. Nothing in §1 changes after.*

### 1.1 The diagnosis protocol (Phase 1)

The four chartered terms, each measured at the 2024 and 2025 screens on the FFR-5D unified
arm's own stack (control re-run, §1.3) plus committed measured data:

* **(a) DETERMINISM / the reserve QUANTITY.** The as-built tail prices
  `reserves = top_of_stack − net_load` — the INSTALLED availability-derated headroom of the
  whole thermal fleet over served net load (`runner.py::_lookahead_reprice_signal`). The
  published ORDC prices REALIZED ONLINE reserves — RTOLCAP (+ RTOFFCAP for the second
  half-hour), the committed on-line headroom telemetry (NP6-905-CD), whose measured 2024
  distribution has mean 16.7 GW and a low tail that dips to 4–8 GW on tight evenings.
  Measure: the full-hour distribution of the arm's pro-forma headroom vs the LOLP knee
  (the reserve level where the published curve's adder reaches $10/$100/$1000), against the
  measured RTOLCAP+RTOFFCAP distribution for the same years. Expectation stated in advance:
  the arm's headroom never approaches the knee (that is WHY the adder is identically zero) —
  the missing structure is the COMMITMENT layer (installed ≠ online) plus the REALIZATION
  distribution (outage/weather dips), not the curve.
* **(b) THE ORDC IMPLEMENTATION vs the published design.** Parameter-by-parameter diff
  (§2.2 table) of the code's construction (`results/scarcity.py::ordc_adder`, `lolp`) against
  the published design: VOLL, X (MCL), μ/σ (NP6-576-ER by season/TOD block), the PUCT 48551
  curve shift, the OBDRR048 multi-step floor and its 2023-11-01 effective date, the two
  half-hour LOLP terms, RDPA, and the post-RTC-B AS demand curves. Plus a REPRODUCTION test:
  the implemented curve evaluated on the MEASURED 2024/2025 reserve series
  (`rtolcap`/`rtoffcap`, NP6-905-CD) against the MEASURED `rtorpa` series, at BOTH parameter
  sets in the repo — the flat fallback (`ordc_lolp_mu_mw=0`, `ordc_lolp_sigma_mw=1400`, the
  arm's as-run params since the harness sets no `ordc_lolp_params_path`) and the committed
  NP6-576-ER table (`data/raw/_validation-source/ercot_ordc_lolp_params.csv`, μ≈904–947 /
  σ≈1333–1368 by season). This is a TRANSCRIPTION validation of a published formula against
  the formula's own published output — the parameters remain the published ones; nothing is
  fitted. Whichever transcription reproduces the published adder series is the repair's
  parameter set; if NEITHER reproduces it, that is a finding and the element escalates.
* **(c) FLEET-LENGTH INHERITANCE.** The object prices the EVOLVED fleet (additions 17.0 GW
  vs 55.4 actual; RM 21.9–31.8 % vs measured 34.8 % in 2024). Quantify by re-pricing the
  SAME construction on the known-vintage actual fleet (diagnostic re-price, no solve): the
  arm's thermal fleet at the 2024 screen (68.0 GW: coal 13,964 / gas_cc 37,241 / gas_ct
  11,413 / gas_st 354 / nuclear 4,980 MW — the FFR-6A revenue-stack log) is SHORTER than the
  actual 2024 thermal fleet (the vintage fleet minus 2.3 GW of actual exits — the 10.9 GW
  gas_st wave did not happen), and the actual VRE/storage build (55.4 GW) far exceeds the
  arm's. Expectation stated in advance: the actual (longer) fleet has MORE headroom, so the
  same construction produces the same zero — the fleet-length term has the WRONG SIGN to
  explain the missing scarcity (the real market priced 161 h > $100 at a HIGHER reserve
  margin than the arm's), and the shortfall is ~100 % construction. The term is measured to
  bound it, not because it is suspected.
* **(d) THE 2023 ECRS TERM.** Scope whether reproducing 2023-level revenue needs the FFR-6A
  verdict row-2 measured AS-quantity input. Two measured facts fix the scope: (i) in THIS
  window design the into-2023 screen consumes the growth-scaled 2021 object (2022 bridged —
  FFR-5A §2), never a 2023-solve object, so the 2023 ECRS energy-price term is OUT of the
  critical path for the failing 2024/2025 screens; (ii) the AS-quantity effect on the
  2024/2025 objects is scoped by comparing the model's existing FORWARD AS-requirement model
  (`results/scarcity.py::ercot_as_forward_requirement_mw`, NP3-160-CD methodology,
  coefficients already in `model/reserves/spec.py`) against the measured ASPLANNP433 plan for
  2024/2025 — both already in-repo, so NO new intake is needed either way. The repair
  consumes the FORWARD model (element E2, §1.4); the measured-plan row-2 intake is NOT
  performed.

**The ablation chain (the per-term contribution table).** The Phase-2 repair elements are
measured as a cumulative chain on the control arm's own dumped stack at each screen, so each
term's contribution is a measured number, not an attribution argument:

* **A1** — the as-built unified tail (installed headroom, flat fallback params): must
  reproduce the recorded zero (p_mean $10.49/$9.54, p_max $24.4/$46.2, 0 h > $100).
* **A2** — A1 + element E1 (committed-capability reserve quantity, point value).
* **A3** — A2 + element E3 (published NP6-576-ER curve parameters, if (b) validates them).
* **A4** — A3 + element E4 (LOLP-bearing outage-uncertainty integration).
* **A5** — A4 + element E2 (pre-RTC AS-plan withholding in the energy-stack search).

Read per step: h > $100, h > $1000, price mean/max, and the per-fuel pro-forma margin
(`Σ_t max(0, p_t − mc_f) × avail × 0.9`, the FFR-6A replica construction at the screen's own
mc levels) vs the FFR-6A replica-at-measured-prices column and the bars.

### 1.2 Phase-1 data sources (all committed, none new)

* Measured reserves/adders: `data/raw/ercot/ercot_{2024,2025}_ordc_reserves_hourly.parquet`
  (NP6-905-CD; columns hour, system_lambda, prc, rtolcap, rtoffcap, rtorpa, rtoffpa,
  rtolhsl, rtordpa; 2025 tail past the 2025-12-05 RTC+B go-live is NaN and excluded).
* Published LOLP stats: `data/raw/_validation-source/ercot_ordc_lolp_params.csv`
  (NP6-576-ER, report 13233).
* Measured AS plan: `data/raw/ercot/ASPLANNP433_{2024,2025}.parquet` via
  `results/scarcity.py::ercot_as_plan_requirement_mw`.
* Measured prices (for the replica columns only, never an input):
  `data/raw/_validation-source/actual_lmp_hourly_ERCOT.parquet` — the standing SOM replica
  basis (`scripts/probes/fom_scarcity_revenue_audit.py`), reproduction-gated exactly as
  FFR-7C §2.1 did.
* The control arm's own stack internals: the §1.3 diagnostic dump.
* 2022 IS BRIDGED AND NEVER READ. No file for 2022 (or any pre-2023 year) is opened by any
  probe in this lane. The measured-data reads above are 2023–2025 training-tier years only.

### 1.3 The control arm (invocation 1 of 2) and its reproduction gate

The FFR-5D unified arm re-run verbatim (ffr-5d handoff §2 + its one flag), with ONE addition:
a diagnostic dump of the lookahead stack internals (net_load, per-hour top-of-stack, the
as-built reserves series, the tail adder, and the final signal) written next to the evolution
ledgers when `capacity_screen_unified_lookahead` is armed. The dump is output-only — no
config field, no cache-key change, no solve-path change; the reproduction gate below proves
it changed nothing.

```
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr8a-unified
```

Cold, 4 LP years (2022 bridged), years sequential (rule 12). **Reproduction gate (all from
the FFR-5D-M/FFR-6A record, `docs/handoffs/ffr-5d-price-object-2026-08-05.md` §3 /
`ffr-6a-...md` §3): runtime `cache_key=49eac64f146b3460`; 2022-ledger gas_st decided 45 /
10,942.9 MW at net $17.90 vs bar $35.00, executed in-ledger; 2025-ledger coal decided 11 /
1,482.1 MW at $0.04; entry_capped 564 / 62,971.7 MW (2024) and 554 / 66,060.5 MW (2025);
screen p_mean $10.49 / p_max $24.4 (into-2024) and $9.54 / $46.2 (into-2025); scored exits
2023–2025 = 0; additions (decision basis) 17.0 GW.** A miss on any of these voids the arm
and stops the lane (drift diagnosis before anything else). This run doubles as the Phase-3
control read — its recorded expectations are the FFR-5D registered arm's, reused, not
re-derived.

### 1.4 The repair elements (Phase 2), each with its published-design identification

Gating: **ONE new `ScenarioConfig` field, `capacity_screen_scarcity_restoration`, GATED
default OFF**, registered in `_CACHE_KEY_OPTIONAL_FIELDS` + the defaults ledger in the same
commit, matrix row in the same PR (rule 28(c)), `__post_init__`-validated to require
`capacity_screen_unified_lookahead` (the repair extends that object's armed stack — one
object, one gate per layer) and `iso == "ERCOT"` (the committed-capability tables are
ERCOT-identified; rule 25 — no cross-ISO transfer; other ISOs enter as `U` cells). Byte
identity of every unarmed path proven by test; the default-key pin tests run before AND
after (the nyiso-128 discipline).

* **E1 — the reserve quantity: committed on-line capability, not installed headroom.**
  `R_online(t) = min(RTOLCAP_fwd(t) + storage_as(t), phys_headroom(t))`,
  `R_full(t) = min(R_online-basis + RTOFFCAP_fwd(t), phys_headroom(t))`, where
  `RTOLCAP_fwd`/`RTOFFCAP_fwd` are the model's OWN forward committed-capability formula
  (`results/scarcity.py::ercot_rtolcap_forward_supply_cap_mw` share tables:
  `ERCOT_RTOLCAP_FWD_ONLINE_SHARE`/`OFFLINE_SHARE` per class × season × net-load decile,
  deliverability 0.8959/0.7756 — CAMPD-quantity-identified, never a price;
  `docs/handoffs/ercot-rtolcap-forward-2026-07.md`), evaluated on the ENTERING year's own
  net load and the EVOLVED fleet's class capacities; `storage_as` = the evolved storage
  fleet's power × `ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC` (0.35, the observed AS-award /
  installed ratio — the formula's own mode-aware storage term, on the evolved fleet rather
  than the base-year default); `phys_headroom` = the stack's own per-hour available capacity
  minus served net load (the FFR-5D repair-(c) object) — the physical bound commitment can
  never exceed, which is what carries energy-shortage pricing to VOLL through the same
  curve. The load-resource (RRS-UFR) term is deliberately ABSENT: the deliv coefficient was
  fit to raw measured RTOLCAP with only storage netted out, so LR capability is already
  inside 0.8959 (`scripts/data/derive_ercot_rtolcap_forward.py` — adding it separately
  would double-count). Under this element the storage peak-shave (FFR-5D repair (a))
  correspondingly uses only the non-AS-committed share (1 − 0.35) of storage power/energy —
  the same MW cannot simultaneously hold an AS award and arbitrage the peak; one constant,
  two disjoint uses.
* **E2 — pre-RTC AS-plan withholding in the energy stack.** The pre-RTC design procures the
  AS plan day-ahead and SCED dispatches around the awards: capacity holding responsive AS is
  not offered to energy, so the energy-stack search runs at
  `net_load(t) + AS_held_thermal(t)` where
  `AS_held_thermal = clip(REGUP + RRS + ECRS − LR_credit − storage_as, 0, ·)` — the
  responsive (10-minute) products held on thermal units. Quantities from the model's OWN
  forward AS-requirement model (`ercot_as_forward_requirement_mw`, NP3-160-CD methodology,
  published-coefficient forms; drivers from the entering year's own load/wind/solar), the
  forward LR enrollment credit (`ercot_load_resource_reserve_forward_mw`), and the same
  storage_as as E1 (each MW counted once). NSPIN is excluded — a 30-minute product the
  offline quick-start tier supplies (the RTOFFCAP definition), not withheld from the online
  energy stack. ECRS is design-date-gated (launched 2023-06-10; zero for entering hours
  before the launch — the published design date, mirroring the measured plan's own onset).
  This is FFR-6A verdict row 2's admissible channel entered through the FORWARD methodology
  model rather than the measured plan — the quantities are the input, the price outcome
  stays the model's. The ORDC R does NOT net these quantities (RTOLCAP counts AS-held
  headroom as reserve — the published definition, the `ordc_as_plan_mw=0` validation).
* **E3 — the published LOLP parameters.** The tail evaluates the published NP6-576-ER
  (μ, σ) seasonal values (the committed table's content, landed as cited constants) instead
  of the provisional flat fallback — CONDITIONAL on the §1.1(b) reproduction test validating
  that transcription against the published design's own adder series; if the test refutes
  the table, the element escalates rather than lands. VOLL ($5,000 HCAP, 16 TAC 25.509),
  X = 3,000 MW (OBDRR038), shift 0.5σ (PUCT 48551) are already the shipped published values
  and do not change. The OBDRR048 multi-step floor is date-gated by the ENTERING year
  (effective 2023-11-01) in the repair's tail — the design's own effective date, replacing
  the mode-keyed gate that applies it anachronistically to pre-Nov-2023 entering years
  (inert before this repair because the tail never left zero).
* **E4 — the LOLP-bearing uncertainty term from the model's own outage machinery.** The
  screen prices the entering year a year ahead; the realized reserve in any hour differs
  from the point forecast by (among other things) the forced-outage realization. The WEFOR
  statistical model is per-unit independent (`data/fleet/arrays.py::_thermal_outage`,
  GADS-anchored rates), so the fleet's capacity-on-forced-outage distribution has variance
  `σ_R²(t) = Σ_plants q_p(t)(1 − q_p(t)) · P_p²` — the model's own rates q (the same
  seasonal composition the availability builder applies, `wefor_multiplier` and
  `gas_st_wefor_base_override` included; `eford` for units outside the WEFOR table),
  aggregated at the model's own plant grain (tranches of one plant share its outage state).
  The tail then prices `E[adder(R + ε)]`, ε ~ N(0, σ_R(t)²), by fixed-order Gauss–Hermite
  quadrature — LOLP-bearing, not smooth: the expectation carries the low-probability deep
  reserve dips the point evaluation cannot see. No new parameter: the variance is the
  mathematical consequence of the model's own documented independence structure; the
  published curve's own σ (intra-hour projection error) composes orthogonally (different
  horizon) and is never rescaled (`correlated_outage_sigma_scale` stays 1.0 and untouched;
  the correlated cold-event derate keeps shifting only the MEAN availability, the D.6 seam,
  which enters through phys_headroom/topofstack). λ in `(VOLL − λ)` is held at the point
  value (the factor moves < 1 % across the ε range; documented approximation).
* **RDPA** is measured in Phase 1 and NOT repaired: the ORDC-regime forward representation
  prices to fundamentals (`effective_reliability_deployment_mw` returns 0 by design —
  the deleted fitted analogue stays deleted, rule 26), and the measured RTORDPA is
  near-inert in the target years (2024 mean $0.23/MWh, max $90).

Every element is rule-13 tested in §2: reproducible from published design/physics, forward
analogue, condition-responsive. If an element cannot be built without inventing a parameter
it STOPS and escalates; the rest land.

### 1.5 Phase-3 measurement (invocation 2 of 2) — pre-registered reads

Repair arm, identical to §1.3 plus the one new flag:

```
uv run python scripts/run_capacity_hindcast.py \
  --iso ERCOT --vintage 2020 --start-year 2021 --end-year 2025 \
  --forward-from-base --arm realized --capacity-screen-unified-lookahead \
  --capacity-screen-scarcity-restoration \
  --out-dir results/hindcast/ercot-2021-2025-t1ff-armr-ffr8a-scarcity
```

Cold, 4 LP years, sequential. Registered as
`ercot-2021-2025-t1ff-armr-ffr8a-{unified,scarcity}` in the HINDCAST namespace only
(`register_hindcast.py`, `meta.kind="full_forward"`) — never the backcast registry
(plan §7.5). Reads, fixed now:

* **(i) THE PRICE-SIDE VALIDATION (the primary read).** The repaired object's per-screen
  hour distribution — h > $100, h > $1000, mean, max — vs the MEASURED distribution
  (2024: 161 h > $100, mean $26.82, max $3,060; 2025: 217 h > $100, mean $32.49, max
  $1,570) and the per-fuel screen margins vs the FFR-6A replica margins (2024: coal 75.4 /
  gas_cc 86.7 / gas_ct 65.6 / gas_st 65.6; 2025: 97.2 / 76.4 / 47.0 / 47.0 $/kW-yr).
  Reported at full magnitude whatever it shows.
* **(ii) The exit-side falsification checks.** (1) The 10.9 GW gas_st false wave: does the
  repaired 2021/Uri-basis entering-2022 screen still manufacture it? (2) In-window
  executions: must be ≈ 0 economic (FFR-7C bound — any in-window economic execution is a
  falsification signal, not a success). (3) The fleet-wide entry_capped census by ledger
  year (control: none/none/564/554). (4) The FFR-5A coal cohort's event sequence (control:
  never decided at the 2021 screen; decided 11 / 1,482 MW in the 2025 ledger, exe 2027).
* **(iii) Additions vs 55.4 GW actual.** The fleet-length knot is expected NOT to be fixed
  by this lane (the entry screen's own economics and caps are FFR-4/5 lanes' objects; this
  lane changes the price object those screens consume, so additions may move as a side
  effect and are reported, not targeted).

**THE HONEST EXPECTATION, STATED BEFORE THE REPAIR ARM SOLVES** *(completed after Phase 1's
measured decomposition, before invocation 2 — see §3.4; committed in the prereg-2 commit
whose hash the §3.4 header records).*

### 1.6 What this lane will NOT do

No arming, no promotion, no keeper contact, no tuning, no backcast-registry touch, no
matrix-cell verdict beyond `O`/`U`, no lift recommendation, no owner-decision re-opening
(D-21(a) is reported against, not adjudicated). The measured ASPLANNP433 plan is read only
as a Phase-1 validation benchmark for the forward AS model — it is not wired into any solve
path. FFR-6A verdict rows 3 and 4 (bar re-levels; scalar uplift/calibration to the measured
curve) remain REFUSED BY NAME.

---

## 2. Phase 1 — the measured decomposition

*(filled after §1 was committed; nothing above this line changed after. Part A — the
measured-data legs — was probed and committed in the FFR-8A Phase-1/2 session
(`scripts/probes/ffr8a_scarcity_decomposition.py` →
`docs/handoffs/ffr-8a/part-a-measured-2026-08-08.json`); this narrative is written FROM that
committed JSON, no re-measurement. Part B — the A1–A5 ablation chain on the control arm's
dumps — is §2.5, filled by the Phase-3 session after the control arm solved.)*

### 2.1 Leg (a) — the reserve quantity: what the published curve prices vs what the arm prices

The measured NP6-905-CD committed on-line capability (RTOLCAP) for 2024: mean 16,679 MW,
p50 16,197, p5 9,298, **p1 7,874, minimum 5,094 MW** (8,760 h). With RTOFFCAP added (the
second half-hour's offline quick-start tier): mean 21,813, p1 9,515, min 5,099 MW. For 2025
(8,112 h — the series ends at the 2025-12-05 RTC+B go-live, NaN tail excluded): RTOLCAP mean
19,124, p1 8,955, min 7,060 MW; +RTOFFCAP mean 24,610, p1 11,015, min 7,389 MW.

Against the curve's knees (the reserve level where the shipped construction's adder crosses
each threshold, λ = $30): the as-shipped flat-fallback parameter set (μ=0, σ=1400) reaches
$10 at 7,415 MW, $100 at 6,200 MW, $1,000 at 4,578 MW; the committed NP6-576-ER seasonal
table (μ≈904–947, σ≈1333–1368) shifts each knee up ~700–1,000 MW ($10 at 8,102–8,255, $100
at 6,911–7,033, $1,000 at 5,208–5,282 MW).

So the MEASURED online reserve spends ≈1 % of 2024 hours at or below the fallback $10-knee
(p1 ≈ the knee) and its minimum sits between the $100- and $1,000-knees — the real
committed-capability series genuinely visits adder territory a few dozen hours a year. The
§1.1(a) expectation for the arm's own quantity (installed availability-derated headroom
never approaches the knee — that is WHY the arm's adder is identically zero) is quantified
on the arm's dump in Part B (§2.5, row A1); Part A establishes the measured side: **the
quantity the published curve prices is committed on-line capability with a realized low
tail near the knee, not installed headroom.**

### 2.2 Leg (b) — the ORDC transcription and the reproduction test

Parameter diff of the shipped construction (`results/scarcity.py::ordc_adder`/`lolp`)
against the published design, as recorded in the probe's `ordc_params_as_shipped`: VOLL
$5,000 (HCAP, 16 TAC 25.509) ✓; X = MCL 3,000 MW (OBDRR038) ✓; PUCT 48551 shift 0.5σ ✓;
OBDRR048 multi-step floor present ✓ (but mode-keyed rather than date-gated — repaired for
the lookahead tail by the entering-year gate, §3.2); two half-hour LOLP terms (RTOLCAP /
RTOLCAP+RTOFFCAP) ✓; RDPA — not represented in the ORDC-regime forward path by design
(`effective_reliability_deployment_mw` = 0; measured RTORDPA is near-inert in the target
years: 2024 mean $0.23/MWh, max $90.0; 2025 mean $0.40, max $93.4) — NOT repaired, per
§1.4. The one open parameter question was μ/σ: the arm runs the flat fallback (μ=0,
σ=1400; no `ordc_lolp_params_path` set), while the committed NP6-576-ER table carries the
published seasonal values.

**The reproduction test** — the implemented curve evaluated on the MEASURED 2024/2025
RTOLCAP/RTOFFCAP series against the MEASURED RTORPA series, both parameter sets
(`legs_ab.<year>.curve_{fallback,np6_576_er}`; `tightest50_*` = the mean of each series' own
50 largest values):

| year | series | h>$1 | h>$10 | h>$100 | max $ | mean $ | top-50 mean $ |
|---|---|---|---|---|---|---|---|
| 2024 | measured RTORPA | 78 | 26 | 4 | 252.7 | 0.203 | 33.9 |
| 2024 | fallback | 48 | 18 | 6 | 279.0 | 0.181 | 31.5 |
| 2024 | NP6-576-ER table | 77 | 37 | **11** | 639.5 | 0.521 | **89.8** |
| 2025 | measured RTORPA | 15 | 3 | 1 | 414.1 | 0.065 | 10.6 |
| 2025 | fallback | 4 | 1 | 0 | 10.3 | 0.003 | 0.4 |
| 2025 | NP6-576-ER table | **15** | **3** | 0 | 44.5 | 0.014 | 2.2 |

**The result is MIXED ACROSS YEARS.** In 2024 the fallback reproduces the deep tail and the
top-50 magnitude (31.5 vs 33.9 measured; h>$100 6 vs 4) while the table over-produces ~2.6×
(top-50 89.8 vs 33.9; h>$100 11 vs 4) — the table is REFUTED on 2024. In 2025 the table
reproduces the exceedance counts exactly (15/15 h>$1, 3/3 h>$10) while the fallback
under-produces (4/15, 1/3) — but BOTH under-produce the 2025 top-50 magnitude (2.2 / 0.4 vs
10.6 measured). Neither transcription reproduces the published adder series in both years.
Disposition under the prereg's own branches: **E3 escalates as a finding** (§3.3).

### 2.3 The scarcity-hour decomposition — where the measured $100+ content actually lives

The probe's `scarcity_hour_decomposition` splits the measured scarcity hours into energy
(system λ) and adder content. 2024: 192 h RTSPP > $100, of which 184 h had λ > $100 — and
**149 of those 184 had adders ≤ $10**; only **5 h** had adders > $100. Median RTOLCAP inside
the RTSPP>$100 hours: 8,742 MW — ABOVE the $100-knee (6,200 fallback / ~6,970 table). 2025:
228 h RTSPP > $100, 210 h λ > $100, 194 of them with adders ≤ $10, **1 h** adders > $100.
Measured λ itself: 2024 mean $28.79, p99 $158.5, max $2,978.8; 2025 mean $34.77, p99
$134.5, max $1,870.5.

**The measured 2024/2025 scarcity content is λ-led, not adder-led**: the ORDC adder proper
contributes > $100 in 5 (2024) / 1 (2025) hours and a mean of $0.20 / $0.065/MWh. The
161/217 measured h>$100 the charter cites are hours where the ENERGY price cleared high with
the adder small — real-time offer conduct, commitment tightness and fuel-price hours, priced
by SCED's λ. This bounds what any design-faithful forward ORDC repair can restore on the
price side (the §3.4 expectation) — the repair's energy-side element (E2) moves the λ
analogue, but a time-mean-mc static stack cannot (and per rule 1 must not be tuned to)
reproduce real-time λ volatility.

### 2.4 Leg (d) — the forward AS-requirement model vs the measured plan

The model's own NP3-160-CD forward AS model (`ercot_as_forward_requirement_mw`, drivers
from the entering year's own load/wind/solar) against the measured ASPLANNP433 plan
(mean / p95 MW):

| product | 2024 fwd | 2024 measured | 2025 fwd | 2025 measured |
|---|---|---|---|---|
| REGUP | 407 / 502 | 406 / 748 | 433 / 577 | 436 / 666 |
| RRS | 2,710 / 3,011 | 2,722 / 3,128 | 2,737 / 3,058 | 2,739 / 3,145 |
| ECRS | 1,484 / 1,917 | 1,752 / 2,673 | 1,590 / 2,218 | 1,416 / 2,556 |
| NSPIN | 2,762 / 2,980 | 2,684 / 3,614 | 2,793 / 3,071 | 2,886 / 4,167 |

RegUp and RRS means reproduce within 0.5 %; ECRS within −15.3 % (2024) / +12.3 % (2025) —
the newest product, methodology still moving in the published plans; NSPIN within ±3.6 %
(excluded from E2's hold anyway — a 30-minute product the offline tier supplies). The
forward model is validated as the E2 quantity input; the measured plan is NOT wired into any
solve path (§1.6), and per §1.1(d) the 2023 ECRS energy-price term is out of the failing
screens' critical path (the into-2023 screen consumes the growth-scaled 2021 object).

Leg (c) — fleet-length inheritance — carries no Part-A measurement by design: its
quantification is the ablation chain's term-(c) actual-fleet re-price (§2.5), per §1.1(c)
expected to have the wrong sign to explain the missing scarcity.

### 2.5 Part B — the A1–A5 ablation chain on the control arm's dumps

*(filled after the control arm solved and its reproduction gate passed;
`scripts/probes/ffr8a_ablation_chain.py` →
`docs/handoffs/ffr-8a/part-b-ablation-2026-08-08.json`)*

## 3. Phase 2 — the repair as landed

*(filled after Phase 1; the element inventory below is written from the MERGED code at
`origin/main` (PR #3722), not from the plan — names, gates and dispositions are the
as-landed facts.)*

### 3.1 The gate and its registration

`ScenarioConfig.capacity_screen_scarcity_restoration` (`config/scenarios.py:3363`), GATED
default OFF, registered in `_CACHE_KEY_OPTIONAL_FIELDS` AND the defaults ledger in the SAME
commit — **`cc0cbd6`** ("FFR-8A: add capacity_screen_scarcity_restoration (gated
default-off, registered) + backfill ERCOT-176 cache-key registration"). That commit also
carries the FFR-8A pre-work discovery: ERCOT-176's `ercot_offline_commit_offer` +
`ercot_offline_commit_offer_path` had landed on main UNREGISTERED, silently moving the
pinned default cache key `603c2498bf71d21d → efd1cda1683a0ebe` (the nyiso-128 pattern, two
fields at once so the pin test's single-field blame could not name them); registering the
pair restores every orphaned default-config key. `__post_init__` hard-requires
`capacity_screen_unified_lookahead` (the repair extends that object's armed stack — one
object, one gate per layer) and `iso == "ERCOT"` (the committed-capability tables are
ERCOT-identified; rule 25 — other ISOs enter the matrix as `U`). Unarmed byte-identity and
the default-key pin are tested in
`tests/unit/model/test_capacity_screen_scarcity_restoration.py`.

### 3.2 The as-landed element inventory (E1, E2, E4 — the landed tail carries these three)

All in `results/scarcity.py`, consumed by `runner.py::_lookahead_reprice_signal` under the
armed bundle (runner seam at `runner.py:3270–3320`):

* **E1 — `ercot_lookahead_committed_reserves`** (scarcity.py:1566): `(r_online, r_full)` =
  the model's own forward RTOLCAP/RTOFFCAP formula
  (`ercot_rtolcap_forward_supply_cap_mw`, CAMPD-quantity-identified share tables on the
  ENTERING year's own net load and the EVOLVED fleet's class capacities) plus the evolved
  storage fleet's AS-award share, each tier bounded above by the physical stack headroom
  (`min()` — a physical identity: commitment can withhold below the physical bound, never
  create reserves beyond it; headroom below the MCL still pins LOLP to 1, carrying
  energy-shortage hours to VOLL). Raises rather than approximates when the fleet carries no
  plant groups (rule 19 — no silent second construction). The LR term is deliberately
  absent (already inside the deliverability coefficient's fit target — adding it would
  double-count).
* **E2 — `ercot_lookahead_as_hold_mw`** (scarcity.py:1508): the energy-stack search runs at
  `net_load + clip(REGUP + RRS + ECRS − LR_credit − storage_as, 0, ·)` from the forward
  NP3-160-CD model (§2.4-validated); NSPIN and REGDN excluded; ECRS design-date-gated at
  its go-live (`ERCOT_ECRS_LAUNCH_YEAR`/`ERCOT_ECRS_LAUNCH_HOUR` = 2023 / hour 3840,
  2023-06-10; `model/reserves/spec.py:126–127`). Search-target only — the reserve
  quantities do NOT net these MW (RTOLCAP's published definition counts AS-held headroom
  as reserve).
* **E4 — `ercot_lookahead_expected_ordc_adder`** (scarcity.py:1627) over
  **`ercot_fleet_forced_outage_sigma_mw`** (scarcity.py:1401): `E[ordc_adder(R + ε)]`,
  ε ~ N(0, σ_R(t)²), σ_R² = Σ_plants q_p(t)(1−q_p(t))·P_p² from the model's own WEFOR/EFORD
  machinery at the model's own plant grain (seasonal composition, `wefor_multiplier` and
  `gas_st_wefor_base_override` honoured), fixed-order Gauss–Hermite quadrature
  (`_FFR8A_GH_ORDER = 31`, a resolution constant pinned by unit test — order 31 sits within
  0.3 % of order 61 on the worst case near the administrative LOLP=1 pin). λ held at its
  point value inside `(VOLL − λ)` (< 1 % effect, documented approximation); every node and
  the sum respect the `VOLL − λ` protocol cap. The same ε shifts both reserve tiers.
* **The OBDRR048 entering-year date gate — `floor_active_mask`** (scarcity.py:342): the
  multi-step floor applies by the ENTERING year against the design's own 2023-11-01
  effective date (`ORDC_FLOOR_START_HOUR_2023 = 304×24`, `model/reserves/spec.py:95`) —
  replacing, for the lookahead tail only, the mode-keyed gate that applied it
  anachronistically to pre-Nov-2023 entering years (inert before this repair because the
  tail never left zero; the post-solve overlay path keeps its own gate untouched).
* **The storage split** (runner seam): one measured constant
  (`ERCOT_RTOLCAP_FWD_STORAGE_RESERVE_FRAC` = 0.35), two disjoint uses — the AS-award share
  enters the tail's R (E1) and the E2 netting; only the merchant share (1 − 0.35) of
  storage power/energy runs the FFR-5D peak shave. The same MW cannot simultaneously hold
  an AS award and arbitrage the peak.
* **The diagnostic dump** (runner.py:3321–3365): armed with the unified lookahead
  (control and repair arms alike), writes
  `screen_signal_diag_<year>_for_<entering>.npz` next to the year's evolution ledger —
  net loads, top-of-stack, installed headroom, base price, adder, sorted stack, σ_R, class
  capacities, storage/VRE context — self-contained for the offline A1–A5 chain and the
  term-(c) actual-fleet re-price, so the diagnosis never replays a solve. Output-only: no
  config field, no cache-key term, no solve-path change (the control arm's reproduction
  gate is the proof).

### 3.3 E3's disposition — ESCALATED AS A FINDING, not landed

The landed tail carries **E1/E2/E4 only**. E3 — switching the tail's LOLP parameters from
the shipped flat fallback (μ=0, σ=1400) to the committed NP6-576-ER seasonal table — was
pre-committed CONDITIONAL on the §1.1(b) reproduction test "validating that transcription";
§1.1(b) further pre-committed "whichever transcription reproduces the published adder
series is the repair's parameter set; **if NEITHER reproduces it, that is a finding and the
element escalates**."

The measured outcome (§2.2) is the NEITHER branch: the table is refuted on 2024 (deep tail
over-produced ~2.6×) and the fallback is refuted on 2025 (h>$1 4/15; top-50 mean $0.4 vs
$10.6) — no parameter set reproduces the published series in both years. Per the prereg's
own pre-commitment this is **a finding to record, not a judgment call to absorb**: E3 is
NOT landed, and the open question — why the published NP6-576-ER seasonal (μ, σ) over-produce
the 2024 deep tail on the design's own reserve telemetry while the flat fallback
under-produces 2025 (candidate causes: table vintage vs operating year, seasonal blending,
the 2025 series' RTC+B-transition truncation, RTORPA floor interactions) — escalates to the
manager with the FH-4/FH-5 determination (§5). The landed tail therefore evaluates
`resolve_lolp_params(config, ·)` = the as-shipped fallback — retained as the UNCHANGED
shipped configuration (the absence of the E3 change), not as a validated winner. Two
as-landed compressions of this mixed result are noted for the record: the E4 docstring's
"the Phase-1 reproduction test validated the as-shipped fallback" (true for the 2024 deep
tail, not for 2025) and the ablation script's A3 header "REFUTED the committed NP6-576-ER
table transcription (over-produces ~2.6× ...)" (the 2024 read; 2025's count-exact table
result is the counterpoint) — this section and the committed part-a JSON are the full
record. The A3 chain row accordingly records A2 unchanged, with the refuted-table
counterfactual emitted as a clearly-labelled annex column, never a candidate.

### 3.4 The honest expectation (the prereg-2 commit)

*(Committed BEFORE invocation 2 — the repair arm — solves; §1.5 requires it. This section's
content is the prereg-2 commit — hash recorded here: **`ea04f03`** (originally committed as
`4a4cc75`, rewritten to `ea04f03` by a push-discipline rebase onto the then-current
`origin/main` `7fd1c28` BEFORE the repair arm started — same tree, same content; the hash
was backfilled by header-only edits, content untouched). Derived from Part A + the
ablation-chain REASONING alone — the control arm had not finished and the repair arm had not
started when this was written. Nothing below is a target; every line is a falsifiable
statement the §4 reads will confirm or refute at full magnitude.)*

**What the elements can and cannot move, from Part A alone.** The measured scarcity content
the charter cites (161/217 h > $100) is λ-led (§2.3): the adder proper contributed > $100 in
5 (2024) / 1 (2025) hours with mean $0.20/$0.065. The repair's tail elements (E1+E4) act on
the ADDER analogue; E2 shifts the ENERGY-stack search point. A design-faithful tail on a
faithful committed-capability series should therefore restore adder content of the measured
RTORPA's ORDER (mean ≲ $1, tail counts in the tens of h > $1, single digits > $100) — NOT
the measured λ tail (mean $28.79/$34.77, p99 $158/$135), which is real-time offer conduct
and volatility a time-mean-mc static stack cannot reproduce and must not be tuned toward
(rule 1). E2's search shift is bounded by the §2.4 quantities: REGUP+RRS+ECRS forward means
≈ 4.60 GW (2024) / 4.76 GW (2025), minus the forward LR credit and the evolved storage AS
share — a net thermal hold of roughly 1.5–3.5 GW, which moves the marginal unit up the
merit stack in every hour; its price effect concentrates where the stack is steep (the
scarcity shoulder), raising the base price by a few $/MWh on average and more in tight
hours. The forward committed-capability formula (E1) is a share-table point model on
net-load deciles — SMOOTHER than realized RTOLCAP — so its own dips will under-visit the
measured p1 tail; E4's expectation over σ_R partially compensates by pricing the
outage-realization mass the point evaluation cannot see. Directionally the two should
land the tail's content between the point-evaluation zero and the measured RTORPA.

Numbered expectations for the §4 reads:

1. **Tail nonzero but adder-scaled.** Repaired per-screen h > $1 of order 10¹–10²;
   h > $100 of order 10⁰–10¹; h > $1000 zero or low single digits (only E4's expectation
   near the deepest committed dips can reach it). The recorded control zeros (p_max
   $24.4/$46.2, 0 h > $100) must NOT reproduce under the repair — if they do, the repair is
   inert at the screens and that is the finding.
2. **Mean well below measured.** Repaired screen p_mean rises from $10.49/$9.54 by roughly
   $1–5/MWh (E2 shift + small mean adder), remaining WELL BELOW the measured $26.82/$32.49.
   The residual λ-led gap is the honest headline, not a failure of the tail elements.
3. **Max may be large.** A single deep committed-dip hour under E4 can carry an expected
   adder in the $10²–10³ range (protocol-capped at VOLL − λ), so repaired p_max in the
   hundreds is consistent with expectation 2's modest mean.
4. **Per-fuel margins move by single-digit $/kW-yr.** The restored content integrates to
   roughly $1–10/kW-yr per fuel — a FRACTION of the FFR-6A replica margins (47–97 $/kW-yr)
   and far below the bars (21–58.5). Expectation: the margin gap does NOT close; the
   measurement establishes how much a design-faithful forward ORDC restores (≲ ~20 % of
   the replica margins), and the remainder is λ-led content this object does not carry.
5. **The 10.9 GW gas_st false wave shrinks; full disappearance is the open question.** The
   control decided gas_st 45 / 10,942.9 MW at net $17.90 vs bar $35.00 (into-2022 screen,
   2021 stack basis). The repair only ADDS revenue, so the wave cannot grow. It vanishes
   iff the restored content at that screen adds ≥ ~$17.1/kW-yr to gas_st's
   dispatch-weighted margin — plausible if the 2022 entering net load carries genuinely
   tight hours against the 2021 fleet, but not guaranteed by expectation 4's range. Either
   branch is reported as measured; partial shrink (fewer units/MW deciding) also counts as
   movement toward the truth (actual gas_st exits in-window: 0.0).
6. **In-window economic executions stay ≈ 0** (FFR-7C falsification bound). The repair
   raises pro-forma revenue everywhere, so any NEW economic execution the control did not
   carry would be a mechanism bug, not a market finding.
7. **entry_capped stays fleet-wide.** With bars at 21–58.5 $/kW-yr against expectation 4's
   restored margins, the adequacy cap keeps doing the retention work: entry_capped counts
   remain at the control's order (564 / 62,971.7 MW in 2024; 554 / 66,060.5 in 2025),
   shrinking only by whatever units the restored margin lifts over their bar.
8. **The FFR-5A coal cohort still decides.** Control: coal 11 / 1,482.1 MW decided in the
   2025 ledger at net $0.04 vs bar $58.5 — the repair must add ~$58/kW-yr at that screen to
   flip it, ~3× expectation 4's upper range. Expected: still decided; a flip would be a
   surprise worth its own diagnosis.
9. **Additions move little.** The entry screen consumes the same repaired object, so
   additions may tick up from 17.0 GW but remain FAR below the 55.4 GW actual — the entry
   economics and caps are FFR-4/5 lanes' objects (§1.5(iii): reported, not targeted).

The FALSIFIABLE core, one line: **the repair should produce a nonzero, adder-scaled tail
and single-digit-$/kW-yr margin restoration with ≈ 0 economic executions, and should NOT
reproduce the measured price level — a repaired object that lands ON the measured curve
would itself be suspect (nothing in E1/E2/E4 knows the measured prices).**

## 4. Phase 3 — the paired-arm measurement

*(filled after the pre-registered solves)*

## 5. Governance

*(filled last)*
