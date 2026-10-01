# FINDING — caiso-137b: the CAISO LOLP scarcity overlay is **UNREACHABLE in the backcast lane**. `caiso_scarcity_pricing=True` on every CAISO keeper is a **stored no-op**; the persisted price is the energy-only LP dual and the realised adder is **exactly $0.00 in every hour**. Two secondary claims in `FINDING-caiso137` are **WITHDRAWN** — including the storage-tier "defect" and the whole D2 gate table built on it. **caiso-137's primary result — ask A2 closes as a no-defect — STANDS unchanged.**

**Keeper `2026-07-27-caiso-130-nameplate-aware` UNCHANGED.** No LP built, no
solver called, nothing armed, no `ScenarioConfig` field added, no bundle
produced. **There is no keeper candidate here and nothing to promote.**

Instrument (committed): `scripts/probes/_caiso137b_overlay_reachability.py`
(§A–§D), which re-verifies the standing result and proves both corrections from
the source tree in seconds.

---

## §1 — what stands

`FINDING-caiso137` §1 — **ask A2 closes as a no-defect** — is unaffected and
re-verified. Read off `results/scarcity.py`, with the keeper's own flags:

* the measure basis is **already plant-level ONLINE** (`_online_plant_mask`, and
  `reserves_online_mw=r_online` drives the half-hour LOLP term) — options **(a)**
  and **(c)** refuted;
* `caiso_scarcity_import_headroom` is `False` on the keeper, so
  `import_headroom` enters **no tier at all** — option **(b)** moot;
* storage and curtailed-VRE headroom are **already** in `r_online`.

A2 as written is **CLOSED (option d)**. Everything below narrows the blast radius
of that closure — it does not reopen it.

## §2 — Correction 1: the overlay never runs in a CAISO backcast

`caiso_scarcity_overlay` has **exactly one call site**:
`src/market_sim/runner.py:2085` — the **forecast** path.

The calibration path is a **disjoint solve core**:

* `scripts/run_calibration_full.py` and `scripts/run_calibration.py` contain
  **zero** imports of `market_sim.runner` (verified by AST walk).
* `_system_frame` (`run_calibration_full.py:870`) is the **only** writer of
  `system_<y>.parquet`'s `price` column, and its `total_overlay` is built from
  **ERCOT terms alone** — `ercot_rtordpa_overlay_series`,
  `ercot_dam_as_overlay_series`, `ercot_ordc_realized_adder`, and the
  reserve-price / cap-dual adders. There is **no CAISO overlay term**.

**Consequences.**

1. A CAISO keeper's persisted price is the **energy-only LP dual**. The realised
   scarcity adder is **exactly $0.00 in every hour of every year**.
2. `caiso_scarcity_pricing=True` in a CAISO backcast `run_config.json` is a
   **stored no-op** — it reads as armed and is structurally incapable of changing
   that run.
3. `FINDING-caiso137` §2's "realised overlay adder dw-mean $0.1399 / $0.0158 /
   $0.0004" is **withdrawn**: it described a counterfactual forecast-path overlay
   evaluated on backcast inputs, not anything in the keeper's prices.
4. `FINDING-caiso137` §4's **entire D2 E1/E2 gate table is withdrawn**. It priced
   a "spillover" onto a backcast LMP that the mechanism cannot reach.

**Empirical corroboration.** The keeper's minimum zonal price sits at **exactly
−$26.001** in 2,774 / 4,251 / 2,771 hours. A uniform positive adder would break
that exactness in every such hour. `FINDING-caiso137` §5.1 read the 152 / 133 / 7
hours where its reconstruction disagreed as *reconstruction error*; the simpler
and correct explanation is that **the adder is identically zero because the
overlay never ran**.

## §3 — Correction 2: there is no flat-nameplate defect

`FINDING-caiso137` §3 claimed `runner.py:2088` passes the flat December
nameplate. It does not. Seven lines govern it:

```python
# src/market_sim/runner.py:991-999
storage = storage_units_to_arrays(storage_units, zone_names)
if getattr(config, "storage_vintage_ramp", False):
    power_cap_2d, energy_cap_2d = storage_cap_profiles(storage_units, storage, config.hours)
    if power_cap_2d is not storage.power_cap:
        storage.power_cap = power_cap_2d      # <-- REPLACED with the COD-ramped 2-D array
        storage.energy_cap = energy_cap_2d
```

So by the time the overlay is called, `storage.power_cap` **is** the hourly
in-service cap and `reserve_headroom` takes its `cap.ndim == 2` branch. When the
ramp does not apply, `storage_cap_profiles` returns the 1-D arrays unchanged, the
`is not` guard suppresses the assignment, and the nameplate **is** the correct
cap. The code is right in both regimes.

