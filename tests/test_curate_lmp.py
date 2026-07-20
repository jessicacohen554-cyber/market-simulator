"""Tests for scripts/data/curate_lmp.py.

Builds a tiny synthetic raw fixture for each source layout (CAISO CSV, PJM
hourly CSV, NYISO 5-min zone ZIP, ISO-NE SMD workbook), runs the curation, and
asserts the result is schema-valid and that each source reconciles onto the
canonical columns (market key, component mapping, hourly aggregation, tz->UTC).

This is NOT a full-data run: CLEAN_DIR is redirected to a temp dir (as in
tests/test_clean_io.py) so it never writes the real data/clean tree.
"""

import io
import unittest
import zipfile
from pathlib import Path

import pandas as pd

from scripts.data import curate_lmp
from scripts.lib.clean_io import validate_clean
from tests.helpers.base import CleanDirTestCase


def _write_caiso(raw_dir: Path) -> None:
    """CAISO dam + rtm CSVs (UTC stamps); dam has an embedded header row."""
    d = raw_dir / "CAISO"
    d.mkdir(parents=True)
    # 2024-01-15 00:00 PST == 08:00 UTC. Embedded repeated header must be dropped.
    (d / "CAISO_dam_hourly_2024.csv").write_text(
        "interval_start_gmt,node,LMP,MCC,MCE,MCL,MGHG\n"
        "2024-01-15 08:00:00+00:00,TH_SP15_GEN-APND,31.2,1.0,30.0,0.2,0.0\n"
        "interval_start_gmt,node,LMP,MCC,MCE,MCL,MGHG\n"  # stray header mid-file
        "2024-01-15 09:00:00+00:00,TH_SP15_GEN-APND,28.7,0.5,28.0,0.2,0.0\n"
    )
    (d / "CAISO_rtm_hourly_2024.csv").write_text(
        "interval_start_gmt,node,LMP,MCC,MCE,MCL,MGHG\n"
        "2024-01-15 08:00:00+00:00,TH_SP15_GEN-APND,40.0,2.0,38.0,0.0,0.0\n"
    )


def _write_pjm(raw_dir: Path) -> None:
    """PJM hourly nodal CSV: one row carrying both DA and RT prices."""
    (raw_dir / "PJM_2024_rt_da_monthly_lmps.csv").write_text(
        "datetime_beginning_utc,datetime_beginning_ept,pnode_id,pnode_name,voltage,"
        "equipment,type,zone,system_energy_price_rt,total_lmp_rt,congestion_price_rt,"
        "marginal_loss_price_rt,system_energy_price_da,total_lmp_da,congestion_price_da,"
        "marginal_loss_price_da\n"
        "1/15/2024 5:00:00 AM,1/15/2024 12:00:00 AM,51288,WESTERN HUB,,,HUB,,"
        "24.0,26.0,1.0,1.0,20.0,25.0,3.0,2.0\n"
    )


def _write_nyiso(raw_dir: Path) -> None:
    """NYISO real-time zone ZIP: 12 five-minute rows for one local hour, one zone.

    LBMP alternates 10/20 -> hourly mean 15.0; loss constant 1.0, cong 0.0.
    Stamps are interval-ENDING 00:05..01:00 on 2024-01-15 (local Eastern, EST).
    """
    d = raw_dir / "NYISO"
    d.mkdir(parents=True)
    lines = [
        '"Time Stamp","Name","PTID","LBMP ($/MWHr)",'
        '"Marginal Cost Losses ($/MWHr)","Marginal Cost Congestion ($/MWHr)"'
    ]
    for i in range(1, 13):  # 00:05, 00:10, ... 01:00
        ts = f"01/15/2024 00:{5 * i:02d}:00" if i < 12 else "01/15/2024 01:00:00"
        lbmp = 10.0 if i % 2 else 20.0
        lines.append(f'"{ts}","CAPITL",61757,{lbmp},1.0,0.0')
    csv_bytes = ("\n".join(lines) + "\n").encode()
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("20240115realtime_zone.csv", csv_bytes)
    (d / "20240101realtime_zone_csv.zip").write_bytes(buf.getvalue())


