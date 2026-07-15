import argparse
import json
import random
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any


EVALUATION_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = EVALUATION_DIRECTORY.parent
BACKEND_DIRECTORY = PROJECT_DIRECTORY / "backend"

DATASET_PATH = (
    EVALUATION_DIRECTORY
    / "data"
    / "sms_spam_collection.jsonl"
)

RESULTS_DIRECTORY = (
    EVALUATION_DIRECTORY
    / "results"
)

METRICS_PATH = (
    RESULTS_DIRECTORY
    / "evaluation_metrics.json"
)

REPORT_PATH = (
    RESULTS_DIRECTORY
    / "evaluation_report.md"
)

LLM_PREDICTIONS_PATH = (
    RESULTS_DIRECTORY
    / "llm_predictions.jsonl"
)

sys.path.insert(
    0,
    str(BACKEND_DIRECTORY),
)

from main import analyze_scam_message
from llm_analyzer import analyze_message_with_llm


def load_dataset():
    if not DATASET_PATH.exists():
        raise FileNotFoundError(
            "Dataset is missing. Run download_sms_dataset.py first."
        )

    records = []

    with DATASET_PATH.open(
        "r",
        encoding="utf-8",
    ) as dataset_file:
        for line in dataset_file:
            line = line.strip()

            if not line:
                continue

            records.append(
                json.loads(line)
            )

    return records


def safe_divide(
    numerator: float,
    denominator: float,
):
    if denominator == 0:
        return 0.0

    return numerator / denominator


def calculate_metrics(
    actual_labels: list[bool],
    predicted_labels: list[bool],
):
    true_positive = 0
    true_negative = 0
    false_positive = 0
    false_negative = 0

    for actual, predicted in zip(
        actual_labels,
        predicted_labels,
    ):
        if actual and predicted:
            true_positive += 1

        elif not actual and not predicted:
            true_negative += 1

        elif not actual and predicted:
            false_positive += 1

        elif actual and not predicted:
            false_negative += 1

    total = (
        true_positive
        + true_negative
        + false_positive
        + false_negative
    )

    accuracy = safe_divide(
        true_positive + true_negative,
        total,
    )

    precision = safe_divide(
        true_positive,
        true_positive + false_positive,
    )

    recall = safe_divide(
        true_positive,
        true_positive + false_negative,
    )

    specificity = safe_divide(
        true_negative,
        true_negative + false_positive,
    )

    f1_score = safe_divide(
        2 * precision * recall,
        precision + recall,
    )

    return {
        "evaluated_messages": total,
        "true_positive": true_positive,
        "true_negative": true_negative,
        "false_positive": false_positive,
        "false_negative": false_negative,
        "accuracy": round(
            accuracy,
            4,
        ),
        "precision": round(
            precision,
            4,
        ),
        "recall": round(
            recall,
            4,
        ),
        "specificity": round(
            specificity,
            4,
        ),
        "f1_score": round(
            f1_score,
            4,
        ),
    }


def evaluate_rule_engine(
    records: list[dict[str, Any]],
    threshold: int,
):
    actual_labels = []
    predicted_labels = []
    latencies = []
    prediction_records = []

    print()
    print("=" * 70)
    print("EVALUATING RULE ENGINE ON COMPLETE DATASET")
    print("=" * 70)

    for index, record in enumerate(
        records,
        start=1,
    ):
        started_at = time.perf_counter()

        analysis = analyze_scam_message(
            record["text"],
            "sms",
        )

        latency_ms = (
            time.perf_counter()
            - started_at
        ) * 1000

        predicted_spam = (
            analysis["risk_score"]
            >= threshold
        )

        actual_spam = (
            record["label"]
            == "spam"
        )

        actual_labels.append(
            actual_spam
        )

        predicted_labels.append(
            predicted_spam
        )

        latencies.append(
            latency_ms
        )

        prediction_records.append(
            {
                "id": record["id"],
                "actual_label": record["label"],
                "predicted_label": (
                    "spam"
                    if predicted_spam
                    else "ham"
                ),
                "risk_score": analysis[
                    "risk_score"
                ],
                "risk_level": analysis[
                    "risk_level"
                ],
                "detected_patterns": analysis[
                    "detected_patterns"
                ],
                "latency_ms": round(
                    latency_ms,
                    4,
                ),
            }
        )

        if index % 500 == 0:
            print(
                f"Processed {index}/{len(records)} messages"
            )

    metrics = calculate_metrics(
        actual_labels,
        predicted_labels,
    )

    metrics["risk_threshold"] = threshold
    metrics["average_latency_ms"] = round(
        statistics.mean(latencies),
        4,
    )

    metrics["median_latency_ms"] = round(
        statistics.median(latencies),
        4,
    )

    rule_predictions_path = (
        RESULTS_DIRECTORY
        / "rule_engine_predictions.jsonl"
    )

    with rule_predictions_path.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for prediction in prediction_records:
            output_file.write(
                json.dumps(
                    prediction,
                    ensure_ascii=False,
                )
                + "\n"
            )

    return metrics


