import os
import json
from dotenv import load_dotenv

load_dotenv()
TARGET_OWNER = os.environ.get("TARGET_OWNER", "Gitlawb")
TARGET_REPO = os.environ.get("TARGET_REPO", "openclaude")


def analyze_jsonl():
    filename = f"{TARGET_OWNER}_{TARGET_REPO}_detailed.jsonl"

    if not os.path.exists(filename):
        print(f"Error: The file '{filename}' does not exist yet.")
        print(
            "Make sure you have run the deep extractor script and it has started saving data."
        )
        return

    total_scraped = 0
    emails_found = 0
    emails_null = 0

    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            try:
                data = json.loads(line)
                total_scraped += 1

                if data.get("email"):
                    emails_found += 1
                else:
                    emails_null += 1
            except json.JSONDecodeError:
                pass

    print(f"\n--- Scraping Stats for {TARGET_OWNER}/{TARGET_REPO} ---")
    print(f"Total Stargazers Processed: {total_scraped}")
    print(f"Emails Successfully Found:  {emails_found}")
    print(f"Emails Null (Hidden):       {emails_null}")

    if total_scraped > 0:
        success_rate = (emails_found / total_scraped) * 100
        print(f"Overall Extraction Rate:    {success_rate:.2f}%")

    print("-" * 50 + "\n")


if __name__ == "__main__":
    analyze_jsonl()
