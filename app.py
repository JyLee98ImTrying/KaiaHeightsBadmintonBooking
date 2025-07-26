import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
import re

# Constants
SHEET_NAME = "Kaia Heights Badminton Booking"
TIME_SLOTS = [f"{hour}:00" for hour in range(10, 22)]  # 10am to 10pm
COURTS = ["Court 1", "Court 2"]

# Google Sheets Auth
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
credentials = Credentials.from_service_account_info(st.secrets["GOOGLE_CREDENTIALS"], scopes=scope)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME).sheet1

# Load existing data
def load_data():
    return pd.DataFrame(sheet.get_all_records())

data = load_data()

def is_valid_unit(unit):
    return re.match(r"^[A-Z]-\d{2}-\d{2}$", unit.upper())

# UI
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")
st.title("🏸 KaiaHeights Badminton Booking")

# Calendar
dates = pd.date_range(datetime.today(), periods=7).strftime("%Y-%m-%d").tolist()
selected_date = st.selectbox("Select a date", dates)

# Availability View
st.subheader(f"Available Slots for {selected_date}")
booked = data[data["Date"] == selected_date]

availability = {
    (slot, court): True for slot in TIME_SLOTS for court in COURTS
}

for _, row in booked.iterrows():
    availability[(row["Time"], row["Court"])] = False

for slot in TIME_SLOTS:
    cols = st.columns(len(COURTS))
    for idx, court in enumerate(COURTS):
        key = (slot, court)
        status = "✅ Available" if availability[key] else "❌ Booked"
        cols[idx].markdown(f"**{court} - {slot}**: {status}")

st.divider()

# Booking Form
st.subheader("📋 Book a Slot")
with st.form("booking_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    unit = st.text_input("Unit (format: X-XX-XX)")
    selected_slots = st.multiselect("Select up to 2 slots", [f"{slot} - {court}" for slot, court in availability if availability[(slot, court)]], max_selections=2)
    submitted = st.form_submit_button("Book Now")

    if submitted:
        if not name or not email or not unit or not selected_slots:
            st.error("Please complete all fields and select slots.")
        elif not is_valid_unit(unit):
            st.error("Unit must follow the format X-XX-XX (e.g., A-12-08).")
        else:
            for sc in selected_slots:
                time, court = sc.split(" - ")
                sheet.append_row([name, email, unit.upper(), selected_date, time, court])
            st.success("✅ Booking successful!")
            st.experimental_rerun()

st.divider()

# Manage Bookings
st.subheader("✏️ Edit or Cancel Booking")
user_email = st.text_input("Enter your email to manage bookings")
if user_email:
    user_bookings = data[data["Email"] == user_email]
    if user_bookings.empty:
        st.info("No bookings found for this email.")
    else:
        for idx, row in user_bookings.iterrows():
            with st.expander(f"{row['Date']} {row['Time']} - {row['Court']}"):
                new_name = st.text_input(f"Name_{idx}", value=row['Name'], key=f"name_{idx}")
                new_unit = st.text_input(f"Unit_{idx}", value=row['Unit'], key=f"unit_{idx}")
                col1, col2 = st.columns(2)

                if col1.button("Update", key=f"update_{idx}"):
                    all_rows = sheet.get_all_values()
                    for i, r in enumerate(all_rows):
                        if r[1] == row['Email'] and r[3] == row['Date'] and r[4] == row['Time'] and r[5] == row['Court']:
                            sheet.update(f"A{i+1}:C{i+1}", [[new_name, row['Email'], new_unit]])
                            st.success("Booking updated.")
                            st.experimental_rerun()
                            break

                if col2.button("Cancel", key=f"cancel_{idx}"):
                    all_rows = sheet.get_all_values()
                    for i, r in enumerate(all_rows):
                        if r[1] == row['Email'] and r[3] == row['Date'] and r[4] == row['Time'] and r[5] == row['Court']:
                            sheet.delete_row(i+1)
                            st.warning("Booking cancelled.")
                            st.experimental_rerun()
                            break