**Where the 1-D array came from.** `scripts/run_calibration.py:3741` assigns the
ramped cap to a **separate local** (`storage_power_cap`) and leaves
`storage.power_cap` at nameplate. `FINDING-caiso137` reconstructed the overlay
through that function's `fleet_only` exit and read its `storage.power_cap` — a
property of **the reconstruction helper**, not of the overlay. The "phantom
3,049 / 3,567 / 4,317 MW" is **withdrawn**, and with it the rule-14 framing, the
"codebase disagrees with itself" corroboration (the derivers agree with the
runner; they disagree only with the `fleet_only` helper's local), and the
rule-25 ERCOT scope note.

**Methodological lesson, stated for the next session:** a claim about *what a
call site passes* must be traced from the call site, never inferred from a
reconstruction helper that reproduces the same *inputs* by a different route.
The `fleet_only` helper is built to reproduce LP **inputs**, and it does; it is
not a model of the runner's local variable bindings.

## §4 — what this leaves standing, which is sharper than what it removes

**CAISO has no scarcity-pricing mechanism in the backcast lane at all:**

* the in-LP co-opt (`caiso_reserve_coopt`) is off, and `FINDING-caiso131` §4
  measures it inert when armed (12.9 GW headroom against a 2.2 GW requirement);
* the LOLP overlay is **forecast-path only** (§2);
* no measured overlay series exists for CAISO, so no `scarcity.parquet` is
  derived and `render_calibration_html` falls back to `_tail_hours` on the
  **energy-only** duals.

**That is the honest reason CAISO's C3c is 0 / 0 / 0** — not that an armed
overlay fails to fire, but that **nothing prices scarcity in the lane C3c is
scored on.** It also sharpens `FINDING-caiso131` §4, whose "the LOLP overlay IS
armed on the keeper and is inert because R never approaches MCL" is imprecise in
both halves: R is irrelevant, because the code never evaluates it in this lane.
(`FINDING-caiso137` §2's own "correction" to that sentence — "nearly inert, but
not for the stated reason" — is likewise withdrawn and replaced by this.)

**Rule 24 `[R-REGISTRY]` note.** `caiso_scarcity_pricing` appears in every CAISO
keeper's `run_config.json` reading as **armed** while being structurally
incapable of changing that run. That is a provenance trap — it is what led
`FINDING-caiso131` §4 and `FINDING-caiso137` §2 to two different wrong readings
of the same flag — and it is why this correction is filed rather than quietly
dropped.

**This also relocates ask A4.** The `FINDING-caiso131` §6 fallback (ledger C3c as
an ACCEPTED MEASURED-INPUT LIMITATION) rests on the MISO/NEISO argument that a
deterministic perfect-foresight LP cannot manufacture probabilistic RT tail
uncertainty. For CAISO that argument is now **stronger and simpler**: there is no
scarcity-pricing mechanism in the scored lane at all. Any future C3c work must
first decide whether CAISO should *have* one in the backcast — which is a
mechanism-charter question (and a rule-19 one), not a tuning question.

## §5 — the keeper question, answered

**No keeper candidate exists and nothing was promoted.** Arming any
storage-tier flag would be **provably inert** in a CAISO backcast (Δ = exactly 0
on every scored series), and an inert flag is not a keeper — it is matrix code
`I`. The keeper remains `2026-07-27-caiso-130-nameplate-aware`, NOT-YET, fail set
{C3a-2025, C3c}.

No dashboard registration is due: rule 15 `[R-DASHBOARD]` applies to completed
**runs**, and neither caiso-137 nor caiso-137b produced a bundle.

## §6 — DO-NOT-REDO (new, binding)

* **Treating `caiso_scarcity_pricing` (or `caiso_scarcity_import_headroom`) as
  live in a CAISO BACKCAST.** §2: the overlay's only call site is the forecast
  runner, which the calibration path never reaches. Any backcast A/B on these
  flags is byte-identical by construction and must not be solved.
* **Re-proposing the flat-nameplate storage-tier "defect".** §3:
  `runner.py:997-998` already replaces `storage.power_cap` with the COD-ramped
  2-D array. There is no defect in either regime.
* **Quoting `FINDING-caiso137` §2's realised-adder numbers, §3's phantom MW, or
  §4's D2 E1/E2 table.** All withdrawn. §5's dump-floor bound and §2's `r_online`
  decomposition survive as *technique* and as a characterisation of the
  **forecast-path** overlay; neither is a statement about a backcast price.
* **Re-deriving why CAISO's C3c is 0 / 0 / 0 as a scarcity-mechanism failure.**
  §4: there is no scarcity mechanism in the scored lane. The question is whether
  CAISO should have one, which needs a charter.

Carried forward unchanged: `FINDING-caiso137` §1 and its §7 first bullet
(re-specifying A2 as options (a)/(b)/(c) is closed), plus everything in
`FINDING-caiso136` §5, `FINDING-caiso135` §10, `FINDING-caiso134` §9,
`FINDING-caiso133` §9, `FINDING-caiso132` §10, `FINDING-caiso131` §10,
`FINDING-caiso130` §7, `FINDING-caiso129` §6 and `FINDING-caiso127` §7.

Next number: caiso-138.
