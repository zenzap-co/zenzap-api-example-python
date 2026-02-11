#!/usr/bin/env python3
"""
Message Examples

This example demonstrates sending messages:
- Send basic text messages
- Send messages with special characters
- Send messages with unicode
- Send messages with external IDs for tracking
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
    print("Message Examples")
    print("=" * 60)

    # Create a topic for messaging
    print("\n1. Creating topic for message examples...")
    response = client.create_topic(
        name=f"Message Demo {int(time.time())}",
        members=member_ids[:1]
    )

    if not response.success:
        print(f"   Error creating topic: {response.data}")
        sys.exit(1)

    topic_id = response.data["id"]
    print(f"   Topic created: {topic_id[:8]}...")

    # Send basic message
    print("\n2. Sending basic text message...")
    response = client.send_message(
        topic_id=topic_id,
        text="Hello! This is a basic text message from the Zenzap API."
    )

    if response.success:
        print(f"   Message sent! ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.data}")

    # Send message with special characters
    print("\n3. Sending message with special characters...")
    response = client.send_message(
        topic_id=topic_id,
        text="Special chars: @mention #hashtag & ampersand < > \"quotes\" 'apostrophes'"
    )

    if response.success:
        print(f"   Message sent! ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.data}")

    # Send message with unicode/emojis
    print("\n4. Sending message with unicode...")
    response = client.send_message(
        topic_id=topic_id,
        text="Unicode test: Hello World!"
    )

    if response.success:
        print(f"   Message sent! ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.data}")

    # Send message with external ID for tracking
    print("\n5. Sending message with external ID...")
    external_msg_id = f"notification-{int(time.time())}"

    response = client.send_message(
        topic_id=topic_id,
        text="This message has an external ID for tracking in your system.",
        external_id=external_msg_id
    )

    if response.success:
        print(f"   Message sent! ID: {response.data.get('id')}")
        print(f"   External ID: {external_msg_id}")
    else:
        print(f"   Error: {response.data}")

    # Send a longer message
    print("\n6. Sending a longer formatted message...")
    long_message = """Project Status Update

Here's the current status of our integration:

- API Connection: Working
- Authentication: Verified
- Topics: Can create and manage
- Messages: Can send and track

Next steps:
1. Implement webhook handling
2. Add error retry logic
3. Create production deployment

Let me know if you have any questions!"""

    response = client.send_message(
        topic_id=topic_id,
        text=long_message
    )

    if response.success:
        print(f"   Message sent! ID: {response.data.get('id')}")
    else:
        print(f"   Error: {response.data}")

    print("\n" + "=" * 60)
    print("Message examples complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
