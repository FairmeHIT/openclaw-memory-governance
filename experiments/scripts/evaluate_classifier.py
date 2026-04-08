#!/usr/bin/env python3

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Dict, List, Tuple


def load_jsonl(path: Path) -> List[Dict]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def sorted_list(values: List[str]) -> List[str]:
    return sorted(values)


def accuracy(pairs: List[Tuple[str, str]]) -> float:
    if not pairs:
        return 0.0
    correct = sum(1 for gold, pred in pairs if gold == pred)
    return round(correct / len(pairs), 4)


def build_confusion(pairs: List[Tuple[str, str]]) -> Dict[str, Dict[str, int]]:
    matrix: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for gold, pred in pairs:
        matrix[gold][pred] += 1
    return {
        gold: dict(sorted(preds.items()))
        for gold, preds in sorted(matrix.items())
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate chunk classification against a manually curated gold set.")
    parser.add_argument("--gold", default="experiments/datasets/classification_gold.jsonl")
    parser.add_argument("--predicted", default="experiments/datasets/real_memory_chunks.jsonl")
    parser.add_argument("--run-id", default="classifier_eval_v1")
    args = parser.parse_args()

    gold_rows = load_jsonl(Path(args.gold))
    predicted_rows = {
        item["chunk_id"]: item
        for item in load_jsonl(Path(args.predicted))
    }

    run_dir = Path("experiments/runs") / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    field_pairs = {
        "domain": [],
        "privacy_level": [],
        "purpose_allow": [],
        "index_policy": [],
    }
    per_privacy_total: Counter = Counter()
    per_privacy_correct: Counter = Counter()
    details = []
    missing_chunk_ids = []

    for row in gold_rows:
        chunk_id = row["chunk_id"]
        predicted = predicted_rows.get(chunk_id)
        if predicted is None:
            missing_chunk_ids.append(chunk_id)
            continue

        gold_purpose = sorted_list(row["gold_purpose_allow"])
        predicted_purpose = sorted_list(predicted["purpose_allow"])

        field_pairs["domain"].append((row["gold_domain"], predicted["domain"]))
        field_pairs["privacy_level"].append((row["gold_privacy_level"], predicted["privacy_level"]))
        field_pairs["purpose_allow"].append(("|".join(gold_purpose), "|".join(predicted_purpose)))
        field_pairs["index_policy"].append((row["gold_index_policy"], predicted["index_policy"]))

        per_privacy_total[row["gold_privacy_level"]] += 1
        if row["gold_privacy_level"] == predicted["privacy_level"]:
            per_privacy_correct[row["gold_privacy_level"]] += 1

        details.append({
            "chunk_id": chunk_id,
            "gold_domain": row["gold_domain"],
            "predicted_domain": predicted["domain"],
            "gold_privacy_level": row["gold_privacy_level"],
            "predicted_privacy_level": predicted["privacy_level"],
            "gold_purpose_allow": gold_purpose,
            "predicted_purpose_allow": predicted_purpose,
            "gold_index_policy": row["gold_index_policy"],
            "predicted_index_policy": predicted["index_policy"],
            "privacy_match": row["gold_privacy_level"] == predicted["privacy_level"],
            "domain_match": row["gold_domain"] == predicted["domain"],
            "purpose_allow_match": gold_purpose == predicted_purpose,
            "index_policy_match": row["gold_index_policy"] == predicted["index_policy"],
            "notes": row.get("notes", ""),
            "raw_text": predicted.get("raw_text", ""),
        })

    metrics = {
        "run_id": args.run_id,
        "gold_size": len(gold_rows),
        "evaluated_size": len(details),
        "missing_chunk_ids": missing_chunk_ids,
        "domain_accuracy": accuracy(field_pairs["domain"]),
        "privacy_level_accuracy": accuracy(field_pairs["privacy_level"]),
        "purpose_allow_accuracy": accuracy(field_pairs["purpose_allow"]),
        "index_policy_accuracy": accuracy(field_pairs["index_policy"]),
        "privacy_confusion_matrix": build_confusion(field_pairs["privacy_level"]),
        "per_privacy_recall": {
            label: round(per_privacy_correct[label] / total, 4)
            for label, total in sorted(per_privacy_total.items())
        },
        "error_breakdown": {
            "domain_mismatch_count": sum(1 for item in details if not item["domain_match"]),
            "privacy_mismatch_count": sum(1 for item in details if not item["privacy_match"]),
            "purpose_allow_mismatch_count": sum(1 for item in details if not item["purpose_allow_match"]),
            "index_policy_mismatch_count": sum(1 for item in details if not item["index_policy_match"]),
        },
    }

    (run_dir / "metrics.json").write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (run_dir / "details.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in details),
        encoding="utf-8",
    )
    print(json.dumps(metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
