# PRECOMMIT — capx D84-ARM: arming `pjm_thermal_accreditation_vintage` for PJM

**Lane:** capx D84-ARM, executing the **OWNER RULING of 2026-09-07** on
`FINDING-capx-d84-2026-09-07.md` §8's card. Branch
`claude/capx-d84-thermal-elcc-vintage-cblmzl`, rebased onto `origin/main` at `a2d9c033`.

**Pushed BEFORE `iso_configs.py` is touched.** The key census below is the **ex-ante expectation**,
measured in memory with the override simulated; the ex-post measurement must agree with it exactly,
and that agreement is the gate.

---

## 1. The ruling, and what it rules on

The owner's instruction: *"Is this a recommended keeper candidate? If so plz promote… If structural
integrity improves but gates regress that may still be a keeper."*

That is the standard §8's card was written against, and D84 meets it on the easier half: **structural
integrity improves and the gates do not regress at all.** Every one of the 361 substantive scored
records is byte-identical between arms — zero flips in either direction. What moves the wrong way is
the **published residual** in the one delivery year the mechanism touches (§4 below), reported at
full magnitude and explicitly not the reason for the change. Rule 14 `[R-ACCURATE]` is the basis:
the delivery year's OWN published accreditation is preferred over one published for a different
year, whatever it does to the fit.

**Terminology, stated once so the record is not ambiguous:** D84 is a **forecast-lane** mechanism
(capacity evolution), so this is an **ARM**, not a rule-15 backcast keeper promotion. No ISO's
keeper shard, `calibration-complete.json` entry or backcast determination is touched, and none can
be — the field is coerced off in `mode="backcast"`.

## 2. The posture — the D57 / D67 / Q55 / Q56 route, NOT a default flip

Add to `config/iso_configs.py::_pjm_config`'s `default_scenario_overrides`:

```python
"pjm_thermal_accreditation_vintage": True,
```

The shared `ScenarioConfig` dataclass default stays **`False`**, and `_CACHE_KEY_OPTIONAL_FIELDS`
keeps its `"False"` drop declaration untouched. This is the posture every prior PJM arm used
(D57/Q44, D67-ARM/Q52, Q55, Q56), and it is chosen over a `(b′-1)` declared default flip for the
reason the D76-ARM-B record makes explicit: a shared-default flip re-keys configs the gate cannot
reach — here it would move every ISO's forecast keys, ten backcast keepers included — while an ISO
override moves PJM forecast keys and nothing else.

`--no-pjm-thermal-accreditation-vintage` reaches the pre-arm posture and keeps its key
(`f736025631d0d27e`), so the control remains expressible.

## 3. EX-ANTE KEY CENSUS — the expectation, recorded before the edit

Instrument: `scripts/probes/capxd84arm_iso_override_no_op_check.py --simulate-arm`
→ `docs/handoffs/d84arm/no-op-expectation.json`. It is the D78-ARM probe verbatim with the field
name changed, so the semantics (backcast coercion, the OVERRIDE-FIX explicit-caller rule) are the
shipped path's own rather than a restatement.

**227 committed run configs; override ABSENT on disk (simulated in memory).**

| ISO / mode | configs | moved |
|---|---:|---:|
| CAISO / backcast | 1 | **0** |
| CAISO / forecast | 21 | **0** |
| ERCOT / backcast | 6 | **0** |
| ERCOT / forecast | 31 | **0** |
| MISO / backcast | 1 | **0** |
| MISO / forecast | 34 | **0** |
| NEISO / backcast | 5 | **0** |
| NEISO / forecast | 56 | **0** |
| NYISO / backcast | 7 | **0** |
| NYISO / forecast | 28 | **0** |
| **PJM / backcast** | 2 | **0** |
| **PJM / forecast** | **33** | **33** |
| SPP / backcast | 1 | **0** |
| SPP / forecast | 1 | **0** |

**33 keys move; ALL of them PJM/forecast. Zero non-PJM. Zero backcast.** Recipe legs:

| recipe | key | field |
|---|---|---|
| **`pjm-t1h-bare`** | **`b9fa47dedb6c3319`** | **True** |
| `miso-t1h-bare` | `71156d9eb2ea896d` | False |
| `nyiso-t1h-bare` | `ee0d44e7d6f26397` | False |
| `neiso-t1h-bare` | `806f31b59b10c911` | False |
| `caiso-t1h-bare` | `51c069044689c42b` | False |
| `ercot-t1h-bare` | `a9ef8b9769d44320` | False |
| `pjm-plain-backcast` | `3a566deac3a85682` | False (unmoved) |

**The decisive line: the armed bare `pjm-t1h` keys `b9fa47dedb6c3319`, which is EXACTLY the key of
the arm bundle D84 already solved.** So the armed recipe is already solved on this container and no
re-solve is owed for registration.

**Rebase safety, checked before this was written:** both keys are unchanged across the rebase onto
`a2d9c033` (29 commits), so every one of those commits is INERT for PJM's hindcast solve surface and
the solved bundle is still the armed recipe at the new HEAD.

## 4. What arming does NOT close — carried forward verbatim from FINDING §8

- The model still clears **above** PJM's published DY 2025/26 position and prices **below** it, and
  this repair moves both **further**: cleared MW **+481.708 MW** further above published on both D66
  frames, price **$34.961/MW-day** further below the published **$269.92**. Reported, never the
  reason (rules 1/14).
- **`unit_recall_gt300` and `false_retire` stay FAIL**, untouched.
- **The Q56 / D57 collision is REPORTED, NOT RESOLVED**: 100.0 % of the newly-uncleared MW is
  EIA-860 Sector 1, which `retirement_sector_gate` partitions out of the exit decision, so the
  clearing's failing set moves while nothing in it can exit. Routed as FINDING §9 item 1.
- The **2025/26 BRA-vs-3IA vintage** question (FINDING §3) is carried forward, not answered — that
  report's tables are images that do not extract.

## 5. Duties this lane discharges

1. `iso_configs.py::_pjm_config` override + its citation block.
2. Ex-post probe run with `--simulate-arm` **omitted**; it must reproduce §3 exactly.
3. The armed `pjm-t1h` **registered on the FORECAST namespace** (`scripts/register_forecast_run.py`)
   from the already-solved `b9fa47dedb6c3319` bundle — the registration Q55/Q56 each owed.
4. Rule 28 duty (b): the PJM matrix cell re-stamped `K` with the arm's citation.
5. Rule 31: the bundles stay on disk, undeleted, and stay gitignored.
