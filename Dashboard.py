import streamlit as st
import pandas as pd
import datetime
import matplotlib.pyplot as plt

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
            *
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

if st.button("Refresh data"):
    load_data.clear()   
    df = load_data()    

def get_today_data(df):
    today = pd.to_datetime(datetime.date.today())
    df['date_only'] = df['date'].dt.normalize()
    return df[df['date_only'] == today]

today_row = get_today_data(df)


st.title("Garmin Sleep & Training Dashboard")
st.markdown("---")

# Today's Data
if not today_row.empty:
    row = today_row.iloc[0]
    hrv_card, hrv_graph = st.columns([1, 2])

    # Big Card
    st.subheader("Recovery Today")
    st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{row['avgOvernightHrv']:.1f} ms</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Average Overnight HRV</h3>", unsafe_allow_html=True)

    st.subheader("Last 7 Days HRV Trend")
    end_date = pd.to_datetime(datetime.date.today()) 
    start_date = end_date - datetime.timedelta(days=6) 
    recent_hrv_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()



    st.markdown("---") 

    # Other Metrics
    st.subheader("Other Key Metrics")
    col2, col3, col4, col5 = st.columns(4) 
    col2.metric("Sleep Duration", format_seconds(row['sleepDuration']))
    col3.metric("Resting HR", f"{row['restingHeartRate']:.0f} bpm")
    col4.metric("Sleep HR", f"{row['SleepHR']:.0f} bpm")
    col5.metric("Waking up HR", f"{row['wakeHR']:.0f} bpm")


else:
    st.subheader("Recovery Today")
    st.markdown("<h1 style='text-align: center; color: grey;'>—</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Average Overnight HRV</h3>", unsafe_allow_html=True)
    st.markdown("---")

    st.subheader("Other Key Metrics")
    col2, col3 = st.columns(2)
    col2.metric("Sleep Duration", "—")
    col3.metric("Resting HR", "—")

    st.markdown("No data available for today.")

