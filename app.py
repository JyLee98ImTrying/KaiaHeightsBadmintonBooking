import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# Airtable configuration
AIRTABLE_API_KEY = "patuTF5R5afg1re9p"
AIRTABLE_BASE_ID = "appelm86wRpQTooy4"
AIRTABLE_TABLE_NAME = "Bookings"
AIRTABLE_ENDPOINT = f"https://api.airtable.com/v0/{AIRTABLE_BASE_ID}/{AIRTABLE_TABLE_NAME}"
HEADERS = {
    "Authorization": f"Bearer {AIRTABLE_API_KEY}",
    "Content-Type": "application/json"
}

# Constants
TIME_SLOTS = ["10:00", "11:00", "12:00", "13:00", "14:00", "15:00",
              "16:00", "17:00", "18:00", "19:00", "20:00", "21:00"]
COURTS = ["Court 1", "Court 2", "Court 3", "Court 4", "Court 5"]

# Utility functions
def fetch_bookings():
    response = requests.get(AIRTABLE_ENDPOINT, headers=HEADERS)
    if response.status_code == 200:
        records = response.json().get("records", [])
        bookings = [
            {
                "id": r["id"],
                "Booking ID": r["fields"].get("Booking ID"),
                "Resident Name": r["fields"].get("Resident"),
                "Email": r["fields"].get("Email"),
                "Unit Number": r["fields"].get("Unit Number"),
                "Booking Date": r["fields"].get("Booking Date"),
                "Booking Time": r["fields"].get("Booking Time"),
                "Court": r["fields"].get("Court")
            }
            for r in records
        ]
        return pd.DataFrame(bookings)
    else:
        return pd.DataFrame()

def create_booking(booking_id, resident, email, unit, date, time, court):
    data = {
        "fields": {
            "Booking ID": booking_id,
            "Resident": resident,
            "Email": email,
            "Unit Number": unit,
            "Booking Date": date,
            "Booking Time": time,
            "Court": court
        }
    }
    response = requests.post(AIRTABLE_ENDPOINT, headers=HEADERS, json=data)
    return response.status_code == 200

def delete_booking(record_id):
    url = f"{AIRTABLE_ENDPOINT}/{record_id}"
    response = requests.delete(url, headers=HEADERS)
    return response.status_code == 200

# Streamlit UI
st.set_page_config(page_title="KaiaHeights Badminton Booking", layout="wide")
st.title("\ud83c\udfc8 KaiaHeights Badminton Booking")

# Sidebar for user input
with st.sidebar:
    st.header("Make a Booking")
    resident_name = st.text_input("Resident Name")
    email = st.text_input("Email")
    unit_number = st.text_input("Unit Number")
    booking_date = st.date_input("Booking Date", min_value=datetime.today())
    booking_time = st.selectbox("Booking Time", TIME_SLOTS)
    court = st.selectbox("Select Court", COURTS)

    if st.button("Book Court"):
        if resident_name and email and unit_number:
            booking_id = f"BKG-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            if create_booking(booking_id, resident_name, email, unit_number,
                              booking_date.strftime("%Y-%m-%d"), booking_time, court):
                st.success("Booking created successfully!")
            else:
                st.error("Failed to create booking")
        else:
            st.warning("Please fill in all required fields")

# Main content
st.header("Current Bookings")
selected_date = st.date_input("Filter by date", datetime.today(), key="main_date")

# Fetch and display bookings
bookings_df = fetch_bookings()
if not bookings_df.empty:
    filtered_df = bookings_df[bookings_df["Booking Date"] == selected_date.strftime("%Y-%m-%d")]

    if not filtered_df.empty:
        st.dataframe(filtered_df)

        # Delete booking option
        if st.checkbox("Delete a booking"):
            booking_to_delete = st.selectbox("Select booking to delete",
                                             filtered_df["Booking ID"].tolist())
            if st.button("Delete"):
                record_id = filtered_df[filtered_df["Booking ID"] == booking_to_delete].iloc[0]["id"]
                if delete_booking(record_id):
                    st.success("Booking deleted successfully!")
                else:
                    st.error("Failed to delete booking")
    else:
        st.info("No bookings found for selected date")
else:
    st.info("No bookings available")

# Display court availability
st.header("Court Availability")
availability_df = pd.DataFrame(True, index=TIME_SLOTS, columns=COURTS)

if not bookings_df.empty:
    for _, booking in bookings_df.iterrows():
        if booking["Booking Date"] == selected_date.strftime("%Y-%m-%d"):
            time = booking["Booking Time"]
            court = booking["Court"]
            if time in TIME_SLOTS and court in COURTS:
                availability_df.loc[time, court] = False

st.dataframe(availability_df.style.applymap(
    lambda x: 'background-color: #90EE90' if x else 'background-color: #FFB6C1'))
