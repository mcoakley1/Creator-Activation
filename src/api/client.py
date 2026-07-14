"""CreatorIQ ExchangeIQ API client."""

from __future__ import annotations

import time
from typing import Any
from urllib.parse import urljoin

import requests


class CreatorIQAPIError(Exception):
    """Raised when the CreatorIQ API returns an error."""

    def __init__(self, message: str, status_code: int | None = None, response_body: Any = None):
        super().__init__(message)
        self.status_code = status_code
        self.response_body = response_body


class CreatorIQClient:
    """Thin wrapper around the CreatorIQ Standard CRM / ExchangeIQ API."""

    DEFAULT_BASE_URL = "https://api.creatoriq.com"

    def __init__(
        self,
        api_key: str,
        org_name: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: int = 60,
        max_retries: int = 3,
    ):
        self.api_key = api_key
        self.org_name = org_name
        self.base_url = base_url.rstrip("/") + "/"
        self.timeout = timeout
        self.max_retries = max_retries
        self._session = requests.Session()
        self._session.headers.update(
            {
                "api-key": api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )
        if org_name:
            self._session.headers["X-Organization"] = org_name

    def _request(self, method: str, path: str, **kwargs: Any) -> Any:
        url = urljoin(self.base_url, path.lstrip("/"))
        last_error: Exception | None = None

        for attempt in range(self.max_retries):
            try:
                response = self._session.request(method, url, timeout=self.timeout, **kwargs)
            except requests.RequestException as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2**attempt)
                    continue
                raise CreatorIQAPIError(f"Request failed: {exc}") from exc

            if response.status_code == 429 and attempt < self.max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue

            if response.status_code >= 400:
                body: Any
                try:
                    body = response.json()
                except ValueError:
                    body = response.text
                raise CreatorIQAPIError(
                    f"API error {response.status_code} for {path}",
                    status_code=response.status_code,
                    response_body=body,
                )

            if not response.content:
                return {}

            try:
                return response.json()
            except ValueError as exc:
                raise CreatorIQAPIError(
                    f"Invalid JSON response from {path}",
                    status_code=response.status_code,
                    response_body=response.text,
                ) from exc

        raise CreatorIQAPIError(f"Request failed after retries: {last_error}")

    @staticmethod
    def _extract_items(payload: Any, *candidate_keys: str) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]

        if not isinstance(payload, dict):
            return []

        for key in candidate_keys:
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
            if isinstance(value, dict):
                for nested_key in ("items", "data", "results", "records", "publishers", "campaigns", "posts"):
                    nested = value.get(nested_key)
                    if isinstance(nested, list):
                        return [item for item in nested if isinstance(item, dict)]

        for key in ("data", "results", "items", "records"):
            value = payload.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]

        return []

    def get_campaigns(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/api/v1/campaigns")
        return self._extract_items(payload, "Campaigns", "campaigns", "CampaignCollection")

    def get_campaign_publishers(self, campaign_id: int | str) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/api/v1/campaign/{campaign_id}/publishers")
        return self._extract_items(payload, "Publishers", "publishers", "PublisherCollection")

    def get_campaign_activity(self, campaign_id: int | str) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/api/v1/campaign/{campaign_id}/activity")
        return self._extract_items(payload, "Activity", "activity", "Activities", "posts", "Posts")

    def get_publishers(self) -> list[dict[str, Any]]:
        payload = self._request("GET", "/api/v1/publishers")
        return self._extract_items(payload, "Publishers", "publishers", "PublisherCollection")

    def get_publisher(self, publisher_id: int | str) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/publisher/{publisher_id}")
        if isinstance(payload, dict):
            for key in ("Publisher", "publisher", "data"):
                value = payload.get(key)
                if isinstance(value, dict):
                    return value
            return payload
        return {}

    def get_publisher_posts(self, publisher_id: int | str) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/api/v1/publisher/{publisher_id}/posts")
        return self._extract_items(payload, "Posts", "posts", "PostCollection")

    def get_publisher_activity(self, publisher_id: int | str) -> list[dict[str, Any]]:
        payload = self._request("GET", f"/api/v1/publisher/{publisher_id}/activity")
        return self._extract_items(payload, "Activity", "activity", "Activities")

    def get_conversions(self, params: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        payload = self._request("GET", "/api/v1/conversions", params=params or {})
        return self._extract_items(payload, "Conversions", "conversions", "ConversionCollection")

    def get_partner(self, partner_id: int | str) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/partner/{partner_id}")
        if isinstance(payload, dict):
            for key in ("Partner", "partner", "data"):
                value = payload.get(key)
                if isinstance(value, dict):
                    return value
            return payload
        return {}

    def test_connection(self) -> bool:
        self.get_campaigns()
        return True
