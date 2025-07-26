import streamlit as st
import pandas as pd
import re
import datetime
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Set page config
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(credentials)
sheet = client.open("Kaia Heights Badminton Booking").sheet1

# Load data
def load_bookings():
    return pd.DataFrame(sheet.get_all_records())

bookings = load_bookings()
timeslots = ["8am - 9am", "9am - 10am", "10am - 11am", "11am - 12pm", "12pm - 1pm", "1pm - 2pm", "2pm - 3pm", "3pm - 4pm", "5pm - 6pm", "6pm - 7pm", "7pm - 8pm", "8pm - 9pm", "9pm - 10pm"]

# Validation
def is_valid_unit(unit):
    return re.match(r"^\d-\d{2}-\d{2}$", unit)

def save_booking(unit, date, time):
    sheet.append_row([unit, str(date), time])
    st.success(f"✅ Booking confirmed for *{date}*, *{time}*, unit: *{unit}*.")

def cancel_booking(unit, date=None, time=None):
    data = sheet.get_all_values()
    headers, rows = data[0], data[1:]
    new_data = []
    cancelled = False

    for row in rows:
        if row[0] == unit and (date is None or row[1] == str(date)) and (time is None or row[2] == time):
            cancelled = True
            continue
        new_data.append(row)

    if cancelled:
        sheet.clear()
        sheet.append_row(headers)
        for row in new_data:
            sheet.append_row(row)
        st.success("✅ Booking cancelled successfully.")
    else:
        st.warning("⚠️ No matching booking found.")

# UI
st.title("🏸 KaiaHeights Badminton Booking")

# Booking Form
st.header("📌 Make a Booking")
with st.form("booking_form"):
    unit = st.text_input("Unit Number (format: X-XX-XX)", max_chars=8)
    date = st.date_input("Booking Date", min_value=datetime.date.today())
    time = st.selectbox("Time Slot", timeslots)
    submit = st.form_submit_button("Book Now")

    if submit:
        bookings = load_bookings()
        if not is_valid_unit(unit):
            st.error("❌ Invalid unit format. Use format X-XX-XX.")
        elif ((bookings["Date"] == str(date)) & (bookings["Time"] == time)).any():
            st.warning("⚠️ Slot already booked. Please choose another.")
        else:
            save_booking(unit, date, time)

# Slot Availability
st.header("📆 Slot Availability")
selected_date = st.date_input("Check availability for:", key="check_availability", min_value=datetime.date.today())
bookings = load_bookings()
booked_times = bookings[bookings["Date"] == str(selected_date)]["Time"].tolist()

for slot in timeslots:
    if slot in booked_times:
        st.markdown(f"❌ **{slot}** - Booked")
    else:
        st.markdown(f"✅ **{slot}** - Available")

# Cancel Booking
st.header("🗑️ Cancel a Booking")
unit_to_cancel = st.text_input("Enter your Unit Number to view/cancel", key="cancel")
if unit_to_cancel:
    filtered = bookings[bookings["Unit"] == unit_to_cancel]
    if not filtered.empty:
        st.write("Your bookings:")
        for i, row in filtered.iterrows():
            col1, col2, col3 = st.columns([3, 3, 2])
            with col1:
                st.write(f"📅 {row['Date']} | 🕒 {row['Time']}")
            with col3:
                if st.button("Cancel", key=f"cancel_{i}"):
                    cancel_booking(unit_to_cancel, row["Date"], row["Time"])
                    st.experimental_rerun()
    else:
        st.info("ℹ️ No bookings found for this unit.")
