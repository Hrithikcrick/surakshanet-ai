import json
import sqlite3
from pathlib import Path
from typing import Any


DATABASE_PATH = Path(__file__).resolve().parent / "surakshanet.db"


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=10,
    )
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS fraud_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            case_id TEXT UNIQUE NOT NULL,
            victim_id TEXT NOT NULL,
            risk_score INTEGER NOT NULL,
            risk_level TEXT NOT NULL,
            priority TEXT NOT NULL,
            scam_verdict TEXT NOT NULL,
            transaction_decision TEXT NOT NULL,
            alert_status TEXT NOT NULL,
            created_at TEXT NOT NULL,
            report_json TEXT NOT NULL
        )
        """
    )

    connection.commit()
    connection.close()


def save_case(report: dict[str, Any]):
    scam_analysis = report.get("scam_analysis", {})
    transaction_analysis = report.get(
        "transaction_analysis",
        {},
    )
    alert_information = report.get(
        "n8n_alert_status",
        {},
    )

    connection = get_connection()

    connection.execute(
        """
        INSERT INTO fraud_cases (
            case_id,
            victim_id,
            risk_score,
            risk_level,
            priority,
            scam_verdict,
            transaction_decision,
            alert_status,
            created_at,
            report_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            report.get("case_id"),
            report.get("victim_id"),
            report.get("final_risk_score", 0),
            report.get("final_risk_level", "Unknown"),
            report.get("priority", "Unknown"),
            scam_analysis.get(
                "verdict",
                "Not available",
            ),
            transaction_analysis.get(
                "decision",
                "Not available",
            ),
            alert_information.get(
                "status",
                "not sent",
            ),
            report.get("created_at", ""),
            json.dumps(
                report,
                ensure_ascii=False,
            ),
        ),
    )

    connection.commit()
    connection.close()


def get_all_cases(limit: int = 100):
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT
            case_id,
            victim_id,
            risk_score,
            risk_level,
            priority,
            scam_verdict,
            transaction_decision,
            alert_status,
            created_at
        FROM fraud_cases
        ORDER BY id DESC
        LIMIT ?
        """,
        (limit,),
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def get_case_by_id(case_id: str):
    connection = get_connection()

    row = connection.execute(
        """
        SELECT report_json
        FROM fraud_cases
        WHERE case_id = ?
        """,
        (case_id,),
    ).fetchone()

    connection.close()

    if row is None:
        return None

    return json.loads(row["report_json"])


def get_dashboard_summary():
    connection = get_connection()

    total_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        """
    ).fetchone()["total"]

    critical_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        WHERE risk_level = 'Critical'
        """
    ).fetchone()["total"]

    high_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        WHERE risk_level = 'High'
        """
    ).fetchone()["total"]

    medium_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        WHERE risk_level = 'Medium'
        """
    ).fetchone()["total"]

    low_cases = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        WHERE risk_level = 'Low'
        """
    ).fetchone()["total"]

    alerts_sent = connection.execute(
        """
        SELECT COUNT(*) AS total
        FROM fraud_cases
        WHERE alert_status = 'sent'
        """
    ).fetchone()["total"]

    average_risk_score = connection.execute(
        """
        SELECT COALESCE(
            AVG(risk_score),
            0
        ) AS average_score
        FROM fraud_cases
        """
    ).fetchone()["average_score"]

    connection.close()

    return {
        "total_cases": total_cases,
        "critical_cases": critical_cases,
        "high_cases": high_cases,
        "medium_cases": medium_cases,
        "low_cases": low_cases,
        "alerts_sent": alerts_sent,
        "average_risk_score": round(
            average_risk_score,
            2,
        ),
    }


init_database()