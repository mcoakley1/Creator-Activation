"""Streamlit dashboard for quarterly creator program activation tracking."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.api.client import CreatorIQAPIError, CreatorIQClient
from src.config import credentials_configured, get_creatoriq_credentials
from src.data.mock_data import generate_demo_data
from src.metrics.activation import build_activation_summary, get_quarter_date_range, quarter_label

st.set_page_config(
    page_title="Creator Activation Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CURRENT_YEAR = date.today().year
QUARTER_OPTIONS = {1: "Q1 (Jan–Mar)", 2: "Q2 (Apr–Jun)", 3: "Q3 (Jul–Sep)", 4: "Q4 (Oct–Dec)"}


def _metric_card(label: str, value: str | int | float, help_text: str = "") -> None:
    st.metric(label=label, value=value, help=help_text)


@st.cache_data(show_spinner=False, ttl=300)
def load_live_data(
    api_key: str,
    org_name: str,
    campaign_id: str | None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    client = CreatorIQClient(api_key=api_key, org_name=org_name or None)
    campaigns = client.get_campaigns()

    if campaign_id:
        publishers = client.get_campaign_publishers(campaign_id)
        activity = client.get_campaign_activity(campaign_id)
        posts = [item for item in activity if _looks_like_post(item)]
        if not posts:
            posts = activity
    else:
        publishers = client.get_publishers()
        posts = []
        for publisher in publishers[:50]:
            publisher_id = publisher.get("PublisherId") or publisher.get("id") or publisher.get("Id")
            if publisher_id:
                try:
                    posts.extend(client.get_publisher_posts(publisher_id))
                except CreatorIQAPIError:
                    continue

    conversions = client.get_conversions()
    return publishers, posts, conversions, campaigns


def _looks_like_post(record: dict[str, Any]) -> bool:
    post_keys = {"Post", "PostId", "postId", "PostType", "postType", "DateSubmitted", "dateSubmitted"}
    return bool(post_keys.intersection(record.keys()))


@st.cache_data(show_spinner=False)
def load_demo_data(year: int, quarter: int):
    return generate_demo_data(year, quarter)


def _activation_funnel_chart(summary) -> go.Figure:
    stages = ["In Program", "Posted", "Linked", "Clicked", "Revenue"]
    values = [
        summary.total_creators,
        summary.posted,
        summary.linked,
        summary.clicked,
        summary.generated_revenue,
    ]
    fig = go.Figure(go.Funnel(y=stages, x=values, textinfo="value+percent initial"))
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=360)
    return fig


def _tier_chart(records: list[dict[str, Any]]) -> go.Figure:
    df = pd.DataFrame(records)
    if df.empty:
        return px.bar(title="No data available")
    counts = df["activation_tier"].value_counts().reset_index()
    counts.columns = ["activation_tier", "count"]
    fig = px.pie(counts, names="activation_tier", values="count", hole=0.45)
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=360)
    return fig


def _monthly_activity_chart(posts: list[dict[str, Any]], year: int, quarter: int) -> go.Figure:
    start, end = get_quarter_date_range(year, quarter)
    df = pd.DataFrame(posts)
    if df.empty or "DateSubmitted" not in df.columns:
        for alt in ("dateSubmitted", "StartDate", "startDate"):
            if alt in df.columns:
                df["DateSubmitted"] = df[alt]
                break

    if df.empty or "DateSubmitted" not in df.columns:
        return px.bar(title="No post activity in selected quarter")

    df["post_date"] = pd.to_datetime(df["DateSubmitted"], errors="coerce")
    df = df.dropna(subset=["post_date"])
    df = df[(df["post_date"].dt.date >= start) & (df["post_date"].dt.date <= end)]
    if df.empty:
        return px.bar(title="No post activity in selected quarter")

    df["month"] = df["post_date"].dt.to_period("M").astype(str)
    monthly = df.groupby("month").size().reset_index(name="posts")
    fig = px.bar(monthly, x="month", y="posts", labels={"month": "Month", "posts": "Posts"})
    fig.update_layout(margin=dict(l=20, r=20, t=30, b=20), height=320)
    return fig


def render_sidebar() -> dict[str, Any]:
    st.sidebar.header("Settings")

    use_demo = st.sidebar.toggle("Demo mode", value=True, help="Explore the dashboard with sample data")

    api_key, org_name = get_creatoriq_credentials()

    if not use_demo:
        if credentials_configured():
            st.sidebar.success("CreatorIQ credentials loaded from secrets.")
        else:
            st.sidebar.warning(
                "Add your API key to `.streamlit/secrets.toml` (see `.streamlit/secrets.toml.example`)."
            )

    year = st.sidebar.selectbox("Year", options=list(range(CURRENT_YEAR - 2, CURRENT_YEAR + 2)), index=2)
    quarter = st.sidebar.selectbox(
        "Quarter",
        options=list(QUARTER_OPTIONS.keys()),
        format_func=lambda q: QUARTER_OPTIONS[q],
        index=((date.today().month - 1) // 3),
    )

    campaign_id = None
    campaigns: list[dict[str, Any]] = []

    if not use_demo and api_key:
        try:
            client = CreatorIQClient(api_key=api_key, org_name=org_name or None)
            campaigns = client.get_campaigns()
        except CreatorIQAPIError as exc:
            st.sidebar.error(f"Could not load campaigns: {exc}")

    if campaigns:
        campaign_options = {"All campaigns": None}
        for campaign in campaigns:
            cid = campaign.get("CampaignId") or campaign.get("id") or campaign.get("Id")
            name = campaign.get("CampaignName") or campaign.get("name") or f"Campaign {cid}"
            if cid:
                campaign_options[f"{name} ({cid})"] = str(cid)
        selected = st.sidebar.selectbox("Campaign filter", options=list(campaign_options.keys()))
        campaign_id = campaign_options[selected]

    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Activation is defined as any creator who posted, linked affiliate content, "
        "generated clicks, or earned revenue during the selected quarter."
    )

    return {
        "use_demo": use_demo,
        "api_key": api_key,
        "org_name": org_name,
        "year": year,
        "quarter": quarter,
        "campaign_id": campaign_id,
    }


def main() -> None:
    settings = render_sidebar()

    st.title("Creator Program Activation Dashboard")
    st.caption(
        "Track quarterly creator activation across posting, linking, clicks, and revenue using CreatorIQ data."
    )

    publishers: list[dict[str, Any]] = []
    posts: list[dict[str, Any]] = []
    conversions: list[dict[str, Any]] = []
    campaigns: list[dict[str, Any]] = []

    if settings["use_demo"]:
        publishers, posts, conversions, campaigns = load_demo_data(settings["year"], settings["quarter"])
        st.info(
            "Demo mode is on. Add your CreatorIQ API key to `.streamlit/secrets.toml` "
            "and turn off demo mode to load live program data."
        )
    else:
        if not credentials_configured():
            st.warning(
                "CreatorIQ credentials are not configured. Copy `.streamlit/secrets.toml.example` "
                "to `.streamlit/secrets.toml`, add your API key, then restart the app. "
                "Or enable demo mode to explore sample data."
            )
            st.stop()

        try:
            with st.spinner("Loading CreatorIQ data..."):
                publishers, posts, conversions, campaigns = load_live_data(
                    settings["api_key"],
                    settings["org_name"],
                    settings["campaign_id"],
                )
        except CreatorIQAPIError as exc:
            st.error(f"CreatorIQ API error: {exc}")
            if exc.status_code == 403:
                st.info(
                    "A 403 usually means the API key is invalid or your account lacks access to this endpoint. "
                    "Contact your CreatorIQ representative or support@creatoriq.com."
                )
            st.stop()

    summary = build_activation_summary(
        publishers=publishers,
        posts=posts,
        conversions=conversions,
        year=settings["year"],
        quarter=settings["quarter"],
    )

    st.subheader(quarter_label(settings["year"], settings["quarter"]))
    start, end = get_quarter_date_range(settings["year"], settings["quarter"])
    st.caption(f"Reporting period: {start.isoformat()} to {end.isoformat()}")

    top_cols = st.columns(5)
    with top_cols[0]:
        _metric_card("Total Creators", summary.total_creators)
    with top_cols[1]:
        _metric_card("Active", summary.active_creators, "Posted, linked, clicked, or generated revenue")
    with top_cols[2]:
        _metric_card("Inactive", summary.inactive_creators, "No posting, linking, clicks, or revenue")
    with top_cols[3]:
        _metric_card("Activation Rate", f"{summary.activation_rate:.1f}%")
    with top_cols[4]:
        _metric_card("Total Revenue", f"${summary.total_revenue:,.2f}")

    metric_cols = st.columns(6)
    with metric_cols[0]:
        _metric_card("Posted", summary.posted)
    with metric_cols[1]:
        _metric_card("Linked", summary.linked, "Affiliate links or requirement-linked posts")
    with metric_cols[2]:
        _metric_card("Clicked", summary.clicked)
    with metric_cols[3]:
        _metric_card("Generated Revenue", summary.generated_revenue)
    with metric_cols[4]:
        _metric_card("Converted", summary.converted)
    with metric_cols[5]:
        _metric_card("Verified", summary.verified)

    chart_left, chart_right = st.columns(2)
    with chart_left:
        st.plotly_chart(_activation_funnel_chart(summary), use_container_width=True)
    with chart_right:
        st.plotly_chart(_tier_chart(summary.creator_records), use_container_width=True)

    st.plotly_chart(
        _monthly_activity_chart(posts, settings["year"], settings["quarter"]),
        use_container_width=True,
    )

    st.subheader("Creator Activation Detail")
    detail_df = pd.DataFrame(summary.creator_records)
    if not detail_df.empty:
        status_filter = st.multiselect(
            "Filter by activation status",
            options=sorted(detail_df["activation_status"].unique()),
            default=list(sorted(detail_df["activation_status"].unique())),
        )
        tier_filter = st.multiselect(
            "Filter by activation tier",
            options=sorted(detail_df["activation_tier"].unique()),
            default=list(sorted(detail_df["activation_tier"].unique())),
        )
        filtered = detail_df[
            detail_df["activation_status"].isin(status_filter) & detail_df["activation_tier"].isin(tier_filter)
        ]

        display_cols = [
            "publisher_name",
            "username",
            "social_network",
            "activation_status",
            "activation_tier",
            "posted",
            "linked",
            "clicked",
            "generated_revenue",
            "post_count",
            "clicks",
            "conversions",
            "revenue",
            "verified",
            "last_post_date",
        ]
        st.dataframe(
            filtered[display_cols].sort_values(["activation_status", "revenue"], ascending=[True, False]),
            use_container_width=True,
            hide_index=True,
        )

        csv = filtered.to_csv(index=False).encode("utf-8")
        st.download_button(
            "Download CSV",
            data=csv,
            file_name=f"creator_activation_{settings['year']}_Q{settings['quarter']}.csv",
            mime="text/csv",
        )
    else:
        st.info("No creator records found for the selected period.")

    with st.expander("Data sources & activation definitions"):
        st.markdown(
            """
            **CreatorIQ endpoints used**
            - `GET /api/v1/campaigns` — list campaigns
            - `GET /api/v1/publishers` — creator roster
            - `GET /api/v1/campaign/{id}/publishers` — campaign-specific creators
            - `GET /api/v1/campaign/{id}/activity` — campaign posts and activity
            - `GET /api/v1/publisher/{id}/posts` — per-creator posts
            - `GET /api/v1/conversions` — revenue and conversion data

            **Activation tiers**
            - *Fully Activated* — posted, linked, and generated revenue
            - *Revenue Driver* — generated revenue (may or may not have posted/linked)
            - *Content + Links* — posted and linked affiliate content
            - *Posted Only* — published content without links or revenue
            - *Linked Only* — affiliate links or clicks without posts
            - *Clicked Only* — link clicks without posts or revenue
            - *Inactive* — no measurable activation activity in the quarter

            **Fields leveraged from CreatorIQ**
            Post dates (`DateSubmitted`), link status (`LinkId`, `RequirementLinked`, `Unlinked`),
            engagement (`Clicks`, `LinkClicks`), and commerce metrics (`Revenue`, `Conversions`, `Commission`).
            """
        )

    if campaigns:
        with st.expander("Campaigns loaded"):
            st.dataframe(pd.DataFrame(campaigns), use_container_width=True, hide_index=True)


if __name__ == "__main__":
    main()
