import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


BACKEND_DIRECTORY = Path(__file__).resolve().parent
PROJECT_DIRECTORY = BACKEND_DIRECTORY.parent

load_dotenv(
    BACKEND_DIRECTORY / ".env",
    override=True,
)

load_dotenv(
    PROJECT_DIRECTORY / ".env",
    override=False,
)


DEFAULT_N8N_WEBHOOK_URL = (
    "http://localhost:5678/webhook/surakshanet-alert"
)

N8N_WEBHOOK_URL = (
    os.getenv(
        "N8N_WEBHOOK_URL",
        DEFAULT_N8N_WEBHOOK_URL,
    ).strip()
    or DEFAULT_N8N_WEBHOOK_URL
)


import requests
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel, Field

from complaint import (
    build_complaint_data,
    build_complaint_text,
)
from database import (
    get_all_cases,
    get_case_by_id,
    get_dashboard_summary,
    save_case,
)
from hybrid_engine import build_hybrid_assessment
from llm_analyzer import (
    analyze_message_with_llm,
    get_model_name,
    llm_is_enabled,
)


app = FastAPI(
    title="SurakshaNet AI",
    description=(
        "Hybrid LLM and deterministic "
        "fraud-intelligence platform"
    ),
    version="2.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScamInput(BaseModel):
    text: str
    channel: str = "message"


class TransactionInput(BaseModel):
    user_id: str
    amount: float = Field(ge=0)
    average_amount: float = Field(ge=0)
    location: str
    usual_location: str
    device_id: str
    known_device: bool

    transaction_hour: int = Field(
        ge=0,
        le=23,
    )

    merchant_category: str
    failed_attempts: int = Field(ge=0)

    recent_scam_risk: int = Field(
        ge=0,
        le=100,
    )


class CaseReportInput(BaseModel):
    victim_id: str
    scam_text: str
    channel: str = "message"
    transaction: TransactionInput


def contains_word(
    text: str,
    word: str,
):
    pattern = rf"\b{re.escape(word)}\b"

    return (
        re.search(
            pattern,
            text,
            re.IGNORECASE,
        )
        is not None
    )


def get_risk_level(score: int):
    if score >= 75:
        return "Critical"

    if score >= 50:
        return "High"

    if score >= 25:
        return "Medium"

    return "Low"


def analyze_scam_message(
    text: str,
    channel: str,
):
    message = text.lower().strip()

    score = 0
    detected_patterns = []

    def add_pattern(
        pattern_name: str,
        points: int,
    ):
        nonlocal score

        if pattern_name not in detected_patterns:
            detected_patterns.append(
                pattern_name
            )

            score += points

    phrase_rules = [
        (
            [
                "digital arrest",
                "digitally arrested",
            ],
            "Digital arrest threat",
            15,
        ),
        (
            [
                "money laundering",
            ],
            "Money laundering accusation",
            10,
        ),
        (
            [
                "aadhaar",
            ],
            "Aadhaar-related threat",
            5,
        ),
        (
            [
                "video call",
            ],
            "Suspicious video-call demand",
            5,
        ),
        (
            [
                "transfer money",
                "send money",
                "deposit money",
            ],
            "Payment pressure",
            10,
        ),
        (
            [
                "immediately",
                "urgent",
                "within 10 minutes",
                "within one hour",
            ],
            "Urgency pressure",
            5,
        ),
        (
            [
                "verification",
                "verification account",
            ],
            "Fake verification request",
            5,
        ),
        (
            [
                "share otp",
                "send otp",
                "tell me the otp",
            ],
            "OTP request",
            15,
        ),
        (
            [
                "upi pin",
                "card pin",
                "bank password",
            ],
            "Banking credential request",
            20,
        ),
        (
            [
                "do not tell anyone",
                "do not tell your family",
                "keep this confidential",
            ],
            "Secrecy pressure",
            8,
        ),
        (
            [
                "you will be arrested",
                "avoid arrest",
                "legal action",
                "freeze your account",
            ],
            "Legal or account threat",
            10,
        ),
        (
            [
                "screen sharing",
                "remote access",
                "anydesk",
                "teamviewer",
            ],
            "Remote-access request",
            15,
        ),
        (
            [
                "guaranteed profit",
                "double your money",
                "investment opportunity",
            ],
            "Suspicious investment promise",
            12,
        ),
    ]

    for phrases, label, points in phrase_rules:
        matched = any(
            phrase in message
            for phrase in phrases
        )

        if matched:
            add_pattern(
                label,
                points,
            )

    authority_rules = [
        (
            "cbi",
            "CBI impersonation",
            5,
        ),
        (
            "ed",
            "ED impersonation",
            5,
        ),
        (
            "police",
            "Police impersonation",
            5,
        ),
        (
            "rbi",
            "RBI impersonation",
            5,
        ),
        (
            "court",
            "Court impersonation",
            5,
        ),
        (
            "customs",
            "Customs impersonation",
            5,
        ),
        (
            "bank",
            "Bank impersonation",
            5,
        ),
    ]

    for word, label, points in authority_rules:
        if contains_word(
            message,
            word,
        ):
            add_pattern(
                label,
                points,
            )

    score = min(
        score,
        100,
    )

    if score >= 60:
        risk_level = "Critical"

        verdict = (
            "Possible digital arrest "
            "or fraud scam"
        )

        recommended_actions = [
            "Do not transfer money",
            "Do not share OTP, PIN, or banking details",
            "Stop communication with the suspicious sender",
            "Preserve screenshots and call details",
            "Report the incident to cybercrime authorities",
        ]

    elif score >= 40:
        risk_level = "High"

        verdict = (
            "Highly suspicious fraud message"
        )

        recommended_actions = [
            "Do not make any payment",
            "Verify the sender through an official channel",
            "Preserve all available evidence",
            "Report the sender if communication continues",
        ]

    elif score >= 20:
        risk_level = "Medium"

        verdict = (
            "Potential scam indicators detected"
        )

        recommended_actions = [
            "Do not share sensitive information",
            "Verify the request independently",
            "Avoid clicking unknown links",
        ]

    else:
        risk_level = "Low"

        verdict = (
            "No strong scam pattern detected"
        )

        recommended_actions = [
            "Remain cautious",
            "Verify unexpected requests",
            "Never share OTP, PIN, or passwords",
        ]

    return {
        "engine": "deterministic-rule-engine",
        "channel": channel,
        "risk_score": score,
        "risk_level": risk_level,
        "detected_patterns": detected_patterns,
        "verdict": verdict,
        "recommended_action": (
            recommended_actions
        ),
    }


def analyze_transaction_data(
    transaction: TransactionInput,
):
    score = 0
    risk_factors = []

    if transaction.average_amount > 0:
        amount_ratio = (
            transaction.amount
            / transaction.average_amount
        )

        if amount_ratio >= 5:
            score += 25

            risk_factors.append(
                "Transaction amount is at least "
                "five times the average"
            )

        elif amount_ratio >= 3:
            score += 18

            risk_factors.append(
                "Transaction amount is at least "
                "three times the average"
            )

        elif amount_ratio >= 2:
            score += 10

            risk_factors.append(
                "Transaction amount is at least "
                "twice the average"
            )

    elif transaction.amount > 0:
        score += 10

        risk_factors.append(
            "Average transaction amount "
            "is unavailable"
        )

    current_location = (
        transaction.location
        .strip()
        .lower()
    )

    usual_location = (
        transaction.usual_location
        .strip()
        .lower()
    )

    if current_location != usual_location:
        score += 15

        risk_factors.append(
            "Transaction location differs "
            "from the usual location"
        )

    if not transaction.known_device:
        score += 15

        risk_factors.append(
            "Transaction is from "
            "an unknown device"
        )

    if (
        transaction.transaction_hour <= 5
        or transaction.transaction_hour >= 23
    ):
        score += 10

        risk_factors.append(
            "Transaction occurred "
            "at an unusual time"
        )

    risky_merchant_categories = [
        "wire transfer",
        "money transfer",
        "crypto",
        "cryptocurrency",
        "gift card",
        "cash withdrawal",
        "international transfer",
    ]

    merchant_category = (
        transaction.merchant_category
        .strip()
        .lower()
    )

    if any(
        category in merchant_category
        for category
        in risky_merchant_categories
    ):
        score += 15

        risk_factors.append(
            "Merchant category has "
            "elevated fraud risk"
        )

    if transaction.failed_attempts >= 3:
        score += 10

        risk_factors.append(
            "Multiple failed transaction "
            "attempts detected"
        )

    elif transaction.failed_attempts > 0:
        score += 5

        risk_factors.append(
            "Failed transaction attempts detected"
        )

    if transaction.recent_scam_risk >= 60:
        score += 10

        risk_factors.append(
            "Recent high scam-risk "
            "signal detected"
        )

    elif transaction.recent_scam_risk >= 30:
        score += 5

        risk_factors.append(
            "Recent moderate scam-risk "
            "signal detected"
        )

    score = min(
        score,
        100,
    )

    risk_level = get_risk_level(
        score
    )

    if risk_level == "Critical":
        decision = (
            "Hold transaction and require "
            "manual verification"
        )

        recommended_actions = [
            "Freeze or hold the transaction",
            "Contact the user through a verified channel",
            "Perform device and location verification",
            "Escalate the transaction to the fraud team",
        ]

    elif risk_level == "High":
        decision = (
            "Temporarily hold transaction "
            "for additional verification"
        )

        recommended_actions = [
            "Ask the user to confirm the transaction",
            "Perform additional authentication",
            "Notify the fraud monitoring team",
        ]

    elif risk_level == "Medium":
        decision = (
            "Require additional verification"
        )

        recommended_actions = [
            "Ask the user for confirmation",
            "Continue monitoring",
            "Store the transaction risk record",
        ]

    else:
        decision = "Allow transaction"

        recommended_actions = [
            "Continue monitoring",
            "Store the transaction risk record",
        ]

    return {
        "engine": "transaction-risk-engine",
        "user_id": transaction.user_id,
        "risk_score": score,
        "risk_level": risk_level,
        "risk_factors": risk_factors,
        "decision": decision,
        "recommended_action": (
            recommended_actions
        ),
    }


def create_case_report(
    data: CaseReportInput,
):
    rule_analysis = analyze_scam_message(
        data.scam_text,
        data.channel,
    )

    transaction_analysis = (
        analyze_transaction_data(
            data.transaction
        )
    )

    transaction_context = (
        data.transaction.model_dump()
    )

    llm_analysis = analyze_message_with_llm(
        message=data.scam_text,
        channel=data.channel,
        rule_analysis=rule_analysis,
        transaction_context=(
            transaction_context
        ),
    )

    hybrid_analysis = (
        build_hybrid_assessment(
            rule_analysis=rule_analysis,
            llm_result=llm_analysis,
            transaction_analysis=(
                transaction_analysis
            ),
        )
    )

    final_score = hybrid_analysis[
        "final_risk_score"
    ]

    final_risk_level = hybrid_analysis[
        "final_risk_level"
    ]

    if final_risk_level == "Critical":
        priority = (
            "Immediate action required"
        )

        next_steps = [
            "Freeze or hold the suspicious transaction if possible",
            "Contact the victim through a verified official channel",
            "Preserve messages, calls, account, device, and transaction evidence",
            "Generate the cybercrime complaint package",
            "Escalate the case to the fraud team or cybercrime authorities",
        ]

    elif final_risk_level == "High":
        priority = (
            "Urgent review required"
        )

        next_steps = [
            "Temporarily hold the transaction",
            "Contact the victim through a verified channel",
            "Preserve all available evidence",
            "Escalate the case to the fraud monitoring team",
        ]

    elif final_risk_level == "Medium":
        priority = (
            "Review recommended"
        )

        next_steps = [
            "Request additional verification",
            "Ask the user to confirm the transaction",
            "Store the case for future pattern analysis",
        ]

    else:
        priority = (
            "Routine monitoring"
        )

        next_steps = [
            "Continue monitoring",
            "Ask the user for confirmation when necessary",
            "Store the case for future pattern analysis",
        ]

    if (
        hybrid_analysis["analysis_mode"]
        == "hybrid"
    ):
        analysis_description = (
            "Gemini contextual analysis, "
            "deterministic message rules, and "
            "transaction-risk signals were combined."
        )

    else:
        analysis_description = (
            "Gemini was unavailable, so deterministic "
            "message and transaction-risk engines "
            "were used safely."
        )

    gemini_score = hybrid_analysis[
        "llm_risk_score"
    ]

    if gemini_score is None:
        gemini_score_text = "unavailable"
    else:
        gemini_score_text = (
            f"{gemini_score}/100"
        )

    investigation_summary = (
        f"{analysis_description} "
        f"The rule engine produced a message score of "
        f"{hybrid_analysis['rule_engine_score']}/100. "
        f"The Gemini score was {gemini_score_text}. "
        f"The transaction score was "
        f"{hybrid_analysis['transaction_risk_score']}/100. "
        f"The combined case score is {final_score}/100, "
        f"classified as {final_risk_level} risk."
    )

    return {
        "case_id": (
            f"CASE-"
            f"{uuid.uuid4().hex[:8].upper()}"
        ),
        "created_at": (
            datetime.now()
            .astimezone()
            .isoformat(
                timespec="seconds"
            )
        ),
        "victim_id": data.victim_id,
        "source_message": {
            "text": data.scam_text,
            "channel": data.channel,
        },
        "transaction_context": (
            transaction_context
        ),
        "final_risk_score": final_score,
        "final_risk_level": (
            final_risk_level
        ),
        "priority": priority,
        "scam_analysis": rule_analysis,
        "llm_analysis": llm_analysis,
        "hybrid_analysis": (
            hybrid_analysis
        ),
        "transaction_analysis": (
            transaction_analysis
        ),
        "investigation_summary": (
            investigation_summary
        ),
        "recommended_next_steps": (
            next_steps
        ),
    }


def send_report_to_n8n(
    report: dict[str, Any],
):
    try:
        response = requests.post(
            N8N_WEBHOOK_URL,
            json=report,
            timeout=(3.05, 20),
        )

        if (
            200
            <= response.status_code
            < 300
        ):
            return {
                "status": "sent",
                "status_code": (
                    response.status_code
                ),
                "message": (
                    "Alert accepted by "
                    "the n8n workflow"
                ),
            }

        return {
            "status": "failed",
            "status_code": (
                response.status_code
            ),
            "message": (
                response.text
                or "n8n returned an error"
            ),
        }

    except requests.RequestException as error:
        return {
            "status": "failed",
            "status_code": None,
            "message": str(error),
        }


@app.get("/")
def home():
    return {
        "project": "SurakshaNet AI",
        "version": "2.0.0",
        "status": "running",
        "analysis_engine": (
            "Hybrid Gemini and deterministic "
            "fraud intelligence"
        ),
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "database": "connected",
        "frontend_allowed": True,
        "llm_enabled": llm_is_enabled(),
        "llm_provider": "google-gemini",
        "llm_model": get_model_name(),
        "gemini_key_configured": bool(
            os.getenv(
                "GEMINI_API_KEY",
                "",
            ).strip()
        ),
        "n8n_webhook_configured": bool(
            N8N_WEBHOOK_URL
        ),
        "n8n_webhook_url": (
            N8N_WEBHOOK_URL
        ),
    }


@app.post("/analyze-scam")
def analyze_scam(
    data: ScamInput,
):
    return analyze_scam_message(
        data.text,
        data.channel,
    )


@app.post("/analyze-transaction")
def analyze_transaction(
    data: TransactionInput,
):
    return analyze_transaction_data(
        data
    )


@app.post("/generate-case-report")
def generate_case_report(
    data: CaseReportInput,
):
    return create_case_report(
        data
    )


@app.post(
    "/generate-case-report-with-alert"
)
def generate_case_report_with_alert(
    data: CaseReportInput,
):
    report = create_case_report(
        data
    )

    report["n8n_alert_status"] = (
        send_report_to_n8n(
            report
        )
    )

    save_case(
        report
    )

    return report


@app.get("/cases")
def list_cases(
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
):
    return {
        "cases": get_all_cases(
            limit
        ),
    }


@app.get("/cases/{case_id}")
def read_case(
    case_id: str,
):
    case = get_case_by_id(
        case_id
    )

    if case is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return case


@app.get("/dashboard-summary")
def dashboard_summary():
    return get_dashboard_summary()


@app.get("/complaints/{case_id}")
def get_complaint_package(
    case_id: str,
):
    report = get_case_by_id(
        case_id
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    return build_complaint_data(
        report
    )


@app.get(
    "/complaints/{case_id}/download"
)
def download_complaint_package(
    case_id: str,
):
    report = get_case_by_id(
        case_id
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Case not found",
        )

    complaint_text = (
        build_complaint_text(
            report
        )
    )

    safe_case_id = re.sub(
        r"[^A-Za-z0-9_-]",
        "",
        case_id,
    )

    if not safe_case_id:
        safe_case_id = "case"

    filename = (
        f"{safe_case_id}-"
        "cybercrime-complaint.txt"
    )

    return Response(
        content=complaint_text,
        media_type=(
            "text/plain; charset=utf-8"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; '
                f'filename="{filename}"'
            ),
        },
    )