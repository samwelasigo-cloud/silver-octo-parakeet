import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# ================= CONFIG =================
# Get API_KEY from Streamlit secrets
try:
    API_KEY = st.secrets["API_KEY"]
except KeyError:
    raise ValueError("API_KEY not found. Add it to .streamlit/secrets.toml")

BASE_URL = "https://v3.football.api-sports.io"

headers = {
    "x-apisports-key": API_KEY
}

today = datetime.today().strftime("%Y-%m-%d")

# ================= LEAGUE NAME MAPPING =================
LEAGUE_MAP = {
    "Premier League": "EPL",
    "La Liga": "LaLiga",
    "Serie A": "Serie A",
    "Bundesliga": "Bundesliga",
    "Ligue 1": "Ligue 1"
}

# ================= HELPER: GOALS LAST 5 =================
def goals_last_5(team_id):
    url = f"{BASE_URL}/fixtures?team={team_id}&last=5"
    response = requests.get(url, headers=headers)
    data = response.json().get("response", [])

    goals = 0
    for match in data:
        if match["teams"]["home"]["id"] == team_id:
            goals += match["goals"]["home"] or 0
        else:
            goals += match["goals"]["away"] or 0

    return goals

# ================= FETCH TODAY'S FIXTURES =================
fixtures_url = f"{BASE_URL}/fixtures?date={today}"
fixtures_response = requests.get(fixtures_url, headers=headers)
fixtures = fixtures_response.json().get("response", [])

rows = []

for match in fixtures:
    raw_league = match["league"]["name"]
    league = LEAGUE_MAP.get(raw_league)

    # Skip unsupported leagues
    if league is None:
        continue

    home_team = match["teams"]["home"]["name"]
    away_team = match["teams"]["away"]["name"]

    home_id = match["teams"]["home"]["id"]
    away_id = match["teams"]["away"]["id"]

    print(f"Fetching form: {home_team} vs {away_team}")

    rows.append({
        "date": today,
        "league": league,
        "home_team": home_team,
        "away_team": away_team,
        "home_scored_last5": goals_last_5(home_id),
        "away_scored_last5": goals_last_5(away_id)
    })

# ================= CREATE FIXTURES DF =================
fixtures_df = pd.DataFrame(rows)

if fixtures_df.empty:
    print("⚠️ No supported fixtures found for today.")
    exit()

# ================= LOAD LEAGUE STATS =================
league_stats = pd.read_csv("league_stats.csv")

# ================= MERGE =================
df = fixtures_df.merge(
    league_stats,
    on="league",
    how="left"
)

# ================= SAFE FALLBACKS =================
df["league_btts_rate"] = df["league_btts_rate"].fillna(55)
df["league_over25_rate"] = df["league_over25_rate"].fillna(58)

# ================= SAVE =================
df.to_csv("matches.csv", index=False)

print("✅ matches.csv generated successfully")


