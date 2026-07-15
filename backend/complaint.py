from datetime import datetime
from typing import Any


def get_text(
    value: Any,
    default: str = "Not available",
):
    if value is None:
        return default

    text = str(value).strip()

    if not text:
        return default

    return text


def get_list(value: Any):
    if not isinstance(value, list):
        return []

    result = []

    for item in value:
        text = get_text(item)

        if text != "Not available":
            result.append(text)

    return result


def build_complaint_data(
    report: dict[str, Any],
):
    scam_analysis = report.get(
        "scam_analysis",
        {},
    )

    transaction_analysis = report.get(
        "transaction_analysis",
        {},
    )

    alert_information = report.get(
        "n8n_alert_status",
        {},
    )

    detected_patterns = get_list(
        scam_analysis.get(
            "detected_patterns",
            [],
        )
    )

    transaction_risk_factors = get_list(
        transaction_analysis.get(
            "risk_factors",
            [],
        )
    )

    recommended_next_steps = get_list(
        report.get(
            "recommended_next_steps",
            [],
        )
    )

    case_id = get_text(
        report.get("case_id"),
        "UNKNOWN",
    )

    complaint_reference = (
        f"CYBER-{case_id}"
    )

    generated_at = (
        datetime.now()
        .astimezone()
        .isoformat(timespec="seconds")
    )

    return {
        "complaint_reference": complaint_reference,
        "generated_at": generated_at,
        "case_information": {
            "case_id": case_id,
            "case_created_at": get_text(
                report.get("created_at")
            ),
            "victim_id": get_text(
                report.get("victim_id")
            ),
            "final_risk_score": report.get(
                "final_risk_score",
                0,
            ),
            "final_risk_level": get_text(
                report.get(
                    "final_risk_level"
                )
            ),
            "priority": get_text(
                report.get("priority")
            ),
        },
        "scam_assessment": {
            "channel": get_text(
                scam_analysis.get("channel")
            ),
            "risk_score": scam_analysis.get(
                "risk_score",
                0,
            ),
            "risk_level": get_text(
                scam_analysis.get(
                    "risk_level"
                )
            ),
            "verdict": get_text(
                scam_analysis.get("verdict")
            ),
            "detected_patterns": (
                detected_patterns
            ),
        },
        "transaction_assessment": {
            "user_id": get_text(
                transaction_analysis.get(
                    "user_id"
                )
            ),
            "risk_score": (
                transaction_analysis.get(
                    "risk_score",
                    0,
                )
            ),
            "risk_level": get_text(
                transaction_analysis.get(
                    "risk_level"
                )
            ),
            "decision": get_text(
                transaction_analysis.get(
                    "decision"
                )
            ),
            "risk_factors": (
                transaction_risk_factors
            ),
        },
        "investigation_summary": get_text(
            report.get(
                "investigation_summary"
            )
        ),
        "recommended_next_steps": (
            recommended_next_steps
        ),
        "automated_alert": {
            "status": get_text(
                alert_information.get(
                    "status"
                )
            ),
            "status_code": (
                alert_information.get(
                    "status_code"
                )
            ),
            "message": get_text(
                alert_information.get(
                    "message"
                )
            ),
        },
        "suggested_evidence": [
            "Screenshot of the suspicious message",
            "Sender phone number, username, email, or profile link",
            "Call logs and call recordings, if legally available",
            "Bank transaction reference number",
            "UPI ID or beneficiary account details",
            "Transaction receipt or bank statement",
            "Device, IP address, location, and login records",
            "Timeline of communication with the suspected fraudster",
        ],
        "safety_note": (
            "Do not include OTP, UPI PIN, card PIN, "
            "banking password, complete Aadhaar number, "
            "or other secret authentication information "
            "in the complaint."
        ),
        "disclaimer": (
            "This package was generated automatically "
            "by SurakshaNet AI as an investigation-support "
            "document. The information must be reviewed "
            "and verified before submission to a bank, "
            "cybercrime authority, police station, or "
            "other official organization."
        ),
    }


def build_complaint_text(
    report: dict[str, Any],
):
    complaint = build_complaint_data(
        report
    )

    case_information = complaint[
        "case_information"
    ]

    scam_assessment = complaint[
        "scam_assessment"
    ]

    transaction_assessment = complaint[
        "transaction_assessment"
    ]

    alert_information = complaint[
        "automated_alert"
    ]

    detected_patterns = (
        scam_assessment[
            "detected_patterns"
        ]
    )

    risk_factors = (
        transaction_assessment[
            "risk_factors"
        ]
    )

    recommended_steps = complaint[
        "recommended_next_steps"
    ]

    evidence_items = complaint[
        "suggested_evidence"
    ]

    detected_patterns_text = "\n".join(
        f"- {pattern}"
        for pattern in detected_patterns
    )

    if not detected_patterns_text:
        detected_patterns_text = (
            "- No detected patterns recorded"
        )

    risk_factors_text = "\n".join(
        f"- {factor}"
        for factor in risk_factors
    )

    if not risk_factors_text:
        risk_factors_text = (
            "- No transaction risk factors recorded"
        )

    recommended_steps_text = "\n".join(
        f"- {step}"
        for step in recommended_steps
    )

    if not recommended_steps_text:
        recommended_steps_text = (
            "- Review and verify the available evidence"
        )

    evidence_text = "\n".join(
        f"- {item}"
        for item in evidence_items
    )

    alert_status_code = get_text(
        alert_information.get(
            "status_code"
        )
    )

    return f"""
SURAKSHANET AI
CYBERCRIME COMPLAINT SUPPORT PACKAGE

Complaint Reference:
{complaint["complaint_reference"]}

Generated At:
{complaint["generated_at"]}

==================================================
1. CASE INFORMATION
==================================================

Case ID:
{case_information["case_id"]}

Case Created At:
{case_information["case_created_at"]}

Victim ID:
{case_information["victim_id"]}

Final Risk Score:
{case_information["final_risk_score"]}/100

Final Risk Level:
{case_information["final_risk_level"]}

Priority:
{case_information["priority"]}

==================================================
2. SCAM MESSAGE ASSESSMENT
==================================================

Communication Channel:
{scam_assessment["channel"]}

Scam Risk Score:
{scam_assessment["risk_score"]}/100

Scam Risk Level:
{scam_assessment["risk_level"]}

Scam Verdict:
{scam_assessment["verdict"]}

Detected Scam Patterns:
{detected_patterns_text}

==================================================
3. TRANSACTION ASSESSMENT
==================================================

User ID:
{transaction_assessment["user_id"]}

Transaction Risk Score:
{transaction_assessment["risk_score"]}/100

Transaction Risk Level:
{transaction_assessment["risk_level"]}

Transaction Decision:
{transaction_assessment["decision"]}

Transaction Risk Factors:
{risk_factors_text}

==================================================
4. INVESTIGATION SUMMARY
==================================================

{complaint["investigation_summary"]}

==================================================
5. RECOMMENDED NEXT STEPS
==================================================

{recommended_steps_text}

==================================================
6. AUTOMATED ALERT INFORMATION
==================================================

Alert Status:
{alert_information["status"]}

Alert Status Code:
{alert_status_code}

Alert Message:
{alert_information["message"]}

==================================================
7. EVIDENCE TO ATTACH
==================================================

{evidence_text}

==================================================
8. SAFETY NOTE
==================================================

{complaint["safety_note"]}

==================================================
9. DISCLAIMER
==================================================

{complaint["disclaimer"]}
""".strip()