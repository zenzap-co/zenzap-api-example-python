"""
Zenzap API Client

A Python client for interacting with the Zenzap External Integration API.
Handles authentication, HMAC signature generation, and API requests.
"""

import hashlib
import hmac
import json
import time
from typing import Any, Optional
from dataclasses import dataclass
from urllib.parse import quote, urlencode

import requests


@dataclass
class ApiResponse:
    """Represents an API response with status code and data."""
    status: int
    data: Any
    success: bool

    @classmethod
    def from_response(cls, response: requests.Response) -> "ApiResponse":
        try:
            data = response.json()
        except ValueError:
            text = response.text.strip()
            data = {"raw": text} if text else {}
        return cls(
            status=response.status_code,
            data=data,
            success=200 <= response.status_code < 300
        )

    @classmethod
    def from_exception(cls, exception: requests.RequestException) -> "ApiResponse":
        """Build a normalized error response for transport-level failures."""
        return cls(
            status=0,
            data={
                "error": str(exception),
                "type": exception.__class__.__name__,
            },
            success=False,
        )


class ZenzapClient:
    """
    Client for the Zenzap External Integration API.

    Handles authentication using Bearer tokens and HMAC-SHA256 signatures.

    Example usage:
        client = ZenzapClient(
            api_key="your_bot_api_key",
            secret="your_bot_secret"
        )

        # Get current bot info
        response = client.get_current_member()
        print(response.data)

        # Create a topic
        response = client.create_topic(
            name="My Topic",
            members=["member-uuid-1", "member-uuid-2"]
        )
    """

    def __init__(
        self,
        api_key: str,
        secret: str,
        base_url: str = "https://api.zenzap.co",
        timeout: float = 30.0,
    ):
        """
        Initialize the Zenzap client.

        Args:
            api_key: Your bot's API key (Bearer token)
            secret: Your bot's secret for HMAC signatures (BOT_SECRET)
            base_url: API base URL (default: https://api.zenzap.co)
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key
        self.secret = secret
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _generate_signature(self, data: str, timestamp: int) -> str:
        """
        Generate HMAC-SHA256 signature for request authentication.

        The signed payload is "{timestamp}.{data}" where data is:
        - GET requests: the full request path (including query string)
        - POST/PATCH/DELETE: the JSON request body

        Args:
            data: The data to sign (path for GET, body for POST/PATCH/DELETE)
            timestamp: Unix timestamp in milliseconds

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        payload = f"{timestamp}.{data}"
        return hmac.new(
            self.secret.encode("utf-8"),
            payload.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    @staticmethod
    def _build_path(path: str, params: Optional[dict[str, Any]] = None) -> str:
        """Build a signed path string with URL-encoded query parameters."""
        if not params:
            return path

        query = urlencode(
            {k: v for k, v in params.items() if v is not None},
            doseq=True,
        )
        return f"{path}?{query}" if query else path

    def _request(self, method: str, path: str, body: Optional[dict] = None) -> ApiResponse:
        """
        Make an authenticated request to the API.

        Handles timestamp generation, HMAC signature, and headers for all methods.

        Args:
            method: HTTP method (GET, POST, PATCH, DELETE)
            path: API path (e.g., "/v2/topics")
            body: Request body as dictionary (for POST/PATCH/DELETE)

        Returns:
            ApiResponse with status and data
        """
        timestamp = int(time.time() * 1000)
        url = f"{self.base_url}{path}"

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Timestamp": str(timestamp),
        }

        if body is not None:
            body_str = json.dumps(body, separators=(",", ":"))
            signature = self._generate_signature(body_str, timestamp)
            headers["X-Signature"] = signature
            headers["Content-Type"] = "application/json"
        else:
            body_str = None
            signature = self._generate_signature(path, timestamp)
            headers["X-Signature"] = signature

        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                data=body_str,
                timeout=self.timeout,
            )
            return ApiResponse.from_response(response)
        except requests.RequestException as exception:
            return ApiResponse.from_exception(exception)

    def _get(self, path: str) -> ApiResponse:
        """Make a GET request to the API."""
        return self._request("GET", path)

    def _post(self, path: str, body: dict) -> ApiResponse:
        """Make a POST request to the API."""
        return self._request("POST", path, body)

    def _patch(self, path: str, body: dict) -> ApiResponse:
        """Make a PATCH request to the API."""
        return self._request("PATCH", path, body)

    def _delete(self, path: str, body: dict) -> ApiResponse:
        """Make a DELETE request to the API."""
        return self._request("DELETE", path, body)

    # =========================================================================
    # Member Endpoints
    # =========================================================================

    def get_current_member(self) -> ApiResponse:
        """
        Get information about the current bot.

        Returns:
            ApiResponse with member data including id, name, email, status
        """
        return self._get("/v2/members/me")

    def list_members(
        self,
        limit: int = 50,
        cursor: Optional[str] = None,
        emails: Optional[list[str]] = None,
    ) -> ApiResponse:
        """
        List all members in the organization.

        Args:
            limit: Maximum number of members to return (default: 50)
            cursor: Pagination cursor for next page
            emails: Filter by email addresses (comma-separated in query)

        Returns:
            ApiResponse with list of members
        """
        params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "emails": ",".join(emails) if emails is not None else None,
        }
        path = self._build_path("/v2/members", params)
        return self._get(path)

    # =========================================================================
    # Topic Endpoints
    # =========================================================================

    def create_topic(
        self,
        name: str,
        members: list[str],
        description: Optional[str] = None,
        external_id: Optional[str] = None
    ) -> ApiResponse:
        """
        Create a new topic (group chat/channel).

        Your bot will automatically be added as a member.

        Args:
            name: Topic name (max 64 characters)
            members: List of member UUIDs to add (min 1)
            description: Optional topic description (max 10,000 characters)
            external_id: Optional external identifier for tracking (max 100 characters)

        Returns:
            ApiResponse with created topic data including id, name, createdAt
        """
        body: dict[str, Any] = {
            "name": name,
            "members": members,
        }
        if description is not None:
            body["description"] = description
        if external_id is not None:
            body["externalId"] = external_id

        return self._post("/v2/topics", body)

    def get_topic(self, topic_id: str) -> ApiResponse:
        """
        Get details of a specific topic by ID.

        Args:
            topic_id: UUID of the topic

        Returns:
            ApiResponse with topic details
        """
        return self._get(f"/v2/topics/{quote(topic_id, safe='')}")

    def get_topic_by_external_id(self, external_id: str) -> ApiResponse:
        """
        Get a topic by its external ID.

        Note: If the topic was created by a different bot, you need to use
        the full external ID (botId:externalId format). If created by your bot,
        you can use just the external ID part.

        Args:
            external_id: The external identifier

        Returns:
            ApiResponse with topic details (404 if not found or not a member)
        """
        encoded_external_id = quote(external_id, safe="")
        return self._get(f"/v2/topics/external/{encoded_external_id}")

    def list_topics(self, limit: int = 50, cursor: Optional[str] = None) -> ApiResponse:
        """
        List all topics where the bot is a member.

        Args:
            limit: Maximum number of topics to return (default: 50)
            cursor: Pagination cursor for next page

        Returns:
            ApiResponse with list of topics
        """
        path = self._build_path("/v2/topics", {"limit": limit, "cursor": cursor})
        return self._get(path)

    def update_topic(
        self,
        topic_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None
    ) -> ApiResponse:
        """
        Update a topic's name and/or description.

        Args:
            topic_id: UUID of the topic
            name: New topic name (max 64 characters)
            description: New topic description (max 10,000 characters)

        Returns:
            ApiResponse with updated topic data
        """
        body = {}
        if name is not None:
            body["name"] = name
        if description is not None:
            body["description"] = description

        return self._patch(f"/v2/topics/{quote(topic_id, safe='')}", body)

    def add_topic_members(self, topic_id: str, member_ids: list[str]) -> ApiResponse:
        """
        Add members to a topic.

        Args:
            topic_id: UUID of the topic
            member_ids: List of member UUIDs to add (max 5 per request)

        Returns:
            ApiResponse with result
        """
        return self._post(f"/v2/topics/{quote(topic_id, safe='')}/members", {"memberIds": member_ids})

    def remove_topic_members(self, topic_id: str, member_ids: list[str]) -> ApiResponse:
        """
        Remove members from a topic.

        Args:
            topic_id: UUID of the topic
            member_ids: List of member UUIDs to remove (max 5 per request)

        Returns:
            ApiResponse with result
        """
        return self._delete(f"/v2/topics/{quote(topic_id, safe='')}/members", {"memberIds": member_ids})

    def get_topic_messages(
        self,
        topic_id: str,
        limit: int = 50,
        cursor: Optional[str] = None,
        before: Optional[int] = None,
        after: Optional[int] = None,
        sender_id: Optional[str] = None,
        order: Optional[str] = None,
        include_system: Optional[bool] = None,
        thread_id: Optional[str] = None,
    ) -> ApiResponse:
        """
        Get messages from a topic with cursor-based pagination.

        Args:
            topic_id: UUID of the topic
            limit: Maximum number of messages to return (1-100, default: 50)
            cursor: Pagination cursor for next page
            before: Only messages before this Unix timestamp (milliseconds)
            after: Only messages after this Unix timestamp (milliseconds)
            sender_id: Filter by sender UUID
            order: Sort order ("asc" or "desc", default: "desc")
            include_system: Include system messages (default: True)
            thread_id: Filter by thread UUID

        Returns:
            ApiResponse with messages array, nextCursor, hasMore
        """
        params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "before": before,
            "after": after,
            "senderId": sender_id,
            "order": order,
            "includeSystem": str(include_system).lower() if include_system is not None else None,
            "threadId": thread_id,
        }
        path = self._build_path(f"/v2/topics/{quote(topic_id, safe='')}/messages", params)
        return self._get(path)

    # =========================================================================
    # Message Endpoints
    # =========================================================================

    def send_message(
        self,
        topic_id: str,
        text: str,
        external_id: Optional[str] = None
    ) -> ApiResponse:
        """
        Send a message to a topic.

        Args:
            topic_id: UUID of the topic
            text: Message content (max 10,000 characters)
            external_id: Optional external identifier (max 100 characters)

        Returns:
            ApiResponse with message data including id, topicId, createdAt
        """
        body: dict[str, Any] = {
            "topicId": topic_id,
            "text": text,
        }
        if external_id is not None:
            body["externalId"] = external_id

        return self._post("/v2/messages", body)

    def add_reaction(self, message_id: str, reaction: str) -> ApiResponse:
        """
        Add an emoji reaction to a message.

        Args:
            message_id: UUID of the message
            reaction: Emoji string to react with

        Returns:
            ApiResponse with reaction details
        """
        return self._post(f"/v2/messages/{quote(message_id, safe='')}/reactions", {"reaction": reaction})

    def mark_message_delivered(self, message_id: str) -> ApiResponse:
        """
        Mark a message as delivered by the current bot.

        Args:
            message_id: UUID of the message

        Returns:
            ApiResponse with result
        """
        return self._post(f"/v2/messages/{quote(message_id, safe='')}/delivered", {})

    def mark_message_read(self, message_id: str) -> ApiResponse:
        """
        Mark a message as read by the current bot.

        Args:
            message_id: UUID of the message

        Returns:
            ApiResponse with result
        """
        return self._post(f"/v2/messages/{quote(message_id, safe='')}/read", {})

    # =========================================================================
    # Task Endpoints
    # =========================================================================

    def create_task(
        self,
        topic_id: str,
        title: str,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[int] = None,
        external_id: Optional[str] = None
    ) -> ApiResponse:
        """
        Create a task in a topic.

        Args:
            topic_id: UUID of the topic
            title: Task title (max 256 characters)
            description: Task description (max 10,000 characters)
            assignee: UUID of member to assign (must be topic member)
            due_date: Due date as Unix timestamp in milliseconds
            external_id: Optional external identifier (max 100 characters)

        Returns:
            ApiResponse with task data including id, topicId, title, createdAt
        """
        body: dict[str, Any] = {
            "topicId": topic_id,
            "title": title,
        }
        if description is not None:
            body["description"] = description
        if assignee is not None:
            body["assignee"] = assignee
        if due_date is not None:
            body["dueDate"] = due_date
        if external_id is not None:
            body["externalId"] = external_id

        return self._post("/v2/tasks", body)

    def list_tasks(
        self,
        topic_id: Optional[str] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        limit: int = 50,
        cursor: Optional[str] = None,
    ) -> ApiResponse:
        """
        List tasks visible to the bot with optional filtering.

        Args:
            topic_id: Filter by topic UUID
            status: Filter by status ("Open" or "Done")
            assignee: Filter by assignee UUID (empty string for unassigned)
            limit: Maximum number of tasks to return (1-100, default: 50)
            cursor: Pagination cursor for next page

        Returns:
            ApiResponse with tasks array, nextCursor, hasMore
        """
        params: dict[str, Any] = {
            "limit": limit,
            "cursor": cursor,
            "topicId": topic_id,
            "status": status,
            "assignee": assignee,
        }
        path = self._build_path("/v2/tasks", params)
        return self._get(path)

    def get_task(self, task_id: str) -> ApiResponse:
        """
        Get a single task by ID.

        Args:
            task_id: UUID of the task

        Returns:
            ApiResponse with full task object
        """
        return self._get(f"/v2/tasks/{quote(task_id, safe='')}")

    def update_task(
        self,
        task_id: str,
        topic_id: Optional[str] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        assignee: Optional[str] = None,
        due_date: Optional[int] = None,
        status: Optional[str] = None,
    ) -> ApiResponse:
        """
        Update task fields via partial update.

        Args:
            task_id: UUID of the task
            topic_id: UUID of the topic (required if status is provided)
            title: New task title (max 256 characters)
            description: New task description (max 10,000 characters)
            assignee: UUID of member to assign (empty string to unassign)
            due_date: Due date in milliseconds (0 to clear)
            status: Task status ("Open" or "Done")

        Returns:
            ApiResponse with id and updatedAt
        """
        body: dict[str, Any] = {
            k: v for k, v in {
                "topicId": topic_id,
                "title": title,
                "description": description,
                "assignee": assignee,
                "dueDate": due_date,
                "status": status,
            }.items() if v is not None
        }
        return self._patch(f"/v2/tasks/{quote(task_id, safe='')}", body)

    # =========================================================================
    # Poll Endpoints
    # =========================================================================

    def create_poll(
        self,
        topic_id: str,
        question: str,
        options: list[str],
        selection_type: str = "single",
        anonymous: bool = False,
    ) -> ApiResponse:
        """
        Create a poll in a topic.

        Args:
            topic_id: UUID of the topic
            question: Poll question (max 500 characters)
            options: List of option strings (2-10 items)
            selection_type: "single" or "multiple" (default: "single")
            anonymous: Whether votes are anonymous (default: False)

        Returns:
            ApiResponse with poll data including id, options (with server-generated IDs)
        """
        body: dict[str, Any] = {
            "topicId": topic_id,
            "question": question,
            "options": options,
            "selectionType": selection_type,
            "anonymous": anonymous,
        }
        return self._post("/v2/polls", body)

    def vote_on_poll(self, poll_id: str, option_id: str) -> ApiResponse:
        """
        Submit a vote on a poll on behalf of the bot.

        Args:
            poll_id: UUID of the poll
            option_id: ID of the option to vote for (from poll options)

        Returns:
            ApiResponse with vote details
        """
        return self._post(f"/v2/polls/{quote(poll_id, safe='')}/votes", {"optionId": option_id})

    # =========================================================================
    # Long Polling Endpoints
    # =========================================================================

    def get_updates(
        self,
        offset: Optional[str] = None,
        limit: int = 50,
        timeout: int = 0,
    ) -> ApiResponse:
        """
        Retrieve outbound events via long polling.

        Args:
            offset: Opaque offset from previous response
            limit: Maximum number of updates (1-100, default: 50)
            timeout: Long-poll timeout in seconds (0-30, default: 0)

        Returns:
            ApiResponse with updates array and nextOffset
        """
        params: dict[str, Any] = {
            "limit": limit,
            "timeout": timeout,
            "offset": offset,
        }
        path = self._build_path("/v2/updates", params)
        return self._get(path)
