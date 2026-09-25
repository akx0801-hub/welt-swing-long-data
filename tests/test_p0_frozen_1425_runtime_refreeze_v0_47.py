#!/usr/bin/env python3
import importlib.util
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest import mock

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "p0_frozen_1425_runtime_refreeze_v0_47.py"
spec = importlib.util.spec_from_file_location("refreeze_v047", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

class RefreezeLifecycleTest(unittest.TestCase):
    def test_finalize_closes_before_hash(self):
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "x.sqlite"
            conn = sqlite3.connect(p)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("CREATE TABLE t(x INTEGER)")
            conn.execute("INSERT INTO t VALUES (1)")
            conn.commit()
            real = mod.stable_file_binding

            def assert_closed_then_hash(path):
                with self.assertRaises(sqlite3.ProgrammingError):
                    conn.execute("SELECT 1")
                return real(path)

            with mock.patch.object(mod, "stable_file_binding", side_effect=assert_closed_then_hash):
                result = mod.finalize_sqlite_for_binding(conn, p)

            self.assertEqual(result["sha256_pass_1"], result["sha256_pass_2"])
            self.assertEqual(result["bytes_pass_1"], result["bytes_pass_2"])
            ro = sqlite3.connect(f"file:{p.resolve()}?mode=ro", uri=True)
            try:
                self.assertEqual(ro.execute("PRAGMA integrity_check").fetchone()[0], "ok")
                self.assertEqual(ro.execute("SELECT COUNT(*) FROM t").fetchone()[0], 1)
            finally:
                ro.close()

if __name__ == "__main__":
    unittest.main()
