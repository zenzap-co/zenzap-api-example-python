#!/usr/bin/env python3
"""
Cleanup Demo Topics (Best-Effort)

This script finds topics created by the example scripts and removes the bot
itself from those topics.

This is effectively a "leave topic" cleanup.
Because the public API does not currently expose topic/task/message delete endpoints,
cleanup is limited to:
- Removing the current bot member from matching demo topics

Usage:
    python3 examples/06_cleanup_demo_topics.py
    python3 examples/06_cleanup_demo_topics.py --apply
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
from zenzap_client import ZenzapClient


DEMO_PREFIXES = (
    "Quickstart Demo ",
    "Regular Topic ",
    "Project Updates Channel",
    "Updated Topic Name ",
    "Message Demo ",
    "Task Demo ",
    "Q1 2024 Product Launch",
)


def parse_topics_payload(payload):
    """Normalize list_topics payload shapes."""
    if isinstance(payload, list):
        return payload, None

    if not isinstance(payload, dict):
        return [], None

    topics = payload.get("topics")
    if topics is None:
        topics = payload.get("data", [])
    if not isinstance(topics, list):
        topics = []

    next_cursor = payload.get("nextCursor")
    if next_cursor is None:
        next_cursor = payload.get("cursor")
    return topics, next_cursor


def is_demo_topic(topic):
    name = (topic.get("name") or "").strip()
    description = (topic.get("description") or "").strip().lower()
    external_id = (topic.get("externalId") or "").strip()

    if any(name.startswith(prefix) for prefix in DEMO_PREFIXES):
        return True

    if external_id and "project-" in external_id:
        return True

    if "quickstart example" in description:
        return True
    if "project integration" in description:
        return True

    return False


def main():
    parser = argparse.ArgumentParser(description="Leave demo topics created by examples.")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes. Default mode is dry-run.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Page size for topic listing (default: 100).",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=20,
        help="Safety limit on pagination depth (default: 20).",
    )
    args = parser.parse_args()

    load_dotenv()

    api_key = os.getenv("BOT_API_KEY")
    secret = os.getenv("BOT_SECRET")
    base_url = os.getenv("API_BASE_URL", "https://api.zenzap.co")

    if not api_key or not secret:
        print("Error: BOT_API_KEY and BOT_SECRET must be set in .env")
        sys.exit(1)

    client = ZenzapClient(api_key=api_key, secret=secret, base_url=base_url)

    me_response = client.get_current_member()
    if not me_response.success:
        print(f"Error: Failed to authenticate bot: {me_response.data}")
        sys.exit(1)

    bot_id = me_response.data.get("id")
    if not bot_id:
        print("Error: Bot ID missing from /v2/members/me response")
        sys.exit(1)

    mode = "APPLY" if args.apply else "DRY-RUN"
    print("=" * 60)
    print(f"Demo Topic Cleanup ({mode})")
    print("=" * 60)
    print(f"Bot ID: {bot_id}")
    print(f"Base URL: {base_url}")

    all_topics = []
    cursor = None

    for page in range(1, args.max_pages + 1):
        response = client.list_topics(limit=args.limit, cursor=cursor)
        if not response.success:
            print(f"Error: list_topics failed on page {page}: {response.data}")
            sys.exit(1)

        page_topics, next_cursor = parse_topics_payload(response.data)
        all_topics.extend(page_topics)
        print(f"Listed page {page}: {len(page_topics)} topics")

        if not next_cursor or next_cursor == cursor:
            break
        cursor = next_cursor
    else:
        print(f"Reached --max-pages ({args.max_pages}); stopping pagination.")

    demo_topics = [topic for topic in all_topics if is_demo_topic(topic)]
    print(f"\nFound {len(demo_topics)} demo topic(s) out of {len(all_topics)} total.")

    if not demo_topics:
        print("Nothing to clean up.")
        return

    topics_with_bot_member = 0
    left_topics_count = 0
    skipped_not_member_count = 0
    failed_topics = 0

    for topic in demo_topics:
        topic_id = topic.get("id", "")
        topic_name = topic.get("name", "(unnamed)")
        current_members = topic.get("members") or []
        bot_is_member = bot_id in current_members

        print(f"\n- Topic: {topic_name} ({topic_id})")
        print("  Action: remove current bot member")

        if bot_is_member:
            topics_with_bot_member += 1
        else:
            skipped_not_member_count += 1
            print("  Skip: bot is not a member of this topic")
            continue

        if not args.apply:
            continue

        remove_response = client.remove_topic_members(topic_id, [bot_id])
        if remove_response.success:
            left_topics_count += 1
            print("  Bot removed successfully")
        else:
            failed_topics += 1
            print(f"  Remove bot failed: {remove_response.data}")

    print("\n" + "=" * 60)
    print("Cleanup Summary")
    print("=" * 60)
    print(f"Mode: {mode}")
    print(f"Demo topics matched: {len(demo_topics)}")
    print(f"Topics where bot is member: {topics_with_bot_member}")
    print(f"Topics left by bot: {left_topics_count}")
    print(f"Topics skipped (bot not member): {skipped_not_member_count}")
    print(f"Topics with failures: {failed_topics}")

    if not args.apply:
        print("\nDry-run only. Re-run with --apply to perform changes.")
    print("Note: Topic/task/message hard delete is not supported by the public API yet.")

    if args.apply and failed_topics:
        sys.exit(1)


if __name__ == "__main__":
    main()
