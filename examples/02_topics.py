#!/usr/bin/env python3
"""
Topic Management Examples

This example demonstrates topic (channel/group chat) operations:
- Create topics with and without external IDs
- List topics
- Get topic by ID
- Get topic by external ID
- Update topic name/description
- Add and remove members
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
    print("Topic Management Examples")
    print("=" * 60)

    # Create a topic without external ID
    print("\n1. Creating topic without external ID...")
    response = client.create_topic(
        name=f"Regular Topic {int(time.time())}",
        members=member_ids[:1],
        description="A regular topic without external ID"
    )

    if response.success:
        regular_topic_id = response.data["id"]
        print(f"   Created topic: {regular_topic_id}")
    else:
        print(f"   Error: {response.data}")
        sys.exit(1)

    # Create a topic with external ID
    print("\n2. Creating topic with external ID...")
    external_id = f"project-{int(time.time())}"

    response = client.create_topic(
        name="Project Updates Channel",
        members=member_ids[:1],
        description="Updates for our project integration",
        external_id=external_id
    )

    if response.success:
        topic_id = response.data["id"]
        full_external_id = response.data.get("externalId", external_id)
        print(f"   Created topic: {topic_id}")
        print(f"   External ID: {full_external_id}")
    else:
        print(f"   Error: {response.data}")
        sys.exit(1)

    # List all topics
    print("\n3. Listing topics...")
    response = client.list_topics(limit=10)

    if response.success:
        topics = response.data.get("topics", [])
        print(f"   Found {len(topics)} topics")
        for topic in topics[:5]:  # Show first 5
            print(f"   - {topic.get('name')} (ID: {topic.get('id')[:8]}...)")
    else:
        print(f"   Error: {response.data}")

    # Get topic by ID
    print("\n4. Getting topic by ID...")
    response = client.get_topic(topic_id)

    if response.success:
        print(f"   Name: {response.data.get('name')}")
        print(f"   Description: {response.data.get('description')}")
        members = response.data.get("members", [])
        print(f"   Members: {members}")
    else:
        print(f"   Error: {response.data}")

    # Get topic by external ID
    print("\n5. Getting topic by external ID...")
    response = client.get_topic_by_external_id(external_id)

    if response.success:
        print(f"   Found topic: {response.data.get('name')}")
        print(f"   Topic ID: {response.data.get('id')}")
    else:
        print(f"   Status: {response.status} (expected if external ID format differs)")

    # Try with full external ID if we have it
    if full_external_id != external_id:
        print(f"\n   Trying with full external ID: {full_external_id}")
        response = client.get_topic_by_external_id(full_external_id)
        if response.success:
            print(f"   Found topic: {response.data.get('name')}")

    # Update topic
    print("\n6. Updating topic...")
    new_name = f"Updated Topic Name {int(time.time())}"
    response = client.update_topic(
        topic_id=topic_id,
        name=new_name,
        description="Updated description via API"
    )

    if response.success:
        print(f"   Topic updated successfully")
        print(f"   New name: {new_name}")
    else:
        print(f"   Error: {response.data}")

    # Add member to topic
    if len(member_ids) > 1:
        print("\n7. Adding member to topic...")
        response = client.add_topic_members(topic_id, [member_ids[1]])

        if response.success:
            print(f"   Member added successfully")
        else:
            print(f"   Error: {response.data}")

        # Remove member from topic
        print("\n8. Removing member from topic...")
        response = client.remove_topic_members(topic_id, [member_ids[1]])

        if response.success:
            print(f"   Member removed successfully")
        else:
            print(f"   Error: {response.data}")

    print("\n" + "=" * 60)
    print("Topic examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
