import streamlit as st
import json
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import re
import os

# --------------------------- CONFIG ---------------------------
SHEET_NAME = "KaiaHeightsBookings"
EMAIL_SENDER = os.getenv("EMAIL_SENDER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# ------------------ GOOGLE SHEETS SETUP ------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["GOOGLE_CREDENTIALS"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

def get_sheet():
    try:
        sheet = client.open(SHEET_NAME).sheet1
    except:
        sheet = client.create(SHEET_NAME).sheet1
        sheet.append_row(["Name", "Email", "Unit", "Date", "Time", "Court", "BookedAt"])
    return sheet

# ------------------ EMAIL FUNCTION ------------------
def send_confirmation_email(to_email, name, unit, date, times, courts):
    if not to_email:
        return
    body = f"""
    Hi {name},\n\nYour booking is confirmed:\nUnit: {unit}\nDate: {date}\nTime: {', '.join(times)}\nCourt(s): {', '.join(courts)}\n\nThank you!\nKaiaHeights Booking System
    """
    msg = MIMEText(body)
    msg['Subject'] = 'KaiaHeights Badminton Booking Confirmation'
    msg['From'] = EMAIL_SENDER
    msg['To'] = to_email

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)

# ------------------ APP SETUP ------------------
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="centered")
st.title("🏸 KaiaHeights Badminton Booking")

sheet = get_sheet()
data = pd.DataFrame(sheet.get_all_records())

dates = pd.date_range(datetime.today(), periods=7).strftime("%Y-%m-%d").tolist()
time_slots = [(datetime.strptime("10:00", "%H:%M") + timedelta(hours=i)).strftime("%I:%M %p") for i in range(13)]
courts = ["Court 1", "Court 2"]

# ------------------ VIEW BOOKINGS ------------------
st.subheader("📅 Check Court Availability")
selected_date = st.selectbox("Choose a date", dates)

booked = data[data['Date'] == selected_date]

for court in courts:
    st.markdown(f"**{court}**")
    booked_slots = booked[booked['Court'] == court]['Time'].tolist()
    available = [t for t in time_slots if t not in booked_slots]
    if available:
        st.write(", ".join(available))
    else:
        st.warning("Fully booked")

# ------------------ BOOK FORM ------------------
st.subheader("✅ Book a Court")
with st.form("booking_form"):
    name = st.text_input("Your Name")
    email = st.text_input("Email (for confirmation, optional)")
    unit = st.text_input("Your Unit Number (format: X-XX-XX)")
    court_choice = st.multiselect("Select Court(s)", courts)
    time_choice = st.multiselect("Select Time Slot(s)", time_slots)
    submit = st.form_submit_button("Book Now")

    if submit:
        if not name or not unit or not court_choice or not time_choice:
            st.error("All fields except email are required.")
        elif not re.match(r"^\d-\d{2}-\d{2}$", unit):
            st.error("Invalid unit format. Use X-XX-XX")
        elif len(court_choice) * len(time_choice) > 4:
            st.error("Max 2 courts for 2 hours allowed.")
        else:
            duplicate = False
            for court in court_choice:
                for t in time_choice:
                    if ((data['Date'] == selected_date) &
                        (data['Court'] == court) &
                        (data['Time'] == t)).any():
                        st.warning(f"{court} at {t} is already booked.")
                        duplicate = True
            if not duplicate:
                for court in court_choice:
                    for t in time_choice:
                        sheet.append_row([name, email, unit, selected_date, t, court, str(datetime.now())])
                send_confirmation_email(email, name, unit, selected_date, time_choice, court_choice)
                st.success("🎉 Booking confirmed!")

# ------------------ CANCEL BY UNIT ------------------
st.subheader("❌ Cancel by Unit")
with st.form("cancel_unit"):
    cancel_unit = st.text_input("Enter your Unit Number (X-XX-XX)")
    cancel_date = st.selectbox("Date of Booking to Cancel", dates, key="cancel")
    cancel_btn = st.form_submit_button("Cancel Booking")

    if cancel_btn:
        if not re.match(r"^\d-\d{2}-\d{2}$", cancel_unit):
            st.error("Invalid unit format.")
        else:
            df = pd.DataFrame(sheet.get_all_records())
            original_len = len(df)
            df = df[~((df['Unit'] == cancel_unit) & (df['Date'] == cancel_date))]
            sheet.clear()
            sheet.append_row(["Name", "Email", "Unit", "Date", "Time", "Court", "BookedAt"])
            for _, row in df.iterrows():
                sheet.append_row(list(row))
            st.success("Booking(s) cancelled for that unit and date.")
