"""Quarterly creator activation metrics derived from CreatorIQ data."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

import pandas as pd


@dataclass
class ActivationSummary:
    quarter: str
    year: int
    total_creators: int
    active_creators: int
    inactive_creators: int
    posted: int
    linked: int
    generated_revenue: int
    clicked: int
    converted: int
    verified: int
    total_revenue: float
    total_clicks: int
    total_conversions: int
    total_posts: int
    activation_rate: float
    creator_records: list[dict[str, Any]] = field(default_factory=list)


def quarter_label(year: int, quarter: int) -> str:
    return f"Q{quarter} {year}"


def get_quarter_date_range(year: int, quarter: int) -> tuple[date, date]:
    start_month = (quarter - 1) * 3 + 1
    start = date(year, start_month, 1)
    if quarter == 4:
        end = date(year, 12, 31)
    else:
        end = date(year, start_month + 3, 1) - pd.Timedelta(days=1)
        end = end.date() if hasattr(end, "date") else end
    return start, end


def _first_present(record: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        if key in record and record[key] not in (None, "", []):
            return record[key]
    return default


def _to_float(value: Any) -> float:
    if value in (None, "", "null"):
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _to_int(value: Any) -> int:
    if value in (None, "", "null"):
        return 0
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _parse_date(value: Any) -> date | None:
    if value in (None, "", "null"):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    text = str(value).strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ", "%m/%d/%Y"):
        try:
            return datetime.strptime(text[:19], fmt).date()
        except ValueError:
            continue
    try:
        return pd.to_datetime(text, utc=True).date()
    except (TypeError, ValueError):
        return None


def _in_quarter(value: Any, start: date, end: date) -> bool:
    parsed = _parse_date(value)
    return parsed is not None and start <= parsed <= end


def _is_truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return value > 0
    if isinstance(value, str):
        return value.strip().lower() in {"true", "yes", "y", "1", "linked", "active", "verified"}
    return bool(value)


def _publisher_id(record: dict[str, Any]) -> str:
    value = _first_present(
        record,
        "PublisherId",
        "publisherId",
        "publisher_id",
        "Id",
        "id",
        "NetworkPublisherId",
        "networkPublisherId",
    )
    return str(value) if value is not None else ""


def _publisher_name(record: dict[str, Any]) -> str:
    return str(
        _first_present(
            record,
            "PublisherName",
            "publisherName",
            "publisher_name",
            "Name",
            "name",
            "UserName",
            "userName",
            "username",
            default="Unknown",
        )
    )


def _normalize_publishers(publishers: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    normalized: dict[str, dict[str, Any]] = {}
    for publisher in publishers:
        publisher_id = _publisher_id(publisher)
        if not publisher_id:
            continue
        normalized[publisher_id] = {
            "publisher_id": publisher_id,
            "publisher_name": _publisher_name(publisher),
            "username": _first_present(publisher, "UserName", "userName", "username", default=""),
            "status": _first_present(publisher, "Status", "status", "CampaignStatus", default=""),
            "verified": _is_truthy(_first_present(publisher, "Verified", "verified")),
            "social_network": _first_present(
                publisher, "SocialNetwork", "socialNetwork", "social_network", default=""
            ),
            "raw": publisher,
        }
    return normalized


def _aggregate_posts(
    posts: list[dict[str, Any]],
    start: date,
    end: date,
) -> dict[str, dict[str, Any]]:
    by_publisher: dict[str, dict[str, Any]] = {}
    for post in posts:
        publisher_id = str(
            _first_present(post, "PublisherId", "publisherId", "publisher_id", default="")
        )
        if not publisher_id:
            continue

        post_date = _first_present(
            post,
            "DateSubmitted",
            "dateSubmitted",
            "DateSubmittedUTC",
            "StartDate",
            "startDate",
            "CreatedAt",
            "createdAt",
        )
        in_quarter = _in_quarter(post_date, start, end)
        if not in_quarter:
            continue

        bucket = by_publisher.setdefault(
            publisher_id,
            {
                "post_count": 0,
                "clicks": 0,
                "link_clicks": 0,
                "engagement": 0,
                "impressions": 0,
                "linked": False,
                "unlinked": False,
                "requirement_linked": False,
                "last_post_date": None,
            },
        )
        bucket["post_count"] += 1
        bucket["clicks"] += _to_int(_first_present(post, "Clicks", "clicks", "CombinedClicks"))
        bucket["link_clicks"] += _to_int(
            _first_present(post, "LinkClicks", "linkClicks", "CombinedClicks", "PaidLinkClicks")
        )
        bucket["engagement"] += _to_int(
            _first_present(post, "Engagement", "engagement", "CombinedEngagement")
        )
        bucket["impressions"] += _to_int(
            _first_present(post, "Impressions", "impressions", "CombinedImpressions")
        )

        link_id = _first_present(post, "LinkId", "linkId", "link_id")
        requirement_linked = _first_present(post, "RequirementLinked", "requirementLinked")
        unlinked = _first_present(post, "Unlinked", "unlinked")
        post_link = _first_present(post, "PostLink", "postLink", "post_link")

        if link_id or _is_truthy(requirement_linked) or post_link:
            bucket["linked"] = True
        if _is_truthy(requirement_linked):
            bucket["requirement_linked"] = True
        if _is_truthy(unlinked):
            bucket["unlinked"] = True

        parsed_date = _parse_date(post_date)
        if parsed_date and (
            bucket["last_post_date"] is None or parsed_date > bucket["last_post_date"]
        ):
            bucket["last_post_date"] = parsed_date

    return by_publisher


def _aggregate_conversions(
    conversions: list[dict[str, Any]],
    start: date,
    end: date,
) -> dict[str, dict[str, Any]]:
    by_publisher: dict[str, dict[str, Any]] = {}
    for conversion in conversions:
        publisher_id = str(
            _first_present(
                conversion,
                "PublisherId",
                "publisherId",
                "publisher_id",
                "PartnerId",
                "partnerId",
                default="",
            )
        )
        if not publisher_id:
            continue

        conversion_date = _first_present(
            conversion,
            "DateSubmitted",
            "dateSubmitted",
            "ConversionDate",
            "conversionDate",
            "CreatedAt",
            "createdAt",
            "StartDate",
            "startDate",
        )
        if not _in_quarter(conversion_date, start, end):
            continue

        revenue = _to_float(
            _first_present(
                conversion,
                "Revenue",
                "revenue",
                "Sales",
                "sales",
                "Commission",
                "commission",
                "EarnedMedia",
                "earnedMedia",
                "SocialMediaValue",
                "socialMediaValue",
                "PaidSpend",
                "paidSpend",
            )
        )
        conversions_count = _to_int(
            _first_present(
                conversion,
                "Conversions",
                "conversions",
                "PaidOffsiteConversions",
                "paidOffsiteConversions",
                "PaidOnsiteConversions",
                "paidOnsiteConversions",
                "Orders",
                "orders",
            )
        )
        clicks = _to_int(_first_present(conversion, "Clicks", "clicks", "LinkClicks", "linkClicks"))

        bucket = by_publisher.setdefault(
            publisher_id,
            {"revenue": 0.0, "conversions": 0, "clicks": 0},
        )
        bucket["revenue"] += revenue
        bucket["conversions"] += max(conversions_count, 1 if revenue > 0 else 0)
        bucket["clicks"] += clicks

    return by_publisher


def build_creator_activation_records(
    publishers: list[dict[str, Any]],
    posts: list[dict[str, Any]],
    conversions: list[dict[str, Any]],
    year: int,
    quarter: int,
) -> list[dict[str, Any]]:
    start, end = get_quarter_date_range(year, quarter)
    publisher_map = _normalize_publishers(publishers)
    post_map = _aggregate_posts(posts, start, end)
    conversion_map = _aggregate_conversions(conversions, start, end)

    records: list[dict[str, Any]] = []
    all_ids = set(publisher_map) | set(post_map) | set(conversion_map)

    for publisher_id in sorted(all_ids):
        publisher = publisher_map.get(publisher_id, {})
        post_stats = post_map.get(publisher_id, {})
        conversion_stats = conversion_map.get(publisher_id, {})

        posted = post_stats.get("post_count", 0) > 0
        linked = bool(
            post_stats.get("linked")
            or post_stats.get("requirement_linked")
            or conversion_stats.get("clicks", 0) > 0
        )
        clicked = (post_stats.get("link_clicks", 0) + conversion_stats.get("clicks", 0)) > 0
        revenue = conversion_stats.get("revenue", 0.0)
        generated_revenue = revenue > 0
        converted = conversion_stats.get("conversions", 0) > 0
        active = posted or linked or generated_revenue or clicked or converted

        activation_status = "Active" if active else "Inactive"
        if generated_revenue and posted and linked:
            activation_tier = "Fully Activated"
        elif generated_revenue:
            activation_tier = "Revenue Driver"
        elif posted and linked:
            activation_tier = "Content + Links"
        elif posted:
            activation_tier = "Posted Only"
        elif linked:
            activation_tier = "Linked Only"
        elif clicked:
            activation_tier = "Clicked Only"
        else:
            activation_tier = "Inactive"

        records.append(
            {
                "publisher_id": publisher_id,
                "publisher_name": publisher.get("publisher_name", f"Creator {publisher_id}"),
                "username": publisher.get("username", ""),
                "social_network": publisher.get("social_network", ""),
                "status": publisher.get("status", ""),
                "verified": publisher.get("verified", False),
                "activation_status": activation_status,
                "activation_tier": activation_tier,
                "posted": posted,
                "linked": linked,
                "clicked": clicked,
                "generated_revenue": generated_revenue,
                "converted": converted,
                "post_count": post_stats.get("post_count", 0),
                "clicks": post_stats.get("link_clicks", 0) + conversion_stats.get("clicks", 0),
                "conversions": conversion_stats.get("conversions", 0),
                "revenue": revenue,
                "engagement": post_stats.get("engagement", 0),
                "impressions": post_stats.get("impressions", 0),
                "last_post_date": post_stats.get("last_post_date"),
            }
        )

    return records


def build_activation_summary(
    publishers: list[dict[str, Any]],
    posts: list[dict[str, Any]],
    conversions: list[dict[str, Any]],
    year: int,
    quarter: int,
) -> ActivationSummary:
    records = build_creator_activation_records(publishers, posts, conversions, year, quarter)
    total = len(records)
    active = sum(1 for record in records if record["activation_status"] == "Active")
    inactive = total - active

    return ActivationSummary(
        quarter=quarter_label(year, quarter),
        year=year,
        total_creators=total,
        active_creators=active,
        inactive_creators=inactive,
        posted=sum(1 for record in records if record["posted"]),
        linked=sum(1 for record in records if record["linked"]),
        generated_revenue=sum(1 for record in records if record["generated_revenue"]),
        clicked=sum(1 for record in records if record["clicked"]),
        converted=sum(1 for record in records if record["converted"]),
        verified=sum(1 for record in records if record["verified"]),
        total_revenue=sum(record["revenue"] for record in records),
        total_clicks=sum(record["clicks"] for record in records),
        total_conversions=sum(record["conversions"] for record in records),
        total_posts=sum(record["post_count"] for record in records),
        activation_rate=(active / total * 100) if total else 0.0,
        creator_records=records,
    )
