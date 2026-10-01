# FINDING — NYISO's 2020 validation touchpoint is DATA-BLOCKED at HEAD, and NYISO is the only ISO of the seven that is

**Session:** `nyiso-fuelvintage-1`, 2026-09-09 · **ISO:** NYISO · **Cost:** zero LP
**Status:** blocker precisely located and ROUTED — deliberately **not** repaired here.

---

## 1. The claim being corrected

`docs/handoffs/xiso-fuelvintage-per-iso-lp-prompts-2026-09-09.md` (PROMPT 3, ADDITION 4) states:
*"NYISO holds `complete`: 2020, 2021, 2022 OPEN with `--holdout-authorized`."*

**Governance-wise that is exactly right** and is re-verified here:
`holdout_policy.registration_refusals([2020, 2021], "NYISO", …)` returns **no refusals**, the
`complete` marker is present (declared 2026-09-06, already re-keyed to the current keeper
`2026-09-07-nyiso-213-summer-seam`), and the spend freeze is scoped to the locked-test tier alone.

**But 2020 is not solvable at HEAD**, for an input reason nothing in the handoff chain anticipated.
Rule 22 separates the two cleanly — *"what is held out is the SCORE, never the DATA"* — and this is
a DATA readiness gap, not a governance one. **The authorization is real and unspent; the input is
missing.**

## 2. The mechanism, exactly

1. `renewables.py::load_renewable_profiles` asks `_eia_hourly_cf_profile(iso, year, fuel, monthly)`
   for each VRE fuel. That reads the BA's own EIA-930 hourly extract, and **returns `None` when the
   series sums to zero** — an all-zero signal is treated as a BA reporting gap, not as genuine zero
   generation.
2. **NYISO reports no utility-scale solar to EIA-930 at all.** Measured:
   `load_eia_hourly_renewable_gen("NYISO", y)["solar"].sum() == 0` in **every** year tested (2020,
   2021, 2023), against wind of 4.38 / 4.06 / 4.60 TWh. (NYISO's solar is overwhelmingly
   behind-the-meter and not telemetered to the BA — the model already knows this: the loader logs
   *"Repaired degenerate NYISO 2023 solar distribution from donor NEISO"*, and the committed profile
   table carries a distinct `solar_proxy` fuel for exactly this reason.)
3. So solar falls through to `_eia930_cf`, which reads
   `data/raw/eia-930/eia_generation_profiles.parquet`.
4. **That artifact begins at 2021 for all seven ISOs** (measured: every ISO's `year` range is
   2021–2025, 5 years each). A 2020 lookup therefore raises

   ```
   ValueError: No EIA-930 data for ISO 'NYISO' in year 2020
       data/eia930/frames.py:396  <- actuals.load_generation_profiles
       <- renewables._eia930_cf   <- renewables.load_renewable_profiles
       <- run_calibration.run_year:2720
   ```

   **before any LP is built.** 2021 and 2022 build normally (verified: full `fleet_only` rebuilds
   succeed, `n_gen` 870 and 873).

## 3. Why NEISO's 2020 touchpoint succeeded and this does not

`2026-09-06-neiso-106-touchpoints-2020` covers 2020–2022 on a structurally similar recipe
(`mode="backcast"`, `use_campd_bins`, `plant_level_fleet`), and the shared profile artifact is
**tracked and unchanged** since — so NEISO did not extend it. NEISO simply never reaches the
fallback: it **does** report solar to EIA-930 (361 GWh in 2020).

Measured across all seven ISOs for 2020 — the exposure is **unique to NYISO**:

| ISO | 2020 EIA-930 wind (MWh) | 2020 EIA-930 solar (MWh) | reaches the absent fallback? |
|---|---|---|---|
| CAISO | 14,877,923 | 28,589,705 | no |
| ERCOT | 86,738,075 | 8,287,483 | no |
| MISO | 71,247,588 | 678,405 | no |
| NEISO | 3,538,710 | 361,045 | no |
| **NYISO** | **4,377,316** | **0** | **YES** |
| PJM | 22,401,811 | 3,120,760 | no |
| SPP | 82,029,861 | 561,739 | no |

That is why the program has not hit this before, and why it is a NYISO-lane finding.

## 4. Why it was NOT repaired in this session

Not because it is hard to notice — because repairing it correctly is a **data-intake project on a
shared, all-ISO artifact**, and doing that unasked, mid-session, would be exactly the kind of scope
expansion that should be routed:

* **`eia_generation_profiles.parquet` has no producer script in the repo.** Nothing under
  `scripts/` references it; it is a tracked artifact with no in-repo derivation.
* **The derivation is not a plain aggregation.** The committed table carries six fuels — `hydro`,
  `nuclear`, `wind`, `offshore_wind`, `solar`, **`solar_proxy`** — each normalized to sum ≈ 1.0 over
  the year (measured for NYISO 2021: 1.000011 / 0.999872 / 0.999971 / 1.000000 / 0.998640 /
  1.000000). The raw `NYIS_fueltype.parquet` carries only `COL NG NUC OIL OTH SUN WAT WND`, so
  reproducing it requires the **cross-ISO donor-proxy logic** that produces `solar_proxy` — a real
  modelling decision, not a transcription.
* **2020 is a leap year**: the raw fueltype extract has 8,784 hours per fuel, while the profile
  table is on 8,760. The producer's convention for that is unknown and must not be guessed.
