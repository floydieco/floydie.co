"""
fetch_notion.py
Pulls all pages from the Floydie Content Dashboard Notion database
and writes a data.json file that the dashboard HTML reads.

Run locally:
  export NOTION_TOKEN=secret_xxx
  export NOTION_DATABASE_ID=1d109ddb2bdc4944a03f5c7a76829191
  python scripts/fetch_notion.py
"""

import json
import os
import requests
from datetime import datetime, timezone

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "1d109ddb2bdc4944a03f5c7a76829191")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def fetch_all_pages():
    pages = []
    url = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
    body = {"page_size": 100, "sorts": [{"property": "Date", "direction": "ascending"}]}

    while True:
        res = requests.post(url, headers=HEADERS, json=body)
        res.raise_for_status()
        data = res.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        body["start_cursor"] = data["next_cursor"]

    return pages


def extract(page):
    props = page.get("properties", {})

    def text(prop):
        items = props.get(prop, {}).get("title") or props.get(prop, {}).get("rich_text") or []
        return "".join(t.get("plain_text", "") for t in items).strip()

    def select(prop):
        s = props.get(prop, {}).get("select")
        return s["name"] if s else ""

    def date_start(prop):
        d = props.get(prop, {}).get("date")
        return d["start"] if d else ""

    return {
        "Post Title": text("Post Title"),
        "Status": select("Status"),
        "date:Date:start": date_start("Date"),
        "Angle": select("Angle"),
        "Format": select("Format"),
        "Keyword Trigger": select("Keyword Trigger") or "None",
        "Week": select("Week"),
        "Day": select("Day"),
    }


def main():
    print(f"Fetching from Notion database: {DATABASE_ID}")
    raw_pages = fetch_all_pages()
    posts = [extract(p) for p in raw_pages]
    print(f"  Fetched {len(posts)} posts")

    output = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "post_count": len(posts),
        "posts": posts,
    }

    out_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data.json")
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Written to {out_path}")


if __name__ == "__main__":
    main()
