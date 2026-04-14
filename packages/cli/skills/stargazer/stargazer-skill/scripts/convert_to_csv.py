import os
import json
import csv
from dotenv import load_dotenv

load_dotenv()
TARGET_OWNER = os.environ.get("TARGET_OWNER", "Gitlawb")
TARGET_REPO = os.environ.get("TARGET_REPO", "openclaude")


def convert_jsonl_to_csv():
    jsonl_filename = f"{TARGET_OWNER}_{TARGET_REPO}_detailed.jsonl"
    csv_filename = f"{TARGET_OWNER}_{TARGET_REPO}_detailed.csv"

    if not os.path.exists(jsonl_filename):
        print(f"Error: The file '{jsonl_filename}' does not exist.")
        return

    headers = [
        "login",
        "name",
        "email",
        "location",
        "company",
        "blog",
        "twitter",
        "followers",
        "public_repos",
        "profile_url",
        "email_found",
    ]

    total_converted = 0

    with (
        open(jsonl_filename, "r", encoding="utf-8") as infile,
        open(csv_filename, "w", encoding="utf-8-sig", newline="") as outfile,
    ):
        writer = csv.DictWriter(outfile, fieldnames=headers)
        writer.writeheader()

        for line in infile:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                row = {header: data.get(header, "") for header in headers}

                for k, v in row.items():
                    if v is None:
                        row[k] = ""

                writer.writerow(row)
                total_converted += 1
            except json.JSONDecodeError:
                pass

    print(f"\nSuccessfully converted {total_converted} records to CSV!")
    print(f"Saved as: {csv_filename}\n")


if __name__ == "__main__":
    convert_jsonl_to_csv()
