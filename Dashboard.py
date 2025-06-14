import streamlit as st
import pandas as pd
import os
import datetime

from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

user = os.getenv("user")
password = os.getenv("password")
host = os.getenv("host")
port = os.getenv("port")
dbname = os.getenv("dbname")

# Create SQLAlchemy engine
engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')

def format_duration_hours(h):
    if pd.isnull(h): return "—"
    total_minutes = int(h * 60)
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

def get_today_data(df):
    today = pd.to_datetime(datetime.date.today())
    df['date_only'] = df['workout_date'].dt.normalize()
    return df[df['date_only'] == today]

def generate_recommendation(row):
    if row['avg_overnight_hrv'] < df['avg_overnight_hrv'].quantile(0.25) and row['resting_heart_rate'] < df['resting_heart_rate'].quantile(0.25):
        return "Consider taking an easier session today."
    return "✅ You're good to go."

# ----------------------------
# 📊 LOAD DATA
# ----------------------------
st.set_page_config(page_title="Sleep & Recovery Dashboard", layout="wide")

@st.cache_data
@st.cache_data
def load_data():
    query = """
        SELECT
            workout_date,
            avg_overnight_hrv,
            sleep_duration,
            sleep_score,
            resting_heart_rate
        FROM sleep_data
        ORDER BY workout_date
    """
    df = pd.read_sql(query, engine)

    # ⏱ Ensure datetime format
    df['workout_date'] = pd.to_datetime(df['workout_date'])

    # 🛠 Ensure numeric types
    numeric_cols = ['avg_overnight_hrv', 'sleep_duration', 'sleep_score', 'resting_heart_rate']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

df = load_data()
today_row = get_today_data(df)


st.title("Garmin Sleep & Training Dashboard")
st.markdown("---")

# Todays Data
st.subheader("Today's Data")
col1, col2, col3 = st.columns(3)
if not today_row.empty:
    row = today_row.iloc[0]
    col1.metric("HRV", f"{row['avg_overnight_hrv']:.1f} ms")
    col2.metric("Sleep Duration", format_duration_hours(row['sleep_duration']))
    col3.metric("Sleep Score", f"{row['sleep_score']:.0f}")
    st.markdown(f"**Recommendations:** {generate_recommendation(row)}")
else:
    col1.metric("HRV", "—")
    col2.metric("Sleep Duration", "—")
    col3.metric("Sleep Score", "—")
    st.markdown("No data available for today.")


# 7-DAY AVERAGES & INSIGHTS
st.subheader("📊 7-Day Averages")

df['hrv_rolling'] = df['avg_overnight_hrv'].rolling(window=7).mean()
df['sleep_rolling'] = df['sleep_duration'].rolling(window=7).mean()

last_7 = df[df['workout_date'] >= df['workout_date'].max() - pd.Timedelta(days=6)]

col1, col2 = st.columns(2)

col1.metric("7-Day Avg HRV", f"{df['hrv_rolling'].iloc[-1]:.1f} ms")
col2.metric("7-Day Avg Sleep", format_duration_hours(df['sleep_rolling'].iloc[-1]))


# Sleep debt highlight
if last_7['sleep_duration'].mean() < 7:
    st.warning("😴 Sleep debt detected — average sleep < 7 hours")
else:
    st.success("✅ No sleep debt detected — good recovery range")

# ----------------------------
# 📉 CHARTS
# ----------------------------
st.subheader("📈 HRV and Sleep Duration Over Time")
import altair as alt

chart_df = df.copy()

base = alt.Chart(chart_df).encode(
    x=alt.X("workout_date:T", title="Date")
)

hrv_line = base.mark_line(color="#1f77b4").encode(
    y=alt.Y("avg_overnight_hrv:Q", title="HRV (ms)"),
    tooltip=["workout_date", "avg_overnight_hrv"]
)

hrv_avg = base.mark_line(strokeDash=[4,4], color="#1f77b4").encode(
    y="rolling_hrv:Q"
)

sleep_line = base.mark_line(color="#ff7f0e").encode(
    y=alt.Y("sleep_duration_hours:Q", axis=alt.Axis(title="Sleep Duration (hrs)", titleColor="#ff7f0e")),
    tooltip=["workout_date", "sleep_duration"]
)

sleep_avg = base.mark_line(strokeDash=[4,4], color="#ff7f0e").encode(
    y="rolling_sleep:Q"
)

st.altair_chart(hrv_line + hrv_avg + sleep_line + sleep_avg, use_container_width=True)