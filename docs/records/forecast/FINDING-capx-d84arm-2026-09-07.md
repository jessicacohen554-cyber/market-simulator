# FINDING — capx D84-ARM: `pjm_thermal_accreditation_vintage` is ARMED for PJM, and registered

**Lane:** capx D84-ARM, executing the **OWNER RULING of 2026-09-07** on
`FINDING-capx-d84-2026-09-07.md` §8's card. Branch
`claude/capx-d84-thermal-elcc-vintage-cblmzl`, rebased onto `origin/main` `a2d9c033`. Ex-ante
record: `PRECOMMIT-capx-d84arm-2026-09-07.md`, **pushed before `iso_configs.py` was touched**.

---

## 0. The answer in one paragraph

The arm is **landed, measured, and registered, and it cost no LP.** The ex-ante key census recorded
before the edit is reproduced **exactly** by the ex-post measurement: **33 of 227 committed run
configs move, every one of them PJM/forecast; zero non-PJM, zero backcast**, so every other ISO and
every backcast keeper is byte-identical. The armed bare `pjm-t1h` keys **`b9fa47dedb6c3319`** —
**the key D84's own arm bundle already carried** — and both keys survived the rebase over 29 commits
unchanged, so the armed recipe was already solved on this container and the registration owed no
re-solve. It is registered on the forecast namespace as **`pjm-2021-2025-realized-t1h-d84arm`**,
**14/14 invariants PASS**, with the pre-arm record preserved at `…-t1h-d75rarm`.

---

## 1. What the ruling was, and what it rules on

> *"Is this a recommended keeper candidate? If so plz promote… If structural integrity improves but
> gates regress that may still be a keeper."*

D84 meets that standard on its **easier** half: structural integrity improves under rule 14
`[R-ACCURATE]`, and **the gates do not regress at all** — all 361 substantive scored records are
byte-identical between arms, 26 bands, zero flips in either direction. What moves the wrong way is
the **published residual** in the one delivery year the mechanism touches (§4), reported at full
magnitude and never the reason for the change.

**Terminology, stated once.** D84 is a **forecast-lane** mechanism (capacity evolution), so this is
an **ARM**, not a rule-15 backcast keeper promotion. No ISO's keeper shard,
`calibration-complete.json` entry or backcast determination is touched, and none *can* be: the field
is coerced to its dataclass default in `mode="backcast"`, and the registry it reads lives in
`capacity_evolution`, which a backcast never enters.

## 2. The posture — the D57 / D67 / Q55 / Q56 route

`config/iso_configs.py::_pjm_config`'s `default_scenario_overrides` gains
`"pjm_thermal_accreditation_vintage": True`, beside the five PJM entries already there. The shared
`ScenarioConfig` dataclass default stays **`False`** and the `_CACHE_KEY_OPTIONAL_FIELDS` `"False"`
drop declaration is untouched, so `--no-pjm-thermal-accreditation-vintage` still reaches the pre-arm
posture and keeps its key `f736025631d0d27e`.

**Not a `(b′-1)` declared default flip**, for the reason the D76-ARM-B record makes explicit: a
shared-default flip re-keys configs the gate cannot reach — here it would move every ISO's forecast
keys and ten backcast keepers — while an ISO override moves PJM forecast keys and nothing else.

## 3. THE GATE — ex-ante recorded before the edit, ex-post reproduced exactly

