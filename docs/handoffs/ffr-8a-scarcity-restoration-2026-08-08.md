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

*(filled after §1 was committed; nothing above this line changed after)*

## 3. Phase 2 — the repair as landed

*(filled after Phase 1)*

## 4. Phase 3 — the paired-arm measurement

*(filled after the pre-registered solves)*

## 5. Governance

*(filled last)*