def _write_neiso(raw_dir: Path) -> None:
    """ISO-NE SMD workbook: a Notes sheet + one zone sheet with two hours."""
    d = raw_dir / "NEISO"
    d.mkdir(parents=True)
    ct = pd.DataFrame(
        {
            "Date": ["2024-01-15", "2024-01-15"],
            "Hr_End": [1, 2],
            "DA_LMP": [30.0, 31.0],
            "DA_EC": [29.0, 30.0],
            "DA_CC": [0.0, 0.0],
            "DA_MLC": [1.0, 1.0],
            "RT_LMP": [35.0, 36.0],
            "RT_EC": [34.0, 35.0],
            "RT_CC": [0.0, 0.0],
            "RT_MLC": [1.0, 1.0],
        }
    )
    notes = pd.DataFrame({"Notes": ["synthetic fixture"]})
    with pd.ExcelWriter(d / "2024_smd_hourly.xlsx") as xw:
        notes.to_excel(xw, sheet_name="Notes", index=False)
        ct.to_excel(xw, sheet_name="CT", index=False)


class TestCurateLmp(CleanDirTestCase):
    def setUp(self):
        super().setUp()  # redirects paths.CLEAN_DIR to self.tmp_path / "clean"
        self.raw = self.tmp_path / "lmp-data"
        self.raw.mkdir(parents=True)
        _write_caiso(self.raw)
        _write_pjm(self.raw)
        _write_nyiso(self.raw)
        _write_neiso(self.raw)

    def _run(self):
        df = curate_lmp.curate(self.raw)
        written = curate_lmp.write_all(df)
        for path in written:
            validate_clean(path)  # round-trip schema check on every file
        return df, written

    def _row(self, df, **keys):
        mask = pd.Series(True, index=df.index)
        for k, v in keys.items():
            mask &= df[k].astype(str) == str(v)
        sub = df[mask]
        self.assertEqual(
            len(sub), 1, f"expected exactly one row for {keys}, got {len(sub)}"
        )
        return sub.iloc[0]

    def test_all_partitions_schema_valid(self):
        _, written = self._run()
        # CAISO DAM/RTM, PJM DAM/RTM, NYISO RTM, NEISO DAM/RTM -> 7 partitions.
        self.assertEqual(len(written), 7)
        parts = {(p.parts[-3], p.parts[-2], p.name) for p in written}
        self.assertEqual(
            parts,
            {
                ("CAISO", "DAM", "lmp_2024.parquet"),
                ("CAISO", "RTM", "lmp_2024.parquet"),
                ("PJM", "DAM", "lmp_2024.parquet"),
                ("PJM", "RTM", "lmp_2024.parquet"),
                ("NYISO", "RTM", "lmp_2024.parquet"),
                ("NEISO", "DAM", "lmp_2024.parquet"),
                ("NEISO", "RTM", "lmp_2024.parquet"),
            },
        )

    def test_caiso_components_and_market(self):
        df, _ = self._run()
        r = self._row(
            df,
            iso="CAISO",
            market="DAM",
            node="TH_SP15_GEN-APND",
            interval_start_utc="2024-01-15 08:00:00+00:00",
        )
        self.assertAlmostEqual(r["lmp_usd_per_mwh"], 31.2)
        self.assertAlmostEqual(r["energy_usd_per_mwh"], 30.0)  # MCE
        self.assertAlmostEqual(r["congestion_usd_per_mwh"], 1.0)  # MCC
        self.assertAlmostEqual(r["loss_usd_per_mwh"], 0.2)  # MCL
        self.assertAlmostEqual(r["ghg_usd_per_mwh"], 0.0)  # MGHG
        # local wall clock is PST midnight (UTC-8).
        self.assertEqual(str(r["interval_start_local"]), "2024-01-15 00:00:00")
        # dam vs rtm split into the market key (rtm row present at same instant).
        rt = self._row(
            df,
            iso="CAISO",
            market="RTM",
            interval_start_utc="2024-01-15 08:00:00+00:00",
        )
        self.assertAlmostEqual(rt["lmp_usd_per_mwh"], 40.0)
        # the embedded mid-file header row was dropped (only 2 dam hours remain).
        self.assertEqual(len(df[(df["iso"] == "CAISO") & (df["market"] == "DAM")]), 2)

    def test_pjm_fans_out_to_both_markets(self):
        df, _ = self._run()
        da = self._row(df, iso="PJM", market="DAM", node="WESTERN HUB")
        rt = self._row(df, iso="PJM", market="RTM", node="WESTERN HUB")
        self.assertAlmostEqual(da["lmp_usd_per_mwh"], 25.0)
        self.assertAlmostEqual(da["congestion_usd_per_mwh"], 3.0)
        self.assertAlmostEqual(da["loss_usd_per_mwh"], 2.0)
        self.assertAlmostEqual(rt["lmp_usd_per_mwh"], 26.0)
        self.assertAlmostEqual(rt["energy_usd_per_mwh"], 24.0)
        # UTC authoritative; ept midnight -> 05:00 UTC.
        self.assertEqual(str(da["interval_start_utc"]), "2024-01-15 05:00:00+00:00")
        self.assertEqual(str(da["interval_start_local"]), "2024-01-15 00:00:00")

    def test_nyiso_hourly_mean_and_components(self):
        df, _ = self._run()
        r = self._row(df, iso="NYISO", market="RTM", node="CAPITL")
        self.assertAlmostEqual(r["lmp_usd_per_mwh"], 15.0)  # mean of 10/20
        self.assertAlmostEqual(r["loss_usd_per_mwh"], 1.0)
        self.assertAlmostEqual(r["congestion_usd_per_mwh"], 0.0)
        self.assertTrue(pd.isna(r["energy_usd_per_mwh"]))  # not published
        self.assertTrue(pd.isna(r["ghg_usd_per_mwh"]))
        self.assertEqual(r["zone"], "CAPITL")
        # 12 five-minute intervals collapse to ONE hourly row (hour-beginning).
        self.assertEqual(len(df[df["iso"] == "NYISO"]), 1)
        self.assertEqual(str(r["interval_start_local"]), "2024-01-15 00:00:00")
        self.assertEqual(str(r["interval_start_utc"]), "2024-01-15 05:00:00+00:00")

    def test_neiso_da_rt_split(self):
        df, _ = self._run()
        da = self._row(
            df,
            iso="NEISO",
            market="DAM",
            node="CT",
            interval_start_local="2024-01-15 00:00:00",
        )
        rt = self._row(
            df,
            iso="NEISO",
            market="RTM",
            node="CT",
            interval_start_local="2024-01-15 00:00:00",
        )
        self.assertAlmostEqual(da["lmp_usd_per_mwh"], 30.0)
        self.assertAlmostEqual(da["energy_usd_per_mwh"], 29.0)
        self.assertAlmostEqual(da["loss_usd_per_mwh"], 1.0)
        self.assertAlmostEqual(rt["lmp_usd_per_mwh"], 35.0)
        self.assertAlmostEqual(rt["energy_usd_per_mwh"], 34.0)
        # Hr_End=1 (hour-ending) -> hour-beginning 00:00 local -> 05:00 UTC (EST).
        self.assertEqual(str(da["interval_start_utc"]), "2024-01-15 05:00:00+00:00")

    def test_lmp_always_populated(self):
        df, _ = self._run()
        self.assertFalse(df["lmp_usd_per_mwh"].isna().any())

    def test_idempotent_rerun(self):
        _, first = self._run()
        _, second = self._run()
        self.assertEqual(sorted(map(str, first)), sorted(map(str, second)))


if __name__ == "__main__":
    unittest.main()
