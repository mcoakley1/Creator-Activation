"""Demo data for exploring the dashboard without live API credentials."""

from __future__ import annotations

from datetime import date, timedelta
from typing import Any


def _quarter_months(year: int, quarter: int) -> list[date]:
    start_month = (quarter - 1) * 3 + 1
    return [date(year, start_month + offset, 15) for offset in range(3)]


def generate_demo_data(
    year: int, quarter: int
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    months = _quarter_months(year, quarter)

    publishers = [
        {"PublisherId": 1001, "PublisherName": "Alex Rivera", "UserName": "alexr_creates", "SocialNetwork": "Instagram", "Status": "Active", "Verified": True},
        {"PublisherId": 1002, "PublisherName": "Jordan Kim", "UserName": "jordankim", "SocialNetwork": "TikTok", "Status": "Active", "Verified": True},
        {"PublisherId": 1003, "PublisherName": "Sam Patel", "UserName": "sampatel", "SocialNetwork": "YouTube", "Status": "Active", "Verified": False},
        {"PublisherId": 1004, "PublisherName": "Taylor Brooks", "UserName": "taylorb", "SocialNetwork": "Instagram", "Status": "Active", "Verified": True},
        {"PublisherId": 1005, "PublisherName": "Casey Nguyen", "UserName": "caseynguyen", "SocialNetwork": "TikTok", "Status": "Active", "Verified": False},
        {"PublisherId": 1006, "PublisherName": "Morgan Lee", "UserName": "morganlee", "SocialNetwork": "Instagram", "Status": "Active", "Verified": True},
        {"PublisherId": 1007, "PublisherName": "Riley Chen", "UserName": "rileychen", "SocialNetwork": "YouTube", "Status": "Active", "Verified": True},
        {"PublisherId": 1008, "PublisherName": "Drew Martinez", "UserName": "drewm", "SocialNetwork": "Instagram", "Status": "Inactive", "Verified": False},
        {"PublisherId": 1009, "PublisherName": "Jamie O'Connor", "UserName": "jamieoc", "SocialNetwork": "TikTok", "Status": "Inactive", "Verified": False},
        {"PublisherId": 1010, "PublisherName": "Quinn Adams", "UserName": "quinnadams", "SocialNetwork": "Instagram", "Status": "Inactive", "Verified": False},
        {"PublisherId": 1011, "PublisherName": "Avery Stone", "UserName": "averystone", "SocialNetwork": "YouTube", "Status": "Active", "Verified": True},
        {"PublisherId": 1012, "PublisherName": "Parker Walsh", "UserName": "parkerw", "SocialNetwork": "TikTok", "Status": "Active", "Verified": False},
        {"PublisherId": 1013, "PublisherName": "Skyler James", "UserName": "skylerj", "SocialNetwork": "Instagram", "Status": "Active", "Verified": True},
        {"PublisherId": 1014, "PublisherName": "Reese Holland", "UserName": "reeseh", "SocialNetwork": "TikTok", "Status": "Inactive", "Verified": False},
        {"PublisherId": 1015, "PublisherName": "Blake Foster", "UserName": "blakef", "SocialNetwork": "YouTube", "Status": "Inactive", "Verified": False},
    ]

    posts: list[dict[str, Any]] = [
        {"PublisherId": 1001, "DateSubmitted": months[0].isoformat(), "PostType": "Reel", "LinkId": "LNK-1001", "RequirementLinked": True, "Clicks": 420, "LinkClicks": 310, "Engagement": 1800, "Impressions": 22000},
        {"PublisherId": 1001, "DateSubmitted": months[2].isoformat(), "PostType": "Story", "LinkId": "LNK-1001B", "RequirementLinked": True, "Clicks": 180, "LinkClicks": 140, "Engagement": 900, "Impressions": 11000},
        {"PublisherId": 1002, "DateSubmitted": months[1].isoformat(), "PostType": "Video", "LinkId": "LNK-1002", "RequirementLinked": True, "Clicks": 890, "LinkClicks": 650, "Engagement": 4200, "Impressions": 85000},
        {"PublisherId": 1003, "DateSubmitted": months[0].isoformat(), "PostType": "Video", "RequirementLinked": False, "Clicks": 55, "LinkClicks": 0, "Engagement": 1200, "Impressions": 18000},
        {"PublisherId": 1004, "DateSubmitted": months[1].isoformat(), "PostType": "Post", "LinkId": "LNK-1004", "RequirementLinked": True, "Clicks": 210, "LinkClicks": 175, "Engagement": 950, "Impressions": 14000},
        {"PublisherId": 1005, "DateSubmitted": months[2].isoformat(), "PostType": "Video", "LinkId": "LNK-1005", "RequirementLinked": True, "Clicks": 130, "LinkClicks": 95, "Engagement": 700, "Impressions": 9000},
        {"PublisherId": 1006, "DateSubmitted": months[0].isoformat(), "PostType": "Reel", "RequirementLinked": False, "Clicks": 40, "LinkClicks": 0, "Engagement": 500, "Impressions": 7000},
        {"PublisherId": 1007, "DateSubmitted": months[1].isoformat(), "PostType": "Video", "LinkId": "LNK-1007", "RequirementLinked": True, "Clicks": 560, "LinkClicks": 410, "Engagement": 3100, "Impressions": 42000},
        {"PublisherId": 1011, "DateSubmitted": months[2].isoformat(), "PostType": "Video", "LinkId": "LNK-1011", "RequirementLinked": True, "Clicks": 340, "LinkClicks": 260, "Engagement": 2100, "Impressions": 30000},
        {"PublisherId": 1012, "DateSubmitted": months[1].isoformat(), "PostType": "Video", "RequirementLinked": False, "Clicks": 25, "LinkClicks": 0, "Engagement": 350, "Impressions": 5000},
        {"PublisherId": 1013, "DateSubmitted": months[0].isoformat(), "PostType": "Reel", "LinkId": "LNK-1013", "RequirementLinked": True, "Clicks": 275, "LinkClicks": 210, "Engagement": 1600, "Impressions": 19000},
    ]

    conversions: list[dict[str, Any]] = [
        {"PublisherId": 1001, "DateSubmitted": months[0] + timedelta(days=2), "Revenue": 1240.50, "Conversions": 18, "Clicks": 45},
        {"PublisherId": 1001, "DateSubmitted": months[2] + timedelta(days=1), "Revenue": 680.25, "Conversions": 9, "Clicks": 22},
        {"PublisherId": 1002, "DateSubmitted": months[1] + timedelta(days=3), "Revenue": 2890.00, "Conversions": 34, "Clicks": 88},
        {"PublisherId": 1004, "DateSubmitted": months[1] + timedelta(days=5), "Revenue": 455.75, "Conversions": 7, "Clicks": 15},
        {"PublisherId": 1005, "DateSubmitted": months[2] + timedelta(days=2), "Revenue": 312.00, "Conversions": 5, "Clicks": 11},
        {"PublisherId": 1007, "DateSubmitted": months[1] + timedelta(days=1), "Revenue": 1675.40, "Conversions": 21, "Clicks": 52},
        {"PublisherId": 1011, "DateSubmitted": months[2] + timedelta(days=4), "Revenue": 920.10, "Conversions": 12, "Clicks": 30},
        {"PublisherId": 1013, "DateSubmitted": months[0] + timedelta(days=6), "Revenue": 540.00, "Conversions": 8, "Clicks": 19},
        {"PublisherId": 1006, "DateSubmitted": months[0] + timedelta(days=4), "Revenue": 0.0, "Conversions": 0, "Clicks": 12},
    ]

    campaigns = [
        {"CampaignId": 501, "CampaignName": "Creator Program - Core", "CampaignStatus": "Active"},
        {"CampaignId": 502, "CampaignName": "Creator Program - Seasonal", "CampaignStatus": "Active"},
    ]

    return publishers, posts, conversions, campaigns
