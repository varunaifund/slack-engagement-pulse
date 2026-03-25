<div align="center">

# Slack Engagement Pulse

### AI-powered Slack analytics that detects team burnout before it becomes a problem.

[![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?style=flat-square&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Slack](https://img.shields.io/badge/Slack_API-SDK_3.x-4A154B?style=flat-square&logo=slack&logoColor=white)](https://api.slack.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--3.5-412991?style=flat-square&logo=openai&logoColor=white)](https://openai.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=flat-square&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)](LICENSE)

</div>

---

## Overview

Slack Engagement Pulse monitors team communication patterns across Slack channels and surfaces early warning signals for burnout, disengagement, and morale decline — all without storing any personal data or message content.

It combines **GPT-3.5 sentiment analysis** with VADER/TextBlob fallback, emoji reaction scoring, engagement trend calculations, and a configurable burnout risk model. Results are surfaced through a **real-time Flask web dashboard** or a **CLI tool**, with reports exported as HTML or JSON.

---

## Features

| Category | Capability |
|---|---|
| **AI Analysis** | GPT-3.5-turbo sentiment analysis with workplace-aware prompting; automatic fallback to VADER + TextBlob |
| **Engagement Metrics** | Daily scores weighted across message volume, reactions, emoji usage, and active-hour spread |
| **Burnout Detection** | Multi-factor risk model scoring consecutive negative days, sentiment decline, engagement drops, and message inactivity |
| **Trend Analysis** | Linear trend direction and percentage change per channel over configurable windows |
| **Activity Patterns** | Peak hour and peak day detection across all monitored channels |
| **Web Dashboard** | Flask + Socket.IO real-time dashboard with live progress updates during analysis |
| **Reports** | JSON and HTML report export with per-channel breakdowns and actionable recommendations |
| **Data Storage** | SQLite with automatic retention-based cleanup; no raw messages or user identities stored |
| **Privacy-First** | Only aggregated, anonymized metrics are persisted |
| **CLI Support** | Full-featured command-line interface for scripted or scheduled runs |

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                         Entry Points                             │
│                 app.py (web)  │  run.py (CLI)                    │
└──────────────────┬────────────┴──────────────┬───────────────────┘
                   │                           │
                   ▼                           ▼
        ┌─────────────────────────────────────────────┐
        │            EngagementAnalyzer               │
        │         (orchestrates all components)       │
        └────┬──────────┬──────────┬──────────┬───────┘
             │          │          │          │
             ▼          ▼          ▼          ▼
   ┌──────────────┐ ┌─────────┐ ┌──────────┐ ┌──────────────┐
   │ SlackData    │ │Sentiment│ │Engagement│ │  Burnout     │
   │ Collector    │ │Analyzer │ │ Tracker  │ │  Detector    │
   │              │ │         │ │          │ │              │
   │ Slack SDK    │ │ GPT-3.5 │ │ Pandas   │ │ Risk Scoring │
   │ Paginated    │ │ VADER   │ │ Trends   │ │ Thresholds   │
   │ history +    │ │ TextBlob│ │ Patterns │ │ Recommends   │
   │ reactions    │ │ Emojis  │ │          │ │              │
   └──────────────┘ └─────────┘ └──────────┘ └──────────────┘
             │                                       │
             ▼                                       ▼
   ┌──────────────┐                       ┌──────────────────┐
   │ DataStorage  │                       │ ReportGenerator  │
   │              │                       │                  │
   │ SQLite (5    │                       │ JSON / HTML      │
   │ tables)      │                       │ reports          │
   │ Auto-cleanup │                       │                  │
   └──────────────┘                       └──────────────────┘
```

**Data flow:** Slack messages are fetched and immediately analyzed — raw text is never written to disk. Only the resulting numeric scores, trends, and risk flags are stored in SQLite.

---

## Tech Stack

- **Backend:** Python 3.8+, Flask 2.3, Flask-SocketIO
- **Slack:** `slack-sdk` 3.x — conversations history, reactions, channel listing
- **AI/NLP:** OpenAI GPT-3.5-turbo, VADER Sentiment, TextBlob
- **Data:** SQLite via stdlib `sqlite3`, Pandas for trend calculations
- **Realtime:** Socket.IO for live progress streaming to the dashboard
- **Reporting:** Plotly (charts), custom HTML/JSON report templates
- **Config:** `python-dotenv` + JSON config file with env-variable overrides

---

## Prerequisites

- Python 3.8+
- A Slack Bot Token with these OAuth scopes:
  - `channels:history`
  - `channels:read`
  - `reactions:read`
  - `users:read`
- An OpenAI API key (optional — the system falls back to VADER if not provided)

---

## Installation

```bash
# 1. Clone the repository
git clone https://github.com/your-username/slack-engagement-pulse.git
cd slack-engagement-pulse

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS/Linux
# venv\Scripts\activate         # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set up environment variables
cp .env.example .env
# Edit .env and add your keys:
#   SLACK_BOT_TOKEN=xoxb-...
#   OPENAI_API_KEY=sk-...
#   FLASK_SECRET_KEY=your-random-secret

# 5. Set up configuration
cp config.example.json config.json
# Edit config.json and set your monitored channels
```

---

## Configuration

`config.json` controls which channels are monitored and all analysis parameters:

```json
{
  "monitored_channels": ["#general", "#engineering", "#product"],
  "analysis_days": 7,
  "burnout_threshold": -0.3,
  "consecutive_negative_days": 3,
  "engagement_drop_threshold": 0.5,
  "database": {
    "path": "./data/engagement.db",
    "retention_days": 30
  },
  "reports": {
    "formats": ["json", "html"]
  }
}
```

All settings can also be overridden via environment variables:

| Variable | Description |
|---|---|
| `SLACK_BOT_TOKEN` | Slack bot OAuth token (required) |
| `OPENAI_API_KEY` | OpenAI key for GPT analysis (optional) |
| `FLASK_SECRET_KEY` | Flask session secret key |
| `ANALYSIS_DAYS` | Override default analysis window |
| `BURNOUT_THRESHOLD` | Sentiment score below which burnout is flagged |
| `MONITORED_CHANNELS` | Comma-separated channel list |
| `LOG_LEVEL` | `DEBUG`, `INFO`, `WARNING`, or `ERROR` |

---

## Usage

### Web Dashboard

```bash
python app.py
# Open http://localhost:5000
```

The dashboard provides:
- **System status panel** — Slack connection health, GPT availability, database stats
- **One-click analysis** — choose 7, 14, or 30-day windows
- **Live progress bar** — real-time Socket.IO updates as each pipeline stage completes
- **Results view** — sentiment scores, engagement metrics, burnout alerts, channel breakdown
- **Report management** — download or view generated HTML/JSON reports in-browser

### CLI

```bash
# Run full analysis with default settings
python run.py

# Analyze the last 14 days
python run.py --days 14

# Test Slack API connectivity only
python run.py --test-connection

# Run without generating reports
python run.py --no-reports

# View database statistics
python run.py --db-stats

# Use a custom config file
python run.py --config /path/to/config.json
```

### Example CLI output

```
============================================================
SLACK EMPLOYEE ENGAGEMENT PULSE - SUMMARY
============================================================
Analysis Date: 2025-03-20
Days Analyzed: 7
Total Messages: 342
Channels: #general, #engineering, #product

Overall Sentiment: 0.187
Overall Engagement: 0.523

Sentiment Breakdown:
  Positive: 61.4%
  Neutral:  28.9%
  Negative:  9.7%

No burnout risks detected
============================================================

Reports generated:
  - reports/engagement_report_20250320_143022.json
  - reports/engagement_dashboard_20250320_143022.html
```

---

## Project Structure

```
slack-engagement-pulse/
├── app.py                        # Flask web application + Socket.IO server
├── run.py                        # CLI entry point
├── config.example.json           # Configuration template
├── requirements.txt
├── .env.example                  # Environment variable template
├── src/
│   ├── engagement_analyzer.py    # Main orchestrator — wires all components together
│   ├── slack_data_collector.py   # Slack API — channel history, reactions, pagination
│   ├── sentiment_analyzer.py     # Text + emoji sentiment with GPT/VADER routing
│   ├── gpt_sentiment_analyzer.py # OpenAI GPT-3.5 sentiment analysis with fallback parsing
│   ├── engagement_tracker.py     # Daily metrics, trend calculation, activity patterns
│   ├── burnout_detector.py       # Multi-factor burnout risk scoring + recommendations
│   ├── report_generator.py       # HTML and JSON report generation
│   ├── data_storage.py           # SQLite persistence + retention-based cleanup
│   └── config_manager.py         # Config loading, env overrides, validation
├── data/                         # SQLite database (auto-created, gitignored)
├── logs/                         # Application logs (auto-created, gitignored)
└── reports/                      # Generated reports (auto-created, gitignored)
```

---

## API Reference

The Flask application exposes a REST + WebSocket API:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/` | Web dashboard |
| `GET` | `/api/status` | System health — Slack connection, analyzer state, DB stats |
| `POST` | `/api/analyze` | Start analysis (`{"days": 7}`) |
| `GET` | `/api/results` | Latest analysis results |
| `GET` | `/api/reports` | List generated reports |
| `GET` | `/api/reports/<filename>` | Download a report file |
| `GET` | `/api/reports/<filename>/view` | View report in browser |

**WebSocket events** (Socket.IO):

| Event | Direction | Payload |
|---|---|---|
| `connected` | server → client | Connection confirmation |
| `analysis_progress` | server → client | `{stage, message, progress, results?}` |

---

## Privacy & Security

- **No raw message storage** — message text is analyzed in-memory and immediately discarded
- **No user identities** — usernames and user IDs are never stored
- **Aggregated only** — SQLite stores only numeric scores, counts, and trend directions per channel per day
- **Local by default** — all data stays on your own infrastructure
- **Secret management** — all credentials loaded from environment variables via `.env`; `config.json` and `.env` are gitignored

---

## License

MIT
