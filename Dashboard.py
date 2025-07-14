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


## Today's Data and 7-Day HRV Trend
col_hrv_card, col_hrv_graph = st.columns([1, 2])

with col_hrv_card:
    st.subheader("Your Recovery Today")
    if not today_row.empty:
        row = today_row.iloc[0]
        st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{row['avgOvernightHrv']:.1f} ms</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>Average Overnight HRV</h3>", unsafe_allow_html=True)
    else:
        st.markdown("<h1 style='text-align: center; color: grey;'>—</h1>", unsafe_allow_html=True)
        st.markdown(f"<h3 style='text-align: center;'>Average Overnight HRV</h3>", unsafe_allow_html=True)

with col_hrv_graph:
    st.subheader("Last 7 Days HRV Trend")
    end_date = pd.to_datetime(datetime.date.today()) 
    start_date = end_date - datetime.timedelta(days=6) 

    recent_hrv_df = df[(df['date'] >= start_date) & (df['date'] <= end_date)].copy()
    
    recent_hrv_df['avgOvernightHrv'] = pd.to_numeric(recent_hrv_df['avgOvernightHrv'], errors='coerce')
    recent_hrv_df.dropna(subset=['avgOvernightHrv'], inplace=True)


    if not recent_hrv_df.empty:
        hrv_mean = recent_hrv_df['avgOvernightHrv'].mean()
        hrv_std = recent_hrv_df['avgOvernightHrv'].std()

        
        lower_limit = hrv_mean - hrv_std
        upper_limit = hrv_mean + hrv_std

        fig, ax = plt.subplots(figsize=(8, 4)) 
        ax.plot(recent_hrv_df['date'], recent_hrv_df['avgOvernightHrv'], marker='o', linestyle='-', color='skyblue', label='Daily HRV')

        # Plot limits
        ax.axhline(y=upper_limit, color='red', linestyle='--', label='Upper Limit')
        ax.axhline(y=lower_limit, color='green', linestyle='--', label='Lower Limit')
        ax.axhline(y=hrv_mean, color='gray', linestyle=':', label='7-Day Avg')


        ax.set_title('7-Day HRV Trend with Limits')
        ax.set_ylabel('HRV (ms)')
        ax.set_xlabel('Date')
        ax.grid(True, linestyle=':', alpha=0.6)
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout() # Adjust layout to prevent labels from overlapping
        st.pyplot(fig)
    else:
        st.info("Not enough HRV data available for the last 7 days to show a trend.")

st.markdown("---") # Separator after the top section



# Today's Data
if not today_row.empty:
    row = today_row.iloc[0]

    # Big Card
    st.subheader("Recovery Today")
    st.markdown(f"<h1 style='text-align: center; color: #4CAF50;'>{row['avgOvernightHrv']:.1f} ms</h1>", unsafe_allow_html=True)
    st.markdown(f"<h3 style='text-align: center;'>Average Overnight HRV</h3>", unsafe_allow_html=True)
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

