import json

from llm_analyzer import (
    analyze_message_with_llm,
)


def run_test(
    test_name: str,
    message: str,
    channel: str,
    rule_analysis: dict,
    transaction_context: dict,
):
    print()
    print("=" * 70)
    print(test_name)
    print("=" * 70)

    result = analyze_message_with_llm(
        message=message,
        channel=channel,
        rule_analysis=rule_analysis,
        transaction_context=transaction_context,
    )

    print(
        json.dumps(
            result,
            ensure_ascii=False,
            indent=2,
        )
    )


def main():
    digital_arrest_message = """
This is CBI. Your Aadhaar has been linked to a money laundering
case. You are under digital arrest. Do not tell your family.
Join a video call immediately and transfer 50,000 rupees to the
verification account to avoid arrest.
""".strip()

    digital_arrest_rules = {
        "risk_score": 60,
        "risk_level": "Critical",
        "verdict": (
            "Possible digital arrest or fraud scam"
        ),
        "detected_patterns": [
            "CBI impersonation",
            "Digital arrest threat",
            "Money laundering accusation",
            "Secrecy pressure",
            "Suspicious video-call demand",
            "Payment pressure",
        ],
    }

    digital_arrest_transaction = {
        "amount": 50000,
        "average_amount": 5000,
        "location": "Mumbai",
        "usual_location": "Delhi",
        "known_device": False,
        "transaction_hour": 2,
        "merchant_category": "wire transfer",
        "failed_attempts": 4,
    }

    run_test(
        test_name="TEST 1: DIGITAL ARREST SCAM",
        message=digital_arrest_message,
        channel="telegram",
        rule_analysis=digital_arrest_rules,
        transaction_context=digital_arrest_transaction,
    )

    legitimate_message = """
Your electricity bill for this month is now available in the
official provider application. Please open the application
directly to review the bill. Do not share your OTP or password
with anyone.
""".strip()

    legitimate_rules = {
        "risk_score": 0,
        "risk_level": "Low",
        "verdict": (
            "No strong scam pattern detected"
        ),
        "detected_patterns": [],
    }

    legitimate_transaction = {
        "amount": 1200,
        "average_amount": 1100,
        "location": "Delhi",
        "usual_location": "Delhi",
        "known_device": True,
        "transaction_hour": 14,
        "merchant_category": "utility bill",
        "failed_attempts": 0,
    }

    run_test(
        test_name="TEST 2: POSSIBLY LEGITIMATE MESSAGE",
        message=legitimate_message,
        channel="sms",
        rule_analysis=legitimate_rules,
        transaction_context=legitimate_transaction,
    )


if __name__ == "__main__":
    main()