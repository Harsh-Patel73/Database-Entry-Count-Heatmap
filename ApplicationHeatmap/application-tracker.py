import requests
import datetime
import os
import calendar
from dotenv import load_dotenv
import plotly.graph_objects as go
from dateutil.parser import isoparse

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if NOTION_TOKEN is None or DATABASE_ID is None:
    raise ValueError("NOTION_TOKEN or DATABASE_ID not set.")

NOTION_API_URL = f"https://api.notion.com/v1/databases/{DATABASE_ID}/query"
HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28",
    "Content-Type": "application/json"
}

def get_applications():
    all_results = []
    has_more = True
    next_cursor = None
    while has_more:
        payload = {"page_size": 100}
        if next_cursor:
            payload["start_cursor"] = next_cursor
        res = requests.post(NOTION_API_URL, headers=HEADERS, json=payload)
        res.raise_for_status()
        data = res.json()
        all_results.extend(data["results"])
        has_more = data.get("has_more", False)
        next_cursor = data.get("next_cursor")
    return all_results

def count_per_day(applications):
    counts = {}
    for app in applications:
        props = app.get("properties", {})
        date_field = props.get("Application Date", {}).get("date")
        if not date_field:
            continue
        date_str = isoparse(date_field["start"]).date().isoformat()
        counts[date_str] = counts.get(date_str, 0) + 1
    print(f"[DEBUG] Daily counts: {counts}")
    return counts

def draw_interactive_grid(counts, output_path="ApplicationHeatmap/interactive_grid.html"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    today = datetime.date.today()
    start_date = today - datetime.timedelta(days=59)
    dates = [start_date + datetime.timedelta(days=i) for i in range(60)]
    total_weeks = (len(dates) + 6) // 7


    z = [[0 for _ in range(total_weeks)] for _ in range(7)]
    hover_text = [[None for _ in range(total_weeks)] for _ in range(7)]

    for i, d in enumerate(dates):
        week_idx = i // 7
        day_idx = d.weekday()
        val = counts.get(d.isoformat(), 0)
        z[day_idx][week_idx] = min(val, 25)
        hover_text[day_idx][week_idx] = f"{d.strftime('%Y-%m-%d')}: {val} application{'s' if val != 1 else ''}"

    colorscale = [
        [0.0, "#ebedf0"],
        [0.25, "#fa1900"],
        [0.5, "#eeeb49"], 
        [1.0, "#2ecc71"]  
    ]

    fig = go.Figure(go.Heatmap(
        z=z,
        text=hover_text,
        hoverinfo="text",
        x=[f"Week {i+1}" for i in range(total_weeks)],
        y=[calendar.day_name[i] for i in range(7)],
        colorscale=colorscale,
        showscale=False,
        xgap=2,
        ygap=2,
        zmin=0,
        zmax=25,
    ))

    fig.update_yaxes(autorange="reversed", showgrid=False, zeroline=False)
    fig.update_xaxes(showgrid=False, zeroline=False, visible=True)

    fig.update_layout(
        width=total_weeks * 25,
        height=7 * 25,
        margin=dict(l=10, r=10, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
    )

    fig.write_html(output_path, include_plotlyjs="cdn", full_html=True, config={"displayModeBar": False})
    print(f"Interactive grid saved to {output_path}")

if __name__ == "__main__":
    applications = get_applications()
    print(f"[DEBUG] Fetched {len(applications)} applications from Notion.")
    daily_counts = count_per_day(applications)
    draw_interactive_grid(daily_counts)