* Changing a shared artifact touches all seven ISOs' inputs; an additive 2020-only extension is the
  safe shape, but it still needs the producer's conventions reproduced and **verified against an
  existing year** before anyone trusts a 2020 row.

**The raw material is present** — `NYIS_fueltype.parquet` carries 2020 (70,272 rows, all eight fuel
types, 8,784 h each) — so this is a build, not a fetch.

## 5. The route, concretely

The next lane that wants NYISO 2020 should:

1. Reconstruct the producer from the committed table's own conventions, and **prove it by
   reproducing an existing year** (NYISO 2021 is the natural target: 52,560 rows, six fuels, each
   summing to ≈ 1.0) before generating any new row.
2. Settle the two conventions the artifact does not document: the **`solar_proxy` donor rule** for a
   BA that reports no solar, and the **leap-year hour mapping** (8,784 → 8,760).
3. Extend **additively** — 2020 rows only, leaving 2021–2025 byte-identical — so no existing run's
   inputs move, and confirm that with a hash of the pre-existing rows.
4. Apply it to **every** ISO's 2020 in one pass, per rule 22's *"collected once and applied
   CONSISTENTLY ACROSS ALL YEARS"*, even though only NYISO currently needs it.

Rule 22 makes the intake itself unrestricted — it needs no marker and no per-window authorization,
because preparing an input is not spending a year. Only solving and scoring 2020 is the spend, and
NYISO's authorization for that is already in hand and **still unspent**.

## 6. What this session did instead

The 2020 rung was **not attempted** — no LP was spent discovering a failure that a zero-LP read
had already proved. NYISO's validation ladder for this session is therefore **2021 and 2022**, and
2020 is reported as **data-blocked, authorization unspent**, not as a miss.

---

## 7. ADDENDUM (v4 run, same session) — **2021 IS DATA-BLOCKED TOO, for a DIFFERENT input**

The v3 run concluded *"NYISO's validation ladder for this session is therefore **2021 and 2022**"*.
**Measured by attempting it: 2021 is blocked as well, and the ladder is 2022 ALONE.**

The 2021 touchpoint was launched on the frozen keeper recipe
(`replay_keeper … --years 2021 --holdout-authorized`) and died before the LP, in
`pipeline/kwargs.apply_reserve_coopt` → `reserves/spec._nyiso_design` →
`data/reserve_requirements.load_nyiso_reserve_requirements`:

```
FileNotFoundError: nyiso_dynamic_reserve_requirements=True but the measured requirement
series is absent: data/raw/NYISO-AS/requirements/NYISO_reserve_requirements_2021.csv.
This is the Ask-B external data intake (docs/handoffs/nyiso-data-asks-2026-07.md); the
flag must not solve on the static requirements it claims to replace.
```

**The intake covers 2022–2025 and nothing earlier** (measured, git-tracked):
`NYISO_reserve_requirements_{2022,2023,2024,2025}.csv` — four files, no 2021, no 2020, no 2019.

**The refusal is the mechanism working correctly, and it must not be worked around.** The
error message states the reason itself: the flag *"must not solve on the static requirements it
claims to replace"*. There is exactly one way to make 2021 solve today — disarm
`nyiso_dynamic_reserve_requirements` for that year — and it is **refused on rule 22
`[R-HOLDOUT]`**: a validation touchpoint *is* the designated keeper's frozen recipe replayed on
a held-out year, so a per-year recipe variant is not a touchpoint at all, it is per-year fitting
wearing a touchpoint's name. The keeper carries the flag in 2022–2025; a 2021 rung must carry it
too or not exist.

**So NYISO's exposure is two rungs, not one, and the two have different causes:**

| rung | status | binding input | scope of the gap |
|---|---|---|---|
| **2019** | REFUSED (governance) | — | locked-test tier, `final` empty, freeze ACTIVE, every ISO |
| **2020** | **DATA-BLOCKED** | `eia_generation_profiles.parquet` starts 2021 | reached only by NYISO (§3), because NYISO alone reports zero utility-scale solar to EIA-930 |
| **2021** | **DATA-BLOCKED** | `NYISO-AS/requirements/` starts 2022 | **NYISO-only by construction** — it is a NYISO-specific intake for a NYISO-specific mechanism |
| **2022** | **SOLVED, SCORED, REGISTERED** | — | the whole of NYISO's spendable ladder at HEAD |

**Neither is a governance state and neither spends anything.** `holdout_policy` returns no
refusal for 2020 or 2021, the `complete` marker is present and correctly re-keyed, and the freeze
is scoped to the locked-test tier alone. Rule 22's own split is what makes this clean: *"what is
held out is the SCORE, never the DATA"* — these are **data-readiness gaps on the input side**, so
**both authorizations remain real and entirely UNSPENT**. No LP was spent discovering the 2020
block (a zero-LP read proved it); the 2021 block cost one aborted process that died in input
assembly, before any matrix was built.

**The route for 2021**, and it is a genuine intake rather than a fetch-and-go: extend the Ask-B
NYISO reserve-requirement intake backward to 2021 (and 2020, and 2019 if the source carries it),
under the same rule-22 clause that makes intake unrestricted — *"collected once and applied
CONSISTENTLY ACROSS ALL YEARS"*. `data/raw/NYISO-AS/requirements/README.md` and
`docs/handoffs/nyiso-data-asks-2026-07.md` own the source and its conventions. Until that lands,
**a NYISO 2021 rung cannot exist on the keeper's recipe**, and quoting one built on a disarmed
flag would be quoting a different model.
