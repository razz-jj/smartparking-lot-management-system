import streamlit as st
import datetime
import math
import pandas as pd
import sqlite3
import matplotlib.pyplot as plt
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os

# -----------------------------
# CONFIG
# -----------------------------
TOTAL_SLOTS = 10

VEHICLE_PRICING = {
    "bike": 10,
    "car": 20,
    "ev": 25,
    "heavy": 40
}

FIRST_2_HOURS_COST = {
    "bike": 20,
    "car": 50,
    "ev": 60,
    "heavy": 100
}

VIP_SLOTS = {1, 2}

# Admin credentials (you can change)
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "1234"

DB_FILE = "parking.db"


# -----------------------------
# DB SETUP
# -----------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parked_vehicles (
            slot INTEGER PRIMARY KEY,
            vehicle_no TEXT UNIQUE,
            vehicle_type TEXT,
            entry_time TEXT,
            vip INTEGER
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_no TEXT,
            vehicle_type TEXT,
            entry_time TEXT,
            exit_time TEXT,
            duration_hours INTEGER,
            bill INTEGER,
            date TEXT
        )
    """)

    conn.commit()
    conn.close()


def db_connect():
    return sqlite3.connect(DB_FILE)


def load_slots_from_db():
    slots = {i: None for i in range(1, TOTAL_SLOTS + 1)}
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("SELECT slot, vehicle_no, vehicle_type, entry_time, vip FROM parked_vehicles")
    rows = cur.fetchall()
    conn.close()

    for slot, vno, vtype, etime, vip in rows:
        slots[slot] = {
            "vehicle_no": vno,
            "type": vtype,
            "entry_time": datetime.datetime.fromisoformat(etime),
            "vip": bool(vip)
        }
    return slots


def add_parked_vehicle(slot, vehicle_no, vtype, entry_time, vip):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO parked_vehicles (slot, vehicle_no, vehicle_type, entry_time, vip)
        VALUES (?, ?, ?, ?, ?)
    """, (slot, vehicle_no, vtype, entry_time.isoformat(), int(vip)))
    conn.commit()
    conn.close()


def remove_parked_vehicle(slot):
    conn = db_connect()
    cur = conn.cursor()
    cur.execute("DELETE FROM parked_vehicles WHERE slot = ?", (slot,))
    conn.commit()
    conn.close()


