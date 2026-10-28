#!/usr/bin/env python3
"""Assign CreatorIQ publishers to a campaign.

Reads publisher IDs from a CSV and calls the CreatorIQ assign-publisher
endpoint. The API key is read from the environment and is never printed.

  python3 scripts/import_campaign_publishers.py --campaign 2991466 --csv publishers.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

BASE_URL = "https://apis.creatoriq.com"
ALLOWED_STATUSES = ("Accepted", "Invited", "Selected", "Declined")
KEY_ENV_VARS = ("CREATORIQ_API_KEY", "Uploading")


class ImportError(Exception):
    """A publisher could not be assigned."""


def api_key() -> str:
    for name in KEY_ENV_VARS:
        value = os.environ.get(name, "").strip()
        if value:
            return value
    names = ", ".join(KEY_ENV_VARS)
    raise SystemExit(f"CreatorIQ API key not found. Set one of: {names}")


def redact(text: str, secret: str) -> str:
    if secret and secret in text:
        return text.replace(secret, "[redacted]")
    return text


def load_publisher_ids(path: Path) -> list[int]:
    raw_text = path.read_text(encoding="utf-8-sig")
    if not raw_text.strip():
        raise SystemExit(f"{path} is empty")

    reader = csv.DictReader(raw_text.splitlines())
    if not reader.fieldnames:
        raise SystemExit(f"{path} has no header row")

    fields = {
        (name or "").strip().lower().replace(" ", "").replace("_", ""): name
        for name in reader.fieldnames
        if name
    }
    column = fields.get("publisherid")
    if column is None:
        found = ", ".join(name for name in reader.fieldnames if name)
        raise SystemExit(
            f"{path} needs a PublisherId column. Found columns: {found or '(none)'}"
        )

    ids: list[int] = []
    seen: set[int] = set()
    for line_number, row in enumerate(reader, start=2):
        cell = (row.get(column) or "").strip()
        if not cell:
            continue
        try:
            publisher_id = int(cell)
        except ValueError as exc:
            raise SystemExit(
                f"{path}:{line_number} has a non-numeric PublisherId: {cell!r}"
            ) from exc
        if publisher_id <= 0:
            raise SystemExit(f"{path}:{line_number} has an invalid PublisherId: {publisher_id}")
        if publisher_id not in seen:
            seen.add(publisher_id)
            ids.append(publisher_id)

    if not ids:
        raise SystemExit(f"{path} has a PublisherId column but no ids")
    return ids


def error_message(payload: Any) -> str | None:
    if isinstance(payload, dict):
        for key in ("message", "Message", "ErrorMessage", "error", "raw"):
            value = payload.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        for value in payload.values():
            found = error_message(value)
            if found:
                return found
    elif isinstance(payload, list):
        for item in payload:
            found = error_message(item)
            if found:
                return found
    return None


def find_record(payload: Any, publisher_id: int) -> dict[str, Any] | None:
    target = str(publisher_id)

    def walk(node: Any) -> dict[str, Any] | None:
        if isinstance(node, dict):
            for key in ("PublisherId", "publisherId"):
                if key in node and str(node[key]) == target:
                    return node
            for value in node.values():
                found = walk(value)
                if found:
                    return found
        elif isinstance(node, list):
            for item in node:
                found = walk(item)
                if found:
                    return found
        return None

    return walk(payload)


def campaign_name(payload: Any) -> str | None:
    if not isinstance(payload, dict):
        return None
    campaign = payload.get("Campaign")
    if isinstance(campaign, dict):
        name = campaign.get("CampaignName") or campaign.get("Name")
        if isinstance(name, str) and name.strip():
            return name.strip()
    name = payload.get("CampaignName") or payload.get("Name")
    if isinstance(name, str) and name.strip():
        return name.strip()
    return None


class CreatorIQ:
    def __init__(self, key: str, timeout: int = 60) -> None:
        self.key = key
        self.timeout = timeout

    def request(self, method: str, path: str, body: dict[str, Any] | None = None) -> tuple[int, Any]:
        data = None if body is None else json.dumps(body).encode()
        headers = {"x-api-key": self.key, "Accept": "application/json"}
        if body is not None:
            headers["Content-Type"] = "application/json"
        last_status = 0
        last_payload: Any = {}
        for attempt in range(3):
            req = urllib.request.Request(
                BASE_URL + path,
                data=data,
                headers=headers,
                method=method,
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as response:
                    raw = response.read().decode("utf-8", "replace")
                    payload = json.loads(raw) if raw else {}
                    return response.status, payload
            except urllib.error.HTTPError as exc:
                raw = exc.read().decode("utf-8", "replace")
                try:
                    payload = json.loads(raw) if raw else {}
                except json.JSONDecodeError:
                    payload = {"raw": redact(raw[:500], self.key)}
                last_status, last_payload = exc.code, payload
                if exc.code in (429, 500, 502, 503, 504) and attempt < 2:
                    time.sleep(2 ** attempt)
                    continue
                return exc.code, payload
            except urllib.error.URLError as exc:
                reason = redact(str(exc.reason), self.key)
                if attempt < 2:
                    time.sleep(2 ** attempt)
                    last_status, last_payload = 0, {"message": reason}
                    continue
                return 0, {"message": reason}
        return last_status, last_payload

    def get_campaign(self, campaign_id: int) -> tuple[int, Any]:
        return self.request("GET", f"/crm/v1/api/campaign/{campaign_id}")

    def get_publisher(self, campaign_id: int, publisher_id: int) -> tuple[int, Any]:
        return self.request(
            "GET",
            f"/crm/v1/api/campaign/{campaign_id}/publishers?publisherId={publisher_id}",
        )

    def assign(self, campaign_id: int, publisher_id: int, status: str) -> tuple[int, Any]:
        return self.request(
            "POST",
            f"/crm/v1/api/campaign/{campaign_id}/publishers",
            {"publisherId": publisher_id, "status": status},
        )


def publisher_label(record: dict[str, Any] | None) -> str:
    if not record:
        return ""
    name = record.get("PublisherName") or record.get("Name") or ""
    current = record.get("Status") or record.get("PublisherStatus") or ""
    parts = []
    if isinstance(name, str) and name.strip():
        parts.append(name.strip())
    if isinstance(current, str) and current.strip():
        parts.append(f"status={current.strip()}")
    return "  ".join(parts)


def import_publishers(
    client: CreatorIQ,
    campaign_id: int,
    publisher_ids: list[int],
    status: str,
    dry_run: bool = False,
) -> tuple[str, list[dict[str, Any]]]:
    code, payload = client.get_campaign(campaign_id)
    if code != 200:
        message = error_message(payload) or f"HTTP {code}"
        raise SystemExit(f"Campaign {campaign_id} could not be loaded: {redact(message, client.key)}")

    name = campaign_name(payload) or "(unnamed campaign)"
    results: list[dict[str, Any]] = []
    for publisher_id in publisher_ids:
        lookup_code, lookup_payload = client.get_publisher(campaign_id, publisher_id)
        existing = find_record(lookup_payload, publisher_id) if lookup_code == 200 else None
        if existing:
            results.append(
                {
                    "publisher_id": publisher_id,
                    "result": "already_on_campaign",
                    "detail": publisher_label(existing),
                }
            )
            continue

        if lookup_code not in (200, 404):
            message = error_message(lookup_payload) or f"HTTP {lookup_code}"
            results.append(
                {
                    "publisher_id": publisher_id,
                    "result": "failed",
                    "detail": redact(message, client.key),
                }
            )
            continue

        if dry_run:
            results.append(
                {
                    "publisher_id": publisher_id,
                    "result": "would_add",
                    "detail": f"status={status}",
                }
            )
            continue

        assign_code, assign_payload = client.assign(campaign_id, publisher_id, status)
        assign_record = find_record(assign_payload, publisher_id)
        assign_error = None
        if isinstance(assign_payload, dict):
            nested = assign_payload.get("CampaignPublisher")
            if isinstance(nested, dict) and nested.get("ErrorMessage"):
                assign_error = str(nested["ErrorMessage"])
        if assign_code not in (200, 201) or assign_error:
            message = assign_error or error_message(assign_payload) or f"HTTP {assign_code}"
            results.append(
                {
                    "publisher_id": publisher_id,
                    "result": "failed",
                    "detail": redact(message, client.key),
                }
            )
            continue

        verify_code, verify_payload = client.get_publisher(campaign_id, publisher_id)
        verified = find_record(verify_payload, publisher_id) if verify_code == 200 else None
        if not verified and not assign_record:
            results.append(
                {
                    "publisher_id": publisher_id,
                    "result": "failed",
                    "detail": "assignment response did not include this publisher",
                }
            )
            continue

        results.append(
            {
                "publisher_id": publisher_id,
                "result": "added",
                "detail": publisher_label(verified or assign_record) or f"status={status}",
            }
        )
    return name, results


def print_report(campaign_id: int, name: str, results: list[dict[str, Any]], dry_run: bool) -> int:
    mode = "DRY RUN" if dry_run else "IMPORT"
    print(f"{mode}  campaign {campaign_id}: {name}")
    failures = 0
    for row in results:
        print(f"{row['publisher_id']}  {row['result']}  {row['detail']}".rstrip())
        if row["result"] == "failed":
            failures += 1
    added = sum(1 for row in results if row["result"] == "added")
    skipped = sum(1 for row in results if row["result"] == "already_on_campaign")
    planned = sum(1 for row in results if row["result"] == "would_add")
    print(
        f"summary  added={added}  already_on_campaign={skipped}  "
        f"would_add={planned}  failed={failures}  total={len(results)}"
    )
    return 1 if failures else 0


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Assign CreatorIQ publishers to a campaign.")
    parser.add_argument("--campaign", required=True, type=int, help="CreatorIQ campaign id")
    parser.add_argument("--csv", required=True, type=Path, help="CSV with a PublisherId column")
    parser.add_argument(
        "--status",
        default="Accepted",
        choices=ALLOWED_STATUSES,
        help="Status to set on newly assigned publishers (default: Accepted)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Look up the campaign and publishers, but do not assign anyone",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if not args.csv.is_file():
        raise SystemExit(f"CSV not found: {args.csv}")
    publisher_ids = load_publisher_ids(args.csv)
    client = CreatorIQ(api_key())
    name, results = import_publishers(
        client,
        args.campaign,
        publisher_ids,
        args.status,
        dry_run=args.dry_run,
    )
    return print_report(args.campaign, name, results, args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
