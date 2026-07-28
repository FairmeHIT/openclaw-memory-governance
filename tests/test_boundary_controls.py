import importlib.util
import os
import base64
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def load_module(name: str, relative_path: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


SANDBOX = load_module("run_sandbox_eval", "experiments/scripts/run_sandbox_eval.py")
SCANNER = load_module("check_artifact_boundaries", "experiments/scripts/check_artifact_boundaries.py")
OUTPUT_SHAPE = load_module("run_output_shape_eval", "experiments/scripts/run_output_shape_eval.py")
ENCRYPTION = load_module("run_encryption_eval", "experiments/scripts/run_encryption_eval.py")
DUAL_STORE = load_module("run_dual_store_sync_eval", "experiments/scripts/run_dual_store_sync_eval.py")
ADAPTER_CONTRACT = load_module("run_adapter_contract_eval", "experiments/scripts/run_adapter_contract_eval.py")
PERFORMANCE = load_module("check_performance_gates", "experiments/scripts/check_performance_gates.py")
OPENCLAW_ADAPTER = load_module("openclaw_guard_adapter", "experiments/scripts/openclaw_guard_adapter.py")
NATIVE_VALIDATOR = load_module("validate_openclaw_native_fts", "experiments/scripts/validate_openclaw_native_fts.py")


class SandboxBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.l3_item = {
            "memory_id": "l3_test",
            "privacy_level": "L3",
            "text": "护照号 P12345678 与酒店入住及返程航班信息不得对外导出。",
        }

    def test_external_l3_sandbox_request_is_blocked_without_output(self):
        result = SANDBOX.run_mode(
            "sandbox_job",
            {
                "query_id": "q_external",
                "agent_id": "content",
                "purpose": "external_share",
                "target_ids": ["l3_test"],
            },
            [self.l3_item],
            "2026-01-01T00:00:00+00:00",
        )

        self.assertTrue(result["blocked"])
        self.assertIsNone(result["returned_text"])
        self.assertFalse(result["raw_replayed"])

    def test_internal_l3_sandbox_result_does_not_replay_raw_text(self):
        result = SANDBOX.run_mode(
            "sandbox_job",
            {
                "query_id": "q_internal",
                "agent_id": "assistant",
                "purpose": "personalization",
                "target_ids": ["l3_test"],
            },
            [self.l3_item],
            "2026-01-01T00:00:00+00:00",
        )

        self.assertFalse(result["blocked"])
        self.assertFalse(result["raw_replayed"])
        self.assertNotIn(self.l3_item["text"], result["returned_text"])


class ArtifactScannerTests(unittest.TestCase):
    def test_scanner_detects_complete_l3_raw_text_in_protected_output(self):
        raw_text = "护照号 P12345678 与酒店入住及返程航班信息不得对外导出。"
        findings = SCANNER.find_raw_replays(
            "受控结果：" + raw_text,
            {"l3_test": raw_text},
            ["l3_test"],
        )

        self.assertEqual(findings, ["l3_test"])

    def test_scanner_allows_derived_output_without_complete_raw_text(self):
        findings = SCANNER.find_raw_replays(
            "受控分析：身份出行信息仅允许内部提醒，禁止对外导出。",
            {"l3_test": "护照号 P12345678 与酒店入住及返程航班信息不得对外导出。"},
            ["l3_test"],
        )

        self.assertEqual(findings, [])


class OutputShapeDatasetTests(unittest.TestCase):
    def test_l3_queries_select_the_l3_dataset(self):
        l3_dataset = {"l3_test": {"memory_id": "l3_test", "privacy_level": "L3"}}
        selected = OUTPUT_SHAPE.dataset_for_query(
            {"dataset": "l3"},
            {},
            {},
            l3_dataset,
        )

        self.assertIs(selected, l3_dataset)

    def test_external_l3_sandbox_output_is_empty(self):
        result = OUTPUT_SHAPE.run_mode(
            "sandbox_job",
            {
                "purpose": "external_share",
                "expected_keywords": [],
                "utility_min_keywords": 0,
            },
            [{"privacy_level": "L3", "text": "护照号 P12345678 不得导出。"}],
        )

        self.assertIsNone(result["returned_text"])


class EncryptionBoundaryTests(unittest.TestCase):
    def test_aes_gcm_envelope_keeps_plaintext_and_key_out_of_persisted_artifact(self):
        key = os.urandom(32)
        payload = [{"memory_id": "m1", "content": "敏感付款偏好，不得写入明文产物。"}]
        envelope = ENCRYPTION.encrypt_payload(payload, key, "test-key")

        self.assertEqual(ENCRYPTION.decrypt_payload(envelope, key), payload)
        self.assertFalse(ENCRYPTION.persisted_artifact_contains(envelope, "敏感付款偏好"))
        self.assertFalse(ENCRYPTION.persisted_artifact_contains(envelope, key.hex()))
        self.assertFalse(
            ENCRYPTION.persisted_artifact_contains(envelope, base64.b64encode(key).decode("ascii"))
        )

    def test_aes_gcm_envelope_rejects_ciphertext_tampering(self):
        key = os.urandom(32)
        envelope = ENCRYPTION.encrypt_payload([{"content": "仅用于篡改检测"}], key, "test-key")

        self.assertTrue(ENCRYPTION.tamper_is_detected(envelope, key))

    def test_policy_sync_payload_excludes_l3_records(self):
        payload = ENCRYPTION.policy_sync_payload(
            [
                {
                    "memory_id": "allowed",
                    "topic": "meal",
                    "domain": "personal",
                    "privacy_level": "L1",
                    "summary_text": "饮食偏好摘要",
                },
                {
                    "memory_id": "blocked",
                    "topic": "legal",
                    "domain": "personal",
                    "privacy_level": "L3",
                    "summary_text": "不应同步的法律材料",
                },
            ]
        )

        self.assertEqual([item["origin_memory_id"] for item in payload], ["allowed"])


class DualStoreSyncTests(unittest.TestCase):
    def test_tombstone_is_persistent_and_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "device_b.sqlite"
            DUAL_STORE.initialize_store(store)
            upsert = {
                "event_id": "upsert-1",
                "event_type": "upsert",
                "origin_memory_id": "payment-1",
                "topic": "payments",
                "domain": "personal",
                "privacy_level": "L2",
                "content": "支付习惯：固定信用卡处理订阅。",
            }
            tombstone = {
                "event_id": "revoke-1",
                "event_type": "tombstone",
                "origin_memory_id": "payment-1",
                "topic": "payments",
            }

            self.assertTrue(DUAL_STORE.apply_event(store, upsert))
            self.assertEqual(len(DUAL_STORE.active_records(store, "payments")), 1)
            self.assertTrue(DUAL_STORE.apply_event(store, tombstone))
            self.assertEqual(DUAL_STORE.active_records(store, "payments"), [])
            self.assertFalse(DUAL_STORE.apply_event(store, tombstone))

    def test_tombstone_prevents_out_of_order_upsert_from_reactivating_memory(self):
        with tempfile.TemporaryDirectory() as directory:
            store = Path(directory) / "device_b.sqlite"
            DUAL_STORE.initialize_store(store)
            tombstone = {
                "event_id": "revoke-first",
                "event_type": "tombstone",
                "origin_memory_id": "payment-1",
                "topic": "payments",
            }
            stale_upsert = {
                "event_id": "upsert-late",
                "event_type": "upsert",
                "origin_memory_id": "payment-1",
                "topic": "payments",
                "domain": "personal",
                "privacy_level": "L2",
                "content": "支付习惯：固定信用卡处理订阅。",
            }

            self.assertTrue(DUAL_STORE.apply_event(store, tombstone))
            self.assertTrue(DUAL_STORE.apply_event(store, stale_upsert))
            self.assertEqual(DUAL_STORE.active_records(store, "payments"), [])


class OpenClawAdapterContractTests(unittest.TestCase):
    def test_new_openclaw_agent_database_path_has_priority(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current_path = root / "agents" / "assistant" / "agent" / "openclaw-agent.sqlite"
            current_path.parent.mkdir(parents=True)
            current_path.touch()
            legacy_path = root / "memory" / "assistant.sqlite"
            legacy_path.parent.mkdir(parents=True)
            legacy_path.touch()

            self.assertEqual(OPENCLAW_ADAPTER.db_path_for_agent(root, "assistant"), current_path)

    def test_native_validator_uses_new_agent_database_path(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            current_path = root / "agents" / "assistant" / "agent" / "openclaw-agent.sqlite"
            current_path.parent.mkdir(parents=True)
            current_path.touch()

            self.assertEqual(NATIVE_VALIDATOR.db_path(root, "assistant"), current_path)

    def test_fts_query_preserves_ascii_words_and_chinese_terms(self):
        self.assertEqual(OPENCLAW_ADAPTER.fts_query("AI 新闻"), "AI 新闻")

    def test_fixture_contract_blocks_cross_domain_and_raw_l2_output(self):
        gates = ADAPTER_CONTRACT.evaluate_contract()

        self.assertTrue(gates["cross_domain_denied"])
        self.assertTrue(gates["l2_downgraded"])
        self.assertTrue(gates["l2_raw_suppressed"])
        self.assertTrue(gates["l3_sandbox_queued"])


class PerformanceGateTests(unittest.TestCase):
    def test_prototype_latency_and_size_thresholds_pass_for_bounded_metrics(self):
        gates = PERFORMANCE.evaluate_gates(
            {
                "real_chunk_baseline_retrieval_p50": 2.0,
                "real_chunk_guarded_retrieval_p50": 2.4,
                "real_chunk_guarded_policy_eval_p50": 0.1,
                "sandbox_job_overhead_p50": 4.0,
                "encryption_payload_bytes": 1500,
            }
        )

        self.assertTrue(all(gates.values()))


if __name__ == "__main__":
    unittest.main()
