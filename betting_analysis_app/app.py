import streamlit as st
import pandas as pd
import subprocess
from datetime import datetime

# ================= PAGE CONFIG =================
st.set_page_config(
    page_title="⚽ Betting Dashboard",
    layout="wide"
)

st.title("⚽ Today's Betting Analysis Dashboard")
st.caption("Personal betting assistant – mobile optimized")

# ================= DATA REFRESH BUTTON =================
if st.sidebar.button("🔄 Update Today's Data"):
    st.info("Fetching latest matches...")
    subprocess.run(["python", "fetch_data.py"])
    st.success("✅ Data refreshed! Reload the app to see updates.")

# ================= LOAD DATA =================
try:
    df = pd.read_csv("matches.csv")
except FileNotFoundError:
    st.error("matches.csv not found. Run fetch_data.py first.")
    st.stop()

df['date'] = pd.to_datetime(df['date'])
today = pd.Timestamp.today().normalize()
df = df[df['date'] == today]

if df.empty:
    st.warning("No matches found for today. Run fetch_data.py")
    st.stop()

# ================= PROBABILITY FUNCTIONS =================
def btts_probability(row):
    home_rate = row['home_scored_last5'] / 5
    away_rate = row['away_scored_last5'] / 5
    league_rate = row['league_btts_rate'] / 100
    return round(((home_rate + away_rate + league_rate) / 3) * 100, 1)

def over25_probability(row):
    home_rate = row['home_scored_last5'] / 5
    away_rate = row['away_scored_last5'] / 5
    league_rate = row['league_over25_rate'] / 100
    return round(((home_rate + away_rate + league_rate) / 3) * 100, 1)

df['BTTS Probability (%)'] = df.apply(btts_probability, axis=1)
df['Over 2.5 (%)'] = df.apply(over25_probability, axis=1)

# ================= SIGNALS =================
def btts_signal(p):
    if p >= 70:
        return "✅ STRONG"
    elif p >= 55:
        return "⚠️ MEDIUM"
    else:
        return "❌ SKIP"

def over25_signal(p):
    if p >= 65:
        return "✅ STRONG"
    elif p >= 50:
        return "⚠️ MEDIUM"
    else:
        return "❌ SKIP"

df['BTTS Signal'] = df['BTTS Probability (%)'].apply(btts_signal)
df['Over 2.5 Signal'] = df['Over 2.5 (%)'].apply(over25_signal)

# ================= FINAL RECOMMENDATION =================
def final_signal(row):
    if row['BTTS Probability (%)'] >= 70 and row['Over 2.5 (%)'] >= 65:
        return "🔥 BEST BET"
    elif row['BTTS Probability (%)'] >= 60:
        return "✅ BTTS ONLY"
    elif row['Over 2.5 (%)'] >= 60:
        return "⚽ OVER 2.5"
    else:
        return "❌ AVOID"

df['Final Recommendation'] = df.apply(final_signal, axis=1)

# ================= SIDEBAR =================
st.sidebar.header("View Mode")
view_mode = st.sidebar.radio(
    "Select View:",
    ["All Today's Matches", "🔥 Today's Best Bets"]
)

st.sidebar.header("Filters")
btts_filter = st.sidebar.multiselect(
    "BTTS Signal",
    options=df['BTTS Signal'].unique(),
    default=df['BTTS Signal'].unique()
)
over_filter = st.sidebar.multiselect(
    "Over 2.5 Signal",
    options=df['Over 2.5 Signal'].unique(),
    default=df['Over 2.5 Signal'].unique()
)

filtered_df = df[
    df['BTTS Signal'].isin(btts_filter) &
    df['Over 2.5 Signal'].isin(over_filter)
]

best_bets_df = filtered_df[
    (filtered_df['BTTS Probability (%)'] >= 70) |
    (filtered_df['Over 2.5 (%)'] >= 65) |
    (filtered_df['Final Recommendation'] == "🔥 BEST BET")
]

# ================= SLIP GENERATION =================
safe_slip = df[df['Final Recommendation'] == "🔥 BEST BET"].head(2)
moderate_slip = df[df['Final Recommendation'].isin(["🔥 BEST BET", "✅ BTTS ONLY"])].head(4)
risky_slip = df[df['Final Recommendation'] != "❌ AVOID"].head(5)

st.sidebar.header("Slip Generator")
slip_type = st.sidebar.selectbox(
    "Generate Betting Slip:",
    ["None", "🟢 Safe Slip", "🟡 Moderate Slip", "🔴 Risky Slip"]
)

# ================= STYLING =================
def color_signal(df):
    styles = pd.DataFrame('', index=df.index, columns=df.columns)

    if 'BTTS Signal' in df.columns:
        styles['BTTS Signal'] = df['BTTS Signal'].map(
            lambda x: 'background-color:#c6f5c6' if '✅' in x
            else 'background-color:#fff3c2' if '⚠️' in x
            else 'background-color:#f5c6c6'
        )

    if 'Over 2.5 Signal' in df.columns:
        styles['Over 2.5 Signal'] = df['Over 2.5 Signal'].map(
            lambda x: 'background-color:#c6f5c6' if '✅' in x
            else 'background-color:#fff3c2' if '⚠️' in x
            else 'background-color:#f5c6c6'
        )

    if 'Final Recommendation' in df.columns:
        styles['Final Recommendation'] = df['Final Recommendation'].map(
            lambda x: 'background-color:#b6ffb6' if 'BEST' in x
            else 'background-color:#d4f1ff' if 'BTTS' in x
            else 'background-color:#ffe5b4' if 'OVER' in x
            else 'background-color:#ffb6b6'
        )

    return styles

# ================= DISPLAY TABLE + SLIP SIDE-BY-SIDE =================
if view_mode == "🔥 Today's Best Bets":
    st.subheader("🔥 TODAY'S BEST BETS")
    display_df = best_bets_df
else:
    st.subheader("All Today's Matches")
    display_df = filtered_df

# Use columns for side-by-side on desktop; stack on mobile
col1, col2 = st.columns([2, 1])

with col1:
    st.dataframe(display_df.style.apply(color_signal, axis=None), use_container_width=True)

with col2:
    if slip_type != "None":
        if slip_type == "🟢 Safe Slip":
            st.subheader("🟢 SAFE SLIP")
            slip_df = safe_slip
        elif slip_type == "🟡 Moderate Slip":
            st.subheader("🟡 MODERATE SLIP")
            slip_df = moderate_slip
        else:
            st.subheader("🔴 RISKY SLIP")
            slip_df = risky_slip

        if slip_df.empty:
            st.info("No matches qualify for this slip today.")
        else:
            st.dataframe(slip_df.style.apply(color_signal, axis=None), use_container_width=True)

st.caption("⚠️ Personal-use tool. Always bet responsibly.")





