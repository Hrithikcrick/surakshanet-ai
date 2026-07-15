import io
import json
import zipfile
from pathlib import Path

import requests


EVALUATION_DIRECTORY = Path(__file__).resolve().parent
DATA_DIRECTORY = EVALUATION_DIRECTORY / "data"

DATASET_URL = (
    "https://archive.ics.uci.edu/static/public/228/"
    "sms%2Bspam%2Bcollection.zip"
)

ZIP_PATH = DATA_DIRECTORY / "sms_spam_collection.zip"
JSONL_PATH = DATA_DIRECTORY / "sms_spam_collection.jsonl"


def download_dataset():
    DATA_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    print("Downloading the UCI SMS Spam Collection...")

    response = requests.get(
        DATASET_URL,
        timeout=60,
    )

    response.raise_for_status()

    ZIP_PATH.write_bytes(
        response.content
    )

    with zipfile.ZipFile(
        io.BytesIO(response.content)
    ) as archive:
        dataset_files = [
            name
            for name in archive.namelist()
            if Path(name).name == "SMSSpamCollection"
        ]

        if not dataset_files:
            raise RuntimeError(
                "SMSSpamCollection was not found inside the archive"
            )

        raw_content = archive.read(
            dataset_files[0]
        )

    dataset_text = raw_content.decode(
        "utf-8",
        errors="replace",
    )

    records = []
    spam_count = 0
    ham_count = 0

    for line_number, line in enumerate(
        dataset_text.splitlines(),
        start=1,
    ):
        line = line.strip()

        if not line:
            continue

        parts = line.split(
            "\t",
            1,
        )

        if len(parts) != 2:
            continue

        label = parts[0].strip().lower()
        message = parts[1].strip()

        if label not in {
            "spam",
            "ham",
        }:
            continue

        if not message:
            continue

        if label == "spam":
            spam_count += 1
        else:
            ham_count += 1

        records.append(
            {
                "id": line_number,
                "label": label,
                "text": message,
            }
        )

    with JSONL_PATH.open(
        "w",
        encoding="utf-8",
    ) as output_file:
        for record in records:
            output_file.write(
                json.dumps(
                    record,
                    ensure_ascii=False,
                )
                + "\n"
            )

    print()
    print("Dataset downloaded successfully")
    print(f"Total messages: {len(records)}")
    print(f"Spam messages: {spam_count}")
    print(f"Legitimate messages: {ham_count}")
    print(f"Saved to: {JSONL_PATH}")


if __name__ == "__main__":
    download_dataset()