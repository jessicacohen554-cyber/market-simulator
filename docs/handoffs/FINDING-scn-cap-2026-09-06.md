# FINDING — SCN-CAP: `mass_cap_tons_by_year` is built, read first, backcast-inert and byte-identical at `None`; `CAP-STATE-TIGHT` is live at the S12 schedule; it binds on NYISO and CAISO in every year 2026–2030 and is slack on NEISO in every one

**Lane:** SCN-CAP (desk ledger `docs/handoffs/scenario-desk-ledger-2026-09.md` §0 r#12 am.1, §5 issuance), chartered from owner ruling **S12** on card **D-2(c)** (2026-09-06, verbatim: *"Commit the 80 % slope and build the field."*) — WS-1a §4.1(a)'s build, not a plan §7 body. **Model:** Fable (`claude-fable-5-1`). **Branch:** `claude/scn-cap-schedule-field-re00nd` (harness-assigned; the desk's issuance stem was `claude/scn-cap-schedule-field-p2wd` — same lane, one branch, the mismatch every SCN lane has recorded). **Base:** `origin/main` `47e306d3` (PR #5147, the r#12 am.1 desk log) at start; rebased onto `acbb5350` (r#12 am.2 + nyiso-202's prereg — neither touching a file this lane reads or writes) before the last commit. **Solves:** NONE — a zero-LP build lane; the only LPs are the trivial-first unit tests (1 generator / 1 zone / 24 h). Rule 29's PRECOMMIT does not apply; rule 29(c) binds trivially (no bundle of this lane exists anywhere). **Data profile:** `neiso` (declared; nothing under `data/raw` was read by any deliverable — the EIA-860 plant-state lookup the row path consults is pinned empty in the tests so they are hermetic).

**Commits, in order (hashes after the rebase onto `acbb5350`):** `75a1a732` (the field + coercion + the three registrations — deliverable 1), `256fc7d1` (`_power_sector_cap` reads the schedule first + `tests/unit/policy/test_mass_cap_schedule.py`, which carries both the backcast-inertness tests and the trivial-first LP tests since they share the module — deliverables 1–2), `89b0a9f4` (the YAML case + pin + the no-program-ISO assertion — deliverable 3), `6e7ade58` (this document, carrying deliverable 4's measurements — deliverable 5), `ad8380f7` (`docs/codebase/05-policy.md` — deliverable 6), then the matrix row + six cells LAST with this paragraph's refresh (deliverable 7).

**The program-ISO policy lanes' precondition P5 is met by this document's merge:** the field and the case are on `main`. Per r#12 am.2 (the cap addendum withdrawn — no policy lane is running — and the cap case folded into the ONE combined policy charter v3 as **case 13**, program ISOs only, gates G10–G12) their phase 0 for case 13 is §3 below; "the charter" below means that combined charter, ledger §5.

---

## 0. Bottom line

1. **The field exists and ships inert.** `ScenarioConfig.mass_cap_tons_by_year: dict[str, dict[int, float]] | None = None` — `{ISO: {year: metric tonnes CO2}}` — placed contiguous with the `mass_cap_*` block, validated in `__post_init__` (non-empty, year-keyed, positive tonnage) and **coerced to `None` in `mode="backcast"` and in a capacity hindcast** beside the `carbon_price_delta` guard (the `datacenter_load_path` pattern, rule 13). Registered in `_CACHE_KEY_OPTIONAL_FIELDS` and `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` at `None` (the frozen drop value) and in `TIER_TAGS` at tier 1 beside `mass_cap_tons`. `scripts/check_cache_key_registration.py --base origin/main` passes ("1 new field(s), all registered").
2. **It is read FIRST.** `policy/cap_and_trade.py::_power_sector_cap` now sources the row's budget **schedule → scalar → published → inert** (§1). The new reader `scheduled_power_sector_budget(config, year)` interpolates linearly between the ISO's knots, holds the edge values outside them (the last knot flat after 2050), coerces YAML/JSON string keys back to int, and returns `None` for an ISO the schedule does not name — so every ISO outside the schedule keeps exactly the order it had.
3. **Byte-identity measured, 0 moved (§4):** the forecast default key `547053bdfccd4264` and backcast default key `f61891696e671969` are unchanged; **0 of 143** committed `results/**/run_config.json` keys move; **0 of 6** keeper backcast keys move (all six recomputed identically on base and on this branch). The charter's `e5ecd4105ada3e58` is the PRE-D60 default and was already superseded on `main` before this lane started (capx D60's declared flip; `tests/regression/test_persisted_identity.py` pins `547053bdfccd4264`); nothing here touches that.
4. **`CAP-STATE-TIGHT` is live at the ruled schedule, verbatim (§2):** NYISO {2026: 23.16, 2030: 20.2, 2040: 12.8, 2050: 4.6} Mt, NEISO {20.67, 18.0, 11.4, 4.1}, CAISO {30.5, 26.5, 16.5, 6.1} — a linear decline to 20 % of the 2025 published per-state budget by 2050, **CAISO anchored to the model's own REF-2026 CO2** because CARB publishes no power-sector budget (disclosed in the case comment and here, §2). No number was adjusted.
5. **Where it binds, from committed numbers (§3):** against the committed T1-F REF CO2 trajectories the schedule **binds on NYISO in all five years 2026–2030** (budget 23.16 → 20.2 Mt vs REF 23.69 → 20.89), **binds on CAISO in all five** (30.5 → 26.5 vs 31.31 → 31.16), and is **slack on NEISO in all five** (20.67 → 18.0 vs REF 15.83 → 13.37, a 4.6–5.7 Mt margin every year) — so under the policy charter's phase-0 rule for case 13 the NEISO lane KILLS the case without a solve, and NYISO/CAISO solve it. The REFs are the **pre-D77** ones (all three program-ISO REF bundles predate `ae8dd2a0`); the NEISO margin is far larger than anything the D77 seam moves in 2026–2027, but NYISO-2030's 0.69 Mt and CAISO-2026's 0.81 Mt margins are the ones a re-solved REF could plausibly cross — the policy lanes redo this table at their pin.
6. **One charter premise is false at HEAD and is routed, not papered over (§5):** PJM is **in** `CAP_AND_TRADE_PROGRAMS` (its partial RGGI footprint), so under the case's `mass_cap_enabled: true` an ISO absent from the schedule falls through — as the chartered fallback order requires — to the **published regional RGGI budget in 2027–2030** and builds a (membership-weighted, presumably slack) row. `CAP-STATE-TIGHT` on PJM is therefore **not** byte-identical to REF; ERCOT and MISO are (no program → no resolution). The PJM lane is already instructed not to solve the case; the test pins the behaviour so the desk's ruling on it cannot be pre-empted.
7. **Matrix duty (rule 28c) discharged in the last commit:** a NEW base row `mass_cap_schedule` plus one appended cell line in every shard — forecast lane `U` in all six ISOs (nothing is tested until the policy lanes solve it), backcast lane `.` by construction (the field is coerced to `None` there). Why a new row rather than extending `mass_cap_lp_row`'s def: §6.

---

## 1. The field and its fallback order

`_power_sector_cap(config, program, year, membership)` returns the row's `MassCapSpec` (metric tonnes) from the first available source, in this order — one composition point (rule 19 `[R-ONE-MECH]`): the schedule ADDS a source ahead of the scalar; nothing stacks.

| rank | source | field / function | when it fires | how the number is formed |
|---|---|---|---|---|
| 1 | **schedule** *(new)* | `mass_cap_tons_by_year[config.iso]` → `scheduled_power_sector_budget` | the field is set AND names `config.iso` | linear interpolation between the ISO's `{year: tonnes}` knots; edge-held before the first and after the last knot (2050 holds flat to the horizon); str keys coerced to int |
| 2 | scalar | `mass_cap_tons` | rank 1 returned `None` and the scalar is set | taken as-is (already metric tonnes) — the pre-existing explicit counterfactual cap |
| 3 | published | `_published_power_sector_budget(program, year)` | ranks 1–2 returned `None` | CARB MMT × 1e6; RGGI = Σ member-state budgets (short tons × `SHORT_TON_TO_METRIC_TONNE`) where `RGGI_MEMBER_STATES_BY_YEAR` has the year, else the **regional** 11-state total (2027–2030 only) |
| 4 | inert | — | ranks 1–3 all `None` | no row; the adder path carries the measured (backcast) / projected (forecast) program price, unchanged |

All four ranks sit behind two unchanged gates: `CAP_AND_TRADE_PROGRAMS.get(config.iso)` (no program → `resolve_carbon_program` returns `None`: ERCOT, MISO) and `state_carbon_pricing` (off → `None`), then `mass_cap_enabled` (off → adder path). The schedule is a budget *source*, never a gate: with `mass_cap_enabled=False` it is ignored (tested).

**Backcast / hindcast.** `__post_init__` validates the shape whatever the mode, then sets `mass_cap_tons_by_year = None` when `mode == "backcast"` or `hindcast` is true. The scalar `mass_cap_tons` and `mass_cap_enabled` are deliberately untouched — they pre-date this field and are live in backcast (the published-budget row is a rule-13-admissible measured input). Tested: backcast and hindcast coercion; the scalar survives beside a coerced schedule; the backcast key with the field set equals the key without it.

**Reader arithmetic** (tested at every row): NYISO 2028 = 23.16 + ½(20.2 − 23.16) = **21.68 Mt**; 2035 = **16.5 Mt**; 2055 = 4.6 Mt (edge-held); 2025 = 23.16 Mt (edge-held); a JSON round trip of the knots (`"2026"` keys) resolves the same budget and hashes to the same cache key.

**Trivial-first LP** (`tests/unit/policy/test_mass_cap_schedule.py::TestTrivialFirstLp`, through the runner's and the calibration harness's shared seam `policy.constraints.build_mass_cap_dispatch_kwargs` → `solve_dispatch`): one 200 MW gas unit at mc $50 and 0.5 t/MWh serving 80 MW for 24 h emits 960 t uncapped; a NEISO schedule `{2026: 1000, 2030: 200}` resolves to **600 t at 2028**, the row binds, emissions equal the cap to 1e-6 relative, and the dual equals the analytic allowance price **(VOLL − mc)/rate = $9,900/t** to 1e-6. A `{1e6, 1e6}` schedule is slack: dual 0 (|dual| < 1e-9), dispatch unconstrained. A `None` schedule in 2026 (no published NEISO budget) returns `{}` — the pre-field LP byte for byte. ERCOT under the schedule returns `{}`.

---

## 2. The case, as committed

```yaml
# configs/scenario_campaign_matrix.yaml — LIVE since SCN-CAP (2026-09-06), ruling S12
CAP-STATE-TIGHT:
  mass_cap_enabled: true
  mass_cap_program: co2
  state_carbon_pricing: true      # the row REPLACES the adder
  carbon_price_path: zero         # no federal price in the cap case
  mass_cap_tons_by_year:          # metric tonnes CO2; linear between knots
    NYISO: {2026: 23.16e+6, 2030: 20.2e+6, 2040: 12.8e+6, 2050: 4.6e+6}
    NEISO: {2026: 20.67e+6, 2030: 18.0e+6, 2040: 11.4e+6, 2050: 4.1e+6}
    CAISO: {2026: 30.5e+6, 2030: 26.5e+6, 2040: 16.5e+6, 2050: 6.1e+6}
```

This is WS-1a §4.2 verbatim, committed by S12. The anchor is the 2025 published per-state budget — NY 23.16 Mt; CT+ME+MA+NH+RI+VT 20.67 Mt (both the metric-converted sums `_published_power_sector_budget` returns for 2025) — then a linear decline to 20 % of the anchor by 2050 (the test pins 2050/2026 = 0.2 ± 0.002 per ISO; the knots carry WS-1a's rounding).

**THE CAISO ANCHOR IS DISCLOSED, NOT PUBLISHED.** CARB publishes no power-sector budget; its 267 Mt whole-economy cap is meaningless as a power-sector row (WS-1a §4.1). CAISO's 2026 knot is therefore the model's own **REF-2026 CO2 at WS-1a's pin, 30.5 Mt**, declining on the same 80 % slope. It is the one non-published anchor in the case; the case comment says so in place. (The committed REF at the campaign pin now reads 31.31 Mt for 2026 — §3 — which is why the CAISO row binds already in 2026.)

**One numeric-form note, for anyone editing the file.** PyYAML reads `23.16e6` as a *string* (its float regex needs a signed exponent); the case writes `23.16e+6` so every knot loads as a float. `test_cap_state_tight_is_live_at_the_committed_schedule` asserts the parsed types (int years, float tonnes), so the unsigned form cannot creep back silently.

**Semantics of the two defaults written out.** `state_carbon_pricing: true` keeps the program resolver ON so the ROW replaces the adder — `resolve_carbon_program` returns exactly one of `price_adder` / `cap_spec` (the resolver invariant), so on the row path the fleet carries no allowance adder and the endogenous dual is the only carbon price in dispatch. `carbon_price_path: zero` means no federal price in the cap case: under S2's floor a zero path resolves to the program alone, and on the row path the program *is* the row. Both are the shipped defaults; they are written out because the case's meaning depends on them (the charter's gate G11 is what the policy lanes verify on their solve).

**Scope.** The schedule names CAISO / NYISO / NEISO only. ERCOT and MISO carry no program, so `resolve_carbon_program` returns `None` under the case in every year and the LP is byte-identical to REF's (tested on the committed 2026–2030 base YAMLs). PJM: §5. The case is HELD under S5 with every other A-POLICY case and is solved only by the three program-ISO policy lanes under their own PRECOMMIT (case 13 of the combined charter, precondition P5) — lanes that, at r#12 am.2, have not been launched (gated on WS-5A's ADDENDUM 2).

---

## 3. Where the row binds — the resolved budget per ISO-year vs the committed REF CO2

Computed from the committed campaign REFs (`results/scn-campaign-load-2026-09-06/<ISO>/REF/full_horizon_summary.json`, the SCN-WS5A-LOAD bundles at the campaign pin) through the code path (`SweepDefinition.case_configs` on each ISO's `*_scenario_base_2026_2030.yaml` → `resolve_carbon_program`). **All three REF bundles are PRE-D77**: NYISO and NEISO were solved 04:11 / 04:16 UTC on a basis (`20f9ce9f`) that does not contain `ae8dd2a0` (05:17 UTC), and CAISO at 07:54 UTC on `2ed69a34`, which also does not contain it (`git merge-base --is-ancestor` on each). The D77 seam is the CCS retrofit emission rate; it is inert before `ccs_retrofit_available_year` 2028 and moves the 2028–2030 rows only where retrofits clear. The policy lanes redo this table at their pin (WS-5A ADDENDUM 2) once the S8 re-solves land; the verdicts below are the pre-fix reading, said as such.

| ISO | year | schedule budget (Mt) | REF CO2 (Mt, pre-D77) | margin (REF − budget) | binds? | published fallback the schedule replaces (Mt) | REF adder path ($/t) |
|---|---|---|---|---|---|---|---|
| **NYISO** | 2026 | 23.16 | 23.692 | +0.53 | **YES** | none (inert) | 23.64 |
| | 2027 | 22.42 | 24.591 | +2.17 | **YES** | 57.334 (regional) | 25.29 |
| | 2028 | 21.68 | 24.111 | +2.43 | **YES** | 55.701 (regional) | 27.06 |
| | 2029 | 20.94 | 23.754 | +2.81 | **YES** | 54.068 (regional) | 28.96 |
| | 2030 | 20.20 | 20.894 | +0.69 | **YES** | 52.526 (regional) | 30.98 |
| **CAISO** | 2026 | 30.50 | 31.306 | +0.81 | **YES** | none (inert) | 30.02 |
| | 2027 | 29.50 | 34.515 | +5.01 | **YES** | 240.6 (whole-economy) | 32.13 |
| | 2028 | 28.50 | 33.319 | +4.82 | **YES** | 227.3 | 34.37 |
| | 2029 | 27.50 | 31.355 | +3.86 | **YES** | 213.9 | 36.78 |
| | 2030 | 26.50 | 31.160 | +4.66 | **YES** | 200.5 | 39.36 |
| **NEISO** | 2026 | 20.67 | 15.832 | −4.84 | no | none (inert) | 26.05 |
| | 2027 | 20.00 | 17.096 | −2.91 | no | 57.334 (regional) | 27.88 |
| | 2028 | 19.34 | 15.856 | −3.48 | no | 55.701 (regional) | 29.83 |
| | 2029 | 18.67 | 14.021 | −4.65 | no | 54.068 (regional) | 31.92 |
| | 2030 | 18.00 | 13.368 | −4.63 | no | 52.526 (regional) | 34.15 |

**Reading, per lane (the charter's phase-0 rule for case 13: slack in every year ⇒ byte-identical to REF ⇒ KILLED, never solved; binds in at least one year ⇒ solve):**

- **NYISO — SOLVE.** Binds in all five years, by 0.5–2.8 Mt. The 2026 margin (+0.53 Mt, 2.2 % of REF) is the thinnest; the row's 2026 dual will be small and 2027–2029's larger. The exogenous comparator on the adder path is $23.64 → $30.98/t (projected RGGI escalator) — the price-vs-quantity comparison is the dual against that column.
- **CAISO — SOLVE.** Binds in all five years, by 0.8–5.0 Mt (2.6–14.5 % of REF). The 2026 bind is an artefact of the anchor: the case's 2026 knot is WS-1a's REF-2026 (30.5) and the pinned REF now reads 31.31, so the row is 0.81 Mt tight in the anchor year itself — disclosed here so the CAISO lane does not read a 2026 dual as a slope effect. Comparator: $30.02 → $39.36/t.
- **NEISO — KILL at phase 0.** Slack in all five years by 2.9–4.8 Mt (18–35 % of REF): under the case the LP is byte-identical to REF on NEISO (the row is built and never binds; dual 0), so the charter says do not solve it. The NEISO margin is an order of magnitude larger than any D77 effect through 2030, so the post-fix REF cannot change this verdict.

**What the schedule replaces.** The last column but one is WS-1a §4.1's census reproduced through the new code path: the published fallback was inert in 2026, the 11-state regional total (52–57 Mt against one ISO's 13–25 Mt) in 2027–2030 for the RGGI ISOs, and CARB's whole-economy cap (200–241 Mt) for CAISO — slack everywhere, which is why "published schedule alone" was never a tight case and why the field exists.

**PJM, for completeness (§5):** the case resolves to the published regional budget 57.3 → 52.5 Mt in 2027–2030 on PJM and to nothing in 2026 and 2031+. That budget cannot be read against PJM's all-ISO REF CO2 (373–470 Mt) because the row is membership-weighted to the MD/DE/NJ fleet (VA exited 2024-01-01); the member-footprint emissions are not tabulated anywhere committed, so whether the PJM row is slack is **unmeasured** here. It is not this lane's to solve and the PJM lane is told not to.

---

## 4. Key measurements (byte-identity)

Method: `ScenarioConfig(**scenario_config)` re-hashed for every committed `results/**/run_config.json` (143 files; unknown keys dropped as `from_yaml` does) and for the six keepers' `results/calibration/<bundle>/run_config.json`, on `origin/main` `47e306d3` and again on this branch after the field, the reader and the case landed; plus the two pinned defaults. Script: the session scratchpad's `measure_keys.py` (not committed; the table is the record).

| surface | base `47e306d3` | this branch | moved |
|---|---|---|---|
| forecast default `ScenarioConfig().cache_key()` | `547053bdfccd4264` | `547053bdfccd4264` | 0 |
| backcast default `ScenarioConfig(mode="backcast").cache_key()` | `f61891696e671969` | `f61891696e671969` | 0 |
| committed `results/**/run_config.json` (143) | — | — | **0 of 143** recomputed keys differ between base and branch |
| keeper CAISO `2026-09-05-caiso-252-b1-notrim` (`caiso252_b1_notrim`) | `6c161c7e6cbd4811` | `6c161c7e6cbd4811` | 0 |
| keeper ERCOT `2026-09-05-ercot248-two-config-keeper` (`ercot248_two_config_keeper`) | `b4e683e3d74c5e87` | `b4e683e3d74c5e87` | 0 |
| keeper MISO `2026-09-05-miso-220-nonsteam-lift` (`miso220_nonsteamlift_B`) | `96d5c4d7ac31084b` | `96d5c4d7ac31084b` | 0 |
| keeper NEISO `2026-08-17-neiso-99-joint-p1` (`neiso99_joint_B`) | `48525196d52e8442` | `48525196d52e8442` | 0 |
| keeper NYISO `2026-09-06-nyiso-196-extract-basis` (`nyiso196_extract_basis`) | `5f130d996ce5ce23` | `5f130d996ce5ce23` | 0 |
| keeper PJM `2026-08-15-pjm-162-inputclock` (`pjm_debugb_inputclock_A`) | `0b5867afa886b9ad` | `0b5867afa886b9ad` | 0 |

Two honesty notes on that table. (i) Keeper bundles record no `cache_key` field, so the keeper row is "recomputed on base == recomputed on branch", the identity claim rule 27 / plan §1 item 4 actually asks for. (ii) Of the 118 forecast `run_config.json` files that DO record a key, 63 recompute to their recorded key at HEAD and 55 do not — **identically on base and on this branch** — which is the pre-existing HEAD drift capx D79's solve-surface fingerprint is chartered on (desk ledger §0 r#12), not anything this lane did; it is reported because a reader comparing recorded keys to HEAD will see it.

**Armed keys are distinct** (so an arm never collides with its control on disk): on the committed 2026–2030 base YAMLs, `CAP-STATE-TIGHT` vs `REF` — CAISO `ca6c6ddfd464c764` vs `0acbe61dd8849e22`; NYISO `20a471e19d461f7c` vs `84955cc82d636568`; NEISO `6d27460a8efb00f0` vs `5fda40850648b31c`; PJM `13d1702cb02ac105` vs `3eee8f1195ee35f0`. (`test_cases_expand_and_carry_distinct_cache_keys` asserts pairwise distinctness across the whole case set for all six ISOs.)

**Guards run locally, all green:** `scripts/check_cache_key_registration.py --base origin/main` (1 new field, registered; 266 declared defaults match HEAD); `scripts/check_mechanism_matrix.py --base origin/main` (after the last commit); `ruff check` + `ruff format --check` on every touched file; `tests/unit/policy/test_mass_cap_schedule.py` (29), `tests/unit/policy/test_cap_and_trade.py`, `tests/unit/policy/test_constraints.py`, `tests/unit/model/test_dispatch.py::TestMassCapConstraint`, `tests/unit/config/test_cache_key_default_flip_guard.py`, `tests/regression/test_persisted_identity.py`, `tests/scoring/test_scenario_campaign_configs.py`.

---

## 5. Routed to SCN-DESK — not executed, outside this lane's regions or its mandate

1. **PJM under `CAP-STATE-TIGHT` is not byte-identical to REF, and the SCN-CAP charter's premise that "the row is gated off by `CAP_AND_TRADE_PROGRAMS`" on PJM is false at HEAD** (the combined policy charter's case-13 text carries the same sentence for the ERCOT / PJM / MISO lanes and needs the same correction for PJM). `CAP_AND_TRADE_PROGRAMS["PJM"]` exists (RGGI; MD/DE/NJ/VA with VA exiting 2024). With the schedule silent on PJM the resolver falls through — exactly as the chartered order requires — to the published regional RGGI budget in 2027–2030 and builds a membership-weighted row (2026 and 2031+ inert). This lane did **not** change the fallback to "inert when the schedule is set but silent on the ISO": that would alter an existing behaviour outside the charter and would make the schedule a gate. Two clean resolutions, the desk's to pick: (a) leave it — the PJM policy lane is already told not to solve the case, and `test_pjm_absent_from_the_schedule_falls_through_to_the_published_fallback` pins the behaviour so it cannot change silently; or (b) rule that a set schedule is exhaustive (ISO absent ⇒ inert), a one-line change in `scheduled_power_sector_budget`'s caller plus a flipped test, which would also make PJM byte-identical. Recommendation: (a) now, (b) only if a PJM cap case is ever chartered (D-1(c), the partial-footprint question, is still open on the adder side too).
2. **The three REF trajectories §3 is scored against are pre-D77.** The policy lanes redo the binding table at their pin; the thin margins that could flip are NYISO-2030 (+0.69 Mt) and CAISO-2026 (+0.81 Mt). NEISO's verdict (slack, kill) cannot flip.
3. **The read-out gap WS-1a §4.3 routed to WS-0 (G-E4 rider) is CLOSED at HEAD, verified by grep only:** `results/export.py::summarize_year` now emits `co2_cap_price_usd_per_t` (the max over active caps) and `co2_cap_price_by_cap` (`export.py:208, :295-296`), and `results/outputs.py` persists `co2_cap_price` (`:242`, `:417`). This lane did not open either file (not its region) and did not exercise the exporter; the program-ISO lanes' gate G10 needs the dual per year and a slack-vs-binding reading, and no `co2_cap_slack_t` is emitted — they read slack as `budget − emissions` from §3's budget and the year's `co2_mt`.
4. **The pinned default key in the charter (`e5ecd4105ada3e58`) is stale** — `main` moved it to `547053bdfccd4264` at capx D60's declared flip. Future charters should read `tests/regression/test_persisted_identity.py::PINNED_DEFAULT_CACHE_KEY` rather than carry a literal.
5. **Region note, disclosed:** the `__post_init__` coercion is a third hunk in `scenarios.py` beyond "the one block + the two registration lines" the collision register names; the charter itself asks for it ("its backcast/hindcast coercion to `None` in `__post_init__`"), it sits beside the `carbon_price_delta` guard the charter cites as the pattern, and it is 43 lines that no other live lane's region touches. A fourth one-line hunk adds the `TIER_TAGS` entry beside `mass_cap_tons` (every sibling field carries one).

---

## 6. Files touched — each inside a region the charter names (or disclosed in §5)

| file | change | region |
|---|---|---|
| `src/market_sim/config/scenarios.py` | the field (contiguous with `mass_cap_*`, ~:2960); `__post_init__` validation + backcast/hindcast coercion (beside the `carbon_price_delta` guard); `_CACHE_KEY_OPTIONAL_FIELDS` + `_CACHE_KEY_OPTIONAL_FIELD_DEFAULTS` entries at `None`; `TIER_TAGS` entry | the `mass_cap_*` block + the two registration lines (+ §5 items 5) |
| `src/market_sim/policy/cap_and_trade.py` | new `scheduled_power_sector_budget`; `_power_sector_cap` reads it first; docstrings | `_power_sector_cap` |
| `configs/scenario_campaign_matrix.yaml` | `CAP-STATE-TIGHT` live; the two header notes that named it as commented | the `CAP-STATE-TIGHT` case block (+ its two header mentions) |
| `tests/unit/policy/test_mass_cap_schedule.py` | NEW, 29 tests | new file |
| `tests/scoring/test_scenario_campaign_configs.py` | the commented-cases pin → all-cases-live; the S12 schedule pin; ERCOT/MISO nothing-resolves; program ISOs resolve the schedule every year | the pin |
| `docs/codebase/05-policy.md` | one paragraph in §5.8 (schedule → scalar → published → inert) | the one paragraph |
| `docs/codebase-site/data/mechanism-matrix.js` + the six shards | NEW base row `mass_cap_schedule` + one appended cell line per ISO (LAST commit, after rebase) | rule 28(c) |
| this document | — | — |

**Why a new base row `mass_cap_schedule` rather than extending `mass_cap_lp_row`'s def.** The two are different objects with different verdict lives: `mass_cap_lp_row` is the LP row itself — mode `BF`, live in backcast on the published budget, and a candidate for a backcast `K` someday on measured data — while the schedule is a forecast-only *scenario instrument* (mode `F`, coerced off in backcast) whose verdict is the policy lanes' CAP-STATE-TIGHT result. Folding the schedule into the row's cell would make one cell carry two verdicts (a backcast row verdict and a forecast case verdict), and the combined policy charter (case 13, from the withdrawn r#12 am.1 addendum) tells the program-ISO lanes to stamp "the `mass_cap_lp_row` (or `mass_cap_schedule`) cell" — a separate cell is the one they can stamp without overwriting the row's. The base row's `def` names both fields and the precedence so the CI mention gate resolves either way.

**Not touched (owner / other lanes, LIVE):** every other line of `scenarios.py`; `policy/carbon.py`, `policy/federal_ces.py`, `policy/voluntary_demand.py`, `model/lp/rows.py`; `frontend/data/hindcast/**`, `results/**`, `scripts/**`; the campaign YAML's other cases (SCN-FIX2's five carbon-form rows included — if it lands first the conflict is one case block each).