def load_llm_checkpoint():
    checkpoint = {}

    if not LLM_PREDICTIONS_PATH.exists():
        return checkpoint

    with LLM_PREDICTIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as checkpoint_file:
        for line in checkpoint_file:
            line = line.strip()

            if not line:
                continue

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            checkpoint[
                str(record["id"])
            ] = record

    return checkpoint


def save_llm_checkpoint(
    prediction: dict[str, Any],
):
    with LLM_PREDICTIONS_PATH.open(
        "a",
        encoding="utf-8",
    ) as checkpoint_file:
        checkpoint_file.write(
            json.dumps(
                prediction,
                ensure_ascii=False,
            )
            + "\n"
        )


def select_balanced_sample(
    records: list[dict[str, Any]],
    per_class: int,
    seed: int,
):
    spam_records = [
        record
        for record in records
        if record["label"] == "spam"
    ]

    ham_records = [
        record
        for record in records
        if record["label"] == "ham"
    ]

    random_generator = random.Random(
        seed
    )

    spam_sample = random_generator.sample(
        spam_records,
        min(
            per_class,
            len(spam_records),
        ),
    )

    ham_sample = random_generator.sample(
        ham_records,
        min(
            per_class,
            len(ham_records),
        ),
    )

    sample = spam_sample + ham_sample

    random_generator.shuffle(
        sample
    )

    return sample


def get_llm_prediction(
    llm_result: dict[str, Any],
):
    if (
        llm_result.get("status")
        != "completed"
    ):
        return None

    analysis = llm_result.get(
        "analysis"
    )

    if not isinstance(
        analysis,
        dict,
    ):
        return None

    verdict = str(
        analysis.get(
            "verdict",
            "",
        )
    ).strip().lower()

    return verdict != "legitimate"


def evaluate_llm(
    records: list[dict[str, Any]],
    per_class: int,
    delay_seconds: float,
    seed: int,
):
    sample = select_balanced_sample(
        records,
        per_class,
        seed,
    )

    checkpoint = load_llm_checkpoint()

    actual_labels = []
    predicted_labels = []
    latencies = []

    failed_requests = 0
    completed_requests = 0

    print()
    print("=" * 70)
    print("EVALUATING GEMINI ON BALANCED SAMPLE")
    print("=" * 70)
    print(
        f"Sample size: {len(sample)} "
        f"({per_class} spam and {per_class} legitimate)"
    )

    for index, record in enumerate(
        sample,
        start=1,
    ):
        checkpoint_key = str(
            record["id"]
        )

        existing_prediction = (
            checkpoint.get(
                checkpoint_key
            )
        )

        if existing_prediction:
            print(
                f"[{index}/{len(sample)}] "
                f"Using saved prediction for message {record['id']}"
            )

            prediction_record = (
                existing_prediction
            )

        else:
            print(
                f"[{index}/{len(sample)}] "
                f"Analyzing message {record['id']} with Gemini"
            )

            rule_analysis = analyze_scam_message(
                record["text"],
                "sms",
            )

            llm_result = analyze_message_with_llm(
                message=record["text"],
                channel="sms",
                rule_analysis=rule_analysis,
                transaction_context={},
            )

            prediction_record = {
                "id": record["id"],
                "actual_label": record["label"],
                "text": record["text"],
                "llm_result": llm_result,
            }

            save_llm_checkpoint(
                prediction_record
            )

            checkpoint[
                checkpoint_key
            ] = prediction_record

            if index < len(sample):
                time.sleep(
                    delay_seconds
                )

        llm_result = prediction_record[
            "llm_result"
        ]

        predicted_spam = get_llm_prediction(
            llm_result
        )

        if predicted_spam is None:
            failed_requests += 1
            continue

        completed_requests += 1

        actual_spam = (
            record["label"]
            == "spam"
        )

        actual_labels.append(
            actual_spam
        )

        predicted_labels.append(
            predicted_spam
        )

        latency_ms = llm_result.get(
            "latency_ms",
            0,
        )

        if isinstance(
            latency_ms,
            (int, float),
        ):
            latencies.append(
                float(latency_ms)
            )

    metrics = calculate_metrics(
        actual_labels,
        predicted_labels,
    )

    metrics["requested_messages"] = len(
        sample
    )

    metrics["completed_requests"] = (
        completed_requests
    )

    metrics["failed_requests"] = (
        failed_requests
    )

    metrics["sample_per_class"] = (
        per_class
    )

    metrics["seed"] = seed

    metrics["average_latency_ms"] = (
        round(
            statistics.mean(
                latencies
            ),
            2,
        )
        if latencies
        else 0
    )

    return metrics