Instrument: `scripts/probes/capxd84arm_iso_override_no_op_check.py` (the D78-ARM probe verbatim with
the field name changed, so the backcast coercion and the OVERRIDE-FIX explicit-caller rule are the
shipped path's own semantics, not a restatement). Records:
`docs/handoffs/d84arm/no-op-{expectation,measured}.json`.

| ISO / mode | configs | moved |
|---|---:|---:|
| CAISO / backcast | 1 | 0 |
| CAISO / forecast | 21 | 0 |
| ERCOT / backcast | 6 | 0 |
| ERCOT / forecast | 31 | 0 |
| MISO / backcast | 1 | 0 |
| MISO / forecast | 34 | 0 |
| NEISO / backcast | 5 | 0 |
| NEISO / forecast | 56 | 0 |
| NYISO / backcast | 7 | 0 |
| NYISO / forecast | 28 | 0 |
| **PJM / backcast** | 2 | **0** |
| **PJM / forecast** | **33** | **33** |
| SPP / backcast | 1 | 0 |
| SPP / forecast | 1 | 0 |

**The two records are byte-identical** apart from the two provenance flags (`simulated`,
`override_present_on_disk`) that exist precisely to differ. That agreement is the gate, and it
passes. Recipe legs after the arm: `pjm-t1h-bare` **`b9fa47dedb6c3319`** (field `True`);
`miso` `71156d9eb2ea896d`, `nyiso` `ee0d44e7d6f26397`, `neiso` `806f31b59b10c911`,
`caiso` `51c069044689c42b`, `ercot` `a9ef8b9769d44320` (all `False`); `pjm-plain-backcast`
`3a566deac3a85682`, **unmoved**.

**Rebase safety.** Both keys are unchanged across the rebase onto `a2d9c033` (29 commits), so every
one of those commits is inert for PJM's hindcast solve surface — which is why the registration below
needed no re-solve.

## 4. Registration — discharged in the same session, at zero LP cost

`scripts/register_forecast_run.py --bundle results/capacity-hindcast/pjm-2021-2025-realized-t1h-d84arm`
→ sidecar `frontend/data/hindcast/pjm-2021-2025-realized-t1h-d84arm.json`, report
`docs/hindcast-reports/pjm-2021-2025-realized-t1h-d84arm-2026-09-07.md`, forecast namespace
regenerated (180 runs).

- **`14/14 invariants PASS`** (I1 energy balance max |supply−demand| 1.019e-10 MW … I14).
- The sidecar records the **solved** posture, `pjm_thermal_accreditation_vintage: true` alongside
  the D48 / DR / Q55 / clearing gates — the FFR-3R property that a record reports what it solved.
- The bundle was **copied**, never moved, from D84's own `…-d84-thermalvintage` arm (rule 31
  `[R-RETAIN]`: nothing was deleted), and its `score.json` is verified identical to the screened
  one, so the registered numbers are the screened numbers.
- The pre-arm record is **preserved** at `pjm-2021-2025-realized-t1h-d75rarm`, the D78-ARM
  precedent for keeping the superseded posture readable.

## 5. What arming does NOT close — carried at the gate, not smoothed

1. **All three published DY 2025/26 comparators move AWAY:** cleared MW **+481.708 MW** further
   above published on both D66 frames (arm 146,646.835 vs published 145,883.0 frame B / 135,684.0
   frame A), and the RTO price **$34.961/MW-day** further below the published **$269.92** (arm
   178.095). This is rule 14's *"treat the worse fit as a discovered bug"* case: the 2026/27 table
   is **not** restored because it fits better. What it points at is the supply-stack **level** and
   the CT / ST / oil zero-E&AS operand D57 §4 already named — not the rating vintage.
2. **`unit_recall_gt300` and `false_retire` stay FAIL**, untouched by this arm.
3. **The Q56 / D57 collision is REPORTED, NOT RESOLVED.** The D57 clearing regime flips
   (`all_offers_clear_curve_sets_price` → `marginal_offer_sets_price`), 2,623.94 MW of coal stops
   clearing, and **zero** decisions move, because **100.0 %** of the newly-uncleared MW is EIA-860
   Sector 1 — which `retirement_sector_gate` partitions out of the economic exit decision. Routed as
   `FINDING-capx-d84-2026-09-07.md` §9 item 1, and it is now a **live** condition on `main` rather
   than a screened one.
4. **The 2025/26 BRA-vs-3IA vintage question** (D84 §3) is carried forward: that report's tables are
   images that do not extract, so the delivery year's FINAL (3IA) ratings are what is wired.

## 6. Rule 31 `[R-RETAIN]` — nothing was deleted

Both D84 screen bundles remain on local disk, undeleted and gitignored
(`results/hindcast/pjm-2021-2025-realized-t1h-d84-{control,thermalvintage}/`, 16 MB each). The
registered copy at `results/capacity-hindcast/pjm-2021-2025-realized-t1h-d84arm/` commits the slim
set (876 KB — meta, run_config, score, the five evolution ledgers, the floor-retention sidecars and
`solve_surface.json`) under the standing `results/capacity-hindcast/**` ignore rules, exactly as the
d75rarm registration did. The control is never registered (rule 29(c)) and stays fully ignored.
