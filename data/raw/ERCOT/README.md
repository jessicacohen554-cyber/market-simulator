# ERCOT — raw publications (payload gitignored)

Potomac Economics' **annual State of the Market (SOM) report for ERCOT**, 2019
through 2025. Potomac is ERCOT's Independent Market Monitor; these are the
published market-assessment volumes.

> **Payload posture.** The 7 PDFs (33.7 MiB) are **gitignored and no longer
> tracked at tip** — BLOAT-B-2 corpus conversion,
> `docs/bloat-removal-plan-2026-08.md` §4.5 item B5 (class-approved under
> release-plan §6 decision 4). Only this README and `SHA256SUMS.txt` are
> tracked. Nothing in `src/`, `scripts/` or `tests/` opens these files: they are
> **hand-read citation sources**, and the values taken from them are recorded
> with their citations in `docs/parameter-citations.md`, `constants.py` and
> `scenarios.py` comments. Re-verified by fresh grep at `315a245` (2026-08-15).

## Sources

Every URL below was fetched and **verified byte-exact against the committed
file on 2026-08-15** (HTTP 200, `Content-Length` equal to the manifest's
`size_bytes`).

| File | Report | Source URL |
|---|---|---|
| `2019-State-of-the-Market-Report.pdf` | 2019 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2020/06/2019-State-of-the-Market-Report.pdf> |
| `2020-ERCOT-State-of-the-Market-Report.pdf` | 2020 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2021/06/2020-ERCOT-State-of-the-Market-Report.pdf> |
| `2021-State-of-the-Market-Report.pdf` | 2021 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2022/05/2021-State-of-the-Market-Report.pdf> |
| `2022-State-of-the-Market-Report_Final_060623.pdf` | 2022 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2023/05/2022-State-of-the-Market-Report_Final_060623.pdf> |
| `2023-State-of-the-Market-Report_Final_060624.pdf` | 2023 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2024/05/2023-State-of-the-Market-Report_Final_060624.pdf> |
| `2024-State-of-the-Market-Report.pdf` | 2024 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-State-of-the-Market-Report.pdf> |
| `2025-State-of-the-Market-Report-for-ERCOT.pdf` | 2025 SOM for ERCOT | <https://www.potomaceconomics.com/wp-content/uploads/2026/06/2025-State-of-the-Market-Report-for-ERCOT.pdf> |

Landing page (if a URL ever moves): <https://www.potomaceconomics.com/markets-monitored/ercot/>.
The `wp-content/uploads/<YYYY>/<MM>/` segment is the WordPress upload month, so
it does **not** generalize from the report year — take the URLs above verbatim.

## Recovery / re-fetch

1. **Restore from git history — exact bytes, always available.** History is
   kept (no rewrite), so every payload stays fetchable from the promisor remote
   at the pin sha:

   ```
   git restore --source=315a24524a851566c3d32cc88668fa32dcbd1d74 -- data/raw/ERCOT
   ```

   **Pin sha `315a24524a851566c3d32cc88668fa32dcbd1d74`** — the last commit at
   which these PDFs were tracked (origin/main, 2026-08-15).

2. **Re-fetch from the publisher.** Run from this directory — each URL's last
   path segment is already the committed filename, so `-O` lands them correctly:

   ```
   xargs -n1 curl -fLO <<'URLS'
   https://www.potomaceconomics.com/wp-content/uploads/2020/06/2019-State-of-the-Market-Report.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2021/06/2020-ERCOT-State-of-the-Market-Report.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2022/05/2021-State-of-the-Market-Report.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2023/05/2022-State-of-the-Market-Report_Final_060623.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2024/05/2023-State-of-the-Market-Report_Final_060624.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2025/06/2024-State-of-the-Market-Report.pdf
   https://www.potomaceconomics.com/wp-content/uploads/2026/06/2025-State-of-the-Market-Report-for-ERCOT.pdf
   URLS
   sha256sum -c <(awk '$1 !~ /^#/ && NF>=3 {s=$1; $1=$2=""; sub(/^ +/,""); print s "  " $0}' SHA256SUMS.txt)
   ```

   `SHA256SUMS.txt` carries the sha256 + byte size of all 7 payloads as of the
   pin sha, so a re-fetch is verifiable rather than merely plausible.
