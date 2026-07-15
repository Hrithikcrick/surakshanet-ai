# SurakshaNet AI Evaluation Report

Generated: 2026-07-16T01:08:42+05:30

## Evaluation Scope

The UCI SMS Spam Collection is used to evaluate the message-classification layer. Transaction fraud scoring, n8n automation and Telegram delivery are outside this dataset benchmark.

## Dataset

- Total messages: 5574
- Spam messages: 747
- Legitimate messages: 4827
- Source: UCI Machine Learning Repository
- Dataset: SMS Spam Collection
- License: CC BY 4.0

## Deterministic Rule Engine

| Metric | Result |
|---|---:|
| Evaluated messages | 5574 |
| Accuracy | 86.60% |
| Precision | 0.00% |
| Recall | 0.00% |
| Specificity | 100.00% |
| F1 score | 0.00% |
| Average latency | 0.0281 ms |

### Rule-Engine Confusion Matrix

| | Predicted Spam | Predicted Legitimate |
|---|---:|---:|
| Actual Spam | 0 | 747 |
| Actual Legitimate | 0 | 4827 |

## Gemini LLM Balanced-Sample Evaluation

| Metric | Result |
|---|---:|
| Requested messages | 20 |
| Successful evaluations | 20 |
| Failed evaluations | 0 |
| Accuracy | 90.00% |
| Precision | 90.00% |
| Recall | 90.00% |
| Specificity | 90.00% |
| F1 score | 90.00% |
| Average latency | 4669.55 ms |

### Gemini Confusion Matrix

| | Predicted Spam | Predicted Legitimate |
|---|---:|---:|
| Actual Spam | 9 | 1 |
| Actual Legitimate | 1 | 9 |

## Interpretation

The deterministic rule engine is specialised for high-risk social-engineering patterns such as digital arrest, authority impersonation, credential theft and payment coercion. Generic promotional spam may therefore produce lower rule-engine recall.

Gemini is evaluated on a smaller balanced sample because each prediction requires an external API call. Saved predictions are reused so repeated runs do not consume unnecessary quota.

## Limitations

- SMS spam classification is not identical to complete financial-fraud detection.
- The dataset does not contain transaction, device, location or banking context.
- Gemini sample metrics depend on the selected random sample and available API quota.
- Final production decisions should retain human review for high-impact actions.

## Attribution

Almeida, T. and Hidalgo, J. SMS Spam Collection. UCI Machine Learning Repository. DOI: 10.24432/C5CC84.
