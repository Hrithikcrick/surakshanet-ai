import json
import os
import time
from pathlib import Path
from typing import Any, Literal

from dotenv import load_dotenv
from pydantic import BaseModel, Field


BACKEND_DIRECTORY = Path(__file__).resolve().parent

load_dotenv(
    BACKEND_DIRECTORY / ".env",
    override=False,
)

load_dotenv(
    BACKEND_DIRECTORY.parent / ".env",
    override=False,
)


class LLMFraudAnalysis(BaseModel):
    scam_type: str = Field(
        description=(
            "The most likely scam category, such as digital arrest, "
            "phishing, fake investment, job scam, loan scam, parcel "
            "scam, impersonation, credential theft, or legitimate."
        )
    )

    verdict: Literal[
        "legitimate",
        "suspicious",
        "likely_scam",
        "high_risk_scam",
    ] = Field(
        description="The final classification of the message."
    )

    risk_score: int = Field(
        ge=0,
        le=100,
        description="Fraud risk score between 0 and 100.",
    )

    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence in the classification between 0 and 1.",
    )

    reasoning_summary: str = Field(
        description=(
            "A short evidence-based explanation without private "
            "chain-of-thought."
        )
    )

    evidence: list[str] = Field(
        description=(
            "Short observable fraud indicators found in the message "
            "and transaction context."
        )
    )

    manipulation_tactics: list[str] = Field(
        description=(
            "Social-engineering techniques such as urgency, fear, "
            "authority impersonation, secrecy, or payment pressure."
        )
    )

    recommended_action: str = Field(
        description=(
            "A practical and safety-focused action for the user or "
            "fraud investigator."
        )
    )

    detected_language: str = Field(
        description="The primary language detected in the message."
    )


def llm_is_enabled():
    enabled_value = os.getenv(
        "LLM_ENABLED",
        "true",
    )

    return enabled_value.strip().lower() in {
        "true",
        "1",
        "yes",
        "on",
    }


def get_model_name():
    model = os.getenv(
        "GEMINI_MODEL",
        "gemini-2.5-flash",
    ).strip()

    if not model:
        return "gemini-2.5-flash"

    return model


def get_unavailable_result(
    reason: str,
    error_type: str | None = None,
    latency_ms: int = 0,
):
    return {
        "status": "unavailable",
        "provider": "google-gemini",
        "model": get_model_name(),
        "fallback_used": True,
        "reason": reason,
        "error_type": error_type,
        "latency_ms": latency_ms,
        "analysis": None,
    }


def build_analysis_input(
    message: str,
    channel: str,
    rule_analysis: dict[str, Any] | None,
    transaction_context: dict[str, Any] | None,
):
    return {
        "message": message,
        "communication_channel": channel,
        "rule_engine_analysis": rule_analysis or {},
        "transaction_context": transaction_context or {},
    }


def analyze_message_with_llm(
    message: str,
    channel: str = "message",
    rule_analysis: dict[str, Any] | None = None,
    transaction_context: dict[str, Any] | None = None,
):
    if not llm_is_enabled():
        return get_unavailable_result(
            "LLM analysis is disabled in environment settings"
        )

    api_key = os.getenv(
        "GEMINI_API_KEY",
        "",
    ).strip()

    if not api_key:
        return get_unavailable_result(
            "GEMINI_API_KEY is missing"
        )

    if not message or not message.strip():
        return get_unavailable_result(
            "The suspicious message is empty",
            "ValidationError",
        )

    try:
        from google import genai
        from google.genai import types
    except ImportError:
        return get_unavailable_result(
            "The google-genai Python package is not installed",
            "ImportError",
        )

    model = get_model_name()

    analysis_input = build_analysis_input(
        message=message,
        channel=channel,
        rule_analysis=rule_analysis,
        transaction_context=transaction_context,
    )

    system_prompt = """
You are the SurakshaNet AI fraud-analysis engine.

Your task is to classify suspicious communications and identify
fraud indicators.

Analyze the supplied message, communication channel, rule-engine
result, and transaction context.

Look for:

- Digital arrest scams
- Police, CBI, ED, RBI, court, customs, bank, or government impersonation
- Phishing and credential theft
- OTP, UPI PIN, card PIN, password, or banking-detail requests
- Fake investment or cryptocurrency opportunities
- Job and work-from-home scams
- Loan and advance-fee scams
- Parcel, customs, and delivery scams
- Remote-access or screen-sharing requests
- Urgent payment demands
- Threats of arrest, account suspension, or legal action
- Forced secrecy or isolation
- Social-engineering and emotional manipulation

Rules:

1. Use only the information supplied in the case.
2. Do not invent missing facts.
3. Return the required structured result.
4. Do not reveal private chain-of-thought.
5. Keep reasoning_summary short and evidence based.
6. Risk score must be between 0 and 100.
7. Confidence must be between 0 and 1.
8. Evidence must contain short observable indicators.
9. Treat arrest threats, authority impersonation, secrecy demands,
   credential requests, and verification payments as strong signals.
10. Recommended action must be practical and safety focused.
11. A message can be suspicious even when there is not enough evidence
    to classify it as a confirmed scam.
""".strip()

    user_prompt = (
        "Analyze the following SurakshaNet fraud case.\n\n"
        + json.dumps(
            analysis_input,
            ensure_ascii=False,
            indent=2,
        )
    )

    started_at = time.perf_counter()

    try:
        client = genai.Client(
            api_key=api_key
        )

        response = client.models.generate_content(
            model=model,
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.1,
                max_output_tokens=2048,
                response_mime_type="application/json",
                response_schema=LLMFraudAnalysis,
            ),
        )

        latency_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000
        )

        response_text = response.text

        if not response_text:
            raise RuntimeError(
                "Gemini returned an empty response"
            )

        parsed_result = (
            LLMFraudAnalysis.model_validate_json(
                response_text
            )
        )

        return {
            "status": "completed",
            "provider": "google-gemini",
            "model": model,
            "fallback_used": False,
            "reason": None,
            "error_type": None,
            "latency_ms": latency_ms,
            "analysis": parsed_result.model_dump(),
        }

    except Exception as error:
        latency_ms = round(
            (
                time.perf_counter()
                - started_at
            )
            * 1000
        )

        error_message = str(error).strip()

        if not error_message:
            error_message = (
                "Unknown Gemini analysis error"
            )

        return {
            "status": "failed",
            "provider": "google-gemini",
            "model": model,
            "fallback_used": True,
            "reason": error_message[:500],
            "error_type": type(error).__name__,
            "latency_ms": latency_ms,
            "analysis": None,
        }