#!/usr/bin/env python3
"""
Task Examples

This example demonstrates task operations:
- Create basic tasks
- Create tasks with assignees
- Create tasks with due dates
- Create tasks with external IDs (e.g., for JIRA integration)
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
        print("Error: No member IDs configured")
        sys.exit(1)

    print("=" * 60)
    print("Task Examples")
    print("=" * 60)

    # Create a topic for tasks
    print("\n1. Creating topic for task examples...")
    response = client.create_topic(
        name=f"Task Demo {int(time.time())}",
        members=member_ids[:2] if len(member_ids) > 1 else member_ids
    )

    if not response.success:
        print(f"   Error creating topic: {response.data}")
        sys.exit(1)

    topic_id = response.data["id"]
    print(f"   Topic created: {topic_id[:8]}...")

    # Create a basic task
    print("\n2. Creating basic task...")
    response = client.create_task(
        topic_id=topic_id,
        title="Review API documentation"
    )

    if response.success:
        print(f"   Task created! ID: {response.data.get('id')}")
        print(f"   Title: {response.data.get('title')}")
    else:
        print(f"   Error: {response.data}")

    # Create task with description and assignee
    print("\n3. Creating task with assignee...")
    response = client.create_task(
        topic_id=topic_id,
        title="Implement error handling",
        description="Add proper error handling and retry logic for API calls. "
                    "Include exponential backoff for rate limiting.",
        assignee=member_ids[0]
    )

    if response.success:
        print(f"   Task created! ID: {response.data.get('id')}")
        print(f"   Assigned to: {member_ids[0][:8]}...")
    else:
        print(f"   Error: {response.data}")

    # Create task with due date
    print("\n4. Creating task with due date...")
    # Due date: 7 days from now (in milliseconds)
    due_date_ms = int((time.time() + 7 * 24 * 60 * 60) * 1000)

    response = client.create_task(
        topic_id=topic_id,
        title="Complete integration testing",
        description="Run full test suite against the API",
        due_date=due_date_ms
    )

    if response.success:
        print(f"   Task created! ID: {response.data.get('id')}")
        print(f"   Due date set to 7 days from now")
    else:
        print(f"   Error: {response.data}")

    # Create task with external ID (JIRA-style)
    print("\n5. Creating task with external ID (JIRA integration example)...")
    external_task_id = f"PROJ-{int(time.time()) % 10000}"

    response = client.create_task(
        topic_id=topic_id,
        title="Deploy to production",
        description="Deploy the latest version to production environment. "
                    "Ensure all tests pass before deployment.",
        assignee=member_ids[0],
        due_date=int((time.time() + 3 * 24 * 60 * 60) * 1000),  # 3 days from now
        external_id=external_task_id
    )

    if response.success:
        print(f"   Task created! ID: {response.data.get('id')}")
        print(f"   External ID: {external_task_id}")
        print(f"   (Use this to link back to your JIRA/project management tool)")
    else:
        print(f"   Error: {response.data}")

    # Create an urgent task
    print("\n6. Creating urgent task (due tomorrow)...")
    tomorrow_ms = int((time.time() + 24 * 60 * 60) * 1000)

    response = client.create_task(
        topic_id=topic_id,
        title="URGENT: Fix critical bug",
        description="High priority bug fix needed before release",
        assignee=member_ids[0],
        due_date=tomorrow_ms
    )

    if response.success:
        print(f"   Task created! ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.data}")

    print("\n" + "=" * 60)
    print("Task examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
