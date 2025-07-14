import datetime
from sqlalchemy import create_engine
import pandas as pd
import os
import garminconnect

email = os.environ["EMAIL"]
password = os.environ["GARMINPASSWORD"]
garmin = garminconnect.Garmin(email, password)
garmin.login()


user = os.environ["DB_USER"]
password = os.environ["DB_PASSWORD"]
host = os.environ["DB_HOST"]
port = os.environ["DB_PORT"]
dbname = os.environ["DB_NAME"]
engine = create_engine(f"postgresql://{user}:{password}@{host}:{port}/{dbname}")

today = datetime.date.today().strftime("%Y-%m-%d")


def getsleep(date):
    data = garmin.get_sleep_data(date)

    # Safeguard: if no data or missing expected structure
    if not data or not isinstance(data, dict) or 'dailySleepDTO' not in data:
        return pd.DataFrame()

    dailysleep_dto = data.get('dailySleepDTO', {})

    sleepdata = {
        'date': dailysleep_dto.get('calendarDate'),
        'startTime': dailysleep_dto.get('sleepStartTimestampLocal'),
        'endTime': dailysleep_dto.get('sleepEndTimestampLocal'),
        'sleepDuration': dailysleep_dto.get('sleepTimeSeconds'),
        'deepSleepDuration': dailysleep_dto.get('deepSleepSeconds'),
        'lightSleepDuration': dailysleep_dto.get('lightSleepSeconds'),
        'remSleepDuration': dailysleep_dto.get('remSleepSeconds'),
        'spo2Avg': dailysleep_dto.get('averageSpO2Value'),
        'spo2Low': dailysleep_dto.get('lowestSpO2Value'),
        'spo2High': dailysleep_dto.get('highestSpO2Value'),
        'respirationAvg': dailysleep_dto.get('averageRespirationValue'),
        'respirationLow': dailysleep_dto.get('lowestRespirationValue'),
        'respirationHigh': dailysleep_dto.get('highestRespirationValue'),
        'awakeCounter': dailysleep_dto.get('awakeCount'),
        'avgOvernightHrv': data.get('avgOvernightHrv'),
        'restingHeartRate': data.get('restingHeartRate'),
        'restlessmoment': data.get('restlessMomentsCount')
    }

    df_sleepdata = pd.DataFrame([sleepdata])

    # Convert time columns if present, otherwise NaT
    for col in ['startTime', 'endTime']:
        if pd.notnull(df_sleepdata.at[0, col]):
            df_sleepdata[col] = pd.to_datetime(df_sleepdata[col], unit='ms')
        else:
            df_sleepdata[col] = pd.NaT

    return df_sleepdata
    
def update():
    df_sleepdata = getsleep(today)

    if df_sleepdata.empty:
        print(f"No sleep data for {today}. Skipping.")
    else:
        with engine.begin() as conn:
            existing = pd.read_sql(f"""
                SELECT 1 FROM simplesleepdata WHERE date = '{today}' LIMIT 1;
            """, conn)
            if not existing.empty:
                print(f"Data for {today} already exists. Skipping insert.")
                return

        df_sleepdata.to_sql('simplesleepdata', con=engine, if_exists="append", index=False)
        print(f"Inserted sleep data for {today}")


if __name__ == "__main__":
    update()