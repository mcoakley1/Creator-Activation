# Creator Activation Dashboard

A Streamlit dashboard for tracking quarterly creator program activation using the [CreatorIQ ExchangeIQ API](https://apidocs.creatoriq.com/).

## What it tracks

For any selected quarter, the dashboard surfaces:

- **Total creators** in the program
- **Active vs. inactive** creators
- **Posted** — creators who published content
- **Linked** — creators with affiliate links or requirement-linked posts
- **Clicked** — creators who drove link clicks
- **Generated revenue** — creators with attributed sales or commissions
- **Converted** — creators with recorded conversions
- **Verified** creators

It also includes an activation funnel, tier breakdown, monthly post activity chart, and a filterable creator detail table with CSV export.

## Quick start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure API credentials (optional)

API keys are stored in **Streamlit secrets** — never in the app code.

Copy the example secrets file and add your CreatorIQ credentials:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
```

Edit `.streamlit/secrets.toml`:

```toml
[creatoriq]
api_key = "your_actual_api_key"
org_name = "your_organization_name"
```

Obtain an API key from your CreatorIQ contact or email support@creatoriq.com.

**Important:** `.streamlit/secrets.toml` is gitignored and should never be committed.

For **Streamlit Community Cloud**, paste the same `[creatoriq]` block in your app's **Secrets** settings in the dashboard.

### 3. Run the app

```bash
streamlit run app.py
```

Open the URL shown in your terminal (typically http://localhost:8501).

## Demo mode

Demo mode is enabled by default so you can explore the dashboard without API credentials. Add your API key to `.streamlit/secrets.toml`, then toggle demo mode off to load live CreatorIQ data.

## CreatorIQ API endpoints

The app uses these ExchangeIQ / Standard CRM API endpoints:

| Endpoint | Purpose |
|----------|---------|
| `GET /api/v1/campaigns` | List campaigns |
| `GET /api/v1/publishers` | Full creator roster |
| `GET /api/v1/campaign/{id}/publishers` | Campaign-specific creators |
| `GET /api/v1/campaign/{id}/activity` | Campaign posts and activity |
| `GET /api/v1/publisher/{id}/posts` | Per-creator posts |
| `GET /api/v1/conversions` | Revenue and conversion data |

Authentication uses an `api-key` header. See the [CreatorIQ API docs](https://apidocs.creatoriq.com/) for full details.

## Activation definitions

A creator is considered **active** in a quarter if they did at least one of the following:

- Published a post (`DateSubmitted` within the quarter)
- Linked affiliate content (`LinkId`, `RequirementLinked`, or `PostLink`)
- Drove link clicks (`LinkClicks`, `Clicks`)
- Generated revenue or conversions (`Revenue`, `Commission`, `Conversions`)

**Inactive** creators are enrolled in the program but had none of the above activity during the selected quarter.

## Project structure

```
app.py                  # Streamlit entry point
src/
  api/client.py         # CreatorIQ API client
  metrics/activation.py # Quarterly activation calculations
  data/mock_data.py     # Demo dataset
requirements.txt
.streamlit/secrets.toml.example
```

## License

MIT
