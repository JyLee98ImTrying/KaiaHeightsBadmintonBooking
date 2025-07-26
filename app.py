import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import re
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------
# Setup Google Sheets
# -------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)
sheet = client.open("kaiaheights_booking").sheet1

# -------------------------
# Setup app
# -------------------------
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")
st.title("🏸 KaiaHeights Badminton Booking")
st.markdown("Check real-time availability and make your booking below.")

# Time slots and courts
start_time = datetime.strptime("10:00", "%H:%M")
slots = [(start_time + timedelta(hours=i)).strftime("%I:%M %p") for i in range(13)]  # 10AM–10PM
courts = ["Court 1", "Court 2"]

# Load existing bookings
records = sheet.get_all_records()
df = pd.DataFrame(records)

# If empty sheet, initialize
if df.empty:
    dates = pd.date_range(datetime.today(), periods=7).strftime("%Y-%m-%d").tolist()
    data = []
    for date in dates:
        for court in courts:
            for slot in slots:
                data.append([date, court, slot, "TRUE", ""])
    sheet.append_rows(data, value_input_option="USER_ENTERED")
    df = pd.DataFrame(data, columns=["date", "court", "time_slot", "available", "booked_by"])

# -------------------------
# UI – Show Availability
# -------------------------
selected_date = st.selectbox("📅 Select a date", sorted(df["date"].unique()))
st.subheader("Available Slots")
available_df = df[(df["date"] == selected_date) & (df["available"] == "TRUE")]

for court in courts:
    st.markdown(f"**{court}**")
    court_slots = available_df[available_df["court"] == court]["time_slot"].tolist()
    if court_slots:
        st.write(", ".join(court_slots))
    else:
        st.write("❌ No available slots")

# -------------------------
# UI – Booking Form
# -------------------------
st.subheader("✅ Book a Court")

with st.form("booking_form"):
    name = st.text_input("Your Name")
    unit = st.text_input("Your Unit Number (format: X-XX-XX)")
    email = st.text_input("Email for confirmation")
    court_choice = st.multiselect("Select Court(s)", courts)
    time_choice = st.multiselect("Select Time Slot(s)", slots)
    submit = st.form_submit_button("Book Now")

    if submit:
        # Validate unit number format
        if not re.match(r"^\d-\d{2}-\d{2}$", unit):
            st.error("❌ Invalid unit number format. Please use X-XX-XX format.")
        elif not name or not email or not court_choice or not time_choice:
            st.error("❌ Please fill in all fields.")
        elif len(court_choice) * len(time_choice) > 4:
            st.error("❌ Maximum of 2 courts for 2 hours (4 total slots).")
        else:
            updated = 0
            for i, row in df.iterrows():
                if row["date"] == selected_date and row["court"] in court_choice and row["time_slot"] in time_choice:
                    if row["available"] == "TRUE":
                        sheet.update_cell(i + 2, 4, "FALSE")  # Column D: available
                        sheet.update_cell(i + 2, 5, f"{name} ({unit})")  # Column E: booked_by
                        updated += 1
            if updated > 0:
                st.success(f"✅ {updated} slot(s) booked successfully.")
                # Send confirmation email
                try:
                    msg = MIMEText(
                        f"Hi {name},\n\nYour booking on {selected_dat_
