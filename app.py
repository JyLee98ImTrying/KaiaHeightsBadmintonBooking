import streamlit as st
import gspread
import pandas as pd
from datetime import datetime, timedelta

# ==== SETUP ====
SHEET_NAME = "Kaia Heights Badminton Booking"
CREDENTIALS_FILE = "credentials.json"  # Update if your file is in a subfolder

# Connect to Google Sheets
gc = gspread.service_account(filename=CREDENTIALS_FILE)
sh = gc.open(SHEET_NAME)
sheet = sh.sheet1

# Load existing data
existing_data = pd.DataFrame(sheet.get_all_records())

# Prepare date & time slots
dates = pd.date_range(datetime.today(), periods=7).strftime("%Y-%m-%d").tolist()
times = [f"{hour}:00" for hour in range(8, 23)]  # 8 AM to 10 PM

# ==== UI ====
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")
st.title("🏸 KaiaHeights Badminton Booking")

st.header("📅 Book a Slot")
with st.form("booking_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    unit = st.text_input("Unit Number")
    date = st.selectbox("Date", dates)
    time = st.selectbox("Time", times)
    comments = st.text_area("Comments (optional)", placeholder="e.g. Bringing guests...")

    submitted = st.form_submit_button("Submit Booking")

    if submitted:
        # Check for double booking
        booked = existing_data[
            (existing_data["Date"] == date) & (existing_data["Time"] == time)
        ]
        if not booked.empty:
            st.error("❌ That slot is already booked. Please choose another.")
        else:
            row = [name, email, unit, date, time, comments, datetime.now().isoformat()]
            sheet.append_row(row)
            st.success(f"✅ Booking confirmed for {date} at {time}!")

# ==== AVAILABILITY VIEW ====
st.header("📋 Available & Booked Slots")
selected_day = st.selectbox("View availability for", dates)

# Get booked times for selected day
booked_times = existing_data[existing_data["Date"] == selected_day]["Time"].tolist()
availability = []

for t in times:
    status = "🟢 Available" if t not in booked_times else "🔴 Booked"
    availability.append({"Time": t, "Status": status})

availability_df = pd.DataFrame(availability)
st.table(availability_df)
