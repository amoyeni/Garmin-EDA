import streamlit as st
import pandas as pd
import os
import datetime
import plotly.express as px

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

def format_seconds(seconds):
    if pd.isnull(seconds):
        return "—"
    total_minutes = int(seconds) // 60
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}h {minutes}m"

def get_today_data(df):
    today = pd.to_datetime(datetime.date.today())
    df['date_only'] = df['date'].dt.normalize()
    return df[df['date_only'] == today]


def estimateSleepNeeded(row):
    base_sleep = 7.5
    
    # Recovery Score impact
    if pd.isnull(row['recoveryScore']):
        recovery_factor = 0
    elif row['recoveryScore'] < 50:
        recovery_factor = 1.0
    elif row['recoveryScore'] < 65:
        recovery_factor = 0.5
    else:
        recovery_factor = 0
    
    # HRV & RHR impact
    hrv_baseline = row['hrv_baseline']
    rhr_baseline = row['rhr_baseline']
    hrv = row['avgOvernightHrv']
    rhr = row['restingHeartRate']
    if pd.isnull(hrv) or pd.isnull(rhr) or pd.isnull(hrv_baseline) or pd.isnull(rhr_baseline):
        hrv_rhr_factor = 0
    else:
        hrv_drop = hrv < 0.9 * hrv_baseline
        rhr_rise = rhr > 1.1 * rhr_baseline
        if hrv_drop and rhr_rise:
            hrv_rhr_factor = 1.0
        elif hrv_drop or rhr_rise:
            hrv_rhr_factor = 0.5
        else:
            hrv_rhr_factor = 0
    # Combine factors
    total_factor = recovery_factor + hrv_rhr_factor 
    # Each factor point adds ~0.5 hours of sleep needed (adjust as you see fit)
    extra_sleep = total_factor * 0.5
    
    return base_sleep + extra_sleep
# ----------------------------
# 📊 LOAD DATA
# ----------------------------
st.set_page_config(page_title="Sleep & Recovery Dashboard", layout="wide")

@st.cache_data
@st.cache_data
def load_data():
    query = """
        SELECT
            "date",
            "avgOvernightHrv",
            "sleepDuration",
            "restingHeartRate",
            "recoveryScore"
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
else:
    col1.metric("HRV", "—")
    col2.metric("Sleep Duration", "—")
    st.markdown("No data available for today.")


# 7-DAY AVERAGES & INSIGHTS
st.subheader("7-Day Averages")

df['hrv_rolling'] = df['avgOvernightHrv'].rolling(window=7).mean()
df['sleep_rolling'] = df['sleepDuration'].rolling(window=7).mean()

last_7 = df[df['date'] >= df['date'].max() - pd.Timedelta(days=6)]

col1, col2 = st.columns(2)

col1.metric("7-Day Avg HRV", f"{df['hrv_rolling'].iloc[-1]:.1f} ms")
col2.metric("7-Day Avg Sleep", format_seconds(df['sleep_rolling'].iloc[-1]))


# Sleep debt highlight
if last_7['sleepDuration'].mean() < 7:
    st.warning("😴 Sleep debt detected — average sleep < 7 hours")
else:
    st.success("✅ No sleep debt detected — good recovery range")



df_chart = df.tail(7).copy()
df_chart['Hours of Sleep'] = df_chart['sleepDuration'] / 3600 # Convert seconds to hours

df_chart['hrv_baseline'] = df['avgOvernightHrv'].rolling(7, min_periods=1).mean().shift(1)
df_chart['rhr_baseline'] = df['restingHeartRate'].rolling(7, min_periods=1).mean().shift(1)

df_chart['sleepNeeded'] = df_chart.apply(estimateSleepNeeded, axis=1)

# Add Day and Date for later labeling
df_chart['Day'] = df_chart['date'].dt.strftime('%a')
df_chart['Date'] = df_chart['date'].dt.day

print(df_chart)
# Melt to long format
df_melted_chart = df_chart.melt(
    id_vars=['date', 'Day', 'Date'],
    value_vars=['Hours of Sleep', 'Sleep Needed'],
    var_name='Metric',
    value_name='Hours'
)

# Plot
fig = px.line(
    df_melted_chart,
    x='Day',
    y='Hours',
    color='Metric',
    text=df_melted_chart['Hours'].round(2),
    markers=True,
    title='Hours vs. Need',
    labels={'Hours': 'Hours', 'Day': 'Day'},
    color_discrete_map={'Hours of Sleep': '#80A4ED', 'Sleep Needed': '#32CD32'}
)

fig.update_traces(textposition='top center')
fig.update_traces(marker=dict(size=10), selector=dict(mode='markers+lines'))
fig.update_traces(line=dict(width=2))

fig.update_layout(
    plot_bgcolor='#282C34',
    paper_bgcolor='#282C34',
    font_color='white',
    title_font_color='white',
    legend_font_color='white',
    xaxis_tickangle=0,
    legend=dict(
        orientation="h",
        yanchor="bottom",
        y=1.02,
        xanchor="right",
        x=1,
        title_text=""
    ),
    xaxis=dict(
        tickvals=df_chart['Day'],
        ticktext=[f"{d}<br>{dt}" for d, dt in zip(df_chart['Day'], df_chart['Date'])]
    )
)

st.plotly_chart(fig, use_container_width=True)