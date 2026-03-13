# AI ROI Tracker

Track the real business value of your AI investment across OpenAI, Anthropic, GitHub Copilot, and custom models.

## Stack
- **Backend**: Python + FastAPI + SQLite (via SQLModel)
- **Frontend**: React + Vite + Tailwind CSS + Recharts

## Quick Start

### Backend
```bash
cd backend
pip install -r requirements.txt
python seed.py          # optional: seed with 90 days of demo data
uvicorn main:app --reload
```
API runs at http://localhost:8000
Docs at http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Dashboard at http://localhost:5173

## Features

### Dashboard
- Net ROI, value generated, total cost, hours saved — KPI cards
- Daily value vs. cost area chart (last 7/14/30/60/90 days)
- ROI by AI source (bar chart)
- Value by department (pie chart)
- ROI by task type (bar chart)

### Log Event
Manually record any AI usage session with cost + business value (time saved × hourly rate).

### Events Table
Browse all usage events with filters by source and date range.

### Integrations
- **OpenAI** — pull daily token usage + auto-calculate cost
- **Anthropic** — pull token usage + auto-calculate cost
- **GitHub Copilot** — pull seat usage + suggestion acceptance rates
- **Custom/Internal** — webhook endpoint for any internal AI system

## ROI Formula

```
Value = (time_saved_minutes / 60) × hourly_rate_usd
Net ROI = Value - API Cost
ROI % = (Net ROI / API Cost) × 100
```

## Custom Webhook

POST any AI event from internal systems:
```bash
curl -X POST http://localhost:8000/integrations/custom/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "my-internal-model",
    "department": "Engineering",
    "task_type": "code",
    "input_tokens": 500,
    "output_tokens": 200,
    "cost_usd": 0.002,
    "time_saved_minutes": 20,
    "hourly_rate_usd": 75
  }'
```
