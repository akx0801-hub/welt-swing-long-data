#!/usr/bin/env python3
from __future__ import annotations

import csv
import hashlib
import importlib.util
import io
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "universe" / "research_partial_1633.csv"
GENERATOR = ROOT / "scripts" / "generate_company_security_mapping_v1.py"

spec = importlib.util.spec_from_file_location("mapping_generator", GENERATOR)
mod = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(mod)


def parse(data: bytes) -> list[dict[str, str]]:
    return list(csv.DictReader(io.StringIO(data.decode("utf-8"), newline="")))


class CompanySecurityMappingV1Test(unittest.TestCase):
    def test_contract_and_determinism(self) -> None:
        source_before = SOURCE.read_bytes()
        source_rows = mod.read_source(SOURCE)
        self.assertEqual(len(source_rows), 2527)

        first = mod.generate_bytes(SOURCE)
        second = mod.generate_bytes(SOURCE)
        self.assertEqual(first, second)
        self.assertEqual(hashlib.sha256(first).hexdigest(), hashlib.sha256(second).hexdigest())
        self.assertEqual(len(first), 217498)

        rows = parse(first)
        self.assertEqual(len(rows), 2527)
        self.assertEqual([r["Source_WS_ID"] for r in rows], [r["WS_ID"].strip() for r in source_rows])

        ws_ids = [r["Source_WS_ID"] for r in rows]
        keys = [r["Security_Key"] for r in rows]
        self.assertEqual(len(ws_ids), 2527)
        self.assertEqual(len(set(ws_ids)), 2527)
        self.assertEqual(len(keys), 2527)
        self.assertEqual(len(set(keys)), 2527)
        self.assertTrue(all(r["Security_Key"] == mod.security_key(r["Source_WS_ID"]) for r in rows))

        missing = [r for r in rows if not r["ISIN"]]
        present = [r for r in rows if r["ISIN"]]
        self.assertEqual(len(missing), 1536)
        self.assertTrue(all(r["Security_Key"] for r in missing))
        self.assertTrue(all(r["Identity_Status"] == "SECURITY_UNRESOLVED" for r in missing))
        self.assertTrue(all(r["Identity_Status"] != "IDENTITY_OK" for r in missing))
        self.assertEqual(len(present), 991)
        self.assertTrue(all(r["Identity_Status"] == "COMPANY_UNRESOLVED" for r in present))

        self.assertEqual(sum(bool(r["Company_Key"]) for r in rows), 0)
        self.assertEqual(sum(not r["Company_Key"] for r in rows), 2527)
        self.assertEqual(sum(r["Identity_Confidence"] == "UNRESOLVED" for r in rows), 2527)
        self.assertEqual(sum(r["Identity_Status"] == "IDENTITY_OK" for r in rows), 0)

        # One source identity row maps to one distinct Security_Key; no merge of distinct source rows.
        self.assertEqual(len({(r["Source_WS_ID"], r["Security_Key"]) for r in rows}), 2527)
        self.assertEqual(SOURCE.read_bytes(), source_before)

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "mapping.csv"
            out.write_bytes(first)
            self.assertEqual(out.read_bytes(), first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
