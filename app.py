import streamlit as st
import pandas as pd
import requests
from datetime import datetime, timedelta

# Airtable configuration
AIRTABLE_API_KEY = "patuTF5R5afg1re9p.95735c59fff75d42e0a73bb8c26780738820b757f09fd4527147982432892a97"
AIRTABLE_BASE_ID = "appfgu3MwNjxrtTg0"
AIRTABLE_TABLE_NAME = "Kaia Heights Badminton Booking"

AIRTABLE_ENDPOINT = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# Constants
TIME_SLOTS = [f"{hour}:00" for hour in range(10, 22)]
COURTS = ["Court 1", "Court 2"]

# Utility functions
def fetch_bookings():
    response = requests.get(AIRTABLE_ENDPOINT, headers=HEADERS)
    if response.status_code == 200:
        records = response.json().get("records", [])
        bookings = [
            {
                "id": r["id"],
                **r["fields"]
            } for r in records
        ]
        return pd.DataFrame(bookings)
    else:
        return pd.DataFrame()

def create_booking(name, email, unit, date, time, court):
    data = {
        "fields": {
            "Name": name,
            "Email": email,
            "Unit": unit,
            "Date": date,
            "Time": time,
            "Court": court
        }
    }
    response = requests.post(AIRTABLE_ENDPOINT, headers=HEADERS, json=data)
    return response.status_code == 200

def delete_booking(record_id):
    url = f"{AIRTABLE_ENDPOINT}/{record_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

# Streamlit App
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="wide")
st.title("🏸 KaiaHeights Badminton Booking")

selected_date = st.date_input("Select a date", datetime.today())
bookings_df = fetch_bookings()

# Filter bookings for selected date
bookings_on_date = bookings_df[bookings_df["Booking Date"] == selected_date.strftime("%Y-%m-%d")]

# Show court availability
st.subheader(f"Availability on {selected_date.strftime('%A, %d %B %Y')}")
for court in COURTS:
    st.markdown(f"### {court}")
    cols = st.columns(6)
    for i, time in enumerate(TIME_SLOTS):
        is_booked = ((bookings_on_date["Court"] == court) & (bookings_on_date["Time"] == time)).any()
        if is_booked:
            cols[i % 6].button(time, disabled=True)
        else:
            cols[i % 6].success(time)

# Booking form
st.subheader("Make a Booking")
with st.form("booking_form"):
    name = st.text_input("Name")
    email = st.text_input("Email")
    unit = st.text_input("Unit")
    date = st.date_input("Booking Date", datetime.today())
    time = st.selectbox("Time Slot", TIME_SLOTS)
    court = st.selectbox("Court", COURTS)
    submit = st.form_submit_button("Book")

    if submit:
        # Check if already booked
        existing = bookings_df[
            (bookings_df["Email"] == email) &
            (bookings_df["Date"] == date.strftime("%Y-%m-%d"))
        ]
        if len(existing) >= 2:
            st.error("You have reached the maximum of 2 bookings per day.")
        else:
            success = create_booking(name, email, unit, date.strftime("%Y-%m-%d"), time, court)
            if success:
                st.success("Booking confirmed!")
            else:
                st.error("Failed to book. Please try again.")

# Cancel/edit bookings
st.subheader("Your Bookings")
user_email = st.text_input("Enter your email to manage bookings")
if user_email:
    user_bookings = bookings_df[bookings_df["Email"] == user_email]
    for i, row in user_bookings.iterrows():
        st.markdown(f"**{row['Date']}** - {row['Time']} - {row['Court']}")
        col1, col2 = st.columns(2)
        if col1.button(f"Cancel {i}"):
            if delete_booking(row["id"]):
                st.success("Booking cancelled.")
                st.experimental_rerun()
            else:
                st.error("Failed to cancel booking.")
