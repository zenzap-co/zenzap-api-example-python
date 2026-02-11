"""
Zenzap API Client

A Python client for interacting with the Zenzap External Integration API.
Handles authentication, HMAC signature generation, and API requests.
"""

import hashlib
import hmac
import json
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

    def _generate_signature(self, data: str) -> str:
        """
        Generate HMAC-SHA256 signature for request authentication.

        For GET requests: sign the full request path (including query string)
        For POST/PATCH/DELETE: sign the JSON request body

        Args:
            data: The data to sign (path for GET, body for POST/PATCH/DELETE)

        Returns:
            Hex-encoded HMAC-SHA256 signature
        """
        return hmac.new(
            self.secret.encode("utf-8"),
            data.encode("utf-8"),
            hashlib.sha256
        ).hexdigest()

    def _get_headers(self, signature: str, include_content_type: bool = False) -> dict:
        """Build request headers with authentication."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-Signature": signature,
        }
        if include_content_type:
            headers["Content-Type"] = "application/json"
        return headers

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

    def _get(self, path: str) -> ApiResponse:
        """
        Make a GET request to the API.

        Args:
            path: API path (e.g., "/v2/topics")

        Returns:
            ApiResponse with status and data
        """
        signature = self._generate_signature(path)
        url = f"{self.base_url}{path}"

        try:
            response = requests.get(
                url,
                headers=self._get_headers(signature),
                timeout=self.timeout,
            )
            return ApiResponse.from_response(response)
        except requests.RequestException as exception:
            return ApiResponse.from_exception(exception)

    def _post(self, path: str, body: dict) -> ApiResponse:
        """
        Make a POST request to the API.

        Args:
            path: API path (e.g., "/v2/topics")
            body: Request body as dictionary

        Returns:
            ApiResponse with status and data
        """
        body_str = json.dumps(body, separators=(",", ":"))
        signature = self._generate_signature(body_str)
        url = f"{self.base_url}{path}"

        try:
            response = requests.post(
                url,
                headers=self._get_headers(signature, include_content_type=True),
                data=body_str,
                timeout=self.timeout,
            )
            return ApiResponse.from_response(response)
        except requests.RequestException as exception:
            return ApiResponse.from_exception(exception)

    def _patch(self, path: str, body: dict) -> ApiResponse:
        """
        Make a PATCH request to the API.

        Args:
            path: API path
            body: Request body as dictionary

        Returns:
            ApiResponse with status and data
        """
        body_str = json.dumps(body, separators=(",", ":"))
        signature = self._generate_signature(body_str)
        url = f"{self.base_url}{path}"

        try:
            response = requests.patch(
                url,
                headers=self._get_headers(signature, include_content_type=True),
                data=body_str,
                timeout=self.timeout,
            )
            return ApiResponse.from_response(response)
        except requests.RequestException as exception:
            return ApiResponse.from_exception(exception)

    def _delete(self, path: str, body: dict) -> ApiResponse:
        """
        Make a DELETE request to the API.

        Args:
            path: API path
            body: Request body as dictionary

        Returns:
            ApiResponse with status and data
        """
        body_str = json.dumps(body, separators=(",", ":"))
        signature = self._generate_signature(body_str)
        url = f"{self.base_url}{path}"

        try:
            response = requests.delete(
                url,
                headers=self._get_headers(signature, include_content_type=True),
                data=body_str,
                timeout=self.timeout,
            )
            return ApiResponse.from_response(response)
        except requests.RequestException as exception:
            return ApiResponse.from_exception(exception)

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

    def list_members(self, limit: int = 50, cursor: Optional[str] = None) -> ApiResponse:
        """
        List all members in the organization.

        Args:
            limit: Maximum number of members to return (default: 50)
            cursor: Pagination cursor for next page

        Returns:
            ApiResponse with list of members
        """
        path = self._build_path("/v2/members", {"limit": limit, "cursor": cursor})
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
        body = {
            "name": name,
            "members": members,
        }
        if description:
            body["description"] = description
        if external_id:
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
        return self._get(f"/v2/topics/{topic_id}")

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

        return self._patch(f"/v2/topics/{topic_id}", body)

    def add_topic_members(self, topic_id: str, member_ids: list[str]) -> ApiResponse:
        """
        Add members to a topic.

        Args:
            topic_id: UUID of the topic
            member_ids: List of member UUIDs to add (max 5 per request)

        Returns:
            ApiResponse with result
        """
        return self._post(f"/v2/topics/{topic_id}/members", {"memberIds": member_ids})

    def remove_topic_members(self, topic_id: str, member_ids: list[str]) -> ApiResponse:
        """
        Remove members from a topic.

        Args:
            topic_id: UUID of the topic
            member_ids: List of member UUIDs to remove (max 5 per request)

        Returns:
            ApiResponse with result
        """
        return self._delete(f"/v2/topics/{topic_id}/members", {"memberIds": member_ids})

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
        body = {
            "topicId": topic_id,
            "text": text,
        }
        if external_id:
            body["externalId"] = external_id

        return self._post("/v2/messages", body)

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
        body = {
            "topicId": topic_id,
            "title": title,
        }
        if description:
            body["description"] = description
        if assignee:
            body["assignee"] = assignee
        if due_date is not None:
            body["dueDate"] = due_date
        if external_id:
            body["externalId"] = external_id

        return self._post("/v2/tasks", body)
