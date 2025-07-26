import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# === CONFIGURATION ===
SHEET_NAME = "Kaia Heights Badminton Booking"

# === AUTHENTICATION ===
scope = ["https://www.googleapis.com/auth/spreadsheets"]
creds = Credentials.from_service_account_file("credentials.json", scopes=scope)
client = gspread.authorize(creds)

# === LOAD EXISTING SHEET (MUST ALREADY EXIST & BE SHARED WITH SERVICE ACCOUNT) ===
def get_sheet():
    return client.open(SHEET_NAME).sheet1

sheet = get_sheet()

# === LOAD DATA ===
data = pd.DataFrame(sheet.get_all_records())

# === UI CONFIG ===
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")
st.title("🏸 KaiaHeights Badminton Booking")

# === DATE & TIME OPTIONS ===
dates = pd.date_range(datetime.today(), periods=7).strftime("%Y-%m-%d").tolist()
times = [f"{h:02d}:00" for h in range(8, 23)]  # 8AM to 10PM

# === SLOT AVAILABILITY VIEW ===
st.subheader("📅 Slot Availability (Next 7 Days)")
selected_day = st.selectbox("Select date to view", dates)

availability_df = pd.DataFrame(index=times, columns=["Status"])
for t in times:
    is_booked = ((data["Date"] == selected_day) & (data["Time"] == t)).any()
    availability_df.loc[t] = "❌ Booked" if is_booked else "✅ Available"

st.dataframe(availability_df, use_container_width=True)

# === BOOKING FORM ===
st.subheader("🔒 Make a Booking")

with st.form("booking_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    unit = st.text_input("Unit Number")
    date = st.selectbox("Date", dates)
    time = st.selectbox("Time", times)
    confirm = st.checkbox("I confirm my booking details are correct")

    submitted = st.form_submit_button("Submit Booking")

    if submitted:
        # Check if already booked
        existing = data[(data["Date"] == date) & (data["Time"] == time)]
        if not confirm:
            st.warning("Please confirm your booking details.")
        elif not name or not email or not unit:
            st.warning("Please fill in all fields.")
        elif not existing.empty:
            st.error("This slot is already booked. Please choose another.")
        else:
            sheet.append_row([name, email, unit, date, time, str(datetime.now())])
            st.success(f"✅ Booking confirmed for {date} at {time}!")
