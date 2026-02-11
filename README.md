# Zenzap API Python Examples

Python examples demonstrating how to use the Zenzap External Integration API.

## Overview

This repository provides a Python client and examples for the [Zenzap API](https://docs.zenzap.co/), enabling you to:

- Create and manage topics (group chats/channels)
- Send messages to topics
- Create and assign tasks
- Look up topics by external IDs (for system integration)
- Manage topic members

## Quick Start

### 1. Install dependencies

```bash
python3 -m pip install -r requirements.txt
```

### 2. Configure credentials

Copy the example environment file and fill in your credentials:

```bash
cp .env.example .env
```

Edit `.env` with your bot credentials from the Zenzap dashboard:

```env
API_BASE_URL=https://api.zenzap.co
BOT_API_KEY=your_bot_api_key_here
BOT_SECRET=your_bot_secret_here
MEMBER_IDS=member-uuid-1,member-uuid-2
```

### 3. Get organization member IDs

The `MEMBER_IDS` in your `.env` file are UUIDs of users in your organization. To find these IDs, use the list members endpoint:

```bash
python3 -c "
from zenzap_client import ZenzapClient
from dotenv import load_dotenv
import os

load_dotenv()
client = ZenzapClient(
    api_key=os.getenv('BOT_API_KEY'),
    secret=os.getenv('BOT_SECRET'),
    base_url=os.getenv('API_BASE_URL')
)
response = client.list_members()
if response.success:
    for member in response.data:
        print(f\"{member['name']}: {member['id']}\")
"
```

Copy the member IDs you want to use and update `MEMBER_IDS` in your `.env` file (comma-separated).

### 4. Run the quickstart example

```bash
python3 examples/01_quickstart.py
```

## Authentication

The Zenzap API uses two-factor authentication:

1. **Bearer Token**: Your bot's API token in the `Authorization` header
2. **HMAC Signature**: A SHA256 signature in the `X-Signature` header

### Signature Generation

- **GET requests**: Sign the full request path (including query string)
- **POST/PATCH/DELETE requests**: Sign the JSON request body

```python
import hmac
import hashlib

def generate_signature(data: str, signing_key: str) -> str:
    return hmac.new(
        signing_key.encode("utf-8"),
        data.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

# For GET request
signature = generate_signature("/v2/topics", signing_key)

# For POST request
body = '{"name": "My Topic", "members": ["uuid"]}'
signature = generate_signature(body, signing_key)
```

## Examples

### 01_quickstart.py
Basic API usage: get bot info, create a topic, send a message, create a task.

### 02_topics.py
Topic management: create, list, update, get by ID/external ID, add/remove members.

### 03_messages.py
Sending messages: basic text, special characters, unicode, with external IDs.

### 04_tasks.py
Task operations: create tasks with assignees, due dates, and external IDs.

### 05_full_workflow.py
Complete integration workflow simulating a project management use case.

### 06_cleanup_demo_topics.py
Best-effort cleanup utility for demo topics (dry-run by default).

## Demo Cleanup

If you ran examples multiple times, you can leave demo topics (remove the bot from them) with:

```bash
python3 examples/06_cleanup_demo_topics.py
```

Apply cleanup changes:

```bash
python3 examples/06_cleanup_demo_topics.py --apply
```

Current public API limitation:
- Hard delete for topics/tasks/messages is not available yet.
- This script removes the current bot member from matching demo topics.

## Client Usage

```python
from zenzap_client import ZenzapClient

# Initialize the client
client = ZenzapClient(
    api_key="your_bot_api_key",
    secret="your_bot_secret",
    base_url="https://api.zenzap.co",  # optional
    timeout=30  # optional, seconds
)

# Get current bot info
response = client.get_current_member()
print(f"Bot name: {response.data['name']}")

# Create a topic with external ID
response = client.create_topic(
    name="Project Updates",
    members=["member-uuid-1", "member-uuid-2"],
    description="Updates for our project",
    external_id="project-123"  # For integration with your system
)
topic_id = response.data["id"]

# Send a message
response = client.send_message(
    topic_id=topic_id,
    text="Hello from the API!"
)

# Create a task
import time
due_date = int((time.time() + 7 * 24 * 60 * 60) * 1000)  # 7 days from now

response = client.create_task(
    topic_id=topic_id,
    title="Review documentation",
    description="Check all docs are up to date",
    assignee="member-uuid-1",
    due_date=due_date,
    external_id="JIRA-123"
)

# Look up topic by external ID
response = client.get_topic_by_external_id("project-123")
```

## API Reference

### Members

| Method | Description |
|--------|-------------|
| `get_current_member()` | Get info about the authenticated bot |
| `list_members(limit, cursor)` | List organization members |

### Topics

| Method | Description |
|--------|-------------|
| `create_topic(name, members, description, external_id)` | Create a new topic |
| `get_topic(topic_id)` | Get topic by UUID |
| `get_topic_by_external_id(external_id)` | Get topic by external identifier |
| `list_topics(limit, cursor)` | List topics where bot is a member |
| `update_topic(topic_id, name, description)` | Update topic details |
| `add_topic_members(topic_id, member_ids)` | Add members to topic |
| `remove_topic_members(topic_id, member_ids)` | Remove members from topic |

### Messages

| Method | Description |
|--------|-------------|
| `send_message(topic_id, text, external_id)` | Send a message to a topic |

### Tasks

| Method | Description |
|--------|-------------|
| `create_task(topic_id, title, description, assignee, due_date, external_id)` | Create a task |

## External IDs

External IDs allow you to integrate Zenzap with your existing systems:

- **Topics**: Create a channel with `external_id="project-123"` and look it up later
- **Tasks**: Link tasks with `external_id="JIRA-456"` to your project management tool
- **Messages**: Track notifications with `external_id="notification-789"`

When a topic is created with an external ID, the API returns a full external ID in the format `botId:externalId`. You can look up topics using either:
- The short ID (only for topics created by your bot)
- The full ID (for any topic where your bot is a member)

### Deep Linking

Link directly to a topic in the Zenzap app:
```
https://app.zenzap.co?external_topic=YOUR_EXTERNAL_ID
```

## Error Handling

All client methods return an `ApiResponse` object:

```python
response = client.create_topic(name="Test", members=["uuid"])

if response.success:
    print(f"Created topic: {response.data['id']}")
else:
    print(f"Error {response.status}: {response.data}")
```

### Common Status Codes

| Code | Description |
|------|-------------|
| 200/201 | Success |
| 400 | Bad request (invalid input) |
| 401 | Unauthorized (invalid token or signature) |
| 404 | Not found (or bot not a member) |
| 500 | Server error |

## Rate Limits

The API has rate limiting. Check the [official documentation](https://docs.zenzap.co/) for current limits.

## Resources

- [Zenzap API Documentation](https://docs.zenzap.co/)
- [Authentication Guide](https://docs.zenzap.co/authentication)
- [API Reference](https://docs.zenzap.co/api-reference)

## License

Apache License 2.0 - see LICENSE file for details.
