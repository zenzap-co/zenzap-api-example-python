#!/usr/bin/env python3
"""Create a topic with a specific member."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
from zenzap_client import ZenzapClient

load_dotenv()


def main():
    client = ZenzapClient(
        api_key=os.environ["BOT_API_KEY"],
        secret=os.environ["BOT_SECRET"],
        base_url=os.getenv("API_BASE_URL", "https://api.zenzap.co")
    )

    member_ids = [m.strip() for m in os.environ.get("MEMBER_IDS", "").split(",") if m.strip()]
    if not member_ids:
        print("Error: No member IDs configured. Set MEMBER_IDS in .env")
        sys.exit(1)

    print("Creating topic...")
    response = client.create_topic(
        name="API Demo Topic",
        members=member_ids[:1]
    )

    if response.success:
        print(f"Topic created successfully!")
        print(f"Topic ID: {response.data['id']}")
        print(f"Topic data: {response.data}")
    else:
        print(f"Error: {response.data}")
        sys.exit(1)


if __name__ == "__main__":
    main()
