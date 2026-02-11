#!/usr/bin/env python3
"""
Quickstart Example - Basic Zenzap API Usage

This example demonstrates the fundamental operations:
1. Initialize the client
2. Get bot information
3. Create a topic
4. Send a message
5. Create a task

Before running, copy .env.example to .env and fill in your credentials.
"""

import os
import sys
import time

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from zenzap_client import ZenzapClient

# Load environment variables
load_dotenv()

def main():
    # Initialize the client
    client = ZenzapClient(
        api_key=os.environ["BOT_API_KEY"],
        secret=os.environ["BOT_SECRET"],
        base_url=os.getenv("API_BASE_URL", "https://api.zenzap.co")
    )

    # Get member IDs from environment
    member_ids = os.environ.get("MEMBER_IDS", "").split(",")
    member_ids = [m.strip() for m in member_ids if m.strip()]

    if not member_ids:
        print("Error: No member IDs configured. Set MEMBER_IDS in .env")
        sys.exit(1)

    print("=" * 60)
    print("Zenzap API Quickstart Example")
    print("=" * 60)

    # Step 1: Get bot information
    print("\n1. Getting bot information...")
    response = client.get_current_member()

    if response.success:
        print(f"   Bot ID: {response.data.get('id')}")
        print(f"   Name: {response.data.get('name')}")
        print(f"   Status: {response.data.get('status')}")
    else:
        print(f"   Error: {response.status} - {response.data}")
        sys.exit(1)

    # Step 2: Create a topic
    print("\n2. Creating a topic...")
    topic_name = f"Quickstart Demo {int(time.time())}"

    response = client.create_topic(
        name=topic_name,
        members=member_ids[:2],  # Use first 2 members
        description="Topic created by the quickstart example"
    )

    if response.success:
        topic_id = response.data.get("id")
        print(f"   Topic created!")
        print(f"   Topic ID: {topic_id}")
        print(f"   Name: {response.data.get('name')}")
    else:
        print(f"   Error: {response.status} - {response.data}")
        sys.exit(1)

    # Step 3: Send a message
    print("\n3. Sending a message...")
    response = client.send_message(
        topic_id=topic_id,
        text="Hello from the Zenzap API quickstart example!"
    )

    if response.success:
        print(f"   Message sent!")
        print(f"   Message ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.status} - {response.data}")

    # Step 4: Create a task
    print("\n4. Creating a task...")
    due_date = int((time.time() + 7 * 24 * 60 * 60) * 1000)  # 7 days from now in ms

    response = client.create_task(
        topic_id=topic_id,
        title="Review quickstart example",
        description="Check that the API integration is working correctly",
        assignee=member_ids[0],
        due_date=due_date
    )

    if response.success:
        print(f"   Task created!")
        print(f"   Task ID: {response.data.get('id')}")
        print(f"   Title: {response.data.get('title')}")
    else:
        print(f"   Error: {response.status} - {response.data}")

    print("\n" + "=" * 60)
    print("Quickstart complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
