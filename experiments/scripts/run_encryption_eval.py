#!/usr/bin/env python3

import argparse
import base64
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Tuple

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


AAD = b"openclaw-memory-governance:policy-sync:v1"


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def write_json(path: Path, data: Dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def payload_bytes(payload: List[Dict]) -> bytes:
    return json.dumps(payload, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def encrypt_payload(payload: List[Dict], key: bytes, key_id: str) -> Dict:
    if len(key) != 32:
        raise ValueError("AES-256-GCM requires a 32-byte data key")
    nonce = os.urandom(12)
    ciphertext = AESGCM(key).encrypt(nonce, payload_bytes(payload), AAD)
    return {
        "version": 1,
        "algorithm": "AES-256-GCM",
        "key_id": key_id,
        "aad": AAD.decode("ascii"),
        "nonce_b64": base64.b64encode(nonce).decode("ascii"),
        "ciphertext_b64": base64.b64encode(ciphertext).decode("ascii"),
    }


def decrypt_payload(envelope: Dict, key: bytes) -> List[Dict]:
    if envelope.get("algorithm") != "AES-256-GCM":
        raise ValueError("unsupported envelope algorithm")
    nonce = base64.b64decode(envelope["nonce_b64"], validate=True)
    ciphertext = base64.b64decode(envelope["ciphertext_b64"], validate=True)
    plaintext = AESGCM(key).decrypt(nonce, ciphertext, envelope["aad"].encode("ascii"))
    return json.loads(plaintext.decode("utf-8"))


def persisted_artifact_contains(envelope: Dict, value: str) -> bool:
    return value in json.dumps(envelope, ensure_ascii=False, sort_keys=True)


def tamper_is_detected(envelope: Dict, key: bytes) -> bool:
    ciphertext = bytearray(base64.b64decode(envelope["ciphertext_b64"], validate=True))
    ciphertext[-1] ^= 1
    tampered = {
        **envelope,
        "ciphertext_b64": base64.b64encode(bytes(ciphertext)).decode("ascii"),
    }
    try:
        decrypt_payload(tampered, key)
    except InvalidTag:
        return True
    return False


def policy_sync_payload(items: List[Dict]) -> List[Dict]:
    return [
        {
            "origin_memory_id": item["memory_id"],
            "device_id": "device_a",
            "topic": item["topic"],
            "domain": item["domain"],
            "privacy_level": item["privacy_level"],
            "content": item["summary_text"],
            "sync_mode": "policy_sync",
            "lifecycle": "active",
            "policy_metadata": True,
        }
        for item in items
        if item["privacy_level"] != "L3"
    ]


def resolve_key() -> Tuple[bytes, str, str]:
    key_hex = os.environ.get("MEMORY_GOVERNANCE_DATA_KEY_HEX")
    if key_hex:
        try:
            key = bytes.fromhex(key_hex)
        except ValueError as exc:
            raise ValueError("MEMORY_GOVERNANCE_DATA_KEY_HEX must be hexadecimal") from exc
        source = "environment_injected"
    else:
        key = AESGCM.generate_key(bit_length=256)
        source = "ephemeral_test_only"
    if len(key) != 32:
        raise ValueError("MEMORY_GOVERNANCE_DATA_KEY_HEX must encode 32 bytes")
    return key, hashlib.sha256(key).hexdigest()[:16], source


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate AES-GCM encrypted-at-rest policy-sync payloads without persisting key material."
    )
    parser.add_argument("--device-a", default="experiments/datasets/sync_device_a.jsonl")
    parser.add_argument("--run-id", default="encryption_eval_v1")
    args = parser.parse_args()

    run_dir = Path("experiments/runs") / args.run_id
    if run_dir.exists():
        shutil.rmtree(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)

    payload = policy_sync_payload(load_jsonl(Path(args.device_a)))
    key, key_id, key_source = resolve_key()
    envelope = encrypt_payload(payload, key, key_id)
    recovered = decrypt_payload(envelope, key)
    persisted = json.dumps(envelope, ensure_ascii=False, sort_keys=True)
    plaintext_values = [item["content"] for item in payload]
    metrics = {
        "run_id": args.run_id,
        "algorithm": envelope["algorithm"],
        "key_id": key_id,
        "key_source": key_source,
        "production_kms_configured": False,
        "payload_item_count": len(payload),
        "encrypted_payload_bytes": len(persisted.encode("utf-8")),
        "decryption_round_trip": recovered == payload,
        "tamper_detected": tamper_is_detected(envelope, key),
        "encrypted_payload_no_plaintext": not any(
            persisted_artifact_contains(envelope, value) for value in plaintext_values
        ),
        "key_not_persisted": not (
            persisted_artifact_contains(envelope, key.hex())
            or persisted_artifact_contains(envelope, base64.b64encode(key).decode("ascii"))
        ),
        "l3_excluded_from_payload": all(item["privacy_level"] != "L3" for item in payload),
    }
    write_json(run_dir / "encrypted_payload.json", envelope)
    write_json(run_dir / "metrics.json", metrics)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
