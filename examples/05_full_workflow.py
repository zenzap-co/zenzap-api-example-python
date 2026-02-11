#!/usr/bin/env python3
"""
Full Workflow Example

This example demonstrates a complete integration workflow:
1. Get bot info and verify credentials
2. Create a project channel with external ID
3. Send an announcement message
4. Create multiple tasks for the team
5. Add more team members
6. Send status update

This simulates how you might integrate Zenzap into your project management workflow.
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
    print("Full Workflow Example - Project Integration")
    print("=" * 60)

    # Step 1: Verify credentials
    print("\nStep 1: Verifying API credentials...")
    response = client.get_current_member()

    if not response.success:
        print(f"   Authentication failed: {response.data}")
        sys.exit(1)

    bot_name = response.data.get("name", "Bot")
    print(f"   Authenticated as: {bot_name}")

    # Step 2: Create project channel
    print("\nStep 2: Creating project channel...")
    project_id = f"project-{int(time.time())}"

    response = client.create_topic(
        name="Q1 2024 Product Launch",
        members=member_ids[:2] if len(member_ids) > 1 else member_ids,
        description="Coordination channel for the Q1 product launch. "
                    "All launch-related discussions, tasks, and updates here.",
        external_id=project_id
    )

    if not response.success:
        print(f"   Error: {response.data}")
        sys.exit(1)

    topic_id = response.data["id"]
    full_external_id = response.data.get("externalId", project_id)
    print(f"   Channel created: {response.data.get('name')}")
    print(f"   Topic ID: {topic_id}")
    print(f"   External ID: {full_external_id}")

    # Step 3: Send welcome announcement
    print("\nStep 3: Sending welcome announcement...")
    welcome_message = f"""Welcome to the Q1 2024 Product Launch channel!

This channel was automatically created by {bot_name} to coordinate our product launch.

What to expect:
- Task assignments will be posted here
- Daily status updates
- Important announcements
- Discussion thread for blockers

Let's make this launch a success!"""

    response = client.send_message(topic_id=topic_id, text=welcome_message)

    if response.success:
        print(f"   Announcement sent!")
    else:
        print(f"   Error: {response.data}")

    # Step 4: Create project tasks
    print("\nStep 4: Creating project tasks...")

    tasks = [
        {
            "title": "Finalize marketing materials",
            "description": "Review and approve all marketing collateral for the launch",
            "days_until_due": 7,
            "external_id": f"{project_id}-TASK-001"
        },
        {
            "title": "Complete QA testing",
            "description": "Run full regression test suite and fix any critical bugs",
            "days_until_due": 5,
            "external_id": f"{project_id}-TASK-002"
        },
        {
            "title": "Prepare launch announcement",
            "description": "Draft and review the public launch announcement",
            "days_until_due": 10,
            "external_id": f"{project_id}-TASK-003"
        },
        {
            "title": "Update documentation",
            "description": "Ensure all user documentation reflects new features",
            "days_until_due": 6,
            "external_id": f"{project_id}-TASK-004"
        },
    ]

    created_tasks = []
    for i, task in enumerate(tasks):
        due_date = int((time.time() + task["days_until_due"] * 24 * 60 * 60) * 1000)
        assignee = member_ids[i % len(member_ids)]

        response = client.create_task(
            topic_id=topic_id,
            title=task["title"],
            description=task["description"],
            assignee=assignee,
            due_date=due_date,
            external_id=task["external_id"]
        )

        if response.success:
            created_tasks.append(response.data)
            print(f"   Created: {task['title']}")
            print(f"      - Assigned to: {assignee[:8]}...")
            print(f"      - Due in {task['days_until_due']} days")
            print(f"      - External ID: {task['external_id']}")
        else:
            print(f"   Error creating task: {response.data}")

    # Step 5: Send task summary
    print("\nStep 5: Sending task summary...")
    task_summary = f"""Task Summary - {len(created_tasks)} tasks created

Here's what we need to accomplish:

"""
    for i, task in enumerate(tasks, 1):
        task_summary += f"{i}. {task['title']} (Due in {task['days_until_due']} days)\n"

    task_summary += "\nPlease check your assigned tasks and let me know if you have any questions!"

    response = client.send_message(topic_id=topic_id, text=task_summary)

    if response.success:
        print(f"   Task summary sent!")
    else:
        print(f"   Error: {response.data}")

    # Step 6: Demonstrate looking up by external ID
    print("\nStep 6: Verifying topic lookup by external ID...")
    response = client.get_topic_by_external_id(project_id)

    if response.success:
        print(f"   Found topic by external ID: {response.data.get('name')}")
    else:
        print(f"   Note: Try with full external ID format")
        response = client.get_topic_by_external_id(full_external_id)
        if response.success:
            print(f"   Found topic by full external ID: {response.data.get('name')}")

    # Summary
    print("\n" + "=" * 60)
    print("Workflow Complete!")
    print("=" * 60)
    print(f"""
Summary:
- Project Channel: {topic_id}
- External ID: {full_external_id}
- Tasks Created: {len(created_tasks)}
- Messages Sent: 2

You can now:
- Look up this channel using the external ID in your system
- Link tasks back using their external IDs
- Send automated updates when project status changes

Deep link to topic: https://app.zenzap.co?external_topic={full_external_id}
""")


if __name__ == "__main__":
    main()
