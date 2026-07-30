"""Load CreatorIQ credentials from Streamlit secrets."""

from __future__ import annotations

import streamlit as st


def get_creatoriq_credentials() -> tuple[str, str]:
    """Return API key and org name from st.secrets, or empty strings if not configured."""
    try:
        creatoriq = st.secrets["creatoriq"]
        api_key = str(creatoriq.get("api_key", "") or "")
        org_name = str(creatoriq.get("org_name", "") or "")
        return api_key, org_name
    except (KeyError, FileNotFoundError, AttributeError):
        return "", ""


def credentials_configured() -> bool:
    api_key, _ = get_creatoriq_credentials()
    return bool(api_key and api_key != "your_api_key_here")
