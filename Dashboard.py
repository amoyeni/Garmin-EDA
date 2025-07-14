import streamlit as st
import pandas as pd
import datetime

from sqlalchemy import create_engine

user = st.secrets["user"]

password = st.secrets["password"]
host = st.secrets["host"]
port = st.secrets["port"]
dbname = st.secrets["dbname"]

engine = create_engine(f'postgresql://{user}:{password}@{host}:{port}/{dbname}')

def format_seconds(seconds):
    if pd.isnull(seconds):
        return "—"
    total_minutes = int(seconds) // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"



st.set_page_config(page_title="Sleep & Recovery Dashboard", layout="wide")

@st.cache_data

def load_data():
    query = """
        SELECT
            "date",
            "avgOvernightHrv",
            "sleepDuration",
            "restingHeartRate"
        FROM simplesleepdata
        ORDER BY date
    """
    df = pd.read_sql(query, engine)

    df['date'] = pd.to_datetime(df['date'])

    numeric_cols = ['avgOvernightHrv', 'sleepDuration', 'restingHeartRate']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    return df

df = load_data()

def get_today_data(df):
    today = pd.to_datetime(datetime.date.today())
    df['date_only'] = df['date'].dt.normalize()
    return df[df['date_only'] == today]

today_row = get_today_data(df)


st.title("Garmin Sleep & Training Dashboard")
st.markdown("---")

# Todays Data
st.subheader("Today's Data")
col1, col2, col3 = st.columns(3)
if not today_row.empty:
    row = today_row.iloc[0]
    col1.metric("HRV", f"{row['avgOvernightHrv']:.1f} ms")
    col2.metric("Sleep Duration", format_seconds(row['sleepDuration']))
    col3.metric("Resting HR", f"{row['restingHeartRate']:.0f} bpm")

else:
    col1.metric("HRV", "—")
    col2.metric("Sleep Duration", "—")
    col3.metric("Resting HR", "_")

    st.markdown("No data available for today.")


if st.button("Refresh data"):
    load_data.clear()  # clears the cache

df = load_data()