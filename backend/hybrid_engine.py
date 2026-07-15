from typing import Any


def clamp_score(value: Any):
    try:
        score = int(round(float(value)))
    except (TypeError, ValueError):
        score = 0

    return max(0, min(score, 100))


def get_risk_level(score: int):
    if score >= 75:
        return "Critical"

    if score >= 50:
        return "High"

    if score >= 25:
        return "Medium"

    return "Low"


def get_case_decision(risk_level: str):
    if risk_level == "Critical":
        return "Block or hold the transaction and escalate immediately"

    if risk_level == "High":
        return "Temporarily hold the transaction for manual review"

    if risk_level == "Medium":
        return "Require additional user verification"

    return "Continue monitoring and allow routine processing"


def get_score_agreement(
    rule_score: int,
    llm_score: int | None,
):
    if llm_score is None:
        return "not_available"

    difference = abs(rule_score - llm_score)

    if difference <= 15:
        return "strong"

    if difference <= 30:
        return "moderate"

    return "low"


def build_hybrid_assessment(
    rule_analysis: dict[str, Any],
    llm_result: dict[str, Any],
    transaction_analysis: dict[str, Any],
):
    rule_score = clamp_score(
        rule_analysis.get("risk_score", 0)
    )

    transaction_score = clamp_score(
        transaction_analysis.get("risk_score", 0)
    )

    llm_status = llm_result.get(
        "status",
        "unavailable",
    )

    llm_data = llm_result.get("analysis")

    llm_completed = (
        llm_status == "completed"
        and isinstance(llm_data, dict)
    )

    if llm_completed:
        llm_score = clamp_score(
            llm_data.get("risk_score", 0)
        )

        message_risk_score = round(
            rule_score * 0.40
            + llm_score * 0.60
        )

        final_risk_score = round(
            message_risk_score * 0.60
            + transaction_score * 0.40
        )

        confidence = llm_data.get(
            "confidence"
        )

        analysis_mode = "hybrid"

        score_weights = {
            "rule_engine": 0.24,
            "gemini_llm": 0.36,
            "transaction_engine": 0.40,
        }

        explanation = (
            "The final score combines deterministic scam rules, "
            "Gemini contextual analysis, and transaction-risk signals."
        )

    else:
        llm_score = None
        message_risk_score = rule_score

        final_risk_score = round(
            rule_score * 0.50
            + transaction_score * 0.50
        )

        confidence = None
        analysis_mode = "rule_fallback"

        score_weights = {
            "rule_engine": 0.50,
            "gemini_llm": 0.00,
            "transaction_engine": 0.50,
        }

        explanation = (
            "Gemini analysis was unavailable, so the platform safely "
            "used the deterministic scam and transaction engines."
        )

    final_risk_score = clamp_score(
        final_risk_score
    )

    message_risk_score = clamp_score(
        message_risk_score
    )

    final_risk_level = get_risk_level(
        final_risk_score
    )

    agreement = get_score_agreement(
        rule_score,
        llm_score,
    )

    return {
        "analysis_mode": analysis_mode,
        "fallback_used": not llm_completed,
        "rule_engine_score": rule_score,
        "llm_risk_score": llm_score,
        "message_risk_score": message_risk_score,
        "transaction_risk_score": transaction_score,
        "final_risk_score": final_risk_score,
        "final_risk_level": final_risk_level,
        "llm_confidence": confidence,
        "rule_llm_agreement": agreement,
        "score_weights": score_weights,
        "recommended_decision": get_case_decision(
            final_risk_level
        ),
        "explanation": explanation,
    }