def log_transaction(vehicle_no, vtype, entry_time, exit_time, hours, bill):
    conn = db_connect()
    cur = conn.cursor()
    today = datetime.date.today().isoformat()
    cur.execute("""
        INSERT INTO transactions (vehicle_no, vehicle_type, entry_time, exit_time, duration_hours, bill, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (vehicle_no, vtype, entry_time.isoformat(), exit_time.isoformat(), hours, bill, today))
    conn.commit()
    conn.close()


def get_today_transactions():
    today = datetime.date.today().isoformat()
    conn = db_connect()
    df = pd.read_sql_query("SELECT * FROM transactions WHERE date = ?", conn, params=(today,))
    conn.close()
    return df


# -----------------------------
# PARKING LOGIC
# -----------------------------
def get_next_free_slot(slots, is_vip=False):
    if is_vip:
        for s in sorted(VIP_SLOTS):
            if slots[s] is None:
                return s
        return None

    for s in range(1, TOTAL_SLOTS + 1):
        if s not in VIP_SLOTS and slots[s] is None:
            return s

    for s in sorted(VIP_SLOTS):
        if slots[s] is None:
            return s

    return None


def calculate_bill(vehicle_type, entry_time, exit_time):
    duration_seconds = (exit_time - entry_time).total_seconds()
    duration_hours = math.ceil(duration_seconds / 3600)

    if duration_hours <= 2:
        return FIRST_2_HOURS_COST[vehicle_type], duration_hours

    extra_hours = duration_hours - 2
    bill = FIRST_2_HOURS_COST[vehicle_type] + extra_hours * VEHICLE_PRICING[vehicle_type]
    return bill, duration_hours


# -----------------------------
# PDF EXPORT
# -----------------------------
def generate_pdf_report(df, total_revenue):
    filename = "daily_report.pdf"
    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    c.setFont("Helvetica-Bold", 16)
    c.drawString(200, height - 50, "Daily Parking Report")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 90, f"Date: {datetime.date.today()}")
    c.drawString(50, height - 110, f"Total Transactions: {len(df)}")
    c.drawString(50, height - 130, f"Total Revenue: ₹{total_revenue}")

    y = height - 170
    c.setFont("Helvetica-Bold", 10)
    c.drawString(50, y, "Vehicle No")
    c.drawString(150, y, "Type")
    c.drawString(250, y, "Hours")
    c.drawString(320, y, "Bill")

    c.setFont("Helvetica", 10)
    y -= 20

    for _, row in df.iterrows():
        if y < 50:
            c.showPage()
            y = height - 50

        c.drawString(50, y, str(row["vehicle_no"]))
        c.drawString(150, y, str(row["vehicle_type"]))
        c.drawString(250, y, str(row["duration_hours"]))
        c.drawString(320, y, f"₹{row['bill']}")
        y -= 18

    c.save()
    return filename


# -----------------------------
# LOGIN
# -----------------------------
def login_ui():
    st.subheader("🔐 Admin Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login ✅"):
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            st.session_state.logged_in = True
            st.success("Login Successful ✅")
            st.rerun()
        else:
            st.error("Invalid username or password ❌")


# -----------------------------
# MAIN APP
# -----------------------------
init_db()

st.set_page_config(page_title="Smart Parking Lot Web App", layout="wide")
st.title("🚗 Smart Parking Lot Management System (Web App)")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    login_ui()
    st.stop()

# Logout
if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# Load slots
slots = load_slots_from_db()

# Tabs
tab1, tab2, tab3, tab4 = st.tabs(["✅ Vehicle Entry", "🚪 Vehicle Exit", "📌 Slot Status", "📊 Dashboard & Report"])


# -----------------------------
# ENTRY TAB
# -----------------------------
with tab1:
    st.subheader("Vehicle Entry")

    col1, col2, col3 = st.columns(3)
    with col1:
        vehicle_no = st.text_input("Vehicle Number", placeholder="Example: TS09AB1234")
    with col2:
        vehicle_type = st.selectbox("Vehicle Type", list(VEHICLE_PRICING.keys()))
    with col3:
        vip_entry = st.radio("VIP Entry?", ["No", "Yes"])

    if st.button("Park Vehicle ✅"):
        vno = vehicle_no.strip().upper()

        if not vno:
            st.error("Vehicle number required!")
        else:
            already = any(data and data["vehicle_no"] == vno for data in slots.values())
            if already:
                st.error("Vehicle already parked!")
            else:
                is_vip = (vip_entry == "Yes")
                slot_no = get_next_free_slot(slots, is_vip=is_vip)

                if slot_no is None:
                    st.error("Parking Full!")
                else:
                    entry_time = datetime.datetime.now()
                    add_parked_vehicle(slot_no, vno, vehicle_type, entry_time, is_vip)
                    st.success(f"✅ Parked in Slot {slot_no}")
                    st.info(f"Entry Time: {entry_time}")
                    st.rerun()


# -----------------------------
# EXIT TAB
# -----------------------------
with tab2:
    st.subheader("Vehicle Exit")

    exit_vehicle_no = st.text_input("Vehicle Number for Exit")

    if st.button("Exit Vehicle 🚪"):
        vno_exit = exit_vehicle_no.strip().upper()
        found_slot = None

        for slot_no, data in slots.items():
            if data and data["vehicle_no"] == vno_exit:
                found_slot = slot_no
                break

        if found_slot is None:
            st.error("Vehicle not found!")
        else:
            exit_time = datetime.datetime.now()
            entry_time = slots[found_slot]["entry_time"]
            vtype = slots[found_slot]["type"]

            bill, hours = calculate_bill(vtype, entry_time, exit_time)

            log_transaction(vno_exit, vtype, entry_time, exit_time, hours, bill)
            remove_parked_vehicle(found_slot)

            st.success("✅ Exit successful!")
            st.write(f"Slot Freed: {found_slot}")
            st.write(f"Duration: {hours} hour(s)")
            st.write(f"Bill Amount: ₹{bill}")
            st.rerun()


# -----------------------------
# SLOT STATUS TAB
# -----------------------------
with tab3:
    st.subheader("Slot Status")

    available = []
    parked = []

    for slot_no, data in slots.items():
        if data is None:
            available.append(f"Slot {slot_no} {'(VIP)' if slot_no in VIP_SLOTS else ''}")
        else:
            parked.append({
                "Slot": slot_no,
                "Vehicle No": data["vehicle_no"],
                "Type": data["type"],
                "Mode": "VIP" if data["vip"] else "NORMAL",
                "Entry Time": data["entry_time"].strftime("%Y-%m-%d %H:%M:%S")
            })

    colA, colB = st.columns(2)

    with colA:
        st.markdown("### ✅ Available Slots")
        if available:
            st.write(available)
        else:
            st.warning("No slots available!")

    with colB:
        st.markdown("### 🚗 Parked Vehicles")
        if parked:
            st.dataframe(pd.DataFrame(parked), use_container_width=True)
        else:
            st.info("No parked vehicles.")


# -----------------------------
# DASHBOARD + REPORT TAB
# -----------------------------
with tab4:
    st.subheader("Dashboard & Daily Report")

    df = get_today_transactions()
    total_revenue = df["bill"].sum() if not df.empty else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Transactions Today", len(df))
    col2.metric("Today's Revenue", f"₹{total_revenue}")
    col3.metric("Vehicles Parked (Live)", sum(1 for x in slots.values() if x is not None))

    st.markdown("---")

    # Charts
    if not df.empty:
        st.markdown("### 📈 Revenue Chart (Per Transaction)")
        fig1 = plt.figure()
        plt.plot(df["bill"].tolist())
        plt.xlabel("Transaction Index")
        plt.ylabel("Bill Amount")
        st.pyplot(fig1)

        st.markdown("### 🚘 Vehicle Type Count")
        fig2 = plt.figure()
        df["vehicle_type"].value_counts().plot(kind="bar")
        plt.xlabel("Vehicle Type")
        plt.ylabel("Count")
        st.pyplot(fig2)

        st.markdown("### 🧾 Today's Transactions Table")
        st.dataframe(df[["vehicle_no", "vehicle_type", "duration_hours", "bill", "exit_time"]], use_container_width=True)

        # PDF download
        if st.button("⬇ Download Daily Report PDF"):
            pdf_file = generate_pdf_report(df, total_revenue)
            with open(pdf_file, "rb") as f:
                st.download_button(
                    label="📄 Click to Download PDF",
                    data=f,
                    file_name="daily_report.pdf",
                    mime="application/pdf"
                )
    else:
        st.info("No transactions today. Exit a vehicle to generate report.")