def percentage(
    value: float,
):
    return f"{value * 100:.2f}%"


def create_markdown_report(
    results: dict[str, Any],
):
    rule_metrics = results[
        "rule_engine"
    ]

    llm_metrics = results.get(
        "gemini_llm"
    )

    lines = [
        "# SurakshaNet AI Evaluation Report",
        "",
        f"Generated: {results['generated_at']}",
        "",
        "## Evaluation Scope",
        "",
        (
            "The UCI SMS Spam Collection is used to evaluate the "
            "message-classification layer. Transaction fraud scoring, "
            "n8n automation and Telegram delivery are outside this "
            "dataset benchmark."
        ),
        "",
        "## Dataset",
        "",
        f"- Total messages: {results['dataset']['total_messages']}",
        f"- Spam messages: {results['dataset']['spam_messages']}",
        f"- Legitimate messages: {results['dataset']['ham_messages']}",
        "- Source: UCI Machine Learning Repository",
        "- Dataset: SMS Spam Collection",
        "- License: CC BY 4.0",
        "",
        "## Deterministic Rule Engine",
        "",
        "| Metric | Result |",
        "|---|---:|",
        (
            f"| Evaluated messages | "
            f"{rule_metrics['evaluated_messages']} |"
        ),
        (
            f"| Accuracy | "
            f"{percentage(rule_metrics['accuracy'])} |"
        ),
        (
            f"| Precision | "
            f"{percentage(rule_metrics['precision'])} |"
        ),
        (
            f"| Recall | "
            f"{percentage(rule_metrics['recall'])} |"
        ),
        (
            f"| Specificity | "
            f"{percentage(rule_metrics['specificity'])} |"
        ),
        (
            f"| F1 score | "
            f"{percentage(rule_metrics['f1_score'])} |"
        ),
        (
            f"| Average latency | "
            f"{rule_metrics['average_latency_ms']} ms |"
        ),
        "",
        "### Rule-Engine Confusion Matrix",
        "",
        "| | Predicted Spam | Predicted Legitimate |",
        "|---|---:|---:|",
        (
            f"| Actual Spam | "
            f"{rule_metrics['true_positive']} | "
            f"{rule_metrics['false_negative']} |"
        ),
        (
            f"| Actual Legitimate | "
            f"{rule_metrics['false_positive']} | "
            f"{rule_metrics['true_negative']} |"
        ),
        "",
    ]

    if llm_metrics:
        lines.extend(
            [
                "## Gemini LLM Balanced-Sample Evaluation",
                "",
                "| Metric | Result |",
                "|---|---:|",
                (
                    f"| Requested messages | "
                    f"{llm_metrics['requested_messages']} |"
                ),
                (
                    f"| Successful evaluations | "
                    f"{llm_metrics['completed_requests']} |"
                ),
                (
                    f"| Failed evaluations | "
                    f"{llm_metrics['failed_requests']} |"
                ),
                (
                    f"| Accuracy | "
                    f"{percentage(llm_metrics['accuracy'])} |"
                ),
                (
                    f"| Precision | "
                    f"{percentage(llm_metrics['precision'])} |"
                ),
                (
                    f"| Recall | "
                    f"{percentage(llm_metrics['recall'])} |"
                ),
                (
                    f"| Specificity | "
                    f"{percentage(llm_metrics['specificity'])} |"
                ),
                (
                    f"| F1 score | "
                    f"{percentage(llm_metrics['f1_score'])} |"
                ),
                (
                    f"| Average latency | "
                    f"{llm_metrics['average_latency_ms']} ms |"
                ),
                "",
                "### Gemini Confusion Matrix",
                "",
                "| | Predicted Spam | Predicted Legitimate |",
                "|---|---:|---:|",
                (
                    f"| Actual Spam | "
                    f"{llm_metrics['true_positive']} | "
                    f"{llm_metrics['false_negative']} |"
                ),
                (
                    f"| Actual Legitimate | "
                    f"{llm_metrics['false_positive']} | "
                    f"{llm_metrics['true_negative']} |"
                ),
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            (
                "The deterministic rule engine is specialised for "
                "high-risk social-engineering patterns such as digital "
                "arrest, authority impersonation, credential theft and "
                "payment coercion. Generic promotional spam may therefore "
                "produce lower rule-engine recall."
            ),
            "",
            (
                "Gemini is evaluated on a smaller balanced sample because "
                "each prediction requires an external API call. Saved "
                "predictions are reused so repeated runs do not consume "
                "unnecessary quota."
            ),
            "",
            "## Limitations",
            "",
            (
                "- SMS spam classification is not identical to complete "
                "financial-fraud detection."
            ),
            (
                "- The dataset does not contain transaction, device, "
                "location or banking context."
            ),
            (
                "- Gemini sample metrics depend on the selected random "
                "sample and available API quota."
            ),
            (
                "- Final production decisions should retain human review "
                "for high-impact actions."
            ),
            "",
            "## Attribution",
            "",
            (
                "Almeida, T. and Hidalgo, J. SMS Spam Collection. "
                "UCI Machine Learning Repository. "
                "DOI: 10.24432/C5CC84."
            ),
            "",
        ]
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--rule-threshold",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--llm-per-class",
        type=int,
        default=10,
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.5,
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=42,
    )

    parser.add_argument(
        "--skip-llm",
        action="store_true",
    )

    arguments = parser.parse_args()

    RESULTS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    records = load_dataset()

    spam_count = sum(
        1
        for record in records
        if record["label"] == "spam"
    )

    ham_count = (
        len(records)
        - spam_count
    )

    rule_metrics = evaluate_rule_engine(
        records,
        arguments.rule_threshold,
    )

    results = {
        "generated_at": (
            datetime.now()
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        ),
        "dataset": {
            "name": "UCI SMS Spam Collection",
            "total_messages": len(
                records
            ),
            "spam_messages": spam_count,
            "ham_messages": ham_count,
            "license": "CC BY 4.0",
            "doi": "10.24432/C5CC84",
        },
        "rule_engine": rule_metrics,
    }

    if not arguments.skip_llm:
        llm_metrics = evaluate_llm(
            records=records,
            per_class=arguments.llm_per_class,
            delay_seconds=arguments.delay,
            seed=arguments.seed,
        )

        results["gemini_llm"] = (
            llm_metrics
        )

    METRICS_PATH.write_text(
        json.dumps(
            results,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    create_markdown_report(
        results
    )

    print()
    print("=" * 70)
    print("EVALUATION COMPLETED")
    print("=" * 70)

    print()
    print("Rule Engine")
    print(
        f"Accuracy: "
        f"{percentage(rule_metrics['accuracy'])}"
    )
    print(
        f"Precision: "
        f"{percentage(rule_metrics['precision'])}"
    )
    print(
        f"Recall: "
        f"{percentage(rule_metrics['recall'])}"
    )
    print(
        f"F1 score: "
        f"{percentage(rule_metrics['f1_score'])}"
    )

    if "gemini_llm" in results:
        llm_metrics = results[
            "gemini_llm"
        ]

        print()
        print("Gemini LLM")
        print(
            f"Accuracy: "
            f"{percentage(llm_metrics['accuracy'])}"
        )
        print(
            f"Precision: "
            f"{percentage(llm_metrics['precision'])}"
        )
        print(
            f"Recall: "
            f"{percentage(llm_metrics['recall'])}"
        )
        print(
            f"F1 score: "
            f"{percentage(llm_metrics['f1_score'])}"
        )

    print()
    print(f"Metrics saved to: {METRICS_PATH}")
    print(f"Report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    main()