import json
import unittest
from copy import deepcopy
from scheduler import *

SHA = "a" * 64


def locked():
    return lock_protocol(new_checkpoint(), SHA, 1_000)


def entered():
    s = locked()
    ledger = {
        "schema": "r21.virtual-ledger.v1", "protocol_sha256": SHA,
        "root_lock": deepcopy(s["root_lock"]),
        "entry": {"entry_time_ms": 2_000, "quantity": "0.5",
                  "entry_reference_id": "synthetic-only"},
        "accounts": {c: {"funding_cash": "0"} for c in ("0.003", "0.006")}, "funding_events": {}, "last_funding_time_ms": 2_000,
    }
    return attach_ledger(s, ledger)


class SchedulerTests(unittest.TestCase):
    def test_unlocked_no_actions(self):
        self.assertEqual(due_work(new_checkpoint(), 10_000)["actions"], [])

    def test_locked_does_not_initialize(self):
        s = locked()
        self.assertEqual(due_work(s, 3_000)["actions"][0]["purpose"], "entry_reference")
        self.assertIsNone(s["entry"])

    def test_immutable_lock(self):
        with self.assertRaises(ValueError):
            lock_protocol(locked(), "b" * 64, 2_000)

    def test_entry_after_lock(self):
        s = entered()
        l = deepcopy(s["ledger"]); l["entry"]["entry_time_ms"] = 999
        with self.assertRaises(ValueError):
            attach_ledger(locked(), l)

    def test_no_schedule_no_funding(self):
        p = due_work(entered(), 100_000)
        self.assertEqual([x["source"] for x in p["actions"]], ["quote_pair"])
        self.assertTrue(p["required_information"])

    def test_funding_due_and_late_resume(self):
        s = record_schedule(entered(), 10_000, 3_000, "fixture")
        self.assertFalse(any(x["source"] == "funding_history"
                             for x in due_work(s, 9_999)["actions"]))
        a = due_work(s, 100_000)["actions"][-1]
        self.assertEqual((a["startTime"], a["endTime"]), (2_001, 100_000))

    def test_reservation_blocks_duplicate(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        self.assertFalse(due_work(s, 10_000_000)["actions"])
        self.assertTrue(validate_restored(json.loads(json.dumps(s))))

    def test_hourly_rolling_budget(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        s = complete_request(s, "quote_pair", "r1", "ok", 4_000, "snapshot")
        self.assertFalse(due_work(s, 3_000 + HOUR_MS - 1)["actions"])
        self.assertEqual(len(due_work(s, 3_000 + HOUR_MS)["actions"]), 1)

    def test_empty_does_not_advance_cursor(self):
        s = record_schedule(entered(), 10_000, 3_000, "fixture")
        s = reserve_request(s, "funding_history", "r1", 10_000)
        s = complete_request(s, "funding_history", "r1", "empty", 11_000, "empty")
        self.assertEqual(s["ledger"]["last_funding_time_ms"], 2_000)
        self.assertNotIn("funding_history",
                         [a["source"] for a in due_work(s, 12_000)["actions"]])

    def test_forbidden_stays_halted(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        s = complete_request(s, "quote_pair", "r1", "forbidden", 4_000)
        self.assertFalse(due_work(s, 10**12)["actions"])

    def test_429_exact_reset(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        s = complete_request(s, "quote_pair", "r1", "rate_limited", 4_000,
                             retry_after="7200")
        self.assertFalse(due_work(s, 7_204_000 - 1)["actions"])
        self.assertEqual(len(due_work(s, 7_204_000)["actions"]), 1)

    def test_429_no_reset_halts(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        s = complete_request(s, "quote_pair", "r1", "rate_limited", 4_000)
        self.assertFalse(due_work(s, 10**12)["actions"])

    def test_retry_after_http_date(self):
        self.assertEqual(parse_retry_after("Thu, 01 Jan 1970 01:00:00 GMT", 0),
                         HOUR_MS)
        self.assertIsNone(parse_retry_after("soon", 0))

    def test_uncertain_not_retried(self):
        s = reserve_request(locked(), "quote_pair", "r1", 3_000)
        s = complete_request(s, "quote_pair", "r1", "uncertain", 4_000)
        self.assertFalse(due_work(s, 10**12)["actions"])

    def test_dedup_map_and_no_forced_stop_30(self):
        s = entered(); l = deepcopy(s["ledger"])
        for n in range(30):
            t = 10_000 + n
            l["funding_events"][f"ETHUSDT:{t}"] = {"funding_time_ms": t, "rate": "0.0001",
                                                  "mark": "1000", "cash": "0.05"}
        l["last_funding_time_ms"] = t
        for a in l["accounts"].values(): a["funding_cash"] = "1.50"
        s = attach_ledger(s, l)
        self.assertTrue(due_work(s, 20_000)["review_first_30"])
        self.assertFalse(due_work(s, 20_000)["forced_stop"])
        same = attach_ledger(s, l)
        self.assertEqual(len(same["ledger"]["funding_events"]), 30)

    def test_conflicting_funding_rejected(self):
        s = entered(); l = deepcopy(s["ledger"])
        l["funding_events"]["ETHUSDT:10000"] = {"funding_time_ms": 10000, "rate": "0.002", "mark": "1000", "cash": "1"}
        for a in l["accounts"].values(): a["funding_cash"] = "1"
        l["last_funding_time_ms"] = 10_000; s = attach_ledger(s, l)
        l["funding_events"]["ETHUSDT:10000"] = {"cash": "2"}
        with self.assertRaises(ValueError):
            attach_ledger(s, l)

    def test_entry_boundary_and_cursor(self):
        s = entered(); l = deepcopy(s["ledger"])
        l["funding_events"]["ETHUSDT:2000"] = {"cash": "1"}
        with self.assertRaises(ValueError):
            attach_ledger(s, l)
        l["funding_events"] = {"ETHUSDT:2001": {"cash": "1"}}
        with self.assertRaises(ValueError):
            attach_ledger(s, l)  # cursor still 2000

    def test_corrupt_account_restore_rejected(self):
        s = entered()
        s["ledger"]["accounts"]["0.003"]["funding_cash"] = "123"
        with self.assertRaises(ValueError): validate_restored(s)

    def test_corrupt_event_formula_rejected(self):
        s = entered(); l = deepcopy(s["ledger"])
        l["funding_events"]["ETHUSDT:10000"] = {"funding_time_ms": 10000, "rate": "0.002", "mark": "1000", "cash": "2"}
        l["last_funding_time_ms"] = 10000
        for a in l["accounts"].values(): a["funding_cash"] = "2"
        with self.assertRaises(ValueError): attach_ledger(s, l)

    def test_event_key_time_rejected(self):
        s = entered(); l = deepcopy(s["ledger"])
        l["funding_events"]["ETHUSDT:10000"] = {"funding_time_ms": 9999, "rate": "0", "mark": "1000", "cash": "0"}
        l["last_funding_time_ms"] = 10000
        with self.assertRaises(ValueError): attach_ledger(s, l)

    def test_manifest_lock_preserved(self):
        s = lock_protocol(new_checkpoint(), SHA, 1000, "b" * 64)
        self.assertEqual(json.loads(json.dumps(s))["root_lock"]["artifact_manifest_sha256"], "b" * 64)

    def test_schedule_change_no_fixed_8h(self):
        s = record_schedule(entered(), 8_000_000, 3_000, "old")
        s = record_schedule(s, 4_000_000, 4_000, "new-shorter-interval")
        self.assertTrue(any(a["source"] == "funding_history"
                            for a in due_work(s, 4_000_000)["actions"]))

    def test_verified_resume_hash_gate(self):
        artifacts = {path: b"synthetic fixture" for path in REQUIRED_ARTIFACTS}
        raw = json.dumps({"schema": "r21.forward-artifact-manifest.v1", "sha256": {p: hash_bytes(b).hexdigest() for p,b in artifacts.items()}}).encode()
        s = lock_protocol(new_checkpoint(), SHA, 1000, hash_bytes(raw).hexdigest())
        self.assertTrue(verified_due_work(s, 3000, raw, artifacts)["actions"])
        artifacts[next(iter(artifacts))] = b"tampered"
        with self.assertRaises(ValueError): verified_due_work(s, 3000, raw, artifacts)
        with self.assertRaises(ValueError): verified_due_work(s, 3000, raw+b" ", artifacts)
        with self.assertRaises(ValueError): verified_due_work(locked(), 3000, raw, artifacts)

    def test_feasibility_failure_latches(self):
        s = record_feasibility_failure(entered(), 3000, "negative-margin-fixture")
        later = record_feasibility_failure(s, 4000, "later-fixture")
        self.assertEqual(later["feasibility_failure"], s["feasibility_failure"])
        self.assertEqual(later["feasibility_failure"]["continuation_mode"], "counterfactual_only")

    def test_revision_race(self):
        s = locked()
        with self.assertRaises(ValueError):
            assert_revision(s, 0)
        assert_revision(s, 1)

    def test_corrupt_restore_and_user_stop(self):
        s = entered(); s["entry"] = None
        with self.assertRaises(ValueError):
            validate_restored(s)
        s = entered(); s["stop_requested"] = True
        self.assertEqual(due_work(s, 10**12)["actions"], [])
        self.assertTrue(due_work(s, 10**12)["forced_stop"])


if __name__ == "__main__":
    unittest.main()
