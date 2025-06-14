from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import os
import time
from datetime import datetime
import shutil

profile_path = "/Users/adammoore/Library/Application Support/Google/Chrome"  # Update with your user path
download_dir = "/Users/adammoore/Documents/GitHub/Garmin-EDA/autodownload"  # Update to your actual path
today = datetime.today().strftime('%Y-%m-%d')

chrome_options = Options()
chrome_options.add_argument(f"user-data-dir={profile_path}")
chrome_options.add_argument("profile-directory=Default")
chrome_options.add_experimental_option("prefs", {
    "download.default_directory": download_dir,
    "download.prompt_for_download": False,
    "directory_upgrade": True,
    "safebrowsing.enabled": True
})

driver = webdriver.Chrome(options=chrome_options)
print("Opening Garmin Sleep page...")
driver.get("https://connect.garmin.com/modern/sleep/2025-05-14")
print("Garmin page opened.")

time.sleep(5)
export_button = driver.find_element("xpath", "//div[contains(text(), 'Export CSV')]")
export_button.click()

time.sleep(10)
files = [f for f in os.listdir(download_dir) if f.endswith(".csv")]
files.sort(key=lambda x: os.path.getctime(os.path.join(download_dir, x)), reverse=True)

if files:
    latest = os.path.join(download_dir, files[0])
    new_name = os.path.join(download_dir, f"garmin_sleep_{today}.csv")
    shutil.move(latest, new_name)
    print(f"Saved: {new_name}")
else:
    print("No file downloaded.")

driver.quit()
