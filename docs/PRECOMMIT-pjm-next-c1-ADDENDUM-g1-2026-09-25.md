# PRECOMMIT ADDENDUM — PJM-NEXT card 1: G1 corrections before the relaunch (2026-09-25)

This addendum was written **before any relaunched solve**. The original PRECOMMIT is
`docs/PRECOMMIT-pjm-next-c1-year-correct-membership-2026-09-25.md`. Recipe, predictions, DOF and
the G-DRIFT audit are unchanged; only the G1 wording changes. The code and data at the new pin are
byte-identical, on the solve path, to the first launch's pin `7f095384`.

## What went wrong in the first launch (the parent's own prompt defects, not model results)

Two first-launch arm shards (2022, 2023) stopped with blocker docs on their own branches.

- **G1(c) is unsatisfiable.** It required the solve log to name `vintage_<y>`. The runner switches the
  EIA-860 directory silently and logs no path. This check could never pass.
- **G1(e) is miscounted.** The expected N came from the phase-0 loader census on a different basis
  from the log line the shard reads. The log counts injected **rows** at injection, observed as **77**
  in 2022 and **49** in 2023; the PRECOMMIT expected 73 and 45. The injected plant sets are supersets of
  §1a's large plants, and the additions are small units: 2023 adds 9 plants totalling ~57 MW. §1a's
  plant-level census stands; only the gate's count was wrong.
- **Memory.** A full `regenerate_clean.py` left only ~6.9 GiB of disk, so only 3 GiB of swap could be
  provisioned. 2022 was OOM-killed after P0, and 2023 completed with 0.46 GiB of headroom.

## Corrected G1 (relaunch)

- **(a), (b), (d), (g):** unchanged.
- **(c):** replaced. `run_config.json` `scenario_config.eia860_vintage_tracks_solve_year` must be true;
  (a) already covers this. There is no log check.
- **(e) arm:** the log line `mid-vintage-year exit carry (PJM <y>): injecting N unit(s)` must appear with
  **N > 0** for 2019–2024. The shard reports N, MW and the plant list, and the parent adjudicates. 2025:
  there is no such line. Control: no such line.
- **(f):** unchanged. The line appears with K > 0 in 2019–2022, 2024 and 2025, and may be absent in 2023.
- **Clean tree:** run `regenerate_clean.py` only on the datatypes the solve names. The shard regenerates
  on each `FileNotFoundError` that names one, rather than running the full 58-datatype pass.

Relaunch: the same eleven legs (7 arm + 4 control), the same out-dirs, and branches suffixed `-r2`.
